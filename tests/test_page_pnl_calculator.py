from pathlib import Path
from datetime import datetime, timedelta
from streamlit.testing.v1 import AppTest
import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _navigate_to_pnl_calculator(at: AppTest):
    at.sidebar.selectbox[0].set_value("P&L Calculator").run()
    assert not at.exception, f"Failed navigating to P&L Calculator: {at.exception}"


def test_zero_inputs_shows_no_pnl_section():
    """Manual entry: entry/exit/quantity all zero shows no P&L section
    (guarded by the > 0 checks) without exception."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_pnl_calculator(at)

    # Defaults are 0.0 for entry_price, exit_price, quantity
    assert not at.exception, f"Exception on zero inputs: {at.exception}"
    metric_labels = [m.label for m in at.metric]
    assert not any("Gross P&L" in label for label in metric_labels), "P&L section should not render with zero inputs"
    assert not any("Total Costs" in label for label in metric_labels), "P&L section should not render with zero inputs"


def test_long_and_short_trades_produce_correct_pnl_sign():
    """A normal Long and a normal Short trade produce the correct sign of P&L
    (Short profits when exit < entry, Long profits when exit > entry)."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_pnl_calculator(at)

    # 1. Test Long trade: entry = 100, exit = 150, quantity = 2 -> Profit
    at.number_input[0].set_value(100.0)
    at.number_input[1].set_value(150.0)
    at.number_input[2].set_value(2.0)
    at.selectbox[0].set_value("Long").run()

    assert not at.exception, f"Exception on Long trade: {at.exception}"
    assert len(at.success) > 0, "Expected Net Profit success banner on winning Long"
    assert any("Net Profit" in s.value for s in at.success)

    # 2. Test Short trade: entry = 100, exit = 70, quantity = 2 -> Profit
    at.number_input[0].set_value(100.0)
    at.number_input[1].set_value(70.0)
    at.number_input[2].set_value(2.0)
    at.selectbox[0].set_value("Short").run()

    assert not at.exception, f"Exception on winning Short trade: {at.exception}"
    assert len(at.success) > 0, "Expected Net Profit success banner on winning Short"
    assert any("Net Profit" in s.value for s in at.success)

    # 3. Test Short trade: entry = 100, exit = 130, quantity = 2 -> Loss
    at.number_input[0].set_value(100.0)
    at.number_input[1].set_value(130.0)
    at.number_input[2].set_value(2.0)
    at.selectbox[0].set_value("Short").run()

    assert not at.exception, f"Exception on losing Short trade: {at.exception}"
    assert len(at.error) > 0, "Expected Net Loss banner on losing Short"
    assert any("Net Loss" in e.value for e in at.error)


def test_analyze_session_trades_empty_history_shows_info():
    """'Analyze Session Trades' with an empty signals_history shows the
    'no signal history' info message."""
    storage.save_state("signals_history", [])

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.signals_history = []
    _navigate_to_pnl_calculator(at)

    analyze_btn = [btn for btn in at.button if "Analyze Session Trades" in btn.label][0]
    analyze_btn.click().run()

    assert not at.exception, f"Exception on analyze empty session trades: {at.exception}"
    info_texts = [i.value for i in at.info]
    assert any("No signal history available" in msg for msg in info_texts)


def test_analyze_session_trades_with_seeded_history_deterministic():
    """'Analyze Session Trades' with seeded signals_history entries fetches real
    follow-up prices and renders the mark-to-market table without exception,
    confirming P&L is NOT random/simulated (two runs produce identical numbers)."""
    now = datetime.now()
    seeded = [
        {"symbol": "BTC", "signal": "BUY", "price": 7000000.0, "timestamp": now - timedelta(days=5), "timeframe": "1h"},
        {"symbol": "ETH", "signal": "SELL", "price": 250000.0, "timestamp": now - timedelta(days=3), "timeframe": "1h"},
    ]
    storage.save_state("signals_history", seeded)

    # Run 1
    at1 = AppTest.from_file(APP_PATH, default_timeout=60)
    at1.run()
    at1.session_state.signals_history = list(seeded)
    _navigate_to_pnl_calculator(at1)

    analyze_btn1 = [btn for btn in at1.button if "Analyze Session Trades" in btn.label][0]
    analyze_btn1.click().run()

    assert not at1.exception, f"Exception on Run 1: {at1.exception}"
    assert len(at1.dataframe) > 0, "Expected mark-to-market table in Run 1"
    df1 = at1.dataframe[0].value
    pnl_run1 = list(df1["P&L (mark-to-market)"])

    # Run 2 with identical seeded history
    at2 = AppTest.from_file(APP_PATH, default_timeout=60)
    at2.run()
    at2.session_state.signals_history = list(seeded)
    _navigate_to_pnl_calculator(at2)

    analyze_btn2 = [btn for btn in at2.button if "Analyze Session Trades" in btn.label][0]
    analyze_btn2.click().run()

    assert not at2.exception, f"Exception on Run 2: {at2.exception}"
    assert len(at2.dataframe) > 0, "Expected mark-to-market table in Run 2"
    df2 = at2.dataframe[0].value
    pnl_run2 = list(df2["P&L (mark-to-market)"])

    # Confirm P&L is deterministic (real follow-up historical prices, not np.random)
    import pytest
    assert pnl_run1 == pytest.approx(pnl_run2, rel=1e-2), f"P&L differed across runs! Run 1: {pnl_run1}, Run 2: {pnl_run2}"

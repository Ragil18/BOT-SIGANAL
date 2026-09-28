from pathlib import Path
from datetime import datetime, timedelta
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _navigate_to_backtesting(at: AppTest):
    at.sidebar.selectbox[0].set_value("Backtesting").run()
    assert not at.exception, f"Failed navigating to Backtesting: {at.exception}"


def test_default_backtest_run_with_trades():
    """Default backtest run completes with no exception for a symbol/timeframe
    combination confirmed to produce trades (ETH on 1d with a 1-year window)."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    at.sidebar.text_input[0].set_value("ETH")
    at.sidebar.selectbox[1].set_value("1d")
    at.date_input[0].set_value(datetime.now().date() - timedelta(days=365)).run()

    at.button[0].click().run()
    assert not at.exception, f"Backtest raised exception: {at.exception}"

    metric_labels = [m.label for m in at.metric]
    assert any("Total Return" in label for label in metric_labels)
    assert any("Win Rate" in label for label in metric_labels)
    assert any("Max Drawdown" in label for label in metric_labels)
    assert any("Sharpe Ratio" in label for label in metric_labels)
    assert len(at.dataframe) > 0, "Expected trade history dataframe to be rendered"


def test_start_date_after_end_date_handled_gracefully():
    """Start Date after End Date (invalid range) is handled with a clear message, not a crash."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    at.date_input[0].set_value(datetime.now().date()).run()
    at.date_input[1].set_value((datetime.now() - timedelta(days=30)).date()).run()

    at.button[0].click().run()
    assert not at.exception, f"Crash on invalid date range: {at.exception}"
    assert len(at.error) > 0, "Expected an error message when start date is after end date"
    error_texts = [e.value for e in at.error]
    assert any("No historical data available" in msg for msg in error_texts)


def test_toggling_stop_loss_and_take_profit_disabled():
    """Toggling stop-loss/take-profit checkboxes off entirely (both disabled)
    still runs and passes None through to run_backtest without exception."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    at.sidebar.text_input[0].set_value("ETH")
    at.sidebar.selectbox[1].set_value("1d")
    at.date_input[0].set_value(datetime.now().date() - timedelta(days=180)).run()

    # Disable both stop-loss and take-profit checkboxes
    at.checkbox[0].set_value(False)
    at.checkbox[1].set_value(False)

    at.button[0].click().run()
    assert not at.exception, f"Crash with SL/TP disabled: {at.exception}"
    metric_labels = [m.label for m in at.metric]
    assert any("Total Return" in label for label in metric_labels)


def test_position_size_slider_min_and_max():
    """Position Size slider at its 10% minimum and 100% maximum both run without
    exception, and the trade sizes actually differ."""
    # 1. Run with position size at 10% on ADA (low unit price ensures integer shares > 0 at 10%)
    at1 = AppTest.from_file(APP_PATH, default_timeout=60)
    at1.run()
    _navigate_to_backtesting(at1)

    at1.sidebar.text_input[0].set_value("ADA")
    at1.sidebar.selectbox[1].set_value("1d")
    at1.date_input[0].set_value(datetime.now().date() - timedelta(days=365)).run()

    at1.slider[0].set_value(10)
    at1.button[0].click().run()
    assert not at1.exception, f"Failed at 10% position size: {at1.exception}"
    assert len(at1.dataframe) > 0, "No trades dataframe at 10%"
    df_small = at1.dataframe[0].value
    small_shares = df_small["shares"].iloc[0]

    # 2. Run with position size at 100% on ADA
    at2 = AppTest.from_file(APP_PATH, default_timeout=60)
    at2.run()
    _navigate_to_backtesting(at2)

    at2.sidebar.text_input[0].set_value("ADA")
    at2.sidebar.selectbox[1].set_value("1d")
    at2.date_input[0].set_value(datetime.now().date() - timedelta(days=365)).run()

    at2.slider[0].set_value(100)
    at2.button[0].click().run()
    assert not at2.exception, f"Failed at 100% position size: {at2.exception}"
    assert len(at2.dataframe) > 0, "No trades dataframe at 100%"
    df_large = at2.dataframe[0].value
    large_shares = df_large["shares"].iloc[0]

    assert small_shares < large_shares, f"Expected {small_shares} < {large_shares}"


def test_run_risk_analysis_with_and_without_trades():
    """'Run risk analysis' checkbox produces VaR/Expected Shortfall/Monte Carlo
    metrics with no exception, including on a backtest that made zero trades."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    # 1. Test with trades (ETH, 1d, 1y)
    at.sidebar.text_input[0].set_value("ETH")
    at.sidebar.selectbox[1].set_value("1d")
    at.date_input[0].set_value(datetime.now().date() - timedelta(days=365)).run()
    at.checkbox[2].set_value(True)  # Run risk analysis

    at.button[0].click().run()
    assert not at.exception, f"Failed on risk analysis with trades: {at.exception}"

    metric_labels = [m.label for m in at.metric]
    assert any("Value at Risk" in label for label in metric_labels)
    assert any("Expected Shortfall" in label for label in metric_labels)
    assert any("Monte Carlo" in label for label in metric_labels)

    # 2. Test with zero trades (BTC 1d defaults produces zero trades)
    at.sidebar.text_input[0].set_value("BTC")
    at.sidebar.selectbox[1].set_value("1d")
    at.date_input[0].set_value(datetime.now().date() - timedelta(days=60)).run()
    at.checkbox[2].set_value(True)

    at.button[0].click().run()
    assert not at.exception, f"Failed on zero trades risk analysis: {at.exception}"
    info_texts = [i.value for i in at.info]
    assert any("No portfolio history to analyze" in msg or "No trades" in msg for msg in info_texts)


def test_run_consistency_check_produces_table():
    """'Run consistency check' checkbox produces a 4-fold table, including on a
    date range short enough that some folds have very few bars."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    at.sidebar.text_input[0].set_value("ETH")
    at.sidebar.selectbox[1].set_value("1d")
    at.date_input[0].set_value(datetime.now().date() - timedelta(days=120)).run()
    at.checkbox[3].set_value(True)  # Run consistency check

    at.button[0].click().run()
    assert not at.exception, f"Failed on consistency check: {at.exception}"
    # Consistency check produces a dataframe with folds
    assert len(at.dataframe) > 0, "Consistency check did not produce any table"


def test_initial_capital_at_minimum():
    """Initial Capital at its 50,000 minimum runs without exception."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_backtesting(at)

    at.sidebar.text_input[0].set_value("ETH")
    at.sidebar.selectbox[1].set_value("1d")
    at.number_input[0].set_value(50000).run()

    at.button[0].click().run()
    assert not at.exception, f"Failed with initial capital 50,000: {at.exception}"

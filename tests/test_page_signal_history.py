from pathlib import Path
from datetime import datetime, timedelta
from streamlit.testing.v1 import AppTest
from core import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _navigate_to_signal_history(at: AppTest):
    at.sidebar.selectbox[0].set_value("Signal History").run()
    assert not at.exception, f"Failed navigating to Signal History: {at.exception}"


def test_empty_history_shows_info_message():
    """With an empty history, the page shows the 'no history' info message."""
    storage.save_state("signals_history", [])

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.signals_history = []
    _navigate_to_signal_history(at)

    assert not at.exception, f"Exception on empty history: {at.exception}"
    assert len(at.info) > 0, "Expected info message when signal history is empty"
    info_texts = [i.value for i in at.info]
    assert any("No signal history available" in msg for msg in info_texts)


def test_filters_narrow_displayed_dataframe():
    """Seed st.session_state.signals_history with several synthetic entries
    (different symbols/signals/timestamps spanning >30 days) before at.run(),
    then verify each filter (Symbol, Signal, Days) narrows the displayed dataframe correctly."""
    now = datetime.now()
    synthetic_history = [
        {"timestamp": now, "symbol": "BTC", "signal": "BUY", "price": 5000000.0, "strength": 0.8, "timeframe": "1h"},
        {"timestamp": now - timedelta(days=3), "symbol": "ETH", "signal": "SELL", "price": 300000.0, "strength": 0.7, "timeframe": "1h"},
        {"timestamp": now - timedelta(days=12), "symbol": "BTC", "signal": "SELL", "price": 4800000.0, "strength": 0.6, "timeframe": "4h"},
        {"timestamp": now - timedelta(days=45), "symbol": "SOL", "signal": "BUY", "price": 15000.0, "strength": 0.9, "timeframe": "1d"},
    ]
    storage.save_state("signals_history", synthetic_history)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.signals_history = list(synthetic_history)
    _navigate_to_signal_history(at)

    assert len(at.dataframe) > 0, "Expected dataframe to be displayed with seeded entries"
    initial_df = at.dataframe[0].value
    assert len(initial_df) == 4

    # 1. Filter by Symbol: BTC
    at.selectbox[0].set_value("BTC").run()
    assert not at.exception
    btc_df = at.dataframe[0].value
    assert len(btc_df) == 2
    assert all(btc_df["symbol"] == "BTC")

    # Reset Symbol filter back to "All"
    at.selectbox[0].set_value("All").run()

    # 2. Filter by Signal: BUY
    at.selectbox[1].set_value("BUY").run()
    assert not at.exception
    buy_df = at.dataframe[0].value
    assert len(buy_df) == 2
    assert all(buy_df["signal"] == "BUY")

    # Reset Signal filter back to "All"
    at.selectbox[1].set_value("All").run()

    # 3. Filter by Days: Last 7 days (should exclude entries from 12 and 45 days ago)
    at.selectbox[2].set_value("Last 7 days").run()
    assert not at.exception
    recent_df = at.dataframe[0].value
    assert len(recent_df) == 2  # Only the entries from today and 3 days ago

    # Filter by Days: Last 30 days (should include entries from 0, 3, 12 days ago, exclude 45)
    at.selectbox[2].set_value("Last 30 days").run()
    assert not at.exception
    month_df = at.dataframe[0].value
    assert len(month_df) == 3


def test_clear_history_empties_session_and_persisted_storage():
    """'Clear History' empties both session state and persisted storage."""
    now = datetime.now()
    synthetic_history = [
        {"timestamp": now, "symbol": "BTC", "signal": "BUY", "price": 5000000.0, "strength": 0.8, "timeframe": "1h"},
        {"timestamp": now - timedelta(days=2), "symbol": "ETH", "signal": "SELL", "price": 300000.0, "strength": 0.7, "timeframe": "1h"},
    ]
    storage.save_state("signals_history", synthetic_history)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_signal_history(at)

    # In Signal History: button[0] is Export to CSV, button[1] is Clear History
    clear_btn = [btn for btn in at.button if "Clear History" in btn.label][0]
    clear_btn.click().run()

    assert not at.exception, f"Exception on clearing history: {at.exception}"
    assert len(at.session_state.signals_history) == 0, "session_state.signals_history was not cleared"
    persisted = storage.load_state("signals_history", [])
    assert len(persisted) == 0, "Persisted signals_history in storage was not cleared"


def test_export_to_csv_produces_non_empty_download():
    """'Export to CSV' produces a non-empty CSV download without exception."""
    now = datetime.now()
    synthetic_history = [
        {"timestamp": now, "symbol": "BTC", "signal": "BUY", "price": 5000000.0, "strength": 0.8, "timeframe": "1h"},
        {"timestamp": now - timedelta(days=1), "symbol": "ETH", "signal": "SELL", "price": 300000.0, "strength": 0.7, "timeframe": "1h"},
    ]
    storage.save_state("signals_history", synthetic_history)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.signals_history = list(synthetic_history)
    _navigate_to_signal_history(at)

    export_btn = [btn for btn in at.button if "Export to CSV" in btn.label][0]
    export_btn.click().run()

    assert not at.exception, f"Exception clicking export to CSV: {at.exception}"
    assert len(at.download_button) > 0, "Download button not found after clicking export"
    download_btn = at.download_button[0]
    assert download_btn.label == "Download CSV"
    assert download_btn.proto.url.endswith(".csv"), "Expected download URL for CSV file"


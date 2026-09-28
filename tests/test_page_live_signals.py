from pathlib import Path
from streamlit.testing.v1 import AppTest
import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def test_default_load_renders_ticker_and_signal_metrics():
    """Default load renders the live ticker (5 metrics) and the 4 signal metrics
    (Current Price, Signal, Risk Level, Market Volatility) with no exception."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    assert not at.exception, f"AppTest raised an exception: {at.exception}"
    assert len(at.metric) >= 9, f"Expected at least 9 metrics, found {len(at.metric)}"

    labels = [m.label for m in at.metric]
    for required_label in ["Current Price", "Signal", "Risk Level", "Market Volatility"]:
        assert any(required_label in label for label in labels), f"Missing metric {required_label}"

    # Verify live ticker metrics for major symbols exist
    for ticker in ["BTC", "ETH", "BNB", "XRP", "ADA"]:
        assert any(ticker in label for label in labels), f"Missing live ticker for {ticker}"


def test_invalid_symbol_shows_error_message():
    """Changing the Symbol text input to an invalid symbol (e.g. 'NOTACOIN')
    shows an error/empty-data message, not a crash."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    # The sidebar Symbol input is text_input[0]
    symbol_input = at.sidebar.text_input[0]
    symbol_input.set_value("NOTACOIN").run()

    assert not at.exception, f"Crash on invalid symbol: {at.exception}"
    assert len(at.error) > 0, "Expected an error message for invalid symbol"
    error_texts = [e.value for e in at.error]
    assert any("NOTACOIN" in msg or "No data available" in msg for msg in error_texts)


def test_timeframe_options_rerender_without_exception():
    """Changing Timeframe across all 7 options (1m..1d) re-renders without
    exception for at least one real symbol."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    timeframe_select = at.sidebar.selectbox[1]

    for tf in timeframes:
        timeframe_select.set_value(tf).run()
        assert not at.exception, f"Failed on timeframe {tf}: {at.exception}"


def test_indicator_sliders_min_max_and_invalid_macd():
    """Moving each indicator slider to its min and max and re-running doesn't crash,
    and MACD Fast >= MACD Slow (an invalid combination a user could select) is handled."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    sliders = at.sidebar.slider
    # Sliders in sidebar:
    # 0: RSI Period (5..30)
    # 1: MACD Fast (5..20)
    # 2: MACD Slow (15..40)
    # 3: MACD Signal (3..15)
    # 4: Bollinger Period (10..30)
    # 5: Bollinger Std (1.0..3.0)
    # 6: Signal Sensitivity (0.2..0.8)
    min_vals = [5, 5, 15, 3, 10, 1.0, 0.2]
    max_vals = [30, 20, 40, 15, 30, 3.0, 0.8]

    # Test all min values
    for s, v in zip(sliders, min_vals):
        s.set_value(v)
    at.run()
    assert not at.exception, f"Failed on min slider values: {at.exception}"

    # Test all max values
    for s, v in zip(sliders, max_vals):
        s.set_value(v)
    at.run()
    assert not at.exception, f"Failed on max slider values: {at.exception}"

    # Test invalid MACD combination: MACD Fast (20) >= MACD Slow (15)
    sliders[1].set_value(20)
    sliders[2].set_value(15)
    at.run()
    assert not at.exception, f"Failed on MACD Fast >= MACD Slow: {at.exception}"


def test_enable_auto_refresh_renders_without_blocking():
    """Enabling 'Enable Auto-Refresh' renders without blocking (fragment ticks
    in the background) and doesn't error."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    auto_refresh_cbs = [cb for cb in at.checkbox if "Auto-Refresh" in cb.label]
    assert len(auto_refresh_cbs) > 0, "Auto-refresh checkbox not found"
    auto_refresh_cbs[0].set_value(True).run()

    assert not at.exception, f"Exception when enabling auto-refresh: {at.exception}"


def test_buy_sell_signal_appended_and_persisted():
    """A generated BUY/SELL signal gets appended to signals_history and persisted
    (assert via storage.load_state('signals_history', []) after the run)."""
    # Clear signals_history in storage before test run to ensure a clean state
    storage.save_state("signals_history", [])

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()

    # Set timeframe to 1d and sensitivity to 0.2 to trigger active BUY/SELL signal
    at.sidebar.selectbox[1].set_value("1d")
    at.sidebar.slider[6].set_value(0.2).run()

    # If BTC on 1d didn't produce a signal, switch to SOL on 1h
    if not at.session_state.signals_history:
        at.sidebar.text_input[0].set_value("SOL")
        at.sidebar.selectbox[1].set_value("1h")
        at.sidebar.slider[6].set_value(0.2).run()

    assert not at.exception, f"Exception during signal run: {at.exception}"
    persisted_history = storage.load_state("signals_history", [])
    assert len(at.session_state.signals_history) > 0, "No signal appended to session_state.signals_history"
    assert len(persisted_history) > 0, "Signal not persisted in storage"
    assert persisted_history[-1]["signal"] in ["BUY", "SELL"]

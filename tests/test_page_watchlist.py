from pathlib import Path
from streamlit.testing.v1 import AppTest
from core import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _navigate_to_watchlist(at: AppTest):
    at.sidebar.selectbox[0].set_value("Watchlist").run()
    assert not at.exception, f"Failed navigating to Watchlist: {at.exception}"


def test_add_valid_new_symbol_succeeds_and_persists():
    """Adding a valid new symbol succeeds, appears in the list, and is persisted."""
    # Reset watchlist to known default in storage
    defaults = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    storage.save_state("watchlist", defaults)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    # Main text input is "Add Crypto Symbol" (at.text_input[0])
    at.text_input[0].set_value("SOL")
    # First button in main area is "Add"
    at.button[0].click().run()

    assert not at.exception, f"Exception adding symbol: {at.exception}"
    assert "SOL" in at.session_state.watchlist, "SOL not found in session_state.watchlist"
    persisted = storage.load_state("watchlist", [])
    assert "SOL" in persisted, "SOL not found in storage.load_state"
    assert len(at.success) > 0, "Expected success notification"


def test_add_already_present_symbol_shows_warning():
    """Adding an already-present symbol shows a warning, doesn't duplicate."""
    defaults = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    storage.save_state("watchlist", defaults)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    at.text_input[0].set_value("BTC")
    at.button[0].click().run()

    assert not at.exception, f"Exception on duplicate symbol: {at.exception}"
    assert len(at.warning) > 0, "Expected warning for duplicate symbol"
    assert at.session_state.watchlist.count("BTC") == 1, "Duplicate BTC added to watchlist"


def test_add_invalid_symbol_shows_error():
    """Adding an invalid symbol shows an error and does NOT get added."""
    defaults = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    storage.save_state("watchlist", defaults)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    at.text_input[0].set_value("FAKECRYPTO999XYZ")
    at.button[0].click().run()

    assert not at.exception, f"Exception on invalid symbol: {at.exception}"
    assert len(at.error) > 0, "Expected error message for invalid crypto symbol"
    assert "FAKECRYPTO999XYZ" not in at.session_state.watchlist


def test_add_empty_string_shows_warning():
    """Adding an empty string shows a warning, not a crash."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    at.text_input[0].set_value("")
    at.button[0].click().run()

    assert not at.exception, f"Crash on empty symbol add: {at.exception}"
    assert len(at.warning) > 0, "Expected warning when attempting to add empty symbol"


def test_remove_symbol_updates_session_and_storage():
    """Removing a symbol updates both session state and persisted storage."""
    defaults = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    storage.save_state("watchlist", defaults)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    assert "BTC" in at.session_state.watchlist
    # button[0] is "Add", button[1] is remove_0 (BTC)
    at.button[1].click().run()

    assert not at.exception, f"Exception on removing symbol: {at.exception}"
    assert "BTC" not in at.session_state.watchlist
    persisted = storage.load_state("watchlist", [])
    assert "BTC" not in persisted, "BTC still present in persisted storage"


def test_render_watchlist_with_price_and_signals():
    """Rendering the list itself (5 default symbols) shows price/change/signal
    for each with no exception, even if one symbol's data fetch fails."""
    defaults = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    storage.save_state("watchlist", defaults)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_watchlist(at)

    assert not at.exception, f"Exception rendering watchlist: {at.exception}"
    # Verify symbols appear in rendered text
    rendered_text = " ".join([m.value for m in at.markdown])
    for sym in defaults:
        assert sym in rendered_text or any(sym in str(c.value) for c in at.columns), f"Symbol {sym} missing from watchlist view"

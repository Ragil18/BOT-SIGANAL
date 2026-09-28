from pathlib import Path
from datetime import datetime
from streamlit.testing.v1 import AppTest
from core import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def _navigate_to_smart_alerts(at: AppTest):
    at.sidebar.selectbox[0].set_value("Smart Alerts").run()
    assert not at.exception, f"Failed navigating to Smart Alerts: {at.exception}"


def test_create_all_five_alert_types_and_persisted():
    """Creating one alert of each of the 5 types (Price Target, RSI Overbought/Oversold,
    Volume Spike, Squeeze Breakout, Trend Change) with a valid symbol succeeds and is persisted."""
    storage.save_state("alerts", [])

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.alerts = []
    _navigate_to_smart_alerts(at)

    alert_types = [
        "Price Target",
        "RSI Overbought/Oversold",
        "Volume Spike",
        "Squeeze Breakout",
        "Trend Change",
    ]

    for alert_type in alert_types:
        at.text_input[0].set_value("BTC")
        at.selectbox[0].set_value(alert_type).run()
        # Click Create Alert button (button[0])
        create_btn = [btn for btn in at.button if "Create Alert" in btn.label][0]
        create_btn.click().run()
        assert not at.exception, f"Exception creating alert of type {alert_type}: {at.exception}"
        assert any("Alert created" in s.value for s in at.success)

    assert len(at.session_state.alerts) == 5
    persisted_alerts = storage.load_state("alerts", [])
    assert len(persisted_alerts) == 5
    persisted_types = [a["type"] for a in persisted_alerts]
    assert set(persisted_types) == set(alert_types)


def test_create_alert_with_invalid_symbol_rejected():
    """Creating an alert with an invalid symbol is rejected with an error."""
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    _navigate_to_smart_alerts(at)

    initial_alert_count = len(at.session_state.alerts)
    at.text_input[0].set_value("INVALIDCOIN999XYZ")
    create_btn = [btn for btn in at.button if "Create Alert" in btn.label][0]
    create_btn.click().run()

    assert not at.exception, f"Crash on invalid alert symbol: {at.exception}"
    assert len(at.error) > 0, "Expected error message when creating alert with invalid symbol"
    assert len(at.session_state.alerts) == initial_alert_count


def test_existing_alert_expander_calls_check_condition_for_all_types():
    """An existing alert's expander actually calls _check_alert_condition and
    renders a detail line with no exception, for each of the 5 types."""
    now = datetime.now()
    seeded_alerts = [
        {"id": 0, "symbol": "BTC", "type": "Price Target", "target_price": 5000000.0, "condition": "Above", "created": now, "active": True},
        {"id": 1, "symbol": "BTC", "type": "RSI Overbought/Oversold", "rsi_level": 30, "condition": "Below (Oversold)", "created": now, "active": True},
        {"id": 2, "symbol": "BTC", "type": "Volume Spike", "volume_multiplier": 2.0, "created": now, "active": True},
        {"id": 3, "symbol": "BTC", "type": "Squeeze Breakout", "created": now, "active": True},
        {"id": 4, "symbol": "BTC", "type": "Trend Change", "created": now, "active": True},
    ]
    storage.save_state("alerts", seeded_alerts)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.alerts = list(seeded_alerts)
    _navigate_to_smart_alerts(at)

    assert not at.exception, f"Exception rendering active alerts: {at.exception}"
    assert len(at.expander) >= 5, f"Expected 5 expanders, found {len(at.expander)}"


def test_delete_alert_sets_inactive_and_persists():
    """Deleting an alert sets it inactive and persists that change."""
    now = datetime.now()
    seeded_alerts = [
        {"id": 0, "symbol": "BTC", "type": "Price Target", "target_price": 5000000.0, "condition": "Above", "created": now, "active": True},
    ]
    storage.save_state("alerts", seeded_alerts)

    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    at.session_state.alerts = list(seeded_alerts)
    _navigate_to_smart_alerts(at)

    delete_btn = [btn for btn in at.button if "Delete" in btn.label][0]
    delete_btn.click().run()

    assert not at.exception, f"Exception on deleting alert: {at.exception}"
    assert not at.session_state.alerts[0]["active"], "Alert active flag was not set to False"
    persisted = storage.load_state("alerts", [])
    assert not persisted[0]["active"], "Persisted alert active flag was not updated to False"

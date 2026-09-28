import importlib


def test_pure_modules_import_cleanly():
    """A basic import-smoke-test would have caught the original bug where
    backtester.py used pd.DataFrame (as a type annotation and at runtime) without
    ever importing pandas — that raised NameError the moment the module loaded."""
    for module_name in ["data_fetcher", "technical_indicators", "signal_generator",
                         "backtester", "storage"]:
        importlib.import_module(module_name)


def test_app_boots_without_error():
    """Runs app.py through Streamlit's own AppTest harness (a real script execution
    in a simulated session, no browser needed) and asserts nothing raised."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=60)
    at.run()

    assert not at.exception, f"app.py raised on boot: {at.exception}"

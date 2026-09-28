from pathlib import Path
from datetime import datetime
from streamlit.testing.v1 import AppTest
import storage

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def test_full_restart_persistence():
    """Full restart persistence: create a watchlist entry, a signal history entry,
    and an alert in one AppTest run; instantiate a fresh AppTest in the same test
    (simulating a process restart) and confirm all three are restored from
    storage.py's SQLite file on load."""
    at1 = AppTest.from_file(APP_PATH, default_timeout=60)
    at1.run()

    # 1. Add a symbol to watchlist
    at1.sidebar.selectbox[0].set_value("Watchlist").run()
    at1.text_input[0].set_value("SOL")
    at1.button[0].click().run()
    assert "SOL" in at1.session_state.watchlist

    # 2. Add an alert
    at1.sidebar.selectbox[0].set_value("Smart Alerts").run()
    at1.text_input[0].set_value("SOL")
    create_btn = [b for b in at1.button if "Create Alert" in b.label][0]
    create_btn.click().run()
    assert any(a["symbol"] == "SOL" for a in at1.session_state.alerts)

    # 3. Add a signal history entry
    now = datetime.now()
    sig_entry = {
        "timestamp": now,
        "symbol": "SOL",
        "signal": "BUY",
        "price": 15000.0,
        "strength": 0.85,
        "timeframe": "1h",
    }
    at1.session_state.signals_history.append(sig_entry)
    storage.save_state("signals_history", at1.session_state.signals_history)

    # Instantiate a fresh AppTest (simulating a clean restart)
    at2 = AppTest.from_file(APP_PATH, default_timeout=60)
    at2.run()

    assert "SOL" in at2.session_state.watchlist, "Watchlist item did not survive process restart"
    assert any(a["symbol"] == "SOL" for a in at2.session_state.alerts), "Alert did not survive process restart"
    assert any(s["symbol"] == "SOL" and s["signal"] == "BUY" for s in at2.session_state.signals_history), "Signal history did not survive process restart"


def test_get_real_time_price_is_cached(monkeypatch):
    """data_fetcher.get_real_time_price is actually cached (call it twice with
    the same symbol within the TTL window and confirm — via a monkeypatched call
    counter on yfinance.Ticker — that the underlying network call only happens once)."""
    import yfinance as yf
    from data_fetcher import DataFetcher

    # Invalidate any prior cache from earlier tests in this pytest run
    DataFetcher.get_real_time_price.clear()

    df = DataFetcher()
    ticker_init_calls = []
    orig_init = yf.Ticker.__init__

    def mock_init(self, ticker, *args, **kwargs):
        if ticker == "DOGE-USD":
            ticker_init_calls.append(ticker)
        orig_init(self, ticker, *args, **kwargs)

    monkeypatch.setattr(yf.Ticker, "__init__", mock_init)

    # Call 1: cold cache, queries yfinance
    p1 = df.get_real_time_price("DOGE")
    assert len(ticker_init_calls) == 1, f"Expected 1 call on cold cache, got {len(ticker_init_calls)}"

    # Call 2: warm cache within 30s TTL, must not trigger new network query
    p2 = df.get_real_time_price("DOGE")
    assert len(ticker_init_calls) == 1, f"Expected cache hit (1 call), got {len(ticker_init_calls)}"
    assert p1["price"] == p2["price"], "Cached price differed between calls"



def test_market_data_source_protocol_structural_subtyping():
    """MarketDataSource Protocol: write a minimal fake implementing its 4 methods
    and confirm `isinstance(fake, MarketDataSource)` is True (structural typing check)."""
    from data_fetcher import MarketDataSource
    import pandas as pd

    class FakeCryptoExchange:
        def get_usd_to_inr_rate(self) -> float:
            return 86.5

        def get_data(self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
            return pd.DataFrame()

        def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> pd.DataFrame:
            return pd.DataFrame()

        def get_real_time_price(self, symbol: str) -> dict:
            return {"symbol": symbol, "price": 100.0, "currency": "INR"}

    fake = FakeCryptoExchange()
    assert isinstance(fake, MarketDataSource), "FakeCryptoExchange failed structural subtyping check against MarketDataSource"

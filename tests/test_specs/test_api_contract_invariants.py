"""
Tests for API Contracts and OpenAPI Response Invariants.
"""

import pytest
from fastapi.testclient import TestClient
from webapp.server import app
from specs.schemas.api_spec import (
    TickerResponseSpec,
    PresetsResponseSpec,
    CandlesResponseSpec,
    ConfluenceResponseSpec,
    SignalResponseSpec,
)


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client."""
    with TestClient(app) as c:
        yield c


def test_openapi_spec_generation(client):
    """SPEC: FastAPI must generate a valid OpenAPI 3.x schema document."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    spec = res.json()
    assert "openapi" in spec
    assert spec["info"]["title"] == "TradeSignal High-Speed Web App"
    assert "/api/candles" in spec["paths"]
    assert "/api/confluence" in spec["paths"]
    assert "/api/presets" in spec["paths"]
    assert "/api/signal" in spec["paths"]
    assert "/api/ticker" in spec["paths"]


def test_api_presets_contract(client):
    """SPEC: /api/presets response must strictly conform to PresetsResponseSpec."""
    res = client.get("/api/presets")
    assert res.status_code == 200
    data = res.json()

    # Validate against formal Pydantic contract
    validated = PresetsResponseSpec.model_validate(data)
    assert "holy_trinity" in validated.presets
    assert "crypto_scalp" in validated.presets
    assert "stock_swing" in validated.presets
    assert "balanced" in validated.presets


def test_api_ticker_contract(client):
    """SPEC: /api/ticker response must strictly conform to TickerResponseSpec."""
    res = client.get("/api/ticker")
    assert res.status_code == 200
    data = res.json()

    validated = TickerResponseSpec.model_validate(data)
    assert len(validated.tickers) > 0
    for item in validated.tickers:
        assert len(item.symbol) > 0
        assert item.price >= 0.0


def test_api_signal_contract(client):
    """SPEC: /api/signal response must strictly conform to SignalResponseSpec."""
    res = client.get("/api/signal?symbol=BTC-USD&timeframe=1h&preset=holy_trinity")
    assert res.status_code == 200
    data = res.json()

    validated = SignalResponseSpec.model_validate(data)
    assert validated.symbol == "BTC-USD"
    assert validated.timeframe == "1h"
    assert validated.signal in ["BUY", "SELL", "HOLD"]
    assert 0.0 <= validated.confidence <= 1.0
    assert validated.price_inr > 0
    assert "IST" in validated.timestamp_ist
    assert validated.strategy_id == "holy_trinity"


def test_api_confluence_contract(client):
    """SPEC: /api/confluence response must strictly conform to ConfluenceResponseSpec."""
    res = client.get("/api/confluence?symbol=BTC-USD&threshold=0.3")
    assert res.status_code == 200
    data = res.json()

    validated = ConfluenceResponseSpec.model_validate(data)
    assert validated.symbol == "BTC-USD"
    assert validated.total_timeframes == 6
    assert 0 <= validated.buy_count <= 6
    assert len(validated.matrix) == 6
    for frame in validated.matrix:
        assert frame.signal in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= frame.strength <= 1.0


def test_api_candles_contract(client):
    """SPEC: /api/candles response must strictly conform to CandlesResponseSpec."""
    res = client.get("/api/candles?symbol=BTC-USD&timeframe=1h&preset=holy_trinity")
    assert res.status_code == 200
    data = res.json()

    validated = CandlesResponseSpec.model_validate(data)
    assert validated.symbol == "BTC-USD"
    assert validated.timeframe == "1h"
    assert validated.current_price > 0
    assert len(validated.candles) > 0
    assert validated.current_signal.signal in ["BUY", "SELL", "HOLD"]
    assert validated.targets.tp >= 0
    assert validated.targets.sl >= 0
    assert len(validated.thesis) > 0

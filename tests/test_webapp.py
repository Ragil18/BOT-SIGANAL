"""Tests for the TradeSignal FastAPI Web Application Backend.
Validates the high-speed endpoints and static file serving without Streamlit.
"""

import pytest
from starlette.testclient import TestClient
from webapp.server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root_serves_html(client):
    """Verify that root / returns the 60 FPS HTML terminal."""
    response = client.get("/")
    assert response.status_code == 200
    assert "TradeSignal" in response.text
    assert "<html" in response.text.lower()


def test_presets_endpoint(client):
    """Verify /api/presets returns the quantitative trading presets."""
    response = client.get("/api/presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert "holy_trinity" in data["presets"]
    assert "balanced" in data["presets"]


def test_ticker_endpoint(client):
    """Verify /api/ticker returns ticker items."""
    response = client.get("/api/ticker")
    assert response.status_code == 200
    data = response.json()
    assert "tickers" in data
    assert isinstance(data["tickers"], list)
    assert len(data["tickers"]) > 0

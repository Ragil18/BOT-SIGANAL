import pytest
import numpy as np
import pandas as pd
from core.regime_classifier import MarketRegimeClassifier, MarketRegime

def test_regime_classifier_init():
    classifier = MarketRegimeClassifier(adx_threshold=25.0, chop_threshold=20.0, volatility_spike_mult=2.0)
    assert classifier.adx_threshold == 25.0
    assert classifier.chop_threshold == 20.0
    assert classifier.volatility_spike_mult == 2.0

def test_regime_classifier_insufficient_data():
    classifier = MarketRegimeClassifier()
    df = pd.DataFrame({
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "volume": [1000, 1200]
    })
    res = classifier.detect_regime(df)
    assert res["regime"] == MarketRegime.CHOPPY_RANGE
    assert res["metrics"]["adx"] == 15.0

def test_regime_classifier_trending_bull():
    classifier = MarketRegimeClassifier(adx_threshold=22.0)
    # Generate 60 candles in a strong upward trend
    np.random.seed(42)
    n = 60
    prices = 100.0 + np.cumsum(np.random.normal(1.5, 0.4, n))
    highs = prices + np.random.uniform(0.5, 1.5, n)
    lows = prices - np.random.uniform(0.5, 1.5, n)
    opens = prices - 0.2
    closes = prices

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": np.random.uniform(1000, 5000, n)
    })
    
    res = classifier.detect_regime(df)
    assert res["regime"] == MarketRegime.TRENDING_BULL
    assert res["rules"]["allow_long"] is True
    assert res["rules"]["allow_short"] is False
    assert res["metrics"]["plus_di"] > res["metrics"]["minus_di"]
    assert res["metrics"]["adx"] >= 20.0

def test_regime_classifier_trending_bear():
    classifier = MarketRegimeClassifier(adx_threshold=22.0)
    # Generate 60 candles in a strong downward trend
    np.random.seed(42)
    n = 60
    prices = 200.0 - np.cumsum(np.random.normal(1.5, 0.4, n))
    highs = prices + np.random.uniform(0.5, 1.5, n)
    lows = prices - np.random.uniform(0.5, 1.5, n)
    opens = prices + 0.2
    closes = prices

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": np.random.uniform(1000, 5000, n)
    })
    
    res = classifier.detect_regime(df)
    assert res["regime"] == MarketRegime.TRENDING_BEAR
    assert res["rules"]["allow_long"] is False
    assert res["rules"]["allow_short"] is True
    assert res["metrics"]["minus_di"] > res["metrics"]["plus_di"]
    assert res["metrics"]["adx"] >= 20.0

def test_regime_classifier_choppy_range():
    classifier = MarketRegimeClassifier(chop_threshold=22.0)
    # Generate 60 oscillating candles around 100
    n = 60
    t = np.linspace(0, 10 * np.pi, n)
    prices = 100.0 + 1.5 * np.sin(t)
    highs = prices + 0.8
    lows = prices - 0.8
    opens = prices - 0.1
    closes = prices

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": [1000] * n
    })

    res = classifier.detect_regime(df)
    assert res["regime"] == MarketRegime.CHOPPY_RANGE
    assert res["rules"]["allow_long"] is True
    assert res["rules"]["allow_short"] is True
    assert res["rules"]["boost_conviction_threshold"] is True
    assert res["metrics"]["adx"] <= 25.0

def test_regime_classifier_volatility_hazard():
    classifier = MarketRegimeClassifier(volatility_spike_mult=2.0)
    # Generate 60 candles with stable range then an extreme 5x spike in range
    n = 60
    prices = [100.0] * n
    highs = [101.0] * n
    lows = [99.0] * n
    opens = [100.0] * n
    closes = [100.0] * n

    # Spike the last candle
    highs[-1] = 130.0
    lows[-1] = 70.0
    closes[-1] = 110.0

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": [1000] * n
    })

    res = classifier.detect_regime(df)
    assert res["regime"] == MarketRegime.VOLATILITY_HAZARD
    assert res["rules"]["allow_auto_pilot"] is False
    assert res["rules"]["risk_multiplier"] == 0.0

def test_regime_api_endpoints():
    from fastapi.testclient import TestClient
    from webapp.server import app

    client = TestClient(app)
    
    # Test dedicated /api/regime endpoint
    reg_res = client.get("/api/regime?symbol=BTC-USD")
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "regime" in reg_data
    assert "label" in reg_data
    assert "strategy_bias" in reg_data
    assert "rules" in reg_data
    assert "metrics" in reg_data
    assert "adx" in reg_data["metrics"]

    # Test /api/candles endpoint includes regime
    c_res = client.get("/api/candles?symbol=BTC-USD&timeframe=1h")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "regime" in c_data
    assert c_data["regime"]["regime"] in [
        MarketRegime.TRENDING_BULL,
        MarketRegime.TRENDING_BEAR,
        MarketRegime.CHOPPY_RANGE,
        MarketRegime.VOLATILITY_HAZARD
    ]

import pytest
import pandas as pd
import numpy as np
from core.ml_predictor import MarketPredictor, FeatureExtractor


def test_feature_extractor():
    n = 50
    df = pd.DataFrame({
        'Open': [100.0 + i for i in range(n)],
        'High': [102.0 + i for i in range(n)],
        'Low': [98.0 + i for i in range(n)],
        'Close': [101.0 + i for i in range(n)],
        'Volume': [1000.0] * n
    }, index=pd.date_range('2026-01-01', periods=n, freq='1h'))

    features, names = FeatureExtractor.extract_features(df)
    assert not features.empty
    assert len(names) > 5
    assert 'norm_atr' in features.columns
    assert 'ret_1' in features.columns


def test_quant_ml_predictor():
    np.random.seed(42)
    n = 60
    base = 100.0 + np.cumsum(np.random.randn(n))
    df = pd.DataFrame({
        'Open': base,
        'High': base + 1.0,
        'Low': base - 1.0,
        'Close': base + 0.5,
        'Volume': np.random.randint(500, 2000, n).astype(float)
    }, index=pd.date_range('2026-01-01', periods=n, freq='1h'))

    predictor = MarketPredictor()
    res = predictor.predict(df, model_type="ml", horizon=3)

    assert res["model_type"] == "ml"
    assert res["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert "probabilities" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert "top_drivers" in res


def test_deep_lstm_predictor():
    np.random.seed(42)
    n = 60
    base = 100.0 + np.cumsum(np.random.randn(n))
    df = pd.DataFrame({
        'Open': base,
        'High': base + 1.0,
        'Low': base - 1.0,
        'Close': base + 0.5,
        'Volume': np.random.randint(500, 2000, n).astype(float)
    }, index=pd.date_range('2026-01-01', periods=n, freq='1h'))

    predictor = MarketPredictor()
    res = predictor.predict(df, model_type="dl", horizon=3)

    assert res["model_type"] == "dl"
    assert res["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert "probabilities" in res
    assert 0.0 <= res["confidence"] <= 1.0

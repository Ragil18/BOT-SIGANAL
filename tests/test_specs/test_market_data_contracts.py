"""
Tests for Market Data Contract and OHLCV Invariants.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from specs.schemas.market_data_spec import MarketDataSpec, MarketDataContractError, validate_ohlcv


@pytest.fixture
def valid_ohlcv_df():
    """Create a synthetically valid OHLCV DataFrame with 50 bars."""
    dates = pd.date_range("2026-10-01 09:15", periods=50, freq="5min", tz="Asia/Kolkata")
    np.random.seed(42)
    base = 100.0
    opens, highs, lows, closes, volumes = [], [], [], [], []
    for _ in range(50):
        o = base + np.random.uniform(-1, 1)
        c = o + np.random.uniform(-1.5, 1.5)
        h = max(o, c) + np.random.uniform(0.1, 1.0)
        l = min(o, c) - np.random.uniform(0.1, 1.0)
        v = np.random.uniform(100, 5000)
        opens.append(o)
        highs.append(h)
        lows.append(l)
        closes.append(c)
        volumes.append(v)
        base = c

    return pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes
    }, index=dates)


def test_valid_ohlcv_passes_spec(valid_ohlcv_df):
    """SPEC: Properly constructed OHLCV data passes without error."""
    is_valid, violations = MarketDataSpec.validate(valid_ohlcv_df, strict=True)
    assert is_valid is True
    assert len(violations) == 0

    validated = validate_ohlcv(valid_ohlcv_df, strict=True)
    assert len(validated) == 50


def test_missing_columns_fails_spec(valid_ohlcv_df):
    """SPEC: DataFrame missing required columns must fail contract."""
    bad_df = valid_ohlcv_df.drop(columns=["High"])
    is_valid, violations = MarketDataSpec.validate(bad_df, strict=True)
    assert is_valid is False
    assert any("Missing required columns" in v for v in violations)

    with pytest.raises(MarketDataContractError):
        validate_ohlcv(bad_df, strict=True)


def test_high_less_than_low_fails_spec(valid_ohlcv_df):
    """SPEC: High < Low violates geometric invariants."""
    bad_df = valid_ohlcv_df.copy()
    bad_df.loc[bad_df.index[5], "High"] = bad_df.loc[bad_df.index[5], "Low"] - 5.0
    
    is_valid, violations = MarketDataSpec.validate(bad_df, strict=True)
    assert is_valid is False
    assert any("High < Low" in v for v in violations)

    with pytest.raises(MarketDataContractError):
        validate_ohlcv(bad_df, strict=True)


def test_negative_volume_fails_spec(valid_ohlcv_df):
    """SPEC: Volume must be non-negative (>= 0)."""
    bad_df = valid_ohlcv_df.copy()
    bad_df.loc[bad_df.index[10], "Volume"] = -50.0

    is_valid, violations = MarketDataSpec.validate(bad_df, strict=True)
    assert is_valid is False
    assert any("negative" in v for v in violations)

    with pytest.raises(MarketDataContractError):
        validate_ohlcv(bad_df, strict=True)


def test_non_monotonic_timestamps_fails_spec(valid_ohlcv_df):
    """SPEC: Timestamp index must be monotonically increasing."""
    bad_df = valid_ohlcv_df.copy()
    idx = list(bad_df.index)
    idx[0], idx[1] = idx[1], idx[0]
    bad_df.index = idx

    is_valid, violations = MarketDataSpec.validate(bad_df, strict=True)
    assert is_valid is False
    assert any("monotonically increasing" in v for v in violations)


def test_non_strict_self_healing(valid_ohlcv_df):
    """SPEC: In non-strict mode, data fetcher self-heals upstream anomalies."""
    bad_df = valid_ohlcv_df.copy()
    bad_df.loc[bad_df.index[2], "High"] = bad_df.loc[bad_df.index[2], "Open"] - 2.0
    bad_df.loc[bad_df.index[3], "Volume"] = -10.0

    healed = validate_ohlcv(bad_df, strict=False)
    assert healed["High"].iloc[2] >= healed["Open"].iloc[2]
    assert healed["Volume"].iloc[3] >= 0.0

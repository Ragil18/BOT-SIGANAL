import sys
from pathlib import Path

# Ensure project root is in sys.path for test discovery
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlcv():
    """Deterministic synthetic OHLCV bars — enough of them (300) that every rolling
    window used across technical_indicators.py, including the 200-period EMA, has
    real (non-NaN) values by the end of the series."""
    n = 300
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    high = close + rng.uniform(0, 1, n)
    low = close - rng.uniform(0, 1, n)
    open_ = close + rng.normal(0, 0.5, n)
    volume = rng.uniform(1000, 5000, n)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )

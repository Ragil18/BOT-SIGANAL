"""
Tests for Causal Invariants and Zero Look-Ahead Bias.
"""

import pytest
import pandas as pd
import numpy as np
from core.technical_indicators import TechnicalIndicators
from core.signal_generator import SignalGenerator


@pytest.fixture
def sample_market_series():
    """Create 100-bar synthetic market data."""
    dates = pd.date_range("2026-10-01 09:15", periods=100, freq="15min", tz="Asia/Kolkata")
    np.random.seed(101)
    base = 50000.0
    opens, highs, lows, closes, volumes = [], [], [], [], []
    for _ in range(100):
        o = base + np.random.uniform(-50, 50)
        c = o + np.random.uniform(-80, 80)
        h = max(o, c) + np.random.uniform(10, 40)
        l = min(o, c) - np.random.uniform(10, 40)
        v = np.random.uniform(500, 2000)
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


def test_zero_lookahead_bias(sample_market_series):
    """SPEC: Zero Look-Ahead Bias.
    Adding future bars (t+1..t+10) must NEVER change signals computed at bar t or earlier.
    """
    ti = TechnicalIndicators()
    sg = SignalGenerator()

    # Past slice: first 80 bars
    df_past = sample_market_series.iloc[:80].copy()
    inds_past = ti.calculate_all(df_past, {})
    sigs_past = sg.generate_signals(df_past, inds_past, threshold=0.3, preset="holy_trinity")

    # Future slice: full 100 bars (appended 20 new bars)
    df_full = sample_market_series.copy()
    inds_full = ti.calculate_all(df_full, {})
    sigs_full = sg.generate_signals(df_full, inds_full, threshold=0.3, preset="holy_trinity")

    # Compare signals on the overlapping window (first 80 bars)
    sigs_past_series = sigs_past['signal'].iloc[-20:]
    sigs_full_slice = sigs_full['signal'].iloc[60:80]

    pd.testing.assert_series_equal(
        sigs_past_series,
        sigs_full_slice,
        check_names=False,
        obj="Past signals when future candles arrive"
    )


def test_signal_generation_is_deterministic(sample_market_series):
    """SPEC: Determinism Invariant.
    Identical inputs must produce bit-for-bit identical outputs across runs.
    """
    ti = TechnicalIndicators()
    sg = SignalGenerator()

    inds1 = ti.calculate_all(sample_market_series, {})
    sigs1 = sg.generate_signals(sample_market_series, inds1, threshold=0.3, preset="holy_trinity")

    inds2 = ti.calculate_all(sample_market_series, {})
    sigs2 = sg.generate_signals(sample_market_series, inds2, threshold=0.3, preset="holy_trinity")

    pd.testing.assert_frame_equal(sigs1, sigs2, obj="Deterministic signal calculation")

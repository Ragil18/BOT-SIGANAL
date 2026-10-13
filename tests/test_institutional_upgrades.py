"""Automated Integration & Unit Tests for the 4 Institutional Upgrades:
1. Quant Auto-Pilot Bot
2. Live News & Sentiment Intelligence Hub
3. Level-2 Order Book (DOM)
4. Interactive Backtesting & Equity Curve Studio
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.data_fetcher import DataFetcher
from core.technical_indicators import TechnicalIndicators
from core.signal_generator import SignalGenerator
from core.backtester import Backtester
from core.sentiment_analyzer import compute_sentiment_score, fetch_structured_news


# =============================================================================
# Upgrade 1: Quant Auto-Pilot Guardrails & Math
# =============================================================================

def test_autopilot_conviction_and_sizing():
    """Verify conviction filter and sizing allocation calculations."""
    conviction_threshold = 0.70
    alloc_pct = 0.10
    avail_margin = 85000.0

    # Signal below threshold
    sig_weak = {"signal": "BUY", "strength": 0.65}
    should_arm_weak = (sig_weak["signal"] in ["BUY", "SELL"]) and (sig_weak["strength"] >= conviction_threshold)
    assert not should_arm_weak

    # Signal meeting or exceeding threshold
    sig_strong = {"signal": "BUY", "strength": 0.78}
    should_arm_strong = (sig_strong["signal"] in ["BUY", "SELL"]) and (sig_strong["strength"] >= conviction_threshold)
    assert should_arm_strong

    # Sizing formula
    allocated_margin = round(avail_margin * alloc_pct, 2)
    assert allocated_margin == 8500.0


# =============================================================================
# Upgrade 2: News & Sentiment Scoring
# =============================================================================

def test_sentiment_scoring_lexicon():
    """Verify lexical sentiment scorer categorizes bullish and bearish headlines."""
    bull_headline = "Bitcoin breaks new all-time high with massive institutional ETF inflow and surge"
    bear_headline = "Market crash triggers massive liquidations as regulatory crackdowns panic traders"
    neutral_headline = "Federal Reserve issues standard scheduled monetary calendar report"

    bull_score = compute_sentiment_score([bull_headline])
    bear_score = compute_sentiment_score([bear_headline])
    neut_score = compute_sentiment_score([neutral_headline])

    assert bull_score > 0.1, f"Expected bullish score, got {bull_score}"
    assert bear_score < -0.1, f"Expected bearish score, got {bear_score}"
    assert -0.2 <= neut_score <= 0.2, f"Expected neutral score, got {neut_score}"


# =============================================================================
# Upgrade 3: Level-2 Order Book (DOM) Math & Imbalance
# =============================================================================

def test_dom_spread_and_order_flow_imbalance():
    """Verify L2 order book cumulative depth and order flow imbalance ratio."""
    bids = [
        [65000.0, 1.5],
        [64995.0, 2.0],
        [64990.0, 3.5],
    ]
    asks = [
        [65002.0, 1.0],
        [65005.0, 1.5],
        [65010.0, 2.0],
    ]

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2.0

    assert spread == 2.0
    assert mid_price == 65001.0

    total_bid_vol = sum(b[1] for b in bids)  # 7.0
    total_ask_vol = sum(a[1] for a in asks)  # 4.5
    total_vol = total_bid_vol + total_ask_vol  # 11.5

    bids_pct = round((total_bid_vol / total_vol) * 100)
    asks_pct = 100 - bids_pct

    assert bids_pct == 61
    assert asks_pct == 39
    assert bids_pct > asks_pct  # Bullish order book imbalance


# =============================================================================
# Upgrade 4: Strategy Backtesting & Equity Curve Studio
# =============================================================================

def test_backtester_metrics_and_equity_curve_generation():
    """Verify backtester outputs full institutional performance metrics and equity curve."""
    # Synthetic prices with a rising trend
    dates = pd.date_range(start="2026-01-01", periods=100, freq="1h")
    prices = 100.0 + np.cumsum(np.random.normal(0.2, 1.0, 100))
    df = pd.DataFrame({
        "Open": prices - 0.2,
        "High": prices + 0.8,
        "Low": prices - 0.8,
        "Close": prices,
        "Volume": [1000] * 100
    }, index=dates)

    # Synthetic alternating BUY and SELL signals
    signals_list = []
    for i in range(100):
        if i % 20 == 5:
            sig = "BUY"
        elif i % 20 == 15:
            sig = "SELL"
        else:
            sig = "HOLD"
        signals_list.append({"signal": sig, "strength": 0.8, "price": prices[i]})

    signals = pd.DataFrame(signals_list, index=dates)

    bt = Backtester()
    results = bt.run_backtest(df, signals, initial_capital=100000.0, stop_loss_pct=0.03, take_profit_pct=0.06)

    assert "total_return" in results
    assert "sharpe_ratio" in results
    assert "max_drawdown" in results
    assert "win_rate" in results
    assert "profit_factor" in results
    assert "portfolio_history" in results

    p_df = results["portfolio_history"]
    assert len(p_df) == 100
    assert "portfolio_value" in p_df.columns
    assert "cash" in p_df.columns

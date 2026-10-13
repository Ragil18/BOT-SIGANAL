"""Market Regime Classifier for TradeSignal Institutional Quant Platform

Classifies real-time market conditions into 4 distinct macro regimes:
1. TRENDING_BULL: Strong directional uptrend (Long-only bias, trail profits)
2. TRENDING_BEAR: Strong directional downtrend (Short-only bias, avoid dip catching)
3. CHOPPY_RANGE: Low directional conviction / mean reversion (Fade extremes, boost conviction threshold)
4. VOLATILITY_HAZARD: Black swan / liquidation cascades / news spike (Disarm auto-pilot, capital preservation)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class MarketRegime:
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    CHOPPY_RANGE = "CHOPPY_RANGE"
    VOLATILITY_HAZARD = "VOLATILITY_HAZARD"


class MarketRegimeClassifier:
    """Quantitative Market Structure & Regime Engine."""

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 23.0,
        trend_threshold: float = 23.0,
        chop_threshold: float = 20.0,
        hazard_multiplier: float = 2.0,
        volatility_spike_mult: float = 2.0
    ):
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold or trend_threshold
        self.trend_threshold = trend_threshold
        self.chop_threshold = chop_threshold
        self.hazard_multiplier = hazard_multiplier or volatility_spike_mult
        self.volatility_spike_mult = volatility_spike_mult or hazard_multiplier

    def _get_col(self, df: pd.DataFrame, col_name: str) -> pd.Series:
        for c in [col_name.capitalize(), col_name.lower(), col_name.upper()]:
            if c in df.columns:
                return df[c]
        raise KeyError(f"Column {col_name} not found in dataframe")

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Welles Wilder's ADX, +DI, and -DI."""
        high = self._get_col(df, 'high')
        low = self._get_col(df, 'low')
        close = self._get_col(df, 'close')
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        # Wilder's smoothing (alpha = 1/period)
        tr_smooth = tr.ewm(alpha=1.0 / period, adjust=False).mean()
        plus_dm_smooth = pd.Series(plus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean()
        minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean()

        tr_smooth_safe = tr_smooth.replace(0, np.nan)
        plus_di = 100.0 * (plus_dm_smooth / tr_smooth_safe)
        minus_di = 100.0 * (minus_dm_smooth / tr_smooth_safe)

        di_sum = plus_di + minus_di
        di_diff = (plus_di - minus_di).abs()
        dx = 100.0 * (di_diff / di_sum.replace(0, np.nan))
        adx = dx.ewm(alpha=1.0 / period, adjust=False).mean()

        return pd.DataFrame({
            'adx': adx.fillna(0),
            'plus_di': plus_di.fillna(0),
            'minus_di': minus_di.fillna(0),
            'tr': tr
        }, index=df.index)

    def detect_regime(self, df: pd.DataFrame, indicators: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Detect current market regime from OHLCV and technical indicators."""
        if df.empty or len(df) < 20:
            return self._default_regime("Insufficient historical data")

        # 1. ADX and Directional Indicators
        dmi = self.calculate_adx(df, period=self.adx_period)
        latest_adx = float(dmi['adx'].iloc[-1])
        latest_plus_di = float(dmi['plus_di'].iloc[-1])
        latest_minus_di = float(dmi['minus_di'].iloc[-1])

        # 2. Moving Average Alignment (Trend Filter)
        close = self._get_col(df, 'close')
        ema_20 = close.ewm(span=20, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        cur_price = float(close.iloc[-1])
        cur_ema20 = float(ema_20.iloc[-1])
        cur_ema50 = float(ema_50.iloc[-1])

        bull_alignment = (cur_price >= cur_ema20) and (cur_ema20 >= cur_ema50)
        bear_alignment = (cur_price <= cur_ema20) and (cur_ema20 <= cur_ema50)

        # 3. Volatility Hazard / Ratio (ATR & Bollinger Band Width)
        tr = dmi['tr']
        atr = tr.rolling(14).mean()
        atr_mean = atr.rolling(min(50, len(df))).mean()
        cur_atr = float(atr.iloc[-1]) if not atr.empty else 0.0
        cur_atr_mean = float(atr_mean.iloc[-1]) if not atr_mean.empty and not pd.isna(atr_mean.iloc[-1]) else cur_atr
        vol_ratio = (cur_atr / cur_atr_mean) if cur_atr_mean > 0 else 1.0

        # Bollinger Band Width
        roll_mean = close.rolling(20).mean()
        roll_std = close.rolling(20).std()
        bb_width = (4.0 * roll_std) / roll_mean.replace(0, np.nan) * 100.0
        cur_bb_width = float(bb_width.iloc[-1]) if not bb_width.empty and not pd.isna(bb_width.iloc[-1]) else 5.0

        # Recent 3-bar absolute returns
        recent_3bar_ret = abs(float((close.iloc[-1] - close.iloc[-3]) / close.iloc[-3])) if len(close) >= 3 else 0.0

        # 4. Classification Decision Logic
        regime = MarketRegime.CHOPPY_RANGE
        label = "Choppy Consolidation"
        description = "Sideways oscillation within defined boundaries. Fade extremes and tighten risk."
        confidence = 0.70
        vol_state = "NORMAL"
        strategy_bias = "Mean Reversion (Fade Extremes)"
        allow_long = True
        allow_short = True
        allow_auto_pilot = True
        boost_conviction = True
        risk_multiplier = 0.8
        min_conviction_boost = 0.05
        recommended_preset = "crypto_scalp"

        # Check Volatility Hazard Condition (Black swan / extreme shakeout)
        spike_limit = max(self.hazard_multiplier, self.volatility_spike_mult)
        if vol_ratio >= spike_limit or recent_3bar_ret >= 0.08:
            regime = MarketRegime.VOLATILITY_HAZARD
            label = "High Volatility Hazard"
            description = "Extreme volatility spike detected. High risk of liquidation cascades or slippage."
            vol_state = "EXTREME_EXPANSION"
            confidence = min(0.95, round(0.70 + (vol_ratio - spike_limit) * 0.15, 2))
            strategy_bias = "Capital Preservation (Pause Entries)"
            allow_long = False
            allow_short = False
            allow_auto_pilot = False
            boost_conviction = True
            risk_multiplier = 0.0
            min_conviction_boost = 0.15
            recommended_preset = "PAUSE"

        # Check Strong Bull Trend
        elif (latest_adx >= self.adx_threshold) and (latest_plus_di > latest_minus_di) and (cur_price >= cur_ema50 * 0.99):
            regime = MarketRegime.TRENDING_BULL
            label = "Strong Bullish Expansion"
            description = "Persistent directional upward momentum with dominant buyer pressure."
            vol_state = "HIGH_MOMENTUM" if vol_ratio > 1.3 else "NORMAL"
            confidence = min(0.95, round(0.65 + (latest_adx / 100.0) * 0.4, 2))
            strategy_bias = "Long Only (Trend Following)"
            allow_long = True
            allow_short = False  # Filter out counter-trend shorts in a bull run
            allow_auto_pilot = True
            boost_conviction = False
            risk_multiplier = 1.0
            min_conviction_boost = 0.00
            recommended_preset = "holy_trinity"

        # Check Strong Bear Trend
        elif (latest_adx >= self.adx_threshold) and (latest_minus_di > latest_plus_di) and (cur_price <= cur_ema50 * 1.01):
            regime = MarketRegime.TRENDING_BEAR
            label = "Strong Bearish Contraction"
            description = "Persistent directional downward momentum with dominant seller liquidation."
            vol_state = "HIGH_MOMENTUM" if vol_ratio > 1.3 else "NORMAL"
            confidence = min(0.95, round(0.65 + (latest_adx / 100.0) * 0.4, 2))
            strategy_bias = "Short Only (Breakdown Entries)"
            allow_long = False  # Filter out counter-trend longs catching knives
            allow_short = True
            allow_auto_pilot = True
            boost_conviction = False
            risk_multiplier = 1.0
            min_conviction_boost = 0.00
            recommended_preset = "stock_swing"

        # Consolidation / Chop Range
        else:
            regime = MarketRegime.CHOPPY_RANGE
            label = "Range-Bound Consolidation"
            description = "Sideways oscillation with low trend conviction. Favour mean reversion or wait for breakout."
            vol_state = "LOW_COMPRESSION" if cur_bb_width < 3.0 else "NORMAL"
            confidence = min(0.85, round(0.60 + ((self.adx_threshold - latest_adx) / max(self.adx_threshold, 1.0)) * 0.25, 2))
            strategy_bias = "Mean Reversion (Fade Bands)"
            allow_long = True
            allow_short = True
            allow_auto_pilot = True
            boost_conviction = True
            risk_multiplier = 0.8
            min_conviction_boost = 0.05
            recommended_preset = "crypto_scalp"

        # Drivers explanation
        drivers = [
            f"ADX = {latest_adx:.1f} ({'Strong Trend' if latest_adx >= self.adx_threshold else 'Weak/Choppy Trend'})",
            f"Direction: +DI {latest_plus_di:.1f} vs -DI {latest_minus_di:.1f}",
            f"MA Stack: {'Bullish (Price > EMA20 > EMA50)' if bull_alignment else ('Bearish (Price < EMA20 < EMA50)' if bear_alignment else 'Neutral Mixed')}",
            f"Volatility Ratio: {vol_ratio:.2f}x average ATR"
        ]

        rules = {
            "allow_long": allow_long,
            "allow_short": allow_short,
            "allow_auto_pilot": allow_auto_pilot,
            "boost_conviction_threshold": boost_conviction,
            "risk_multiplier": risk_multiplier,
            "min_conviction_boost": min_conviction_boost,
            "recommended_preset": recommended_preset
        }

        metrics = {
            "adx": round(latest_adx, 1),
            "plus_di": round(latest_plus_di, 1),
            "minus_di": round(latest_minus_di, 1),
            "atr_expansion": round(vol_ratio, 2),
            "bb_width": round(cur_bb_width, 2)
        }

        return {
            "regime": regime,
            "label": label,
            "regime_title": label,
            "description": description,
            "confidence": confidence,
            "strategy_bias": strategy_bias,
            "recommended_action": strategy_bias,
            "volatility_state": vol_state,
            "volatility_ratio": round(vol_ratio, 2),
            "rules": rules,
            "auto_pilot_rules": rules,
            "metrics": metrics,
            "drivers": drivers
        }

    def _default_regime(self, reason: str) -> Dict[str, Any]:
        rules = {
            "allow_long": True,
            "allow_short": True,
            "allow_auto_pilot": True,
            "boost_conviction_threshold": True,
            "risk_multiplier": 0.8,
            "min_conviction_boost": 0.05,
            "recommended_preset": "holy_trinity"
        }
        metrics = {
            "adx": 15.0,
            "plus_di": 20.0,
            "minus_di": 20.0,
            "atr_expansion": 1.0,
            "bb_width": 4.0
        }
        return {
            "regime": MarketRegime.CHOPPY_RANGE,
            "label": "Neutral Range",
            "regime_title": "Neutral Range",
            "description": "Insufficient historical candles; defaulting to neutral parameters.",
            "confidence": 0.50,
            "strategy_bias": "Neutral / Hold",
            "recommended_action": "Neutral / Hold",
            "volatility_state": "NORMAL",
            "volatility_ratio": 1.0,
            "rules": rules,
            "auto_pilot_rules": rules,
            "metrics": metrics,
            "drivers": [reason]
        }

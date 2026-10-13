"""
Market Data Contract Specification.
Defines formal invariants and schemas for ingested OHLCV market data.
"""

from typing import Tuple, List
import pandas as pd
import numpy as np


class MarketDataContractError(ValueError):
    """Raised when market data violates formal OHLCV schema invariants."""
    pass


class MarketDataSpec:
    """Formal specifications and invariants for OHLCV Market Data."""
    REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
    REQUIRED_TIMEZONE = "Asia/Kolkata"

    @classmethod
    def validate(cls, df: pd.DataFrame, strict: bool = True) -> Tuple[bool, List[str]]:
        """Validate DataFrame against formal OHLCV contract invariants.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations: List[str] = []

        if df is None or not isinstance(df, pd.DataFrame):
            return False, ["Input is not a valid pandas DataFrame"]

        if df.empty:
            return False, ["DataFrame is empty (0 candles)"]

        # 1. Required Columns Invariant
        missing = [col for col in cls.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            violations.append(f"Missing required columns: {missing}")

        # If required columns are missing, we cannot evaluate price invariants safely
        if missing:
            return False, violations

        # 2. Datetime Index & Monotonicity Invariant
        if not isinstance(df.index, pd.DatetimeIndex):
            violations.append(f"Index must be a pd.DatetimeIndex, got {type(df.index).__name__}")
        else:
            if not df.index.is_monotonic_increasing:
                violations.append("Timestamp index is not monotonically increasing")
            
            # Check duplicate timestamps
            if df.index.has_duplicates:
                violations.append(f"Found {df.index.duplicated().sum()} duplicate timestamps in index")

        # 3. Price Positivity Invariants
        price_cols = ["Open", "High", "Low", "Close"]
        for col in price_cols:
            non_positive = (df[col] <= 0).sum()
            if non_positive > 0:
                violations.append(f"Column '{col}' has {non_positive} non-positive (<=0) price values")

        # 4. Volume Non-Negativity Invariant
        neg_vol = (df["Volume"] < 0).sum()
        if neg_vol > 0:
            violations.append(f"Volume has {neg_vol} negative (<0) values")

        # 5. Candlestick Spread Geometry Invariants
        # Allow tiny epsilon for float precision
        eps = 1e-5
        invalid_hl = (df["High"] < df["Low"] - eps).sum()
        if invalid_hl > 0:
            violations.append(f"High < Low violation in {invalid_hl} candles")

        invalid_ho = (df["High"] < df["Open"] - eps).sum()
        if invalid_ho > 0:
            violations.append(f"High < Open violation in {invalid_ho} candles")

        invalid_hc = (df["High"] < df["Close"] - eps).sum()
        if invalid_hc > 0:
            violations.append(f"High < Close violation in {invalid_hc} candles")

        invalid_lo = (df["Low"] > df["Open"] + eps).sum()
        if invalid_lo > 0:
            violations.append(f"Low > Open violation in {invalid_lo} candles")

        invalid_lc = (df["Low"] > df["Close"] + eps).sum()
        if invalid_lc > 0:
            violations.append(f"Low > Close violation in {invalid_lc} candles")

        # 6. NaN or Inf Invariants
        nan_counts = df[cls.REQUIRED_COLUMNS].isna().sum().to_dict()
        bad_nans = {k: v for k, v in nan_counts.items() if v > 0}
        if bad_nans:
            violations.append(f"Found NaN values in OHLCV columns: {bad_nans}")

        is_valid = len(violations) == 0
        return is_valid, violations


def validate_ohlcv(df: pd.DataFrame, strict: bool = True) -> pd.DataFrame:
    """Validate DataFrame against MarketDataSpec.
    
    If strict=True, raises MarketDataContractError on violation.
    If strict=False, attempts deterministic self-healing (clamping High/Low, dropping NaNs).
    
    Returns:
        The validated (and sanitized if strict=False) DataFrame.
    """
    if df is None or df.empty:
        return df

    is_valid, violations = MarketDataSpec.validate(df, strict=strict)
    if is_valid:
        return df

    if strict:
        raise MarketDataContractError(
            f"Market data failed spec contract validation with {len(violations)} violations:\n - "
            + "\n - ".join(violations)
        )

    # Self-healing fallback mode for upstream provider noise
    sanitized = df.copy()
    sanitized = sanitized.dropna(subset=[col for col in MarketDataSpec.REQUIRED_COLUMNS if col in sanitized.columns])
    
    if "High" in sanitized and "Low" in sanitized and "Open" in sanitized and "Close" in sanitized:
        sanitized["High"] = sanitized[["High", "Low", "Open", "Close"]].max(axis=1)
        sanitized["Low"] = sanitized[["High", "Low", "Open", "Close"]].min(axis=1)

    if "Volume" in sanitized:
        sanitized["Volume"] = sanitized["Volume"].clip(lower=0.0)

    if isinstance(sanitized.index, pd.DatetimeIndex) and not sanitized.index.is_monotonic_increasing:
        sanitized = sanitized.sort_index()

    return sanitized

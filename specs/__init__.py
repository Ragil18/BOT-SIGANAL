"""
Specs Package - Spec-Driven Development (SDD) Foundation for TradeSignal.
Contains formal schemas, contracts, declarative strategies, and API specifications.
"""

from specs.schemas.market_data_spec import MarketDataSpec, validate_ohlcv
from specs.schemas.strategy_spec import StrategySpec, load_strategy_spec, load_all_strategy_specs
from specs.schemas.api_spec import (
    CandleItemSpec,
    CandlesResponseSpec,
    ConfluenceResponseSpec,
    SignalResponseSpec,
    TickerResponseSpec,
    PresetsResponseSpec,
)

__all__ = [
    "MarketDataSpec",
    "validate_ohlcv",
    "StrategySpec",
    "load_strategy_spec",
    "load_all_strategy_specs",
    "CandleItemSpec",
    "CandlesResponseSpec",
    "ConfluenceResponseSpec",
    "SignalResponseSpec",
    "TickerResponseSpec",
    "PresetsResponseSpec",
]

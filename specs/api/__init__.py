"""
API Specifications module for FastAPI endpoints.
"""

from specs.schemas.api_spec import (
    CandleItemSpec,
    CandlesResponseSpec,
    ConfluenceItemSpec,
    ConfluenceResponseSpec,
    TickerItemSpec,
    TickerResponseSpec,
    PresetItemSpec,
    PresetsResponseSpec,
    SignalResponseSpec,
)

__all__ = [
    "CandleItemSpec",
    "CandlesResponseSpec",
    "ConfluenceItemSpec",
    "ConfluenceResponseSpec",
    "TickerItemSpec",
    "TickerResponseSpec",
    "PresetItemSpec",
    "PresetsResponseSpec",
    "SignalResponseSpec",
]

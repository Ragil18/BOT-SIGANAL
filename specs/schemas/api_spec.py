"""
API Contract Specification.
Defines typed Pydantic request and response contracts for the FastAPI Web Server.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class CandleItemSpec(BaseModel):
    """TradingView candlestick bar format."""
    time: int = Field(..., description="Unix timestamp in seconds")
    open: float = Field(..., gt=0.0)
    high: float = Field(..., gt=0.0)
    low: float = Field(..., gt=0.0)
    close: float = Field(..., gt=0.0)


class VolumeItemSpec(BaseModel):
    """TradingView volume histogram bar."""
    time: int
    value: float = Field(..., ge=0.0)
    color: str


class MarkerItemSpec(BaseModel):
    """TradingView BUY/SELL trigger marker."""
    time: int
    position: Literal["belowBar", "aboveBar"]
    color: str
    shape: Literal["arrowUp", "arrowDown", "circle"]
    text: str
    size: int = 2


class SignalCardSpec(BaseModel):
    """Active quantitative signal decision card."""
    signal: Literal["BUY", "SELL", "HOLD"] = "HOLD"
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    score: float = Field(default=0.0)


class RiskTargetsSpec(BaseModel):
    """Dynamic risk targets (ATR-based)."""
    tp: float = Field(default=0.0, ge=0.0)
    sl: float = Field(default=0.0, ge=0.0)
    atr: Optional[float] = None
    rr_ratio: Optional[str] = "2.5 : 1"


class MLProbabilitySpec(BaseModel):
    """Probability breakdown for direction."""
    bullish: float = Field(..., ge=0.0, le=1.0)
    bearish: float = Field(..., ge=0.0, le=1.0)
    neutral: float = Field(..., ge=0.0, le=1.0)


class MLTopDriverSpec(BaseModel):
    """Factor driver contributing to prediction."""
    factor: str
    magnitude: float
    impact: str


class MLPredictionSpec(BaseModel):
    """Predictive Machine Learning & Deep Learning Contract."""
    model_type: Literal["ml", "dl"] = "ml"
    model_name: str
    horizon_candles: int = 3
    sequence_window: Optional[int] = None
    direction: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    expected_return_pct: float
    probabilities: MLProbabilitySpec
    top_drivers: List[MLTopDriverSpec] = Field(default_factory=list)
    training_accuracy: Optional[float] = None
    statistical_edge: Optional[str] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None


class CandlesResponseSpec(BaseModel):
    """Full API contract for /api/candles endpoint."""
    symbol: str
    timeframe: str
    current_price: float = Field(..., ge=0.0)
    candles: List[CandleItemSpec]
    volume: List[VolumeItemSpec]
    markers: List[MarkerItemSpec]
    current_signal: SignalCardSpec
    targets: RiskTargetsSpec
    thesis: str
    preset: Optional[str] = "holy_trinity"
    preset_info: Optional[Dict[str, Any]] = None
    available_presets: Optional[Dict[str, Any]] = None
    ml_prediction: Optional[MLPredictionSpec] = None
    regime: Optional[Dict[str, Any]] = None


class ConfluenceItemSpec(BaseModel):
    """Single timeframe confluence state."""
    timeframe: str
    signal: Literal["BUY", "SELL", "HOLD"]
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    score: float = 0.0


class ConfluenceResponseSpec(BaseModel):
    """Full API contract for /api/confluence endpoint."""
    symbol: str
    verdict: str
    verdict_badge: str
    color: str
    advice: Optional[str] = None
    buy_count: int = Field(..., ge=0)
    total_timeframes: int = Field(..., gt=0)
    matrix: List[ConfluenceItemSpec]


class TickerItemSpec(BaseModel):
    """Ticker item for live banner."""
    symbol: str
    full_symbol: str
    name: str
    price: float = Field(..., ge=0.0)
    change_pct: float


class TickerResponseSpec(BaseModel):
    """Full API contract for /api/ticker endpoint."""
    tickers: List[TickerItemSpec]


class PresetItemSpec(BaseModel):
    """Strategy preset detail."""
    name: str
    description: str
    indicators: List[str]
    weights: Dict[str, float]
    params: Dict[str, Any] = Field(default_factory=dict)
    threshold: Optional[float] = 0.30
    target_timeframes: Optional[List[str]] = Field(default_factory=list)


class PresetsResponseSpec(BaseModel):
    """Full API contract for /api/presets endpoint."""
    presets: Dict[str, PresetItemSpec]


class SignalResponseSpec(BaseModel):
    """Full API contract for dedicated /api/signal endpoint."""
    symbol: str
    timeframe: str
    timestamp_ist: str
    signal: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    price_inr: float = Field(..., ge=0.0)
    target_price_inr: float = Field(..., ge=0.0)
    stop_loss_inr: float = Field(..., ge=0.0)
    strategy_id: str
    rationale: str

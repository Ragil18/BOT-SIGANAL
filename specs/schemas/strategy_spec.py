"""
Strategy Specification Schema.
Defines formal declarative contracts for trading strategy presets.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class IndicatorParamSpec(BaseModel):
    """Specification of an indicator configuration."""
    name: str
    weight: float = Field(default=0.1, ge=0.0, le=1.0)
    params: Dict[str, Any] = Field(default_factory=dict)


class RiskManagementSpec(BaseModel):
    """Risk and execution parameters for a strategy."""
    tp_atr_multiplier: float = Field(default=2.5, gt=0.0)
    sl_atr_multiplier: float = Field(default=1.5, gt=0.0)
    max_risk_pct: float = Field(default=0.02, gt=0.0, le=0.10)
    trailing_stop: bool = Field(default=False)


class StrategySpec(BaseModel):
    """Formal Strategy Specification Contract."""
    strategy_id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    target_timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h", "1d"])
    entry_threshold: float = Field(default=0.30, ge=0.05, le=0.95)
    indicators: List[str] = Field(..., min_length=1)
    weights: Dict[str, float] = Field(...)
    params: Dict[str, Any] = Field(default_factory=dict)
    risk: RiskManagementSpec = Field(default_factory=RiskManagementSpec)

    @field_validator("weights")
    @classmethod
    def validate_weights_non_negative(cls, v: Dict[str, float]) -> Dict[str, float]:
        for k, weight in v.items():
            if weight < 0.0 or weight > 1.0:
                raise ValueError(f"Indicator weight for '{k}' must be between 0.0 and 1.0, got {weight}")
        return v

    @model_validator(mode="after")
    def validate_indicators_match_weights(self) -> "StrategySpec":
        """Spec invariant: Each indicator listed in weights must be declared in indicators."""
        for k in self.weights:
            if k not in self.indicators:
                raise ValueError(f"Weight assigned to undeclared indicator '{k}'. Available: {self.indicators}")
        return self

    def to_preset_dict(self) -> Dict[str, Any]:
        """Convert formal specification to legacy preset dictionary format for runtime compatibility."""
        return {
            "name": self.name,
            "description": self.description,
            "indicators": list(self.indicators),
            "weights": dict(self.weights),
            "params": dict(self.params),
            "threshold": self.entry_threshold,
            "target_timeframes": list(self.target_timeframes),
            "risk": self.risk.model_dump(),
        }


def get_strategies_dir() -> Path:
    """Resolve directory containing strategy YAML files."""
    return Path(__file__).resolve().parent.parent / "strategies"


def load_strategy_spec(strategy_id: str, strategies_dir: Optional[Path] = None) -> StrategySpec:
    """Load and validate a StrategySpec from YAML by strategy_id."""
    folder = strategies_dir or get_strategies_dir()
    filepath = folder / f"{strategy_id}.yaml"
    if not filepath.exists():
        raise FileNotFoundError(f"Strategy spec not found at: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid strategy specification format in {filepath}")

    # Ensure strategy_id is present
    if "strategy_id" not in data:
        data["strategy_id"] = strategy_id

    return StrategySpec.model_validate(data)


def load_all_strategy_specs(strategies_dir: Optional[Path] = None) -> Dict[str, StrategySpec]:
    """Load and validate all StrategySpecs found in strategies directory."""
    folder = strategies_dir or get_strategies_dir()
    specs: Dict[str, StrategySpec] = {}
    if not folder.exists():
        return specs

    for yaml_file in sorted(folder.glob("*.yaml")):
        strat_id = yaml_file.stem
        try:
            specs[strat_id] = load_strategy_spec(strat_id, folder)
        except Exception as e:
            print(f"Warning: Failed to load strategy spec {yaml_file.name}: {e}")

    return specs

"""
Tests for Strategy Specifications and YAML Contracts.
"""

import pytest
from pydantic import ValidationError
from specs.schemas.strategy_spec import (
    StrategySpec,
    load_strategy_spec,
    load_all_strategy_specs,
    get_strategies_dir,
)
from core.signal_generator import SignalGenerator


def test_all_yaml_strategy_files_valid():
    """SPEC: Every YAML file in specs/strategies/ must parse and validate against StrategySpec."""
    strategies_dir = get_strategies_dir()
    assert strategies_dir.exists(), "specs/strategies/ directory does not exist"

    specs = load_all_strategy_specs(strategies_dir)
    assert len(specs) >= 4, f"Expected at least 4 strategy specs, found {len(specs)}"

    expected = ["holy_trinity", "crypto_scalp", "stock_swing", "balanced"]
    for strat_id in expected:
        assert strat_id in specs, f"Missing required strategy spec '{strat_id}'"
        spec = specs[strat_id]
        assert isinstance(spec, StrategySpec)
        assert len(spec.name) >= 3
        assert len(spec.description) >= 10
        assert spec.risk.tp_atr_multiplier > 0
        assert spec.risk.sl_atr_multiplier > 0
        assert 0.05 <= spec.entry_threshold <= 0.95


def test_strategy_spec_rejects_negative_weight():
    """SPEC: Indicator weights must be non-negative (>= 0.0)."""
    with pytest.raises(ValidationError):
        StrategySpec(
            strategy_id="invalid_neg",
            name="Invalid Negative Weight",
            description="Testing negative weight validation error",
            indicators=["rsi", "macd"],
            weights={"rsi": -0.2, "macd": 0.5}
        )


def test_strategy_spec_rejects_weight_over_one():
    """SPEC: Individual indicator weights must not exceed 1.0."""
    with pytest.raises(ValidationError):
        StrategySpec(
            strategy_id="invalid_large",
            name="Invalid Weight Over 1",
            description="Testing excessive weight validation error",
            indicators=["rsi"],
            weights={"rsi": 1.5}
        )


def test_strategy_spec_rejects_undeclared_indicator():
    """SPEC: All weighted indicators must be explicitly declared in indicators list."""
    with pytest.raises(ValidationError):
        StrategySpec(
            strategy_id="undeclared_test",
            name="Undeclared Indicator Test",
            description="Testing undeclared indicator weight validation error",
            indicators=["rsi"],
            weights={"rsi": 0.5, "bollinger": 0.5}
        )


def test_signal_generator_loads_specs():
    """SPEC: SignalGenerator.PRESETS is populated from verified StrategySpecs."""
    sg = SignalGenerator()
    for strat_id in ["holy_trinity", "crypto_scalp", "stock_swing", "balanced"]:
        assert strat_id in sg.PRESETS
        preset = sg.PRESETS[strat_id]
        assert "name" in preset
        assert "weights" in preset
        assert "description" in preset

        spec = sg.get_strategy_spec(strat_id)
        assert spec is not None
        assert spec.strategy_id == strat_id

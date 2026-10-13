"""
Unit tests for Quant Auto-Pilot Bot:
- Signal Conviction Threshold Evaluation
- Multi-Asset Risk Guardrails (Max Positions, Margin Sizing)
- Daily Drawdown Circuit Breaker / Kill-Switch
- Dynamic ATR-Target Construction
- Duplicate Entry Prevention & Direction Reversal
"""

import pytest


def evaluate_auto_pilot_signal(signal: str, score: float, min_threshold: float = 0.70) -> bool:
    """Evaluate if an algorithmic signal meets conviction threshold for autonomous execution."""
    if signal not in ("BUY", "SELL"):
        return False
    return score >= min_threshold


def check_risk_guardrails(
    open_positions: int,
    max_positions: int,
    current_daily_drawdown_pct: float,
    max_daily_drawdown_limit_pct: float,
    available_margin: float,
    min_order_margin: float = 100.0
) -> tuple[bool, str]:
    """Check institutional risk rules before allowing auto-pilot order placement."""
    if current_daily_drawdown_pct >= max_daily_drawdown_limit_pct:
        return False, "CIRCUIT_BREAKER_TRIGGERED"
    if open_positions >= max_positions:
        return False, "MAX_POSITIONS_REACHED"
    if available_margin < min_order_margin:
        return False, "INSUFFICIENT_MARGIN"
    return True, "APPROVED"


def calc_auto_order_parameters(
    balance: float,
    allocation_pct: float,
    leverage: int,
    current_price: float,
    atr_val: float,
    side: str,
    tp_multiplier: float = 2.0,
    sl_multiplier: float = 1.5
) -> dict:
    """Compute autonomous order sizing and dynamic ATR TP/SL targets."""
    margin = balance * allocation_pct
    notional = margin * leverage
    qty = notional / current_price
    
    if side == "BUY":
        tp = current_price + (tp_multiplier * atr_val)
        sl = current_price - (sl_multiplier * atr_val)
    else:
        tp = current_price - (tp_multiplier * atr_val)
        sl = current_price + (sl_multiplier * atr_val)
        
    return {
        "margin": round(margin, 2),
        "notional": round(notional, 2),
        "qty": round(qty, 6),
        "tp": round(tp, 2),
        "sl": round(sl, 2)
    }


def should_reenter_symbol(active_positions: list[dict], symbol: str, new_side: str) -> tuple[bool, str]:
    """Prevent double-entering the same asset or trigger smart reversal."""
    for pos in active_positions:
        if pos["symbol"] == symbol:
            if pos["side"] == new_side:
                return False, "ALREADY_ACTIVE_SAME_SIDE"
            else:
                return True, "REVERSE_EXISTING_POSITION"
    return True, "NEW_ENTRY"


# ==============================================================================
# TESTS
# ==============================================================================

def test_signal_conviction_threshold():
    # 65% is below 70% threshold -> Skip
    assert not evaluate_auto_pilot_signal("BUY", 0.65, min_threshold=0.70)
    # 75% meets 70% threshold -> Execute
    assert evaluate_auto_pilot_signal("BUY", 0.75, min_threshold=0.70)
    # 82% meets 80% threshold -> Execute
    assert evaluate_auto_pilot_signal("SELL", 0.82, min_threshold=0.80)
    # HOLD signal never triggers auto-execution
    assert not evaluate_auto_pilot_signal("HOLD", 0.95, min_threshold=0.70)


def test_risk_guardrails_circuit_breaker():
    # Normal state passes
    allowed, reason = check_risk_guardrails(
        open_positions=1,
        max_positions=3,
        current_daily_drawdown_pct=1.2,
        max_daily_drawdown_limit_pct=3.0,
        available_margin=50000.0
    )
    assert allowed
    assert reason == "APPROVED"

    # Circuit breaker triggers when daily drawdown exceeds 3%
    allowed, reason = check_risk_guardrails(
        open_positions=1,
        max_positions=3,
        current_daily_drawdown_pct=3.5,
        max_daily_drawdown_limit_pct=3.0,
        available_margin=50000.0
    )
    assert not allowed
    assert reason == "CIRCUIT_BREAKER_TRIGGERED"


def test_risk_guardrails_max_positions():
    # Blocks new entry when max concurrent positions (3) reached
    allowed, reason = check_risk_guardrails(
        open_positions=3,
        max_positions=3,
        current_daily_drawdown_pct=0.5,
        max_daily_drawdown_limit_pct=3.0,
        available_margin=50000.0
    )
    assert not allowed
    assert reason == "MAX_POSITIONS_REACHED"


def test_auto_order_parameters_sizing():
    order = calc_auto_order_parameters(
        balance=100000.0,
        allocation_pct=0.10,  # 10% = $10,000 margin
        leverage=5,           # 5x = $50,000 notional
        current_price=80000.0,
        atr_val=1200.0,
        side="BUY"
    )
    assert order["margin"] == 10000.0
    assert order["notional"] == 50000.0
    assert round(order["qty"], 4) == round(50000.0 / 80000.0, 4)
    # Buy TP = 80000 + 2*1200 = 82400
    assert order["tp"] == 82400.0
    # Buy SL = 80000 - 1.5*1200 = 78200
    assert order["sl"] == 78200.0


def test_duplicate_reentry_prevention():
    active = [{"symbol": "BTC-USD", "side": "BUY"}]
    
    # Same side -> block duplicate spam
    allowed, reason = should_reenter_symbol(active, "BTC-USD", "BUY")
    assert not allowed
    assert reason == "ALREADY_ACTIVE_SAME_SIDE"

    # Opposite side -> reverse position
    allowed, reason = should_reenter_symbol(active, "BTC-USD", "SELL")
    assert allowed
    assert reason == "REVERSE_EXISTING_POSITION"

    # Different symbol -> new entry
    allowed, reason = should_reenter_symbol(active, "ETH-USD", "BUY")
    assert allowed
    assert reason == "NEW_ENTRY"

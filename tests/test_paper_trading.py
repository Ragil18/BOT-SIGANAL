"""
Unit tests for Paper Trading financial calculations:
- Margin & Notional Sizing
- Liquidation Price Equations (Isolated Leverage)
- Long & Short Realized / Unrealized PnL with Fee Deductions
- Take Profit & Stop Loss Trigger Logic
- Quant Performance Analytics (Win Rate, Profit Factor, Expectancy)
"""

import pytest


def calc_notional(margin: float, leverage: int) -> float:
    return margin * leverage


def calc_liquidation_price(side: str, entry_price: float, leverage: int, mmr: float = 0.005) -> float | None:
    if leverage <= 1:
        return None  # Spot mode has zero liquidation risk
    if side == "LONG":
        return entry_price * (1.0 - (1.0 / leverage) + mmr)
    elif side == "SHORT":
        return entry_price * (1.0 + (1.0 / leverage) - mmr)
    raise ValueError(f"Unknown side: {side}")


def calc_pnl(side: str, entry_price: float, exit_price: float, qty: float, taker_fee_rate: float = 0.0004) -> tuple[float, float, float]:
    """Returns (gross_pnl, fees, net_pnl)"""
    if side == "LONG":
        gross = (exit_price - entry_price) * qty
    elif side == "SHORT":
        gross = (entry_price - exit_price) * qty
    else:
        raise ValueError(f"Unknown side: {side}")
    
    entry_notional = entry_price * qty
    exit_notional = exit_price * qty
    fees = (entry_notional + exit_notional) * taker_fee_rate
    net = gross - fees
    return gross, fees, net


def check_target_triggers(side: str, cur_price: float, tp: float | None, sl: float | None) -> str | None:
    if side == "LONG":
        if tp and cur_price >= tp:
            return "TP_HIT"
        if sl and cur_price <= sl:
            return "SL_HIT"
    elif side == "SHORT":
        if tp and cur_price <= tp:
            return "TP_HIT"
        if sl and cur_price >= sl:
            return "SL_HIT"
    return None


def calc_quant_analytics(trades: list[float]) -> dict:
    if not trades:
        return {"win_rate": 0.0, "profit_factor": 0.0, "total": 0}
    
    wins = [t for t in trades if t > 0]
    losses = [abs(t) for t in trades if t <= 0]
    
    win_rate = (len(wins) / len(trades)) * 100.0
    gross_win = sum(wins)
    gross_loss = sum(losses)
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)
    
    return {
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "total": len(trades),
        "net_pnl": round(gross_win - gross_loss, 2)
    }


# ==============================================================================
# TESTS
# ==============================================================================

def test_margin_and_notional():
    margin = 5000.0
    leverage = 10
    notional = calc_notional(margin, leverage)
    assert notional == 50000.0
    
    btc_price = 68000.0
    qty = notional / btc_price
    assert round(qty, 4) == round(50000.0 / 68000.0, 4)


def test_liquidation_price():
    # Spot 1x should never liquidate
    assert calc_liquidation_price("LONG", 65000.0, 1) is None
    assert calc_liquidation_price("SHORT", 65000.0, 1) is None
    
    # 10x Long: Entry $65,000 -> Liq price ~ $65,000 * (1 - 0.10 + 0.005) = $58,825
    long_liq = calc_liquidation_price("LONG", 65000.0, 10)
    assert long_liq is not None
    assert 58000 < long_liq < 59500
    
    # 10x Short: Entry $65,000 -> Liq price ~ $65,000 * (1 + 0.10 - 0.005) = $71,175
    short_liq = calc_liquidation_price("SHORT", 65000.0, 10)
    assert short_liq is not None
    assert 70500 < short_liq < 71500


def test_pnl_with_exchange_taker_fees():
    # Long trade: Buy 1 BTC at $60,000, sell at $63,000 (+ $3,000 gross)
    gross, fees, net = calc_pnl("LONG", 60000.0, 63000.0, 1.0, 0.0004)
    assert gross == 3000.0
    # Entry fee: 60,000 * 0.0004 = $24; Exit fee: 63,000 * 0.0004 = $25.2 -> Total fees $49.20
    assert round(fees, 2) == 49.20
    assert round(net, 2) == 2950.80

    # Short trade: Sell 2 ETH at $3,500, buy back at $3,200 (+ $600 gross)
    gross_s, fees_s, net_s = calc_pnl("SHORT", 3500.0, 3200.0, 2.0, 0.0004)
    assert gross_s == 600.0
    assert net_s < 600.0


def test_tp_sl_trigger_evaluation():
    # Long tests
    assert check_target_triggers("LONG", 67000.0, tp=66000.0, sl=63000.0) == "TP_HIT"
    assert check_target_triggers("LONG", 62500.0, tp=66000.0, sl=63000.0) == "SL_HIT"
    assert check_target_triggers("LONG", 64500.0, tp=66000.0, sl=63000.0) is None

    # Short tests
    assert check_target_triggers("SHORT", 61000.0, tp=62000.0, sl=66000.0) == "TP_HIT"
    assert check_target_triggers("SHORT", 67000.0, tp=62000.0, sl=66000.0) == "SL_HIT"
    assert check_target_triggers("SHORT", 64000.0, tp=62000.0, sl=66000.0) is None


def test_quant_analytics_computation():
    trades = [250.0, 400.0, -150.0, 600.0, -200.0, 300.0]
    # 4 wins (250+400+600+300 = 1550), 2 losses (150+200 = 350)
    analytics = calc_quant_analytics(trades)
    assert analytics["total"] == 6
    assert analytics["win_rate"] == pytest.approx(66.67, 0.01)
    # Profit factor: 1550 / 350 = 4.43
    assert analytics["profit_factor"] == pytest.approx(4.43, 0.01)
    assert analytics["net_pnl"] == 1200.0

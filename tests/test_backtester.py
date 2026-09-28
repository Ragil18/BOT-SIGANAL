import pandas as pd
from backtester import Backtester


def _flat_signals(index, close):
    signals = pd.DataFrame(index=index)
    signals["signal"] = "HOLD"
    signals["strength"] = 0.5
    signals["price"] = close
    return signals


def test_run_backtest_smoke(ohlcv):
    signals = _flat_signals(ohlcv.index, ohlcv["Close"])
    signals.iloc[30, signals.columns.get_loc("signal")] = "BUY"
    signals.iloc[60, signals.columns.get_loc("signal")] = "SELL"

    bt = Backtester()
    results = bt.run_backtest(ohlcv, signals, initial_capital=100000)

    assert "portfolio_history" in results
    assert not results["portfolio_history"].empty
    assert results["total_trades"] >= 1


def test_stop_loss_forces_exit_before_a_sell_signal(ohlcv):
    # Force a sharp drop right after entry and confirm the stop-loss exits the
    # position intrabar (via a STOP_LOSS trade), instead of riding it down to the
    # next SELL signal with no protection — this is the exact gap flagged in the
    # roadmap: "no stop-loss/take-profit, a losing position rides with zero
    # protection until the next opposite signal."
    data = ohlcv.copy()
    entry_idx = 10
    data.iloc[entry_idx + 1, data.columns.get_loc("Low")] = data["Close"].iloc[entry_idx] * 0.80

    signals = _flat_signals(data.index, data["Close"])
    signals.iloc[entry_idx, signals.columns.get_loc("signal")] = "BUY"

    bt = Backtester()
    results = bt.run_backtest(data, signals, initial_capital=100000, stop_loss_pct=0.05)

    trade_types = [t["type"] for t in results["trades"]]
    assert "STOP_LOSS" in trade_types


def test_position_size_pct_limits_shares_bought(ohlcv):
    signals = _flat_signals(ohlcv.index, ohlcv["Close"])
    signals.iloc[10, signals.columns.get_loc("signal")] = "BUY"

    bt = Backtester()
    small = bt.run_backtest(ohlcv, signals, initial_capital=100000, position_size_pct=0.2)
    large = bt.run_backtest(ohlcv, signals, initial_capital=100000, position_size_pct=0.9)

    assert small["trades"][0]["shares"] < large["trades"][0]["shares"]


def test_walk_forward_validation_splits_into_requested_folds(ohlcv):
    signals = _flat_signals(ohlcv.index, ohlcv["Close"])
    signals.iloc[::20, signals.columns.get_loc("signal")] = "BUY"
    signals.iloc[10::20, signals.columns.get_loc("signal")] = "SELL"

    bt = Backtester()
    result = bt.walk_forward_validation(ohlcv, signals, initial_capital=100000, num_folds=4)

    assert len(result["folds"]) == 4
    assert "mean_return" in result and "consistent" in result

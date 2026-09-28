from technical_indicators import TechnicalIndicators
from signal_generator import SignalGenerator


def _indicators(ohlcv):
    ti = TechnicalIndicators()
    params = {
        "rsi_period": 14, "macd_fast": 12, "macd_slow": 26,
        "macd_signal": 9, "bb_period": 20, "bb_std": 2.0,
    }
    return ti.calculate_all(ohlcv, params)


def test_generate_signals_returns_expected_contract(ohlcv):
    sg = SignalGenerator()
    indicators = _indicators(ohlcv)
    signals = sg.generate_signals(ohlcv, indicators, threshold=0.3)

    assert len(signals) == len(ohlcv)
    assert set(signals["signal"].unique()).issubset({"BUY", "SELL", "HOLD"})
    assert (signals["strength"] >= 0).all()

    # Every weighted sub-signal must show up as its own contribution column, so a
    # BUY/SELL call is auditable rather than only narrated by the "reason" text.
    for name in sg.signal_weights:
        assert f"contrib_{name}" in signals.columns


def test_higher_threshold_produces_fewer_or_equal_signals(ohlcv):
    sg = SignalGenerator()
    indicators = _indicators(ohlcv)

    loose = sg.generate_signals(ohlcv, indicators, threshold=0.2)
    strict = sg.generate_signals(ohlcv, indicators, threshold=0.7)

    loose_count = (loose["signal"] != "HOLD").sum()
    strict_count = (strict["signal"] != "HOLD").sum()
    assert strict_count <= loose_count


def test_calculate_signal_strength_labels():
    sg = SignalGenerator()
    assert sg.calculate_signal_strength(0.9) == "Very Strong"
    assert sg.calculate_signal_strength(0.65) == "Strong"
    assert sg.calculate_signal_strength(0.45) == "Moderate"
    assert sg.calculate_signal_strength(0.25) == "Weak"
    assert sg.calculate_signal_strength(0.05) == "Very Weak"

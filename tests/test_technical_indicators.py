from technical_indicators import TechnicalIndicators


def test_calculate_all_returns_expected_columns(ohlcv):
    ti = TechnicalIndicators()
    params = {
        "rsi_period": 14, "macd_fast": 12, "macd_slow": 26,
        "macd_signal": 9, "bb_period": 20, "bb_std": 2.0,
    }
    indicators = ti.calculate_all(ohlcv, params)

    # These are exactly the columns app.py's create_chart() and signal_generator.py
    # read back out by name — a mismatch here is a silent bug (this is what caused
    # the EMA 5/8/13 and Stochastic chart traces to never render before the fix).
    expected_columns = {
        "rsi", "rsi_fast", "rsi_slow", "macd", "macd_signal", "macd_histogram",
        "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_position",
        "ema_9", "ema_21", "ema_50", "ema_200", "sma_50",
        "stoch_k", "stoch_d", "williams_r", "cci", "atr",
        "volume_sma", "volume_ratio", "momentum", "roc", "vwap",
        "swing_trend", "price_momentum", "trend_strength",
        "support_resistance", "breakout_signal", "volatility_ratio", "volume_trend",
    }
    assert expected_columns.issubset(set(indicators.columns))
    assert len(indicators) == len(ohlcv)


def test_rsi_bounded_between_0_and_100(ohlcv):
    ti = TechnicalIndicators()
    rsi = ti.calculate_rsi(ohlcv["Close"], 14)
    valid = rsi.dropna()
    assert not valid.empty
    assert (valid >= 0).all() and (valid <= 100).all()


def test_bollinger_bands_are_ordered(ohlcv):
    ti = TechnicalIndicators()
    bb = ti.calculate_bollinger_bands(ohlcv["Close"], 20, 2.0)
    valid = bb.dropna()
    assert not valid.empty
    assert (valid["bb_upper"] >= valid["bb_middle"]).all()
    assert (valid["bb_middle"] >= valid["bb_lower"]).all()


def test_atr_is_non_negative(ohlcv):
    ti = TechnicalIndicators()
    atr = ti.calculate_atr(ohlcv, 14)
    assert (atr.dropna() >= 0).all()


def test_williams_r_bounded(ohlcv):
    ti = TechnicalIndicators()
    wr = ti.calculate_williams_r(ohlcv, 14)
    valid = wr.dropna()
    assert not valid.empty
    assert (valid <= 0).all() and (valid >= -100).all()


def test_stochastic_bounded(ohlcv):
    ti = TechnicalIndicators()
    stoch = ti.calculate_stochastic(ohlcv, 14, 3, 3)
    valid = stoch.dropna()
    assert not valid.empty
    assert (valid["stoch_k"] >= 0).all() and (valid["stoch_k"] <= 100).all()

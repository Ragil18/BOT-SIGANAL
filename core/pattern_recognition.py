import pandas as pd
import numpy as np


class PatternRecognition:
    """Algorithmic Candlestick Pattern Recognition & Price Action Validation Engine."""

    @staticmethod
    def detect_patterns(data: pd.DataFrame) -> pd.DataFrame:
        """Analyze OHLCV candles and return detected candlestick patterns, volume surges,
        and breakout confirmations."""
        if data.empty or len(data) < 5:
            empty_df = pd.DataFrame(index=data.index)
            empty_df['pattern_name'] = 'None'
            empty_df['pattern_type'] = 'NEUTRAL'
            empty_df['pattern_score'] = 0.0
            empty_df['volume_surge'] = False
            empty_df['volume_ratio'] = 1.0
            empty_df['is_breakout'] = False
            return empty_df

        df = data.copy()
        open_p = df['Open']
        high_p = df['High']
        low_p = df['Low']
        close_p = df['Close']
        volume = df['Volume']

        body = (close_p - open_p).abs()
        candle_range = (high_p - low_p).replace(0, 0.0001)
        upper_shadow = high_p - np.maximum(open_p, close_p)
        lower_shadow = np.minimum(open_p, close_p) - low_p
        is_green = close_p > open_p
        is_red = close_p < open_p

        # 20-period volume moving average & breakout levels
        vol_sma20 = volume.rolling(20, min_periods=3).mean().replace(0, 1)
        volume_ratio = volume / vol_sma20
        volume_surge = volume_ratio >= 1.3

        swing_high_20 = high_p.shift(1).rolling(20, min_periods=5).max()
        swing_low_20 = low_p.shift(1).rolling(20, min_periods=5).min()

        pattern_name = pd.Series('None', index=df.index, dtype='object')
        pattern_type = pd.Series('NEUTRAL', index=df.index, dtype='object')
        pattern_score = pd.Series(0.0, index=df.index)
        is_breakout = pd.Series(False, index=df.index)

        # Loop from index 2 to end for multi-candle sequence matching
        for i in range(2, len(df)):
            curr_body = body.iloc[i]
            prev_body = body.iloc[i - 1]
            prev2_body = body.iloc[i - 2]
            curr_range = candle_range.iloc[i]

            # 1. Bullish Engulfing
            if (is_red.iloc[i - 1] and is_green.iloc[i] and
                    open_p.iloc[i] <= close_p.iloc[i - 1] and
                    close_p.iloc[i] >= open_p.iloc[i - 1] and
                    curr_body > prev_body * 1.05):
                pattern_name.iloc[i] = 'Bullish Engulfing'
                pattern_type.iloc[i] = 'BULLISH'
                pattern_score.iloc[i] = 0.85

            # 2. Bearish Engulfing
            elif (is_green.iloc[i - 1] and is_red.iloc[i] and
                  open_p.iloc[i] >= close_p.iloc[i - 1] and
                  close_p.iloc[i] <= open_p.iloc[i - 1] and
                  curr_body > prev_body * 1.05):
                pattern_name.iloc[i] = 'Bearish Engulfing'
                pattern_type.iloc[i] = 'BEARISH'
                pattern_score.iloc[i] = -0.85

            # 3. Hammer / Bullish Pinbar (long lower shadow, small upper body)
            elif (lower_shadow.iloc[i] >= 2.0 * curr_body and
                  upper_shadow.iloc[i] <= 0.35 * curr_body and
                  curr_body >= 0.1 * curr_range):
                pattern_name.iloc[i] = 'Hammer (Pinbar)'
                pattern_type.iloc[i] = 'BULLISH'
                pattern_score.iloc[i] = 0.75

            # 4. Shooting Star (long upper shadow, rejection of highs)
            elif (upper_shadow.iloc[i] >= 2.0 * curr_body and
                  lower_shadow.iloc[i] <= 0.35 * curr_body and
                  curr_body >= 0.1 * curr_range):
                pattern_name.iloc[i] = 'Shooting Star'
                pattern_type.iloc[i] = 'BEARISH'
                pattern_score.iloc[i] = -0.75

            # 5. Morning Star (3-candle sequence: Red -> Small Gap -> Strong Green)
            elif (is_red.iloc[i - 2] and prev2_body > 0.4 * candle_range.iloc[i - 2] and
                  prev_body <= 0.3 * candle_range.iloc[i - 1] and
                  is_green.iloc[i] and close_p.iloc[i] >= (open_p.iloc[i - 2] + close_p.iloc[i - 2]) / 2):
                pattern_name.iloc[i] = 'Morning Star'
                pattern_type.iloc[i] = 'BULLISH'
                pattern_score.iloc[i] = 0.90

            # 6. Evening Star (3-candle sequence: Green -> Small Gap -> Strong Red)
            elif (is_green.iloc[i - 2] and prev2_body > 0.4 * candle_range.iloc[i - 2] and
                  prev_body <= 0.3 * candle_range.iloc[i - 1] and
                  is_red.iloc[i] and close_p.iloc[i] <= (open_p.iloc[i - 2] + close_p.iloc[i - 2]) / 2):
                pattern_name.iloc[i] = 'Evening Star'
                pattern_type.iloc[i] = 'BEARISH'
                pattern_score.iloc[i] = -0.90

            # 7. 20-Period Resistance Breakout with Volume Confirmation
            if not pd.isna(swing_high_20.iloc[i]) and close_p.iloc[i] > swing_high_20.iloc[i] and volume_surge.iloc[i]:
                is_breakout.iloc[i] = True
                if pattern_name.iloc[i] == 'None':
                    pattern_name.iloc[i] = 'Resistance Breakout'
                    pattern_type.iloc[i] = 'BULLISH'
                    pattern_score.iloc[i] = 0.80

            # 8. 20-Period Support Breakdown
            elif not pd.isna(swing_low_20.iloc[i]) and close_p.iloc[i] < swing_low_20.iloc[i] and volume_surge.iloc[i]:
                is_breakout.iloc[i] = True
                if pattern_name.iloc[i] == 'None':
                    pattern_name.iloc[i] = 'Support Breakdown'
                    pattern_type.iloc[i] = 'BEARISH'
                    pattern_score.iloc[i] = -0.80

        res = pd.DataFrame(index=df.index)
        res['pattern_name'] = pattern_name
        res['pattern_type'] = pattern_type
        res['pattern_score'] = pattern_score
        res['volume_surge'] = volume_surge
        res['volume_ratio'] = volume_ratio
        res['is_breakout'] = is_breakout

        return res

    @staticmethod
    def generate_trade_thesis(symbol: str, current_price: float, signal_row: dict,
                              pattern_row: dict, fundamentals: dict) -> str:
        """Generate a coherent, institutional executive rationale combining
        technical signals, price patterns, volume confirmation, and fundamentals."""
        signal = signal_row.get('signal', 'HOLD')
        strength = signal_row.get('strength', 0.5)
        pattern = pattern_row.get('pattern_name', 'None')
        vol_surge = pattern_row.get('volume_surge', False)
        vol_ratio = pattern_row.get('volume_ratio', 1.0)
        
        fundamentals = fundamentals or {}
        name = fundamentals.get('name', symbol)
        target = fundamentals.get('target_price')
        pe = fundamentals.get('pe_trailing')
        sector = fundamentals.get('sector', 'N/A')

        if signal == 'BUY':
            thesis = f"**Executive Trade Thesis ({symbol})**: Algorithmic models indicate a **STRONG BUY** setup on {name}."
            if pattern != 'None':
                thesis += f" A confirmed **{pattern}** formed at support, validating institutional accumulation."
            else:
                thesis += f" Momentum indicators (RSI & MACD) confirm a bullish trend continuation."

            if vol_surge:
                thesis += f" Volume is expanding strongly at **{vol_ratio:.1f}x** normal average volume, confirming real breakout participation."
            else:
                thesis += f" Volume is steady at normal baseline levels."

            if target and target > current_price:
                upside = ((target - current_price) / current_price) * 100
                thesis += f" Dalal Street / Consensus target projects a **+{upside:.1f}% potential upside** (Target: ₹{target:,.2f})."
            if pe and pe > 0:
                thesis += f" Sector: {sector} (Trailing P/E: {pe:.1f})."

            return thesis

        elif signal == 'SELL':
            thesis = f"**Executive Trade Thesis ({symbol})**: Risk algorithms triggered a **SELL / CAPITAL PRESERVATION** alert on {name}."
            if pattern != 'None':
                thesis += f" A bearish **{pattern}** signal rejected local resistance."
            else:
                thesis += f" Momentum exhaustion detected across moving average and oscillator consensus."

            if vol_surge:
                thesis += f" High selling volume (**{vol_ratio:.1f}x normal**) indicates institutional distribution."
            return thesis

        else:
            return f"**Market Equilibrium Thesis ({symbol})**: {name} is currently consolidating in a range-bound state without clear trend confirmation. Algorithms advise **HOLD** until a decisive breakout occurs above resistance or below support."

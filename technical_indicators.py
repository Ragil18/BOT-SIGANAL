import pandas as pd
import numpy as np
from typing import Dict, Any

class TechnicalIndicators:
    """Class for calculating various technical indicators"""
    
    def __init__(self):
        pass
    
    def calculate_all(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Calculate all technical indicators optimized for swing trading"""
        indicators = pd.DataFrame(index=data.index)
        
        # RSI for swing trading
        indicators['rsi'] = self.calculate_rsi(data['Close'], params.get('rsi_period', 14))
        indicators['rsi_fast'] = self.calculate_rsi(data['Close'], 9)  # Faster RSI for entries
        indicators['rsi_slow'] = self.calculate_rsi(data['Close'], 25)  # Slower for trend
        
        # MACD with standard swing settings
        macd_data = self.calculate_macd(
            data['Close'], 
            params.get('macd_fast', 12), 
            params.get('macd_slow', 26), 
            params.get('macd_signal', 9)
        )
        indicators = indicators.join(macd_data)
        
        # Bollinger Bands with standard settings
        bb_data = self.calculate_bollinger_bands(
            data['Close'], 
            params.get('bb_period', 20), 
            params.get('bb_std', 2.0)
        )
        indicators = indicators.join(bb_data)
        
        # Moving Averages for swing trend analysis
        indicators['ema_9'] = self.calculate_ema(data['Close'], 9)
        indicators['ema_21'] = self.calculate_ema(data['Close'], 21)
        indicators['ema_50'] = self.calculate_ema(data['Close'], 50)
        indicators['ema_200'] = self.calculate_ema(data['Close'], 200)  # Long-term trend
        indicators['sma_50'] = self.calculate_sma(data['Close'], 50)
        
        # Stochastic with standard swing settings
        stoch_data = self.calculate_stochastic(data, 14, 3, 3)
        indicators = indicators.join(stoch_data)
        
        # Williams %R for swing momentum
        indicators['williams_r'] = self.calculate_williams_r(data, 14)
        
        # CCI for swing reversals
        indicators['cci'] = self.calculate_cci(data, 20)
        
        # Average True Range for swing volatility
        indicators['atr'] = self.calculate_atr(data, 14)
        
        # Volume indicators for swing analysis
        indicators['volume_sma'] = self.calculate_sma(data['Volume'], 50)  # Longer average
        indicators['volume_ratio'] = data['Volume'] / indicators['volume_sma']
        
        # Price momentum for swing trading
        indicators['momentum'] = self.calculate_momentum(data['Close'], 10)  # Medium-term
        indicators['roc'] = self.calculate_roc(data['Close'], 12)  # Rate of change
        
        # VWAP for swing levels
        indicators['vwap'] = self.calculate_vwap(data)
        
        # Swing trading specific indicators
        indicators['swing_trend'] = self.calculate_swing_trend(data)
        indicators['price_momentum'] = self.calculate_price_momentum(data['Close'])
        
        # Advanced swing trading enhancements
        try:
            indicators['trend_strength'] = self.calculate_trend_strength(data)
            indicators['support_resistance'] = self.calculate_support_resistance(data)
            indicators['breakout_signal'] = self.calculate_breakout_signal(data)
            indicators['volatility_ratio'] = self.calculate_volatility_ratio(data)
            indicators['volume_trend'] = self.calculate_volume_trend(data)
        except:
            # Fallback values if advanced indicators fail
            indicators['trend_strength'] = pd.Series(0, index=data.index)
            indicators['support_resistance'] = pd.Series(0, index=data.index)
            indicators['breakout_signal'] = pd.Series(0, index=data.index)
            indicators['volatility_ratio'] = pd.Series(1, index=data.index)
            indicators['volume_trend'] = pd.Series(0, index=data.index)
        
        return indicators
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        
        return pd.DataFrame({
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram
        })
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return pd.DataFrame({
            'bb_upper': upper_band,
            'bb_middle': sma,
            'bb_lower': lower_band,
            'bb_width': (upper_band - lower_band) / sma,
            'bb_position': (prices - lower_band) / (upper_band - lower_band)
        })
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    def calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        low_min = data['Low'].rolling(window=k_period).min()
        high_max = data['High'].rolling(window=k_period).max()
        
        k_percent = 100 * ((data['Close'] - low_min) / (high_max - low_min))
        k_percent_smooth = k_percent.rolling(window=smooth_k).mean()
        d_percent = k_percent_smooth.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'stoch_k': k_percent_smooth,
            'stoch_d': d_percent
        })
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        high_max = data['High'].rolling(window=period).max()
        low_min = data['Low'].rolling(window=period).min()
        
        williams_r = -100 * ((high_max - data['Close']) / (high_max - low_min))
        return williams_r
    
    def calculate_cci(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (typical_price - sma_tp) / (0.015 * mad)
        return cci
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Price Momentum"""
        return prices.diff(period)
    
    def calculate_roc(self, prices: pd.Series, period: int = 12) -> pd.Series:
        """Calculate Rate of Change"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        volume_price = typical_price * data['Volume']
        cumulative_volume_price = volume_price.cumsum()
        cumulative_volume = data['Volume'].cumsum()
        
        return cumulative_volume_price / cumulative_volume
    
    def calculate_scalp_trend(self, data: pd.DataFrame) -> pd.Series:
        """Calculate scalping trend indicator based on fast EMAs"""
        ema5 = self.calculate_ema(data['Close'], 5)
        ema8 = self.calculate_ema(data['Close'], 8)
        ema13 = self.calculate_ema(data['Close'], 13)
        
        # Trend strength: +1 (strong up), 0 (neutral), -1 (strong down)
        trend = pd.Series(0.0, index=data.index)
        
        # Bullish when EMAs are aligned upward
        bullish = (ema5 > ema8) & (ema8 > ema13) & (data['Close'] > ema5)
        bearish = (ema5 < ema8) & (ema8 < ema13) & (data['Close'] < ema5)
        
        trend[bullish] = 1.0
        trend[bearish] = -1.0
        
        return trend
    
    def calculate_price_velocity(self, prices: pd.Series, period: int = 3) -> pd.Series:
        """Calculate price velocity for scalping momentum"""
        return prices.diff(period) / period
    
    def calculate_squeeze_momentum(self, data: pd.DataFrame) -> pd.Series:
        """Calculate TTM Squeeze momentum for scalping entries"""
        try:
            bb_data = self.calculate_bollinger_bands(data['Close'], 20, 2.0)
            bb_upper = bb_data['bb_upper']
            bb_lower = bb_data['bb_lower']
            kc_upper, kc_lower = self.calculate_keltner_channels(data)
            
            # Squeeze occurs when Bollinger Bands are inside Keltner Channels
            squeeze = (bb_upper < kc_upper) & (bb_lower > kc_lower)
            
            # Momentum calculation
            highest = data['High'].rolling(20).max()
            lowest = data['Low'].rolling(20).min()
            avg_price = (highest + lowest) / 2
            momentum = data['Close'] - avg_price.shift(10)
            
            return pd.Series(np.where(squeeze, 0, momentum), index=data.index)
        except:
            return pd.Series(0, index=data.index)
    
    def calculate_keltner_channels(self, data: pd.DataFrame, period: int = 20, multiplier: float = 2.0):
        """Calculate Keltner Channels"""
        ema = self.calculate_ema(data['Close'], period)
        atr = self.calculate_atr(data, period)
        
        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)
        
        return upper, lower
    
    def calculate_market_structure(self, data: pd.DataFrame) -> pd.Series:
        """Identify market structure for scalping context"""
        high_period = 5
        low_period = 5
        
        # Higher highs and higher lows = uptrend
        # Lower highs and lower lows = downtrend
        
        rolling_max = data['High'].rolling(high_period, center=True).max()
        rolling_min = data['Low'].rolling(low_period, center=True).min()
        
        higher_highs = data['High'] > rolling_max.shift(1)
        higher_lows = data['Low'] > rolling_min.shift(1)
        lower_highs = data['High'] < rolling_max.shift(1)
        lower_lows = data['Low'] < rolling_min.shift(1)
        
        structure = pd.Series(0.0, index=data.index)  # 0 = sideways
        structure[(higher_highs & higher_lows)] = 1.0  # 1 = uptrend
        structure[(lower_highs & lower_lows)] = -1.0   # -1 = downtrend
        
        return structure.fillna(method='ffill').fillna(0)
    
    def calculate_volume_profile(self, data: pd.DataFrame) -> pd.Series:
        """Calculate volume profile strength"""
        volume_sma = self.calculate_sma(data['Volume'], 20)
        price_change = data['Close'].pct_change()
        
        # Volume-price relationship
        volume_strength = data['Volume'] / volume_sma
        price_volume_correlation = price_change.rolling(10).corr(volume_strength)
        
        return volume_strength * (1 + price_volume_correlation.fillna(0))
    
    def calculate_volatility_ratio(self, data: pd.DataFrame) -> pd.Series:
        """Calculate volatility ratio for scalping timing"""
        atr = self.calculate_atr(data, 14)
        atr_avg = atr.rolling(50).mean()
        
        # Current volatility vs average volatility
        volatility_ratio = atr / atr_avg
        
        return volatility_ratio
    
    def calculate_trend_strength(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trend strength using multiple EMAs"""
        ema_5 = self.calculate_ema(data['Close'], 5)
        ema_13 = self.calculate_ema(data['Close'], 13)
        ema_21 = self.calculate_ema(data['Close'], 21)
        
        # Calculate trend alignment strength
        bullish_strength = ((ema_5 > ema_13) & (ema_13 > ema_21) & 
                           (data['Close'] > ema_5)).astype(int)
        bearish_strength = ((ema_5 < ema_13) & (ema_13 < ema_21) & 
                           (data['Close'] < ema_5)).astype(int)
        
        trend_strength = bullish_strength - bearish_strength
        
        # Smooth the signal
        return trend_strength.rolling(3).mean()
    
    def calculate_swing_trend(self, data: pd.DataFrame) -> pd.Series:
        """Calculate swing trend direction using EMA crossovers"""
        # Use EMAs appropriate for swing trading
        ema_9 = self.calculate_ema(data['Close'], 9)
        ema_21 = self.calculate_ema(data['Close'], 21)
        
        trend = pd.Series(0, index=data.index)
        trend[ema_9 > ema_21] = 1   # Uptrend
        trend[ema_9 < ema_21] = -1  # Downtrend
        
        return trend
    
    def calculate_price_momentum(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate price momentum for swing trading"""
        return prices.diff(period) / period
    
    def calculate_support_resistance(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """Identify support and resistance levels for swing trading"""
        high_rolling = data['High'].rolling(window=window, center=True).max()
        low_rolling = data['Low'].rolling(window=window, center=True).min()
        
        # Find pivot points
        resistance = (data['High'] == high_rolling).astype(int)
        support = (data['Low'] == low_rolling).astype(int) * -1
        
        return resistance + support
    
    def calculate_breakout_signal(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate breakout signals for swing trading"""
        high_max = data['High'].rolling(period).max()
        low_min = data['Low'].rolling(period).min()
        
        breakout = pd.Series(0, index=data.index)
        breakout[data['Close'] > high_max.shift(1)] = 1   # Upward breakout
        breakout[data['Close'] < low_min.shift(1)] = -1   # Downward breakout
        
        return breakout
    
    def calculate_volume_trend(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate volume trend for swing confirmation"""
        volume_sma = self.calculate_sma(data['Volume'], period)
        volume_trend = data['Volume'] / volume_sma
        
        # Smooth the trend
        return volume_trend.rolling(5).mean()

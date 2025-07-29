import pandas as pd
import numpy as np
from typing import Dict, Any

class TechnicalIndicators:
    """Class for calculating various technical indicators"""
    
    def __init__(self):
        pass
    
    def calculate_all(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Calculate all technical indicators optimized for scalp trading"""
        indicators = pd.DataFrame(index=data.index)
        
        # Fast RSI for scalping
        indicators['rsi'] = self.calculate_rsi(data['Close'], params.get('rsi_period', 7))
        indicators['rsi_fast'] = self.calculate_rsi(data['Close'], 5)  # Very fast RSI
        
        # MACD with faster settings
        macd_data = self.calculate_macd(
            data['Close'], 
            params.get('macd_fast', 5), 
            params.get('macd_slow', 13), 
            params.get('macd_signal', 5)
        )
        indicators = indicators.join(macd_data)
        
        # Bollinger Bands with tighter settings
        bb_data = self.calculate_bollinger_bands(
            data['Close'], 
            params.get('bb_period', 10), 
            params.get('bb_std', 1.5)
        )
        indicators = indicators.join(bb_data)
        
        # Fast Moving Averages for scalping
        indicators['ema_5'] = self.calculate_ema(data['Close'], 5)
        indicators['ema_8'] = self.calculate_ema(data['Close'], 8)
        indicators['ema_13'] = self.calculate_ema(data['Close'], 13)
        indicators['ema_21'] = self.calculate_ema(data['Close'], 21)
        indicators['sma_9'] = self.calculate_sma(data['Close'], 9)
        
        # Fast Stochastic for scalping
        stoch_data = self.calculate_stochastic(data, 5, 3, 3)
        indicators = indicators.join(stoch_data)
        
        # Williams %R for scalping
        indicators['williams_r'] = self.calculate_williams_r(data, 14)
        
        # CCI (Commodity Channel Index) for scalping
        indicators['cci'] = self.calculate_cci(data, 14)
        
        # Average True Range for volatility
        indicators['atr'] = self.calculate_atr(data, 14)
        
        # Volume indicators
        indicators['volume_sma'] = self.calculate_sma(data['Volume'], 10)
        indicators['volume_ratio'] = data['Volume'] / indicators['volume_sma']
        
        # Price momentum for scalping
        indicators['momentum'] = self.calculate_momentum(data['Close'], 3)
        indicators['roc'] = self.calculate_roc(data['Close'], 5)
        
        # VWAP (Volume Weighted Average Price)
        indicators['vwap'] = self.calculate_vwap(data)
        
        # Scalping specific indicators
        indicators['scalp_trend'] = self.calculate_scalp_trend(data)
        indicators['price_velocity'] = self.calculate_price_velocity(data['Close'])
        
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

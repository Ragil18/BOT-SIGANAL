import pandas as pd
import numpy as np
from typing import Dict, Any

class SignalGenerator:
    """Class for generating trading signals based on technical indicators"""
    
    def __init__(self):
        # Enhanced weights for advanced scalp trading
        self.signal_weights = {
            'fast_rsi': 0.18,
            'macd': 0.18,
            'bollinger': 0.12,
            'scalp_trend': 0.15,
            'stochastic': 0.10,
            'williams_r': 0.08,
            'volume': 0.05,
            'velocity': 0.04,
            'squeeze_momentum': 0.05,
            'market_structure': 0.03,
            'trend_strength': 0.02
        }
    
    def generate_signals(self, data: pd.DataFrame, indicators: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        """Generate scalping-optimized trading signals"""
        signals = pd.DataFrame(index=data.index)
        
        # Calculate individual signal components for scalping
        fast_rsi_signals = self._fast_rsi_signals(indicators)
        macd_signals = self._macd_signals(indicators)
        bb_signals = self._bollinger_signals(data, indicators)
        scalp_trend_signals = self._scalp_trend_signals(indicators)
        stoch_signals = self._stochastic_signals(indicators)
        williams_signals = self._williams_r_signals(indicators)
        volume_signals = self._volume_signals(data, indicators)
        velocity_signals = self._velocity_signals(indicators)
        squeeze_signals = self._squeeze_momentum_signals(indicators)
        structure_signals = self._market_structure_signals(indicators)
        trend_strength_signals = self._trend_strength_signals(indicators)
        
        # Combine signals with enhanced scalping weights
        combined_score = (
            fast_rsi_signals * self.signal_weights['fast_rsi'] +
            macd_signals * self.signal_weights['macd'] +
            bb_signals * self.signal_weights['bollinger'] +
            scalp_trend_signals * self.signal_weights['scalp_trend'] +
            stoch_signals * self.signal_weights['stochastic'] +
            williams_signals * self.signal_weights['williams_r'] +
            volume_signals * self.signal_weights['volume'] +
            velocity_signals * self.signal_weights['velocity'] +
            squeeze_signals * self.signal_weights['squeeze_momentum'] +
            structure_signals * self.signal_weights['market_structure'] +
            trend_strength_signals * self.signal_weights['trend_strength']
        )
        
        # Generate final signals
        signals['score'] = combined_score
        signals['signal'] = 'HOLD'
        signals['strength'] = np.abs(combined_score)
        signals['price'] = data['Close']
        signals['reason'] = ''
        
        # Apply threshold
        buy_condition = combined_score > threshold
        sell_condition = combined_score < -threshold
        
        signals.loc[buy_condition, 'signal'] = 'BUY'
        signals.loc[sell_condition, 'signal'] = 'SELL'
        
        # Add reasoning
        signals['reason'] = self._generate_scalp_reasons(
            signals, indicators, fast_rsi_signals, macd_signals, 
            bb_signals, scalp_trend_signals, stoch_signals, williams_signals, 
            volume_signals, velocity_signals
        )
        
        return signals
    
    def _fast_rsi_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate fast RSI signals for scalping"""
        rsi = indicators.get('rsi_fast', indicators.get('rsi', pd.Series(50, index=indicators.index)))
        signals = pd.Series(0.0, index=indicators.index)
        
        # More sensitive thresholds for scalping
        signals[rsi < 25] = 1.0   # Strong buy
        signals[rsi < 30] = 0.8   # Moderate buy
        signals[rsi > 75] = -1.0  # Strong sell
        signals[rsi > 70] = -0.8  # Moderate sell
        
        # Fast momentum for scalping
        rsi_momentum = rsi.diff(2)
        signals[rsi_momentum > 8] += 0.4
        signals[rsi_momentum < -8] -= 0.4
        
        return np.clip(signals, -1, 1)
    
    def _macd_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate MACD-based signals"""
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_histogram = indicators['macd_histogram']
        
        signals = pd.Series(0.0, index=indicators.index)
        
        # MACD line crossing signal line
        macd_cross = macd - macd_signal
        macd_cross_prev = macd_cross.shift(1)
        
        # Bullish crossover
        bullish_cross = (macd_cross > 0) & (macd_cross_prev <= 0)
        signals[bullish_cross] = 0.8
        
        # Bearish crossover
        bearish_cross = (macd_cross < 0) & (macd_cross_prev >= 0)
        signals[bearish_cross] = -0.8
        
        # Histogram momentum
        histogram_momentum = macd_histogram.diff()
        signals[histogram_momentum > 0] += 0.3
        signals[histogram_momentum < 0] -= 0.3
        
        # Zero line cross
        zero_cross_up = (macd > 0) & (macd.shift(1) <= 0)
        zero_cross_down = (macd < 0) & (macd.shift(1) >= 0)
        signals[zero_cross_up] += 0.4
        signals[zero_cross_down] -= 0.4
        
        return np.clip(signals, -1, 1)
    
    def _bollinger_signals(self, data: pd.DataFrame, indicators: pd.DataFrame) -> pd.Series:
        """Generate Bollinger Bands-based signals"""
        price = data['Close']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        bb_middle = indicators['bb_middle']
        bb_position = indicators['bb_position']
        
        signals = pd.Series(0.0, index=indicators.index)
        
        # Price position relative to bands
        signals[bb_position < 0.2] = 0.8  # Near lower band - buy
        signals[bb_position > 0.8] = -0.8  # Near upper band - sell
        
        # Band squeeze (low volatility)
        bb_width = indicators['bb_width']
        bb_width_ma = bb_width.rolling(20).mean()
        squeeze = bb_width < bb_width_ma * 0.8
        
        # Breakout after squeeze
        price_above_upper = price > bb_upper
        price_below_lower = price < bb_lower
        
        signals[(squeeze.shift(1)) & price_above_upper] = 0.6
        signals[(squeeze.shift(1)) & price_below_lower] = -0.6
        
        # Mean reversion
        distance_from_middle = np.abs(price - bb_middle) / bb_middle
        signals[distance_from_middle > 0.05] -= distance_from_middle * 2
        
        return np.clip(signals, -1, 1)
    
    def _scalp_trend_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate scalping trend signals"""
        trend = indicators.get('scalp_trend', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Direct trend following for scalping
        signals[trend > 0] = 0.8
        signals[trend < 0] = -0.8
        
        return signals
    
    def _williams_r_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate Williams %R signals for scalping"""
        williams = indicators.get('williams_r', pd.Series(-50, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Oversold/Overbought levels for scalping
        signals[williams < -85] = 0.9   # Strong buy
        signals[williams < -80] = 0.6   # Moderate buy
        signals[williams > -15] = -0.9  # Strong sell
        signals[williams > -20] = -0.6  # Moderate sell
        
        return signals
    
    def _velocity_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate price velocity signals for scalping"""
        velocity = indicators.get('price_velocity', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Momentum-based signals
        velocity_std = velocity.rolling(20).std()
        threshold = velocity_std * 1.5
        
        signals[velocity > threshold] = 0.7   # Strong upward momentum
        signals[velocity < -threshold] = -0.7  # Strong downward momentum
        
        return signals
    
    def _squeeze_momentum_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate squeeze momentum signals for scalping"""
        squeeze = indicators.get('squeeze_momentum', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Momentum breakout signals
        momentum_change = squeeze.diff()
        signals[momentum_change > 0.5] = 0.8   # Positive momentum
        signals[momentum_change < -0.5] = -0.8  # Negative momentum
        
        return signals
    
    def _market_structure_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate market structure signals"""
        structure = indicators.get('market_structure', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Structure alignment
        signals[structure > 0] = 0.6   # Uptrend structure
        signals[structure < 0] = -0.6  # Downtrend structure
        
        return signals
    
    def _trend_strength_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate trend strength signals"""
        strength = indicators.get('trend_strength', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Strong trend alignment
        signals[strength > 0.8] = 0.7   # Strong bullish trend
        signals[strength < -0.8] = -0.7  # Strong bearish trend
        
        return signals
    
    def _moving_average_signals(self, data: pd.DataFrame, indicators: pd.DataFrame) -> pd.Series:
        """Generate Moving Average-based signals"""
        price = data['Close']
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        ema_12 = indicators['ema_12']
        ema_26 = indicators['ema_26']
        
        signals = pd.Series(0.0, index=indicators.index)
        
        # Price vs Moving Averages
        signals[price > sma_20] += 0.3
        signals[price < sma_20] -= 0.3
        signals[price > sma_50] += 0.2
        signals[price < sma_50] -= 0.2
        
        # Golden/Death Cross
        ma_cross = sma_20 - sma_50
        ma_cross_prev = ma_cross.shift(1)
        
        golden_cross = (ma_cross > 0) & (ma_cross_prev <= 0)
        death_cross = (ma_cross < 0) & (ma_cross_prev >= 0)
        
        signals[golden_cross] += 0.7
        signals[death_cross] -= 0.7
        
        # EMA trend
        ema_trend = ema_12 - ema_26
        ema_trend_prev = ema_trend.shift(1)
        
        signals[ema_trend > ema_trend_prev] += 0.2
        signals[ema_trend < ema_trend_prev] -= 0.2
        
        return np.clip(signals, -1, 1)
    
    def _stochastic_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate Stochastic Oscillator-based signals"""
        if 'stoch_k' not in indicators.columns:
            return pd.Series(0.0, index=indicators.index)
            
        stoch_k = indicators['stoch_k']
        stoch_d = indicators['stoch_d']
        
        signals = pd.Series(0.0, index=indicators.index)
        
        # Oversold/Overbought
        signals[stoch_k < 20] = 0.7
        signals[stoch_k > 80] = -0.7
        
        # %K and %D crossover
        k_cross_d = stoch_k - stoch_d
        k_cross_d_prev = k_cross_d.shift(1)
        
        bullish_stoch = (k_cross_d > 0) & (k_cross_d_prev <= 0) & (stoch_k < 50)
        bearish_stoch = (k_cross_d < 0) & (k_cross_d_prev >= 0) & (stoch_k > 50)
        
        signals[bullish_stoch] += 0.5
        signals[bearish_stoch] -= 0.5
        
        return np.clip(signals, -1, 1)
    
    def _volume_signals(self, data: pd.DataFrame, indicators: pd.DataFrame) -> pd.Series:
        """Generate Volume-based signals"""
        volume = data['Volume']
        volume_ratio = indicators['volume_ratio']
        
        signals = pd.Series(0.0, index=indicators.index)
        
        # High volume confirmation
        high_volume = volume_ratio > 1.5
        price_change = data['Close'].pct_change()
        
        # Volume confirms price movement
        signals[(high_volume) & (price_change > 0.02)] += 0.4
        signals[(high_volume) & (price_change < -0.02)] -= 0.4
        
        # Volume divergence (simplified)
        volume_trend = volume.rolling(5).mean().diff()
        price_trend = data['Close'].rolling(5).mean().diff()
        
        # Volume increasing while price declining (potential reversal)
        signals[(volume_trend > 0) & (price_trend < 0)] += 0.2
        signals[(volume_trend < 0) & (price_trend > 0)] -= 0.2
        
        return np.clip(signals, -1, 1)
    
    def _generate_scalp_reasons(self, signals: pd.DataFrame, indicators: pd.DataFrame,
                               fast_rsi_signals: pd.Series, macd_signals: pd.Series,
                               bb_signals: pd.Series, scalp_trend_signals: pd.Series,
                               stoch_signals: pd.Series, williams_signals: pd.Series,
                               volume_signals: pd.Series, velocity_signals: pd.Series) -> pd.Series:
        """Generate human-readable reasons for signals"""
        reasons = pd.Series('', index=signals.index)
        
        for idx in signals.index[signals['signal'] != 'HOLD']:
            reason_parts = []
            
            if abs(fast_rsi_signals[idx]) > 0.5:
                rsi_val = indicators.get('rsi_fast', indicators.get('rsi', pd.Series(50, index=indicators.index)))[idx]
                if fast_rsi_signals[idx] > 0:
                    reason_parts.append(f"Fast RSI oversold ({rsi_val:.1f})")
                else:
                    reason_parts.append(f"Fast RSI overbought ({rsi_val:.1f})")
            
            if abs(macd_signals[idx]) > 0.5:
                if macd_signals[idx] > 0:
                    reason_parts.append("MACD scalp bullish")
                else:
                    reason_parts.append("MACD scalp bearish")
            
            if abs(scalp_trend_signals[idx]) > 0.6:
                if scalp_trend_signals[idx] > 0:
                    reason_parts.append("Scalp trend UP")
                else:
                    reason_parts.append("Scalp trend DOWN")
            
            if abs(williams_signals[idx]) > 0.6:
                if williams_signals[idx] > 0:
                    reason_parts.append("Williams %R oversold")
                else:
                    reason_parts.append("Williams %R overbought")
            
            if abs(velocity_signals[idx]) > 0.5:
                if velocity_signals[idx] > 0:
                    reason_parts.append("Strong upward momentum")
                else:
                    reason_parts.append("Strong downward momentum")
            
            if abs(volume_signals[idx]) > 0.3:
                reason_parts.append("Volume spike")
            
            reasons[idx] = "; ".join(reason_parts) if reason_parts else "Scalp signals aligned"
        
        return reasons
    
    def calculate_signal_strength(self, score: float) -> str:
        """Convert signal score to strength description"""
        abs_score = abs(score)
        if abs_score >= 0.8:
            return "Very Strong"
        elif abs_score >= 0.6:
            return "Strong"
        elif abs_score >= 0.4:
            return "Moderate"
        elif abs_score >= 0.2:
            return "Weak"
        else:
            return "Very Weak"

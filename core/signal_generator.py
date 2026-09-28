import pandas as pd
import numpy as np
from typing import Dict, Any

class SignalGenerator:
    """Class for generating trading signals based on technical indicators"""
    
    def __init__(self):
        # Enhanced weights for swing trading
        self.signal_weights = {
            'rsi': 0.20,
            'macd': 0.25,  # Higher weight for trend following
            'bollinger': 0.15,
            'swing_trend': 0.15,
            'stochastic': 0.08,
            'williams_r': 0.06,
            'volume': 0.04,
            'momentum': 0.03,
            'support_resistance': 0.02,
            'breakout_signal': 0.02
        }
    
    def generate_signals(self, data: pd.DataFrame, indicators: pd.DataFrame, threshold: float = 0.3) -> pd.DataFrame:
        """Generate swing trading optimized signals"""
        signals = pd.DataFrame(index=data.index)
        
        # Calculate individual signal components for swing trading
        rsi_signals = self._rsi_signals(indicators)
        macd_signals = self._macd_signals(indicators)
        bb_signals = self._bollinger_signals(data, indicators)
        swing_trend_signals = self._swing_trend_signals(indicators)
        stoch_signals = self._stochastic_signals(indicators)
        williams_signals = self._williams_r_signals(indicators)
        volume_signals = self._volume_signals(data, indicators)
        momentum_signals = self._momentum_signals(indicators)
        support_resistance_signals = self._support_resistance_signals(indicators)
        breakout_signals = self._breakout_signals(indicators)
        
        # Per-indicator contributions, kept alongside the final score so a BUY/SELL call
        # is auditable (which sub-signals actually drove it) rather than only narrated.
        contributions = {
            'rsi': rsi_signals * self.signal_weights['rsi'],
            'macd': macd_signals * self.signal_weights['macd'],
            'bollinger': bb_signals * self.signal_weights['bollinger'],
            'swing_trend': swing_trend_signals * self.signal_weights['swing_trend'],
            'stochastic': stoch_signals * self.signal_weights['stochastic'],
            'williams_r': williams_signals * self.signal_weights['williams_r'],
            'volume': volume_signals * self.signal_weights['volume'],
            'momentum': momentum_signals * self.signal_weights['momentum'],
            'support_resistance': support_resistance_signals * self.signal_weights['support_resistance'],
            'breakout_signal': breakout_signals * self.signal_weights['breakout_signal'],
        }

        # Combine signals with swing trading weights
        combined_score = sum(contributions.values())

        # Generate final signals
        signals['score'] = combined_score
        signals['signal'] = 'HOLD'
        signals['strength'] = np.abs(combined_score)
        signals['price'] = data['Close']
        signals['reason'] = ''

        for name, contribution in contributions.items():
            signals[f'contrib_{name}'] = contribution
        
        # Apply threshold
        buy_condition = combined_score > threshold
        sell_condition = combined_score < -threshold
        
        signals.loc[buy_condition, 'signal'] = 'BUY'
        signals.loc[sell_condition, 'signal'] = 'SELL'
        
        # Add reasoning
        signals['reason'] = self._generate_swing_reasons(
            signals, indicators, rsi_signals, macd_signals, 
            bb_signals, swing_trend_signals, stoch_signals, williams_signals, 
            volume_signals, momentum_signals
        )
        
        return signals
    
    def _rsi_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate RSI signals for swing trading"""
        rsi = indicators.get('rsi', None)
        if rsi is None or rsi.empty:
            return pd.Series(0.0, index=indicators.index)
            
        signals = pd.Series(0.0, index=indicators.index)
        
        # Standard swing trading RSI thresholds
        signals[rsi < 30] = 0.8   # Oversold - buy signal
        signals[rsi < 25] = 1.0   # Very oversold - strong buy
        signals[rsi > 70] = -0.8  # Overbought - sell signal
        signals[rsi > 75] = -1.0  # Very overbought - strong sell
        
        # RSI divergence detection for swing entries
        rsi_momentum = rsi.diff(5)  # Longer period for swing
        signals[rsi_momentum > 5] += 0.2
        signals[rsi_momentum < -5] -= 0.2
        
        return signals.clip(-1, 1)
    
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
    
    def _williams_r_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate Williams %R signals for scalping"""
        williams = indicators.get('williams_r', None)
        if williams is None:
            return pd.Series(0.0, index=indicators.index)
            
        signals = pd.Series(0.0, index=indicators.index)
        
        # Oversold/Overbought levels for scalping
        signals[williams < -85] = 0.9   # Strong buy
        signals[williams < -80] = 0.6   # Moderate buy
        signals[williams > -15] = -0.9  # Strong sell
        signals[williams > -20] = -0.6  # Moderate sell
        
        return signals
    
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
    
    def _generate_swing_reasons(self, signals: pd.DataFrame, indicators: pd.DataFrame,
                               rsi_signals: pd.Series, macd_signals: pd.Series,
                               bb_signals: pd.Series, swing_trend_signals: pd.Series,
                               stoch_signals: pd.Series, williams_signals: pd.Series,
                               volume_signals: pd.Series, momentum_signals: pd.Series) -> pd.Series:
        """Generate human-readable reasons for swing trading signals"""
        reasons = pd.Series('', index=signals.index)
        
        for idx in signals.index[signals['signal'] != 'HOLD']:
            reason_parts = []
            
            if abs(rsi_signals[idx]) > 0.5:
                rsi_val = indicators.get('rsi', pd.Series(50, index=indicators.index))[idx]
                if rsi_signals[idx] > 0:
                    reason_parts.append(f"RSI oversold ({rsi_val:.1f})")
                else:
                    reason_parts.append(f"RSI overbought ({rsi_val:.1f})")
            
            if abs(macd_signals[idx]) > 0.5:
                if macd_signals[idx] > 0:
                    reason_parts.append("MACD swing bullish")
                else:
                    reason_parts.append("MACD swing bearish")
            
            if abs(swing_trend_signals[idx]) > 0.4:
                if swing_trend_signals[idx] > 0:
                    reason_parts.append("Swing trend UP")
                else:
                    reason_parts.append("Swing trend DOWN")
            
            if abs(williams_signals[idx]) > 0.6:
                if williams_signals[idx] > 0:
                    reason_parts.append("Williams %R oversold")
                else:
                    reason_parts.append("Williams %R overbought")
            
            if abs(momentum_signals[idx]) > 0.3:
                if momentum_signals[idx] > 0:
                    reason_parts.append("Positive momentum")
                else:
                    reason_parts.append("Negative momentum")
            
            if abs(volume_signals[idx]) > 0.3:
                reason_parts.append("Volume confirmation")
            
            reasons[idx] = "; ".join(reason_parts) if reason_parts else "Swing signals aligned"
        
        return reasons
    
    def _swing_trend_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate swing trend signals"""
        swing_trend = indicators.get('swing_trend', pd.Series(0, index=indicators.index))
        signals = pd.Series(0.0, index=indicators.index)
        
        # Medium-term trend following for swing trading
        trend_changes = swing_trend.diff()
        
        signals[swing_trend > 0] = 0.6   # Uptrend
        signals[swing_trend < 0] = -0.6  # Downtrend
        
        # Moderate boost on trend changes (less aggressive than scalping)
        signals[trend_changes > 0] += 0.2
        signals[trend_changes < 0] -= 0.2
        
        return signals
    
    def _momentum_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate momentum signals for swing trading"""
        momentum = indicators.get('momentum', None)
        if momentum is None:
            return pd.Series(0.0, index=indicators.index)
            
        signals = pd.Series(0.0, index=indicators.index)
        
        # Medium-term momentum thresholds
        momentum_std = momentum.rolling(20).std()
        threshold = momentum_std * 1.2
        
        signals[momentum > threshold] = 0.5   # Positive momentum
        signals[momentum < -threshold] = -0.5  # Negative momentum
        
        return signals
    
    def _support_resistance_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate support/resistance signals for swing trading"""
        sr_levels = indicators.get('support_resistance', None)
        if sr_levels is None:
            return pd.Series(0.0, index=indicators.index)
            
        signals = pd.Series(0.0, index=indicators.index)
        
        # Support level buy signals
        signals[sr_levels < 0] = 0.3  # Near support - potential buy
        # Resistance level sell signals  
        signals[sr_levels > 0] = -0.3  # Near resistance - potential sell
        
        return signals
    
    def _breakout_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Generate breakout signals for swing trading"""
        breakout = indicators.get('breakout_signal', None)
        if breakout is None:
            return pd.Series(0.0, index=indicators.index)
            
        signals = pd.Series(0.0, index=indicators.index)
        
        # Breakout signals for swing entries
        signals[breakout > 0] = 0.7   # Upward breakout - buy
        signals[breakout < 0] = -0.7  # Downward breakout - sell
        
        return signals
    
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

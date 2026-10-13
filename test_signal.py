import sys, os
sys.path.append(r"c:/Users/Ragil Immanuvel/Downloads/z-20260925T063727Z-1-001/z/TradeSignal")
from core.signal_generator import SignalGenerator
import pandas as pd, numpy as np

# Dummy data
data = pd.DataFrame({
    'Close': np.random.rand(10) * 100 + 100,
    'Volume': np.random.randint(1000, 5000, size=10),
    'Symbol': ['TEST'] * 10
})
# Dummy indicators
indicators = pd.DataFrame({
    'rsi': np.random.rand(10) * 100,
    'macd': np.random.randn(10),
    'macd_signal': np.random.randn(10),
    'macd_histogram': np.random.randn(10),
    'bb_upper': data['Close'] + 5,
    'bb_lower': data['Close'] - 5,
    'bb_middle': data['Close'],
    'bb_position': np.random.rand(10),
    'bb_width': np.random.rand(10) * 2,
    'williams_r': np.random.rand(10) * -100,
    'stoch_k': np.random.rand(10) * 100,
    'stoch_d': np.random.rand(10) * 100,
    'volume_ratio': np.random.rand(10) * 2,
    'swing_trend': np.random.choice([-1, 1], size=10),
    'momentum': np.random.randn(10),
    'support_resistance': np.random.randn(10),
    # add other needed columns as placeholders
})

sg = SignalGenerator(default_preset='holy_trinity')
signals = sg.generate_signals(data, indicators)
print(signals[['signal','score','reason']])

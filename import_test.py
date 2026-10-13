import sys, os
sys.path.append(r"c:/Users/Ragil Immanuvel/Downloads/z-20260925T063727Z-1-001/z/TradeSignal")
from core.signal_generator import SignalGenerator
print('Loaded SignalGenerator presets:', list(SignalGenerator.PRESETS.keys()))

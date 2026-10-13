import pandas as pd
from typing import Dict, Any
from .cache_utils import ttl_cache


class MTFConfluence:
    """Evaluates multi-timeframe signal alignment across 1m, 5m, 15m, 1h, 4h, 1d."""

    MTF_TIMEFRAMES = [
        {"tf": "1m", "period": "1d", "label": "1-Min Scalp"},
        {"tf": "5m", "period": "5d", "label": "5-Min Momentum"},
        {"tf": "15m", "period": "5d", "label": "15-Min Swing Entry"},
        {"tf": "1h", "period": "1mo", "label": "1-Hour Trend"},
        {"tf": "4h", "period": "3mo", "label": "4-Hour Macro"},
        {"tf": "1d", "period": "1y", "label": "Daily Baseline"}
    ]

    @staticmethod
    @ttl_cache(ttl=60)
    def calculate_confluence(_data_fetcher, _technical_indicators, _signal_generator,
                             symbol: str, indicator_params: dict, signal_threshold: float = 0.25) -> Dict[str, Any]:
        """Compute signal for each timeframe and determine multi-timeframe confluence."""
        results = []
        buy_count = 0
        sell_count = 0
        hold_count = 0

        for item in MTFConfluence.MTF_TIMEFRAMES:
            tf = item["tf"]
            period = item["period"]
            label = item["label"]

            try:
                data = _data_fetcher.get_data(symbol, period, tf)
                if not data.empty and len(data) >= 20:
                    indicators = _technical_indicators.calculate_all(data, indicator_params)
                    signals = _signal_generator.generate_signals(data, indicators, threshold=signal_threshold)
                    
                    if not signals.empty:
                        last_sig = signals.iloc[-1]
                        sig_type = last_sig.get('signal', 'HOLD')
                        strength = float(last_sig.get('strength', 0.0))
                        price = float(data['Close'].iloc[-1])
                    else:
                        sig_type = 'HOLD'
                        strength = 0.0
                        price = float(data['Close'].iloc[-1])
                else:
                    sig_type = 'HOLD'
                    strength = 0.0
                    price = 0.0
            except Exception:
                sig_type = 'HOLD'
                strength = 0.0
                price = 0.0

            if sig_type == 'BUY':
                buy_count += 1
            elif sig_type == 'SELL':
                sell_count += 1
            else:
                hold_count += 1

            results.append({
                "timeframe": tf.upper(),
                "label": label,
                "signal": sig_type,
                "strength": strength,
                "price": price
            })

        total = len(results)
        bullish_pct = (buy_count / total) * 100
        bearish_pct = (sell_count / total) * 100

        if buy_count >= 4:
            verdict = "🔥 STRONG BULLISH ALIGNMENT"
            verdict_badge = "STRONG BUY"
            color = "#00E676"
            advice = "High-conviction long momentum across multiple time horizons. Ideal breakout edge."
        elif sell_count >= 4:
            verdict = "🩸 STRONG BEARISH ALIGNMENT"
            verdict_badge = "STRONG SELL"
            color = "#FF3366"
            advice = "Heavy distribution detected across multiple time horizons. High downside risk."
        elif buy_count > sell_count and buy_count >= 2:
            verdict = "🟢 LEANING BULLISH CONFLUENCE"
            verdict_badge = "MODERATE BUY"
            color = "#00E676"
            advice = "Shorter-term timeframes showing upside push against neutral macro background."
        elif sell_count > buy_count and sell_count >= 2:
            verdict = "🔴 LEANING BEARISH CONFLUENCE"
            verdict_badge = "MODERATE SELL"
            color = "#FF3366"
            advice = "Selling pressure emerging on lower frames. Exercise caution on long positions."
        else:
            verdict = "⚪ MIXED / CHOPPY MARKET"
            verdict_badge = "NEUTRAL"
            color = "#FFB300"
            advice = "Timeframes are conflicting. Market is range-bound without clear directional consensus."

        return {
            "symbol": symbol,
            "matrix": results,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "total_timeframes": total,
            "bullish_pct": bullish_pct,
            "bearish_pct": bearish_pct,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "color": color,
            "advice": advice
        }

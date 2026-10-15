"""FastAPI High-Speed Trading Application Backend for TradeSignal

Provides sub-millisecond cached responses for:
- TradingView Lightweight Charts OHLCV candles
- Pristine BUY / SELL trigger markers
- Multi-Timeframe Confluence Matrix
- Real-time Live Ticker & AI Trade Thesis
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

# Ensure parent directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import numpy as np
import pandas as pd

from core.data_fetcher import DataFetcher
from core.technical_indicators import TechnicalIndicators
from core.signal_generator import SignalGenerator
from core.pattern_recognition import PatternRecognition
from core.mtf_confluence import MTFConfluence
from core.ml_predictor import MarketPredictor
from core.sentiment_analyzer import fetch_structured_news, compute_sentiment_score
from core.backtester import Backtester
from core.regime_classifier import MarketRegimeClassifier
import asyncio
from datetime import datetime, timezone, timedelta
from specs.schemas.api_spec import (
    CandlesResponseSpec,
    ConfluenceResponseSpec,
    TickerResponseSpec,
    PresetsResponseSpec,
    SignalResponseSpec,
    MLPredictionSpec,
)

app = FastAPI(
    title="TradeSignal High-Speed Web App",
    description="Spec-Driven Algorithmic Trading API with formal OpenAPI contracts",
    version="2.0"
)

# 1. High-Performance GZip Compression Middleware (80%+ wire size reduction)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. High-Performance Static Asset Caching Middleware
@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return response

data_fetcher = DataFetcher()
tech_indicators = TechnicalIndicators()
signal_generator = SignalGenerator()
market_predictor = MarketPredictor()
backtester = Backtester()
regime_classifier = MarketRegimeClassifier()

# In-memory cache with timestamps for lightning speed
_CANDLE_CACHE: Dict[str, Dict[str, Any]] = {}
_CONFLUENCE_CACHE: Dict[str, Dict[str, Any]] = {}
_NEWS_CACHE: Dict[str, Dict[str, Any]] = {}
_BACKTEST_CACHE: Dict[str, Dict[str, Any]] = {}
_REGIME_CACHE: Dict[str, Dict[str, Any]] = {}
_TICKER_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0.0}
CACHE_TTL = 30  # 30 seconds
TICKER_TTL = 30  # 30 seconds

async def _background_cache_prewarmer():
    """Background task to pre-fetch & pre-calculate candles and ML forecasts for top symbols in RAM."""
    await asyncio.sleep(2)  # Wait for startup
    warm_symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    while True:
        for sym in warm_symbols:
            try:
                # Pre-warm default 1h holy_trinity in memory
                await get_candles(symbol=sym, timeframe="1h", period="1mo", threshold=0.3, preset="holy_trinity", model_type="ml", horizon=3)
            except Exception:
                pass
            await asyncio.sleep(0.5)
        await asyncio.sleep(15)

@app.on_event("startup")
async def startup_prewarm():
    asyncio.create_task(_background_cache_prewarmer())

PERIOD_DEFAULTS = {
    "1m": "1d",
    "3m": "3d",
    "5m": "5d",
    "15m": "1mo",
    "30m": "1mo",
    "1h": "1mo",
    "4h": "3mo",
    "1d": "1y"
}

WATCHLIST_SYMBOLS = [
    {"symbol": "BTC-USD", "name": "Bitcoin", "type": "crypto"},
    {"symbol": "ETH-USD", "name": "Ethereum", "type": "crypto"},
    {"symbol": "SOL-USD", "name": "Solana", "type": "crypto"},
    {"symbol": "XRP-USD", "name": "XRP", "type": "crypto"},
    {"symbol": "DOGE-USD", "name": "Dogecoin", "type": "crypto"},
    {"symbol": "ADA-USD", "name": "Cardano", "type": "crypto"},
    {"symbol": "BNB-USD", "name": "BNB", "type": "crypto"},
]


@app.get("/api/ticker", response_model=TickerResponseSpec)
async def get_ticker_data():
    """Return live prices and 24h change for the ticker banner with high-speed in-memory caching."""
    now = time.time()
    if _TICKER_CACHE["data"] and (now - _TICKER_CACHE["timestamp"] < TICKER_TTL):
        return _TICKER_CACHE["data"]

    def _fetch_tickers():
        results = []
        binance_data = {}
        try:
            req = urllib.request.Request(
                'https://api.binance.com/api/v3/ticker/24hr',
                headers={'User-Agent': 'TradeSignal/2.0'}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                raw_list = json.loads(resp.read().decode())
                binance_data = {
                    item['symbol']: (float(item['lastPrice']), float(item['priceChangePercent']))
                    for item in raw_list
                }
        except Exception as e:
            logger.warning(f"Bulk Binance ticker fetch failed: {e}")

        for item in WATCHLIST_SYMBOLS:
            sym = item["symbol"]
            clean = sym.upper().replace("-USD", "").replace("USDT", "")
            binance_sym = f"{clean}USDT"
            
            if binance_sym in binance_data:
                price_val, change = binance_data[binance_sym]
            else:
                price_info = data_fetcher.get_real_time_price(sym)
                price_val = float(price_info.get('price', 0.0)) if isinstance(price_info, dict) else float(price_info or 0.0)
                change = 0.0
                try:
                    df = data_fetcher.get_data(sym, period="2d", timeframe="1d")
                    if len(df) >= 2:
                        prev_close = float(df['Close'].iloc[-2])
                        cur_close = float(df['Close'].iloc[-1])
                        change = ((cur_close - prev_close) / prev_close) * 100
                except Exception:
                    pass

            results.append({
                "symbol": sym.replace("-USD", ""),
                "full_symbol": sym,
                "name": item["name"],
                "price": round(price_val, 4 if price_val < 10 else 2),
                "change_pct": round(change, 2)
            })
        return {"tickers": results}

    data = await asyncio.to_thread(_fetch_tickers)
    _TICKER_CACHE["data"] = data
    _TICKER_CACHE["timestamp"] = time.time()
    return data


@app.get("/api/presets", response_model=PresetsResponseSpec)
async def get_presets():
    """Return available indicator combo presets."""
    return {"presets": SignalGenerator.PRESETS}


@app.get("/api/candles", response_model=CandlesResponseSpec)
async def get_candles(
    symbol: str = Query("BTC-USD"),
    timeframe: str = Query("1h"),
    period: Optional[str] = Query(None),
    threshold: float = Query(0.3),
    preset: str = Query("holy_trinity"),
    model_type: str = Query("ml"),
    horizon: int = Query(3)
):
    """Return lightweight-charts formatted OHLCV, markers, and ML/DL forecasts."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"

    if not isinstance(period, str) or not period:
        period = PERIOD_DEFAULTS.get(str(timeframe), "1mo")

    cache_key = f"{symbol}_{timeframe}_{period}_{threshold}_{preset}_{model_type}_{horizon}"
    now = time.time()
    if cache_key in _CANDLE_CACHE:
        entry = _CANDLE_CACHE[cache_key]
        if now - entry["timestamp"] < CACHE_TTL:
            return entry["data"]

    def _compute_candle_analytics():
        df = data_fetcher.get_data(symbol, period, timeframe)
        if df.empty:
            return df, None, None, None, None, None
        inds = tech_indicators.calculate_all(df, {}, preset=preset)
        sigs = signal_generator.generate_signals(df, inds, threshold, preset=preset)
        pats = PatternRecognition.detect_patterns(df.iloc[-100:])
        latest_pat = pats.iloc[-1].to_dict() if not pats.empty else None
        funds = {}
        return df, inds, sigs, pats, latest_pat, funds

    try:
        data, indicators, signals, patterns, latest_pattern, fundamentals = await asyncio.to_thread(_compute_candle_analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

    # Convert candles to TradingView Lightweight-Charts format:
    # { time: unix_timestamp_in_seconds, open, high, low, close }
    candles = []
    volume_data = []
    prev_close = None

    for idx, row in data.iterrows():
        # Handle index timestamp (could be Timestamp or DatetimeIndex)
        ts = int(idx.timestamp()) if hasattr(idx, 'timestamp') else int(pd.to_datetime(idx).timestamp())
        o = float(row['Open'])
        h = float(row['High'])
        l = float(row['Low'])
        c = float(row['Close'])
        v = float(row['Volume']) if 'Volume' in row else 0.0

        candles.append({
            "time": ts,
            "open": round(o, 4 if c < 10 else 2),
            "high": round(h, 4 if c < 10 else 2),
            "low": round(l, 4 if c < 10 else 2),
            "close": round(c, 4 if c < 10 else 2)
        })

        vol_color = "rgba(0, 230, 118, 0.4)" if (prev_close is None or c >= prev_close) else "rgba(255, 51, 102, 0.4)"
        volume_data.append({
            "time": ts,
            "value": v,
            "color": vol_color
        })
        prev_close = c

    # Generate ONLY BUY/SELL markers at signal triggers (transition points)
    markers = []
    prev_sig = None

    for i in range(len(signals)):
        cur_sig = signals['signal'].iloc[i]
        if cur_sig in ['BUY', 'SELL'] and cur_sig != prev_sig:
            ts = candles[i]["time"]
            strength = float(signals['strength'].iloc[i]) if 'strength' in signals else 0.5
            if cur_sig == 'BUY':
                markers.append({
                    "time": ts,
                    "position": "belowBar",
                    "color": "#00E676",
                    "shape": "arrowUp",
                    "text": f"BUY ({strength:.0%})",
                    "size": 2
                })
            else:
                markers.append({
                    "time": ts,
                    "position": "aboveBar",
                    "color": "#FF3366",
                    "shape": "arrowDown",
                    "text": f"SELL ({strength:.0%})",
                    "size": 2
                })
        prev_sig = cur_sig

    latest_price = candles[-1]["close"]
    latest_sig = signals['signal'].iloc[-1] if not signals.empty else "HOLD"
    latest_strength = float(signals['strength'].iloc[-1]) if not signals.empty else 0.0
    latest_score = float(signals['score'].iloc[-1]) if not signals.empty and 'score' in signals else 0.0

    # ATR for TP/SL targets
    atr_val = indicators['atr'].iloc[-1] if 'atr' in indicators and not indicators['atr'].isna().iloc[-1] else (latest_price * 0.02)
    tp = latest_price + (2.0 * atr_val) if latest_sig == 'BUY' else latest_price - (2.0 * atr_val)
    sl = latest_price - (1.5 * atr_val) if latest_sig == 'BUY' else latest_price + (1.5 * atr_val)

    # Candlestick pattern & AI thesis
    thesis = PatternRecognition.generate_trade_thesis(
        symbol=symbol,
        current_price=latest_price,
        signal_row={'signal': latest_sig, 'strength': latest_strength},
        pattern_row=latest_pattern,
        fundamentals=fundamentals
    )

    # Machine Learning / Deep Learning Predictive Inference (Non-blocking)
    ml_prediction = await asyncio.to_thread(market_predictor.predict, data, indicators, model_type=model_type, horizon=horizon)

    response_payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "volume": volume_data,
        "markers": markers,
        "current_price": latest_price,
        "current_signal": {
            "signal": latest_sig,
            "strength": round(latest_strength, 2),
            "score": round(latest_score, 3)
        },
        "thesis": thesis,
        "targets": {
            "tp": round(tp, 4 if latest_price < 10 else 2),
            "sl": round(sl, 4 if latest_price < 10 else 2),
            "atr": round(atr_val, 4 if latest_price < 10 else 2)
        },
        "preset": preset,
        "preset_info": SignalGenerator.PRESETS.get(preset, SignalGenerator.PRESETS['holy_trinity']),
        "available_presets": SignalGenerator.PRESETS,
        "ml_prediction": ml_prediction,
        "regime": regime_classifier.detect_regime(data, indicators)
    }

    _CANDLE_CACHE[cache_key] = {"timestamp": now, "data": response_payload}
    return response_payload


@app.get("/api/predict", response_model=MLPredictionSpec)
async def get_market_prediction(
    symbol: str = Query("BTC-USD"),
    timeframe: str = Query("1h"),
    model_type: str = Query("ml"),
    horizon: int = Query(3, ge=1, le=10)
):
    """Return statistical Quant ML or Deep LSTM predictive forecast."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"

    period = PERIOD_DEFAULTS.get(timeframe, "1mo")
    try:
        data = data_fetcher.get_data(symbol, period, timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

    indicators = tech_indicators.calculate_all(data, {})
    return market_predictor.predict(data, indicators, model_type=model_type, horizon=horizon)


@app.get("/api/confluence", response_model=ConfluenceResponseSpec)
async def get_confluence(symbol: str = Query("BTC-USD"), threshold: float = Query(0.3)):
    """Return MTF confluence matrix for 1m, 5m, 15m, 1h, 4h, 1d."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"

    cache_key = f"{symbol}_{threshold}"
    now = time.time()
    if cache_key in _CONFLUENCE_CACHE:
        entry = _CONFLUENCE_CACHE[cache_key]
        if now - entry["timestamp"] < CACHE_TTL:
            return entry["data"]

    res = await asyncio.to_thread(
        MTFConfluence.calculate_confluence,
        data_fetcher,
        tech_indicators,
        signal_generator,
        symbol,
        {},
        threshold
    )
    _CONFLUENCE_CACHE[cache_key] = {"timestamp": now, "data": res}
    return res


@app.get("/api/signal", response_model=SignalResponseSpec)
async def get_signal_endpoint(
    symbol: str = Query("BTC-USD"),
    timeframe: str = Query("1h"),
    threshold: float = Query(0.3),
    preset: str = Query("holy_trinity")
):
    """Return formally typed quantitative signal response conforming to SignalResponseSpec."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"

    period = PERIOD_DEFAULTS.get(timeframe, "1mo")
    data = data_fetcher.get_data(symbol, period=period, timeframe=timeframe)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")

    indicators = tech_indicators.calculate_all(data, {})
    signals = signal_generator.generate_signals(data, indicators, threshold, preset=preset)

    latest_price = float(data['Close'].iloc[-1])
    latest_sig = signals['signal'].iloc[-1] if not signals.empty else "HOLD"
    latest_strength = float(signals['strength'].iloc[-1]) if not signals.empty else 0.0
    latest_reason = signals['reason'].iloc[-1] if not signals.empty and 'reason' in signals else "Consensus quant edge."

    # ATR for TP/SL targets
    atr_val = float(indicators['atr'].iloc[-1]) if 'atr' in indicators and not indicators['atr'].isna().iloc[-1] else (latest_price * 0.02)
    tp = latest_price + (2.0 * atr_val) if latest_sig == 'BUY' else latest_price - (2.0 * atr_val)
    sl = latest_price - (1.5 * atr_val) if latest_sig == 'BUY' else latest_price + (1.5 * atr_val)

    now_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)

    return SignalResponseSpec(
        symbol=symbol,
        timeframe=timeframe,
        timestamp_ist=now_ist.strftime('%Y-%m-%d %I:%M:%S %p IST'),
        signal=latest_sig,
        confidence=round(latest_strength, 2),
        price_inr=round(latest_price, 2),
        target_price_inr=round(tp, 2),
        stop_loss_inr=round(sl, 2),
        strategy_id=preset,
        rationale=str(latest_reason)
    )


@app.get("/api/news")
async def get_market_news(symbol: str = Query("BTC-USD")):
    """Return real-time financial headlines, sentiment score, and fundamentals."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"

    now = time.time()
    if symbol in _NEWS_CACHE:
        entry = _NEWS_CACHE[symbol]
        if now - entry["timestamp"] < 90:  # 90s cache
            return entry["data"]

    def _fetch_news_payload():
        headlines = fetch_structured_news(symbol, limit=8)
        scores = [h["score"] for h in headlines]
        avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0

        sentiment_label = "EXTREME GREED (BULLISH)" if avg_score >= 0.35 else (
            "BULLISH" if avg_score >= 0.10 else (
                "EXTREME FEAR (BEARISH)" if avg_score <= -0.35 else (
                    "BEARISH" if avg_score <= -0.10 else "NEUTRAL"
                )
            )
        )

        fundamentals = data_fetcher.get_asset_fundamentals(symbol)

        return {
            "symbol": symbol,
            "sentiment_score": avg_score,
            "sentiment_label": sentiment_label,
            "headline_count": len(headlines),
            "headlines": headlines,
            "fundamentals": fundamentals
        }

    payload = await asyncio.to_thread(_fetch_news_payload)
    _NEWS_CACHE[symbol] = {"timestamp": now, "data": payload}
    return payload


@app.get("/api/regime")
async def get_market_regime(
    symbol: str = Query("BTC-USD"),
    timeframe: str = Query("1h"),
    period: Optional[str] = Query(None)
):
    """Detect current macro market regime (Trending Bull/Bear, Range, or Vol Hazard)."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"
    if not isinstance(period, str) or not period:
        period = PERIOD_DEFAULTS.get(str(timeframe), "1mo")

    cache_key = f"{symbol}_{timeframe}_{period}"
    now = time.time()
    if cache_key in _REGIME_CACHE:
        entry = _REGIME_CACHE[cache_key]
        if now - entry["timestamp"] < 30:
            return entry["data"]

    try:
        data = data_fetcher.get_data(symbol, period, timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    if data.empty or len(data) < 20:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

    indicators = tech_indicators.calculate_all(data, {})
    regime = regime_classifier.detect_regime(data, indicators)
    _REGIME_CACHE[cache_key] = {"timestamp": now, "data": regime}
    return regime


@app.get("/api/backtest")
async def run_strategy_backtest(
    symbol: str = Query("BTC-USD"),
    timeframe: str = Query("1h"),
    period: Optional[str] = Query("3mo"),
    threshold: float = Query(0.3),
    preset: str = Query("holy_trinity"),
    initial_capital: float = Query(100000.0),
    stop_loss_pct: Optional[float] = Query(0.03),
    take_profit_pct: Optional[float] = Query(0.06),
):
    """Run an institutional backtest and return performance metrics + equity curve."""
    if not symbol.endswith("-USD") and not ("." in symbol):
        symbol = f"{symbol}-USD"
    if not isinstance(period, str) or not period:
        period = "3mo"

    cache_key = f"{symbol}_{timeframe}_{period}_{threshold}_{preset}_{initial_capital}_{stop_loss_pct}_{take_profit_pct}"
    now = time.time()
    if cache_key in _BACKTEST_CACHE:
        entry = _BACKTEST_CACHE[cache_key]
        if now - entry["timestamp"] < 90:  # 90 second backtest cache
            return entry["data"]

    try:
        data = data_fetcher.get_data(symbol, period, timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data fetch error: {str(e)}")

    if data.empty or len(data) < 20:
        raise HTTPException(status_code=404, detail=f"Insufficient historical data for {symbol}")

    indicators = tech_indicators.calculate_all(data, {})
    signals = signal_generator.generate_signals(data, indicators, threshold, preset=preset)

    results = backtester.run_backtest(
        data=data,
        signals=signals,
        initial_capital=initial_capital,
        position_size_pct=0.95,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )

    # Convert portfolio history to lightweight charts / canvas format
    portfolio_df = results.get("portfolio_history", pd.DataFrame())
    equity_curve = []
    if not portfolio_df.empty:
        peak_val = initial_capital
        for ts, row in portfolio_df.iterrows():
            unix_time = int(ts.timestamp()) if hasattr(ts, 'timestamp') else int(pd.to_datetime(ts).timestamp())
            val = round(float(row.get("portfolio_value", initial_capital)), 2)
            if val > peak_val:
                peak_val = val
            dd = round(float(((val - peak_val) / peak_val) * 100), 2)
            equity_curve.append({
                "time": unix_time,
                "value": val,
                "cash": round(float(row.get("cash", initial_capital)), 2),
                "drawdown": dd
            })

    # Format trades list
    clean_trades = []
    for t in results.get("trades", []):
        ts = t.get("timestamp")
        unix_time = int(ts.timestamp()) if hasattr(ts, 'timestamp') else int(pd.to_datetime(ts).timestamp())
        clean_trades.append({
            "time": unix_time,
            "type": t.get("type"),
            "shares": round(float(t.get("shares", 0)), 6),
            "price": round(float(t.get("price", 0)), 4),
            "profit_loss": round(float(t.get("profit_loss", 0)), 2),
            "profit_loss_pct": round(float(t.get("profit_loss_pct", 0)), 2),
            "commission": round(float(t.get("commission", 0)), 2)
        })

    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "period": period,
        "preset": preset,
        "initial_capital": initial_capital,
        "final_value": round(float(results.get("final_value", initial_capital)), 2),
        "total_return": round(float(results.get("total_return", 0.0)), 2),
        "buy_hold_return": round(float(results.get("buy_hold_return", 0.0)), 2),
        "alpha": round(float(results.get("alpha", 0.0)), 2),
        "total_trades": int(results.get("total_trades", 0)),
        "win_rate": round(float(results.get("win_rate", 0.0)), 1),
        "profitable_trades": int(results.get("profitable_trades", 0)),
        "losing_trades": int(results.get("losing_trades", 0)),
        "max_drawdown": round(float(results.get("max_drawdown", 0.0)), 2),
        "sharpe_ratio": round(float(results.get("sharpe_ratio", 0.0)), 2),
        "sortino_ratio": round(float(results.get("sortino_ratio", 0.0)), 2),
        "calmar_ratio": round(float(results.get("calmar_ratio", 0.0)), 2),
        "profit_factor": round(float(results.get("profit_factor", 0.0)), 2),
        "total_commission": round(float(results.get("total_commission", 0.0)), 2),
        "equity_curve": equity_curve,
        "trades": clean_trades[:100]
    }
    _BACKTEST_CACHE[cache_key] = {"timestamp": now, "data": payload}
    return payload


# Mount static files directory
STATIC_DIR = BASE_DIR / "webapp" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting TradeSignal High-Speed Web App on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

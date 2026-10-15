import json
import urllib.request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import logging
from .cache_utils import ttl_cache

logger = logging.getLogger(__name__)
import requests
from specs.schemas.market_data_spec import validate_ohlcv


@runtime_checkable
class MarketDataSource(Protocol):
    """The surface app.py actually depends on. Everything downstream (TechnicalIndicators,
    SignalGenerator, Backtester) only ever sees the DataFrames/dicts these four methods
    return — so swapping yfinance for a crypto-native exchange API just means writing a
    class with this shape and pointing app.py's `data_fetcher = DataFetcher()` at it
    instead. No structural inheritance is required; this is checked by shape, not by type.
    """
    def get_usd_to_inr_rate(self) -> float: ...
    def get_data(self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame: ...
    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime,
                             interval: str = "1d") -> pd.DataFrame: ...
    def get_real_time_price(self, symbol: str) -> dict: ...
def is_indian_stock(symbol: str) -> bool:
    s = symbol.strip().upper()
    return s.endswith('.NS') or s.endswith('.BO') or s.startswith(('^NSE', '^BSE'))


def to_yf_symbol(symbol: str, is_stock: bool = False) -> tuple[str, bool]:
    """Returns (yahoo_finance_symbol, is_inr_native).
    Indian stocks are quoted natively in INR on Yahoo Finance (.NS / .BO).
    Crypto pairs are quoted in USD on Yahoo Finance and converted to INR.
    """
    s = symbol.strip().upper()
    if is_stock or is_indian_stock(s):
        if not (s.endswith('.NS') or s.endswith('.BO') or s.startswith('^')):
            s = f"{s}.NS"
        return s, True
    if not s.endswith('-USD'):
        s = f"{s}-USD"
    return s, False


class DataFetcher:
    """Fetches cryptocurrency & Indian stock market data via Yahoo Finance (yfinance) with INR conversion.
    Implements the MarketDataSource shape above."""
    
    def __init__(self):
        self.cache_duration = 60  # 1 minute cache for more real-time data
        self.usd_to_inr_rate = None
    
    @ttl_cache(ttl=300)
    def get_usd_to_inr_rate(_self) -> float:
        """Get current USD to INR exchange rate"""
        try:
            # Using Yahoo Finance for USD/INR rate
            ticker = yf.Ticker("USDINR=X")
            data = ticker.history(period="1d", interval="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            else:
                # Fallback rate if API fails
                return 83.0  # Approximate rate
        except Exception:
            return 83.0  # Fallback rate
    
    @ttl_cache(ttl=60)
    def _fetch_crypto_klines(_self, symbol: str, interval: str = "1h", limit: int = 500) -> pd.DataFrame:
        """Fetch real-time, low-latency crypto OHLCV directly from Binance public REST API (under 200ms)."""
        clean = symbol.upper().replace('-USD', '').replace('USDT', '')
        binance_symbol = f"{clean}USDT"
        binance_interval_map = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
            '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
        }
        b_interval = binance_interval_map.get(interval, '1h')
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={b_interval}&limit={limit}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TradeSignal/2.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                raw = json.loads(response.read().decode('utf-8'))
            if not raw:
                return pd.DataFrame()
            df = pd.DataFrame(raw, columns=[
                'open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = df[col].astype(float)
            df.index = pd.to_datetime(df['open_time'], unit='ms', utc=True)
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            logger.warning(f"Binance kline fetch failed for {symbol}: {e}")
            return pd.DataFrame()

    @ttl_cache(ttl=60)
    def get_data(_self, symbol: str, period: str = "1mo", interval: str = "1h", timeframe: str = None) -> pd.DataFrame:
        """Fetch cryptocurrency or Indian stock data with low latency."""
        try:
            target_interval = timeframe if timeframe is not None else interval
            yf_symbol, is_inr_native = to_yf_symbol(symbol)

            # 1. High-Speed Crypto-Native Path (Binance API: ~200ms, raw USD price)
            if not is_inr_native:
                df_crypto = _self._fetch_crypto_klines(symbol, interval=target_interval)
                if not df_crypto.empty:
                    df_crypto = validate_ohlcv(df_crypto, strict=False)
                    return df_crypto

            # 2. Equity & Stock Path / Fallback (Yahoo Finance)
            ticker = yf.Ticker(yf_symbol)
            actual_interval = '1m' if target_interval == '3m' else target_interval
            actual_period = '5d' if (target_interval == '3m' and period not in ['1d', '5d', '7d']) else period
            data = ticker.history(period=actual_period, interval=actual_interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()

            if interval == '3m' and not data.empty:
                data = data.resample('3min').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
            
            # Convert timestamp index to UTC
            if hasattr(data.index, 'tz') and data.index.tz is not None:
                data.index = data.index.tz_convert('UTC')
            elif hasattr(data.index, 'tz_localize'):
                data.index = data.index.tz_localize('UTC')

            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return pd.DataFrame()
            
            # Spec-Driven Contract Validation (OHLCV Market Data Invariants)
            data = validate_ohlcv(data, strict=False)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @ttl_cache(ttl=300)
    def get_historical_data(_self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> pd.DataFrame:
        """Fetch historical cryptocurrency or Indian stock data for backtesting with INR conversion"""
        try:
            yf_symbol, is_inr_native = to_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()

            # Convert timestamp index to Indian Standard Time (IST)
            if hasattr(data.index, 'tz') and data.index.tz is not None:
                data.index = data.index.tz_convert('Asia/Kolkata')
            elif hasattr(data.index, 'tz_localize'):
                data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            
            # Convert USD prices to INR for crypto; stocks are already in INR
            if not is_inr_native:
                usd_to_inr = _self.get_usd_to_inr_rate()
                price_columns = ['Open', 'High', 'Low', 'Close']
                for col in price_columns:
                    if col in data.columns:
                        data[col] = data[col] * usd_to_inr
            
            # Spec-Driven Contract Validation (OHLCV Market Data Invariants)
            data = validate_ohlcv(data, strict=False)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @ttl_cache(ttl=30)
    def get_real_time_price(_self, symbol: str) -> dict:
        """Get real-time cryptocurrency or Indian stock price data."""
        try:
            yf_symbol, is_inr_native = to_yf_symbol(symbol)
            display_sym = symbol.replace('-USD', '')

            # 1. Fast Crypto Path (Binance REST ~50ms)
            if not is_inr_native:
                try:
                    clean = symbol.upper().replace('-USD', '').replace('USDT', '')
                    binance_sym = f"{clean}USDT"
                    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_sym}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'TradeSignal/2.0'})
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        bdata = json.loads(resp.read().decode())
                    return {
                        'symbol': display_sym,
                        'price': float(bdata.get('lastPrice', 0.0)),
                        'change': float(bdata.get('priceChange', 0.0)),
                        'change_percent': float(bdata.get('priceChangePercent', 0.0)),
                        'volume': float(bdata.get('volume', 0.0)),
                        'currency': 'USD'
                    }
                except Exception as be:
                    logger.debug(f"Binance ticker fallback for {symbol}: {be}")

            # 2. Equity & Indian Stock Path / Fallback (Yahoo Finance)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            rate = 1.0 if is_inr_native else _self.get_usd_to_inr_rate()
            price_val = info.get('currentPrice', info.get('regularMarketPrice', 0))
            change_val = info.get('regularMarketChange', 0)
            
            return {
                'symbol': display_sym,
                'price': price_val * rate,
                'change': change_val * rate,
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': (info.get('marketCap', 0) * rate) if info.get('marketCap') else 0,
                'currency': 'INR' if is_inr_native else 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return {}
    
    @ttl_cache(ttl=300)
    def validate_symbol(_self, symbol: str) -> bool:
        """Validate if a crypto or stock symbol exists and has data on Yahoo Finance"""
        try:
            yf_symbol, _ = to_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            return 'regularMarketPrice' in info or 'currentPrice' in info

        except Exception as e:
            logger.warning(f"Could not validate {symbol}: {str(e)}")
            return False

    validate_crypto_symbol = validate_symbol

    @ttl_cache(ttl=600)
    def get_asset_fundamentals(_self, symbol: str) -> dict:
        """Fetch fundamental company/crypto research details."""
        try:
            yf_symbol, is_inr_native = to_yf_symbol(symbol)
            clean = symbol.replace('-USD', '')
            
            # 1. Fast Crypto Asset Profile (Zero network blocking)
            if not is_inr_native:
                return {
                    'name': f"{clean} Digital Asset",
                    'summary': f"Decentralized digital asset and liquid crypto protocol for {clean}.",
                    'sector': 'Cryptocurrency & Web3',
                    'industry': 'Digital Store of Value / DeFi',
                    'market_cap': 0,
                    'pe_trailing': None,
                    'pe_forward': None,
                    'high_52w': 0,
                    'low_52w': 0,
                    'dividend_yield': 0,
                    'target_price': None,
                    'recommendation': 'NEUTRAL / ACCUMULATE',
                    'analyst_count': 0,
                }

            # 2. Equity & Stock Path (Yahoo Finance)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info or {}
            rate = 1.0 if is_inr_native else _self.get_usd_to_inr_rate()

            # Extract valuation and profile metrics
            return {
                'name': info.get('longName', info.get('shortName', symbol)),
                'summary': info.get('longBusinessSummary', 'No company description available.'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': (info.get('marketCap', 0) * rate) if info.get('marketCap') else 0,
                'pe_trailing': info.get('trailingPE'),
                'pe_forward': info.get('forwardPE'),
                'high_52w': (info.get('fiftyTwoWeekHigh', 0) * rate) if info.get('fiftyTwoWeekHigh') else 0,
                'low_52w': (info.get('fiftyTwoWeekLow', 0) * rate) if info.get('fiftyTwoWeekLow') else 0,
                'dividend_yield': (info.get('dividendYield', 0) * 100) if info.get('dividendYield') else 0,
                'target_price': (info.get('targetMeanPrice', 0) * rate) if info.get('targetMeanPrice') else None,
                'recommendation': info.get('recommendationKey', 'N/A').replace('_', ' ').upper(),
                'analyst_count': info.get('numberOfAnalystOpinions', 0),
                'beta': info.get('beta'),
                'currency': 'INR',
                'is_stock': is_inr_native,
            }
        except Exception as e:
            return {
                'name': symbol,
                'summary': f'Fundamental details unavailable: {str(e)}',
                'sector': 'N/A',
                'industry': 'N/A',
                'market_cap': 0,
                'pe_trailing': None,
                'high_52w': 0,
                'low_52w': 0,
                'is_stock': False,
            }

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import streamlit as st
import requests


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


class DataFetcher:
    """Fetches cryptocurrency market data via Yahoo Finance (yfinance) with INR conversion.
    Implements the MarketDataSource shape above."""
    
    def __init__(self):
        self.cache_duration = 60  # 1 minute cache for more real-time data
        self.usd_to_inr_rate = None
    
    @st.cache_data(ttl=300)
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
    
    @st.cache_data(ttl=60)
    def get_data(_self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
        """Fetch cryptocurrency data with INR conversion"""
        try:
            # Ensure crypto symbol format for Yahoo Finance
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {missing_columns}")
                return pd.DataFrame()
            
            # Convert USD prices to INR
            usd_to_inr = _self.get_usd_to_inr_rate()
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                data[col] = data[col] * usd_to_inr
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_historical_data(_self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> pd.DataFrame:
        """Fetch historical cryptocurrency data for backtesting with INR conversion"""
        try:
            # Ensure crypto symbol format
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()
            
            # Convert USD prices to INR
            usd_to_inr = _self.get_usd_to_inr_rate()
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                if col in data.columns:
                    data[col] = data[col] * usd_to_inr
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=30)
    def get_real_time_price(_self, symbol: str) -> dict:
        """Get real-time cryptocurrency price data in INR"""
        try:
            # Ensure crypto symbol format
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get USD to INR rate
            usd_to_inr = _self.get_usd_to_inr_rate()
            
            price_usd = info.get('currentPrice', info.get('regularMarketPrice', 0))
            change_usd = info.get('regularMarketChange', 0)
            
            return {
                'symbol': symbol.replace('-USD', ''),
                'price': price_usd * usd_to_inr,
                'change': change_usd * usd_to_inr,
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0) * usd_to_inr if info.get('marketCap') else 0,
                'currency': 'INR'
            }
            
        except Exception as e:
            st.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return {}
    
    @st.cache_data(ttl=300)
    def validate_crypto_symbol(_self, symbol: str) -> bool:
        """Validate if a crypto symbol exists and has data on Yahoo Finance"""
        try:
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return 'regularMarketPrice' in info or 'currentPrice' in info

        except Exception as e:
            # yfinance raises an untyped mix of network/parsing errors here; we still want
            # to fail closed (treat as invalid) but the message must be visible, not swallowed,
            # so a rate-limit or outage doesn't look identical to "this symbol doesn't exist".
            st.warning(f"Could not validate {symbol}: {str(e)}")
            return False

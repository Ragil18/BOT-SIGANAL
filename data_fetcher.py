import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class DataFetcher:
    """Class for fetching market data from various sources"""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
    
    @st.cache_data(ttl=300)
    def get_data(_self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
        """Fetch market data for a given symbol"""
        try:
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
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)
    def get_historical_data(_self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> pd.DataFrame:
        """Fetch historical data for backtesting"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Clean data
            data = data.dropna()
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> dict:
        """Get real-time price data"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0)
            }
            
        except Exception as e:
            st.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return {}
    
    def get_company_info(self, symbol: str) -> dict:
        """Get company information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'description': info.get('longBusinessSummary', 'No description available')[:500] + '...',
                'website': info.get('website', ''),
                'employees': info.get('fullTimeEmployees', 0),
                'city': info.get('city', ''),
                'country': info.get('country', '')
            }
            
        except Exception as e:
            st.error(f"Error fetching company info for {symbol}: {str(e)}")
            return {}
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and has data"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we get valid info back
            return 'regularMarketPrice' in info or 'currentPrice' in info
            
        except:
            return False
    
    def get_market_status(self) -> dict:
        """Get general market status"""
        try:
            # Use SPY as market indicator
            spy = yf.Ticker("SPY")
            info = spy.info
            
            return {
                'market_open': info.get('regularMarketOpen', 0),
                'market_price': info.get('regularMarketPrice', 0),
                'market_change': info.get('regularMarketChange', 0),
                'market_change_percent': info.get('regularMarketChangePercent', 0)
            }
            
        except Exception as e:
            st.error(f"Error fetching market status: {str(e)}")
            return {}
    
    def get_trending_symbols(self) -> list:
        """Get trending symbols (predefined list for reliability)"""
        # Popular symbols that usually have good data
        trending = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
            'META', 'NFLX', 'NVDA', 'AMD', 'BABA',
            'SPY', 'QQQ', 'IWM', 'GLD', 'TLT'
        ]
        
        return trending
    
    def get_crypto_data(self, symbol: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
        """Fetch cryptocurrency data"""
        try:
            # Add -USD suffix for crypto symbols
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
            
            return self.get_data(symbol, period, interval)
            
        except Exception as e:
            st.error(f"Error fetching crypto data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_forex_data(self, base: str, quote: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
        """Fetch forex data"""
        try:
            symbol = f"{base}{quote}=X"
            return self.get_data(symbol, period, interval)
            
        except Exception as e:
            st.error(f"Error fetching forex data for {base}/{quote}: {str(e)}")
            return pd.DataFrame()

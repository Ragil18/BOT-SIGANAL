import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import requests

class DataFetcher:
    """Class for fetching cryptocurrency market data with INR conversion"""
    
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
    
    def get_real_time_price(self, symbol: str) -> dict:
        """Get real-time cryptocurrency price data in INR"""
        try:
            # Ensure crypto symbol format
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get USD to INR rate
            usd_to_inr = self.get_usd_to_inr_rate()
            
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
        """Get popular cryptocurrency symbols for trading"""
        # Popular crypto symbols that usually have good data
        trending = [
            'BTC', 'ETH', 'BNB', 'XRP', 'ADA',
            'SOL', 'DOGE', 'DOT', 'AVAX', 'SHIB',
            'MATIC', 'LTC', 'LINK', 'UNI', 'ATOM'
        ]
        
        return trending
    
    def validate_crypto_symbol(self, symbol: str) -> bool:
        """Validate if a crypto symbol exists and has data"""
        try:
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we get valid info back
            return 'regularMarketPrice' in info or 'currentPrice' in info
            
        except:
            return False
    
    def get_crypto_info(self, symbol: str) -> dict:
        """Get cryptocurrency information"""
        try:
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
                
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', symbol.replace('-USD', '')),
                'symbol': symbol.replace('-USD', ''),
                'description': info.get('longBusinessSummary', 'Cryptocurrency')[:500] + '...',
                'website': info.get('website', ''),
                'market_cap_rank': info.get('marketCapRank', 0)
            }
            
        except Exception as e:
            st.error(f"Error fetching crypto info for {symbol}: {str(e)}")
            return {}

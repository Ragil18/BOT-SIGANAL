# Crypto Trading Signal Bot

## Overview

This is a Streamlit-based cryptocurrency trading signal bot that provides live market analysis, technical indicators, and backtesting capabilities specifically for cryptocurrency trading. The application fetches real-time crypto market data, calculates various technical indicators, generates trading signals, and allows users to backtest strategies on historical data. All prices are displayed in Indian Rupees (INR) for local relevance.

## User Preferences

Preferred communication style: Simple, everyday language.
Currency preference: Indian Rupees (INR) for all price displays.
Market focus: Cryptocurrencies only (Bitcoin, Ethereum, etc.).

## System Architecture

The application follows a modular architecture with separate components for different functionalities:

- **Frontend**: Streamlit web application for user interface
- **Data Layer**: Yahoo Finance API integration for market data
- **Analysis Engine**: Technical indicator calculations and signal generation
- **Backtesting Engine**: Historical strategy performance analysis
- **Session Management**: Streamlit session state for user data persistence

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Central application entry point and UI coordination
- **Technologies**: Streamlit, Plotly for visualizations
- **Features**: Multi-page navigation, real-time dashboards, interactive charts
- **State Management**: Session-based storage for watchlists, signals history, and alerts

### 2. Data Fetcher (data_fetcher.py)
- **Purpose**: Cryptocurrency market data acquisition and INR conversion
- **Data Source**: Yahoo Finance (yfinance library) for crypto symbols
- **Currency Conversion**: Automatic USD to INR conversion using live exchange rates
- **Caching Strategy**: 1-minute TTL caching for near real-time updates
- **Data Types**: Real-time and historical cryptocurrency OHLCV data with INR pricing

### 3. Technical Indicators (technical_indicators.py)
- **Purpose**: Mathematical analysis of price and volume data
- **Indicators Supported**: 
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Moving Averages (SMA, EMA)
  - Stochastic Oscillator
  - Average True Range (ATR)
  - Volume analysis
- **Design**: Modular calculation methods for easy extension

### 4. Signal Generator (signal_generator.py)
- **Purpose**: Trading signal generation using weighted indicator combinations
- **Algorithm**: Multi-factor scoring system with configurable weights
- **Signal Types**: BUY, SELL, HOLD with strength ratings
- **Threshold System**: Configurable sensitivity for signal triggers

### 5. Backtester (backtester.py)
- **Purpose**: Historical strategy performance evaluation
- **Features**: 
  - Portfolio simulation with realistic costs
  - Commission and slippage modeling
  - Comprehensive performance metrics
  - Trade history tracking
- **Risk Management**: Position sizing and capital management

## Data Flow

1. **Data Acquisition**: Market data fetched from Yahoo Finance API
2. **Indicator Calculation**: Raw data processed through technical analysis
3. **Signal Generation**: Indicators combined using weighted scoring
4. **Display/Action**: Signals presented to user or fed to backtester
5. **Backtesting**: Historical performance analysis for strategy validation

## External Dependencies

### Primary Libraries
- **Streamlit**: Web application framework
- **yfinance**: Yahoo Finance API client
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **plotly**: Interactive charting and visualization

### Data Sources
- **Yahoo Finance**: Primary cryptocurrency market data provider
- **USD/INR Exchange**: Live exchange rate for currency conversion
- **Real-time Data**: Intraday cryptocurrency price and volume information in INR
- **Historical Data**: Extended periods for crypto backtesting with INR pricing

## Deployment Strategy

The application is designed for:
- **Platform**: Replit deployment with Streamlit server
- **Architecture**: Single-server application with client-side caching
- **Scalability**: Session-based state management for multiple users
- **Performance**: Cached data fetching to minimize external API calls

### Configuration Options
- Customizable technical indicator parameters
- Adjustable signal generation thresholds
- Flexible backtesting periods and initial capital
- User-managed watchlists and alert systems

### Key Design Decisions

1. **Streamlit Choice**: Selected for rapid prototyping and easy deployment, though limited in real-time capabilities
2. **Yahoo Finance API**: Free data source with good coverage, but rate-limited
3. **Modular Architecture**: Separated concerns for maintainability and testing
4. **Weighted Signal System**: Combines multiple indicators to reduce false signals
5. **Session State**: Simple persistence solution suitable for prototype/demo use
6. **Caching Strategy**: Balances data freshness with API rate limits
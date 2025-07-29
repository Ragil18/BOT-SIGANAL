import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
from technical_indicators import TechnicalIndicators
from signal_generator import SignalGenerator
from data_fetcher import DataFetcher
from backtester import Backtester

# Page configuration
st.set_page_config(
    page_title="Trading Signal Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
if 'signals_history' not in st.session_state:
    st.session_state.signals_history = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Initialize components
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()
signal_generator = SignalGenerator()
backtester = Backtester()

def main():
    st.title("📈 Trading Signal Bot")
    st.markdown("---")
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("Settings")
        
        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["Live Signals", "Backtesting", "Watchlist", "Signal History"]
        )
        
        # Symbol selection
        symbol = st.text_input("Symbol", value="AAPL", help="Enter stock symbol (e.g., AAPL, GOOGL)")
        
        # Timeframe selection
        timeframe = st.selectbox(
            "Timeframe",
            ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            index=4  # Default to 1h
        )
        
        # Period selection
        period_map = {
            "1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo",
            "1h": "1mo", "4h": "3mo", "1d": "1y"
        }
        period = period_map.get(timeframe, "1mo")
        
        st.markdown("---")
        
        # Indicator settings
        st.subheader("Indicator Settings")
        rsi_period = st.slider("RSI Period", 5, 50, 14)
        macd_fast = st.slider("MACD Fast", 5, 20, 12)
        macd_slow = st.slider("MACD Slow", 20, 50, 26)
        macd_signal = st.slider("MACD Signal", 5, 15, 9)
        bb_period = st.slider("Bollinger Bands Period", 10, 30, 20)
        bb_std = st.slider("Bollinger Bands Std", 1.0, 3.0, 2.0, 0.1)
        
        # Signal threshold
        signal_threshold = st.slider("Signal Strength Threshold", 0.0, 1.0, 0.6, 0.1)
    
    # Main content based on selected page
    if page == "Live Signals":
        show_live_signals(symbol, timeframe, period, {
            'rsi_period': rsi_period,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'bb_period': bb_period,
            'bb_std': bb_std
        }, signal_threshold)
    
    elif page == "Backtesting":
        show_backtesting(symbol, timeframe, period, {
            'rsi_period': rsi_period,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'bb_period': bb_period,
            'bb_std': bb_std
        }, signal_threshold)
    
    elif page == "Watchlist":
        show_watchlist()
    
    elif page == "Signal History":
        show_signal_history()

def show_live_signals(symbol, timeframe, period, indicator_params, signal_threshold):
    st.header(f"Live Signals - {symbol}")
    
    try:
        # Fetch data
        with st.spinner("Fetching market data..."):
            data = data_fetcher.get_data(symbol, period, timeframe)
        
        if data.empty:
            st.error(f"No data available for {symbol}")
            return
        
        # Calculate indicators
        with st.spinner("Calculating technical indicators..."):
            indicators = technical_indicators.calculate_all(data, indicator_params)
        
        # Generate signals
        signals = signal_generator.generate_signals(data, indicators, signal_threshold)
        
        # Current price and signal
        current_price = data['Close'].iloc[-1]
        current_signal = signals.iloc[-1] if not signals.empty else None
        
        # Display current status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Current Price",
                value=f"${current_price:.2f}",
                delta=f"{((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100):.2f}%"
            )
        
        with col2:
            if current_signal is not None:
                signal_type = current_signal['signal']
                signal_strength = current_signal['strength']
                
                if signal_type == 'BUY':
                    st.metric(
                        label="Signal",
                        value="🟢 BUY",
                        delta=f"Strength: {signal_strength:.2f}"
                    )
                elif signal_type == 'SELL':
                    st.metric(
                        label="Signal",
                        value="🔴 SELL",
                        delta=f"Strength: {signal_strength:.2f}"
                    )
                else:
                    st.metric(
                        label="Signal",
                        value="⚪ HOLD",
                        delta="No clear signal"
                    )
            else:
                st.metric(label="Signal", value="⚪ HOLD", delta="No data")
        
        with col3:
            if current_signal is not None:
                risk_level = "HIGH" if current_signal['strength'] < 0.4 else "MEDIUM" if current_signal['strength'] < 0.7 else "LOW"
                risk_color = "🔴" if risk_level == "HIGH" else "🟡" if risk_level == "MEDIUM" else "🟢"
                st.metric(
                    label="Risk Level",
                    value=f"{risk_color} {risk_level}",
                    delta=f"Score: {current_signal['strength']:.2f}"
                )
        
        # Chart
        st.subheader("Price Chart with Indicators")
        fig = create_chart(data, indicators, signals)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent signals table
        st.subheader("Recent Signals")
        if not signals.empty:
            recent_signals = signals.tail(10).copy()
            recent_signals['timestamp'] = recent_signals.index
            recent_signals = recent_signals[['timestamp', 'signal', 'strength', 'price', 'reason']]
            st.dataframe(recent_signals, use_container_width=True)
        else:
            st.info("No signals generated yet.")
        
        # Add signal to history if it's new
        if current_signal is not None and current_signal['signal'] in ['BUY', 'SELL']:
            signal_data = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'signal': current_signal['signal'],
                'price': current_price,
                'strength': current_signal['strength'],
                'timeframe': timeframe
            }
            
            # Check if this is a new signal
            if not st.session_state.signals_history or \
               st.session_state.signals_history[-1]['timestamp'].date() != signal_data['timestamp'].date():
                st.session_state.signals_history.append(signal_data)
        
        # Auto-refresh
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Real-time updates (every 30 seconds for demo)
        placeholder = st.empty()
        if st.checkbox("Enable Auto-Refresh (30s)"):
            time.sleep(30)
            st.rerun()
            
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")

def show_backtesting(symbol, timeframe, period, indicator_params, signal_threshold):
    st.header(f"Backtesting - {symbol}")
    
    # Backtesting parameters
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=90),
            max_value=datetime.now()
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    initial_capital = st.number_input("Initial Capital ($)", min_value=1000, value=10000, step=1000)
    
    if st.button("Run Backtest"):
        try:
            with st.spinner("Running backtest..."):
                # Fetch historical data
                data = data_fetcher.get_historical_data(symbol, start_date, end_date, timeframe)
                
                if data.empty:
                    st.error("No historical data available for the selected period")
                    return
                
                # Calculate indicators
                indicators = technical_indicators.calculate_all(data, indicator_params)
                
                # Generate signals
                signals = signal_generator.generate_signals(data, indicators, signal_threshold)
                
                # Run backtest
                results = backtester.run_backtest(data, signals, initial_capital)
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Return",
                        f"{results['total_return']:.2f}%",
                        delta=f"${results['final_value'] - initial_capital:.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Win Rate",
                        f"{results['win_rate']:.1f}%",
                        delta=f"{results['total_trades']} trades"
                    )
                
                with col3:
                    st.metric(
                        "Max Drawdown",
                        f"{results['max_drawdown']:.2f}%"
                    )
                
                with col4:
                    st.metric(
                        "Sharpe Ratio",
                        f"{results['sharpe_ratio']:.2f}"
                    )
                
                # Portfolio value chart
                st.subheader("Portfolio Performance")
                portfolio_fig = go.Figure()
                portfolio_fig.add_trace(go.Scatter(
                    x=results['portfolio_history'].index,
                    y=results['portfolio_history']['portfolio_value'],
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='blue', width=2)
                ))
                
                # Add buy/sell markers
                buy_signals = signals[signals['signal'] == 'BUY']
                sell_signals = signals[signals['signal'] == 'SELL']
                
                if not buy_signals.empty:
                    portfolio_fig.add_trace(go.Scatter(
                        x=buy_signals.index,
                        y=[results['portfolio_history'].loc[idx, 'portfolio_value'] 
                           for idx in buy_signals.index if idx in results['portfolio_history'].index],
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(color='green', size=10, symbol='triangle-up')
                    ))
                
                if not sell_signals.empty:
                    portfolio_fig.add_trace(go.Scatter(
                        x=sell_signals.index,
                        y=[results['portfolio_history'].loc[idx, 'portfolio_value'] 
                           for idx in sell_signals.index if idx in results['portfolio_history'].index],
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(color='red', size=10, symbol='triangle-down')
                    ))
                
                portfolio_fig.update_layout(
                    title="Portfolio Value Over Time",
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value ($)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Trade history
                st.subheader("Trade History")
                if results['trades']:
                    trades_df = pd.DataFrame(results['trades'])
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("No trades executed during the backtest period")
        
        except Exception as e:
            st.error(f"Error running backtest: {str(e)}")

def show_watchlist():
    st.header("Watchlist Management")
    
    # Add new symbol
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("Add Symbol", placeholder="Enter symbol (e.g., AAPL)")
    with col2:
        if st.button("Add"):
            if new_symbol and new_symbol.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_symbol.upper())
                st.success(f"Added {new_symbol.upper()} to watchlist")
                st.rerun()
    
    # Display current watchlist with signals
    st.subheader("Current Watchlist")
    
    if st.session_state.watchlist:
        for i, symbol in enumerate(st.session_state.watchlist):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                try:
                    # Get current data
                    data = data_fetcher.get_data(symbol, "1d", "1h")
                    if not data.empty:
                        current_price = data['Close'].iloc[-1]
                        price_change = ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100)
                        
                        # Quick signal analysis
                        indicators = technical_indicators.calculate_all(data, {
                            'rsi_period': 14, 'macd_fast': 12, 'macd_slow': 26,
                            'macd_signal': 9, 'bb_period': 20, 'bb_std': 2.0
                        })
                        signals = signal_generator.generate_signals(data, indicators, 0.6)
                        current_signal = signals.iloc[-1] if not signals.empty else None
                        
                        with col1:
                            st.write(f"**{symbol}**")
                        
                        with col2:
                            st.write(f"${current_price:.2f}")
                        
                        with col3:
                            color = "red" if price_change < 0 else "green"
                            st.write(f":{color}[{price_change:+.2f}%]")
                        
                        with col4:
                            if current_signal is not None:
                                signal_type = current_signal['signal']
                                if signal_type == 'BUY':
                                    st.write("🟢 BUY")
                                elif signal_type == 'SELL':
                                    st.write("🔴 SELL")
                                else:
                                    st.write("⚪ HOLD")
                            else:
                                st.write("⚪ HOLD")
                        
                        with col5:
                            if st.button("❌", key=f"remove_{i}"):
                                st.session_state.watchlist.remove(symbol)
                                st.rerun()
                    
                    else:
                        with col1:
                            st.write(f"**{symbol}**")
                        with col2:
                            st.write("No data")
                        with col5:
                            if st.button("❌", key=f"remove_{i}"):
                                st.session_state.watchlist.remove(symbol)
                                st.rerun()
                
                except Exception as e:
                    with col1:
                        st.write(f"**{symbol}**")
                    with col2:
                        st.write("Error")
                    with col5:
                        if st.button("❌", key=f"remove_{i}"):
                            st.session_state.watchlist.remove(symbol)
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No symbols in watchlist. Add some symbols to get started!")

def show_signal_history():
    st.header("Signal History")
    
    if st.session_state.signals_history:
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state.signals_history)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol_filter = st.selectbox(
                "Filter by Symbol",
                ["All"] + list(df['symbol'].unique())
            )
        
        with col2:
            signal_filter = st.selectbox(
                "Filter by Signal",
                ["All", "BUY", "SELL"]
            )
        
        with col3:
            days_filter = st.selectbox(
                "Filter by Days",
                ["All", "Last 7 days", "Last 30 days"]
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if symbol_filter != "All":
            filtered_df = filtered_df[filtered_df['symbol'] == symbol_filter]
        
        if signal_filter != "All":
            filtered_df = filtered_df[filtered_df['signal'] == signal_filter]
        
        if days_filter == "Last 7 days":
            cutoff_date = datetime.now() - timedelta(days=7)
            filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff_date]
        elif days_filter == "Last 30 days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff_date]
        
        # Display filtered results
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)
            
            # Export functionality
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No signals match the selected filters.")
        
        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.signals_history = []
            st.success("Signal history cleared!")
            st.rerun()
    
    else:
        st.info("No signal history available. Signals will appear here as they are generated.")

def create_chart(data, indicators, signals):
    """Create an interactive chart with price, indicators, and signals"""
    
    # Create subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Price & Bollinger Bands', 'Volume', 'RSI', 'MACD'),
        row_width=[0.4, 0.1, 0.2, 0.3]
    )
    
    # Price chart with Bollinger Bands
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    if 'bb_upper' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(0,100,80,0.5)', width=1)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(0,100,80,0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.1)'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )
    
    # Moving averages
    if 'sma_20' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['sma_20'],
                mode='lines',
                name='SMA 20',
                line=dict(color='blue', width=1)
            ),
            row=1, col=1
        )
    
    if 'ema_12' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['ema_12'],
                mode='lines',
                name='EMA 12',
                line=dict(color='red', width=1)
            ),
            row=1, col=1
        )
    
    # Buy/Sell signals
    if not signals.empty:
        buy_signals = signals[signals['signal'] == 'BUY']
        sell_signals = signals[signals['signal'] == 'SELL']
        
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['price'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(
                        color='green',
                        size=12,
                        symbol='triangle-up',
                        line=dict(color='darkgreen', width=2)
                    )
                ),
                row=1, col=1
            )
        
        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['price'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(
                        color='red',
                        size=12,
                        symbol='triangle-down',
                        line=dict(color='darkred', width=2)
                    )
                ),
                row=1, col=1
            )
    
    # Volume
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color='rgba(0,150,136,0.6)'
        ),
        row=2, col=1
    )
    
    # RSI
    if 'rsi' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ),
            row=3, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1)
    
    # MACD
    if 'macd' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ),
            row=4, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd_signal'],
                mode='lines',
                name='MACD Signal',
                line=dict(color='red', width=2)
            ),
            row=4, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=indicators['macd_histogram'],
                name='MACD Histogram',
                marker_color='gray',
                opacity=0.6
            ),
            row=4, col=1
        )
    
    # Update layout
    fig.update_layout(
        title="Technical Analysis Chart",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)
    
    return fig

if __name__ == "__main__":
    main()

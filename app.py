import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from technical_indicators import TechnicalIndicators
from signal_generator import SignalGenerator
from data_fetcher import DataFetcher
from backtester import Backtester
from storage import load_state, save_state

# Page configuration
st.set_page_config(
    page_title="Crypto Trading Signal Bot",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)


def _load_persisted_state():
    """Restore watchlist/signal history/alerts from SQLite so they survive a process
    restart, instead of living only in st.session_state (which is wiped on restart)."""
    watchlist = load_state('watchlist', ['BTC', 'ETH', 'BNB', 'XRP', 'ADA'])

    signals_history = []
    for entry in load_state('signals_history', []):
        entry = dict(entry)
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
        signals_history.append(entry)

    alerts = []
    for alert in load_state('alerts', []):
        alert = dict(alert)
        if isinstance(alert.get('created'), str):
            alert['created'] = datetime.fromisoformat(alert['created'])
        alerts.append(alert)

    return watchlist, signals_history, alerts


def _save_persisted_state():
    """Write the current watchlist/signal history/alerts to SQLite. Call this after any
    mutation to those session_state lists."""
    save_state('watchlist', st.session_state.watchlist)
    save_state('signals_history', st.session_state.signals_history)
    save_state('alerts', st.session_state.alerts)


# Initialize session state (seeded from persisted storage on first load)
if 'watchlist' not in st.session_state:
    _watchlist, _signals_history, _alerts = _load_persisted_state()
    st.session_state.watchlist = _watchlist
    st.session_state.signals_history = _signals_history
    st.session_state.alerts = _alerts

# Initialize components
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()
signal_generator = SignalGenerator()
backtester = Backtester()

def display_live_ticker():
    """Display a live price ticker for major cryptocurrencies"""
    ticker_symbols = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']
    
    cols = st.columns(len(ticker_symbols))
    
    for i, symbol in enumerate(ticker_symbols):
        try:
            price_data = data_fetcher.get_real_time_price(symbol)
            if price_data:
                with cols[i]:
                    price = price_data['price']
                    change_pct = price_data['change_percent']
                    color = "🟢" if change_pct >= 0 else "🔴"
                    
                    st.metric(
                        label=f"{color} {symbol}",
                        value=f"₹{price:,.0f}",
                        delta=f"{change_pct:+.2f}%"
                    )
        except:
            with cols[i]:
                st.metric(label=f"⚪ {symbol}", value="Loading...", delta="")

def main():
    st.title("₿ Crypto Trading Signal Bot")
    st.markdown("**Real-time cryptocurrency analysis with signals in Indian Rupees (INR)**")
    
    # Live price ticker
    st.subheader("Live Crypto Prices")
    display_live_ticker()
    st.markdown("---")
    
    # Display current USD/INR rate and real-time status
    usd_to_inr = data_fetcher.get_usd_to_inr_rate()
    st.sidebar.info(f"💱 USD to INR: ₹{usd_to_inr:.2f}")
    st.sidebar.success("🟢 Real-time Data Active | Updates every 1 minute")
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.header("Settings")
        
        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["Live Signals", "Backtesting", "Watchlist", "Signal History", "Smart Alerts", "P&L Calculator"]
        )
        
        # Symbol selection
        symbol = st.text_input("Symbol", value="BTC", help="Enter crypto symbol (e.g., BTC, ETH, ADA)")
        
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

        # Indicator settings — the signal engine below (technical_indicators.py,
        # signal_generator.py) is built and weighted for swing trading, so the
        # defaults here match that rather than a scalping setup.
        st.subheader("Signal Settings")
        st.markdown("**Swing trading (3–10 day holding periods)**")

        rsi_period = st.slider("RSI Period", 5, 30, 14)
        macd_fast = st.slider("MACD Fast", 5, 20, 12)
        macd_slow = st.slider("MACD Slow", 15, 40, 26)
        macd_signal = st.slider("MACD Signal", 3, 15, 9)
        bb_period = st.slider("Bollinger Period", 10, 30, 20)
        bb_std = st.slider("Bollinger Std", 1.0, 3.0, 2.0, 0.1)

        # Signal threshold — matches SignalGenerator's own default (0.3)
        signal_threshold = st.slider("Signal Sensitivity", 0.2, 0.8, 0.3, 0.1)

        # Timeframe recommendation for a multi-day swing hold
        if timeframe in ['1h', '4h']:
            st.success("✅ Good for swing entries/exits")
        elif timeframe == '1d':
            st.success("✅ Good for swing trend confirmation")
        elif timeframe in ['15m', '30m']:
            st.warning("⚠️ Usable, but noisier than needed for a multi-day hold")
        else:
            st.error("❌ Too short for a 3–10 day swing hold — try 1h or higher")
    
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
    
    elif page == "Smart Alerts":
        show_smart_alerts()
    
    elif page == "P&L Calculator":
        show_pnl_calculator()

def _auto_refresh_ticker(interval_seconds: int):
    """Trigger a full app rerun every `interval_seconds`, using st.fragment's own
    scheduler rather than a time.sleep() loop that would block this session's thread
    for the entire countdown."""
    @st.fragment(run_every=interval_seconds)
    def _tick():
        now = datetime.now().timestamp()
        last_tick = st.session_state.get('_last_auto_refresh_tick', 0)
        if last_tick > 0 and (now - last_tick) >= (interval_seconds - 1):
            st.session_state['_last_auto_refresh_tick'] = now
            st.rerun()
        elif last_tick == 0:
            st.session_state['_last_auto_refresh_tick'] = now
    _tick()


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
        
        # Show last update time
        last_update = data.index[-1]
        st.info(f"📊 Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')} | Data refreshes every 1 minute")
        
        # Signal dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Current Price",
                value=f"₹{current_price:,.2f}",
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
        
        with col4:
            # Market volatility from ATR
            if 'atr' in indicators.columns:
                current_atr = indicators['atr'].iloc[-1]
                avg_atr = indicators['atr'].rolling(20).mean().iloc[-1]
                volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
                
                vol_status = "HIGH" if volatility_ratio > 1.5 else "NORMAL" if volatility_ratio > 0.8 else "LOW"
                vol_color = "🟠" if vol_status == "HIGH" else "🟢" if vol_status == "NORMAL" else "🔵"
                
                st.metric(
                    label="Market Volatility",
                    value=f"{vol_color} {vol_status}",
                    delta=f"Ratio: {volatility_ratio:.2f}"
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
                _save_persisted_state()

        # Auto-refresh controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Data"):
                st.rerun()

        with col2:
            auto_refresh = st.checkbox("Enable Auto-Refresh")

        # Auto-refresh functionality — ticks on a timer managed by Streamlit's own
        # fragment scheduler instead of blocking this session's thread with time.sleep().
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                ["30 seconds", "1 minute", "2 minutes", "5 minutes"],
                index=1
            )
            interval_map = {
                "30 seconds": 30,
                "1 minute": 60,
                "2 minutes": 120,
                "5 minutes": 300
            }
            st.caption(f"Auto-refreshing every {refresh_interval} — the page stays responsive between refreshes.")
            _auto_refresh_ticker(interval_map[refresh_interval])

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
    
    initial_capital = st.number_input("Initial Capital (₹)", min_value=50000, value=500000, step=50000)

    st.subheader("Risk Controls")
    col3, col4, col5 = st.columns(3)
    with col3:
        position_size_pct = st.slider("Position Size (% of cash per trade)", 10, 100, 95) / 100
    with col4:
        use_stop_loss = st.checkbox("Enable stop-loss", value=True)
        stop_loss_pct = (st.slider("Stop-loss (%)", 1, 20, 5, disabled=not use_stop_loss) / 100) if use_stop_loss else None
    with col5:
        use_take_profit = st.checkbox("Enable take-profit", value=True)
        take_profit_pct = (st.slider("Take-profit (%)", 2, 40, 10, disabled=not use_take_profit) / 100) if use_take_profit else None

    st.subheader("Validation")
    col6, col7 = st.columns(2)
    with col6:
        run_risk_analysis = st.checkbox(
            "Run risk analysis (VaR, Expected Shortfall, Monte Carlo)", value=False,
            help="Re-runs the backtest 200 times with randomized price noise — slower."
        )
    with col7:
        run_consistency_check = st.checkbox(
            "Run consistency check across sub-periods", value=False,
            help="Splits the date range into 4 sequential folds and backtests each independently, "
                 "to check the result isn't specific to this one date range."
        )

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
                results = backtester.run_backtest(
                    data, signals, initial_capital,
                    position_size_pct=position_size_pct,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct
                )

                # Display results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Return",
                        f"{results['total_return']:.2f}%",
                        delta=f"₹{results['final_value'] - initial_capital:,.2f}"
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
                    yaxis_title="Portfolio Value (₹)",
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

                # Risk analysis: VaR / Expected Shortfall / Monte Carlo
                if run_risk_analysis:
                    st.subheader("Risk Analysis")
                    if not results['portfolio_history'].empty:
                        returns = results['portfolio_history']['portfolio_value'].pct_change().dropna()
                        var_95 = backtester.calculate_var(returns, 0.05)
                        es_95 = backtester.calculate_expected_shortfall(returns, 0.05)

                        with st.spinner("Running Monte Carlo simulation (200 re-draws)..."):
                            mc = backtester.monte_carlo_simulation(data, signals, initial_capital, num_simulations=200)

                        rcol1, rcol2, rcol3 = st.columns(3)
                        with rcol1:
                            st.metric("Value at Risk (95%)", f"{var_95 * 100:.2f}%",
                                      help="Worst expected per-bar loss at 95% confidence")
                        with rcol2:
                            st.metric("Expected Shortfall (95%)", f"{es_95 * 100:.2f}%",
                                      help="Average loss in the worst 5% of bars")
                        with rcol3:
                            st.metric("Monte Carlo: P(profit)", f"{mc['probability_positive']:.1f}%")

                        st.caption(
                            f"Monte Carlo range (200 re-draws, ±2% price noise): "
                            f"{mc['percentile_5']:.1f}% to {mc['percentile_95']:.1f}% return, "
                            f"mean {mc['mean_return']:.1f}%"
                        )
                    else:
                        st.info("No portfolio history to analyze — the backtest made no trades.")

                # Consistency check across sequential sub-periods
                if run_consistency_check:
                    st.subheader("Consistency Across Sub-Periods")
                    wf = backtester.walk_forward_validation(
                        data, signals, initial_capital, num_folds=4,
                        position_size_pct=position_size_pct,
                        stop_loss_pct=stop_loss_pct,
                        take_profit_pct=take_profit_pct
                    )
                    if wf['folds']:
                        wf_df = pd.DataFrame(wf['folds'])
                        st.dataframe(wf_df, use_container_width=True)
                        if wf['consistent']:
                            st.success(
                                f"Profitable in {wf['positive_folds']}/{len(wf['folds'])} sub-periods — "
                                f"mean {wf['mean_return']:.2f}%, std {wf['std_return']:.2f}%"
                            )
                        else:
                            st.warning(
                                f"Only profitable in {wf['positive_folds']}/{len(wf['folds'])} sub-periods — "
                                "this result may be specific to the exact date range chosen above, "
                                "not a durable edge."
                            )
                    else:
                        st.info("Not enough data in this date range to split into 4 sub-periods.")

        except Exception as e:
            st.error(f"Error running backtest: {str(e)}")

def show_watchlist():
    st.header("Watchlist Management")
    
    # Add new symbol
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("Add Crypto Symbol", placeholder="Enter crypto symbol (e.g., BTC, ETH, ADA)")
    with col2:
        if st.button("Add"):
            candidate = new_symbol.upper() if new_symbol else ""
            if not candidate:
                st.warning("Enter a symbol first")
            elif candidate in st.session_state.watchlist:
                st.warning(f"{candidate} is already on your watchlist")
            elif not data_fetcher.validate_crypto_symbol(candidate):
                st.error(f"'{candidate}' doesn't look like a valid crypto symbol on Yahoo Finance")
            else:
                st.session_state.watchlist.append(candidate)
                _save_persisted_state()
                st.success(f"Added {candidate} to watchlist")
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
                            st.write(f"₹{current_price:,.2f}")
                        
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
                                _save_persisted_state()
                                st.rerun()
                    
                    else:
                        with col1:
                            st.write(f"**{symbol}**")
                        with col2:
                            st.write("No data")
                        with col5:
                            if st.button("❌", key=f"remove_{i}"):
                                st.session_state.watchlist.remove(symbol)
                                _save_persisted_state()
                                st.rerun()
                
                except Exception as e:
                    with col1:
                        st.write(f"**{symbol}**")
                    with col2:
                        st.write("Error")
                    with col5:
                        if st.button("❌", key=f"remove_{i}"):
                            st.session_state.watchlist.remove(symbol)
                            _save_persisted_state()
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
            _save_persisted_state()
            st.success("Signal history cleared!")
            st.rerun()
    
    else:
        st.info("No signal history available. Signals will appear here as they are generated.")

def create_chart(data, indicators, signals):
    """Create an interactive chart with price, indicators, and signals"""
    
    # Create subplots for the swing-trading indicator set
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Price & EMAs', 'Volume', 'RSI & Williams %R', 'MACD', 'Stochastic'),
        row_heights=[0.4, 0.1, 0.2, 0.2, 0.1]
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
    
    # Swing EMAs — must match the columns TechnicalIndicators.calculate_all() actually
    # produces (ema_9/ema_21/ema_50); this used to reference ema_5/ema_8/ema_13, which
    # calculate_all() never computes, so these lines never rendered.
    if 'ema_9' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['ema_9'],
                mode='lines',
                name='EMA 9',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )

    if 'ema_21' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['ema_21'],
                mode='lines',
                name='EMA 21',
                line=dict(color='red', width=2)
            ),
            row=1, col=1
        )

    if 'ema_50' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['ema_50'],
                mode='lines',
                name='EMA 50',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
    
    # VWAP
    if 'vwap' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['vwap'],
                mode='lines',
                name='VWAP',
                line=dict(color='purple', width=2, dash='dash')
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
    
    # RSI and Williams %R
    if 'rsi_fast' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['rsi_fast'],
                mode='lines',
                name='Fast RSI',
                line=dict(color='purple', width=2)
            ),
            row=3, col=1
        )
        
    if 'williams_r' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['williams_r'],
                mode='lines',
                name='Williams %R',
                line=dict(color='orange', width=2),
                yaxis='y2'
            ),
            row=3, col=1
        )
        
        # Reference lines for Williams %R
        fig.add_hline(y=-20, line_dash="dash", line_color="red", row=3, col=1, opacity=0.5)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", row=3, col=1, opacity=0.5)
        
    # RSI reference levels
    fig.add_hline(y=75, line_dash="dash", line_color="red", row=3, col=1, opacity=0.7)
    fig.add_hline(y=25, line_dash="dash", line_color="green", row=3, col=1, opacity=0.7)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1, opacity=0.5)
    
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
    
    # Stochastic Oscillator — calculate_stochastic() names these 'stoch_k'/'stoch_d',
    # not 'stochastic_k'/'stochastic_d', so this subplot used to never render.
    if 'stoch_k' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['stoch_k'],
                mode='lines',
                name='%K',
                line=dict(color='blue', width=2)
            ),
            row=5, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['stoch_d'],
                mode='lines',
                name='%D',
                line=dict(color='red', width=2)
            ),
            row=5, col=1
        )
        
        # Stochastic reference lines
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=5, col=1, opacity=0.7)
        fig.add_hline(y=20, line_dash="dash", line_color="green", row=5, col=1, opacity=0.7)
    
    # Update layout with better time formatting
    fig.update_layout(
        title=f"Swing Trading Analysis Chart - Last Updated: {data.index[-1].strftime('%H:%M:%S')}",
        xaxis_rangeslider_visible=False,
        height=900,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Format x-axis to show time properly
    fig.update_xaxes(
        tickformat='%H:%M',
        title_text="Time"
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)
    
    return fig

def _check_alert_condition(alert, current_data) -> tuple:
    """Evaluate one alert's trigger condition against freshly fetched data.
    Returns (triggered: bool, detail_message: str)."""
    current_price = current_data['Close'].iloc[-1]

    if alert['type'] == "Price Target":
        target = alert.get('target_price', 0)
        if alert['condition'] == "Above" and current_price > target:
            return True, f"Price ₹{current_price:,.2f} is above target ₹{target:,.2f}"
        if alert['condition'] == "Below" and current_price < target:
            return True, f"Price ₹{current_price:,.2f} is below target ₹{target:,.2f}"
        return False, f"Price ₹{current_price:,.2f}, target ₹{target:,.2f}"

    if alert['type'] == "RSI Overbought/Oversold":
        rsi = technical_indicators.calculate_rsi(current_data['Close'], 14)
        current_rsi = rsi.iloc[-1]
        level = alert.get('rsi_level', 30)
        if alert['condition'] == "Below (Oversold)" and current_rsi < level:
            return True, f"RSI {current_rsi:.1f} is below {level} (oversold)"
        if alert['condition'] == "Above (Overbought)" and current_rsi > level:
            return True, f"RSI {current_rsi:.1f} is above {level} (overbought)"
        return False, f"RSI {current_rsi:.1f}"

    if alert['type'] == "Volume Spike":
        volume_sma = current_data['Volume'].rolling(20).mean()
        ratio = (current_data['Volume'].iloc[-1] / volume_sma.iloc[-1]) if volume_sma.iloc[-1] else 1.0
        multiplier = alert.get('volume_multiplier', 2.0)
        if ratio > multiplier:
            return True, f"Volume is {ratio:.1f}x the 20-bar average (threshold {multiplier}x)"
        return False, f"Volume is {ratio:.1f}x the 20-bar average"

    if alert['type'] == "Squeeze Breakout":
        squeeze = technical_indicators.calculate_squeeze_momentum(current_data)
        latest_change = squeeze.diff().iloc[-1]
        if abs(latest_change) > 0.5:
            direction = "upward" if latest_change > 0 else "downward"
            return True, f"Squeeze momentum shifted {direction} ({latest_change:.2f})"
        return False, f"Squeeze momentum change: {latest_change:.2f}"

    if alert['type'] == "Trend Change":
        structure = technical_indicators.calculate_market_structure(current_data)
        if len(structure) >= 2 and structure.iloc[-1] != structure.iloc[-2]:
            labels = {1.0: "uptrend", -1.0: "downtrend", 0.0: "sideways"}
            return True, f"Market structure shifted to {labels.get(structure.iloc[-1], 'unknown')}"
        return False, "Market structure unchanged"

    return False, "Unknown alert type"


def show_smart_alerts():
    """Smart alert system for swing trading opportunities"""
    st.header("🔔 Smart Alerts")
    
    # Alert configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create New Alert")
        alert_symbol = st.text_input("Symbol", value="BTC", key="alert_symbol")
        alert_type = st.selectbox("Alert Type", [
            "Price Target", 
            "RSI Overbought/Oversold", 
            "Volume Spike", 
            "Squeeze Breakout",
            "Trend Change"
        ])
        
        target_price = 0.0
        rsi_level = 30
        volume_multiplier = 2.0
        alert_condition = "Above"
        
        if alert_type == "Price Target":
            target_price = st.number_input("Target Price (₹)", min_value=0.0, step=1000.0)
            alert_condition = st.selectbox("Condition", ["Above", "Below"])
        elif alert_type == "RSI Overbought/Oversold":
            rsi_level = st.slider("RSI Level", 10, 90, 30)
            alert_condition = st.selectbox("Condition", ["Below (Oversold)", "Above (Overbought)"])
        elif alert_type == "Volume Spike":
            volume_multiplier = st.slider("Volume Multiplier", 1.5, 5.0, 2.0, 0.1)
        elif alert_type == "Squeeze Breakout":
            st.info("Alert triggers when squeeze momentum changes direction")
        elif alert_type == "Trend Change":
            st.info("Alert triggers when market structure changes")
        
        if st.button("Create Alert"):
            symbol_clean = alert_symbol.upper() if alert_symbol else ""
            if not symbol_clean:
                st.warning("Enter a symbol first")
            elif not data_fetcher.validate_crypto_symbol(symbol_clean):
                st.error(f"'{symbol_clean}' doesn't look like a valid crypto symbol on Yahoo Finance")
            else:
                alert_data = {
                    'id': len(st.session_state.alerts),
                    'symbol': symbol_clean,
                    'type': alert_type,
                    'created': datetime.now(),
                    'active': True
                }

                if alert_type == "Price Target":
                    alert_data['target_price'] = target_price
                    alert_data['condition'] = alert_condition
                elif alert_type == "RSI Overbought/Oversold":
                    alert_data['rsi_level'] = rsi_level
                    alert_data['condition'] = alert_condition
                elif alert_type == "Volume Spike":
                    alert_data['volume_multiplier'] = volume_multiplier

                st.session_state.alerts.append(alert_data)
                _save_persisted_state()
                st.success(f"Alert created for {symbol_clean}!")
    
    with col2:
        st.subheader("Active Alerts")
        if st.session_state.alerts:
            for i, alert in enumerate(st.session_state.alerts):
                if alert['active']:
                    with st.expander(f"{alert['symbol']} - {alert['type']}"):
                        st.write(f"Created: {alert['created'].strftime('%Y-%m-%d %H:%M')}")
                        
                        # Check the alert's actual trigger condition
                        try:
                            current_data = data_fetcher.get_data(alert['symbol'], "5d", "1h")
                            if not current_data.empty:
                                triggered, detail = _check_alert_condition(alert, current_data)
                                st.write(detail)
                                if triggered:
                                    st.error("🚨 ALERT TRIGGERED!")
                            else:
                                st.write("No data available to check this alert")
                        except Exception as e:
                            st.write(f"Unable to check alert condition: {str(e)}")

                        if st.button(f"Delete", key=f"delete_{i}"):
                            st.session_state.alerts[i]['active'] = False
                            _save_persisted_state()
                            st.rerun()
        else:
            st.info("No active alerts. Create one to get started!")
    
    # Alert history
    st.subheader("Alert History")
    if st.session_state.alerts:
        alerts_df = pd.DataFrame([alert for alert in st.session_state.alerts])
        st.dataframe(alerts_df, use_container_width=True)

def show_pnl_calculator():
    """Profit & Loss calculator for swing trades"""
    st.header("💰 Trade P&L Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trade Parameters")
        
        # Basic trade info
        entry_price = st.number_input("Entry Price (₹)", min_value=0.0, step=0.01, format="%.2f")
        exit_price = st.number_input("Exit Price (₹)", min_value=0.0, step=0.01, format="%.2f")
        quantity = st.number_input("Quantity", min_value=0.0, step=0.001, format="%.6f")
        
        # Trading costs
        st.subheader("Trading Costs")
        trading_fee = st.slider("Trading Fee (%)", 0.0, 1.0, 0.1, 0.01)
        slippage = st.slider("Slippage (%)", 0.0, 0.5, 0.02, 0.01)
        
        # Trade type
        trade_type = st.selectbox("Trade Type", ["Long", "Short"])
        
    with col2:
        st.subheader("P&L Analysis")
        
        if entry_price > 0 and exit_price > 0 and quantity > 0:
            # Calculate P&L
            if trade_type == "Long":
                gross_pnl = (exit_price - entry_price) * quantity
            else:
                gross_pnl = (entry_price - exit_price) * quantity
            
            # Calculate costs
            entry_cost = entry_price * quantity * (trading_fee / 100)
            exit_cost = exit_price * quantity * (trading_fee / 100)
            slippage_cost = (entry_price + exit_price) * quantity * (slippage / 100)
            total_costs = entry_cost + exit_cost + slippage_cost
            
            # Net P&L
            net_pnl = gross_pnl - total_costs
            
            # Trade value
            trade_value = entry_price * quantity
            pnl_percentage = (net_pnl / trade_value) * 100 if trade_value > 0 else 0
            
            # Display results
            st.metric("Gross P&L", f"₹{gross_pnl:,.2f}")
            st.metric("Total Costs", f"₹{total_costs:,.2f}")
            
            if net_pnl >= 0:
                st.success(f"Net Profit: ₹{net_pnl:,.2f} ({pnl_percentage:+.2f}%)")
            else:
                st.error(f"Net Loss: ₹{net_pnl:,.2f} ({pnl_percentage:+.2f}%)")
            
            # Breakdown
            st.subheader("Cost Breakdown")
            st.write(f"Entry Fee: ₹{entry_cost:.2f}")
            st.write(f"Exit Fee: ₹{exit_cost:.2f}")
            st.write(f"Slippage: ₹{slippage_cost:.2f}")
            
            # Risk metrics
            st.subheader("Risk Metrics")
            if trade_value > 0:
                risk_reward = abs(net_pnl / trade_value) if trade_value > 0 else 0
                st.write(f"Risk/Reward Ratio: {risk_reward:.2f}")
                st.write(f"Trade Size: ₹{trade_value:,.2f}")
                
                # Break-even calculation
                if trade_type == "Long":
                    breakeven_price = entry_price + (total_costs / quantity)
                else:
                    breakeven_price = entry_price - (total_costs / quantity)
                st.write(f"Break-even Price: ₹{breakeven_price:.2f}")
    
    # Batch calculator
    st.markdown("---")
    st.subheader("📊 Multiple Trades Analysis")
    
    if st.button("Analyze Session Trades"):
        if st.session_state.signals_history:
            st.caption(
                "Exit price below is the most recent real close fetched for each symbol since "
                "the signal fired — this marks each still-open position to market now. It is "
                "not a simulated or randomized outcome, and it does not assume any particular "
                "exit rule was followed."
            )
            trades_data = []
            with st.spinner("Fetching follow-up prices..."):
                for signal in st.session_state.signals_history[-10:]:  # Last 10 signals
                    if signal['signal'] not in ['BUY', 'SELL']:
                        continue

                    since = data_fetcher.get_historical_data(
                        signal['symbol'], signal['timestamp'], datetime.now().replace(second=0, microsecond=0),
                        signal.get('timeframe', '1h')
                    )
                    if since.empty:
                        continue

                    latest_price = since['Close'].iloc[-1]
                    quantity = 1000 / signal['price']  # ₹1000 notional per signal, for comparability

                    if signal['signal'] == 'BUY':
                        pnl = (latest_price - signal['price']) * quantity
                    else:
                        pnl = (signal['price'] - latest_price) * quantity

                    trades_data.append({
                        'Symbol': signal['symbol'],
                        'Signal': signal['signal'],
                        'Entry Price': signal['price'],
                        'Latest Price': latest_price,
                        'P&L (mark-to-market)': pnl,
                        'Timestamp': signal['timestamp']
                    })

            if trades_data:
                trades_df = pd.DataFrame(trades_data)
                st.dataframe(trades_df, use_container_width=True)

                total_pnl = trades_df['P&L (mark-to-market)'].sum()
                win_rate = (trades_df['P&L (mark-to-market)'] > 0).mean() * 100

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total P&L (mark-to-market)", f"₹{total_pnl:,.2f}")
                with col2:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col3:
                    st.metric("Avg Trade", f"₹{trades_df['P&L (mark-to-market)'].mean():,.2f}")
            else:
                st.info("No recent BUY/SELL signals with follow-up price data available yet.")
        else:
            st.info("No signal history available for analysis")

if __name__ == "__main__":
    main()

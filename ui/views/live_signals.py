import streamlit as st
from datetime import datetime
from ui.charts import create_chart
from ui.state import save_persisted_state


def _auto_refresh_ticker(interval_seconds: int) -> None:
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


def show_live_signals(data_fetcher, technical_indicators, signal_generator,
                       symbol, timeframe, period, indicator_params, signal_threshold):
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
                save_persisted_state()

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

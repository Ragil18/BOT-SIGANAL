import streamlit as st
import pandas as pd
from datetime import datetime
from ui.state import save_persisted_state


def _check_alert_condition(alert, current_data, technical_indicators) -> tuple:
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


def show_smart_alerts(data_fetcher, technical_indicators):
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
                save_persisted_state()
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
                                triggered, detail = _check_alert_condition(alert, current_data, technical_indicators)
                                st.write(detail)
                                if triggered:
                                    st.error("🚨 ALERT TRIGGERED!")
                            else:
                                st.write("No data available to check this alert")
                        except Exception as e:
                            st.write(f"Unable to check alert condition: {str(e)}")

                        if st.button(f"Delete", key=f"delete_{i}"):
                            st.session_state.alerts[i]['active'] = False
                            save_persisted_state()
                            st.rerun()
        else:
            st.info("No active alerts. Create one to get started!")

    # Alert history
    st.subheader("Alert History")
    if st.session_state.alerts:
        alerts_df = pd.DataFrame([alert for alert in st.session_state.alerts])
        st.dataframe(alerts_df, use_container_width=True)

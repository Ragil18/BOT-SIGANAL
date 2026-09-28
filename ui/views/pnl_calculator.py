import streamlit as st
import pandas as pd
from datetime import datetime


def show_pnl_calculator(data_fetcher):
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

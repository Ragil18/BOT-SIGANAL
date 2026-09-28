import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta


def show_backtesting(data_fetcher, technical_indicators, signal_generator, backtester,
                      symbol, timeframe, period, indicator_params, signal_threshold):
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

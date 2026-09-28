import streamlit as st
from ui.state import save_persisted_state


def show_watchlist(data_fetcher, technical_indicators, signal_generator):
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
                save_persisted_state()
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
                                save_persisted_state()
                                st.rerun()

                    else:
                        with col1:
                            st.write(f"**{symbol}**")
                        with col2:
                            st.write("No data")
                        with col5:
                            if st.button("❌", key=f"remove_{i}"):
                                st.session_state.watchlist.remove(symbol)
                                save_persisted_state()
                                st.rerun()

                except Exception as e:
                    with col1:
                        st.write(f"**{symbol}**")
                    with col2:
                        st.write("Error")
                    with col5:
                        if st.button("❌", key=f"remove_{i}"):
                            st.session_state.watchlist.remove(symbol)
                            save_persisted_state()
                            st.rerun()

                st.markdown("---")
    else:
        st.info("No symbols in watchlist. Add some symbols to get started!")

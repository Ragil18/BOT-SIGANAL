"""Reusable UI chrome shared across pages: the top live-price ticker and the
sidebar (navigation + symbol/timeframe/indicator settings)."""
import streamlit as st

PAGES = ["Live Signals", "Backtesting", "Watchlist", "Signal History", "Smart Alerts", "P&L Calculator"]

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

PERIOD_MAP = {
    "1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo",
    "1h": "1mo", "4h": "3mo", "1d": "1y"
}


def render_live_ticker(data_fetcher) -> None:
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
        except Exception:
            with cols[i]:
                st.metric(label=f"⚪ {symbol}", value="Loading...", delta="")


class SidebarSettings:
    """The bundled result of the sidebar's navigation/symbol/timeframe/indicator widgets."""

    def __init__(self, page: str, symbol: str, timeframe: str, period: str,
                 indicator_params: dict, signal_threshold: float):
        self.page = page
        self.symbol = symbol
        self.timeframe = timeframe
        self.period = period
        self.indicator_params = indicator_params
        self.signal_threshold = signal_threshold


def render_sidebar() -> SidebarSettings:
    with st.sidebar:
        st.header("Settings")

        # Navigation
        page = st.selectbox("Navigate to:", PAGES)

        # Symbol selection
        symbol = st.text_input("Symbol", value="BTC", help="Enter crypto symbol (e.g., BTC, ETH, ADA)")

        # Timeframe selection
        timeframe = st.selectbox("Timeframe", TIMEFRAMES, index=4)  # Default to 1h

        period = PERIOD_MAP.get(timeframe, "1mo")

        st.markdown("---")

        # Indicator settings — the signal engine (core/technical_indicators.py,
        # core/signal_generator.py) is built and weighted for swing trading, so the
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

    indicator_params = {
        'rsi_period': rsi_period,
        'macd_fast': macd_fast,
        'macd_slow': macd_slow,
        'macd_signal': macd_signal,
        'bb_period': bb_period,
        'bb_std': bb_std
    }

    return SidebarSettings(page, symbol, timeframe, period, indicator_params, signal_threshold)

import streamlit as st
from core.data_fetcher import DataFetcher
from core.technical_indicators import TechnicalIndicators
from core.signal_generator import SignalGenerator
from core.backtester import Backtester
from ui.state import init_session_state
from ui.styles import inject_custom_css
from ui.components import render_live_ticker, render_sidebar
from ui.views.live_signals import show_live_signals
from ui.views.backtesting import show_backtesting
from ui.views.watchlist import show_watchlist
from ui.views.signal_history import show_signal_history
from ui.views.smart_alerts import show_smart_alerts
from ui.views.pnl_calculator import show_pnl_calculator

# Page configuration
st.set_page_config(
    page_title="Crypto Trading Signal Bot",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

# Session state (seeded from SQLite storage on first load — see ui/state.py)
init_session_state()

# Shared service instances, injected into whichever view the sidebar routes to
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()
signal_generator = SignalGenerator()
backtester = Backtester()


def main():
    st.title("₿ Crypto Trading Signal Bot")
    st.markdown("**Real-time cryptocurrency analysis with signals in Indian Rupees (INR)**")

    st.subheader("Live Crypto Prices")
    render_live_ticker(data_fetcher)
    st.markdown("---")

    usd_to_inr = data_fetcher.get_usd_to_inr_rate()
    st.sidebar.info(f"💱 USD to INR: ₹{usd_to_inr:.2f}")
    st.sidebar.success("🟢 Real-time Data Active | Updates every 1 minute")

    settings = render_sidebar()

    if settings.page == "Live Signals":
        show_live_signals(
            data_fetcher, technical_indicators, signal_generator,
            settings.symbol, settings.timeframe, settings.period,
            settings.indicator_params, settings.signal_threshold
        )

    elif settings.page == "Backtesting":
        show_backtesting(
            data_fetcher, technical_indicators, signal_generator, backtester,
            settings.symbol, settings.timeframe, settings.period,
            settings.indicator_params, settings.signal_threshold
        )

    elif settings.page == "Watchlist":
        show_watchlist(data_fetcher, technical_indicators, signal_generator)

    elif settings.page == "Signal History":
        show_signal_history()

    elif settings.page == "Smart Alerts":
        show_smart_alerts(data_fetcher, technical_indicators)

    elif settings.page == "P&L Calculator":
        show_pnl_calculator(data_fetcher)


if __name__ == "__main__":
    main()

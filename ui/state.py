"""Bridges core.storage (SQLite) and st.session_state so watchlist/signal
history/alerts survive a process restart. Every view that mutates one of
those three lists must call save_persisted_state() right after."""
import streamlit as st
from datetime import datetime
from core.storage import load_state, save_state


def _load_persisted_state():
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


def init_session_state() -> None:
    """Seed st.session_state.{watchlist,signals_history,alerts} from persisted
    storage on first load of a session. Idempotent — safe to call every rerun."""
    if 'watchlist' not in st.session_state:
        watchlist, signals_history, alerts = _load_persisted_state()
        st.session_state.watchlist = watchlist
        st.session_state.signals_history = signals_history
        st.session_state.alerts = alerts


def save_persisted_state() -> None:
    """Write the current watchlist/signal history/alerts to SQLite. Call this
    after any mutation to those session_state lists."""
    save_state('watchlist', st.session_state.watchlist)
    save_state('signals_history', st.session_state.signals_history)
    save_state('alerts', st.session_state.alerts)

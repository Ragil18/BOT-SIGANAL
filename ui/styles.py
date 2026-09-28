"""Design tokens and injected CSS for the dark, glassmorphic terminal look.

Approach: `.streamlit/config.toml`'s [theme] block sets the *base* dark
palette — it's the only lever that reaches Streamlit's canvas-rendered
dataframe grid, so it stays the foundation. Everything here layers on top
of that as CSS, restyling the same native widgets (st.metric, st.button,
st.dataframe's outer chrome, st.slider, alerts, expanders) rather than
replacing them with raw HTML — so every existing AppTest assertion
(at.metric, at.dataframe, etc.) still sees the widget type it expects.
"""
import streamlit as st

# Design tokens — single source of truth for the palette, referenced both
# here (as CSS custom properties) and from ui/charts.py for Plotly traces.
COLORS = {
    "bg_primary": "#0B0E14",
    "bg_secondary": "#151924",
    "bg_glass": "rgba(255, 255, 255, 0.04)",
    "bg_glass_hover": "rgba(255, 255, 255, 0.07)",
    "border_glass": "rgba(255, 255, 255, 0.08)",
    "text_primary": "#E6E8EC",
    "text_secondary": "#8B92A5",
    "emerald": "#00E676",       # BUY / profit / positive
    "emerald_glow": "rgba(0, 230, 118, 0.35)",
    "crimson": "#FF3366",       # SELL / loss / negative
    "crimson_glow": "rgba(255, 51, 102, 0.35)",
    "amber": "#FFB300",         # HOLD / warnings / medium risk
    "cyan": "#00F2FE",          # secondary accent
    "grid": "#1E2330",
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');

:root {{
    --bg-primary: {COLORS['bg_primary']};
    --bg-secondary: {COLORS['bg_secondary']};
    --bg-glass: {COLORS['bg_glass']};
    --bg-glass-hover: {COLORS['bg_glass_hover']};
    --border-glass: {COLORS['border_glass']};
    --text-primary: {COLORS['text_primary']};
    --text-secondary: {COLORS['text_secondary']};
    --emerald: {COLORS['emerald']};
    --emerald-glow: {COLORS['emerald_glow']};
    --crimson: {COLORS['crimson']};
    --crimson-glow: {COLORS['crimson_glow']};
    --amber: {COLORS['amber']};
    --cyan: {COLORS['cyan']};
}}

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, sans-serif;
}}

/* ---- App shell ---- */
.stApp {{
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0, 230, 118, 0.06), transparent),
        var(--bg-primary);
}}

[data-testid="stSidebar"] {{
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-glass);
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

h1, h2, h3 {{
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.01em;
}}

hr {{
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-glass) 50%, transparent);
    margin: 1.2rem 0;
}}

/* ---- Metric cards (glass) ---- */
[data-testid="stMetric"] {{
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 14px 16px;
    backdrop-filter: blur(12px);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    border-color: rgba(0, 230, 118, 0.3);
    box-shadow: 0 0 24px -8px var(--emerald-glow);
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-secondary) !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Roboto Mono', monospace;
    font-weight: 600;
    color: var(--text-primary) !important;
}}
[data-testid="stMetricDelta"] svg {{
    display: none;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'Roboto Mono', monospace;
    font-size: 0.82rem;
}}

/* ---- Buttons ---- */
.stButton > button {{
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    color: var(--text-primary);
    border-radius: 8px;
    font-weight: 500;
    letter-spacing: 0.02em;
    transition: all 0.15s ease;
}}
.stButton > button:hover {{
    background: var(--bg-glass-hover);
    border-color: var(--emerald);
    box-shadow: 0 0 16px -4px var(--emerald-glow);
    color: var(--emerald);
}}

/* ---- Inputs ---- */
.stTextInput input, .stNumberInput input, .stDateInput input {{
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 1px var(--cyan) !important;
}}
[data-baseweb="select"] > div {{
    background: var(--bg-glass) !important;
    border-color: var(--border-glass) !important;
    border-radius: 8px !important;
}}

/* ---- Sliders ---- */
[data-testid="stSlider"] [role="slider"] {{
    background-color: var(--emerald) !important;
    box-shadow: 0 0 10px -2px var(--emerald-glow);
}}
.stSlider [data-baseweb="slider"] > div > div {{
    background: var(--emerald) !important;
}}

/* ---- Alerts (st.success/error/warning/info) ---- */
[data-testid="stAlertContentSuccess"], div[data-baseweb="notification"]:has(> [data-testid="stAlertContentSuccess"]) {{
    background: rgba(0, 230, 118, 0.08) !important;
}}
[data-testid="stAlertContentError"] {{
    background: rgba(255, 51, 102, 0.08) !important;
}}
[data-testid="stAlert"] {{
    border-radius: 10px;
    backdrop-filter: blur(8px);
}}

/* ---- Expander / containers ---- */
[data-testid="stExpander"] {{
    background: var(--bg-glass);
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px;
    backdrop-filter: blur(10px);
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: var(--border-glass) !important;
    border-radius: 12px !important;
}}

/* ---- Dataframes (outer chrome; the grid itself follows config.toml's theme) ---- */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--border-glass);
    border-radius: 10px;
    overflow: hidden;
}}

/* ---- Custom badges (see ui/components.py render_signal_badge) ---- */
.signal-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    font-family: 'Roboto Mono', monospace;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    border: 1px solid;
}}
.signal-badge.buy {{
    color: var(--emerald);
    border-color: var(--emerald);
    background: rgba(0, 230, 118, 0.08);
    box-shadow: 0 0 20px -6px var(--emerald-glow);
}}
.signal-badge.sell {{
    color: var(--crimson);
    border-color: var(--crimson);
    background: rgba(255, 51, 102, 0.08);
    box-shadow: 0 0 20px -6px var(--crimson-glow);
}}
.signal-badge.hold {{
    color: var(--text-secondary);
    border-color: var(--border-glass);
    background: var(--bg-glass);
}}
.confidence-track {{
    width: 100%;
    height: 5px;
    border-radius: 999px;
    background: var(--bg-glass);
    margin-top: 8px;
    overflow: hidden;
}}
.confidence-fill {{
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}}
.confidence-fill.buy {{ background: linear-gradient(90deg, var(--emerald), #00ffa3); }}
.confidence-fill.sell {{ background: linear-gradient(90deg, var(--crimson), #ff6b8a); }}
.confidence-fill.hold {{ background: var(--text-secondary); }}
</style>
"""


def inject_custom_css() -> None:
    """Render the dark glassmorphic theme's CSS. Call once, early in app.py."""
    st.markdown(_CSS, unsafe_allow_html=True)

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.styles import COLORS

# Shared trace palette so every chart in the app reads as one system instead
# of plotly's default blue/red/green primaries.
EMERALD = COLORS["emerald"]
CRIMSON = COLORS["crimson"]
AMBER = COLORS["amber"]
CYAN = COLORS["cyan"]
GRID = COLORS["grid"]
TEXT_SECONDARY = COLORS["text_secondary"]
TEXT_PRIMARY = COLORS["text_primary"]


def apply_dark_theme(fig, height: int) -> None:
    """Transparent paper so the page's own background/glass card shows through,
    dark plot area with a subtle grid, and axis/legend text in the design
    system's palette."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY, family="Inter, sans-serif", size=11),
        height=height,
        # Horizontal, wrapped strip below the plot instead of Plotly's default
        # vertical list on the right — with ~19 traces across 5 subplots, a
        # right-side legend ends up as a giant column crowding the chart itself.
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="top",
            y=-0.09,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
        ),
        margin=dict(b=150),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)


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
            name="Price",
            increasing=dict(line=dict(color=EMERALD), fillcolor=EMERALD),
            decreasing=dict(line=dict(color=CRIMSON), fillcolor=CRIMSON),
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
                line=dict(color='rgba(0,242,254,0.35)', width=1)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(0,242,254,0.35)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,242,254,0.06)'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color=AMBER, width=1, dash='dot')
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
                line=dict(color=CYAN, width=1.5)
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
                line=dict(color=AMBER, width=1.5)
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
                line=dict(color='#B388FF', width=1.5)
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
                line=dict(color=TEXT_SECONDARY, width=1.5, dash='dash')
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
                        color=EMERALD,
                        size=12,
                        symbol='triangle-up',
                        line=dict(color=TEXT_PRIMARY, width=1)
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
                        color=CRIMSON,
                        size=12,
                        symbol='triangle-down',
                        line=dict(color=TEXT_PRIMARY, width=1)
                    )
                ),
                row=1, col=1
            )

    # Volume — color-matched to the candle's own direction (green under a green
    # candle, red under a red one) instead of one flat color regardless of move.
    volume_colors = [EMERALD if c >= o else CRIMSON for o, c in zip(data['Open'], data['Close'])]
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=volume_colors,
            marker_opacity=0.55
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
                line=dict(color=CYAN, width=1.5)
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
                line=dict(color=AMBER, width=1.5),
                yaxis='y2'
            ),
            row=3, col=1
        )

        # Reference lines for Williams %R
        fig.add_hline(y=-20, line_dash="dash", line_color=CRIMSON, row=3, col=1, opacity=0.5)
        fig.add_hline(y=-80, line_dash="dash", line_color=EMERALD, row=3, col=1, opacity=0.5)

    # RSI reference levels
    fig.add_hline(y=75, line_dash="dash", line_color=CRIMSON, row=3, col=1, opacity=0.7)
    fig.add_hline(y=25, line_dash="dash", line_color=EMERALD, row=3, col=1, opacity=0.7)
    fig.add_hline(y=50, line_dash="dot", line_color=TEXT_SECONDARY, row=3, col=1, opacity=0.5)

    # MACD
    if 'macd' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd'],
                mode='lines',
                name='MACD',
                line=dict(color=CYAN, width=1.5)
            ),
            row=4, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd_signal'],
                mode='lines',
                name='MACD Signal',
                line=dict(color=AMBER, width=1.5)
            ),
            row=4, col=1
        )

        macd_hist_colors = [EMERALD if v >= 0 else CRIMSON for v in indicators['macd_histogram']]
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=indicators['macd_histogram'],
                name='MACD Histogram',
                marker_color=macd_hist_colors,
                opacity=0.5
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
                line=dict(color=CYAN, width=1.5)
            ),
            row=5, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['stoch_d'],
                mode='lines',
                name='%D',
                line=dict(color=AMBER, width=1.5)
            ),
            row=5, col=1
        )

        # Stochastic reference lines
        fig.add_hline(y=80, line_dash="dash", line_color=CRIMSON, row=5, col=1, opacity=0.7)
        fig.add_hline(y=20, line_dash="dash", line_color=EMERALD, row=5, col=1, opacity=0.7)

    # Title, hover behavior, and the dark theme (transparent paper, grid, fonts)
    fig.update_layout(
        title=f"Swing Trading Analysis Chart - Last Updated: {data.index[-1].strftime('%H:%M:%S')}",
        xaxis_rangeslider_visible=False,
        showlegend=True,
        hovermode='x unified'
    )
    apply_dark_theme(fig, height=900)

    # Format x-axis to show time properly. Only the bottom-most subplot gets the
    # "Time" title — with shared_xaxes, update_xaxes() with no row/col filter
    # applies to every row, which previously stamped "Time" under each of the
    # 5 stacked subplots instead of once at the bottom.
    fig.update_xaxes(tickformat='%H:%M')
    fig.update_xaxes(title_text="Time", row=5, col=1)

    # Update y-axis labels
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig

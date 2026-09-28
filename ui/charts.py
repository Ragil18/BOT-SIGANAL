import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
            name="Price"
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
                line=dict(color='rgba(0,100,80,0.5)', width=1)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(0,100,80,0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.1)'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color='orange', width=1)
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
                line=dict(color='blue', width=2)
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
                line=dict(color='red', width=2)
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
                line=dict(color='green', width=2)
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
                line=dict(color='purple', width=2, dash='dash')
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
                        color='green',
                        size=12,
                        symbol='triangle-up',
                        line=dict(color='darkgreen', width=2)
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
                        color='red',
                        size=12,
                        symbol='triangle-down',
                        line=dict(color='darkred', width=2)
                    )
                ),
                row=1, col=1
            )

    # Volume
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color='rgba(0,150,136,0.6)'
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
                line=dict(color='purple', width=2)
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
                line=dict(color='orange', width=2),
                yaxis='y2'
            ),
            row=3, col=1
        )

        # Reference lines for Williams %R
        fig.add_hline(y=-20, line_dash="dash", line_color="red", row=3, col=1, opacity=0.5)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", row=3, col=1, opacity=0.5)

    # RSI reference levels
    fig.add_hline(y=75, line_dash="dash", line_color="red", row=3, col=1, opacity=0.7)
    fig.add_hline(y=25, line_dash="dash", line_color="green", row=3, col=1, opacity=0.7)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1, opacity=0.5)

    # MACD
    if 'macd' in indicators.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ),
            row=4, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['macd_signal'],
                mode='lines',
                name='MACD Signal',
                line=dict(color='red', width=2)
            ),
            row=4, col=1
        )

        fig.add_trace(
            go.Bar(
                x=data.index,
                y=indicators['macd_histogram'],
                name='MACD Histogram',
                marker_color='gray',
                opacity=0.6
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
                line=dict(color='blue', width=2)
            ),
            row=5, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=indicators['stoch_d'],
                mode='lines',
                name='%D',
                line=dict(color='red', width=2)
            ),
            row=5, col=1
        )

        # Stochastic reference lines
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=5, col=1, opacity=0.7)
        fig.add_hline(y=20, line_dash="dash", line_color="green", row=5, col=1, opacity=0.7)

    # Update layout with better time formatting
    fig.update_layout(
        title=f"Swing Trading Analysis Chart - Last Updated: {data.index[-1].strftime('%H:%M:%S')}",
        xaxis_rangeslider_visible=False,
        height=900,
        showlegend=True,
        hovermode='x unified'
    )

    # Format x-axis to show time properly
    fig.update_xaxes(
        tickformat='%H:%M',
        title_text="Time"
    )

    # Update y-axis labels
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig

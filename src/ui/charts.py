"""
Plotly chart components for visualization.
"""
from typing import List
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.domain.models import SimulationResult


def render_portfolio_growth(results: List[SimulationResult]) -> go.Figure:
    """
    Render portfolio growth comparison chart.

    Args:
        results: List of simulation results to compare

    Returns:
        Plotly Figure with line chart comparing all strategies
    """
    fig = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for i, result in enumerate(results):
        dates = [state.date for state in result.history]
        values = [state.total_value for state in result.history]

        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            name=result.strategy_name,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=(
                f"<b>{result.strategy_name}</b><br>"
                "Date: %{x}<br>"
                "Value: $%{y:,.2f}<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Portfolio Growth Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        template="plotly_white",
    )

    # Add range slider
    fig.update_xaxes(rangeslider_visible=True)

    # Add log/linear toggle buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        args=[{"yaxis.type": "linear"}],
                        label="Linear",
                        method="relayout"
                    ),
                    dict(
                        args=[{"yaxis.type": "log"}],
                        label="Log",
                        method="relayout"
                    ),
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1,
                xanchor="right",
                y=1.15,
                yanchor="top"
            ),
        ]
    )

    return fig


def render_cash_exposure(results: List[SimulationResult]) -> go.Figure:
    """
    Render cash exposure chart, particularly useful for Smart Adjust strategy.

    Args:
        results: List of simulation results

    Returns:
        Plotly Figure showing cash percentage over time
    """
    fig = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for i, result in enumerate(results):
        dates = [state.date for state in result.history]
        cash_pcts = []

        for state in result.history:
            if state.total_value > 0:
                cash_pct = (state.cash_balance / state.total_value) * 100
            else:
                cash_pct = 0
            cash_pcts.append(cash_pct)

        fig.add_trace(go.Scatter(
            x=dates,
            y=cash_pcts,
            mode='lines',
            name=result.strategy_name,
            line=dict(color=colors[i % len(colors)], width=2),
            fill='tozeroy' if result.strategy_name == "DCA + Smart Adjust" else None,
            hovertemplate=(
                f"<b>{result.strategy_name}</b><br>"
                "Date: %{x}<br>"
                "Cash: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Cash Allocation Over Time",
        xaxis_title="Date",
        yaxis_title="Cash Percentage (%)",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        template="plotly_white",
        yaxis=dict(range=[0, 100]),
    )

    return fig


def render_drawdown_chart(results: List[SimulationResult]) -> go.Figure:
    """
    Render drawdown chart for all strategies.

    Args:
        results: List of simulation results

    Returns:
        Plotly Figure showing drawdowns over time
    """
    fig = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    for i, result in enumerate(results):
        dates = [state.date for state in result.history]
        values = [state.total_value for state in result.history]

        # Calculate running drawdown
        peak = values[0]
        drawdowns = []

        for value in values:
            if value > peak:
                peak = value
            if peak > 0:
                dd = (value - peak) / peak * 100
            else:
                dd = 0
            drawdowns.append(dd)

        fig.add_trace(go.Scatter(
            x=dates,
            y=drawdowns,
            mode='lines',
            name=result.strategy_name,
            line=dict(color=colors[i % len(colors)], width=2),
            fill='tozeroy',
            hovertemplate=(
                f"<b>{result.strategy_name}</b><br>"
                "Date: %{x}<br>"
                "Drawdown: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Portfolio Drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        template="plotly_white",
    )

    return fig

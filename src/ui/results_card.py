"""
Results display components for Streamlit.
"""
from typing import List
import streamlit as st
import pandas as pd

from src.domain.models import SimulationResult


def render_results_summary(results: List[SimulationResult]) -> None:
    """
    Render the results summary cards showing key metrics.

    Args:
        results: List of simulation results
    """
    st.subheader("📈 Results Summary")

    # Find best strategy by final balance
    if results:
        best_result = max(results, key=lambda r: r.metrics.get('final_balance', 0))
        best_name = best_result.strategy_name
    else:
        best_name = None

    # Create columns for each strategy
    cols = st.columns(len(results))

    for i, result in enumerate(results):
        with cols[i]:
            is_best = result.strategy_name == best_name

            # Add highlight for best strategy
            if is_best:
                st.success(f"🏆 **{result.strategy_name}**")
            else:
                st.info(f"**{result.strategy_name}**")

            final_balance = result.metrics.get('final_balance', 0)
            irr = result.metrics.get('irr', 0)
            cagr = result.metrics.get('cagr', 0)
            max_dd = result.metrics.get('max_drawdown', 0)

            st.metric(
                label="Final Balance",
                value=f"${final_balance:,.0f}",
            )

            st.metric(
                label="IRR",
                value=f"{irr:.2f}%",
            )

            st.metric(
                label="CAGR",
                value=f"{cagr:.2f}%",
            )

            st.metric(
                label="Max Drawdown",
                value=f"{max_dd:.1f}%",
            )


def render_comparison_table(results: List[SimulationResult]) -> None:
    """
    Render a detailed comparison table of all strategies.

    Args:
        results: List of simulation results
    """
    st.subheader("📊 Detailed Comparison")

    data = []
    for result in results:
        metrics = result.metrics
        data.append({
            "Strategy": result.strategy_name,
            "Final Balance": f"${metrics.get('final_balance', 0):,.0f}",
            "Total Invested": f"${result.total_invested:,.0f}",
            "CAGR (%)": f"{metrics.get('cagr', 0):.2f}",
            "IRR (%)": f"{metrics.get('irr', 0):.2f}",
            "Max Drawdown (%)": f"{metrics.get('max_drawdown', 0):.1f}",
            "Volatility (%)": f"{metrics.get('volatility', 0):.1f}",
            "Sharpe Ratio": f"{metrics.get('sharpe_ratio', 0):.2f}",
        })

    df = pd.DataFrame(data)

    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_strategy_details(result: SimulationResult) -> None:
    """
    Render detailed view for a single strategy.

    Args:
        result: Simulation result to display
    """
    st.subheader(f"📋 {result.strategy_name} Details")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Initial Value", f"${result.history[0].total_value:,.0f}")
        st.metric("Final Value", f"${result.history[-1].total_value:,.0f}")

    with col2:
        st.metric("Total Invested", f"${result.total_invested:,.0f}")
        profit = result.history[-1].total_value - result.total_invested
        st.metric("Total Profit", f"${profit:,.0f}")

    with col3:
        st.metric("Months", len(result.history))
        years = len(result.history) / 12
        st.metric("Years", f"{years:.1f}")

    # Show final portfolio composition
    st.write("**Final Portfolio Composition:**")
    final_state = result.history[-1]
    total = final_state.total_value

    if total > 0:
        for ticker, shares in final_state.shares.items():
            # We'd need prices to show actual values
            st.write(f"- {ticker}: {shares:.4f} shares")

        cash_pct = (final_state.cash_balance / total) * 100
        st.write(f"- Cash: ${final_state.cash_balance:,.2f} ({cash_pct:.1f}%)")

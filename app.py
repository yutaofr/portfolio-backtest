"""
QQQ/QLD/Cash Portfolio Backtester - Main Application Entry Point.

This is the composition root that wires together all modules:
- Data loading
- Strategy registry
- Simulation engine
- UI components
"""
import streamlit as st

from src.data_loader import load_json, load_data
from src.strategies import get_all_strategies
from src.simulation import run_backtest
from src.ui import (
    render_config_card,
    render_results_summary,
    render_comparison_table,
    render_portfolio_growth,
    render_cash_exposure,
)
from src.ui.charts import render_drawdown_chart


def main():
    # Page configuration
    st.set_page_config(
        page_title="QQQ/QLD Portfolio Backtester",
        page_icon="📈",
        layout="wide",
    )

    st.title("📊 QQQ/QLD/Cash Portfolio Backtester")
    st.markdown("""
    Compare four investment strategies using historical QQQ and QLD data.
    Adjust parameters in the sidebar and click **Run Simulation** to see results.
    """)

    # Render configuration sidebar
    config, initial_capital, monthly_contribution = render_config_card()

    # Data file path
    data_path = st.sidebar.text_input(
        "Data File Path",
        value="data/price_history.json",
        help="Path to the JSON file containing price history",
    )

    # Run simulation button
    run_button = st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True)

    if run_button:
        # Load data
        try:
            with st.spinner("Loading price data..."):
                market_data = load_data(load_json, data_path)

            st.sidebar.success(f"✅ Loaded {len(market_data)} months of data")
            st.sidebar.info(f"📅 {market_data.index[0].date()} to {market_data.index[-1].date()}")

        except FileNotFoundError:
            st.error(f"❌ Data file not found: {data_path}")
            st.info("Please ensure the price_history.json file exists in the data/ directory.")
            return
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            return

        # Get all registered strategies
        strategies = get_all_strategies()

        # Run backtests
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (name, strategy_func) in enumerate(strategies.items()):
            status_text.text(f"Running {name}...")
            progress_bar.progress((i + 1) / len(strategies))

            try:
                result = run_backtest(
                    market_df=market_data,
                    strategy_func=strategy_func,
                    strategy_name=name,
                    config=config,
                    initial_capital=initial_capital,
                    monthly_contribution=monthly_contribution,
                )
                results.append(result)
            except Exception as e:
                st.warning(f"⚠️ Error running {name}: {e}")

        progress_bar.empty()
        status_text.empty()

        if not results:
            st.error("No simulations completed successfully.")
            return

        # Display results
        st.divider()

        # Results summary cards
        render_results_summary(results)

        st.divider()

        # Portfolio growth chart
        st.subheader("📈 Portfolio Growth")
        fig_growth = render_portfolio_growth(results)
        st.plotly_chart(fig_growth, use_container_width=True)

        # Cash exposure chart
        st.subheader("💵 Cash Allocation")
        st.markdown("*Visualize how the Smart Adjust strategy accumulates cash during bull markets and deploys it during bear markets.*")
        fig_cash = render_cash_exposure(results)
        st.plotly_chart(fig_cash, use_container_width=True)

        # Drawdown chart
        st.subheader("📉 Drawdown Analysis")
        fig_dd = render_drawdown_chart(results)
        st.plotly_chart(fig_dd, use_container_width=True)

        st.divider()

        # Detailed comparison table
        render_comparison_table(results)

        # Store results in session state for potential further analysis
        st.session_state['results'] = results

    else:
        # Show instructions when no simulation has been run
        st.info("👈 Configure your parameters in the sidebar and click **Run Simulation** to start.")

        st.subheader("📋 Available Strategies")

        st.markdown("""
        | Strategy | Description |
        |----------|-------------|
        | **Lump Sum** | One-time investment at T=0, hold forever. No monthly contributions. |
        | **DCA Monthly** | Monthly contributions by target weight. No rebalancing. |
        | **DCA + Yearly Rebalance** | Monthly DCA with annual rebalancing to target weights in January. |
        | **DCA + Smart Adjust** | Monthly DCA with profit-taking (sell 1/3 of QLD gains) or dip-buying (buy 2% of portfolio in QLD when down) at year-end. |
        """)

        st.subheader("📊 Metrics Explained")

        st.markdown("""
        - **CAGR**: Compound Annual Growth Rate - average annual return over the period
        - **IRR**: Internal Rate of Return - accounts for timing of cash flows
        - **Max Drawdown**: Largest peak-to-trough decline in portfolio value
        - **Sharpe Ratio**: Risk-adjusted return (excess return per unit of volatility)
        - **Volatility**: Annualized standard deviation of monthly returns
        """)


if __name__ == "__main__":
    main()

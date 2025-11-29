"""
Configuration card component for Streamlit sidebar.
"""
from typing import Tuple
import streamlit as st

from src.domain.models import AssetConfig


def render_config_card() -> Tuple[AssetConfig, float, float]:
    """
    Render the configuration input card in the sidebar.

    Returns:
        Tuple of (AssetConfig, initial_capital, monthly_contribution)
    """
    st.sidebar.header("📊 Configuration")

    # Initial Capital
    initial_capital = st.sidebar.number_input(
        "Initial Capital ($)",
        min_value=1000.0,
        max_value=10_000_000.0,
        value=100_000.0,
        step=1000.0,
        help="Starting investment amount",
    )

    # Monthly Contribution
    monthly_contribution = st.sidebar.number_input(
        "Monthly Contribution ($)",
        min_value=0.0,
        max_value=100_000.0,
        value=1000.0,
        step=100.0,
        help="Amount to invest each month (set to 0 for Lump Sum only)",
    )

    st.sidebar.subheader("Asset Allocation")

    # QQQ Weight
    qqq_weight = st.sidebar.slider(
        "QQQ Weight (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        help="Percentage allocation to QQQ (Nasdaq 100 ETF)",
    )

    # QLD Weight
    qld_weight = st.sidebar.slider(
        "QLD Weight (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        help="Percentage allocation to QLD (2x Leveraged Nasdaq 100 ETF)",
    )

    # Cash Weight (calculated)
    cash_weight = 100 - qqq_weight - qld_weight

    if cash_weight < 0:
        st.sidebar.error("⚠️ QQQ + QLD cannot exceed 100%!")
        cash_weight = 0
        # Normalize weights
        total = qqq_weight + qld_weight
        qqq_weight = int(qqq_weight / total * 100)
        qld_weight = 100 - qqq_weight

    st.sidebar.info(f"💵 Cash Weight: {cash_weight}%")

    # Cash Yield
    cash_yield = st.sidebar.number_input(
        "Cash Annual Yield (%)",
        min_value=0.0,
        max_value=20.0,
        value=4.0,
        step=0.5,
        help="Annual yield for money market fund / cash allocation",
    )

    # Validate and create config
    try:
        config = AssetConfig(
            qqq_weight=float(qqq_weight),
            qld_weight=float(qld_weight),
            cash_weight=float(cash_weight),
            cash_yield_annual=float(cash_yield),
        )
    except ValueError as e:
        st.sidebar.error(f"Configuration Error: {e}")
        # Return default config
        config = AssetConfig(
            qqq_weight=40.0,
            qld_weight=40.0,
            cash_weight=20.0,
            cash_yield_annual=4.0,
        )

    return config, initial_capital, monthly_contribution

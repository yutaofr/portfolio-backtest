"""
Core strategy implementations: Lump Sum, DCA, and Yearly Rebalance.
All strategies are pure functions following the Strategy Protocol.
"""
from typing import Dict, Protocol

from src.domain.models import AssetConfig, PortfolioState


class StrategyFunction(Protocol):
    """Protocol defining the strategy function signature."""
    def __call__(
        self,
        current_state: PortfolioState,
        market_prices: Dict[str, float],
        config: AssetConfig,
        monthly_contribution: float,
        is_first_month: bool,
    ) -> PortfolioState:
        ...


def strategy_lump_sum(
    state: PortfolioState,
    prices: Dict[str, float],
    config: AssetConfig,
    monthly_contribution: float,
    is_first_month: bool,
) -> PortfolioState:
    """
    Strategy 1: Lump Sum - One-time investment at T=0, hold forever.

    - Initial capital invested at T=0 according to asset allocation
    - No monthly contributions
    - No rebalancing
    - Cash earns interest automatically (handled by engine)
    """
    # Lump Sum does nothing after initial investment
    # Just update total value based on current prices
    total_value = _calculate_total_value(state.shares, state.cash_balance, prices)
    return state.with_updates(total_value=total_value)


def strategy_dca_monthly(
    state: PortfolioState,
    prices: Dict[str, float],
    config: AssetConfig,
    monthly_contribution: float,
    is_first_month: bool,
) -> PortfolioState:
    """
    Strategy 2: DCA Monthly - Monthly contribution by weight, no rebalancing.

    - Initial capital invested at T=0 according to asset allocation
    - Monthly contributions added according to asset allocation
    - No selling of existing holdings
    - Asset ratios naturally drift with market movements
    """
    if is_first_month or monthly_contribution <= 0:
        total_value = _calculate_total_value(state.shares, state.cash_balance, prices)
        return state.with_updates(total_value=total_value)

    # Calculate new purchases based on allocation
    qqq_amount = monthly_contribution * (config.qqq_weight / 100)
    qld_amount = monthly_contribution * (config.qld_weight / 100)
    cash_amount = monthly_contribution * (config.cash_weight / 100)

    # Buy shares
    new_shares = state.shares.copy()
    new_shares['QQQ'] = state.shares.get('QQQ', 0) + (qqq_amount / prices['QQQ'] if prices['QQQ'] > 0 else 0)
    new_shares['QLD'] = state.shares.get('QLD', 0) + (qld_amount / prices['QLD'] if prices['QLD'] > 0 else 0)

    # Add cash allocation
    new_cash = state.cash_balance + cash_amount

    total_value = _calculate_total_value(new_shares, new_cash, prices)

    return state.with_updates(
        shares=new_shares,
        cash_balance=new_cash,
        total_value=total_value,
    )


def strategy_dca_yearly_rebalance(
    state: PortfolioState,
    prices: Dict[str, float],
    config: AssetConfig,
    monthly_contribution: float,
    is_first_month: bool,
) -> PortfolioState:
    """
    Strategy 3: DCA + Yearly Rebalance.

    - Monthly DCA purchases same as Strategy 2
    - At the start of each year (January), rebalance to target allocation
    - Rebalancing sells overweight assets and buys underweight assets
    """
    # First, do the DCA
    state = strategy_dca_monthly(state, prices, config, monthly_contribution, is_first_month)

    # Check if it's January (rebalance month) and not the first month
    if not is_first_month and state.date.month == 1:
        state = _rebalance_portfolio(state, prices, config)

    return state


def _rebalance_portfolio(
    state: PortfolioState,
    prices: Dict[str, float],
    config: AssetConfig,
) -> PortfolioState:
    """Rebalance portfolio to target weights."""
    total_value = _calculate_total_value(state.shares, state.cash_balance, prices)

    # Calculate target allocations
    target_qqq_value = total_value * (config.qqq_weight / 100)
    target_qld_value = total_value * (config.qld_weight / 100)
    target_cash = total_value * (config.cash_weight / 100)

    # Calculate new share counts
    new_shares = {
        'QQQ': target_qqq_value / prices['QQQ'] if prices['QQQ'] > 0 else 0,
        'QLD': target_qld_value / prices['QLD'] if prices['QLD'] > 0 else 0,
    }

    return state.with_updates(
        shares=new_shares,
        cash_balance=target_cash,
        total_value=total_value,
    )


def _calculate_total_value(
    shares: Dict[str, float],
    cash: float,
    prices: Dict[str, float]
) -> float:
    """Calculate total portfolio value."""
    stock_value = sum(
        shares.get(ticker, 0) * prices.get(ticker, 0)
        for ticker in ['QQQ', 'QLD']
    )
    return stock_value + cash

"""
Backtest simulation engine.
Stateless loop that iterates through time, applies interest, and calls strategy functions.
"""
from datetime import date
from typing import Callable, Dict, List, Tuple
import pandas as pd

from src.domain.models import AssetConfig, PortfolioState, SimulationResult
from src.domain.finance_math import (
    calculate_cagr,
    calculate_max_drawdown,
    calculate_irr,
    calculate_sharpe_ratio,
    calculate_volatility,
    calculate_monthly_returns,
)

# Strategy function type signature
StrategyFunc = Callable[
    [PortfolioState, Dict[str, float], AssetConfig, float, bool],
    PortfolioState
]


def run_backtest(
    market_df: pd.DataFrame,
    strategy_func: StrategyFunc,
    strategy_name: str,
    config: AssetConfig,
    initial_capital: float,
    monthly_contribution: float,
) -> SimulationResult:
    """
    Run a backtest simulation.

    Args:
        market_df: DataFrame with Date index and price columns (QQQ, QLD)
        strategy_func: Strategy function to apply each month
        strategy_name: Name of the strategy for display
        config: Asset allocation configuration
        initial_capital: Starting capital
        monthly_contribution: Monthly contribution amount

    Returns:
        SimulationResult with history and metrics
    """
    history: List[PortfolioState] = []
    cash_flows: List[Tuple[date, float]] = []

    # Initialize state
    first_date = market_df.index[0].date()
    first_prices = {
        'QQQ': float(market_df.iloc[0]['QQQ']),
        'QLD': float(market_df.iloc[0]['QLD']),
    }

    state = _initialize_state(first_date, initial_capital, config, first_prices)
    history.append(state)

    # Record initial investment as negative cash flow
    cash_flows.append((first_date, -initial_capital))

    total_invested = initial_capital

    # Iterate through each month
    for i, (timestamp, row) in enumerate(market_df.iterrows()):
        current_date = timestamp.date()
        prices = {
            'QQQ': float(row['QQQ']),
            'QLD': float(row['QLD']),
        }

        is_first_month = (i == 0)

        # Step 1: Apply cash interest (before any transactions)
        if not is_first_month:
            state = _apply_interest(state, config.cash_yield_annual, current_date)

        # Step 2: Apply strategy
        # For first month, we already initialized, so only apply strategy for subsequent months
        # But strategy might need to run on first month for some logic
        state = strategy_func(state, prices, config, monthly_contribution, is_first_month)

        # Record monthly contribution as cash flow (except first month - already counted in initial)
        if not is_first_month and monthly_contribution > 0:
            # Check if strategy actually used the contribution
            # For Lump Sum strategy, monthly contribution is 0
            if strategy_name != "Lump Sum":
                cash_flows.append((current_date, -monthly_contribution))
                total_invested += monthly_contribution

        # Update total value based on current prices
        total_value = _calculate_total_value(state.shares, state.cash_balance, prices)
        state = state.with_updates(date=current_date, total_value=total_value)

        history.append(state)

    # Final cash flow: ending value as positive
    final_date = history[-1].date
    final_value = history[-1].total_value
    cash_flows.append((final_date, final_value))

    # Calculate metrics
    metrics = _calculate_metrics(history, cash_flows, config.cash_yield_annual, total_invested)

    return SimulationResult(
        strategy_name=strategy_name,
        history=history,
        metrics=metrics,
        total_invested=total_invested,
    )


def _initialize_state(
    init_date: date,
    capital: float,
    config: AssetConfig,
    prices: Dict[str, float]
) -> PortfolioState:
    """Initialize portfolio state based on asset allocation."""
    qqq_allocation = capital * (config.qqq_weight / 100)
    qld_allocation = capital * (config.qld_weight / 100)
    cash_allocation = capital * (config.cash_weight / 100)

    shares = {
        'QQQ': qqq_allocation / prices['QQQ'] if prices['QQQ'] > 0 else 0,
        'QLD': qld_allocation / prices['QLD'] if prices['QLD'] > 0 else 0,
    }

    total_value = _calculate_total_value(shares, cash_allocation, prices)

    return PortfolioState(
        date=init_date,
        shares=shares,
        cash_balance=cash_allocation,
        total_value=total_value,
        strategy_memory={},
    )


def _apply_interest(
    state: PortfolioState,
    annual_yield: float,
    current_date: date
) -> PortfolioState:
    """Apply monthly interest to cash balance."""
    # Monthly rate from annual yield: (1 + annual_yield/100)^(1/12) - 1
    monthly_rate = pow(1 + annual_yield / 100, 1 / 12) - 1
    new_cash = state.cash_balance * (1 + monthly_rate)

    return state.with_updates(cash_balance=new_cash, date=current_date)


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


def _calculate_metrics(
    history: List[PortfolioState],
    cash_flows: List[Tuple[date, float]],
    risk_free_rate: float,
    total_invested: float,
) -> Dict[str, float]:
    """Calculate all performance metrics."""
    if len(history) < 2:
        return {}

    values = [s.total_value for s in history]
    start_value = values[0]
    end_value = values[-1]

    # Time span in years
    start_date = history[0].date
    end_date = history[-1].date
    years = (end_date - start_date).days / 365.25

    # CAGR
    cagr = calculate_cagr(start_value, end_value, years)

    # Max Drawdown
    max_dd = calculate_max_drawdown(values)

    # IRR
    irr = calculate_irr(cash_flows)

    # Volatility and Sharpe
    monthly_returns = calculate_monthly_returns(values)
    volatility = calculate_volatility(monthly_returns)
    sharpe = calculate_sharpe_ratio(cagr, risk_free_rate, volatility)

    return {
        'final_balance': end_value,
        'total_invested': total_invested,
        'cagr': cagr,
        'irr': irr,
        'max_drawdown': max_dd,
        'volatility': volatility,
        'sharpe_ratio': sharpe,
    }

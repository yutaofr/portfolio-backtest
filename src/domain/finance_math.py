"""
Financial mathematics calculations - pure functions only.
Implements CAGR, IRR (Newton-Raphson), Max Drawdown, and Sharpe Ratio.
"""
from typing import List, Tuple
from datetime import date
import math


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate.

    Args:
        start_value: Initial investment value
        end_value: Final investment value
        years: Number of years

    Returns:
        CAGR as a percentage (e.g., 10.5 for 10.5%)
    """
    if start_value <= 0 or years <= 0:
        return 0.0
    if end_value <= 0:
        return -100.0

    cagr = (pow(end_value / start_value, 1 / years) - 1) * 100
    return cagr


def calculate_max_drawdown(history_values: List[float]) -> float:
    """
    Calculate Maximum Drawdown from a series of portfolio values.

    Args:
        history_values: List of portfolio values over time

    Returns:
        Max drawdown as a percentage (e.g., -25.5 for 25.5% drawdown)
    """
    if not history_values or len(history_values) < 2:
        return 0.0

    max_drawdown = 0.0
    peak = history_values[0]

    for value in history_values:
        if value > peak:
            peak = value

        if peak > 0:
            drawdown = (value - peak) / peak * 100
            max_drawdown = min(max_drawdown, drawdown)

    return max_drawdown


def calculate_irr(
    cash_flows: List[Tuple[date, float]],
    max_iterations: int = 100,
    tolerance: float = 1e-7
) -> float:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.

    Cash flows are (date, amount) tuples where:
    - Negative amounts = investments/outflows
    - Positive amounts = returns/inflows

    Args:
        cash_flows: List of (date, amount) tuples
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence threshold

    Returns:
        Annual IRR as a percentage (e.g., 12.5 for 12.5%)

    Raises:
        ValueError: If IRR calculation doesn't converge
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0.0

    # Sort by date
    sorted_flows = sorted(cash_flows, key=lambda x: x[0])
    base_date = sorted_flows[0][0]

    # Convert dates to years from base date
    flows_with_years: List[Tuple[float, float]] = []
    for dt, amount in sorted_flows:
        years = (dt - base_date).days / 365.25
        flows_with_years.append((years, amount))

    def npv(rate: float) -> float:
        """Calculate NPV at given rate."""
        if rate <= -1:
            return float('inf')
        total = 0.0
        for years, amount in flows_with_years:
            total += amount / pow(1 + rate, years)
        return total

    def npv_derivative(rate: float) -> float:
        """Calculate derivative of NPV with respect to rate."""
        if rate <= -1:
            return float('inf')
        total = 0.0
        for years, amount in flows_with_years:
            if years != 0:
                total -= years * amount / pow(1 + rate, years + 1)
        return total

    # Initial guess based on simple return
    total_invested = sum(-amt for _, amt in flows_with_years if amt < 0)
    total_returned = sum(amt for _, amt in flows_with_years if amt > 0)

    if total_invested <= 0:
        return 0.0

    years_span = flows_with_years[-1][0] if flows_with_years else 1
    if years_span <= 0:
        years_span = 1

    # Initial guess
    simple_return = (total_returned / total_invested) - 1
    rate = pow(1 + simple_return, 1 / years_span) - 1 if simple_return > -1 else 0.1

    # Newton-Raphson iteration
    for _ in range(max_iterations):
        npv_val = npv(rate)

        if abs(npv_val) < tolerance:
            return rate * 100  # Convert to percentage

        derivative = npv_derivative(rate)

        if abs(derivative) < 1e-10:
            # Derivative too small, try bisection step
            rate = rate * 0.5 if npv_val > 0 else rate * 1.5
            continue

        new_rate = rate - npv_val / derivative

        # Prevent extreme jumps
        if new_rate < -0.99:
            new_rate = -0.99
        elif new_rate > 10:
            new_rate = 10

        if abs(new_rate - rate) < tolerance:
            return new_rate * 100

        rate = new_rate

    # If didn't converge, return best estimate with warning
    return rate * 100


def calculate_volatility(monthly_returns: List[float]) -> float:
    """
    Calculate annualized volatility from monthly returns.

    Args:
        monthly_returns: List of monthly return percentages

    Returns:
        Annualized volatility as a percentage
    """
    if not monthly_returns or len(monthly_returns) < 2:
        return 0.0

    n = len(monthly_returns)
    mean = sum(monthly_returns) / n
    variance = sum((r - mean) ** 2 for r in monthly_returns) / (n - 1)
    std_dev = math.sqrt(variance)

    # Annualize: multiply by sqrt(12) for monthly data
    return std_dev * math.sqrt(12)


def calculate_sharpe_ratio(
    cagr: float,
    risk_free_rate: float,
    volatility: float
) -> float:
    """
    Calculate Sharpe Ratio.

    Args:
        cagr: Compound Annual Growth Rate (percentage)
        risk_free_rate: Risk-free rate / cash yield (percentage)
        volatility: Annualized volatility (percentage)

    Returns:
        Sharpe Ratio
    """
    if volatility <= 0:
        return 0.0

    return (cagr - risk_free_rate) / volatility


def calculate_monthly_returns(history_values: List[float]) -> List[float]:
    """
    Calculate monthly returns from portfolio value history.

    Args:
        history_values: List of portfolio values

    Returns:
        List of monthly return percentages
    """
    if len(history_values) < 2:
        return []

    returns = []
    for i in range(1, len(history_values)):
        if history_values[i - 1] > 0:
            ret = (history_values[i] / history_values[i - 1] - 1) * 100
            returns.append(ret)

    return returns

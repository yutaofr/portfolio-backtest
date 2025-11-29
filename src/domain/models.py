"""
Domain models for the portfolio backtester.
All classes are immutable (frozen=True) following FP principles.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Any, List


@dataclass(frozen=True)
class AssetConfig:
    """Configuration for asset allocation and simulation parameters."""
    qqq_weight: float  # QQQ allocation percentage (0-100)
    qld_weight: float  # QLD allocation percentage (0-100)
    cash_weight: float  # Cash allocation percentage (0-100)
    cash_yield_annual: float  # Annual yield for cash/MMF (e.g., 4.0 for 4%)

    def __post_init__(self):
        total = self.qqq_weight + self.qld_weight + self.cash_weight
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Asset weights must sum to 100%, got {total}%")


@dataclass(frozen=True)
class PortfolioState:
    """
    Represents the portfolio state at a single point in time.
    Immutable to prevent accidental modification of historical data.
    """
    date: date
    shares: Dict[str, float]  # {'QQQ': 10.5, 'QLD': 20.0}
    cash_balance: float
    total_value: float
    # For strategies that need to remember state across time steps (e.g., Strategy 4)
    strategy_memory: Dict[str, Any] = field(default_factory=dict)

    def with_updates(self, **kwargs) -> 'PortfolioState':
        """Create a new state with updated fields (immutable update pattern)."""
        return PortfolioState(
            date=kwargs.get('date', self.date),
            shares=kwargs.get('shares', self.shares),
            cash_balance=kwargs.get('cash_balance', self.cash_balance),
            total_value=kwargs.get('total_value', self.total_value),
            strategy_memory=kwargs.get('strategy_memory', self.strategy_memory),
        )


@dataclass(frozen=True)
class SimulationResult:
    """Complete result of a backtest simulation."""
    strategy_name: str
    history: List[PortfolioState]
    metrics: Dict[str, float]  # CAGR, IRR, MaxDrawdown, Sharpe, etc.
    total_invested: float  # Total capital invested over the simulation

"""
Strategy registry - central registration of all available strategies.
"""
from typing import Callable, Dict

from src.domain.models import AssetConfig, PortfolioState

# Type alias for strategy functions
StrategyFunc = Callable[
    [PortfolioState, Dict[str, float], AssetConfig, float, bool],
    PortfolioState
]

# Internal registry
_strategies: Dict[str, StrategyFunc] = {}


def register_strategy(name: str, func: StrategyFunc) -> None:
    """Register a strategy function."""
    _strategies[name] = func


def get_all_strategies() -> Dict[str, StrategyFunc]:
    """Get all registered strategies."""
    return _strategies.copy()


def get_strategy(name: str) -> StrategyFunc:
    """Get a specific strategy by name."""
    if name not in _strategies:
        raise KeyError(f"Strategy '{name}' not found. Available: {list(_strategies.keys())}")
    return _strategies[name]


# Auto-register built-in strategies
def _register_builtin_strategies():
    from .core_logic import (
        strategy_lump_sum,
        strategy_dca_monthly,
        strategy_dca_yearly_rebalance,
    )
    from .special_rules import strategy_smart_adjust

    register_strategy("Lump Sum", strategy_lump_sum)
    register_strategy("DCA Monthly", strategy_dca_monthly)
    register_strategy("DCA + Yearly Rebalance", strategy_dca_yearly_rebalance)
    register_strategy("DCA + Smart Adjust", strategy_smart_adjust)


# Register on module import
_register_builtin_strategies()

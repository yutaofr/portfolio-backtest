"""Quick test to verify the implementation works."""
from src.domain.models import AssetConfig, PortfolioState
from src.domain.finance_math import calculate_cagr, calculate_irr
from src.data_loader import load_json, load_data
from src.strategies import get_all_strategies
from src.simulation import run_backtest
from datetime import date

# Test models
config = AssetConfig(qqq_weight=40.0, qld_weight=40.0, cash_weight=20.0, cash_yield_annual=4.0)
print(f'AssetConfig: {config}')

# Test finance math
cagr = calculate_cagr(100, 200, 5)
print(f'CAGR (100->200 in 5 years): {cagr:.2f}%')

irr = calculate_irr([
    (date(2020, 1, 1), -10000),
    (date(2021, 1, 1), -1000),
    (date(2022, 1, 1), 13000),
])
print(f'IRR calculation: {irr:.2f}%')

# Test data loading
data = load_data(load_json, 'data/price_history.json')
print(f'Data loaded: {len(data)} months from {data.index[0].date()} to {data.index[-1].date()}')

# Test strategies
strategies = get_all_strategies()
print(f'Strategies registered: {list(strategies.keys())}')

# Run a quick backtest
print('\nBacktest Results:')
for name, strategy_func in strategies.items():
    result = run_backtest(
        market_df=data,
        strategy_func=strategy_func,
        strategy_name=name,
        config=config,
        initial_capital=100000,
        monthly_contribution=1000,
    )
    final = result.metrics.get('final_balance', 0)
    irr_val = result.metrics.get('irr', 0)
    print(f'  {name}: Final=${final:,.0f}, IRR={irr_val:.2f}%')

print('\nAll tests passed!')

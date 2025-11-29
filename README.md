# QQQ/QLD/Cash Portfolio Backtester

A Python-based backtesting application for comparing leveraged ETF investment strategies using historical QQQ (Nasdaq 100) and QLD (2x Leveraged Nasdaq 100) data.

## Features

- **Four Investment Strategies**: Compare Lump Sum, DCA, Yearly Rebalance, and Smart Adjust strategies
- **Interactive Web UI**: Built with Streamlit for easy parameter adjustment
- **Comprehensive Metrics**: CAGR, IRR, Max Drawdown, Sharpe Ratio, Volatility
- **Visual Analysis**: Portfolio growth charts, cash exposure tracking, drawdown visualization
- **Functional Architecture**: Immutable data models and pure functions for reliable backtesting

## Quick Start

```bash
# Clone and navigate to project
cd protfolio-simulator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Investment Strategies

### Strategy 1: Lump Sum
One-time investment at the start. No monthly contributions or rebalancing. Cash earns interest passively.

### Strategy 2: DCA Monthly
Dollar-cost averaging with monthly contributions allocated by target weights. No selling or rebalancing - asset ratios drift naturally with market movements.

### Strategy 3: DCA + Yearly Rebalance
Monthly DCA with annual rebalancing every January. Forces portfolio back to target allocation by selling overweight assets and buying underweight ones.

### Strategy 4: DCA + Smart Adjust
Monthly DCA with intelligent year-end adjustments based on QLD performance:
- **If QLD profitable**: Sell 1/3 of gains, move proceeds to Cash
- **If QLD loses money**: Use Cash to buy QLD worth 2% of total portfolio

This strategy aims to take profits during bull markets and accumulate positions during bear markets.

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Initial Capital | Starting investment amount | $100,000 |
| Monthly Contribution | Amount added each month | $1,000 |
| QQQ Weight | Target allocation to QQQ | 40% |
| QLD Weight | Target allocation to QLD (2x leverage) | 40% |
| Cash Weight | Target allocation to Cash/MMF | 20% |
| Cash Annual Yield | Interest rate for cash holdings | 4.0% |

## Performance Metrics

- **Final Balance**: Portfolio value at end of simulation
- **Total Invested**: Sum of all capital contributions
- **CAGR**: Compound Annual Growth Rate
- **IRR**: Internal Rate of Return (accounts for cash flow timing)
- **Max Drawdown**: Largest peak-to-trough decline
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return metric

## Project Structure

```
protfolio-simulator/
├── app.py                      # Streamlit application entry point
├── requirements.txt            # Python dependencies
├── data/
│   └── price_history.json      # Historical price data
└── src/
    ├── domain/                 # Core models & math
    │   ├── models.py           # AssetConfig, PortfolioState, SimulationResult
    │   └── finance_math.py     # CAGR, IRR, MaxDrawdown, Sharpe
    ├── data_loader/            # Data access layer
    │   ├── json_source.py      # JSON file parser
    │   └── repository.py       # Data standardization
    ├── strategies/             # Investment strategies
    │   ├── core_logic.py       # Lump Sum, DCA, Yearly Rebalance
    │   ├── special_rules.py    # Smart Adjust strategy
    │   └── registry.py         # Strategy registration
    ├── simulation/
    │   └── engine.py           # Backtest execution engine
    └── ui/                     # Streamlit components
        ├── charts.py           # Plotly visualizations
        ├── config_card.py      # Configuration inputs
        └── results_card.py     # Results display
```

## Architecture

This project follows **functional programming principles**:

- **Immutable Data**: All domain models use `@dataclass(frozen=True)` to prevent accidental state mutation
- **Pure Functions**: Strategies are stateless functions that transform `PortfolioState` objects
- **Dependency Injection**: The main app composes all modules together
- **Adapter Pattern**: Data loaders can be swapped without changing business logic

### Strategy Function Protocol

Every strategy implements this interface:

```python
def strategy_func(
    current_state: PortfolioState,
    market_prices: Dict[str, float],  # {'QQQ': price, 'QLD': price}
    config: AssetConfig,
    monthly_contribution: float,
    is_first_month: bool,
) -> PortfolioState
```

## Data Format

The `price_history.json` file expects this structure:

```json
{
  "qqq": [
    {"date": "2000-03-01", "adjClose": 102.50},
    {"date": "2000-04-01", "adjClose": 97.30}
  ],
  "qld": [
    {"date": "2000-03-01", "adjClose": 50.25},
    {"date": "2000-04-01", "adjClose": 45.80}
  ]
}
```

## Extending the Project

### Adding a New Strategy

1. Create your strategy function in `src/strategies/`:

```python
def strategy_custom(state, prices, config, contribution, is_first_month):
    # Your logic here
    return state.with_updates(shares=new_shares, cash_balance=new_cash)
```

2. Register it in `src/strategies/registry.py`:

```python
register_strategy("My Custom Strategy", strategy_custom)
```

### Adding a New Data Source

1. Create a loader in `src/data_loader/`:

```python
def load_excel(path: str) -> pd.DataFrame:
    # Return DataFrame with Date index and QQQ, QLD columns
    pass
```

2. Use it in `app.py`:

```python
data = load_data(load_excel, "data/prices.xlsx")
```

## Technical Requirements

- Python 3.9+
- pandas >= 2.0.0
- numpy >= 1.24.0
- streamlit >= 1.28.0
- plotly >= 5.18.0

## License

MIT

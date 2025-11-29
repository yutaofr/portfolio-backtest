# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QQQ/QLD/Cash leveraged portfolio backtesting system - a Python-based visualization application for simulating mixed investment strategies using Nasdaq 100 ETF (QQQ), 2x leveraged ETF (QLD), and money market funds (Cash/MMF).

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

## Architecture

This project follows **functional programming (FP)** principles with strict separation of data and logic:

### Core Principles
- **Immutability**: All domain models use `@dataclass(frozen=True)`
- **Pure Functions**: Strategies are state transformers, not classes with side effects
- **Dependency Injection**: `app.py` composes all modules together

### Module Structure

```
src/
├── domain/           # Core models & pure math (no business logic)
│   ├── models.py     # AssetConfig, PortfolioState, SimulationResult
│   └── finance_math.py  # IRR (Newton-Raphson), CAGR, MaxDrawdown, Sharpe
├── data_loader/      # Data access layer (adapter pattern)
│   ├── repository.py # Unified data interface
│   └── json_source.py
├── strategies/       # Strategy functions (not classes!)
│   ├── registry.py   # Strategy registration
│   ├── core_logic.py # Lump Sum, DCA, Yearly Rebalance
│   └── special_rules.py  # Smart Adjust (profit-taking/buying-the-dip)
├── simulation/
│   └── engine.py     # Stateless loop: iterate months, apply interest, call strategy
└── ui/               # Streamlit components
    ├── config_card.py
    ├── results_card.py
    └── charts.py     # Plotly wrappers
```

### Strategy Function Protocol

Every strategy is a pure function with this signature:
```python
def strategy_func(
    current_state: PortfolioState,
    market_data: dict,      # {'QQQ': price, 'QLD': price}
    config: AssetConfig,
    monthly_contribution: float
) -> PortfolioState
```

Use `PortfolioState.strategy_memory` (Dict) for cross-timestep state (e.g., year-start values for Strategy 4).

### Four Investment Strategies
1. **Lump Sum**: One-time investment at T=0, hold forever
2. **DCA Monthly**: Monthly contribution by weight, no rebalancing
3. **DCA + Yearly Rebalance**: DCA with annual rebalancing to target weights
4. **Smart Adjust**: DCA with profit-taking (sell 1/3 QLD gains) or dip-buying (buy 2% of portfolio in QLD when down)

## Key Technical Requirements

- **IRR Calculation**: Must use Newton-Raphson algorithm (not numpy.financial)
- **Cash Simulation**: MMF modeled as `MonthlyRate = (1 + AnnualYield)^(1/12) - 1`
- **Data Alignment**: QQQ/QLD prices must be inner-joined on date
- **No Negative Cash**: System must never allow Cash < 0

## Tech Stack

- Python 3.9+
- Pandas (data manipulation)
- Numpy (vectorized calculations)
- Streamlit (web UI)
- Plotly (interactive charts)

这是一个基于 **函数式编程 (Functional Programming, FP)** 范式、模块化、且高度可扩展的系统架构设计。

此架构的核心原则是：**数据与逻辑分离**。我们将“状态”（投资组合）与“行为”（策略逻辑）解耦，使得添加新数据源或新策略只需编写新的纯函数，而无需修改核心引擎。

---

### 1. 系统目录结构 (Project Structure)

```text
qqq_backtester/
├── data/                       # 存放本地数据文件 (JSON/CSV/Excel)
│   └── price_history.json
├── src/                        # 源代码根目录
│   ├── __init__.py
│   ├── domain/                 # 核心领域模型与纯数学计算
│   │   ├── __init__.py
│   │   ├── models.py           # 数据类 (Dataclasses) 定义状态
│   │   └── finance_math.py     # IRR, CAGR, MaxDrawdown (纯函数)
│   ├── data_loader/            # 数据获取层
│   │   ├── __init__.py
│   │   ├── repository.py       # 统一数据访问接口
│   │   ├── json_source.py      # JSON 解析器
│   │   └── web_source.py       # (预留) 网络爬虫/API
│   ├── strategies/             # 策略逻辑层 (核心业务)
│   │   ├── __init__.py
│   │   ├── registry.py         # 策略注册中心
│   │   ├── core_logic.py       # 通用逻辑 (DCA, Rebalance)
│   │   └── special_rules.py    # 特殊规则 (如策略4的止盈抄底)
│   ├── simulation/             # 回测引擎层
│   │   ├── __init__.py
│   │   └── engine.py           # 状态机循环
│   └── ui/                     # 展现层 (Streamlit Components)
│       ├── __init__.py
│       ├── layouts.py          # 页面布局容器
│       ├── config_card.py      # 配置面板
│       ├── results_card.py     # 结果展示
│       └── charts.py           # Plotly 图表封装
├── app.py                      # 应用程序入口 (Composition Root)
└── requirements.txt
```

---

### 2. 核心模块详解与代码契约

#### 2.1 Domain Layer (`src/domain`)
定义整个系统的通用语言。这里没有业务逻辑，只有数据结构和数学公式。

*   **`models.py`**: 使用 `dataclass(frozen=True)` 确保状态不可变（Immutability），符合 FP 范式。

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Any

@dataclass(frozen=True)
class AssetConfig:
    qqq_weight: float
    qld_weight: float
    cash_weight: float
    cash_yield_annual: float

@dataclass(frozen=True)
class PortfolioState:
    date: date
    shares: Dict[str, float]  # {'QQQ': 10.5, 'QLD': 20.0}
    cash_balance: float
    total_value: float
    # 用于策略4这种需要记忆历史状态的策略 (Metadata)
    strategy_memory: Dict[str, Any] = field(default_factory=dict) 

@dataclass(frozen=True)
class SimulationResult:
    strategy_name: str
    history: list[PortfolioState]
    metrics: Dict[str, float]
```

#### 2.2 Data Loader Layer (`src/data_loader`)
负责将不同来源的数据标准化为 Pandas DataFrame。

*   **设计思路**：使用“适配器模式”。无论源是 JSON、PDF 还是 Web，最终都输出相同的 DataFrame 格式（Index=Date, Columns=[AssetNames]）。

```python
# src/data_loader/repository.py
import pandas as pd
from typing import Callable

# 定义加载器函数的类型签名
DataLoaderFunc = Callable[[str], pd.DataFrame]

def load_data(source_func: DataLoaderFunc, source_path: str) -> pd.DataFrame:
    """高阶函数：注入具体的加载逻辑"""
    df = source_func(source_path)
    # 在此进行统一的数据清洗、对齐、填充NaN等操作
    return _standardize_data(df)
```

**扩展性**：未来只需在 `src/data_loader` 下添加 `excel_source.py`，然后在 `app.py` 中传入该函数即可。

#### 2.3 Strategies Layer (`src/strategies`)
这是最需要扩展性的部分。我们不使用继承（Class Inheritance），而是使用**高阶函数**和**策略模式**。

*   **契约**：每个策略都是一个接受当前状态和市场数据，返回新状态的函数。

```python
# src/strategies/protocols.py
from typing import Protocol
from src.domain.models import PortfolioState, AssetConfig

class StrategyFunction(Protocol):
    def __call__(self, 
                 current_state: PortfolioState, 
                 market_data: dict, # 当日价格 {'QQQ': 100, 'QLD': 50}
                 config: AssetConfig, 
                 monthly_contribution: float) -> PortfolioState:
        ...
```

*   **示例：如何实现策略 4 (Smart Adjust)**
    利用 `PortfolioState.strategy_memory` 传递跨时间步的状态（如年初市值），避免全局变量。

```python
# src/strategies/special_rules.py

def strategy_smart_adjust(state: PortfolioState, market_prices: dict, config: AssetConfig, contribution: float) -> PortfolioState:
    # 1. 提取或初始化 Memory
    memory = state.strategy_memory.copy()
    current_year = state.date.year
    
    # 2. 处理跨年逻辑 (重置追踪器)
    if memory.get('last_year') != current_year:
        memory['start_qld_val'] = state.shares['QLD'] * market_prices['QLD']
        memory['year_inflow'] = 0.0
        memory['last_year'] = current_year

    # 3. 执行定投 (假设定投按初始比例，或者全买 QLD，此处需按需求定义)
    # ... 计算买入股数，更新 cash ...
    memory['year_inflow'] += contribution_to_qld
    
    # 4. 判断是否为年底 (12月) -> 执行核心逻辑
    if state.date.month == 12:
        current_qld_val = new_shares_qld * market_prices['QLD']
        profit = current_qld_val - (memory['start_qld_val'] + memory['year_inflow'])
        
        if profit > 0:
            # 止盈逻辑：生成新的 shares 和 cash
            pass 
        else:
            # 抄底逻辑：生成新的 shares 和 cash
            pass
            
    # 5. 返回新的不可变状态
    return PortfolioState(..., strategy_memory=memory)
```

#### 2.4 Simulation Layer (`src/simulation`)
纯粹的循环引擎。它不关心策略的具体内容，只负责时间推进、利息计算和调用策略函数。

```python
# src/simulation/engine.py

def run_backtest(
    market_df: pd.DataFrame, 
    strategy_func: Callable, 
    config: AssetConfig,
    initial_capital: float,
    monthly_contribution: float
) -> SimulationResult:
    
    history = []
    # 初始化状态
    state = _initialize_state(initial_capital, config, market_df.iloc[0])
    
    for date, prices in market_df.iterrows():
        # 1. 现金生息 (纯函数转换)
        state = _apply_interest(state, config.cash_yield_annual)
        
        # 2. 应用策略 (传入当前状态，获得下一刻状态)
        state = strategy_func(state, prices, config, monthly_contribution)
        
        history.append(state)
        
    metrics = calculate_metrics(history) # 调用 domain.finance_math
    return SimulationResult("Strategy Name", history, metrics)
```

#### 2.5 UI Layer (`src/ui`)
基于 Streamlit，但将组件拆分。

*   `config_card.py`: 返回 `AssetConfig` 对象。
*   `charts.py`: 接收 `List[SimulationResult]`，返回 Plotly Figure 对象。
*   **扩展性**：如果以后要加“回撤热力图”，只需新建 `ui/heatmap.py` 并在主程序调用。

---

### 3. 主程序组装 (`app.py`)

这是唯一的“脏”文件，负责将各个纯函数模块组装在一起。

```python
import streamlit as st
from src.data_loader import json_source, repository
from src.strategies import registry
from src.simulation import engine
from src.ui import layouts, config_card, results_card, charts

def main():
    st.set_page_config(layout="wide", page_title="QQQ/QLD Backtester")
    
    # 1. UI: 渲染配置卡片
    with st.sidebar:
        user_config, initial_cap, monthly_contrib = config_card.render()
        
    # 2. Data: 加载数据 (未来可在此处加个 Try/Catch 或数据源选择器)
    try:
        data = repository.load_data(json_source.load, "data/price_history.json")
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return

    # 3. Simulation: 点击运行
    if st.button("Run Simulation"):
        results = []
        
        # 获取所有已注册的策略函数
        strategies = registry.get_all_strategies()
        
        # 并行或循环运行回测
        for name, strat_func in strategies.items():
            res = engine.run_backtest(
                data, strat_func, user_config, initial_cap, monthly_contrib
            )
            # 覆写结果名称用于展示
            # (在 dataclass 中使用 replace 方法保持不可变性)
            results.append(res)

        # 4. UI: 渲染结果
        layouts.render_scrollable_container(
            results_card.render(results),
            charts.render_portfolio_growth(results),
            charts.render_cash_exposure(results), # 专门针对策略4的可视化
            results_card.render_comparison_table(results)
        )

if __name__ == "__main__":
    main()
```

---

### 4. 应对未来需求的扩展指南

#### 场景 A：需要支持上传 Excel 文件作为数据源
1.  在 `src/data_loader/` 新建 `excel_source.py`。
2.  实现 `load(path) -> DataFrame` 函数。
3.  在 `app.py` 中添加 `st.file_uploader`，并将上传的文件流传给新的 load 函数。

#### 场景 B：增加“RSI 指标动态调整”新策略
1.  在 `src/strategies/` 新建 `technical_strategies.py`。
2.  编写纯函数 `strategy_rsi_dynamic(...)`。
3.  在 `src/strategies/registry.py` 中注册该函数。
4.  无需修改 `engine.py` 或 UI 代码，系统会自动运行并展示新策略。

#### 场景 C：添加“年度回报率柱状图”新卡片
1.  在 `src/ui/charts.py` 中添加 `render_yearly_returns(results)` 函数。
2.  在 `app.py` 的 `layouts.render_scrollable_container` 参数列表中调用它。

### 5. 总结
这个架构利用了 Python 的动态特性和函数式编程的简洁性：
*   **State Monad 风格**：`Engine` 管理时间循环，`Strategy` 只是状态转换器。
*   **依赖注入**：`app.py` 决定使用哪个数据源及哪些策略。
*   **不可变性**：使用 `Frozen Dataclass` 极大减少了回测中常见的“意外修改了历史数据”的 Bug。
*   **模块化 UI**：UI 组件像乐高积木一样在 `app.py` 中组装。

这是一个基于**函数式架构**分解的开发 Todo List。列表按**依赖关系**排序（从底层模型到顶层 UI），确保每个任务完成后都能独立运行单元测试。

你可以直接复制每一个任务的“**Prompt 提示词摘要**”发给 LLM。

---

### Phase 1: 领域建模与核心算法 (Foundation)

#### 📋 Task 1: 定义不可变数据模型 (Domain Models)
*   **目标**: 创建 `src/domain/models.py`。
*   **依赖**: 无。
*   **详细要求**:
    *   使用 Python `dataclasses`。
    *   所有类必须是 `frozen=True` (不可变)。
    *   定义 `AssetConfig` (配置参数), `PortfolioState` (单步状态), `SimulationResult` (回测结果)。
    *   `PortfolioState` 需包含 `strategy_memory` (Dict) 用于处理复杂策略的状态记忆。
*   **LLM 提示词摘要**: "编写 `src/domain/models.py`。使用 frozen dataclasses 定义 AssetConfig, PortfolioState (含 date, shares_dict, cash, total_value, strategy_memory), SimulationResult。确保类型提示(Type Hinting)清晰。"

#### 📋 Task 2: 金融计算纯函数 (Financial Math)
*   **目标**: 创建 `src/domain/finance_math.py`。
*   **依赖**: 无 (纯数学计算)。
*   **详细要求**:
    *   实现 `calculate_cagr(start_val, end_val, years)`。
    *   实现 `calculate_max_drawdown(history_values)`。
    *   实现 `calculate_irr(cash_flows)`。**核心要求**: 手写 Newton-Raphson 算法，不依赖 numpy.financial，需处理不收敛的异常情况。
    *   实现 `calculate_sharpe_ratio`。
*   **LLM 提示词摘要**: "编写 `src/domain/finance_math.py`。实现纯函数：CAGR, MaxDrawdown, SharpeRatio, 和基于 Newton-Raphson 算法的 XIRR/IRR 计算器。包含异常处理和单元测试用例。"

---

### Phase 2: 数据层 (Data Layer)

#### 📋 Task 3: JSON 数据加载与清洗 (Data Loader)
*   **目标**: 创建 `src/data_loader/json_source.py` 和 `repository.py`。
*   **依赖**: Pandas。
*   **详细要求**:
    *   读取指定的 JSON 结构。
    *   转换为 Pandas DataFrame。
    *   **关键逻辑**: Inner Join `qqq` 和 `qld` 的日期，确保数据对齐；将字符串日期转为 datetime 对象；按日期升序排列。
*   **LLM 提示词摘要**: "编写数据加载模块。输入是特定格式的 JSON (QQQ/QLD 历史)，输出是清洗后、日期对齐的 Pandas DataFrame。索引为 Date，列为 ['QQQ', 'QLD']。包含处理缺失值和日期解析的逻辑。"

---

### Phase 3: 仿真引擎 (Simulation Engine)

#### 📋 Task 4: 回测引擎核心循环 (Engine)
*   **目标**: 创建 `src/simulation/engine.py`。
*   **依赖**: Task 1 (Models), Task 2 (Math)。
*   **详细要求**:
    *   实现 `run_backtest` 函数。
    *   **逻辑流程**:
        1. 初始化 `PortfolioState`。
        2. 遍历 DataFrame 的每一行（每一个月）。
        3. **Step A**: 现金生息 (Cash *= 1+rate)。
        4. **Step B**: 调用传入的 `strategy_func` 获取新状态。
        5. 记录历史。
    *   计算最终 Metrics 并返回 `SimulationResult`。
*   **LLM 提示词摘要**: "编写回测引擎 `engine.py`。核心是一个函数，接收 `market_data` DataFrame, `strategy_func` (高阶函数), 和 `config`。在循环中，先计算现金利息，再调用策略函数更新状态。最后利用 `finance_math` 计算指标。"

---

### Phase 4: 策略逻辑 (Strategies)

#### 📋 Task 5: 基础策略实现 (Lump Sum & DCA)
*   **目标**: 创建 `src/strategies/core_logic.py`。
*   **依赖**: Task 1 (Models)。
*   **详细要求**:
    *   定义策略函数的 Protocol 接口。
    *   实现 `strategy_lump_sum`: 仅在 T=0 买入，之后持有。
    *   实现 `strategy_dca_monthly`: 每月按权重买入，不卖出。
*   **LLM 提示词摘要**: "定义策略函数 Protocol。实现两个纯函数策略：1. Lump Sum (T=0建仓后不动), 2. DCA Monthly (每月定投，不卖出，存量不平衡)。确保输入输出符合 `PortfolioState` 的定义。"

#### 📋 Task 6: 再平衡策略实现 (Yearly Rebalance)
*   **目标**: 扩展 `src/strategies/core_logic.py`。
*   **依赖**: Task 5。
*   **详细要求**:
    *   实现 `strategy_year_rebalance`: 每月 DCA，但仅在每年 1 月检查并强制重置资产权重。
*   **LLM 提示词摘要**: "实现 'DCA + Yearly Rebalance' 策略函数。逻辑：每月执行 DCA 买入。如果当前月份是 1 月，计算总资产，强制买卖 QQQ/QLD/Cash 使其回归目标权重。"

#### 📋 Task 7: 智能止盈/抄底策略 (Strategy 4 - Smart Adjust)
*   **目标**: 创建 `src/strategies/special_rules.py`。
*   **依赖**: Task 1 (Models - strategy_memory)。
*   **详细要求**:
    *   这是最复杂的逻辑。
    *   利用 `state.strategy_memory` 记录：`start_year_qld_value` 和 `year_qld_inflows`。
    *   在 12 月触发判断：
        *   若 QLD 盈利：卖出 1/3 利润 -> Cash。
        *   若 QLD 亏损：Cash -> 买入总资产 2% 的 QLD。
*   **LLM 提示词摘要**: "实现 Strategy 4 (Smart Adjust)。利用 `strategy_memory` 跟踪 QLD 的年度成本。在每年 12 月，根据 QLD 的年度盈亏，执行'卖出 1/3 利润转现金'或'用现金抄底 2% 仓位'的逻辑。确保处理跨年时的状态重置。"

---

### Phase 5: UI 组件 (UI Components)

#### 📋 Task 8: Plotly 图表封装 (Charts)
*   **目标**: 创建 `src/ui/charts.py`。
*   **依赖**: Task 1 (Result Model), Plotly。
*   **详细要求**:
    *   实现 `render_portfolio_growth(results)`: 多条折线图对比总资产。
    *   实现 `render_cash_exposure(results)`: 堆叠面积图，专门展示 Strategy 4 的现金仓位变化。
*   **LLM 提示词摘要**: "编写 `src/ui/charts.py`。使用 Plotly Graph Objects。实现两个函数：1. 绘制所有策略的'总资产随时间变化'折线图。2. 绘制特定策略的'现金持仓百分比'堆叠面积图/面积图。"

#### 📋 Task 9: Streamlit 卡片组件 (Cards)
*   **目标**: 创建 `src/ui/config_card.py` 和 `results_card.py`。
*   **依赖**: Streamlit, Task 1。
*   **详细要求**:
    *   `config_card`: 使用 Sliders 和 Inputs 获取参数，返回 `AssetConfig`。需校验权重和为 100%。
    *   `results_card`: 展示 KPI 指标（Final Balance, IRR）和详细对比表格。
*   **LLM 提示词摘要**: "编写 Streamlit UI 组件。`config_card` 负责获取用户输入并组装成 `AssetConfig` 对象（含数据校验）。`results_card` 负责接收 `SimulationResult` 列表，渲染 Metrics 卡片和 Pandas 对比表格。"

---

### Phase 6: 集成 (Integration)

#### 📋 Task 10: 应用程序入口 (Main App)
*   **目标**: 创建 `app.py`。
*   **依赖**: 所有上述模块。
*   **详细要求**:
    *   组装 UI、数据加载、策略注册和回测引擎。
    *   处理 Streamlit 的 Session State（如果需要）。
    *   实现策略注册表 (`strategies.registry`) 的简单映射。
*   **LLM 提示词摘要**: "编写 `app.py` 作为 Streamlit 入口。连接 `data_loader`, `strategies`, `engine`, 和 `ui` 模块。逻辑：加载数据 -> 获取 UI 配置 -> 循环运行 4 个策略 -> 将结果传递给 UI 图表组件进行渲染。包含基本的错误处理。"

---
# 软件需求说明书 (SRS)
## 项目名称：QQQ/QLD/Cash 杠杆投资组合回测系统
**版本**：1.0
**日期**：2025-01-01
---

## 1. 引言 (Introduction)

### 1.1 目的
本项目旨在开发一个基于 Python 的可视化回测应用程序，用于模拟纳斯达克100 ETF (QQQ)、两倍杠杆 ETF (QLD) 以及带息货币市场基金 (Cash/MMF) 的混合投资策略。

### 1.2 范围
系统将利用 2000 年至 2025 年的月度历史数据，通过四种不同的资金管理和再平衡策略，计算并对比投资组合的各项风险收益指标（CAGR, IRR, 最大回撤等）。系统将提供交互式的 Web 界面供用户调整参数并实时查看图表。

---

## 2. 数据层规范 (Data Specifications)

### 2.1 股票数据源
- **输入文件**：`price_history.json`
- **数据结构**：包含 `qqq` 和 `qld` 两个键，值为对象列表 `[{ "date": "YYYY-MM-DD", "adjClose": float }, ...]`。
- **时间跨度**：2000-03-01 至 2025-01-01。
- **预处理**：
  - 必须将字符串日期转换为日期对象。
  - 必须对齐两个序列的日期，确保回测仅在两者均有数据的月份进行。

### 2.2 现金资产 (Cash Asset) 模拟
系统不使用外部数据源作为现金历史价格，而是通过数学模型模拟“货币市场基金”：
- **定义**：Cash 被视为一种名为 "MMF" 的资产，且永不亏损，按月产生复利。
- **参数**：用户输入 `Annual Yield` (年化收益率，例如 4.0%)。
- **计算逻辑**：
  $$ MonthlyRate = (1 + \frac{AnnualYield}{100})^{(1/12)} - 1 $$
  $$ CashBalance_{t} = CashBalance_{t-1} \times (1 + MonthlyRate) $$
  *(注：利息在每月初、交易发生前结算入账)*

---

## 3. 仿真引擎逻辑 (Simulation Engine)

### 3.1 账户模型
回测引擎需在每个时间步（月）维护以下状态：
- **Shares_QQQ**：持有的 QQQ 股数。
- **Shares_QLD**：持有的 QLD 股数。
- **Balance_Cash**：现金账户金额。
- **Total_Value**：$Shares_{QQQ} \times Price_{QQQ} + Shares_{QLD} \times Price_{QLD} + Balance_{Cash}$。

### 3.2 输入参数 (Configuration)
用户通过 UI 配置以下参数：
1.  **初始本金 (Initial Capital)**：起始资金。
2.  **月度定投 (Monthly Contribution)**：每月追加资金。
3.  **资产配比 (Asset Allocation)**：
    - QQQ 权重 (%)
    - QLD 权重 (%)
    - Cash 权重 (%) = 100% - QQQ% - QLD%。
4.  **现金年化收益率 (Cash Yield)**：用于模拟 MMF 回报。

### 3.3 投资策略详细定义

系统需并行运行以下四种策略：

#### 策略 1: Lump Sum (一次性投入)
- **T=0**：将“初始本金”按“资产配比”分配，买入 QQQ、QLD，剩余存入 Cash。
- **T=1 to End**：
  - 不进行月度定投（Monthly Contribution = 0）。
  - 不进行再平衡。
  - Cash 账户每月自动累积利息。

#### 策略 2: DCA Monthly (月度定投 - 无再平衡)
- **T=0**：按“资产配比”投入初始本金。
- **T=Monthly**：
  - 将“月度定投”资金，按“资产配比”买入 QQQ、QLD 和存入 Cash。
  - 不卖出任何存量资产。
  - 存量资产比例会随市场波动而自然漂移。

#### 策略 3: DCA + Yearly Rebalance (定投 + 年度标准再平衡)
- **买入逻辑**：同策略 2。
- **再平衡逻辑**：
  - **触发时间**：每年的第一个交易月（或每12个月）。
  - **操作**：计算当前总资产价值，强制卖出超配资产，买入低配资产，使各类资产（QQQ/QLD/Cash）的市值占比重新等于用户设定的“资产配比”。

#### 策略 4: DCA + Smart Yearly Adjust (定投 + 智能止盈抄底)
此策略不追求维持固定比例，而是基于 QLD 的年度表现进行非对称操作。

- **初始与定投**：
  - 初始资金与月度定投均按用户设定的“资产配比”执行（通常此策略建议用户设定的 Cash 配比很低或为0，依靠止盈来积累 Cash）。
- **调整逻辑**：
  - **触发时间**：每年的最后一个交易月（12月）。
  - **计算指标**：
    - `QLD_Start_Value`：当年年初 QLD 的市值。
    - `QLD_Inflow`：当年累计定投进入 QLD 的金额。
    - `QLD_End_Value`：当年年末 QLD 的市值。
    - **QLD 年度盈亏** = $QLD_{End\_Value} - (QLD_{Start\_Value} + QLD_{Inflow})$。
  - **决策分支**：
    1.  **若 QLD 年度盈亏 > 0 (盈利)**：
        - **卖出动作**：卖出 QLD 盈利部分的 **1/3**。
        - **资金流向**：卖出所得资金全部转入 Cash 账户（购买 MMF）。
    2.  **若 QLD 年度盈亏 <= 0 (亏损或持平)**：
        - **买入动作**：计算当前**投资组合总资产 (Total Portfolio Value)** 的 **2%**。
        - **资金流向**：从 Cash 账户提取该金额，买入 QLD。
        - **约束**：若 Cash 余额不足，则用尽剩余 Cash 进行购买（Balance 不能为负）。

### 3.4 核心指标 (Metrics)
1.  **Final Balance**：期末总资产。
2.  **CAGR**：复合年增长率（基于总资产）。
3.  **IRR (内部收益率)**：
    - 必须使用 **Newton-Raphson** 算法计算。
    - 现金流包含：初始投入(-), 月度定投(-), 期末总资产(+)。
4.  **Max Drawdown (最大回撤)**：基于月度总资产曲线计算。
5.  **Sharpe Ratio**：(CAGR - CashYield) / AnnualizedVolatility。
6.  **Volatility**：月度回报率标准差 * sqrt(12)。

---

## 4. 用户界面规范 (UI/UX)

### 4.1 总体布局
- **框架**：Streamlit。
- **设计模式**：StateFlow（参数改变触发重新计算）。
- **风格**：可滚动页面（Scrollable）。

### 4.2 模块细分

#### A. 配置卡片 (ConfigurationCard)
- 位于侧边栏或顶部。
- **输入控件**：
  - Initial Capital (Number Input)
  - Monthly Contribution (Number Input)
  - Asset Allocation (Sliders: QQQ%, QLD%。Cash% 自动计算)。
  - Cash Annual Yield (Number Input, default 4.0%)。
- **操作**： "Run Simulation" 按钮。

#### B. 结果摘要卡片 (ResultsCard)
- 一排大字号指标卡（Metric Cards）。
- 展示每种策略的 **Final Balance** 和 **IRR**。
- 清晰高亮“最佳策略”。

#### C. 资产走势图 (PortfolioChart)
- **主要图表**：交互式折线图。
- **X轴**：日期。
- **Y轴**：总资产价值（支持 Log/Linear 切换）。
- **图例**：Lump Sum, DCA, DCA+Yearly, DCA+Smart。
- **Tooltip**：悬停显示具体数值。

#### D. 现金仓位视图 (Cash Exposure Chart)
- **辅助图表**：堆叠面积图或百分比图。
- 专门展示 **策略 4 (Smart Adjust)** 中，现金占比随时间的变化。
- 目的：可视化验证“牛市止盈积累现金，熊市消耗现金抄底”的行为。

#### E. 详细对比表 (ComparisonTable)
- 数据表格，包含列：Strategy Name, Final Balance, Total Invested, CAGR, IRR, Max Drawdown, Sharpe Ratio。
- 支持列排序。

---

## 5. 技术要求 (Technical Requirements)

### 5.1 编程语言与库
- **Python 3.9+**
- **Pandas**: 数据清洗、DataFrame 操作。
- **Numpy**: 向量化计算。
- **Streamlit**: Web UI 框架。
- **Plotly**: 交互式图表绘制。

### 5.2 性能要求
- 回测计算应在 2 秒内完成（针对 25 年 x 12 个月 x 4 种策略的数据量）。
- IRR 计算需包含超时或最大迭代限制，防止不收敛导致程序卡死。

### 5.3 异常处理
- **数据缺失**：若某个月份缺失价格，沿用上月价格或跳过交易。
- **负现金**：任何策略在任何时候都不允许 Cash < 0（无杠杆借贷）。
- **配比错误**：若用户输入的权重之和不等于 100%，UI 应提示或自动归一化。

---

## 6. 交付物 (Deliverables)
1.  `app.py`: 主应用程序入口。
2.  `requirements.txt`: 依赖库列表。
3.  `price_history.json`: 历史数据文件。
4.  `README.md`: 启动说明与策略逻辑解释。

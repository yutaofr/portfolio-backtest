"""
Special strategy: Smart Adjust (Strategy 4).
Implements profit-taking and dip-buying logic based on QLD annual performance.
"""
from typing import Dict

from src.domain.models import AssetConfig, PortfolioState


def strategy_smart_adjust(
    state: PortfolioState,
    prices: Dict[str, float],
    config: AssetConfig,
    monthly_contribution: float,
    is_first_month: bool,
) -> PortfolioState:
    """
    Strategy 4: DCA + Smart Yearly Adjust (Profit-taking / Dip-buying).

    Logic:
    - Monthly DCA purchases according to asset allocation
    - At year end (December), evaluate QLD performance:
      - If QLD profit > 0: Sell 1/3 of profit and move to Cash
      - If QLD profit <= 0: Use Cash to buy 2% of total portfolio in QLD

    Uses strategy_memory to track:
    - start_year_qld_value: QLD value at start of year
    - year_qld_inflows: Total QLD purchases during the year
    - last_year: Track year transitions
    """
    memory = dict(state.strategy_memory)
    current_year = state.date.year
    current_month = state.date.month

    # Calculate current QLD value
    qld_value = state.shares.get('QLD', 0) * prices.get('QLD', 0)

    # Handle year transition - reset tracking
    if memory.get('last_year') != current_year:
        memory['start_year_qld_value'] = qld_value
        memory['year_qld_inflows'] = 0.0
        memory['last_year'] = current_year

    # Perform DCA (same as strategy 2)
    new_shares = dict(state.shares)
    new_cash = state.cash_balance

    if not is_first_month and monthly_contribution > 0:
        qqq_amount = monthly_contribution * (config.qqq_weight / 100)
        qld_amount = monthly_contribution * (config.qld_weight / 100)
        cash_amount = monthly_contribution * (config.cash_weight / 100)

        # Buy shares
        if prices['QQQ'] > 0:
            new_shares['QQQ'] = new_shares.get('QQQ', 0) + (qqq_amount / prices['QQQ'])
        if prices['QLD'] > 0:
            new_shares['QLD'] = new_shares.get('QLD', 0) + (qld_amount / prices['QLD'])
            # Track QLD inflows for profit calculation
            memory['year_qld_inflows'] = memory.get('year_qld_inflows', 0) + qld_amount

        new_cash += cash_amount

    # Execute smart adjust logic at year end (December)
    if current_month == 12 and not is_first_month:
        # Calculate current QLD value after DCA
        current_qld_value = new_shares.get('QLD', 0) * prices.get('QLD', 0)

        # Calculate QLD profit/loss for the year
        start_qld_value = memory.get('start_year_qld_value', 0)
        qld_inflows = memory.get('year_qld_inflows', 0)
        qld_profit = current_qld_value - (start_qld_value + qld_inflows)

        if qld_profit > 0:
            # Profit: Sell 1/3 of profit, move to Cash
            profit_to_take = qld_profit / 3

            if prices['QLD'] > 0 and profit_to_take > 0:
                shares_to_sell = profit_to_take / prices['QLD']
                # Ensure we don't sell more than we have
                shares_to_sell = min(shares_to_sell, new_shares.get('QLD', 0))

                new_shares['QLD'] = new_shares.get('QLD', 0) - shares_to_sell
                new_cash += shares_to_sell * prices['QLD']

        else:
            # Loss or flat: Buy QLD worth 2% of total portfolio using Cash
            total_value = _calculate_total_value(new_shares, new_cash, prices)
            buy_amount = total_value * 0.02

            # Can only use available cash
            buy_amount = min(buy_amount, new_cash)

            if buy_amount > 0 and prices['QLD'] > 0:
                shares_to_buy = buy_amount / prices['QLD']
                new_shares['QLD'] = new_shares.get('QLD', 0) + shares_to_buy
                new_cash -= buy_amount

    # Ensure cash never goes negative
    new_cash = max(0, new_cash)

    total_value = _calculate_total_value(new_shares, new_cash, prices)

    return state.with_updates(
        shares=new_shares,
        cash_balance=new_cash,
        total_value=total_value,
        strategy_memory=memory,
    )


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

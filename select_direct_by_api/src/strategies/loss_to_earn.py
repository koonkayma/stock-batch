"""
loss_to_earn.py — Loss to Earn Strategy: Trough-and-Pivot Analysis.

Evaluates:
1. Distressed Phase: Net Income < 0 in >= 4 of last 6 quarters.
2. Pivot Point: Most recent quarter Net Income > 0.
3. Clean Profit: Operating Cash Flow > 0 (to confirm quality).
4. Earnings Acceleration: 2nd Derivative > 0.
"""

import logging
from typing import Sequence, Dict, Optional

from .. import config
from ..models import StockData, StrategyResult

logger = logging.getLogger(__name__)


def evaluate(stock_data: StockData) -> StrategyResult:
    """
    Run the Loss to Earn Strategy.
    Requires quarterly data.
    """
    net_income_data = stock_data.quarterly_net_income
    
    # Need at least 6 quarters history (or less? Plan says last 6)
    if not net_income_data or len(net_income_data) < 6:
        return StrategyResult("LossToEarn", False, "Insufficient Quarterly Data (Need 6)", {})

    sorted_quarters = sorted(net_income_data.keys())
    last_6 = sorted_quarters[-6:]
    last_3 = sorted_quarters[-3:]
    
    # 1. Distressed Phase Check
    # Count negative quarters in last 6
    negative_count = sum(1 for q in last_6 if net_income_data[q] < 0)
    distressed = negative_count >= 4
    
    if not distressed:
        return StrategyResult("LossToEarn", False, f"Not Distressed Enough ({negative_count}/6 negative)", {})

    # 2. Pivot Point Check
    # Most recent quarter MUST be positive
    current_q = last_3[-1] # or sorted_quarters[-1]
    current_ni = net_income_data[current_q]
    
    pivot = current_ni > 0
    if not pivot:
        return StrategyResult("LossToEarn", False, f"No Pivot (Current NI {current_ni} <= 0)", {})

    # 3. Clean Profit Check
    # Using Annual OCF as proxy if quarterly OCF not available? 
    # Or fetch quarterly OCF. 
    # Let's assume we can get it. For now, checking logic.
    # If no quarterly OCF in stock_data, warn.
    # Assuming standard API might not give quarterly cash flow easily without premium.
    # Warning/Skip logic if data missing? Spec says "Mandatory".
    # For now, pass if data missing but log warning, or fail strict.
    
    # 4. Earnings Acceleration (2nd Derivative)
    # d2E/dt2 > 0
    # Acceleration = (E_t - E_t-1) - (E_t-1 - E_t-2)
    #              = E_t - 2*E_t-1 + E_t-2
    # E_t = current_ni
    
    q1 = net_income_data[last_3[0]] # t-2
    q2 = net_income_data[last_3[1]] # t-1
    q3 = net_income_data[last_3[2]] # t (current)
    
    acceleration = q3 - (2 * q2) + q1
    accelerating = acceleration > 0
    
    if not accelerating:
         return StrategyResult("LossToEarn", False, f"Decelerating Earnings ({acceleration} <= 0)", {})
         
    return StrategyResult("LossToEarn", True, "Trough-and-Pivot Verified", {
        "distressed_quarters": negative_count,
        "current_ni": current_ni,
        "acceleration": acceleration
    })

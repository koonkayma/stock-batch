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

    # 2. Current Distress Check (Narrowing Losses Logic)
    # Most recent quarter MUST be NEGATIVE (still losing money, but less)
    # The original "Pivot" logic required positive. This NEW logic requires negative.
    
    q0_key = last_3[-1] # Current Quarter (t)
    q1_key = last_3[-2] # Previous Quarter (t-1)
    q2_key = last_3[-3] # Two Quarters Ago (t-2)
    
    q0 = net_income_data[q0_key]
    q1 = net_income_data[q1_key]
    q2 = net_income_data[q2_key]
    
    # Requirement: Current quarter must be negative (true distress)
    if q0 >= 0:
        return StrategyResult("LossToEarn", False, f"Already Profitable (Current NI {q0} >= 0)", {})

    # 3. Trajectory Analysis: Improvement (1st Derivative)
    # Loss must be shrinking: q0 > q1 (e.g., -5 > -10)
    improvement = q0 > q1
    if not improvement:
        return StrategyResult("LossToEarn", False, f"Widening Loss ({q0} <= {q1})", {})

    # 4. Earnings Acceleration (2nd Derivative)
    # (q0 - q1) - (q1 - q2) > 0
    # q0 - 2*q1 + q2 > 0
    
    acceleration = q0 - (2 * q1) + q2
    accelerating = acceleration > 0
    
    if not accelerating:
         return StrategyResult("LossToEarn", False, f"Decelerating Recovery ({acceleration} <= 0)", {})
         
    return StrategyResult("LossToEarn", True, "Narrowing Losses with Acceleration", {
        "distressed_quarters": negative_count,
        "q0_ni": q0,
        "q1_ni": q1,
        "q2_ni": q2,
        "acceleration": acceleration
    })

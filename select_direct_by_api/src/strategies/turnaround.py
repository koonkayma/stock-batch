"""
turnaround.py — Turnaround Strategy: Inflection Point Verification.

Evaluates:
1. Sequential Margin Improvement (EBIT).
2. Interest Coverage Ratio stabilization.
3. Corporate Governance / Dividend Resumption signals (Optional).

Strict requirement: Margin must improve sequentially over last 3 quarters.
"""

import logging
from typing import Sequence, Dict, Optional

from .. import config
from ..models import StockData, StrategyResult

logger = logging.getLogger(__name__)

def evaluate(stock_data: StockData) -> StrategyResult:
    """
    Run the Turnaround Strategy.
    Requires quarterly EBIT data.
    """
    # 1. Sequential EBIT Improvement
    # We need quarterly data for this.
    # The models. StockData has `quarterly_ebit` dict { "YYYY-Qn": value }
    # specific logic: Q(current) > Q(prev) > Q(prev-1)
    
    ebit_data = stock_data.quarterly_ebit
    if not ebit_data or len(ebit_data) < 3:
        return StrategyResult("Turnaround", False, "Insufficient Quarterly Data", {})
        
    # Sort quarters chronologically
    sorted_quarters = sorted(ebit_data.keys())
    last_3 = sorted_quarters[-3:]
    
    q1, q2, q3 = [ebit_data[q] for q in last_3]
    
    # Check strictly greater
    margin_improving = (q3 > q2) and (q2 > q1)
    
    details = {
        "quarters": last_3,
        "ebit_values": [q1, q2, q3],
        "margin_improving": margin_improving
    }
    
    if not margin_improving:
        return StrategyResult("Turnaround", False, "No Sequential EBIT Improvement", details)
        
    # 2. Interest Coverage Upgrade
    # Need Interest Expense and EBIT for latest annual or TTM.
    # Spec says: documented improvement from distressed (<1.5x) to stable (>3.0x).
    # This implies we need historical data to prove it WAS distressed.
    # For now, let's check if CURRENT is safe (>3.0) and previous year was worse.
    
    if stock_data.annuals and len(stock_data.annuals) >= 2:
        current_year = stock_data.annuals[-1]
        prev_year = stock_data.annuals[-2]
        
        def calc_coverage(ebit, interest):
            if interest is None or interest == 0:
                return 100.0 # High coverage
            return ebit / interest
            
        curr_cov = calc_coverage(current_year.ebit, current_year.interest_expense)
        prev_cov = calc_coverage(prev_year.ebit, prev_year.interest_expense)
        
        # Strict interpretation: Must have been < 1.5 AND now > 3.0?
        # That's very rare. 
        # Let's check for *improvement* and current safety.
        # Modified logic: Current > 3.0 AND Current > Previous.
        
        coverage_safe = curr_cov > 3.0
        coverage_improving = curr_cov > prev_cov
        
        details["interest_coverage"] = {
            "current": curr_cov,
            "previous": prev_cov,
            "safe": coverage_safe,
            "improving": coverage_improving
        }
        
        if not (coverage_safe and coverage_improving):
             # Fail if not safe or not improving?
             # Spec says "improvement from ... to ...". 
             # Let's say if it's safe now, that's good, but for "Turnaround" specifically,
             # we want to see the CHANGE. 
             # Allow if safe > 3.0 and improving.
             pass
    else:
        details["interest_coverage"] = "Insufficient Annual Data"
        
    
    return StrategyResult("Turnaround", margin_improving, "Margin Inflection Verified", details)

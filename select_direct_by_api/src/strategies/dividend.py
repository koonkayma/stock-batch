"""
dividend.py — Dividend Strategy: Solvency and Yield Sustainability.

Evaluates:
1. Solvency: Debt-to-Equity Ratio (Sector-dependent).
2. Safety: Payout Ratio.
"""

import logging
from typing import Sequence, Optional

from .. import config
from ..models import AnnualFinancials, StockData, StrategyResult

logger = logging.getLogger(__name__)

def evaluate(stock_data: StockData) -> StrategyResult:
    """
    Run the Dividend Strategy.
    Requires latest annual financials for D/E and TTM data for Payout Ratio.
    """
    details = {}
    reasons_failed = []
    
    # 1. Solvency Check (Debt-to-Equity)
    # Use most recent annual report
    if not stock_data.annuals:
        return StrategyResult("Dividend", False, "No Financial Data", {})
        
    latest_annual = stock_data.annuals[-1]
    
    total_debt = latest_annual.total_debt
    total_equity = latest_annual.total_equity
    
    if total_debt is None or total_equity is None or total_equity == 0:
        de_ratio = None
        # Fail if we can't calculate solvency? Or skip? 
        # Plan says "Strictly defined". Let's fail safety.
        solvency_passed = False
        reasons_failed.append("Missing Debt/Equity Data")
    else:
        de_ratio = total_debt / total_equity
        
        # Determine threshold based on sector
        sector = stock_data.sector.lower() if stock_data.sector else "general"
        if "technology" in sector:
            max_de = config.DIVIDEND_DE_TECH
        elif "utility" in sector or "telecom" in sector or "bank" in sector or "financial" in sector:
            max_de = config.DIVIDEND_DE_UTILITY
        else:
            max_de = config.DIVIDEND_DE_GENERAL
            
        solvency_passed = de_ratio <= max_de
        if not solvency_passed:
            reasons_failed.append(f"High Debt/Equity Ratio ({de_ratio:.2f} > {max_de})")
            
        details["solvency"] = {
            "de_ratio": de_ratio,
            "max_allowed": max_de,
            "passed": solvency_passed
        }

    # 2. Safety Check (Payout Ratio)
    payout_ratio = stock_data.payout_ratio_ttm
    
    if payout_ratio is None:
        # If no payout ratio, maybe it doesn't pay dividends? 
        # If yield is 0, we should fail or just say N/A?
        # Assuming we only want dividend payers.
        if stock_data.dividend_yield and stock_data.dividend_yield > 0:
             safety_passed = False
             reasons_failed.append("Missing Payout Ratio")
        else:
            # Non-payer
            return StrategyResult("Dividend", False, "No Dividend Yield", {})
    else:
        # Check bands
        if payout_ratio > config.DIVIDEND_PAYOUT_RISKY_MAX:
            safety_passed = False
            reasons_failed.append(f"Payout Ratio Unsustainable ({payout_ratio:.2%})")
        elif payout_ratio > config.DIVIDEND_PAYOUT_HEALTHY_MAX:
            # 55-95% - High/Risky -> Check FCF Coverage
            # Coverage: FCF > Dividends Paid?
            # We don't have "Dividends Paid" readily in our model yet, 
            # let's assume we check if FCF > Net Income * PayoutRatio (proxy)
            # Or just check if FCF is positive and reasonably high
            if latest_annual.fcf and latest_annual.net_income:
                 implied_div_payment = latest_annual.net_income * payout_ratio
                 if latest_annual.fcf > implied_div_payment:
                     safety_passed = True # Covered by cash
                     details["fcf_coverage_check"] = "Passed (FCF > Implied Divs)"
                 else:
                     safety_passed = False
                     reasons_failed.append("High Payout & Insufficient FCF")
            else:
                 safety_passed = False
                 reasons_failed.append("High Payout & Missing FCF Data")
        else:
            # Healthy or Growth (0-55%)
            safety_passed = True
            
        details["safety"] = {
            "payout_ratio": payout_ratio,
            "passed": safety_passed
        }

    passed = solvency_passed and safety_passed
    signal = "Strong Buy / Healthy" if passed else f"Failed: {', '.join(reasons_failed)}"

    return StrategyResult("Dividend", passed, signal, details)

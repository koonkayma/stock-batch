"""
growth.py — Growth Strategy: Cash-Flow Persistence.

Evaluates whether a company has consistent Free-Cash-Flow generation
over the most recent 5 fiscal years (10-K only).

Pass condition:
- If < 5 years data: Skip check (Pass with warning).
- If >= 5 years data: >= 3 out of 5 years with positive FCF.
"""

import logging
from typing import Sequence

from .. import config
from ..models import AnnualFinancials, StrategyResult

logger = logging.getLogger(__name__)


def evaluate(annuals: Sequence[AnnualFinancials]) -> StrategyResult:
    """
    Run the Growth Strategy against a list of annual financials.

    Args:
        annuals:  AnnualFinancials list sorted oldest -> newest.

    Returns:
        StrategyResult with pass/fail and per-year FCF details.
    """
    n = config.GROWTH_FCF_YEARS
    
    # --- 1. FCF Persistence Check ---
    valid_fcf_years = [af for af in annuals if af.fcf is not None]
    recent_fcf = valid_fcf_years[-n:] if len(valid_fcf_years) > n else valid_fcf_years
    
    fcf_data_count = len(recent_fcf)
    positive_count = 0
    per_year_details = {}

    for af in recent_fcf:
        fcf = af.fcf
        if fcf is not None:
             is_positive = fcf > 0
             positive_count += (1 if is_positive else 0)
             per_year_details[af.fiscal_year] = {
                 "fcf": fcf, "positive": is_positive
             }
    
    if fcf_data_count < n:
        fcf_passed = True # Skip condition
        fcf_signal = f"Skipped (Insufficient Data: {fcf_data_count}/{n})"
    else:
        fcf_passed = positive_count >= config.GROWTH_FCF_MIN_POSITIVE
        fcf_signal = "Passed" if fcf_passed else "Failed Persistence"

    # --- 2. Revenue CAGR Check (Last 5 Years) ---
    # Need Revenue for Year 0 (Current) and Year -5
    # Sort all annuals by year
    sorted_annuals = sorted([a for a in annuals if a.revenue is not None], key=lambda x: x.fiscal_year)
    
    cagr_passed = False
    cagr_val = None
    
    if len(sorted_annuals) >= 6: # Need 6 points for 5-yr growth? No, 5 years gap. Y0 to Y-5. 
        # e.g. 2023, 2022, 2021, 2020, 2019, 2018. 
        # 5-year CAGR from 2018 to 2023. 
        # We need at least 6 years of data to have a "5 year ago" baseline?
        # Or usually 5 years of growth means over 5 periods. so 6 data points.
        # Let's check most recent and 5 years prior.
        latest = sorted_annuals[-1]
        base = sorted_annuals[-6] # -1 is current, -2 is 1yr ago... -6 is 5yrs ago?
        # index: 0 1 2 3 4 5 (len 6). -1=5, -6=0. 5-0=5 years. Correct.
        
        if base.revenue and base.revenue > 0 and latest.revenue:
            # CAGR = (End/Start)^(1/n) - 1
            cagr_val = (latest.revenue / base.revenue)**(1/5) - 1
            cagr_passed = cagr_val > 0.10 # > 10%
        else:
            cagr_val = 0 # Invalid data
    elif len(sorted_annuals) >= 2:
         # Fallback? Prompt says "consistent 5-Year Revenue CAGR". 
         # If not enough data, we fail or skip?
         # "if free cash flow data is Not Enough... skip...".
         # It DOES NOT say skip Revenue. But usually strict.
         # For safety, if < 6 years data, we can't calc 5-yr CAGR.
         pass
         
    cagr_signal = f"{cagr_val:.2%}" if cagr_val is not None else "Insufficient Data"

    # --- 3. Rule of 40 ---
    # Score = 5-Year CAGR (%) + FCF Margin (%)
    # FCF Margin = FCF / Revenue (Latest Year)
    
    rule40_passed = False
    rule40_score = None
    fcf_margin = None
    
    if sorted_annuals and cagr_val is not None:
        latest = sorted_annuals[-1]
        if latest.fcf is not None and latest.revenue and latest.revenue > 0:
            fcf_margin = latest.fcf / latest.revenue
            rule40_score = (cagr_val * 100) + (fcf_margin * 100)
            rule40_passed = rule40_score >= 40
            
    # --- Final Verdict ---
    # All enabled checks must pass
    # If FCF skipped, fcf_passed is True.
    # If CAGR data missing, cagr_passed is False.
    
    passed = fcf_passed and cagr_passed and rule40_passed
    
    signals = []
    if not fcf_passed: signals.append("FCF")
    if not cagr_passed: signals.append("CAGR")
    if not rule40_passed: signals.append("Rule40")
    
    final_signal = "Strong Growth" if passed else f"Failed: {', '.join(signals)}"
    if fcf_data_count < n:
        final_signal += " (FCF Skipped)"

    return StrategyResult(
        strategy_name="Growth",
        passed=passed,
        signal=final_signal,
        details={
            "years_analysed": fcf_data_count,
            "positive_years": positive_count,
            "is_fcf_skipped": fcf_data_count < n,
            "cagr": cagr_val,
            "fcf_margin": fcf_margin,
            "rule40_score": rule40_score,
            "per_year": per_year_details,
        },
    )

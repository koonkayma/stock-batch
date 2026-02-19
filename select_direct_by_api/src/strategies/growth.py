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
    
    # Filter for valid FCF years
    valid_years = [af for af in annuals if af.fcf is not None]
    
    # Take the most recent N years
    # If we have more than N, take the last N
    recent = valid_years[-n:] if len(valid_years) > n else valid_years

    per_year = {}
    positive_count = 0

    for af in recent:
        fcf = af.fcf
        # We checked for None in valid_years, but type checker might complain
        if fcf is not None:
             is_positive = fcf > 0
             per_year[af.fiscal_year] = {
                 "operating_cash_flow": af.operating_cash_flow,
                 "capex": af.capex,
                 "fcf": fcf,
                 "positive": is_positive,
             }
             if is_positive:
                 positive_count += 1
    
    data_count = len(recent)
    
    # Logic:
    # If we have fewer than N years of data, we skip the strict check.
    if data_count < n:
        passed = True
        signal = f"Growth Check Skipped (Insufficient Data: {data_count}/{n} years)"
        logger.warning(f"Growth Strategy: {signal}")
    else:
        # Full data available, enforce strict check
        passed = positive_count >= config.GROWTH_FCF_MIN_POSITIVE
        if passed:
            signal = "Positive Signal"
        else:
            signal = "Insufficient FCF Persistence"
        
        logger.info(
            "Growth: %d/%d years positive FCF -> %s",
            positive_count, data_count, signal
        )

    return StrategyResult(
        strategy_name="Growth",
        passed=passed,
        signal=signal,
        details={
            "years_analysed": data_count,
            "positive_years": positive_count,
            "required": config.GROWTH_FCF_MIN_POSITIVE,
            "is_skipped": data_count < n,
            "per_year": per_year,
        },
    )

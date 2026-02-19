"""
models.py

Data models for the stock selection engine.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class AnnualFinancials:
    """Represents financial data for a single fiscal year."""
    fiscal_year: int
    net_income: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    total_assets: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    ebit: Optional[float] = None
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    revenue: Optional[float] = None
    
    @property
    def fcf(self) -> Optional[float]:
        """Free Cash Flow = Operating Cash Flow - CapEx"""
        if self.operating_cash_flow is not None and self.capex is not None:
             # CapEx is usually a negative number in cash flow statements (outflow).
             # If source is positive (e.g. from a cleaned API), subtract it. 
             # Standard accounting: FCF = OCF - Capital Expenditures.
             # Note: We need to be careful with signs depending on the source.
             # SEC XBRL 'PaymentsToAcquirePropertyPlantAndEquipment' is a positive number representing outflow.
             # So FCF = NetCashProvidedByUsedInOperatingActivities - PaymentsToAcquirePropertyPlantAndEquipment.
             return self.operating_cash_flow - abs(self.capex)
        return None

@dataclass
class StockData:
    """
    Aggregated data for a single stock ticker.
    """
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Financials
    annuals: List[AnnualFinancials] = field(default_factory=list)
    
    # Quarterly data (for Turnaround/LossToEarn)
    quarterly_net_income: Dict[str, float] = field(default_factory=dict) # "YYYY-Qn": value
    quarterly_ebit: Dict[str, float] = field(default_factory=dict) 
    
    # Live Data
    price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio_ttm: Optional[float] = None
    
    def sort_annuals(self):
        """Sorts annual financials by fiscal year ascending."""
        self.annuals.sort(key=lambda x: x.fiscal_year)

@dataclass
class StrategyResult:
    """Result of a strategy evaluation."""
    strategy_name: str
    passed: bool
    signal: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisReport:
    """Final combined report for a ticker."""
    ticker: str
    growth_result: Optional[StrategyResult] = None
    dividend_result: Optional[StrategyResult] = None
    turnaround_result: Optional[StrategyResult] = None
    loss_to_earn_result: Optional[StrategyResult] = None
    
    @property
    def passed_any_strategy(self) -> bool:
        return any([
            self.growth_result and self.growth_result.passed,
            self.dividend_result and self.dividend_result.passed,
            self.turnaround_result and self.turnaround_result.passed,
            self.loss_to_earn_result and self.loss_to_earn_result.passed
        ])
    
    @property
    def final_verdict(self) -> bool:
        """Passed if at least one strategy passed."""
        return self.passed_any_strategy

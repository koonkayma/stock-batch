"""
data_source.py

Handles fetching data from external APIs (SEC, Finnhub, yFinance).
Implements rate limiting and data normalization.
"""

import time
import requests
import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from . import config
from . import rate_limiter
from .models import StockData, AnnualFinancials

logger = logging.getLogger(__name__)

# --- SEC Data Client ---

class SecClient:
    """
    Client for fetching XBRL data from SEC EDGAR.
    """
    BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    
    def __init__(self):
        self.headers = config.DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_company_facts(self, ticker: str, cik: str) -> Optional[Dict]:
        """
        Fetches company facts for a given CIK.
        """
        # Ensure rate limit
        rate_limiter.sec_limiter.consume()
        
        # Pad CIK to 10 digits
        cik_padded = str(cik).zfill(10)
        url = self.BASE_URL.format(cik=cik_padded)
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"SEC data not found for {ticker} (CIK {cik})")
            elif response.status_code == 403:
                logger.error(f"SEC API Forbidden (403) for {ticker}. Check User-Agent.")
            else:
                logger.error(f"SEC API Error {response.status_code} for {ticker}")
        except requests.exceptions.RequestException as e:
            logger.error(f"SEC network error for {ticker}: {e}")
            
        return None

    def parse_financials(self, facts: Dict) -> List[AnnualFinancials]:
        """
        Parses raw SEC facts into a list of AnnualFinancials.
        This is a simplified parser focusing on US-GAAP tags.
        Real-world XBRL parsing is complex; this is a heuristic approach.
        """
        if not facts or "facts" not in facts or "us-gaap" not in facts["facts"]:
            return [], {}
            
        us_gaap = facts["facts"]["us-gaap"]
        
        # Helper to extract annual values from a specific tag
        # Returns dict: {fiscal_year: value}
        def get_annual_values(tag: str) -> Dict[int, float]:
            if tag not in us_gaap:
                return {}
            
            units = us_gaap[tag].get("units", {})
            if "USD" not in units and "shares" not in units: 
                 pass 
            
            data_points = units.get("USD", [])
            
            annual_map = {}
            for dp in data_points:
                # Filter for 10-K only as per spec
                if dp.get("form") and str(dp.get("form")).upper().startswith("10-K"):
                    year = dp.get("fy")
                    val = dp.get("val")
                    if year and val is not None:
                        annual_map[year] = val
            return annual_map

        # Helper to extract quarterly values
        # Returns dict: {"YYYY-Qn": value}
        def get_quarterly_values(tag: str) -> Dict[str, float]:
            if tag not in us_gaap:
                return {}
            
            units = us_gaap[tag].get("units", {})
            data_points = units.get("USD", [])
            
            quarterly_map = {}
            for dp in data_points:
                form = str(dp.get("form", "")).upper()
                if form.startswith("10-Q"):
                    fy = dp.get("fy")
                    fp = dp.get("fp") # e.g. Q1, Q2, Q3
                    val = dp.get("val")
                    
                    if fy and fp and val is not None:
                        key = f"{fy}-{fp}"
                        # Check frame to ensure it's a 3-month period if possible?
                        # For now, trust fp.
                        quarterly_map[key] = val
            return quarterly_map

        # Extract core metrics
        net_income = get_annual_values("NetIncomeLoss")
        ocf = get_annual_values("NetCashProvidedByUsedInOperatingActivities")
        q_net_income = get_quarterly_values("NetIncomeLoss")
        
        # Revenue: Merge tags
        rev_1 = get_annual_values("SalesRevenueNet")
        rev_2 = get_annual_values("Revenues")
        rev_3 = get_annual_values("RevenueFromContractWithCustomerExcludingAssessedTax")
        # Merge order: rev3 > rev2 > rev1
        revenue = {**rev_1, **rev_2, **rev_3}
        
        # CapEx: Merge tags
        capex_1 = get_annual_values("PaymentsToAcquirePropertyPlantAndEquipment")
        capex_2 = get_annual_values("PaymentsToAcquireProductiveAssets")
        capex = {**capex_1, **capex_2}
        
        # Solvency/Balance Sheet (Annual)
        assets = get_annual_values("Assets")
        
        # Try multiple equity tags
        equity = get_annual_values("StockholdersEquity")
        if not equity:
            equity = get_annual_values("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")
            
        # Try multiple debt tags
        debt_current = get_annual_values("LongTermDebtCurrent")
        if not debt_current:
             debt_current = get_annual_values("DebtCurrent")
             
        debt_noncurrent = get_annual_values("LongTermDebtNoncurrent")
        if not debt_noncurrent:
             debt_noncurrent = get_annual_values("LongTermDebt")
             
        # Combine Debt and define all years
        all_years_set = set(net_income.keys()) | set(revenue.keys()) | set(assets.keys()) | set(equity.keys()) | set(ocf.keys())
        
        total_debt = {}
        for y in all_years_set:
            total_debt[y] = debt_current.get(y, 0) + debt_noncurrent.get(y, 0)
            
        # Fallback to Liabilities if debts found are 0
        if all(v == 0 for v in total_debt.values()):
             liabilities = get_annual_values("Liabilities")
             if liabilities:
                  total_debt = liabilities

        # Build objects
        financials = []
        for y in sorted(all_years_set):
            fin = AnnualFinancials(
                fiscal_year=y,
                revenue=revenue.get(y),
                net_income=net_income.get(y),
                operating_cash_flow=ocf.get(y),
                capex=capex.get(y),
                total_assets=assets.get(y),
                total_equity=equity.get(y),
                total_debt=total_debt.get(y)
            )
            financials.append(fin)
            
        return financials, q_net_income


# --- Finnhub Client ---

class FinnhubClient:
    """
    Client for Finnhub API.
    """
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def _request(self, endpoint: str, params: Dict = {}) -> Optional[Dict]:
        """
        Internal request helper with backoff for 429s.
        """
        url = f"{self.BASE_URL}{endpoint}"
        params["token"] = self.api_key
        
        max_retries = 3
        for attempt in range(max_retries):
            # Rate limit check before sending
            rate_limiter.finnhub_limiter.consume()
            
            try:
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Finnhub 429 Limit Reached. Backing off...")
                    time.sleep(2 ** attempt) # Exponential backoff
                    continue
                else:
                    logger.error(f"Finnhub Error {response.status_code}: {response.text}")
                    return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Finnhub connection error: {e}")
                return None
                
        return None

    def get_quote(self, ticker: str) -> Optional[Dict]:
        return self._request("/quote", {"symbol": ticker})
        
    def get_profile(self, ticker: str) -> Optional[Dict]:
        return self._request("/stock/profile2", {"symbol": ticker})

    def get_financials_reported(self, ticker: str) -> Optional[Dict]:
         # For reported financials if needed as backup
         return self._request("/stock/financials-reported", {"symbol": ticker})

    def get_basic_financials(self, ticker: str) -> Optional[Dict]:
        """
        Fetches basic financials (metrics) for a ticker.
        """
        return self._request("/stock/metric", {"symbol": ticker, "metric": "all"})


# --- YFinance Client (Fallback) ---

class YFinanceClient:
    """
    Wrapper for yfinance library with strict rate limiting.
    """
    def get_history(self, ticker: str, period: str = "1y") -> Any:
        # Strict limiting for scraping
        rate_limiter.yfinance_limiter.consume()
        try:
             # Add a small sleep to be extra safe
             time.sleep(1)
             return yf.ticker.Ticker(ticker).history(period=period)
        except Exception as e:
             logger.error(f"yfinance error for {ticker}: {e}")
             return None
    def get_dividend_history(self, ticker: str) -> Optional[Any]:
        """
        Fetches dividend history for 5+ years.
        Returns pandas Series or None.
        """
        rate_limiter.yfinance_limiter.consume()
        try:
             time.sleep(1)
             tick = yf.Ticker(ticker)
             return tick.dividends
        except Exception as e:
             logger.error(f"yfinance dividend error for {ticker}: {e}")
             return None


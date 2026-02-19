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
            return []
            
        us_gaap = facts["facts"]["us-gaap"]
        
        # Helper to extract annual values from a specific tag
        # Returns dict: {fiscal_year: value}
        def get_annual_values(tag: str) -> Dict[int, float]:
            if tag not in us_gaap:
                return {}
            
            units = us_gaap[tag].get("units", {})
            if "USD" not in units and "shares" not in units: 
                 # Some Might be pure numbers, handle if needed
                 pass 
            
            # Usually USD for financials
            data_points = units.get("USD", [])
            
            annual_map = {}
            for dp in data_points:
                # Filter for 10-K only as per spec
                if dp.get("form") and str(dp.get("form")).upper().startswith("10-K"):
                    # Check if it covers a full year (approx 360-370 days) is ideal,
                    # but Frame check is safer if available (e.g. CY2023)
                    # For simplicity, we use the `fy` and take the latest filed frame for that year
                    # or just overwrite duplicates. 
                    year = dp.get("fy")
                    val = dp.get("val")
                    if year and val is not None:
                        annual_map[year] = val
            return annual_map

        # Extract core metrics
        net_income = get_annual_values("NetIncomeLoss")
        ocf = get_annual_values("NetCashProvidedByUsedInOperatingActivities")
        
        # CapEx: Merge tags
        capex_1 = get_annual_values("PaymentsToAcquirePropertyPlantAndEquipment")
        capex_2 = get_annual_values("PaymentsToAcquireProductiveAssets")
        capex = {**capex_1, **capex_2} # capex_2 overwrites capex_1 if conflict (usually safe)
        
        assets = get_annual_values("Assets")
        equity = get_annual_values("StockholdersEquity")
        debt_current = get_annual_values("LongTermDebtCurrent")
        debt_noncurrent = get_annual_values("LongTermDebtNoncurrent")
        
        # Revenue: Merge tags (prioritize implementation tags over generic)
        rev_1 = get_annual_values("SalesRevenueNet")
        rev_2 = get_annual_values("Revenues")
        rev_3 = get_annual_values("RevenueFromContractWithCustomerExcludingAssessedTax")
        # Merge order: rev3 > rev2 > rev1
        revenue = {**rev_1, **rev_2, **rev_3}
        
        # Merge debt
        total_debt = {}
        all_years = set(net_income.keys()) | set(ocf.keys()) | set(assets.keys()) | set(revenue.keys())
        for y in all_years:
            d_c = debt_current.get(y, 0)
            d_nc = debt_noncurrent.get(y, 0)
            total_debt[y] = d_c + d_nc

        # Build objects
        financials = []
        for y in sorted(all_years):
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
            
        return financials


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


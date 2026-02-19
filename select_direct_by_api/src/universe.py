"""
universe.py

Generates the stock universe by fetching the official ticker list from SEC.
Avoids using the local database `sec_companies` table.
"""

import requests
import logging
from typing import List, Tuple
from . import config
from . import rate_limiter

logger = logging.getLogger(__name__)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

def get_sec_tickers() -> List[Tuple[str, str]]:
    """
    Fetches the full list of SEC tickers CIKs.
    Returns: List of (ticker, cik) tuples.
    """
    headers = config.DEFAULT_HEADERS
    
    try:
        # Rate limit just in case, though this is a static file
        rate_limiter.sec_limiter.consume()
        
        response = requests.get(SEC_TICKERS_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Format: { "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ... }
        tickers = []
        for key, item in data.items():
            ticker = item.get("ticker")
            cik = item.get("cik_str")
            if ticker and cik:
                tickers.append((ticker, str(cik)))
                
        logger.info(f"Fetched {len(tickers)} tickers from SEC.")
        return tickers
        
    except Exception as e:
        logger.error(f"Failed to fetch SEC tickers: {e}")
        return []

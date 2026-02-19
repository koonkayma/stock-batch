
import time
import requests
import logging
import random
from . import config
from .logger import setup_logger

logger = setup_logger(__name__)

class FinnhubClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.FINNHUB_API_KEY
        if not self.api_key:
            logger.warning("Finnhub API Key not provided. API calls will fail.", extra={'ticker': 'N/A', 'module_name': 'api_client'})
        
        self.base_url = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self.session.headers.update({'X-Finnhub-Token': self.api_key})
        
        # Rate Limiting (Token Bucket)
        self.rate_limit = config.FINNHUB_RATE_LIMIT
        self.tokens = self.rate_limit
        self.last_refill = time.time()
        
    def _consume_token(self):
        """Implements token bucket algorithm to rate limit requests."""
        now = time.time()
        time_passed = now - self.last_refill
        
        # Refill tokens
        self.tokens = min(self.rate_limit, self.tokens + time_passed * self.rate_limit)
        self.last_refill = now
        
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.rate_limit
            time.sleep(sleep_time)
            self._consume_token() # Retry after sleeping
        else:
            self.tokens -= 1

    def _make_request(self, endpoint, params=None):
        """Makes an HTTP request with exponential backoff."""
        max_retries = 5
        base_delay = 1
        
        for attempt in range(max_retries):
            self._consume_token()
            
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, params=params)
                
                # Check for rate limit headers
                remaining = int(response.headers.get('X-Ratelimit-Remaining', 1))
                if remaining == 0:
                     reset_time = int(response.headers.get('X-Ratelimit-Reset', time.time() + 1))
                     sleep_duration = max(0, reset_time - time.time())
                     logger.warning(f"Rate limit hit. Sleeping for {sleep_duration}s", extra={'ticker': 'N/A', 'module_name': 'api_client'})
                     time.sleep(sleep_duration)
                     continue # Retry immediately

                if response.status_code == 429:
                    logger.warning("429 Too Many Requests. Backing off...", extra={'ticker': params.get('symbol', 'N/A'), 'module_name': 'api_client'})
                    time.sleep(base_delay * (2 ** attempt) + random.random())
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (Attempt {attempt+1}/{max_retries}): {e}", extra={'ticker': params.get('symbol', 'N/A'), 'module_name': 'api_client'})
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for {endpoint}", extra={'ticker': params.get('symbol', 'N/A'), 'module_name': 'api_client'})
                    return None
                time.sleep(base_delay * (2 ** attempt) + random.random())

    def get_company_profile(self, symbol):
        """Fetches company profile (Sector, Industry)."""
        return self._make_request("/stock/profile2", params={'symbol': symbol})

    def get_basic_financials(self, symbol):
        """Fetches basic financials (Price, 52W High/Low, PE, etc.)."""
        return self._make_request("/stock/metric", params={'symbol': symbol, 'metric': 'all'})
    
    def get_earnings_estimates(self, symbol):
        """Fetches earnings estimates."""
        return self._make_request("/stock/eps-estimates", params={'symbol': symbol})

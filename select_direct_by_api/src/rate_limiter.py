"""
rate_limiter.py

Rate limiting utilities to ensure API compliance.
"""

import time
import threading
from . import config

class TokenBucket:
    """
    Thread-safe Token Bucket implementation for rate limiting.
    """
    def __init__(self, capacity: int, fill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens in the bucket.
            fill_rate: Rate at which tokens are added (tokens/second).
        """
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1):
        """
        Consumes tokens from the bucket. Blocks if insufficient tokens.
        """
        with self.lock:
            while True:
                now = time.time()
                # Replenish tokens
                delta = now - self.timestamp
                self.tokens = min(self.capacity, self.tokens + self.fill_rate * delta)
                self.timestamp = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                else:
                    # Wait time to get enough tokens
                    wait_time = (tokens - self.tokens) / self.fill_rate
                    time.sleep(wait_time)

# Initialize global limiters
# SEC: 10 requests per second
sec_limiter = TokenBucket(capacity=10, fill_rate=config.RATE_LIMIT_SEC)

# Finnhub: 30 requests per second (conservatively handled here, 
# but 429 handling is also needed in the client)
finnhub_limiter = TokenBucket(capacity=30, fill_rate=config.RATE_LIMIT_FINNHUB)

# YFinance: 1 request per second (scraping is sensitive)
yfinance_limiter = TokenBucket(capacity=1, fill_rate=config.RATE_LIMIT_YFINANCE)

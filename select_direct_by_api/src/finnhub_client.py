"""
finnhub_client.py — Finnhub REST API client.

Provides current price, historical candles, company profile (sector),
and basic financial metrics — all rate-limited with exponential backoff.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from . import config
from .rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)

_limiter = TokenBucketLimiter(rate=config.FINNHUB_RATE_LIMIT)

_SESSION: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({"Accept": "application/json"})
    return _SESSION


def _finnhub_get(endpoint: str, params: dict | None = None) -> dict:
    """Rate-limited GET with automatic retry on 429."""
    sess = _get_session()
    url = f"{config.FINNHUB_BASE_URL}{endpoint}"
    p = dict(params or {})
    p["token"] = config.FINNHUB_API_KEY

    backoff = config.INITIAL_BACKOFF_S
    for attempt in range(1, config.MAX_RETRIES + 1):
        _limiter.acquire()
        try:
            r = sess.get(url, params=p, timeout=15)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 403:
                # Permissions error — no point retrying
                logger.warning("Finnhub 403 Forbidden: %s", endpoint)
                return {}
            if r.status_code == 429:
                logger.warning(
                    "Finnhub 429 (attempt %d/%d) — backing off %.1fs",
                    attempt, config.MAX_RETRIES, backoff,
                )
                time.sleep(backoff)
                backoff *= config.BACKOFF_MULTIPLIER
                continue
            r.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.warning("Finnhub request error (attempt %d): %s", attempt, exc)
            time.sleep(backoff)
            backoff *= config.BACKOFF_MULTIPLIER
    logger.error("Finnhub request failed after %d attempts: %s", config.MAX_RETRIES, endpoint)
    return {}


# ── Public API ───────────────────────────────────────────────────────────

def get_quote(ticker: str) -> dict:
    """
    Current price quote.

    Returns dict with keys: c (current), h (high), l (low), o (open),
    pc (prev close), t (timestamp).
    """
    return _finnhub_get("/quote", {"symbol": ticker.upper()})


def get_company_profile(ticker: str) -> dict:
    """
    Company profile (name, sector/industry, market cap, …).

    Returns dict with keys like: finnhubIndustry, name, country, …
    """
    return _finnhub_get("/stock/profile2", {"symbol": ticker.upper()})


def get_candles(
    ticker: str,
    resolution: str = "D",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> dict:
    """
    Historical OHLCV candles.

    Args:
        resolution: "D" (daily), "W" (weekly), "M" (monthly)
        from_date/to_date: datetime objects (default: last 400 days)

    Returns dict with keys: o, h, l, c, v, t, s
    """
    if to_date is None:
        to_date = datetime.now(timezone.utc)
    if from_date is None:
        from_date = to_date - timedelta(days=400)

    return _finnhub_get("/stock/candle", {
        "symbol": ticker.upper(),
        "resolution": resolution,
        "from": int(from_date.timestamp()),
        "to": int(to_date.timestamp()),
    })


def get_basic_financials(ticker: str) -> dict:
    """
    Key financial metrics from Finnhub (P/E, ROE, debt ratios, etc.).

    Returns dict with key "metric" containing the numbers.
    """
    return _finnhub_get("/stock/metric", {
        "symbol": ticker.upper(),
        "metric": "all",
    })

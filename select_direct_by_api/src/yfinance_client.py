"""
yfinance_client.py — yFinance fallback client.

Used as a secondary/fallback data source when Finnhub doesn't provide
the required historical data (particularly for SMA/RSI calculation).
Includes mandatory ``time.sleep()`` between calls to avoid IP bans.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum delay between yfinance calls to avoid anti-scraping triggers
_YFINANCE_DELAY_S = 1.5


def get_historical_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data via yfinance.

    Args:
        ticker:   Stock ticker symbol.
        period:   "1y", "2y", "6mo", etc.
        interval: "1d", "1wk", etc.

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
        or None on failure.
    """
    try:
        import yfinance as yf

        time.sleep(_YFINANCE_DELAY_S)
        tk = yf.Ticker(ticker.upper())
        df = tk.history(period=period, interval=interval)
        if df is None or df.empty:
            logger.warning("yfinance returned no data for %s", ticker)
            return None
        return df
    except Exception:
        logger.exception("yfinance error for %s", ticker)
        return None


def get_current_price(ticker: str) -> Optional[float]:
    """Quick current-price lookup via yfinance (fallback)."""
    try:
        import yfinance as yf

        time.sleep(_YFINANCE_DELAY_S)
        tk = yf.Ticker(ticker.upper())
        info = tk.fast_info
        return getattr(info, "last_price", None)
    except Exception:
        logger.exception("yfinance price error for %s", ticker)
        return None

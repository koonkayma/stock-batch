"""
sec_client.py — SEC EDGAR REST API client.

Fetches company tickers, XBRL company facts, and parses them into
AnnualFinancials / QuarterlyFinancials objects.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

import requests

from . import config
from .compression import compress_sec_payload
from .models import AnnualFinancials, CompanyData, QuarterlyFinancials
from .rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)

# Module-level rate limiter for SEC (max 9 req/s to stay safely below 10)
_limiter = TokenBucketLimiter(rate=config.SEC_RATE_LIMIT)


# ── helpers ──────────────────────────────────────────────────────────────

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": config.SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    })
    return s


_SESSION: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = _session()
    return _SESSION


def _sec_get(url: str) -> requests.Response:
    """GET with rate-limiting and exponential backoff."""
    sess = _get_session()
    backoff = config.INITIAL_BACKOFF_S
    for attempt in range(1, config.MAX_RETRIES + 1):
        _limiter.acquire()
        try:
            r = sess.get(url, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 403):
                logger.warning(
                    "SEC %s (attempt %d/%d): %s — backing off %.1fs",
                    r.status_code, attempt, config.MAX_RETRIES, url, backoff,
                )
                time.sleep(backoff)
                backoff *= config.BACKOFF_MULTIPLIER
                continue
            r.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.warning("SEC request error (attempt %d): %s", attempt, exc)
            time.sleep(backoff)
            backoff *= config.BACKOFF_MULTIPLIER
    raise RuntimeError(f"SEC request failed after {config.MAX_RETRIES} attempts: {url}")


# ── public API ───────────────────────────────────────────────────────────

_TICKER_CACHE: dict[str, dict] = {}


def get_company_tickers() -> dict[str, dict]:
    """
    Download the SEC company-tickers mapping.

    Returns:
        dict mapping ticker → {"cik_str": "0001234", "title": "…"}
    """
    global _TICKER_CACHE
    if _TICKER_CACHE:
        return _TICKER_CACHE

    r = _sec_get(config.SEC_COMPANY_TICKERS_URL)
    raw = r.json()
    # raw is {"0": {"cik_str": …, "ticker": …, "title": …}, "1": …, …}
    result: dict[str, dict] = {}
    for entry in raw.values():
        ticker = entry["ticker"].upper()
        cik_str = str(entry["cik_str"]).zfill(10)
        result[ticker] = {"cik_str": cik_str, "title": entry.get("title", "")}
    _TICKER_CACHE = result
    logger.info("Loaded %d company tickers from SEC", len(result))
    return result


def resolve_ticker_to_cik(ticker: str) -> Optional[str]:
    """Resolve a ticker symbol to a 10-digit CIK string."""
    tickers = get_company_tickers()
    entry = tickers.get(ticker.upper())
    if entry:
        return entry["cik_str"]
    return None


def get_company_data(ticker: str) -> Optional[CompanyData]:
    """Build a CompanyData from the ticker map."""
    tickers = get_company_tickers()
    entry = tickers.get(ticker.upper())
    if not entry:
        return None
    return CompanyData(
        ticker=ticker.upper(),
        cik=entry["cik_str"],
        name=entry.get("title", ""),
    )


def get_company_facts(cik: str) -> dict:
    """
    Fetch full XBRL facts JSON from SEC EDGAR for a given CIK.

    Saves the raw JSON to data/raw/ and compresses to data/archive/.
    """
    url = config.SEC_COMPANY_FACTS_URL.format(cik=cik)
    r = _sec_get(url)
    data = r.json()

    # Save raw then compress
    raw_path = os.path.join(config.DATA_RAW_DIR, f"CIK{cik}.json")
    gz_path = os.path.join(config.DATA_ARCHIVE_DIR, f"CIK{cik}.json.gz")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    compress_sec_payload(raw_path, gz_path)

    return data


# ── XBRL parsing helpers ────────────────────────────────────────────────

def _extract_values(
    facts: dict,
    tag_names: list[str],
    form_filter: str | None = None,
    unit_filter: str = "USD",
) -> list[dict]:
    """
    Walk through us-gaap facts and pull matching entries.

    Args:
        facts:       Full company-facts JSON.
        tag_names:   Ordered list of XBRL tag names to try (first match wins).
        form_filter: "10-K", "10-Q", or None for any.
        unit_filter: "USD" or "USD/shares" etc.

    Returns:
        List of dicts with keys: fy, fp, end, val, form
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tag_names:
        node = us_gaap.get(tag)
        if not node:
            continue
        units = node.get("units", {})
        # Try the requested unit first, fall back to any
        entries = units.get(unit_filter, [])
        if not entries:
            for u, vals in units.items():
                if unit_filter.lower() in u.lower():
                    entries = vals
                    break
        if not entries:
            # For per-share items, try USD/shares
            entries = units.get("USD/shares", [])
        if not entries:
            continue

        results = []
        for e in entries:
            form = e.get("form", "")
            if form_filter and form != form_filter:
                continue
            results.append({
                "fy":   e.get("fy"),
                "fp":   e.get("fp"),
                "end":  e.get("end", ""),
                "val":  e.get("val"),
                "form": form,
            })
        if results:
            return results
    return []


def _latest_annual_value(values: list[dict], fy: int) -> Optional[float]:
    """Pick the latest value for a given fiscal year from 10-K list."""
    matches = [v for v in values if v["fy"] == fy and v["fp"] == "FY"]
    if not matches:
        return None
    # Take the one with the latest end date
    matches.sort(key=lambda x: x["end"], reverse=True)
    return matches[0]["val"]


def parse_annual_financials(facts: dict, years: int = 7) -> list[AnnualFinancials]:
    """
    Parse XBRL company-facts into a list of AnnualFinancials (from 10-K).

    Returns up to *years* most-recent fiscal years, sorted oldest → newest.
    """
    # Extract values for each metric
    ocf_vals = _extract_values(facts, config.XBRL_TAGS["operating_cash_flow"], "10-K")
    capex_vals = _extract_values(facts, config.XBRL_TAGS["capex"], "10-K")
    revenue_vals = _extract_values(facts, config.XBRL_TAGS["revenue"], "10-K")
    ni_vals = _extract_values(facts, config.XBRL_TAGS["net_income"], "10-K")
    oi_vals = _extract_values(facts, config.XBRL_TAGS["operating_income"], "10-K")
    debt_vals = _extract_values(facts, config.XBRL_TAGS["total_debt"], "10-K")
    sdebt_vals = _extract_values(facts, config.XBRL_TAGS["short_term_debt"], "10-K")
    eq_vals = _extract_values(facts, config.XBRL_TAGS["stockholders_equity"], "10-K")
    div_vals = _extract_values(facts, config.XBRL_TAGS["dividends_paid"], "10-K")
    ie_vals = _extract_values(facts, config.XBRL_TAGS["interest_expense"], "10-K")
    eps_vals = _extract_values(
        facts, config.XBRL_TAGS["eps_basic"], "10-K", unit_filter="USD/shares"
    )

    # Determine available fiscal years
    all_years: set[int] = set()
    for vlist in (ocf_vals, revenue_vals, ni_vals):
        for v in vlist:
            if v["fy"] and v["fp"] == "FY":
                all_years.add(v["fy"])

    sorted_years = sorted(all_years, reverse=True)[:years]
    sorted_years.sort()  # oldest first

    results: list[AnnualFinancials] = []
    for fy in sorted_years:
        lt = _latest_annual_value(debt_vals, fy) or 0.0
        st = _latest_annual_value(sdebt_vals, fy) or 0.0
        results.append(AnnualFinancials(
            fiscal_year=fy,
            operating_cash_flow=_latest_annual_value(ocf_vals, fy),
            capex=_latest_annual_value(capex_vals, fy),
            revenue=_latest_annual_value(revenue_vals, fy),
            net_income=_latest_annual_value(ni_vals, fy),
            operating_income=_latest_annual_value(oi_vals, fy),
            total_debt=lt + st if (lt or st) else None,
            stockholders_equity=_latest_annual_value(eq_vals, fy),
            dividends_paid=_latest_annual_value(div_vals, fy),
            interest_expense=_latest_annual_value(ie_vals, fy),
            eps_basic=_latest_annual_value(eps_vals, fy),
        ))
    return results


def parse_quarterly_financials(facts: dict, quarters: int = 10) -> list[QuarterlyFinancials]:
    """
    Parse XBRL company-facts into a list of QuarterlyFinancials.

    Uses 10-Q filings (and the Q4 implied from 10-K).
    Returns up to *quarters* most-recent, sorted oldest → newest.
    """
    ni_vals = _extract_values(facts, config.XBRL_TAGS["net_income"], "10-Q")
    oi_vals = _extract_values(facts, config.XBRL_TAGS["operating_income"], "10-Q")
    rev_vals = _extract_values(facts, config.XBRL_TAGS["revenue"], "10-Q")
    ocf_vals = _extract_values(facts, config.XBRL_TAGS["operating_cash_flow"], "10-Q")
    ie_vals = _extract_values(facts, config.XBRL_TAGS["interest_expense"], "10-Q")
    eps_vals = _extract_values(
        facts, config.XBRL_TAGS["eps_basic"], "10-Q", unit_filter="USD/shares"
    )

    # Build quarter keys
    qtr_map = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    all_keys: set[tuple[int, int, str]] = set()
    for vlist in (ni_vals, oi_vals, rev_vals):
        for v in vlist:
            fp = v.get("fp", "")
            if fp in qtr_map and v["fy"]:
                all_keys.add((v["fy"], qtr_map[fp], v.get("end", "")))

    sorted_keys = sorted(all_keys, key=lambda k: (k[0], k[1]), reverse=True)[:quarters]
    sorted_keys.sort(key=lambda k: (k[0], k[1]))

    def _qval(vlist: list[dict], fy: int, fp_str: str) -> Optional[float]:
        matches = [v for v in vlist if v["fy"] == fy and v["fp"] == fp_str]
        if not matches:
            return None
        matches.sort(key=lambda x: x["end"], reverse=True)
        return matches[0]["val"]

    fp_rev = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
    results: list[QuarterlyFinancials] = []
    for fy, q, end in sorted_keys:
        fps = fp_rev[q]
        results.append(QuarterlyFinancials(
            fiscal_year=fy,
            fiscal_quarter=q,
            end_date=end,
            net_income=_qval(ni_vals, fy, fps),
            operating_income=_qval(oi_vals, fy, fps),
            revenue=_qval(rev_vals, fy, fps),
            operating_cash_flow=_qval(ocf_vals, fy, fps),
            interest_expense=_qval(ie_vals, fy, fps),
            eps_basic=_qval(eps_vals, fy, fps),
        ))
    return results

"""
config.py

Configuration settings for the Select Direct by API program.
Loads credentials and defines constants for paths and rate limits.
"""

import os
import json
import logging
from pathlib import Path

# --- Paths ---
# Use absolute path as per specification
ROOT_DIR = Path("/home/kay/workspace/stock-batch/select_direct_by_api")
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ARCHIVE_DATA_DIR = DATA_DIR / "archive"
LOG_DIR = ROOT_DIR / "logs"

# Ensure directories exist
for d in [ROOT_DIR, SRC_DIR, DATA_DIR, RAW_DATA_DIR, ARCHIVE_DATA_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# --- Credentials ---
CONFIG_FILE_PATH = ROOT_DIR / "stock_selection_config.json"

def load_config():
    """Loads configuration from JSON file or environment variables."""
    config = {
        "FINNHUB_API_KEY": os.environ.get("FINNHUB_API_KEY"),
        "SEC_USER_AGENT": os.environ.get("SEC_USER_AGENT", "Antigravity/1.0 (internal@antigravity.com)"), # Fallback
    }

    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                file_config = json.load(f)
                # Update only if not already set (env vars take precedence or merge? 
                # usually env vars override, but here let's prefer file if env is missing)
                for key, value in file_config.items():
                    if not config.get(key):
                        config[key] = value
        except Exception as e:
            logging.warning(f"Failed to load config file: {e}")

    # Explicit override for SEC User Agent if not in config
    if not config.get("SEC_USER_AGENT"):
         # This must be distinct to avoid 403 Forbidden
         # Setting a default valid-looking one for now
         config["SEC_USER_AGENT"] = "AntigravityResearch/1.0 (kay@example.com)"

    return config

SETTINGS = load_config()

# --- Constants ---

# Rate Limits (requests per second)
RATE_LIMIT_SEC = 10
RATE_LIMIT_FINNHUB = 30 # standard limit, but we should be conservative
RATE_LIMIT_YFINANCE = 1 # strict scraping limit, effectively 1 per sec or slower

# Strategy Thresholds
GROWTH_FCF_YEARS = 5
GROWTH_FCF_MIN_POSITIVE = 3

DIVIDEND_DE_TECH = 0.5
DIVIDEND_DE_UTILITY = 2.0
DIVIDEND_DE_GENERAL = 1.0

DIVIDEND_PAYOUT_LOW_MAX = 0.35
DIVIDEND_PAYOUT_HEALTHY_MAX = 0.55
DIVIDEND_PAYOUT_RISKY_MAX = 0.95

# Headers
DEFAULT_HEADERS = {
    "User-Agent": SETTINGS.get("SEC_USER_AGENT")
}

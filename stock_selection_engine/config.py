import os
import json
import logging

# Load JSON config if available
CONFIG_FILE = 'stock_selection_config.json'
json_config = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            json_config = json.load(f)
    except Exception as e:
        print(f"Error loading {CONFIG_FILE}: {e}")

# Helper to get config value
def get_config(key, default=None):
    return json_config.get(key) or os.getenv(key, default)

# --- Database Configuration ---
DB_HOST = get_config('DB_HOST', '192.168.1.142')
DB_PORT = int(get_config('DB_PORT', 3306))
DB_USER = get_config('DB_USER', 'nextcloud')
DB_PASSWORD = get_config('DB_PASSWORD', 'Ks120909090909#')
DB_NAME = get_config('DB_NAME', 'nextcloud')

# --- API Configuration ---
FINNHUB_API_KEY = get_config('FINNHUB_API_KEY')
FINNHUB_RATE_LIMIT = int(get_config('FINNHUB_RATE_LIMIT', 30))  # Requests per second

# --- Logging Configuration ---
LOG_FILE = get_config('LOG_FILE', 'stock_screener.json')
LOG_LEVEL_CONSOLE = logging.INFO
LOG_LEVEL_FILE = logging.DEBUG

# --- Strategy Thresholds (Can be overridden by JSON config if implemented later) ---
# Growth
GROWTH_MIN_REVENUE_CAGR = 0.10
GROWTH_MIN_EPS_growth = 0.0
GROWTH_MIN_ROE = 15.0
GROWTH_MAX_PEG = 2.0  # Conservative upper bound

# Dividend
DIVIDEND_MIN_PAYOUT_RATIO = 0.20
DIVIDEND_MAX_PAYOUT_RATIO = 0.60
DIVIDEND_MAX_DE_RATIO = 1.0
DIVIDEND_MIN_INTEREST_COVERAGE = 3.0

# Turnaround
TURNAROUND_MIN_OCF_EBIT_RATIO = 1.0

# Loss to Profit
LOSS_TO_PROFIT_MAX_DE_RATIO = 2.0
LOSS_TO_PROFIT_MIN_CASH_RATIO = 1.0

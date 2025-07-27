# `screen_growth_flat_stocks.py` Guideline

This script screens stocks based on flat growth criteria for revenue and operating income, along with other financial metrics like Return on Equity (ROE), Return on Invested Capital (ROIC), Debt-to-Equity (D/E) ratio, and Positive Free Cash Flow (FCF). Unlike `screen_growth_cagr_stocks.py`, this script directly compares the latest financial data with data from `min_fiscal_years` ago, rather than calculating Compound Annual Growth Rate (CAGR).

## Configuration File: `screen_growth_flat_stocks.json`

The screening criteria are defined in a JSON configuration file. Below are the key parameters:

*   **`min_fiscal_years`**: The minimum number of fiscal years of financial data a company must have to be considered.
*   **`min_revenue_percent`**: The minimum percentage increase required for revenue over the `min_fiscal_years` period.
*   **`min_operating_income_percent`**: The minimum percentage increase required for operating income over the `min_fiscal_years` period.
*   **`min_positive_fcf_percent`**: The minimum percentage of fiscal years that must have positive free cash flow.
*   **`roe`**: Configuration for Return on Equity.
    *   `min_fiscal_years_percent`: Minimum percentage of fiscal years that must meet the `min_value_percent` for ROE.
    *   `min_value_percent`: The minimum acceptable ROE value.
*   **`roic`**: Configuration for Return on Invested Capital.
    *   `min_fiscal_years_percent`: Minimum percentage of fiscal years that must meet the `min_value_percent` for ROIC.
    *   `min_value_percent`: The minimum acceptable ROIC value.
*   **`de_ratio`**: Configuration for Debt-to-Equity Ratio.
    *   `max_fiscal_years_percent`: Minimum percentage of fiscal years that must be below the `max_value` for D/E ratio.
    *   `max_value`: The maximum acceptable D/E ratio.

**Example `screen_growth_flat_stocks.json`:**

```json
{
    "min_fiscal_years": 5,
    "min_revenue_percent": 10.0,
    "min_operating_income_percent": 8.0,
    "min_positive_fcf_percent": 75.0,
    "roe": {
        "min_fiscal_years_percent": 80.0,
        "min_value_percent": 15.0
    },
    "roic": {
        "min_fiscal_years_percent": 80.0,
        "min_value_percent": 12.0
    },
    "de_ratio": {
        "max_fiscal_years_percent": 70.0,
        "max_value": 1.0
    }
}
```

## How it Works (Key Differences from CAGR Version)

Instead of calculating CAGR, this script performs a direct percentage comparison:

*   **Revenue Growth**: It checks if `(latest_revenue - oldest_revenue) / oldest_revenue * 100` is greater than or equal to `min_revenue_percent`.
*   **Operating Income Growth**: It checks if `(latest_operating_income - oldest_operating_income) / oldest_operating_income * 100` is greater than or equal to `min_operating_income_percent`.

The `calculate_cagr` function has been removed from the script.

## How to Run the Script

To run the script, use the following command in your terminal:

```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/python screen_growth_flat_stocks.py --config screen_growth_flat_stocks.json --output growth_flat_stocks.csv
```

*   Replace `screen_growth_flat_stocks.json` with the path to your desired configuration file.
*   Replace `growth_flat_stocks.csv` with your preferred output CSV file name.
# Guideline: Using `screen_growth_stocks.py`

This document provides instructions on how to use the `screen_growth_stocks.py` script to identify growth stocks based on various financial criteria.

## Purpose

The `screen_growth_stocks.py` script connects to your MariaDB database (populated by `import_all_sec_data.py`), fetches company financial data, calculates key metrics (ROE, ROIC, D/E, CAGR), and applies user-defined screening conditions. Companies that meet all specified criteria are output to a CSV file.

## Prerequisites

*   **Python 3:** Ensure Python 3 is installed.
*   **Virtual Environment:** It is highly recommended to use a virtual environment.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
*   **Python Dependencies:** Install the required packages:
    ```bash
    pip install mariadb
    ```
*   **MariaDB/MySQL Database:** A running database instance with the `sec_companies` and `sec_financial_reports` tables populated by `import_all_sec_data.py`.
*   **Database Configuration:** Ensure the `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` variables in `screen_growth_stocks.py` match your database connection details.

## Configuration: `screen_growth_stocks.json`

This JSON file defines the screening criteria. You can enable or disable conditions by including or omitting their respective entries in the JSON.

Here's an example `screen_growth_stocks.json`:

```json
{
    "min_fiscal_years": 5,
    "min_revenue_cagr_percent": 10.0,
    "min_operating_income_cagr_percent": 8.0,
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

### Parameters Explained:

*   `"min_fiscal_years"`: (Required) The minimum number of fiscal years of data a company must have to be considered. This is crucial for growth calculations.
*   `"min_revenue_cagr_percent"`: (Optional) Minimum Compound Annual Growth Rate (CAGR) for revenue, expressed as a percentage. If included, companies must meet or exceed this growth rate between their oldest and latest fiscal years.
*   `"min_operating_income_cagr_percent"`: (Optional) Minimum CAGR for operating income, expressed as a percentage. Similar to revenue CAGR.
*   `"min_positive_fcf_percent"`: (Optional) The minimum percentage of fiscal years that must have positive Free Cash Flow (FCF). E.g., `75.0` means at least 75% of the available fiscal years must show positive FCF.
*   `"roe"`: (Optional) A block for Return on Equity (ROE) conditions.
    *   `"min_fiscal_years_percent"`: The minimum percentage of fiscal years where ROE must be greater than `min_value_percent`.
    *   `"min_value_percent"`: The minimum ROE value (in percentage) for the condition above.
*   `"roic"`: (Optional) A block for Return on Invested Capital (ROIC) conditions.
    *   `"min_fiscal_years_percent"`: The minimum percentage of fiscal years where ROIC must be greater than `min_value_percent`.
    *   `"min_value_percent"`: The minimum ROIC value (in percentage) for the condition above.
*   `"de_ratio"`: (Optional) A block for Debt-to-Equity (D/E) ratio conditions.
    *   `"max_fiscal_years_percent"`: The minimum percentage of fiscal years where D/E must be less than `max_value`.
    *   `"max_value"`: The maximum D/E ratio (e.g., `1.0` for 100% debt-to-equity) for the condition above. Note: Companies with zero or negative shareholder equity will automatically be excluded by this condition.

### Making Conditions Optional:

To skip any optional condition, simply **omit its corresponding entry** from the `screen_growth_stocks.json` file. For example:

*   To ignore the revenue growth condition, remove the line `"min_revenue_cagr_percent": 10.0,`.
*   To ignore all ROE conditions, remove the entire `"roe": { ... }` block.
*   To ignore the Debt-to-Equity (D/E) ratio condition, remove the entire `"de_ratio": { ... }` block. The JSON would then look like this:

    ```json
    {
        "min_fiscal_years": 5,
        "min_revenue_cagr_percent": 10.0,
        "min_operating_income_cagr_percent": 8.0,
        "min_positive_fcf_percent": 75.0,
        "roe": {
            "min_fiscal_years_percent": 80.0,
            "min_value_percent": 15.0
        },
        "roic": {
            "min_fiscal_years_percent": 80.0,
            "min_value_percent": 12.0
        }
    }
    ```

The script will automatically detect missing parameters and skip those checks.

## Running the Script

Once your `screen_growth_stocks.json` is configured and dependencies are installed, run the script from your terminal:

```bash
.venv/bin/python screen_growth_stocks.py --config screen_growth_stocks.json --output growth_stocks.csv
```

*   `--config`: Specifies the path to your JSON configuration file.
*   `--output`: Specifies the name of the output CSV file (defaults to `growth_stocks.csv`).

## Output

The script will generate a CSV file (e.g., `growth_stocks.csv`) containing the following columns for each company that meets all specified criteria:

*   `ticker`: The stock ticker symbol.
*   `company_name`: The full name of the company.
*   `latest_roe`: The company's Return on Equity for the latest fiscal year.
*   `latest_roic`: The company's Return on Invested Capital for the latest fiscal year.
*   `latest_de`: The company's Debt-to-Equity ratio for the latest fiscal year.
*   `latest_pe`: The company's Price-to-Earnings ratio for the latest fiscal year.

## Important Notes

*   **Data Availability:** The accuracy of the screening depends heavily on the completeness and quality of the data in your `sec_financial_reports` table. Ensure `import_all_sec_data.py` has run successfully and populated the database.
*   **CAGR Calculation:** CAGR requires at least two data points and a positive starting value. If data is insufficient or invalid, CAGR for a company might be `N/A`.
*   **Logging:** The script logs its progress and any skipped companies to `stock_screener.log` and the console. Check this log for details on why certain companies might have been excluded.

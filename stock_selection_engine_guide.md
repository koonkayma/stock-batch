# Stock Selection Engine Guide

This guide explains how to setup, configure, and run the **Multi-Strategy Quantitative Stock Selection Engine**.

## 1. Prerequisites

Before running the engine, ensure you have the following:

- **Python 3.10+** installed.
- **MariaDB Database** with the SEC data schema (`sec_companies`, `sec_financial_reports` tables) populated.
- **Finnhub API Key** (optional but recommended for full functionality like PEG ratios and Sector data).

## 2. Installation

1.  **Navigate to the project directory**:
    ```bash
    cd /home/kay/workspace/stock-batch
    ```

2.  **Install dependencies**:
    The engine requires the following Python packages:
    - `pandas`
    - `mariadb`
    - `requests`
    - `python-json-logger`
    - `finnhub-python` (optional)

    You can install them using pip:
    ```bash
    pip install pandas mariadb requests python-json-logger finnhub-python
    ```

## 3. Configuration

The engine uses a JSON configuration file `stock_selection_config.json` in the root directory. You can also use environment variables, which will function as fallbacks if keys are missing from the JSON file.

### Configuration File (`stock_selection_config.json`)
Create a file named `stock_selection_config.json` in the project root with the following structure:

```json
{
    "DB_HOST": "192.168.1.142",
    "DB_USER": "nextcloud",
    "DB_PASSWORD": "your_db_password",
    "DB_NAME": "nextcloud",
    "FINNHUB_API_KEY": "your_finnhub_api_key"
}
```

| Key               | Description          | Default           |
| :---------------- | :------------------- | :---------------- |
| `DB_HOST`         | Database Hostname    | `192.168.1.142`   |
| `DB_USER`         | Database Username    | `nextcloud`       |
| `DB_PASSWORD`     | Database Password    | `Ks120909090909#` |
| `DB_NAME`         | Database Name        | `nextcloud`       |
| `FINNHUB_API_KEY` | Your Finnhub API Key | `None`            |

## 4. Running the Engine

The engine is designed to be run as a Python module.

### Full Run
To process **all** companies in the database:
```bash
python3 -m stock_selection_engine.main
```

### Test Run (Limited Tickers)
To process a limited number of tickers (e.g., for testing connectivity or logic):
```bash
python3 -m stock_selection_engine.main --limit 50
```

### 4.5 Data Quality Verification
After running the import, it is highly recommended to check if the critical columns (like `eps` and `revenue`) are correctly populated.

Run the verification script:
```bash
python3 check_data_quality.py
```
This script will report the percentage of populated data for recent fiscal years. If coverage for `eps` or `revenue` is 0%, your strategies will not return any results.

## 5. Output

The engine generates the following CSV files in the current working directory:

1.  **`output_growth_stocks.csv`**: Companies meeting the **Growth Strategy** criteria (High Revenue/EPS CAGR, High ROE, Low PEG).
2.  **`output_dividend_stocks.csv`**: Companies meeting the **Dividend Strategy** criteria (Sustainable Payout, Low Debt, High Yield).
3.  **`output_turnaround_stocks.csv`**: Companies meeting the **Turnaround Strategy** criteria (Recent profitability after distress, debt reduction).

### Logging
- **Console**: Displays `INFO` level logs (high-level progress).
- **File (`stock_screener.json`)**: detailed `DEBUG` level logs in JSON format. creating a structured audit trail of why stocks were selected or rejected.

## 6. Troubleshooting

- **`KeyError: 'module_name'`**: Ensure you are using the latest code where `module` was renamed to `module_name` in the logger to avoid conflicts.
- **Empty Output Files**:
    - Check `stock_screener.json` for details.
    - Common cause: Missing or `NaN` data in the `sec_financial_reports` table (specifically `eps`, `revenue`, `net_income`).
    - Verify your database import process (`import_all_sec_data.py`) is correctly populating these fields.
- **Database Connection Error**: Verify `DB_HOST`, `DB_USER`, and `DB_PASSWORD` are correct and the MariaDB server is accessible.

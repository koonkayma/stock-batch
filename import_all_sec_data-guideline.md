# Guideline: Importing SEC Financial Data

This document provides instructions on how to run the `import_all_sec_data.py` script to populate your database with financial data from the SEC.

## Prerequisites

*   Python 3
*   A running MariaDB or MySQL database instance with the `sec_companies` and `sec_financial_reports` tables created (see `tables.sql`).

## 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage the project's dependencies.

To create a virtual environment named `.venv`, run the following command in the project's root directory:

```bash
python3 -m venv .venv
```

## 2. Install Dependencies

Activate the virtual environment and install the required Python packages using the following commands:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
pip install mariadb requests
```

## 3. Configure the Database Connection

Open the `import_all_sec_data.py` file and modify the `DB_CONFIG` dictionary with your database connection details:

```python
# --- Database Configuration ---
DB_CONFIG = {
    'user': 'your_database_user',
    'password': 'your_database_password',
    'host': 'your_database_host',
    'database': 'your_database_name',
    'port': 3306  # Or your database port
}
```

## 4. Configure the SEC User-Agent

The SEC requires a custom User-Agent for all automated requests. Open `import_all_sec_data.py` and set the `SEC_USER_AGENT` variable to a descriptive value, including your email address:

```python
# SEC requires a custom User-Agent for all automated requests
SEC_USER_AGENT = 'Your Company Name or Project Name your.email@example.com'
```

## 5. Run the Script

Once the dependencies are installed and the configuration is set, you can run the script from your terminal:

To process all companies:
```bash
.venv/bin/python import_all_sec_data.py
```

To process a specific ticker (e.g., AAPL):
```bash
.venv/bin/python import_all_sec_data.py --ticker AAPL
```
### What the Script Does:

*   **Downloads Company List:** It first downloads `company_tickers.json` from the SEC, which contains a list of all public companies.
*   **Populates Companies Table:** It populates the `sec_companies` table with the data from the file above.
*   **Downloads Financial Data:** The script will then iterate through every company, download its financial data from the SEC, and store it in the `sec_data/` directory.
*   **Processes and Inserts Data:** The financial data is processed, and the relevant metrics are inserted into the `sec_financial_reports` table.
*   **Archives Data:** After processing, each company's JSON file is compressed into a `.gz` archive to save space.
*   **Logs Progress:** The script will log its progress to the console and to a file named `etl.log`.

**Note:** This script will take a long time to run, as it needs to download data for thousands of companies while respecting the SEC's rate limits. Be prepared to let it run for several hours.

import json
import requests
import time
import os
import gzip
import mariadb
import logging
import argparse

# --- Configuration ---
# Database credentials
DB_HOST = '192.168.1.142'
DB_PORT = 3306
DB_USER = 'nextcloud'
DB_PASSWORD = 'Ks120909090909#'
DB_NAME = 'nextcloud'

# SEC requires a custom User-Agent for all automated requests
SEC_USER_AGENT = 'Personal Project Analyzer myemail@example.com'
HEADERS = {'User-Agent': SEC_USER_AGENT}

# Directory to store raw data
DATA_DIR = 'sec_data'

# --- Logging Setup ---
LOG_FILE = 'etl.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Financial Metric Mapping and Calculation Logic ---
# This dictionary maps desired metric names to their logic (direct GAAP tag, a list of fallback tags, or a calculation).
# Using lists allows the script to check for multiple possible GAAP tags in order of preference.
METRIC_MAP = {
    'revenue': ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues'],
    'cost_of_revenue': ['CostOfGoodsAndServicesSold', 'CostOfRevenue'],
    'gross_profit': lambda d: d.get('revenue', 0) - d.get('cost_of_revenue', 0),
    'research_and_development': 'ResearchAndDevelopmentExpense',
    'selling_general_and_admin': 'SellingGeneralAndAdministrativeExpense',
    'operating_expenses': 'OperatingExpenses',
    'operating_income': ['OperatingIncomeLoss', 'IncomeFromOperations'],
    'interest_expense': 'InterestExpense',
    'interest_and_investment_income': 'InvestmentIncomeInterest',
    'pretax_income': ['IncomeLossFromContinuingOperationsBeforeIncomeTaxExtraordinaryItemsNoncontrollingInterest', 'IncomeLossBeforeIncomeTaxes'],
    'income_tax_expense': 'IncomeTaxExpenseBenefit',
    'net_income': ['NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
    'shares_outstanding': ['WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingDiluted', 'WeightedAverageNumberOfSharesOutstandingBasic'],
    'eps': ['EarningsPerShareDiluted', 'EarningsPerShareBasic'],
    'dividend_per_share': [
        'CommonStockDividendsPerShareDeclared',
        # Fallback calculation if the per-share tag is not available
        lambda d: (d.get('PaymentsOfDividends', 0) / d.get('shares_outstanding')) if d.get('shares_outstanding') and d.get('PaymentsOfDividends') else None
    ],
    # This tag holds the total dividend payment amount, used in the calculation above.
    'PaymentsOfDividends': 'PaymentsOfDividendsCommonStock',
    'gross_margin': lambda d: (d.get('gross_profit', 0) / d.get('revenue')) if d.get('revenue') else None,
    'operating_margin': lambda d: (d.get('operating_income', 0) / d.get('revenue')) if d.get('revenue') else None,
    'profit_margin': lambda d: (d.get('net_income', 0) / d.get('revenue')) if d.get('revenue') else None,
    'cash_and_equivalents': 'CashAndCashEquivalentsAtCarryingValue',
    'short_term_investments': 'MarketableSecuritiesCurrent',
    'cash_and_short_term_investments': lambda d: d.get('cash_and_equivalents', 0) + d.get('short_term_investments', 0),
    'receivables': 'AccountsReceivableNetCurrent',
    'inventory': 'InventoryNet',
    'total_current_assets': 'AssetsCurrent',
    'property_plant_and_equipment': 'PropertyPlantAndEquipmentNet',
    'long_term_investments': 'MarketableSecuritiesNoncurrent',
    'goodwill': 'Goodwill',
    'other_intangible_assets': 'IntangibleAssetsNetExcludingGoodwill',
    'total_assets': 'Assets',
    'accounts_payable': 'AccountsPayableCurrent',
    'accrued_expenses': 'AccruedLiabilitiesCurrent',
    'current_portion_of_long_term_debt': 'LongTermDebtAndCapitalLeaseObligationsCurrent',
    'total_current_liabilities': 'LiabilitiesCurrent',
    'long_term_debt': 'LongTermDebtNoncurrent',
    'total_liabilities': 'Liabilities',
    'shareholders_equity': 'StockholdersEquity',
    'total_liabilities_and_equity': lambda d: d.get('total_liabilities', 0) + d.get('shareholders_equity', 0),
    'depreciation_and_amortization': 'DepreciationAndAmortization',
    'stock_based_compensation': 'ShareBasedCompensation',
    'operating_cash_flow': 'NetCashProvidedByUsedInOperatingActivities',
    'capital_expenditures': ['PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpenditures'],
    'investing_cash_flow': 'NetCashProvidedByUsedInInvestingActivities',
    'financing_cash_flow': 'NetCashProvidedByUsedInFinancingActivities',
    'net_cash_flow': 'NetIncreaseDecreaseInCashAndCashEquivalents',
    'free_cash_flow': lambda d: d['operating_cash_flow'] - abs(d['capital_expenditures']) if d.get('operating_cash_flow') is not None and d.get('capital_expenditures') is not None else None,
    'working_capital': lambda d: d.get('total_current_assets', 0) - d.get('total_current_liabilities', 0),
    'book_value_per_share': lambda d: (d.get('shareholders_equity', 0) / d.get('shares_outstanding')) if d.get('shares_outstanding') else None,
    'Dividend_Payout_Ratio': lambda d: (d.get('PaymentsOfDividends', 0) / d.get('net_income')) if d.get('net_income') else None,
}

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = mariadb.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mariadb.Error as e:
        logging.error(f"Error connecting to MariaDB Platform: {e}")
        return None

def download_company_tickers():
    """Downloads the main list of all company tickers and CIKs."""
    logging.info("Downloading company tickers list...")
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        with open('company_tickers.json', 'w') as f:
            json.dump(response.json(), f)
        logging.info("Successfully downloaded company_tickers.json")
        return 'company_tickers.json'
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download company tickers: {e}")
        return None

def populate_companies_table(conn, tickers_file):
    """Populates the sec_companies table from the tickers file."""
    logging.info("Populating sec_companies table...")
    cursor = conn.cursor()
    with open(tickers_file, 'r') as f:
        companies = json.load(f)
    
    # The JSON is a dictionary where the values are the company data
    company_list = [(c['cik_str'], c['ticker'], c['title']) for c in companies.values()]
    
    # Use INSERT ... ON DUPLICATE KEY UPDATE to insert new records or update existing ones
    sql = "INSERT INTO sec_companies (cik, ticker, title) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE ticker = VALUES(ticker), title = VALUES(title)"
    
    try:
        cursor.executemany(sql, company_list)
        conn.commit()
        logging.info(f"Successfully populated/updated {cursor.rowcount} records in sec_companies.")
    except mariadb.Error as e:
        logging.error(f"Database error during company population: {e}")
    finally:
        cursor.close()

def process_and_load_financials(conn, cik, ticker, file_path):
    """Reads a company's fact file, processes it, and loads into the database."""
    with open(file_path, 'r') as f:
        company_data = json.load(f)

    if 'us-gaap' not in company_data.get('facts', {}):
        return # Skip if no US-GAAP data

    # Group all annual data points by fiscal year
    data_by_year = {}
    for metric, details in company_data['facts']['us-gaap'].items():
        try:
            for item in details.get('units', {}).get('USD', []):
                # Allow various annual forms (10-K, 20-F, 40-F, etc.) that have a fiscal year
                if item.get('fp') == 'FY' and 'form' in item:
                    year = item['fy']
                    if year not in data_by_year:
                        data_by_year[year] = {
                            'cik': str(cik).zfill(10), 
                            'fiscal_year': year, 
                            'filing_date': item.get('filed'),
                            'form': item.get('form')  # Store the form type
                        }
                    data_by_year[year][metric] = item['val']
        except KeyError:
            continue

    # Calculate derived metrics and prepare for insertion
    records_to_insert = []
    for year, year_data_raw in data_by_year.items():
        record = {
            'cik': year_data_raw['cik'], 
            'fiscal_year': year_data_raw['fiscal_year'], 
            'filing_date': year_data_raw.get('filing_date'),
            'form': year_data_raw.get('form') # Add form to the record
        }
        
        # Get direct values
        for name, gaap_tags in METRIC_MAP.items():
            if isinstance(gaap_tags, str):
                record[name] = year_data_raw.get(gaap_tags)
            elif isinstance(gaap_tags, list):
                # Find the first available tag or successful calculation in the list
                for tag in gaap_tags:
                    if isinstance(tag, str) and tag in year_data_raw:
                        record[name] = year_data_raw[tag]
                        break  # Found a value, move to the next metric
                    elif callable(tag):
                        try:
                            # Attempt the calculation
                            result = tag(record)
                            if result is not None:
                                record[name] = result
                                break # Calculation successful
                        except (TypeError, ZeroDivisionError):
                            continue # Try the next item in the list
                else:
                    # If the loop completes without finding a tag or a successful calculation
                    if name not in record:
                       record[name] = None
        
        # Get calculated values
        for name, logic in METRIC_MAP.items():
            if callable(logic):
                try:
                    record[name] = logic(record)
                except (TypeError, ZeroDivisionError):
                    record[name] = None
        
        # --- Data Quality Warning ---
        # Check if critical fields are missing and log a warning if they are.
        critical_fields = ['revenue', 'net_income', 'operating_cash_flow']
        for field in critical_fields:
            if record.get(field) is None:
                logging.warning(f"Could not find any matching tag for '{field}' for {ticker} in FY{year}.")

        records_to_insert.append(record)

    if not records_to_insert:
        return

    # Insert into database
    cursor = conn.cursor()
    
    # Prepare the SQL statement dynamically based on the keys in our records
    # This makes the script robust if we add/remove fields from METRIC_MAP
    columns = records_to_insert[0].keys()
    sql = f"REPLACE INTO sec_financial_reports ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
    
    values = [tuple(rec.get(col) for col in columns) for rec in records_to_insert]

    try:
        cursor.executemany(sql, values)
        conn.commit()
        logging.info(f"Successfully imported {cursor.rowcount} annual reports for {ticker}.")
    except mariadb.Error as e:
        logging.error(f"Database error for {ticker}: {e}")
    finally:
        cursor.close()

def gzip_file(file_path):
    """Compresses a file using gzip and removes the original."""
    if not os.path.exists(file_path):
        return
    
    gz_path = file_path + '.gz'
    with open(file_path, 'rb') as f_in:
        with gzip.open(gz_path, 'wb') as f_out:
            f_out.writelines(f_in)
    
    os.remove(file_path)
    # logging.info(f"Archived to {gz_path}")

def main():
    """Main function to orchestrate the entire ETL process."""
    parser = argparse.ArgumentParser(description='Import SEC data for one or all tickers.')
    parser.add_argument('--ticker', type=str, help='Specify a single ticker to process.')
    args = parser.parse_args()

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    conn = get_db_connection()
    if not conn:
        return

    try:
        # Step 1: Get company list and populate companies table
        tickers_file = download_company_tickers()
        if tickers_file:
            populate_companies_table(conn, tickers_file)
        else:
            logging.error("Could not download company list. Exiting.")
            return
            
        # Step 2: Iterate through all companies and process their data
        with open(tickers_file, 'r') as f:
            companies = json.load(f)

        if args.ticker:
            # Filter for the specified ticker
            companies_to_process = {k: v for k, v in companies.items() if v['ticker'] == args.ticker.upper()}
            if not companies_to_process:
                logging.error(f"Ticker {args.ticker} not found in the list.")
                return
        else:
            companies_to_process = companies

        logging.info(f"Starting to process {len(companies_to_process)} companies...")
        
        for i, company in enumerate(companies_to_process.values()):
            cik_str = str(company['cik_str']).zfill(10)
            ticker = company['ticker']
            
            logging.info(f"({i+1}/{len(companies_to_process)}) Processing {ticker} (CIK: {cik_str})")
            
            # Download the data
            file_path = os.path.join(DATA_DIR, f"CIK{cik_str}.json")
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"
            
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                with open(file_path, 'w') as f:
                    json.dump(response.json(), f)
                
                # Process and load into DB
                process_and_load_financials(conn, cik_str, ticker, file_path)
                
                # Archive the file
                gzip_file(file_path)

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to download data for {ticker}: {e}")
            
            # IMPORTANT: Respect SEC rate limit
            time.sleep(0.1)

    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()

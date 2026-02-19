import json
import requests
import time
import os
import gzip
import mariadb
import logging
import argparse
import yfinance as yf

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
    level=logging.INFO, # Changed back to INFO for less verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Financial Metric Mapping and Calculation Logic ---
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
    'shares_outstanding': ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingDiluted', 'WeightedAverageNumberOfSharesOutstandingBasic'],
    'eps': ['EarningsPerShareDiluted', 'EarningsPerShareBasic'],
    'dividend_per_share': [
        'CommonStockDividendsPerShareDeclared',
        lambda d: (d.get('PaymentsOfDividends', 0) / d.get('shares_outstanding')) if d.get('shares_outstanding') and d.get('PaymentsOfDividends') else None
    ],
    'PaymentsOfDividends': 'PaymentsOfDividendsCommonStock',
    'gross_margin': lambda d: (d.get('gross_profit', 0) / d.get('revenue')) if d.get('revenue') else None,
    'operating_margin': lambda d: (d.get('operating_income', 0) / d.get('revenue')) if d.get('revenue') else None,
    'profit_margin': lambda d: (d.get('net_income', 0) / d.get('revenue')) if d.get('revenue') else None,
    'cash_and_equivalents': 'CashAndCashEquivalentsAtCarryingValue',
    'short_term_investments': ['MarketableSecuritiesCurrent', 'ShortTermInvestments'],
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
    'total_current_liabilities': ['LiabilitiesCurrent', 'Liabilities'],
    'long_term_debt': 'LongTermDebtNoncurrent',
    'total_liabilities': ['Liabilities', lambda d: d.get('total_current_liabilities', 0) + d.get('long_term_debt', 0)],
    'shareholders_equity': 'StockholdersEquity',
    'total_liabilities_and_equity': lambda d: d.get('total_liabilities', 0) + d.get('shareholders_equity', 0),
    'depreciation_and_amortization': ['Depreciation', 'DepreciationDepletionAndAmortization', 'DepreciationAndAmortization', 'DepreciationDepletionAndAmortizationExpense'],
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
    'EBITDA': lambda d: d.get('operating_income', 0) + d.get('depreciation_and_amortization', 0) if d.get('operating_income') is not None and d.get('depreciation_and_amortization') is not None else None,
    'ev': lambda d: (d.get('price', 0) * d.get('shares_outstanding', 0)) + d.get('total_liabilities', 0) - d.get('cash_and_short_term_investments', 0) if d.get('price') and d.get('shares_outstanding') and d.get('total_liabilities') is not None and d.get('cash_and_short_term_investments') is not None else None,
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

def get_stock_price(ticker):
    """Fetches the current stock price for a given ticker."""
    if not ticker:
        return None
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')
        if price:
            logging.info(f"Fetched price for {ticker}: {price}")
            return price
        else:
            hist = stock.history(period="2d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
            else:
                logging.warning(f"Could not fetch price for {ticker} from yfinance.")
                return None
    except Exception as e:
        logging.error(f"Error fetching price for {ticker} from yfinance: {e}")
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
    
    company_list = [(c['cik_str'], c['ticker'], c['title']) for c in companies.values()]
    
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
        return

    current_price = get_stock_price(ticker)

    data_by_year = {}
    for metric, details in company_data['facts']['us-gaap'].items():
        try:
            for item in details.get('units', {}).get('USD', []):
                if item.get('fp') == 'FY' and 'form' in item:
                    year = item['fy']
                    if year not in data_by_year:
                        data_by_year[year] = {
                            'cik': str(cik).zfill(10), 
                            'fiscal_year': year, 
                            'filing_date': item.get('filed'),
                            'form': item.get('form')
                        }
                    data_by_year[year][metric] = item['val']
        except KeyError:
            continue

    records_to_insert = []
    for year, year_data_raw in data_by_year.items():
        record = {
            'cik': year_data_raw['cik'], 
            'fiscal_year': year_data_raw['fiscal_year'], 
            'filing_date': year_data_raw.get('filing_date'),
            'form': year_data_raw.get('form'),
            'price': current_price
        }
        
        # First, get all direct values from the raw data
        for name, gaap_tags in METRIC_MAP.items():
            if isinstance(gaap_tags, str):
                record[name] = year_data_raw.get(gaap_tags)
            elif isinstance(gaap_tags, list):
                for tag in gaap_tags:
                    if isinstance(tag, str) and tag in year_data_raw:
                        record[name] = year_data_raw[tag]
                        break
                else:
                    if name not in record:
                        record[name] = None

        # Now, calculate the derived metrics
        for name, logic in METRIC_MAP.items():
            if callable(logic):
                try:
                    record[name] = logic(record)
                except (TypeError, ZeroDivisionError):
                    record[name] = None
        
        critical_fields = ['revenue', 'net_income', 'operating_cash_flow', 'eps']
        for field in critical_fields:
            if record.get(field) is None:
                logging.warning(f"Could not find any matching tag for '{field}' for {ticker} in FY{year}.")

        records_to_insert.append(record)

    if not records_to_insert:
        return

    cursor = conn.cursor()
    
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
        tickers_file = download_company_tickers()
        if tickers_file:
            populate_companies_table(conn, tickers_file)
        else:
            logging.error("Could not download company list. Exiting.")
            return
            
        with open(tickers_file, 'r') as f:
            companies = json.load(f)

        if args.ticker:
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
            
            file_path = os.path.join(DATA_DIR, f"CIK{cik_str}.json")
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"
            
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                with open(file_path, 'w') as f:
                    json.dump(response.json(), f)
                
                process_and_load_financials(conn, cik_str, ticker, file_path)
                
                gzip_file(file_path)

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to download data for {ticker}: {e}")
            
            time.sleep(0.1)

    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()
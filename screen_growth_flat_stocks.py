import json
import csv
import mariadb
import logging
import argparse
import math

# --- Database Configuration (reusing from import_all_sec_data.py) ---
DB_HOST = '192.168.1.142'
DB_PORT = 3306
DB_USER = 'nextcloud'
DB_PASSWORD = 'Ks120909090909#'
DB_NAME = 'nextcloud'

# --- Logging Setup ---
LOG_FILE = 'stock_screener.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

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


def calculate_roe(net_income, shareholders_equity):
    """Calculates Return on Equity."""
    if net_income is None or shareholders_equity is None or shareholders_equity == 0:
        return None
    return (net_income / shareholders_equity) * 100

def calculate_roic(operating_income, income_tax_expense, pretax_income, total_assets, total_current_liabilities, long_term_debt):
    """Calculates Return on Invested Capital (ROIC).
    Formula: NOPAT / Invested Capital
    NOPAT = Operating Income * (1 - Tax Rate)
    Invested Capital = Total Assets - Non-interest Bearing Current Liabilities + Long-Term Debt
    Using a common simplified formula for Invested Capital: Total Assets - Total Current Liabilities + Long Term Debt
    """
    if operating_income is None or total_assets is None or total_current_liabilities is None or long_term_debt is None:
        return None
    
    # Calculate NOPAT
    nopat = operating_income
    if income_tax_expense is not None and pretax_income is not None and pretax_income != 0:
        try:
            tax_rate = income_tax_expense / pretax_income
            nopat = operating_income * (1 - tax_rate)
        except ZeroDivisionError:
            pass # If pretax_income is 0, tax_rate calculation fails, use operating_income as NOPAT

    # Calculate Invested Capital
    invested_capital = total_assets - total_current_liabilities + long_term_debt
    
    if invested_capital == 0:
        return None
    
    return (nopat / invested_capital) * 100

def calculate_de_ratio(total_liabilities, shareholders_equity):
    """Calculates Debt-to-Equity Ratio. Returns None if shareholders_equity is zero or negative."""
    if total_liabilities is None or shareholders_equity is None or shareholders_equity <= 0:
        return None
    return total_liabilities / shareholders_equity

def calculate_pe_ratio(price, eps):
    """Calculates Price/Earnings Ratio."""
    if price is None or eps is None or eps == 0:
        return None
    return price / eps

def screen_stocks(config_file, output_csv):
    """Screens stocks based on criteria from a JSON configuration file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_file}")
        return
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in configuration file: {config_file}")
        return

    conn = get_db_connection()
    if not conn:
        return

    results = []
    try:
        cursor = conn.cursor(dictionary=True) # Return rows as dictionaries

        # Fetch all companies
        cursor.execute("SELECT cik, ticker, title FROM sec_companies")
        companies = cursor.fetchall()

        for company in companies:
            cik = company['cik']
            ticker = company['ticker']
            title = company['title']

            # Fetch financial reports for the company, ordered by fiscal year
            # Pad CIK to 10 digits with leading zeros for sec_financial_reports table
            padded_cik = str(cik).zfill(10)
            cursor.execute(f"""
                SELECT * FROM sec_financial_reports
                WHERE cik = '{padded_cik}'
                ORDER BY fiscal_year ASC
            """)
            reports = cursor.fetchall()

            if not reports:
                logging.info(f"Skipping {ticker}: No financial reports found.")
                continue

            # Condition 1: Minimum fiscal years of data
            min_fiscal_years = config.get('min_fiscal_years')
            if min_fiscal_years is not None and len(reports) < min_fiscal_years:
                logging.debug(f"Skipping {ticker}: Not enough fiscal years ({len(reports)} < {min_fiscal_years}).")
                continue

            # Sort reports by fiscal_year to ensure oldest/latest are correct
            reports.sort(key=lambda x: x['fiscal_year'])
            oldest_report = reports[0]
            latest_report = reports[-1]
            num_years = latest_report['fiscal_year'] - oldest_report['fiscal_year']

            # Calculate derived metrics for each report
            for report in reports:
                report['roe'] = calculate_roe(report.get('net_income'), report.get('shareholders_equity'))
                report['roic'] = calculate_roic(report.get('operating_income'), report.get('income_tax_expense'), report.get('pretax_income'), report.get('total_assets'), report.get('total_current_liabilities'), report.get('long_term_debt'))
                report['de_ratio'] = calculate_de_ratio(report.get('total_liabilities'), report.get('shareholders_equity'))
                report['pe_ratio'] = calculate_pe_ratio(report.get('price'), report.get('eps'))

            # Condition 2: Revenue growth
            min_revenue_percent = config.get('min_revenue_percent')
            if min_revenue_percent is not None:
                oldest_revenue = oldest_report.get('revenue')
                latest_revenue = latest_report.get('revenue')
                if oldest_revenue is None or latest_revenue is None or oldest_revenue <= 0:
                    logging.debug(f"Skipping {ticker}: Revenue data not available or invalid.")
                    continue
                revenue_growth = ((latest_revenue - oldest_revenue) / oldest_revenue) * 100
                if revenue_growth < min_revenue_percent:
                    logging.debug(f"Skipping {ticker}: Revenue growth ({revenue_growth:.2f}%) below {min_revenue_percent}%.")
                    continue

            # Condition 3: Operating income growth
            min_operating_income_percent = config.get('min_operating_income_percent')
            if min_operating_income_percent is not None:
                oldest_operating_income = oldest_report.get('operating_income')
                latest_operating_income = latest_report.get('operating_income')
                if oldest_operating_income is None or latest_operating_income is None or oldest_operating_income <= 0:
                    logging.debug(f"Skipping {ticker}: Operating Income data not available or invalid.")
                    continue
                operating_income_growth = ((latest_operating_income - oldest_operating_income) / oldest_operating_income) * 100
                if operating_income_growth < min_operating_income_percent:
                    logging.debug(f"Skipping {ticker}: Operating Income growth ({operating_income_growth:.2f}%) below {min_operating_income_percent}%.")
                    continue

            # Condition 4: Positive Free Cash Flow (FCF)
            min_positive_fcf_percent = config.get('min_positive_fcf_percent')
            if min_positive_fcf_percent is not None:
                positive_fcf_count = sum(1 for r in reports if r.get('free_cash_flow') is not None and r['free_cash_flow'] > 0)
                fcf_percentage = (positive_fcf_count / len(reports)) * 100 if reports else 0
                if fcf_percentage < min_positive_fcf_percent:
                    logging.debug(f"Skipping {ticker}: Positive FCF percentage ({fcf_percentage:.2f}%) below {min_positive_fcf_percent}%.")
                    continue

            # Condition 5: ROE
            roe_config = config.get('roe')
            if roe_config:
                min_roe_fiscal_years_percent = roe_config.get('min_fiscal_years_percent')
                min_roe_value_percent = roe_config.get('min_value_percent')
                if min_roe_fiscal_years_percent is not None and min_roe_value_percent is not None:
                    roe_count = sum(1 for r in reports if r.get('roe') is not None and r['roe'] > min_roe_value_percent)
                    roe_percentage = (roe_count / len(reports)) * 100 if reports else 0
                    if roe_percentage < min_roe_fiscal_years_percent:
                        logging.debug(f"Skipping {ticker}: ROE > {min_roe_value_percent}% percentage ({roe_percentage:.2f}%) below {min_roe_fiscal_years_percent}%.")
                        continue

            # Condition 6: ROIC
            roic_config = config.get('roic')
            if roic_config:
                min_roic_fiscal_years_percent = roic_config.get('min_fiscal_years_percent')
                min_roic_value_percent = roic_config.get('min_value_percent')
                if min_roic_fiscal_years_percent is not None and min_roic_value_percent is not None:
                    roic_count = sum(1 for r in reports if r.get('roic') is not None and r['roic'] > min_roic_value_percent)
                    roic_percentage = (roic_count / len(reports)) * 100 if reports else 0
                    if roic_percentage < min_roic_fiscal_years_percent:
                        logging.debug(f"Skipping {ticker}: ROIC > {min_roic_value_percent}% percentage ({roic_percentage:.2f}%) below {min_roic_fiscal_years_percent}%.")
                        continue

            # Condition 7: D/E
            de_config = config.get('de_ratio')
            if de_config:
                max_de_fiscal_years_percent = de_config.get('max_fiscal_years_percent')
                max_de_value = de_config.get('max_value')
                if max_de_fiscal_years_percent is not None and max_de_value is not None:
                    de_count = sum(1 for r in reports if r.get('de_ratio') is not None and r['de_ratio'] < max_de_value)
                    de_percentage = (de_count / len(reports)) * 100 if reports else 0
                    if de_percentage < max_de_fiscal_years_percent:
                        logging.debug(f"Skipping {ticker}: D/E < {max_de_value}% percentage ({de_percentage:.2f}%) below {max_de_fiscal_years_percent}%.")
                        continue
            
            # If all conditions met, add to results
            latest_roe = latest_report.get('roe')
            latest_roic = latest_report.get('roic')
            latest_de = latest_report.get('de_ratio')
            latest_pe = latest_report.get('pe_ratio')

            results.append({
                'ticker': ticker,
                'company_name': title,
                'latest_roe': f"{latest_roe:.2f}%" if latest_roe is not None else 'N/A',
                'latest_roic': f"{latest_roic:.2f}%" if latest_roic is not None else 'N/A',
                'latest_de': f"{latest_de:.2f}" if latest_de is not None else 'N/A',
                'latest_pe': f"{latest_pe:.2f}" if latest_pe is not None else 'N/A'
            })
            logging.info(f"Included {ticker} in results.")

    except mariadb.Error as e:
        logging.error(f"Database error during screening: {e}")
    finally:
        if conn:
            conn.close()

    # Write results to CSV
    if results:
        with open(output_csv, 'w', newline='') as csvfile:
            fieldnames = ['ticker', 'company_name', 'latest_roe', 'latest_roic', 'latest_de', 'latest_pe']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Screening complete. Results saved to {output_csv}")
    else:
        logging.info("No companies matched the screening criteria.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Screen growth stocks based on financial criteria.')
    parser.add_argument('--config', type=str, required=True, help='Path to the JSON configuration file.')
    parser.add_argument('--output', type=str, default='growth_flat_stocks.csv', help='Output CSV file name.')
    args = parser.parse_args()

    screen_stocks(args.config, args.output)
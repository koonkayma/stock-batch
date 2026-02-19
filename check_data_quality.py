
import mariadb
import logging
from stock_selection_engine import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

CRITICAL_COLUMNS = [
    'ticker',
    'fiscal_year',
    'eps',                     # Growth Strategy (EPS Growth)
    'revenue',                 # Growth Strategy (Revenue CAGR)
    'net_income',              # Growth (ROE), Turnaround Strategy
    'operating_cash_flow',     # Dividend (FCF), Turnaround (OCF/EBIT)
    'capital_expenditures',    # Dividend (FCF)
    'total_liabilities',       # Dividend (Debt/Equity)
    'shareholders_equity',     # Dividend (Debt/Equity), Growth (ROE)
    'operating_income',        # Dividend (Interest Coverage), Turnaround
    'interest_expense',        # Dividend (Interest Coverage)
    'PaymentsOfDividends',     # Dividend (Payout Ratio)
    'long_term_debt'           # Turnaround (Debt Reduction)
]

def check_data_quality():
    try:
        conn = mariadb.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        cursor = conn.cursor()
        
        logger.info("--- Data Quality Check Report ---")
        
        # 1. Total Companies
        cursor.execute("SELECT COUNT(*) FROM sec_companies")
        total_companies = cursor.fetchone()[0]
        logger.info(f"Total Companies in DB: {total_companies}")
        
        # 2. Total Financial Reports
        cursor.execute("SELECT COUNT(*) FROM sec_financial_reports")
        total_reports = cursor.fetchone()[0]
        logger.info(f"Total Financial Reports: {total_reports}")

        if total_reports == 0:
            logger.warning("No financial reports found! Please run import_all_sec_data.py first.")
            return

        # 3. Recent Data Quality (Last 3 Years)
        logger.info("\nChecking data completeness for recent fiscal years (>= 2022):")
        
        # Get count of reports per column that are NOT NULL for recent years
        for col in CRITICAL_COLUMNS:
            if col in ['ticker', 'fiscal_year']: continue
            
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) as populated
                FROM sec_financial_reports 
                WHERE fiscal_year >= 2022
            """
            cursor.execute(query)
            result = cursor.fetchone()
            total = result[0]
            populated = result[1] or 0
            percentage = (populated / total * 100) if total > 0 else 0
            
            status = "OK" if percentage > 50 else "WARNING (Low Coverage)"
            if percentage == 0: status = "CRITICAL (Missing)"
            
            logger.info(f"{col:25}: {populated}/{total} ({percentage:.1f}%) - {status}")

        logger.info("\n---------------------------------")
        logger.info("If coverage is low for 'eps' or 'revenue', the stock selection engine will not find many candidates.")

    except mariadb.Error as e:
        logger.error(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_data_quality()

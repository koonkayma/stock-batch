
import mariadb
import pandas as pd
from . import config
from .logger import setup_logger

logger = setup_logger(__name__)

def get_connection():
    """Establishes and returns a database connection."""
    try:
        conn = mariadb.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return conn
    except mariadb.Error as e:
        logger.error(f"Error connecting to MariaDB: {e}", extra={'ticker': 'N/A', 'module_name': 'db_client'})
        return None

def fetch_all_companies():
    """Fetches all companies (cik, ticker) from the database."""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        query = "SELECT cik, ticker, title as company_name FROM sec_companies"
        df = pd.read_sql(query, conn)
        logger.info(f"Fetched {len(df)} companies from database.", extra={'ticker': 'ALL', 'module_name': 'db_client'})
        return df
    except Exception as e:
        logger.exception(f"Error fetching companies: {e}", extra={'ticker': 'ALL', 'module_name': 'db_client'})
        return pd.DataFrame()
    finally:
        conn.close()

def fetch_all_financial_reports():
    """Fetches all financial reports from the database."""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        # Fetching all columns. We handle CIK padding here if necessary, though spec says DB has it.
        # Note: Spec says sec_financial_reports has padded CIKs, sec_companies might not.
        query = "SELECT * FROM sec_financial_reports"
        logger.info("Starting bulk fetch of financial reports...", extra={'ticker': 'ALL', 'module_name': 'db_client'})
        
        # Using chunksize if data is huge, but for now loading all to DF as per spec optimization
        df = pd.read_sql(query, conn)
        
        logger.info(f"Fetched {len(df)} financial records from database.", extra={'ticker': 'ALL', 'module_name': 'db_client'})
        return df
    except Exception as e:
        logger.exception(f"Error fetching financial reports: {e}", extra={'ticker': 'ALL', 'module_name': 'db_client'})
        return pd.DataFrame()
    finally:
        conn.close()

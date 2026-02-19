
import os
import argparse
import pandas as pd
from . import config
from .logger import setup_logger
from . import db_client
from . import api_client
from . import data_processor
from .strategies import growth, dividend, turnaround, loss_to_profit

logger = setup_logger(__name__)

def save_to_csv(df, filename):
    """Saves DataFrame to CSV with atomic write."""
    if df.empty:
        logger.info(f"No results to save for {filename}", extra={'ticker': 'N/A', 'module_name': 'main'})
        return

    temp_filename = f"{filename}.tmp"
    try:
        df.to_csv(temp_filename, index=False)
        os.replace(temp_filename, filename)
        logger.info(f"Saved {len(df)} records to {filename}", extra={'ticker': 'N/A', 'module_name': 'main'})
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}", extra={'ticker': 'N/A', 'module_name': 'main'})
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def main():
    parser = argparse.ArgumentParser(description='Multi-Strategy Quantitative Stock Selection Engine')
    parser.add_argument('--limit', type=int, help='Limit number of tickers for testing')
    args = parser.parse_args()

    logger.info("Initializing Stock Selection Engine...", extra={'ticker': 'N/A', 'module_name': 'main'})

    # 1. Initialize API Client
    client = api_client.FinnhubClient()

    # 2. Bulk Extraction
    logger.info("Step 1: Bulk Data Extraction", extra={'ticker': 'N/A', 'module_name': 'main'})
    companies_df = db_client.fetch_all_companies()
    financials_df = db_client.fetch_all_financial_reports()

    # Merge company info (ticker) into financials if not present
    # financials_df has cik. companies_df has cik, ticker.
    # Ensure CIK types match
    if 'cik' in companies_df.columns and 'cik' in financials_df.columns:
         # Normalize CIKs? DB load typically handles types but good to ensure
         companies_df['cik'] = companies_df['cik'].astype(str).str.zfill(10)
         financials_df['cik'] = financials_df['cik'].astype(str).str.zfill(10)
         
         # Merge
         df = pd.merge(financials_df, companies_df[['cik', 'ticker', 'company_name']], on='cik', how='left')
    else:
         logger.critical("Missing CIK columns for merge.", extra={'ticker': 'N/A', 'module_name': 'main'})
         return

    if args.limit:
        logger.info(f"Limiting to first {args.limit} tickers for testing.", extra={'ticker': 'N/A', 'module_name': 'main'})
        tickers = df['ticker'].unique()[:args.limit]
        df = df[df['ticker'].isin(tickers)]

    # 3. Data Processing
    logger.info("Step 2: Vectorized Data Transformation", extra={'ticker': 'N/A', 'module_name': 'main'})
    df = data_processor.prepare_data(df)

    # 4. Strategy Execution
    logger.info("Step 3: Executing Quantitative Strategies", extra={'ticker': 'N/A', 'module_name': 'main'})
    
    # Growth
    growth_results = growth.filter(df, client)
    save_to_csv(growth_results, 'output_growth_stocks.csv')

    # Dividend
    dividend_results = dividend.filter(df, client)
    save_to_csv(dividend_results, 'output_dividend_stocks.csv')

    # Turnaround
    turnaround_results = turnaround.filter(df, client)
    save_to_csv(turnaround_results, 'output_turnaround_stocks.csv')

    # Loss-to-Profit
    # New strategy added
    loss_to_profit_results = loss_to_profit.filter(df, client)
    save_to_csv(loss_to_profit_results, 'output_loss_to_profit_stocks.csv')

    logger.info("Stock Selection Engine execution completed.", extra={'ticker': 'N/A', 'module_name': 'main'})

if __name__ == "__main__":
    main()

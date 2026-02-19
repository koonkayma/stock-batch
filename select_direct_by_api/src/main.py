"""
main.py

Main entry point for the Stock Selection Engine.
Orchestrates data fetching, strategy execution, and reporting.
"""

import argparse
import sys
import csv
import logging
import json
from pathlib import Path
from datetime import datetime

# Import local modules
# Note: Using relative imports requires running as module (python -m src.main)
# or absolute imports if pythonpath set. 
# We'll rely on running via `python3 -m src.main` from root.

try:
    from . import config
    from . import utils
    from . import universe
    from . import data_source
    from .models import StockData, AnalysisReport
    from .strategies import growth, dividend, turnaround, loss_to_earn
except ImportError:
    # Fallback for direct execution if needed (dev)
    import config
    import utils
    import universe
    import data_source
    from models import StockData, AnalysisReport
    from strategies import growth, dividend, turnaround, loss_to_earn

logger = logging.getLogger(__name__)

def process_ticker(ticker: str, cik: str, clients) -> AnalysisReport:
    """
    Runs the full analysis pipeline for a single ticker.
    """
    sec_client, finnhub_client, yf_client = clients
    
    stock = StockData(ticker=ticker)
    
    # 1. Fetch SEC Data (Financials)
    facts = sec_client.get_company_facts(ticker, cik)
    if facts:
        # Save raw JSON and compress
        raw_path = config.RAW_DATA_DIR / f"{ticker}_facts.json"
        try:
            with open(raw_path, 'w') as f:
                json.dump(facts, f)
            
            gz_path = config.ARCHIVE_DATA_DIR / f"{ticker}_facts.json.gz"
            utils.compress_sec_payload(raw_path, gz_path)
            
        except Exception as e:
            logger.error(f"Compression error for {ticker}: {e}")

        # Parse Annuals
        stock.annuals = sec_client.parse_financials(facts)
        stock.sort_annuals()
        
    # 2. Fetch Market Data (Finnhub)
    quote = finnhub_client.get_quote(ticker)
    if quote:
         stock.price = quote.get("c")
    
    profile = finnhub_client.get_profile(ticker)
    if profile:
        stock.sector = profile.get("finnhubIndustry")
        stock.market_cap = profile.get("marketCapitalization")
    
    # 3. strategies
    report = AnalysisReport(ticker=ticker)
    
    # Growth
    report.growth_result = growth.evaluate(stock.annuals)
    
    # Dividend
    stock.payout_ratio_ttm = None 
    report.dividend_result = dividend.evaluate(stock)
    
    # Turnaround
    report.turnaround_result = turnaround.evaluate(stock)
    
    # Loss to Earn
    report.loss_to_earn_result = loss_to_earn.evaluate(stock)
    
    return report

def run():
    parser = argparse.ArgumentParser(description="Stock Selection Engine")
    parser.add_argument("--ticker", type=str, help="Run in Single Ticker Mode")
    parser.add_argument("--batch", action="store_true", help="Run in Batch Mode")
    
    args = parser.parse_args()
    
    utils.setup_logging()
    
    # Load settings
    api_key = config.SETTINGS.get("FINNHUB_API_KEY", "")
    if not api_key:
        logger.error("FINNHUB_API_KEY not found in configuration.")
        sys.exit(1)

    # Init Clients
    sec_client = data_source.SecClient()
    finnhub_client = data_source.FinnhubClient(api_key)
    yf_client = data_source.YFinanceClient() # Keep client if we need it later, or remove? Keeping for now logic simplicty
    clients = (sec_client, finnhub_client, yf_client)
    
    if args.ticker:
        ticker_symbol = args.ticker.upper()
        logger.info(f"Running Single Ticker Mode for {ticker_symbol}")
        
        # Resolve CIK
        tickers = universe.get_sec_tickers()
        target_cik = next((c for t, c in tickers if t == ticker_symbol), None)
        
        if not target_cik:
            logger.error(f"Ticker {ticker_symbol} not found in SEC universe.")
            return

        try:
             report = process_ticker(ticker_symbol, target_cik, clients)
        except Exception as e:
             logger.exception(f"Fatal error processing {ticker_symbol}: {e}")
             return

        # Output to Console
        print(f"\n{'='*40}")
        print(f"REPORT FOR {ticker_symbol}")
        print(f"{'='*40}")
        
        def print_strat(name, res):
            if not res: return
            status = "PASS" if res.passed else "FAIL"
            print(f"{name:<12} [{status}] {res.signal}")
            if res.details:
                 if "per_year" in res.details:
                      print(f"  Years: {res.details['years_analysed']}")
                 else:
                      print(f"  {res.details}")

        print_strat("Growth", report.growth_result)
        print_strat("Dividend", report.dividend_result)
        print_strat("Turnaround", report.turnaround_result)
        print_strat("Loss2Earn", report.loss_to_earn_result)
        
        print(f"{'='*40}\n")
        
    elif args.batch:
        logger.info("Running Batch Mode")
        tickers = universe.get_sec_tickers()
        
        # --- Resume Logic ---
        checkpoint_file = config.ROOT_DIR / "checkpoint.json"
        processed_tickers = set()
        csv_path = None
        
        # 1. Check for existing checkpoint
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                    csv_path = Path(checkpoint_data.get("csv_path", ""))
                    
                if csv_path and csv_path.exists():
                    logger.info(f"Resuming from checkpoint: {csv_path}")
                    # Read existing tickers to skip
                    with open(csv_path, 'r') as f:
                        reader = csv.reader(f)
                        header = next(reader, None)
                        for row in reader:
                            if row:
                                processed_tickers.add(row[0]) # Ticker is first column
                    logger.info(f"Skipping {len(processed_tickers)} already processed tickers.")
                else:
                    logger.warning("Checkpoint found but CSV missing/invalid. Starting fresh.")
                    csv_path = None
            except Exception as e:
                logger.error(f"Error reading checkpoint: {e}. Starting fresh.")
                csv_path = None

        # 2. Setup new run if no valid resume
        if not csv_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = config.ROOT_DIR / f"output_{ts}.csv"
            # Create checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump({"csv_path": str(csv_path)}, f)
                
            # Init CSV with header
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Ticker", "Growth_Pass", "Growth_Signal", 
                    "Dividend_Pass", "Turnaround_Pass", "LossToEarn_Pass"
                ])

        # 3. Processing Loop
        # Append mode 'a' for resume, but we open/close per batch logic or keep open?
        # To be safe and simple: open in append mode for the whole loop
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            
            for ticker, cik in tickers:
                if ticker in processed_tickers:
                    continue
                    
                try:
                    logger.info(f"Processing {ticker}...")
                    report = process_ticker(ticker, cik, clients)
                    
                    writer.writerow([
                        ticker,
                        report.growth_result.passed, report.growth_result.signal,
                        report.dividend_result.passed,
                        report.turnaround_result.passed,
                        report.loss_to_earn_result.passed
                    ])
                    f.flush() # Ensure data is written immediately
                    
                except KeyboardInterrupt:
                    print("\nBatch interrupted. Checkpoint saved.")
                    # We do NOT delete checkpoint here
                    break
                except Exception as e:
                    logger.error(f"Error {ticker}: {e}")
                    continue
        
            # 4. Cleanup checkpoint if finished naturally (not interrupted)
            else:
                # This else block executes if the loop completes normally (no break)
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
                logger.info(f"Batch completed successfully: {csv_path}")

if __name__ == "__main__":
    run()

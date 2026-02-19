
import pandas as pd
from .. import config
from ..logger import setup_logger

logger = setup_logger(__name__)

def filter(df, api_client):
    """
    Filters stocks for Healthy Dividend Strategy.
    """
    logger.info("Starting Dividend Strategy filtering...", extra={'ticker': 'ALL', 'module_name': 'strategies.dividend'})
    
    # Filter 1: Positive Free Cash Flow
    div_df = df[df['free_cash_flow'] > 0].copy()
    
    # Filter 2: Debt-to-Equity < 1.0 (or industry avg)
    div_df = div_df[div_df['debt_to_equity'] < config.DIVIDEND_MAX_DE_RATIO]
    
    # Filter 3: Interest Coverage > 3.0
    div_df = div_df[div_df['interest_coverage'] > config.DIVIDEND_MIN_INTEREST_COVERAGE]

    # Filter 4: Payout Ratio (20% - 60%)
    # Assuming 'payout_ratio' column exists or calculated (Dividends / Net Income)
    if 'dividend_per_share' in div_df.columns and 'eps' in div_df.columns:
         div_df['payout_calc'] = div_df['dividend_per_share'] / div_df['eps']
         div_df = div_df[(div_df['payout_calc'] > config.DIVIDEND_MIN_PAYOUT_RATIO) & 
                         (div_df['payout_calc'] < config.DIVIDEND_MAX_PAYOUT_RATIO)]
    
    # Process latest year for candidates
    candidates = div_df.groupby('cik').tail(1)
    final_candidates = []

    for index, row in candidates.iterrows():
        ticker = row['ticker']
        try:
            # Yield check against market average? Spec: Yield > Market Average
            # We can get yield from Finnhub basic financials
            basic_fin = api_client.get_basic_financials(ticker)
            if not basic_fin or 'metric' not in basic_fin:
                continue
                
            metrics = basic_fin['metric']
            yield_curr = metrics.get('dividendYieldIndicatedAnnual', 0)
            
            # Simple threshold for "Market Average" -> e.g., > 1.5% or just verify it's a payer
            if yield_curr and yield_curr > 1.5: 
                 # Add
                 row['dividend_yield'] = yield_curr
                 profile = api_client.get_company_profile(ticker)
                 if profile:
                     row['sector'] = profile.get('finnhubIndustry')
                     row['market_cap'] = profile.get('marketCapitalization')
                 
                 final_candidates.append(row)
                 logger.info(f"Added {ticker} to Dividend Portfolio. Yield: {yield_curr}%", extra={'ticker': ticker, 'module_name': 'strategies.dividend'})

        except Exception as e:
            logger.error(f"Error processing {ticker} for dividend: {e}", extra={'ticker': ticker, 'module_name': 'strategies.dividend'})

    return pd.DataFrame(final_candidates)

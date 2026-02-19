
import pandas as pd
from .. import config
from ..logger import setup_logger

logger = setup_logger(__name__)

def filter(df, api_client):
    """
    Filters stocks for Earnings Turnaround Strategy.
    """
    logger.info("Starting Turnaround Strategy filtering...", extra={'ticker': 'ALL', 'module_name': 'strategies.turnaround'})
    
    # Logic: 
    # 1. Distress: Negative Net Income for previous 2 years (T-1, T-2).
    # 2. Inflection: Positive Net Income in current year (T).
    # 3. Validation: OCF / EBIT > 1.0 (or > 0 if EBIT/OCF ratio logic)
    # 4. De-risking: Debt reduced from T-1 to T.
    
    # We need to act on the time series. 
    # Group by CIK, check conditions on the *latest* row T.
    
    # Condition: T > 0, T-1 < 0, T-2 < 0
    df['is_turnaround_candidate'] = (df['net_income'] > 0) & \
                                    (df['net_income_prev'] < 0) & \
                                    (df['net_income_2y_ago'] < 0)
    
    candidates_df = df[df['is_turnaround_candidate']].copy()
    
    # Filter: OCF / EBIT Ratio
    candidates_df = candidates_df[candidates_df['ocf_to_ebit'] > config.TURNAROUND_MIN_OCF_EBIT_RATIO]
    
    # Filter: Debt Reduced (Debt Change < 0)
    candidates_df = candidates_df[candidates_df['debt_change_yoy'] < 0]
    
    # Accrual Ratio check? |Accrual| < 0.1?
    
    # Finalize
    # Get latest data per ticker (should be the turnaround year)
    candidates = candidates_df.groupby('cik').tail(1)
    final_candidates = []
    
    for index, row in candidates.iterrows():
         ticker = row['ticker']
         try:
             # Just enrich with sector/profile
             profile = api_client.get_company_profile(ticker)
             if profile:
                 row['sector'] = profile.get('finnhubIndustry')
                 row['market_cap'] = profile.get('marketCapitalization')
             
             final_candidates.append(row)
             logger.info(f"Added {ticker} to Turnaround Portfolio.", extra={'ticker': ticker, 'module_name': 'strategies.turnaround'})
         except Exception as e:
             logger.error(f"Error processing {ticker}: {e}", extra={'ticker': ticker, 'module_name': 'strategies.turnaround'})
             
    return pd.DataFrame(final_candidates)


import pandas as pd
from .. import config
from ..logger import setup_logger

logger = setup_logger(__name__)

def filter(df, api_client):
    """
    Filters stocks for Loss-to-Profit Strategy.
    Criteria:
    1. Net Income Transition: Current > 0, Previous < 0
    2. Operational Validation: Revenue Growth (Current > Previous), Gross Margin Improvement (Current > Previous)
    3. Solvency: Debt-to-Equity < 2.0, Cash Ratio > 1.0
    """
    logger.info("Starting Loss-to-Profit Strategy filtering...", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})
    
    # Filter 1: Net Income Transition
    # Current Net Income > 0 AND Previous Net Income < 0
    transition_df = df[(df['net_income'] > 0) & (df['net_income_prev'] < 0)].copy()
    logger.debug(f"Stocks passing Net Income Transition check: {len(transition_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})
    
    if transition_df.empty:
        return pd.DataFrame()

    # Filter 2: Operational Validation
    # Sequential Revenue Growth: Revenue (Current) > Revenue (Previous)
    op_val_df = transition_df[transition_df['revenue'] > transition_df['revenue_prev']]
    logger.debug(f"Stocks passing Revenue Growth check: {len(op_val_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})
    
    # Gross Margin Improvement: Gross Margin (Current) > Gross Margin (Previous)
    op_val_df = op_val_df[op_val_df['gross_margin'] > op_val_df['gross_margin_prev']]
    logger.debug(f"Stocks passing Gross Margin check: {len(op_val_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})

    # Filter 3: Solvency
    # Debt-to-Equity < 2.0
    # Note: Using config constant if defined, else 2.0 as per spec
    max_de = getattr(config, 'LOSS_TO_PROFIT_MAX_DE_RATIO', 2.0)
    solvency_df = op_val_df[op_val_df['debt_to_equity'] < max_de]
    logger.debug(f"Stocks passing Debt-to-Equity check: {len(solvency_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})

    # Cash Ratio > 1.0
    min_cash_ratio = getattr(config, 'LOSS_TO_PROFIT_MIN_CASH_RATIO', 1.0)
    solvency_df = solvency_df[solvency_df['cash_ratio'] > min_cash_ratio]
    logger.debug(f"Stocks passing Cash Ratio check: {len(solvency_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})

    # API Enrichment
    final_candidates = []
    # Using only the latest year for each CIK if duplicates exist (though calc logic suggests df might have multiple years per company, we usually want the LATEST fiscal year for screening)
    # The main script usually prepares data but might not strictly filter for "only latest year" before passing to strategies.
    # Standard practice: Take the latest fiscal year for each CIK that passed filters.
    
    # Sort by fiscal year descending to get latest
    solvency_df = solvency_df.sort_values(by=['cik', 'fiscal_year'], ascending=[True, False])
    # Drop duplicates to keep only latest fiscal year per CIK
    latest_reports = solvency_df.drop_duplicates(subset=['cik'], keep='first')
    
    logger.info(f"Final candidates before API enrichment: {len(latest_reports)}", extra={'ticker': 'ALL', 'module_name': 'strategies.loss_to_profit'})

    for index, row in latest_reports.iterrows():
        ticker = row['ticker']
        try:
            # API Enrichment (Sector, Price)
            basic_fin = api_client.get_basic_financials(ticker)
            
            # Enrich with Sector/Industry/Market Cap
            # Initialize defaults
            row['sector'] = 'N/A'
            row['industry'] = 'N/A'
            row['market_cap'] = 0
            row['current_price'] = 0
            
            if basic_fin and 'metric' in basic_fin:
                metrics = basic_fin['metric']
                row['current_price'] = metrics.get('currentPrice', 0)
                row['sector'] = basic_fin.get('finnhubIndustry', 'N/A') # Basic fin might not have industry directly at top level?
                
            profile = api_client.get_company_profile(ticker)
            if profile:
                row['sector'] = profile.get('finnhubIndustry', row['sector'])
                row['industry'] = profile.get('finnhubIndustry', 'N/A')
                row['market_cap'] = profile.get('marketCapitalization', 0)
            
            # Add strategy specific output columns if needed for display
            # Already have net_income, net_income_prev, debt_to_equity, cash_ratio in row
            
            final_candidates.append(row)
            logger.info(f"Added {ticker} to Loss-to-Profit Portfolio.", extra={'ticker': ticker, 'module_name': 'strategies.loss_to_profit'})

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}", extra={'ticker': ticker, 'module_name': 'strategies.loss_to_profit'})
            # We might still want to add it even if API fails, trusting DB data? 
            # For now, let's keep consistency with other strategies and include it if DB data passed.
            if row['sector'] == 'N/A':
                 # Fallback if API completely failed
                 final_candidates.append(row)

    return pd.DataFrame(final_candidates)

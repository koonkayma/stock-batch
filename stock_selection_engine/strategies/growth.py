
import pandas as pd
from .. import config
from ..logger import setup_logger

logger = setup_logger(__name__)

def filter(df, api_client):
    """
    Filters stocks for Growth Strategy.
    """
    logger.info("Starting Growth Strategy filtering...", extra={'ticker': 'ALL', 'module_name': 'strategies.growth'})
    
    # Filter: 3-Year Revenue CAGR > 10%
    growth_df = df[df['revenue_cagr_3y'] > config.GROWTH_MIN_REVENUE_CAGR].copy()
    logger.debug(f"Stocks passing Revenue CAGR check: {len(growth_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.growth'})
    
    # Filter: Positive EPS Growth (1Y)
    growth_df = growth_df[growth_df['eps_growth_1y'] > config.GROWTH_MIN_EPS_growth]
    logger.debug(f"Stocks passing EPS Growth check: {len(growth_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.growth'})
    
    # Filter: ROE > 15%
    growth_df = growth_df[growth_df['roe'] > config.GROWTH_MIN_ROE]
    logger.debug(f"Stocks passing ROE check: {len(growth_df)}", extra={'ticker': 'ALL', 'module_name': 'strategies.growth'})
    
    # Sort and deduplicate to get latest reports
    growth_df = growth_df.sort_values(by=['cik', 'fiscal_year'], ascending=[True, False])
    latest_reports = growth_df.drop_duplicates(subset=['cik'], keep='first')
    
    final_candidates = []

    for index, row in latest_reports.iterrows():
        ticker = row['ticker']
        try:
            # API Enrichment (Sector, Price, etc.)
            # Fetch basic financials for context, even if PEG filter is removed
            basic_fin = api_client.get_basic_financials(ticker)
            
            if basic_fin and 'metric' in basic_fin:
                metrics = basic_fin['metric']
                
                # We still might want PEG for display if available, but no longer filtering by it.
                peg = metrics.get('pegTTM')
                row['peg_ratio'] = peg if peg else 'N/A'
                
                # Enrich with Sector/Industry/Market Cap
                row['sector'] = basic_fin.get('finnhubIndustry', 'N/A')
                
                profile = api_client.get_company_profile(ticker)
                if profile:
                    row['sector'] = profile.get('finnhubIndustry', 'N/A')
                    row['industry'] = profile.get('finnhubIndustry', 'N/A')
                    row['market_cap'] = profile.get('marketCapitalization', 0)
                
                row['current_price'] = metrics.get('currentPrice')
                
                final_candidates.append(row)
                logger.info(f"Added {ticker} to Growth Portfolio.", extra={'ticker': ticker, 'module_name': 'strategies.growth'})
            else:
                 # If API fails to get basics, we might still want to add it or skip?
                 # Assuming we need at least price/sector for the report, skipping if API fails completely is safer for data quality
                 logger.warning(f"Skipping {ticker} due to missing API data.", extra={'ticker': ticker, 'module_name': 'strategies.growth'})

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}", extra={'ticker': ticker, 'module_name': 'strategies.growth'})
            
    return pd.DataFrame(final_candidates)

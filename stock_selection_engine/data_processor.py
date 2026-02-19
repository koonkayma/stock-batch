
import pandas as pd
import numpy as np
from .logger import setup_logger

logger = setup_logger(__name__)

def prepare_data(df):
    """
    Prepares the DataFrame for analysis by calculating derived metrics and sorting.
    Expects df to contain all financial reports.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to prepare_data.", extra={'ticker': 'N/A', 'module_name': 'data_processor'})
        return df

    # Ensure correct data types
    numeric_cols = ['revenue', 'net_income', 'eps', 'operating_cash_flow', 'shareholders_equity', 
                    'total_liabilities', 'dividend_per_share', 'capital_expenditures', 'operating_income',
                    'total_assets', 'total_current_liabilities', 'long_term_debt', 'current_assets', 
                    'current_liabilities', 'ebit', 'gross_profit', 'gross_margin', 'cash_and_short_term_investments', 'cash_and_equivalents']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Sort by CIK and Fiscal Year
    df.sort_values(by=['cik', 'fiscal_year'], inplace=True)

    # Calculate basic derived metrics
    # ROE = Net Income / Shareholders Equity * 100
    df['roe'] = (df['net_income'] / df['shareholders_equity']) * 100
    
    # FCF = Operating Cash Flow - Capital Expenditures
    df['free_cash_flow'] = df['operating_cash_flow'] - df['capital_expenditures']
    
    # Debt to Equity = Total Liabilities / Shareholders Equity
    df['debt_to_equity'] = df['total_liabilities'] / df['shareholders_equity']

    # Interest Coverage = EBIT / Interest Expense (interest_expense might be missing, using simple proxy if needed, based on spec OCF/EBIT logic mainly)
    # Spec says: Interest Coverage Ratio (EBIT / Interest Expense) > 3.0
    # We need interest_expense column if available, or derive it. Assuming 'interest_expense' exists or we need to add mapping for it.
    # Checking spec: It mentions Interest Coverage Ratio. 
    # Providing placeholder if column missing, ensuring no crash.
    if 'interest_expense' in df.columns and 'ebit' in df.columns:
         df['interest_coverage'] = df['ebit'] / df['interest_expense']
    else:
         df['interest_coverage'] = np.nan # Or 0

    # Payout Ratio = Dividends Paid / Net Income
    # Spec: PaymentsOfDividends / net_income (Dividend_Payout_Ratio provided in mapping)
    # If using pre-calculated column from DB imports:
    # df['payout_ratio'] = df['Dividend_Payout_Ratio'] 
    
    # Calculate YoY Growth and shifts for CAGR
    # Using groupby to ensure shifts don't cross companies
    
    # Previous Year EPS
    df['eps_prev'] = df.groupby('cik')['eps'].shift(1)
    df['eps_growth_1y'] = (df['eps'] - df['eps_prev']) / df['eps_prev'].abs()
    
    # Previous Year Net Income
    df['net_income_prev'] = df.groupby('cik')['net_income'].shift(1)
    df['net_income_2y_ago'] = df.groupby('cik')['net_income'].shift(2)

    # Revenue 3 years ago (for 3Y CAGR)
    # fiscal_year is int. We want to compare row N with row N-3
    # Shift 3 rows back
    df['revenue_3y_ago'] = df.groupby('cik')['revenue'].shift(3)
    
    # Calculate 3Y Revenue CAGR: (Val_end / Val_start)^(1/3) - 1
    # Handle negative base values or zeroes
    def calculate_cagr(end, start, years):
        if start <= 0 or pd.isna(start) or pd.isna(end) or end <= 0:
            return np.nan
        return (end / start)**(1/years) - 1
    
    # Vectorized check isn't trivial with power on negative bases, but revenue is usually positive.
    # Using lambda for simplicity on series
    df['revenue_cagr_3y'] = df.apply(
        lambda row: calculate_cagr(row['revenue'], row['revenue_3y_ago'], 3), axis=1
    )

    # EPS 3Y CAGR (optional based on spec, but good for growth)
    df['eps_3y_ago'] = df.groupby('cik')['eps'].shift(3)
    # EPS needed for growth consistency check (positive increase for trailing 3 periods)
    df['eps_2y_ago'] = df.groupby('cik')['eps'].shift(2)
    
    
    # Turnaround specific:
    # "two consecutive trailing fiscal years of negative net income"
    # Current row is T (potential turnaround year). We look at T-1 and T-2.
    # Wait, the spec says "baseline of historical distress... two consecutive trailing fiscal years of negative"
    # And "inflection point... transition from negative to positive profitability in the most recent reporting period"
    # So: T (Current) > 0, T-1 < 0, T-2 < 0
    
    # Total Debt Change
    # Assuming 'total_liabilities' or 'long_term_debt' + 'short_term_debt'. Spec says "Total Debt".
    # Using total_liabilities as proxy for leverage if specific debt columns missing, or sum.
    # Let's check available columns. import_all_sec_data_mapping.md has long_term_debt and short_term_debt (added recently short_term_borrowings?)
    # Mapping has `short_term_borrowings` and `long_term_debt`.
    # df['total_debt'] = df['short_term_borrowings'].fillna(0) + df['long_term_debt'].fillna(0)
    
    if 'short_term_borrowings' in df.columns and 'long_term_debt' in df.columns:
         df['total_debt'] = df['short_term_borrowings'].fillna(0) + df['long_term_debt'].fillna(0)
         df['total_debt_prev'] = df.groupby('cik')['total_debt'].shift(1)
         df['debt_change_yoy'] = (df['total_debt'] - df['total_debt_prev']) / df['total_debt_prev']
    else:
        df['total_debt'] = np.nan
        df['debt_change_yoy'] = np.nan

    # Calculate EBIT if missing
    if 'ebit' not in df.columns:
        if 'net_income' in df.columns and 'interest_expense' in df.columns and 'income_tax_expense' in df.columns:
            df['ebit'] = df['net_income'] + df['interest_expense'].fillna(0) + df['income_tax_expense'].fillna(0)
        elif 'operating_income' in df.columns:
            df['ebit'] = df['operating_income']
        else:
            df['ebit'] = np.nan

    # OCF / EBIT
    # Spec: Operating Cash Flow / EBIT
    if 'operating_cash_flow' in df.columns:
         df['ocf_to_ebit'] = df.apply(lambda row: row['operating_cash_flow'] / row['ebit'] if pd.notna(row.get('ebit')) and row['ebit'] != 0 else np.nan, axis=1)
    else:
         df['ocf_to_ebit'] = np.nan
    
    # Solvency: Debt to Equity (already calculated)
    
    # Loss-to-Profit specific metrics:
    
    # Revenue Growth (Sequential/YoY)
    df['revenue_prev'] = df.groupby('cik')['revenue'].shift(1)
    
    # Gross Margin Improvement
    # Using 'gross_margin' column if available, else derive: gross_profit / revenue
    if 'gross_margin' not in df.columns:
         if 'gross_profit' in df.columns and 'revenue' in df.columns:
             df['gross_margin'] = df.apply(lambda row: (row['gross_profit'] / row['revenue'] * 100) if row['revenue'] and row['revenue'] != 0 else np.nan, axis=1)
         else:
             df['gross_margin'] = np.nan
             
    df['gross_margin_prev'] = df.groupby('cik')['gross_margin'].shift(1)
    
    # Cash Ratio
    # (Cash + Marketable Securities) / Current Liabilities
    # Try 'cash_and_short_term_investments' first, then 'cash_and_equivalents'
    def calculate_cash_ratio(row):
        liabilities = row.get('total_current_liabilities')
        if not liabilities or liabilities == 0:
            return np.nan
            
        cash = row.get('cash_and_short_term_investments')
        if pd.isna(cash):
            cash = row.get('cash_and_equivalents')
            
        if pd.isna(cash):
            return np.nan
            
        return cash / liabilities

    df['cash_ratio'] = df.apply(calculate_cash_ratio, axis=1)

    # Accrual Ratio
    # (Net Income - OCF) / Total Assets
    if 'total_assets' in df.columns:
         df['accrual_ratio'] = (df['net_income'] - df['operating_cash_flow']) / df['total_assets']
    
    logger.info("Data preparation complete.", extra={'ticker': 'ALL', 'module_name': 'data_processor'})
    return df

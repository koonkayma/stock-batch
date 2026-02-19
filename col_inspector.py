from import_all_sec_data import METRIC_MAP
hardcoded = ['cik', 'fiscal_year', 'filing_date', 'form', 'price']
all_cols = hardcoded + list(METRIC_MAP.keys())
for i, col in enumerate(all_cols):
    print(f"{i}: {col}")

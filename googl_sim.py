import json
import gzip
import os
from import_all_sec_data import METRIC_MAP

def simulate_googl():
    cik = "0001652044"
    ticker = "GOOGL"
    file_path = f"sec_data/CIK{cik}.json.gz"
    
    with gzip.open(file_path, 'rb') as f:
        company_data = json.load(f)

    data_by_year = {}
    supported_units = ['USD', 'USD/shares', 'shares']
    for metric, details in company_data.get('facts', {}).get('us-gaap', {}).items():
        for unit in supported_units:
            if unit in details.get('units', {}):
                for item in details['units'][unit]:
                    if item.get('fp') == 'FY' and 'form' in item:
                         year = int(item.get('end', '').split('-')[0]) if item.get('end') else item.get('fy')
                         if not year:
                             continue
                         if year not in data_by_year:
                             data_by_year[year] = {
                                 'cik': str(cik).zfill(10), 
                                 'fiscal_year': year, 
                                 'filing_date': item.get('filed'),
                                 'form': item.get('form'),
                                 'temp_metrics': {}
                             }
                         data_by_year[year].setdefault('temp_metrics', {})[metric] = item['val']

    # We need a dummy price since we are not calling yfinance
    current_price = 302.02

    records_to_insert = []
    for year, year_data_raw in data_by_year.items():
        record = {
            'cik': year_data_raw['cik'], 
            'fiscal_year': year_data_raw['fiscal_year'], 
            'filing_date': year_data_raw.get('filing_date'),
            'form': year_data_raw.get('form'),
            'price': current_price
        }
        
        metrics_data = year_data_raw.get('temp_metrics', {})
        for name, gaap_tags in METRIC_MAP.items():
            if isinstance(gaap_tags, str):
                record[name] = metrics_data.get(gaap_tags)
            elif isinstance(gaap_tags, list):
                for tag in gaap_tags:
                    if isinstance(tag, str) and tag in metrics_data:
                        record[name] = metrics_data[tag]
                        break
                else:
                    if name not in record:
                        record[name] = None

        for name, logic in METRIC_MAP.items():
            if callable(logic):
                try: record[name] = logic(record)
                except: record[name] = None
            elif isinstance(logic, list) and len(logic) > 0 and callable(logic[-1]):
                if record.get(name) is None:
                    try: record[name] = logic[-1](record)
                    except: record[name] = None
        
        records_to_insert.append(record)

    hardcoded = ['cik', 'fiscal_year', 'filing_date', 'form', 'price']
    all_cols = hardcoded + list(METRIC_MAP.keys())
    
    for i, rec in enumerate(records_to_insert):
        if i == 4:
            print(f"\n--- Full Data for Record {i} (FY{rec['fiscal_year']}) ---")
            for j, col in enumerate(all_cols):
                val = rec.get(col)
                print(f"{j}: {col} = {val} ({type(val)})")
        else:
            col19_name = all_cols[19]
            val = rec.get(col19_name)
            # print(f"Record {i} FY{rec['fiscal_year']}: Col 19 = {val}")

if __name__ == "__main__":
    simulate_googl()

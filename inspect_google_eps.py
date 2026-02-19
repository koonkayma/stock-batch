import json
import gzip

def find_metrics_for_years(target_years):
    with gzip.open('sec_data/CIK0001652044.json.gz', 'rb') as f:
        data = json.load(f)
    metrics_found = {year: [] for year in target_years}
    for metric, content in data['facts'].get('us-gaap', {}).items():
        for unit, items in content.get('units', {}).items():
            for item in items:
                if item.get('fp') == 'FY' and item.get('fy') in target_years:
                    metrics_found[item['fy']].append(metric)
    
    for year in target_years:
        print(f"\n--- Metrics for FY{year} ---")
        unique_metrics = sorted(list(set(metrics_found[year])))
        print(f"Count: {len(unique_metrics)}")
        # Print first 100
        print(unique_metrics[:100])
        
        eps_diluted = 'EarningsPerShareDiluted'
        eps_basic = 'EarningsPerShareBasic'
        
        if eps_diluted in unique_metrics:
            print(f"FOUND {eps_diluted}!")
        else:
            print(f"MISSING {eps_diluted}")
            
        if eps_basic in unique_metrics:
            print(f"FOUND {eps_basic}!")
        else:
            print(f"MISSING {eps_basic}")

if __name__ == "__main__":
    find_metrics_for_years([2016, 2017])

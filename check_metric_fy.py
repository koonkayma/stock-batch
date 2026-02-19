import json
import gzip

def check_metric_fy(metric_name):
    with gzip.open('sec_data/CIK0001652044.json.gz', 'rb') as f:
        data = json.load(f)
    metric_data = data['facts'].get('us-gaap', {}).get(metric_name, {})
    if not metric_data:
        print(f"Metric {metric_name} not found.")
        return
    
    print(f"\n--- FY entries for {metric_name} ---")
    for unit, items in metric_data.get('units', {}).items():
        print(f"Unit: {unit}")
        fy_items = [i for i in items if i.get('fp') == 'FY']
        for i in sorted(fy_items, key=lambda x: x.get('fy')):
            print(f"FY{i['fy']}: {i['val']} (form {i.get('form')}, filed {i.get('filed')})")

if __name__ == "__main__":
    check_metric_fy('EntityCommonStockSharesOutstanding')
    check_metric_fy('CommonStockSharesOutstanding')
    check_metric_fy('WeightedAverageNumberOfDilutedSharesOutstanding')

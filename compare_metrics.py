import json
import gzip

def compare_metrics(metrics):
    with gzip.open('sec_data/CIK0001652044.json.gz', 'rb') as f:
        data = json.load(f)
    for metric_name in metrics:
        print(f"\n--- {metric_name} ---")
        metric_data = data['facts'].get('us-gaap', {}).get(metric_name, {})
        units = metric_data.get('units', {})
        for unit, items in units.items():
            print(f"Unit: {unit}")
            fy_items = [i for i in items if i.get('fp') == 'FY' and i.get('fy') in [2016, 2017, 2018, 2019]]
            for i in sorted(fy_items, key=lambda x: (x.get('fy'), x.get('end'))):
                print(f"FY{i['fy']} ({i['start']} to {i['end']}) val={i['val']} accn={i['accn']}")

if __name__ == "__main__":
    compare_metrics(['NetIncomeLoss', 'EarningsPerShareDiluted'])

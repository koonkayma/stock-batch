import json
import gzip

def dump_eps():
    with gzip.open('sec_data/CIK0001652044.json.gz', 'rb') as f:
        data = json.load(f)
    eps = data['facts']['us-gaap'].get('EarningsPerShareDiluted', {})
    units = eps.get('units', {}).get('USD/shares', [])
    print(f"Total entries: {len(units)}")
    for i in sorted(units, key=lambda x: (x.get('fy', 0), x.get('fp', ''), x.get('start', ''))):
        print(i)

if __name__ == "__main__":
    dump_eps()

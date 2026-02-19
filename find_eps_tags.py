import json
import gzip

def find_eps_tags():
    with gzip.open('sec_data/CIK0001652044.json.gz', 'rb') as f:
        data = json.load(f)
    facts = data['facts'].get('us-gaap', {})
    eps_tags = [t for t in facts.keys() if 'EarningsPerShare' in t]
    print(f"Found {len(eps_tags)} EPS tags:")
    for tag in sorted(eps_tags):
        tag_data = facts[tag]
        # Check if it has any FY2016 or FY2017 data
        has_2016 = any(i.get('fp') == 'FY' and i.get('fy') == 2016 for u in tag_data.get('units', {}).values() for i in u)
        has_2017 = any(i.get('fp') == 'FY' and i.get('fy') == 2017 for u in tag_data.get('units', {}).values() for i in u)
        status = []
        if has_2016: status.append("FY2016")
        if has_2017: status.append("FY2017")
        print(f"  {tag}: {', '.join(status) if status else 'None'}")

if __name__ == "__main__":
    find_eps_tags()

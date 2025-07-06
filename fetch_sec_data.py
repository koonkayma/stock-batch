

import json
import requests
import time
import os

# Set a compliant User-Agent
HEADERS = {'User-Agent': 'Gemini CLI Agent gemini-cli@google.com'}

# Create a directory to store the data
if not os.path.exists('sec_data'):
    os.makedirs('sec_data')

# Load the company tickers file
with open('company_tickers.json', 'r') as f:
    companies = json.load(f)

# --- Demonstration: Fetch data for the first 5 companies ---
# In a real scenario, you would loop through all companies.
# For this example, we'll just get a few to prove the concept.
count = 0
for company in companies.values():
    if count >= 5:
        break

    cik_str = str(company['cik_str']).zfill(10)
    ticker = company['ticker']
    
    print(f"Fetching data for {ticker} (CIK: {cik_str})...")

    # Construct the API URL
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"

    # Make the request
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save the data
        output_path = os.path.join('sec_data', f'CIK{cik_str}.json')
        with open(output_path, 'w') as out_file:
            json.dump(response.json(), out_file, indent=4)

        print(f"  -> Successfully saved to {output_path}")
        count += 1

    except requests.exceptions.RequestException as e:
        print(f"  -> Failed to fetch data for {ticker}: {e}")

    # Respect the SEC rate limit
    time.sleep(0.1)

print("\nDemonstration complete. Check the 'sec_data' directory.")


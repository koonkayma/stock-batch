# Select Direct by API - User Guide

This guide provides instructions for setting up, running, and understanding the logic of the `select_direct_by_api` program.

## 1. Setup and Installation

### Prerequisites
- Python 3.8+
- Active Internet Connection (for API access)

### Environment Configuration
The program requires its configuration to be in a JSON file or set as environment variables.
1. Create or ensure the existence of `/home/kay/workspace/stock-batch/select_direct_by_api/stock_selection_config.json`.
2. Ensure it contains your **Finnhub API Key**:
   ```json
   {
     "FINNHUB_API_KEY": "your_api_key_here"
   }
   ```
3. (Optional) Set up your **SEC User-Agent** (e.g., `Sample Company AdminContact@example.com`) if needed by changing `config.py`.

### Installation
Navigate to the project directory and install the necessary Python libraries:
```bash
cd /home/kay/workspace/stock-batch/select_direct_by_api
pip install -r requirements.txt
```
This will install `requests`, `pandas`, `yfinance`, and `numpy`.

---

## 2. Technical Architecture

### APIs Used
- **SEC EDGAR RESTful API**: Fetches XBRL financial facts (10-K).
- **Finnhub**: Fetches real-time quotes, company profiles, and market cap.
- **yFinance**: Used as a secondary fallback for historical price data.

### Local Data Management
- **Ticker Universe**: Fetches the universe directly from the SEC's public `company-tickers.json` endpoint.
- **Data Compression**: Raw SEC data is stored temporarily in `data/raw/`, then compressed to `.gz` in `data/archive/`.
- **No Database Dependency**: The program does not require any external database tables.

---

## 3. How to Run the Program

### Single Ticker Mode (Diagnostics)
Use this to analyze a specific stock instantly.
```bash
python3 -m src.main --ticker AAPL
```

### Batch Mode (Scanning the Market)
Analyzes all ~10,000+ tickers in the SEC universe.
```bash
python3 -m src.main --batch
```

> [!NOTE]
> **Batch Resume Feature**: If the batch process is interrupted (e.g., connection loss or manual stop), simply run `python3 -m src.main --batch` again. The program detects the `checkpoint.json` file, reads the existing CSV, and automatically skips tickers that have already been processed.

---

## 4. Understanding Outputs and Logs

### Output Files (Batch Mode)
Results are saved to a CSV file in the root directory: `output_YYYYMMDD_HHMMSS.csv`.
- **Growth_Pass**: Boolean (True/False) indicating if the company passed the Growth strategy.
- **Growth_Signal**: Description of why it passed/failed (e.g., "Positive Signal", "Insufficient FCF Persistence").

### Log Files
Logs are located in the `logs/` directory with timestamped names: `execution-YYYY-MM-DD_HH-MM-SS.log`.
- **INFO**: General progress (ticker being processed).
- **WARNING**: Rate limiting backoff or "Insufficient Data" skips.
- **ERROR**: API connection failures or parsing issues.

---

## 5. Stock Selection Logic

### Growth Strategy
- **Core Metric**: Free Cash Flow (FCF) = Operating Cash Flow - CapEx.
- **Logic**: Analyzes the last 5 fiscal years.
- **Threshold**: Requires at least **3 out of 5 years** to be positive.
- **Skip Logic**: If the system finds fewer than 5 years of FCF data (e.g., for recent IPOs), the check is **skipped**, and the stock passes by default to ensure no disqualification due to lack of history.

### Dividend Strategy
- **Solvency**: Checks the Debt-to-Equity (D/E) Ratio.
  - Baseline: Max 1.0
  - Tech: Max 0.5
  - Utilities/Finance: Max 2.0
- **Safety**: Checks the Payout Ratio.
  - Healthy: 35% - 55% (Strong Buy)
  - Potential: 0% - 35%
  - Risky: 55% - 95% (Requires FCF coverage check)
  - Trap: > 95% (Disqualified)

### Turnaround Strategy
- **Inflection**: Checks for **Sequential Improvement** in Operating Margin (EBIT) over the last 3 quarters.
- **Solvency**: Checks for improvement in the Interest Coverage Ratio (moving from <1.5 towards >3.0).
- **Governance**: (Optional) Detects CEO/CFO changes in recent 8-K filings.

### Loss to Earn Strategy (Trough-and-Pivot)
- **Distress**: Must have negative Net Income in at least 4 of the last 6 quarters.
- **Pivot**: The most recent quarter must report a positive Net Income.
- **Clean Profit**: Positive Net Income must be backed by positive Operating Cash Flow.
- **Acceleration**: The rate of growth in Net Income (2nd derivative) must be positive.

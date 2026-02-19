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
Results are saved to a CSV file (`output_YYYYMMDD_HHMMSS.csv`) and specific Markdown reports (e.g., `output_YYYYMMDD_HHMMSS_growth.md`) in the root directory.

#### CSV Columns:
- **Growth_Pass**: True if company passes FCF, CAGR, and Rule of 40.
- **Growth_Signal**: High-level status (e.g., "Strong Growth").
- **Growth_CAGR**: The calculated 5-Year Revenue CAGR.
- **Growth_Rule40**: The Rule of 40 score (CAGR % + FCF Margin %).

#### Markdown Report Columns (Growth):
- **Ticker**
- **Signal**
- **Years Analyzed**
- **Positive Years**
- **Skipped FCF Check?**
- **5-Yr CAGR**
- **Rule of 40**
- **FCF Margin**

#### Markdown Report Columns (Loss to Earn):
- **Ticker**
- **Signal**
- **Distressed Qtrs**
- **Current NI (Q0)**
- **Prev NI (Q1)**
- **Acceleration**

### Log Files
Logs are located in the `logs/` directory with timestamped names: `execution-YYYY-MM-DD_HH-MM-SS.log`.
- **INFO**: General progress (ticker being processed).
- **WARNING**: Rate limiting backoff or "Insufficient Data" skips.
- **ERROR**: API connection failures or parsing issues.

---

## 5. Stock Selection Logic

### Growth Strategy
- **Free Cash Flow (FCF) Persistence**: 
  - Analyzes the last 5 fiscal years.
  - Requires at least **3 out of 5 years** to be positive.
  - **Skip Logic**: If fewer than 5 years of FCF data exist, the check is skipped (passes component).
- **Revenue CAGR**: Requires a 5-Year Revenue Compound Annual Growth Rate strictly greater than **10%**.
- **Rule of 40**: The sum of **Revenue CAGR (%)** and **FCF Margin (%)** must be at least **40**.

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

### Loss to Earn Strategy (Narrowing Losses)
- **Distress**: Must have negative Net Income in at least 4 of the last 6 quarters.
- **Current Distress**: The most recent quarter ($Q_0$) must be negative.
- **Improvement**: Loss must be narrowing ($Q_0 > Q_{-1}$).
- **Acceleration**: The rate of recovery (2nd derivative) must be positive.

---

## 6. Version Control with Git & GitHub

This project uses Git for tracking changes and GitHub for remote collaboration.

### Standard Workflow
1. **Stage Changes**: Prepare your modified files for a commit.
   ```bash
   git add .
   ```
2. **Commit**: Save a snapshot of your changes locally with a descriptive message.
   ```bash
   git commit -m "Describe your changes here"
   ```
3. **Push**: Upload your local commits to the remote repository on GitHub.
   ```bash
   git push origin main
   ```

### Detailed Feature Branch Workflow
Follow this exact procedure to work on a new feature and safely merge it into the main project:

1. **Create and Switch to a New Branch**:
   Start fresh from the current state of `main`.
   ```bash
   git checkout -b feature-branch-name
   ```

2. **Modify and Test**:
   Make your changes to the code (e.g., in `src/strategies/growth.py`).

3. **Stage, Commit, and Push the Feature Branch**:
   Save your work and upload it to GitHub for backup or review.
   ```bash
   git add .
   git commit -m "Detailed message about your changes"
   git push origin feature-branch-name
   ```

4. **Merge into Main**:
   Once you are satisfied with the changes on your feature branch:
   - **Switch back to main**:
     ```bash
     git checkout main
     ```
   - **Merge the feature branch**:
     ```bash
     git merge feature-branch-name
     ```
   - **Push the updated main branch**:
     ```bash
     git push origin main
     ```

5. **Clean Up (Optional)**:
   After the merge is successful, you can delete the local feature branch:
   ```bash
   git branch -d feature-branch-name
   ```

### Safety & Best Practices
- **Security Check**: Never commit files containing secrets (API keys, Personal Access Tokens). The project is configured with a `.gitignore` file to automatically exclude:
  - `stock_selection_config.json` (Your API keys)
  - `*_Chat.txt` (Conversation logs that may contain tokens)
  - `data/` and `logs/` (Large or temporary data files)
- **Blocked Pushes**: If GitHub blocks a push due to "Secret Scanning", do **not** force it. 
  1. Undo your commit: `git reset --soft HEAD~1`.
  2. Remove the sensitive file from your history: `git rm --cached <filename>`.
  3. Ensure the file is in `.gitignore`, then re-commit and push.

---

## 7. Troubleshooting & Fresh Starts

### How to Start from the Beginning
If you want to clear all progress and start a completely fresh batch scan:
1. **Remove the Checkpoint**: Delete `checkpoint.json` in the project root. This forces the program to generate a new output file instead of resuming.
   ```bash
   rm checkpoint.json
   ```
2. **Clean Outputs (Optional)**: If you want to clear previous results:
   ```bash
   rm output_*
   ```
3. **Clear Logs (Optional)**:
   ```bash
   rm logs/*.log
   ```
4. **Re-run the Program**:
   ```bash
   python3 -m src.main --batch
   ```

> [!TIP]
> **Keep Your Data Archive**: You do **not** need to delete `data/archive/` to start a fresh run. Keeping these `.gz` files allows the program to reuse previously fetched SEC data, making the new run significantly faster.

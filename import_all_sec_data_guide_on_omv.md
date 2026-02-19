# SEC Data Import Guide: OpenMediaVault (OMV) Deployment

This guide explains how to set up and run the `import_all_sec_data.py` script on your OMV server (**mopemediavalut**).

## 1. Files to Copy
Copy the following files from your development machine to a folder on OMV (e.g., `~/stock-batch/`):
- `import_all_sec_data.py`
- `tables.sql`
- `check_data_quality.py`

## 2. Install System Dependencies
Since OMV is Debian-based, you need the MariaDB client libraries for the `mariadb` Python package to work. Run these commands in the OMV terminal:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev libmariadb3 libmariadb-dev build-essential
```

## 3. Set Up Python Environment
Create a virtual environment to manage dependencies cleanly:

```bash
cd ~/stock-batch/
python3 -m venv .venv
source .venv/bin/activate
pip install mariadb requests yfinance
```

## 4. Database Setup
Ensure your MariaDB server is running. If you haven't created the tables yet:

```bash
# Replace 'your_user' and 'db_name' with your actual MariaDB credentials
mariadb -u your_user -p db_name < tables.sql
```

## 5. Configuration & Execution

### Configuration
Edit the configuration section at the top of `import_all_sec_data.py` on the OMV server (using `nano` or `vim`):
- `DB_HOST`: Set to your MariaDB IP (likely `localhost` if it's on the same OMV).
- `DB_USER`: Your database username.
- `DB_PASSWORD`: Your database password.
- `DB_NAME`: Your database name.
- `SEC_USER_AGENT`: Update with your project name and email.

### Running the Import
1. **Test with a small limit**:
   ```bash
   source .venv/bin/activate
   python import_all_sec_data.py --limit 5
   ```
2. **Full run** (Note: this can take several hours depending on the number of companies):
   ```bash
   python import_all_sec_data.py
   ```

## 6. Verification
After the import starts or finishes, check the data quality to ensure metrics are being mapped correctly:

```bash
python check_data_quality.py
```

Check the `etl.log` file for detailed logs if any errors occur.

# Guideline: SEC Financial Data Viewer

This document provides instructions on how to set up and run the SEC Financial Data Viewer application.

## Prerequisites

*   Python 3
*   A running MariaDB or MySQL database instance with the `sec_companies` and `sec_financial_reports` tables created (see `tables.sql`).

## 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage the project's dependencies.

To create a virtual environment named `.venv`, run the following command in the project's root directory:

```bash
python3 -m venv .venv
```

## 2. Install Dependencies

Activate the virtual environment and install the required Python packages using the following commands:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
pip install Flask mysql-connector-python
```

## 3. Configure the Database Connection

Open the `app.py` file and modify the `DB_CONFIG` dictionary with your database connection details:

```python
# --- Database Configuration ---
DB_CONFIG = {
    'user': 'your_database_user',
    'password': 'your_database_password',
    'host': 'your_database_host',
    'database': 'your_database_name',
    'port': 3306  # Or your database port
}
```

## 4. Run the Application

Once the dependencies are installed and the database is configured, you can run the application with the following command:

```bash
.venv/bin/python app.py
```

This will start a local web server, and you should see output similar to this:

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
```

## 5. Access the Application

Open your web browser and navigate to the following URL:

[http://127.0.0.1:5001](http://127.0.0.1:5001)

You can now use the application to search for companies and view their financial data.

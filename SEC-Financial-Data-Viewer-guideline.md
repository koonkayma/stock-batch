# Guideline: SEC Financial Data Viewer

This document provides instructions on how to set up and run the SEC Financial Data Viewer application.

## Overview

The SEC Financial Data Viewer is a web application that allows users to search for publicly traded companies and visualize their historical financial data from SEC filings.

The application is built with the following technologies:
*   **Backend:** A Python Flask server that provides a JSON API to query the database.
*   **Frontend:** A dynamic single-page application built with Vue.js and Vite.
*   **Database:** A MariaDB or MySQL database that stores the company and financial report data.

## Prerequisites

*   Python 3
*   Node.js and npm
*   A running MariaDB or MySQL database instance with the `sec_companies` and `sec_financial_reports` tables created (see `tables.sql`).

## 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage the project's Python dependencies.

To create a virtual environment named `.venv`, run the following command in the project's root directory:

```bash
python3 -m venv .venv
```

## 2. Install Backend Dependencies

Activate the virtual environment and install the required Python packages using the following commands:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the dependencies
pip install Flask mysql-connector-python
```

## 3. Install Frontend Dependencies

In a separate terminal, navigate to the `frontend` directory and install the required npm packages:

```bash
cd frontend
npm install
```

## 4. Configure the Database Connection

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

## 5. Run the Application

The application now has two parts that need to be run concurrently: the Flask backend and the Vite frontend development server.

**Terminal 1: Run the Backend**

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate
python app.py
```

**Terminal 2: Run the Frontend**

```bash
cd frontend
npm run dev
```

This will start the Vite development server, typically on port 5173.

## 6. Access the Application

Open your web browser and navigate to the URL provided by the Vite development server (e.g., `http://localhost:5173`).

## 7. Building for Production

To build the frontend for production, run the following command in the `frontend` directory:

```bash
npm run build
```

This will create a `dist` directory with the optimized and bundled assets. The Flask application is configured to serve these static files in a production environment.

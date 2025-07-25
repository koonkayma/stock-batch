from flask import Flask, jsonify, render_template, send_from_directory
import mysql.connector
import os

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')

# --- Database Configuration ---
DB_CONFIG = {
    'user': 'nextcloud',
    'password': 'Ks120909090909#',
    'host': '192.168.1.142',
    'database': 'nextcloud',
    'port': 3306
}

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

@app.route('/api/companies')
def get_companies():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cik, ticker, title FROM sec_companies")
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(companies)

@app.route('/api/financials/<string:cik>')
def get_financials(cik):
    # Pad CIK to 10 digits with leading zeros
    padded_cik = cik.zfill(10)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all columns from sec_financial_reports except identifiers and timestamps
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'nextcloud' 
        AND TABLE_NAME = 'sec_financial_reports'
        AND COLUMN_NAME NOT IN ('cik', 'filing_date', 'form', 'created_at', 'updated_at')
    """)
    columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

    # Fetch the financial data
    query = f"SELECT {', '.join(columns)} FROM sec_financial_reports WHERE cik = %s ORDER BY fiscal_year ASC"
    cursor.execute(query, (padded_cik,))
    financials = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'columns': columns,
        'data': financials
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)

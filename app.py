from flask import Flask, jsonify, render_template, send_from_directory, request
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
    conn = None
    cursor = None
    print("DEBUG: get_companies called.")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT cik, ticker, title FROM sec_companies")
        companies = cursor.fetchall()
        print(f"DEBUG: Fetched {len(companies)} companies.")
        return jsonify(companies)
    except mysql.connector.Error as err:
        print(f"ERROR: MySQL Connector Error in get_companies: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"ERROR: Unexpected error in get_companies: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/financials/<string:cik>')
def get_financials(cik):
    print(f"DEBUG: get_financials called for CIK: {cik}")
    # Pad CIK to 10 digits with leading zeros
    padded_cik = cik.zfill(10)
    print(f"DEBUG: Padded CIK: {padded_cik}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all columns from sec_financial_reports except identifiers and timestamps
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'nextcloud' 
            AND TABLE_NAME = 'sec_financial_reports'
            AND COLUMN_NAME NOT IN ('cik', 'filing_date', 'form', 'created_at', 'updated_at')
        """)
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        # Ensure fiscal_year is always included for charting/table display
        if 'fiscal_year' not in columns:
            columns.insert(0, 'fiscal_year') # Add fiscal_year at the beginning if not present
        print(f"DEBUG: Fetched columns: {columns}")

        # Fetch the financial data
        query = f"SELECT {', '.join(columns)} FROM sec_financial_reports WHERE cik = %s ORDER BY fiscal_year ASC"
        print(f"DEBUG: Executing financial data query: {query} with CIK: {padded_cik}")
        cursor.execute(query, (padded_cik,))
        financials = cursor.fetchall()
        
        return jsonify({
            'columns': columns,
            'data': financials
        })
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Watchlist Endpoints ---
@app.route('/api/watchlists', methods=['GET'])
def get_watchlists():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM watch_list_watchlists")
    watchlists = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(watchlists)

@app.route('/api/watchlists', methods=['POST'])
def create_watchlist():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Watchlist name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watch_list_watchlists (name) VALUES (%s)", (name,))
        conn.commit()
        return jsonify({'message': 'Watchlist created successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Watchlist with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>', methods=['PUT'])
def update_watchlist(watchlist_id):
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Watchlist name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE watch_list_watchlists SET name = %s WHERE id = %s", (name, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify({'message': 'Watchlist updated successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Watchlist with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist(watchlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_watchlists WHERE id = %s", (watchlist_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify({'message': 'Watchlist deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

def get_company_info(ticker):
    conn = None
    cursor = None
    print(f"DEBUG: get_company_info called with ticker: {ticker}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get CIK from sec_companies
        cursor.execute("SELECT cik, title FROM sec_companies WHERE ticker = %s", (ticker,))
        company_info = cursor.fetchone()
        
        if not company_info:
            print(f"DEBUG: Company not found in sec_companies for ticker: {ticker}")
            return None, None # Company not found

        cik = company_info['cik']
        company_name = company_info['title']
        print(f"DEBUG: Found company: {company_name}, CIK: {cik}")

        # Get latest PE ratio from sec_financial_reports
        # Pad CIK to 10 digits with leading zeros for sec_financial_reports table
        padded_cik = str(cik).zfill(10)
        cursor.execute("SELECT price, eps FROM sec_financial_reports WHERE cik = %s ORDER BY fiscal_year DESC LIMIT 1", (padded_cik,))
        financial_data = cursor.fetchone()
        
        latest_pe_ratio = None
        if financial_data and financial_data['price'] is not None and financial_data['eps'] is not None and financial_data['eps'] != 0:
            try:
                latest_pe_ratio = financial_data['price'] / financial_data['eps']
                print(f"DEBUG: Calculated PE Ratio: {latest_pe_ratio}")
            except ZeroDivisionError:
                print(f"DEBUG: ZeroDivisionError when calculating PE ratio for CIK: {cik}")
                latest_pe_ratio = None
        else:
            print(f"DEBUG: No valid price/eps data found for PE ratio calculation for CIK: {cik}")

        return company_name, latest_pe_ratio

    except mysql.connector.Error as err:
        print(f"ERROR: MySQL Connector Error in get_company_info: {err}")
        return None, None
    except Exception as e:
        print(f"ERROR: Unexpected error in get_company_info: {e}")
        return None, None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/company_lookup/<string:ticker>', methods=['GET'])
def company_lookup(ticker):
    company_name, latest_pe_ratio = get_company_info(ticker.upper())
    if company_name:
        return jsonify({'ticker': ticker.upper(), 'company_name': company_name, 'latest_pe_ratio': latest_pe_ratio}), 200
    return jsonify({'error': 'Company not found'}), 404



@app.route('/api/watchlists/<int:watchlist_id>/stocks', methods=['POST'])
def add_stock_to_watchlist(watchlist_id):
    data = request.get_json()
    ticker = data.get('ticker')
    note = data.get('note', '') # Frontend currently doesn't send note

    print(f"DEBUG: add_stock_to_watchlist called for watchlist_id: {watchlist_id}, ticker: {ticker}")

    if not ticker:
        print("DEBUG: Ticker is missing.")
        return jsonify({'error': 'Ticker is required'}), 400

    company_name, latest_pe_ratio = get_company_info(ticker.upper())
    print(f"DEBUG: get_company_info returned company_name: {company_name}, latest_pe_ratio: {latest_pe_ratio}")

    if not company_name:
        print("DEBUG: Company not found by get_company_info.")
        return jsonify({'error': 'Company not found for the given ticker'}), 404

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure latest_pe_ratio is None if it's not a valid number
        if latest_pe_ratio is not None and not isinstance(latest_pe_ratio, (int, float, Decimal)):
            print(f"DEBUG: Invalid latest_pe_ratio type: {type(latest_pe_ratio)}. Setting to None.")
            latest_pe_ratio = None

        cursor.execute(
            "INSERT INTO watch_list_stocks (watchlist_id, ticker, company_name, latest_pe_ratio, note) VALUES (%s, %s, %s, %s, %s)",
            (watchlist_id, ticker.upper(), company_name, latest_pe_ratio, note)
        )
        conn.commit()
        print(f"DEBUG: Stock {ticker} added successfully to watchlist {watchlist_id}.")
        return jsonify({'message': 'Stock added to watchlist successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"ERROR: MySQL Connector Error in add_stock_to_watchlist: {err}")
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Stock already exists in this watchlist'}), 409
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Unexpected error in add_stock_to_watchlist: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>', methods=['PUT'])
def update_watchlist_stock(watchlist_id, stock_id):
    data = request.get_json()
    note = data.get('note', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE watch_list_stocks SET note = %s WHERE id = %s AND watchlist_id = %s", (note, stock_id, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Stock not found in this watchlist'}), 404
        return jsonify({'message': 'Stock note updated successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>', methods=['DELETE'])
def delete_watchlist_stock(watchlist_id, stock_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_stocks WHERE id = %s AND watchlist_id = %s", (stock_id, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Stock not found in this watchlist'}), 404
        return jsonify({'message': 'Stock deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Tag Endpoints ---
@app.route('/api/tags', methods=['GET'])
def get_tags():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM watch_list_tags")
        tags = cursor.fetchall()
        return jsonify(tags)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tags', methods=['POST'])
def create_tag():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Tag name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watch_list_tags (name) VALUES (%s)", (name,))
        conn.commit()
        return jsonify({'message': 'Tag created successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Tag with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_tags WHERE id = %s", (tag_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tag not found'}), 404
        return jsonify({'message': 'Tag deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Stock Tag Endpoints ---
@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>/tags', methods=['POST'])
def assign_tag_to_stock(watchlist_id, stock_id):
    data = request.get_json()
    tag_id = data.get('tag_id')
    if not tag_id:
        return jsonify({'error': 'Tag ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if stock exists in watchlist
        cursor.execute("SELECT id FROM watch_list_stocks WHERE id = %s AND watchlist_id = %s", (stock_id, watchlist_id))
        if not cursor.fetchone():
            return jsonify({'error': 'Stock not found in this watchlist'}), 404

        # Check if tag exists
        cursor.execute("SELECT id FROM watch_list_tags WHERE id = %s", (tag_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Tag not found'}), 404

        cursor.execute("INSERT INTO watch_list_stock_tags (stock_id, tag_id) VALUES (%s, %s)", (stock_id, tag_id))
        conn.commit()
        return jsonify({'message': 'Tag assigned successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Tag already assigned to this stock'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_stock(watchlist_id, stock_id, tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_stock_tags WHERE stock_id = %s AND tag_id = %s", (stock_id, tag_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tag not found for this stock'}), 404
        return jsonify({'message': 'Tag removed successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Modified get_watchlist_stocks for Tag Filtering and Notes Search Endpoint ---
@app.route('/api/watchlists/<int:watchlist_id>/stocks', methods=['GET'])
def get_watchlist_stocks(watchlist_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    tag_id = request.args.get('tag_id', type=int)
    search_query = request.args.get('search_query', type=str)

    query = """
        SELECT
            wls.id, wls.ticker, wls.company_name, wls.latest_pe_ratio, wls.note,
            IFNULL(GROUP_CONCAT(wlt.name SEPARATOR ','), '') AS tags
        FROM
            watch_list_stocks wls
        LEFT JOIN
            watch_list_stock_tags wlst ON wls.id = wlst.stock_id
        LEFT JOIN
            watch_list_tags wlt ON wlst.tag_id = wlt.id
        WHERE
            wls.watchlist_id = %s
    """
    params = [watchlist_id]

    if tag_id:
        query += " AND wls.id IN (SELECT stock_id FROM watch_list_stock_tags WHERE tag_id = %s)"
        params.append(tag_id)

    if search_query:
        query += " AND wls.note LIKE %s"
        params.append(f'%{search_query}%')

    query += " GROUP BY wls.id ORDER BY wls.ticker"

    try:
        cursor.execute(query, tuple(params))
        stocks = cursor.fetchall()
        return jsonify(stocks)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/search_notes', methods=['GET'])
def search_watchlist_notes(watchlist_id):
    search_query = request.args.get('query', type=str)
    if not search_query:
        return jsonify({'error': 'Search query is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, ticker, company_name, note FROM watch_list_stocks WHERE watchlist_id = %s AND note LIKE %s"
        cursor.execute(query, (watchlist_id, f'%{search_query}%'))
        results = cursor.fetchall()
        return jsonify(results)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
        

# --- Watchlist Endpoints ---
@app.route('/api/watchlists', methods=['GET'])
def get_watchlists():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM watch_list_watchlists")
    watchlists = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(watchlists)

@app.route('/api/watchlists', methods=['POST'])
def create_watchlist():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Watchlist name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watch_list_watchlists (name) VALUES (%s)", (name,))
        conn.commit()
        return jsonify({'message': 'Watchlist created successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Watchlist with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>', methods=['PUT'])
def update_watchlist(watchlist_id):
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Watchlist name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE watch_list_watchlists SET name = %s WHERE id = %s", (name, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify({'message': 'Watchlist updated successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Watchlist with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist(watchlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_watchlists WHERE id = %s", (watchlist_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify({'message': 'Watchlist deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

def get_company_info(ticker):
    conn = None
    cursor = None
    print(f"DEBUG: get_company_info called with ticker: {ticker}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get CIK from sec_companies
        cursor.execute("SELECT cik, title FROM sec_companies WHERE ticker = %s", (ticker,))
        company_info = cursor.fetchone()
        
        if not company_info:
            print(f"DEBUG: Company not found in sec_companies for ticker: {ticker}")
            return None, None # Company not found

        cik = company_info['cik']
        company_name = company_info['title']
        print(f"DEBUG: Found company: {company_name}, CIK: {cik}")

        # Get latest PE ratio from sec_financial_reports
        # Pad CIK to 10 digits with leading zeros for sec_financial_reports table
        padded_cik = str(cik).zfill(10)
        cursor.execute("SELECT price, eps FROM sec_financial_reports WHERE cik = %s ORDER BY fiscal_year DESC LIMIT 1", (padded_cik,))
        financial_data = cursor.fetchone()
        
        latest_pe_ratio = None
        if financial_data and financial_data['price'] is not None and financial_data['eps'] is not None and financial_data['eps'] != 0:
            try:
                latest_pe_ratio = financial_data['price'] / financial_data['eps']
                print(f"DEBUG: Calculated PE Ratio: {latest_pe_ratio}")
            except ZeroDivisionError:
                print(f"DEBUG: ZeroDivisionError when calculating PE ratio for CIK: {cik}")
                latest_pe_ratio = None
        else:
            print(f"DEBUG: No valid price/eps data found for PE ratio calculation for CIK: {cik}")

        return company_name, latest_pe_ratio

    except mysql.connector.Error as err:
        print(f"ERROR: MySQL Connector Error in get_company_info: {err}")
        return None, None
    except Exception as e:
        print(f"ERROR: Unexpected error in get_company_info: {e}")
        return None, None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/company_lookup/<string:ticker>', methods=['GET'])
def company_lookup(ticker):
    company_name, latest_pe_ratio = get_company_info(ticker.upper())
    if company_name:
        return jsonify({'ticker': ticker.upper(), 'company_name': company_name, 'latest_pe_ratio': latest_pe_ratio}), 200
    return jsonify({'error': 'Company not found'}), 404



@app.route('/api/watchlists/<int:watchlist_id>/stocks', methods=['POST'])
def add_stock_to_watchlist(watchlist_id):
    data = request.get_json()
    ticker = data.get('ticker')
    note = data.get('note', '') # Frontend currently doesn't send note

    print(f"DEBUG: add_stock_to_watchlist called for watchlist_id: {watchlist_id}, ticker: {ticker}")

    if not ticker:
        print("DEBUG: Ticker is missing.")
        return jsonify({'error': 'Ticker is required'}), 400

    company_name, latest_pe_ratio = get_company_info(ticker.upper())
    print(f"DEBUG: get_company_info returned company_name: {company_name}, latest_pe_ratio: {latest_pe_ratio}")

    if not company_name:
        print("DEBUG: Company not found by get_company_info.")
        return jsonify({'error': 'Company not found for the given ticker'}), 404

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure latest_pe_ratio is None if it's not a valid number
        if latest_pe_ratio is not None and not isinstance(latest_pe_ratio, (int, float, Decimal)):
            print(f"DEBUG: Invalid latest_pe_ratio type: {type(latest_pe_ratio)}. Setting to None.")
            latest_pe_ratio = None

        cursor.execute(
            "INSERT INTO watch_list_stocks (watchlist_id, ticker, company_name, latest_pe_ratio, note) VALUES (%s, %s, %s, %s, %s)",
            (watchlist_id, ticker.upper(), company_name, latest_pe_ratio, note)
        )
        conn.commit()
        print(f"DEBUG: Stock {ticker} added successfully to watchlist {watchlist_id}.")
        return jsonify({'message': 'Stock added to watchlist successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"ERROR: MySQL Connector Error in add_stock_to_watchlist: {err}")
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Stock already exists in this watchlist'}), 409
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Unexpected error in add_stock_to_watchlist: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>', methods=['PUT'])
def update_watchlist_stock(watchlist_id, stock_id):
    data = request.get_json()
    note = data.get('note', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE watch_list_stocks SET note = %s WHERE id = %s AND watchlist_id = %s", (note, stock_id, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Stock not found in this watchlist'}), 404
        return jsonify({'message': 'Stock note updated successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>', methods=['DELETE'])
def delete_watchlist_stock(watchlist_id, stock_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_stocks WHERE id = %s AND watchlist_id = %s", (stock_id, watchlist_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Stock not found in this watchlist'}), 404
        return jsonify({'message': 'Stock deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Tag Endpoints ---
@app.route('/api/tags', methods=['GET'])
def get_tags():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM watch_list_tags")
        tags = cursor.fetchall()
        return jsonify(tags)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tags', methods=['POST'])
def create_tag():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Tag name is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watch_list_tags (name) VALUES (%s)", (name,))
        conn.commit()
        return jsonify({'message': 'Tag created successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Tag with this name already exists'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_tags WHERE id = %s", (tag_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tag not found'}), 404
        return jsonify({'message': 'Tag deleted successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Stock Tag Endpoints ---
@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>/tags', methods=['POST'])
def assign_tag_to_stock(watchlist_id, stock_id):
    data = request.get_json()
    tag_id = data.get('tag_id')
    if not tag_id:
        return jsonify({'error': 'Tag ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if stock exists in watchlist
        cursor.execute("SELECT id FROM watch_list_stocks WHERE id = %s AND watchlist_id = %s", (stock_id, watchlist_id))
        if not cursor.fetchone():
            return jsonify({'error': 'Stock not found in this watchlist'}), 404

        # Check if tag exists
        cursor.execute("SELECT id FROM watch_list_tags WHERE id = %s", (tag_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Tag not found'}), 404

        cursor.execute("INSERT INTO watch_list_stock_tags (stock_id, tag_id) VALUES (%s, %s)", (stock_id, tag_id))
        conn.commit()
        return jsonify({'message': 'Tag assigned successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062: # Duplicate entry
            return jsonify({'error': 'Tag already assigned to this stock'}), 409
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/<int:stock_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_stock(watchlist_id, stock_id, tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watch_list_stock_tags WHERE stock_id = %s AND tag_id = %s", (stock_id, tag_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tag not found for this stock'}), 404
        return jsonify({'message': 'Tag removed successfully'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Modified get_watchlist_stocks for Tag Filtering and Notes Search Endpoint ---
@app.route('/api/watchlists/<int:watchlist_id>/stocks', methods=['GET'])
def get_watchlist_stocks(watchlist_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    tag_id = request.args.get('tag_id', type=int)
    search_query = request.args.get('search_query', type=str)

    query = """
        SELECT
            wls.id, wls.ticker, wls.company_name, wls.latest_pe_ratio, wls.note,
            GROUP_CONCAT(wlt.name SEPARATOR ',') AS tags
        FROM
            watch_list_stocks wls
        LEFT JOIN
            watch_list_stock_tags wlst ON wls.id = wlst.stock_id
        LEFT JOIN
            watch_list_tags wlt ON wlst.tag_id = wlt.id
        WHERE
            wls.watchlist_id = %s
    """
    params = [watchlist_id]

    if tag_id:
        query += " AND wls.id IN (SELECT stock_id FROM watch_list_stock_tags WHERE tag_id = %s)"
        params.append(tag_id)

    if search_query:
        query += " AND wls.note LIKE %s"
        params.append(f'%{search_query}%')

    query += " GROUP BY wls.id ORDER BY wls.ticker"

    try:
        cursor.execute(query, tuple(params))
        stocks = cursor.fetchall()
        return jsonify(stocks)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/watchlists/<int:watchlist_id>/stocks/search_notes', methods=['GET'])
def search_watchlist_notes(watchlist_id):
    search_query = request.args.get('query', type=str)
    if not search_query:
        return jsonify({'error': 'Search query is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, ticker, company_name, note FROM watch_list_stocks WHERE watchlist_id = %s AND note LIKE %s"
        cursor.execute(query, (watchlist_id, f'%{search_query}%'))
        results = cursor.fetchall()
        return jsonify(results)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)

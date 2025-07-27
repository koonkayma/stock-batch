import mysql.connector
import sys
import os

# --- Database Configuration (from app.py) ---
DB_CONFIG = {
    'user': 'nextcloud',
    'password': 'Ks120909090909#',
    'host': '192.168.1.142',
    'database': 'nextcloud',
    'port': 3306
}

def execute_query(query):
    """
    Connects to the database, executes the given query,
    and prints the results.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG, ssl_disabled=True)
        cursor = conn.cursor(dictionary=True)
        
        print(f"Executing query: {query}")
        
        cursor.execute(query)
        
        # For SELECT statements, fetch and print results
        if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('WITH'):
            results = cursor.fetchall()
            if results:
                print("Query results:")
                for row in results:
                    print(row)
            else:
                print("Query returned no results.")
        # For other statements (INSERT, UPDATE, DELETE, etc.), commit and show row count
        else:
            conn.commit()
            print(f"Query successful. Rows affected: {cursor.rowcount}")
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Connection closed.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sql_query = sys.argv[1]
        execute_query(sql_query)
    else:
        print("Usage: python db_executor.py \"<your_sql_query>\"")
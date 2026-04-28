from flask import g, current_app
from mysql.connector import pooling

# 1. Database Configuration
dbconfig = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_monitoring',
    'port': 3307,
    'use_pure': True
}

global_pool = None

def init_db_pool():
    """Attempts to create the database pool."""
    global global_pool
    try:
        current_app.logger.info("Creating database connection pool...")
        global_pool = pooling.MySQLConnectionPool(
            pool_name="main_entry_exit", 
            pool_size=20, 
            autocommit=True, 
            **dbconfig
        )
        current_app.logger.info("Database connection pool created.")
        return True
    except Exception as err:
        current_app.logger.critical(f"CRITICAL ERROR: Could not connect to MySQL database. Details: {err}")
        global_pool = None
        return False

def connect_db():
    """Gets a connection, retrying pool creation if it failed previously."""
    if 'db' not in g:        
        # AUTO-REBOOT LOGIC
        if global_pool is None:
            current_app.logger.warning("Pool is offline. Attempting auto-reconnect...")
            init_db_pool()

        if global_pool is None:
            g.db = None 
        else:
            try:
                g.db = global_pool.get_connection()
            except Exception as err:
                current_app.logger.error(f"Pool exhausted or connection error: {err}")
                g.db = None
    return g.db

def get_employee_dashboard_stats():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    
    # 1. Currently Inside (Live Tracking)
    cursor.execute("SELECT COUNT(*) as count FROM event_log WHERE time_out IS NULL AND date = CURDATE()")
    live = cursor.fetchone()['count']
    
    # 2. Avg Stay Duration (Hours)
    cursor.execute("SELECT AVG(TIMESTAMPDIFF(HOUR, time_in, time_out)) as avg_stay FROM event_log WHERE time_out IS NOT NULL")
    stay = cursor.fetchone()['avg_stay'] or 0.0
    
    # 3. Peak Entry Hour
    cursor.execute("""
        SELECT HOUR(time_in) as hr, COUNT(*) as count 
        FROM event_log GROUP BY hr ORDER BY count DESC LIMIT 1
    """)
    peak_data = cursor.fetchone()
    peak = f"{peak_data['hr']}:00" if peak_data else "N/A"
    
    return {"live": live, "stay": round(stay, 1), "peak": peak}

def close_db(error=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
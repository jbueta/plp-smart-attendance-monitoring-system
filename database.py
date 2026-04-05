from flask import g, current_app
from mysql.connector import pooling

# 1. Database Configuration
dbconfig = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_monitoring',
    'port': 3306,
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

def close_db(error=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
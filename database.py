from flask import current_app, g
from mysql.connector import pooling

from config import get_config

config = get_config()

dbconfig = {
    "host": config.DB_HOST,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
    "database": config.DB_NAME,
    "port": config.DB_PORT,
    "use_pure": True,
}

global_pool = None

def init_db_pool():
    """Attempts to create the database pool."""
    global global_pool
    try:
        current_app.logger.info("Creating database connection pool...")
        global_pool = pooling.MySQLConnectionPool(
            pool_name="main_entry_exit",
            pool_size=config.DB_POOL_SIZE,
            autocommit=config.DB_AUTOCOMMIT,
            **dbconfig,
        )
        current_app.logger.info("Database connection pool created.")
        return True
    except Exception as err:
        current_app.logger.critical(f"CRITICAL ERROR: Could not connect to MySQL database. Details: {err}")
        global_pool = None
        return False

def connect_db():
    """Gets a connection, retrying pool creation if it failed previously."""
    if "db" not in g:
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
    db = g.pop("db", None)
    if db is not None:
        db.close()

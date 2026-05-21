import mysql.connector
from config import get_config

config = get_config()
try:
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute("DESCRIBE bulletins")
    columns = [c[0] for c in cursor.fetchall()]
    print(f"Columns: {columns}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")

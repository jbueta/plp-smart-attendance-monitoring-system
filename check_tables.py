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
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    if 'bulletins' not in tables:
        print("Missing table: bulletins")
    if 'paging_alerts' not in tables:
        print("Missing table: paging_alerts")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")

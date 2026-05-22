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
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT event_id FROM events LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"ID: {row['event_id']}")
    else:
        print("No events")
    conn.close()
except Exception as e:
    print(f"Error: {e}")

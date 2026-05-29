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
    
    print("Checking if 'student_type' column exists...")
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'students'
          AND COLUMN_NAME = 'student_type'
    """)
    row = cursor.fetchone()
    column_exists = row[0] if row else 0
    
    if not column_exists:
        print("Column 'student_type' does not exist. Adding it...")
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN student_type ENUM('Regular', 'Irregular') NOT NULL DEFAULT 'Regular' AFTER student_name
        """)
        conn.commit()
        print("Successfully added 'student_type' column!")
    else:
        print("Column 'student_type' already exists.")
        
    conn.close()
except Exception as e:
    print(f"Error migrating database: {e}")

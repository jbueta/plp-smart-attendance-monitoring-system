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
    
    # 1. Check total number of users and students
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    print(f"Total Users: {cursor.fetchone()['total_users']}")
    
    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    print(f"Total Students: {cursor.fetchone()['total_students']}")
    
    cursor.execute("SELECT COUNT(*) AS active_users FROM users WHERE active = 1")
    print(f"Total Active Users: {cursor.fetchone()['active_users']}")
    
    cursor.execute("SELECT COUNT(*) AS active_students FROM students s JOIN users u ON s.user_id = u.user_id WHERE u.active = 1")
    print(f"Total Active Students: {cursor.fetchone()['active_students']}")

    # 2. Get some sample student details
    cursor.execute("""
        SELECT s.student_id, s.student_name, u.active, u.role, s.student_type, s.status
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        LIMIT 10
    """)
    rows = cursor.fetchall()
    print("\nSample Student Records:")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")

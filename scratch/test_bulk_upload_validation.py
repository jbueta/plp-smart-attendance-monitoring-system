import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from app import app, validate_student_upload_rows
from database import init_db_pool, connect_db

with app.app_context():
    init_db_pool()
    conn = connect_db()
    try:
        # Case 1: Valid regular student type
        print("\n--- Test 1: Valid Student Type (regular) ---")
        rows = [{
            "row_number": 1,
            "student_id": "99-99991",
            "student_name": "Regular Student",
            "course_name": "BS Information Technology",
            "course_id": "",
            "status": "Outside",
            "student_type": "regular",
        }]
        result = validate_student_upload_rows(conn, rows)
        print("Success:", result["success"])
        print("Errors:", result["errors"])
        print("Valid Rows:", len(result["valid_rows"]))

        # Case 2: Missing student type
        print("\n--- Test 2: Missing Student Type ---")
        rows = [{
            "row_number": 2,
            "student_id": "99-99992",
            "student_name": "Missing Type Student",
            "course_name": "BS Information Technology",
            "course_id": "",
            "status": "Outside",
            "student_type": "", # Missing!
        }]
        result = validate_student_upload_rows(conn, rows)
        print("Success:", result["success"])
        print("Errors:", result["errors"])
        print("Valid Rows:", len(result["valid_rows"]))

        # Case 3: Invalid student type
        print("\n--- Test 3: Invalid Student Type (guest) ---")
        rows = [{
            "row_number": 3,
            "student_id": "99-99993",
            "student_name": "Invalid Type Student",
            "course_name": "BS Information Technology",
            "course_id": "",
            "status": "Outside",
            "student_type": "guest", # Invalid!
        }]
        result = validate_student_upload_rows(conn, rows)
        print("Success:", result["success"])
        print("Errors:", result["errors"])
        print("Valid Rows:", len(result["valid_rows"]))

    finally:
        if conn:
            conn.close()

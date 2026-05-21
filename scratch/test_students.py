import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from app import app, fetch_admin_students_page_data
from database import init_db_pool

with app.app_context():
    init_db_pool()
    try:
        print("Testing fetch_admin_students_page_data...")
        logs, records, course_options = fetch_admin_students_page_data()
        print(f"Success! Logs: {len(logs)}, Records: {len(records)}, Courses: {len(course_options)}")
    except Exception as e:
        import traceback
        traceback.print_exc()

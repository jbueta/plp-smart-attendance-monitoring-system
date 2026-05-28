import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from app import app

with app.app_context():
    print("Listing all routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    print("\nChecking critical student routes:")
    critical_routes = [
        "admin_students",
        "download_student_upload_template",
        "get_courses",
        "add_student_manual",
        "upload_students_preview",
        "upload_students_commit",
        "update_student",
        "delete_student"
    ]
    for route in critical_routes:
        if route in app.view_functions:
            print(f"✓ {route} is defined")
        else:
            print(f"✗ {route} is MISSING")

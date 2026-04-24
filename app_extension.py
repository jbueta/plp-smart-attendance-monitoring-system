
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, request, g
from datetime import date, timedelta, datetime

from db_connect import Database
from database import init_db_pool, connect_db, close_db

import json
import os
import logging
import mysql.connector as connector
from mysql.connector import pooling
from flask_cors import CORS
from functools import wraps
import jwt  #token based authentication

JWT_SECRET = 'plp_jwt_secret_key_2026'  # Secret key for JWT (to be changed)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(hours=8)  # Token valid for 8 hours
        
app = Flask(__name__)
app.secret_key = 'plp_secure_key_2026'  # Required for session management

app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(logging.StreamHandler())
app.logger.addHandler(logging.FileHandler('logs/app.log'))

allowed_origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://192.168.1.3:5000"
]

CORS(app, origins=allowed_origins)

# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

with app.app_context():
    init_db_pool()

app.teardown_appcontext(close_db)


# ==============================================================================
# ADMIN AUTHENTICATION
# ==============================================================================

@app.route('/admin/login/auth', methods=['POST'])
def login():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            # Mock login for dev (no DB)
            data = request.get_json()
            if data and data.get('username') == 'admin' and data.get('password') == 'admin':
                return jsonify({"success": True, "message": "Mock auth success (DB offline)", "data": {"username": "admin", "role": "Administrator"}}), 200
            else:
                return jsonify({"success": False, "message": "Mock DB offline - use admin/admin"}), 500

        data = request.get_json()
        required_fields = ["username", "password"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        username = data['username']
        password = data['password']

        params = (username, password)
        db = Database(conn, params)
        result = db.admin_login()

        if not result or len(result) == 0:
            return jsonify({"success": False, "message": "Incorrect username or password."}), 200

        return jsonify({"success": True, "message": "Authentication successful", "data": result}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/user/authentication', methods=['POST'])
def user_authenticate():
    conn = None
    try:
        print("Authenticating...")
        data = request.get_json()
        print(data)

        if not data or not data.get('id'):
            return jsonify({"error": "ID is required. No ID string attached"}), 400
        
        scan_id = data.get('id')
        
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. AUTHENTICATE
        db = Database(conn, (scan_id, scan_id, scan_id))
        result = db.authenticate_user()

        if not result or len(result) == 0:
            return jsonify({"Invalid": "Invalid ID!"}), 404

        # 2. GET USER DATA
        user_data = result[0]
        user_id = user_data['user_id']
        role = user_data['role']
        current_status = user_data['current_status']

        full_name = user_data.get('full_name', 'Unknown User')
        affiliation = user_data.get('affiliation', 'N/A')

        print(f"User found: ID {user_id}, Role: {role}, Status: {current_status}")

        # 3. CHANGE STATUS
        db_status_param = (user_id, current_status, role)
        db_status = Database(conn, db_status_param)
        
        db_status_result = db_status.change_status()
        if not db_status_result:
            return jsonify({"success": False, "message": "Failed to update user status in database."}), 500

        new_status = db_status_result['new_status']
        log_type = 'Entry' if new_status == 'Inside' else 'Exit'
        gate = 'Gate 1' if new_status == 'Inside' else 'Gate 2'    

        violation = db_status_result.get('forgot_to_timeout', False)

        # ==========================================
        # SMTP: EMAILING MODULE FOR VIOLATION (optional)
        # ==========================================
        if violation:
            # Code goes through here
            pass            

        # 4. INSERT LOG
        log_params = (user_id, formatted_time, log_type, gate)
        db_insert_log = Database(conn, log_params)
        
        print(f"Inserting {log_type} log...")
        db_insert_log_result = db_insert_log.insert_general_log()
        
        if not db_insert_log_result:
            return jsonify({"success": False, "message": "Status changed, but failed to insert log."}), 500

        return jsonify({
            "success": True, 
            "message": f"User authenticated. Status updated to {new_status}.", 
            "status": "found",
            "attendance_status": log_type,
            "name": full_name,
            "affiliation": affiliation,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error during authentication: {str(e)}"}), 500
    
    


# ==============================================================================
# EVENTS ENDPOINT
# ==============================================================================

@app.route('/admin/dashboard/add-events', methods=['POST'])
def add_events():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500  

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        required_fields = ['event_name', 'event_type', 'frequency', 'location', 'event_date', 'time_start', 'time_end', 'participants_type']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"success": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        participants_type = data.get('participants_type')
        participants = None
        match (participants_type):
            case 'grouped':
                participants = data.get('grouped_participants')
                if not participants:
                    return jsonify({"success": False, "error": "Participants are required"}), 400
            case 'custom':
                participants = data.get('custom_participants')
                if not participants:
                    return jsonify({"success": False, "error": "Participants are required"}), 400
            case 'hybrid':
                participants = {"grouped_participants": data.get('grouped_participants') or [], 
                                "custom_participants": data.get('custom_participants') or []
                               }
                if not participants["grouped_participants"] and not participants["custom_participants"]:
                    return jsonify({"success": False, "error": "At least one participant type is required for hybrid"}), 400
            case _:
                return jsonify({"success": False, "error": "Invalid participants type"}), 400

        ed = data.get('event_date')
        cd = date.today()

        try:
            event_date = datetime.strptime(ed, '%Y-%m-%d').date()
            current_date = cd
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
        if event_date < current_date:
            return jsonify({"success": False, "error": "Event Date cannot be in the past"}), 400

        frequency = data.get('frequency')
        if frequency == 'WEEKLY':
            day = data.get('day')
            if not day:
                return jsonify({"success": False, "error": "Day is required"}), 400
            
        event_name = data.get('event_name')
        event_type = data.get('event_type')
        day = data.get('day')
        event_date = data.get('event_date')
        time_start = data.get('time_start')
        time_end = data.get('time_end')
        location = data.get('location')

        db = Database(conn, (event_name, event_type, frequency, day, event_date, time_start, time_end, location, participants, participants_type))
        db_result = db.add_event()
        
        if not db_result or db_result.get('success') is False:
            error_msg = db_result.get('message', 'Error adding event') if db_result else 'Unknown database error'
            return jsonify({"success": False, "message": error_msg}), 400
        
        events = db.get_all_events()
        return jsonify({"success": True, 
                        "message": f"Event '{event_name}' added successfully",
                        "data": events
                       }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error adding event: {str(e)}"}), 500
    


# ==========================================
# ENDPOINT 1: The Weekly Instance Generator (Triggered by Cron Every Sunday)

@app.route("/admin/generate-daily-instances", methods=["POST"])
def generate_daily_instances():
    """
    Triggered every Sunday at midnight by a cron job or cloud scheduler.
    Generates instances for the upcoming 7 days including:
    - WEEKLY events for their scheduled days
    - DAILY events for every day
    - ONCE events on their scheduled date
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        today = date.today()
        upcoming_week = [today + timedelta(days=i) for i in range(7)]
        
        created_count = 0
        failed_count = 0

        for target_date in upcoming_week:
            day_name = target_date.strftime("%A")
            
            cursor = conn.cursor(dictionary=True)
            
            # Get all active events matching this day
            # WEEKLY events: match day name and event_date <= target_date
            # DAILY events: all active daily events
            # ONCE events: event_date == target_date
            query = """
                SELECT event_id, event_name, frequency, event_date
                FROM events
                WHERE active = 1 AND (
                    (frequency = 'WEEKLY' AND day = %s AND event_date <= %s) OR
                    (frequency = 'DAILY' AND event_date <= %s) OR
                    (frequency = 'ONCE' AND event_date = %s)
                )
            """
            cursor.execute(query, (day_name, target_date, target_date, target_date))
            events = cursor.fetchall()
            
            for event in events:
                event_id = event['event_id']
                new_db = Database(conn, (event_id, target_date))
                instance_result = new_db.add_event_instances()
                
                if instance_result.get('success'):
                    created_count += 1
                else:
                    failed_count += 1
                    print(f"Failed to add instance for Event {event_id} on {target_date}: {instance_result.get('message')}")
        
        return jsonify({
            "success": True,
            "message": f"Daily instances generated for the upcoming week",
            "created": created_count,
            "failed": failed_count,
            "date_range": f"{today} to {upcoming_week[-1]}"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

# ==========================================
# ENDPOINT 2: The Gate Swipe Webhook
# ==========================================
@app.route("/api/events/authentication", methods=["POST"])
def events_authentication():
    """
    Triggered by the hardware gate when a user swipes their ID.
    Logs the raw data AND updates their attendance status.
    """
    data = request.get_json()
    
    required_fields = ["user_id", "event_id"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400
        
    user_id = data['user_id']
    event_id = data['event_id']

    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500
        
        params = (user_id, event_id)
        obj = Database(conn, params)
        last_log = obj.check_last_swipe()

        if isinstance(last_log, dict) and last_log.get('success') is False:
            return jsonify({"success": False, "message": last_log['message']}), 500

        if not last_log or last_log.get('log_type') == 'Exit':
            log_type = 'Entry'
        else:
            log_type = 'Exit'

        insert_params = (user_id, event_id, log_type)
        db = Database(conn, insert_params)
        event_log_insert = db.events_authentication()

        if not event_log_insert or event_log_insert.get('success') is False:
            return jsonify({"success": False, "message": event_log_insert.get('message', 'Unknown Error')}), 500

        return jsonify({"success": True, "message": "Swipe logged and attendance updated."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

# ====================================================
# ENDPOINT 3: Status Update for Excused Individuals
# ====================================================
@app.route("/admin/update-attendance", methods=["PUT"])
def update_attendance():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        data = request.get_json()
        required_fields = ["user_id", "instance_id", "status"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        user_id = data['user_id']
        instance_id = data['instance_id']
        status = data['status'] 
        remarks = data.get('remarks', None)

        if status not in ['Present', 'Absent', 'Late', 'Excused']:
            return jsonify({"success": False, "message": "Invalid status option"}), 400

        params = (status, remarks, user_id, instance_id)
        db = Database(conn, params)
        result = db.update_attendance_status()

        if not result or result.get('success') is False:
            return jsonify({"success": False, "message": result.get('message', 'Error updating status')}), 500

        return jsonify({"success": True, 
                        "message": f"Attendance updated to {status}."
                       }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ====================================================
# ENDPOINT 4: Update Event Status (Completed or Cancelled)
# ====================================================
@app.route("/admin/events/update-status", methods=["PUT"])
def update_event_status():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        data = request.get_json()
        required_fields = ["instance_id", "new_status"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        instance_id = data['instance_id']
        status = data['new_status'] 

        if status not in ['Scheduled','Completed','Cancelled']:
            return jsonify({"success": False, "message": "Invalid status option"}), 400

        params = (status, instance_id)
        db = Database(conn, params)
        result = db.update_instance_status()

        if not result or result.get('success') is False:
            return jsonify({"success": False, "message": result.get('message', 'Error updating status')}), 500

        events = db.get_all_events()
        return jsonify({"success": True, 
                        "message": f"Event status updated to {status}.",
                        "data": events.get('data')
                      }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ====================================================
# ENDPOINT 5: Delete an event (soft deletion, UI controlled)
# ====================================================
@app.route("/admin/events/delete-event", methods=["PUT"])
def delete_event():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        data = request.get_json()
        required_fields = ["event_id"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        event_id = data['event_id']

        if isinstance(event_id, str):
            pass
        else:
            return jsonify({"success": False, "message": "Invalid event ID"}), 400

        params = (event_id,)
        db = Database(conn, params)
        result = db.delete_event()

        if not result or result.get('success') is False:
            print(result)
            return jsonify({"success": False, "message": result.get('message', 'Error deleting event')}), 500

        return jsonify({"success": True, 
                        "message": f"Event deleted successfully."
                      }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ====================================================
# ENDPOINT 6: Delete an event (soft deletion, UI controlled)
# ====================================================
@app.route("/admin/events/delete-events", methods=["PUT"])
def delete_bulk_event():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        data = request.get_json()
        event_ids = data.get('event_ids', [])

        valid_ids = [str(eid) for eid in event_ids if int(eid) > 2]

        if not valid_ids:
            return jsonify({'success': False, 'message': 'Cannot delete default system events.'}), 403

        params = (valid_ids,)
        db = Database(conn, params)
        result = db.delete_bulk_events()

        if not result or result.get('success') is False:
            print(result)
            return jsonify({"success": False, "message": result.get('message', 'Error deleting event')}), 500

        return jsonify({"success": True, 
                        "message": f"Event deleted successfully."
                      }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================================================================
# LIVE DATA GETTER FUNCTIONS
# ==============================================================================

@app.route("/kiosk/employee/select-event", methods=["GET"])
def kiosk_live_events():
    """
        Fetches events scheduled on the same day.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        events = Database.get_events_kiosk(conn)
        
        if events is None:
            return jsonify({"success": False, "message": "Error fetching scheduled events"}), 500
            
        print(events)
        return jsonify({"success": True, "events": events}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route("/api/reports/all-events", methods=["GET"])
def reports_all_events():
    """
        Fetches all scheduled events for reports dropdown (Detailed Report Type).
        Returns all events regardless of date or active status.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        events = Database.get_all_events_for_reports(conn)
        
        if events is None:
            return jsonify({"success": False, "message": "Error fetching scheduled events"}), 500
            
        return jsonify({"success": True, "events": events}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route("/admin/dashboard/events", methods=["GET"])
def admin_dashboard_events():
    """
        Fetches events.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        events = Database.get_events_dashboard(conn)

        if events is None:
            return jsonify({"success": False, "message": "Error fetching events"}), 500

        return jsonify({"success": True, "events": events}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    


@app.route("/kiosk/students/student-logs", methods=["GET"])
def live_student_logs():
    """
        Fetches recent student logs in current day.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        logs = Database.get_student_logs(conn)

        if logs is None:
            return jsonify({"success": False, "message": "Error fetching student_logs"}), 500

        return jsonify({"success": True, "logs": logs}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    


@app.route("/admin/dashboard/events/live-departments", methods=["GET"])
def live_departments():
    """
        Fetches departments registered in the database.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        depts = Database.get_admin_departments(conn)

        if depts is None:
            return jsonify({"success": False, "message": "Error fetching departments"}), 500

        return jsonify({"success": True, "departments": depts}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/departments", methods=["GET"])
def get_all_departments():
    """
    Fetches all departments from the departments table for filtering.
    Returns: [{"id": 1, "name": "College of Electrical Engineering"}, ...]
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        cursor = conn.cursor(dictionary=True)
        query = "SELECT department_id as id, department_name as name FROM departments ORDER BY department_name ASC"
        cursor.execute(query)
        departments = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success": True,
            "departments": departments
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route("/admin/instances/<int:instance_id>/get-attendance", methods=["GET"])
def get_instance_attendance(instance_id):
    """
    Fetches the complete roster for a specific event date (instance_id),
    including user names, IDs, and attendance statuses.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify([]), 500

        roster = Database.get_instance_attendance(conn, instance_id)

        if roster is None:
            return jsonify([]), 500

        return jsonify(roster), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify([]), 500
    


@app.route("/admin/event/<int:event_id>/instances", methods=["GET"])
def get_event_instances(event_id):
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify([]), 500

        events = Database.get_event_instances(conn, event_id)

        return jsonify(events), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify([]), 500

@app.route("/admin/dashboard/analytics/overall", methods=["GET"])
def dashboard_overall_stats():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        stats = Database.get_overall_dashboard_stats(conn)
        if stats is None:
            return jsonify({"success": False, "message": "Error fetching stats"}), 500

        return jsonify({"success": True, "data": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/dashboard/analytics/students", methods=["GET"])
def dashboard_student_stats():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        stats = Database.get_student_dashboard_stats(conn)
        if stats is None:
            return jsonify({"success": False, "message": "Error fetching student stats"}), 500

        return jsonify({"success": True, "data": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/dashboard/analytics/employees", methods=["GET"])
def dashboard_employee_stats():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        stats = Database.get_employee_dashboard_stats(conn)
        if stats is None:
            return jsonify({"success": False, "message": "Error fetching employee stats"}), 500

        return jsonify({"success": True, "data": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================================================================
# NEW ENDPOINT – MANUAL EVENT ENTRY
# ==============================================================================
@app.route("/api/events/manual_entry", methods=["POST"])
def manual_event_entry():
    """
    Accepts employee_id and event_id, logs attendance for the event.
    Also toggles the general status (Inside/Outside) and inserts a record in general_log.
    Returns user details and the new log entry for live feed update.
    """
    conn = None
    try:
        data = request.get_json()
        if not data or 'employee_id' not in data or 'event_id' not in data:
            return jsonify({"success": False, "message": "Missing employee_id or event_id"}), 400

        employee_id = data['employee_id']
        event_id = data['event_id']

        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        cursor = conn.cursor(dictionary=True)

        # 1. Look up user_id from employee_id
        query = """
            SELECT u.user_id, u.role, e.employee_name, d.department_name as department
            FROM users u
            JOIN employees e ON u.user_id = e.user_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE e.employee_id = %s
        """
        cursor.execute(query, (employee_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "message": "Employee ID not found"}), 404

        user_id = user['user_id']
        employee_name = user['employee_name']
        department = user['department'] or 'N/A'

        # 2. Determine entry or exit based on last swipe for this event today
        params = (user_id, event_id)
        db = Database(conn, params)
        last_log = db.check_last_swipe()

        if isinstance(last_log, dict) and last_log.get('success') is False:
            return jsonify({"success": False, "message": last_log['message']}), 500

        if not last_log or last_log.get('log_type') == 'Exit':
            log_type = 'Entry'
        else:
            log_type = 'Exit'

        # 3. Insert event log and update event attendance
        insert_params = (user_id, event_id, log_type)
        db2 = Database(conn, insert_params)
        result = db2.events_authentication()

        if not result or result.get('success') is False:
            return jsonify({"success": False, "message": result.get('message', 'Unknown error')}), 500

        # 4. Retrieve attendance with pre‑formatted times
        cursor.execute("""
            SELECT ea.status, 
                   DATE_FORMAT(ea.first_in, '%h:%i %p') as first_in_formatted,
                   DATE_FORMAT(ea.last_out, '%h:%i %p') as last_out_formatted
            FROM event_attendance ea
            JOIN event_instances ei ON ea.instance_id = ei.instance_id
            WHERE ea.user_id = %s AND ei.event_id = %s AND ea.event_date = CURDATE()
        """, (user_id, event_id))
        attendance = cursor.fetchone()

        if not attendance:
            return jsonify({"success": False, "message": "Attendance record not found for this user/event."}), 404

        status = attendance['status']
        if log_type == 'Entry':
            time_str = attendance['first_in_formatted'] or ''
        else:
            time_str = attendance['last_out_formatted'] or ''
        # Remove leading zero (e.g., "08:15 AM" → "8:15 AM")
        if time_str.startswith('0'):
            time_str = time_str[1:]

        # 5. Update general status (employees table) and insert general_log
        new_general_status = 'Inside' if log_type == 'Entry' else 'Outside'
        gate = 'Gate 1' if log_type == 'Entry' else 'Gate 2'

        cursor.execute("UPDATE employees SET status = %s WHERE user_id = %s", (new_general_status, user_id))
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO general_log (user_id, timestamp, log_type, gate) VALUES (%s, %s, %s, %s)",
            (user_id, formatted_time, log_type, gate)
        )
        conn.commit()

        # 6. Determine status type for UI (success for Present, warning for Late, etc.)
        status_type = "success" if status == 'Present' else "warning" if status == 'Late' else "secondary"
        # Generate initials from employee name (first letters of first two words)
        name_parts = employee_name.split()[:2]
        initials = ''.join(part[0] for part in name_parts).upper()

        # 7. Return data needed to update live feed
        return jsonify({
            "success": True,
            "log_type": log_type,
            "log": {
                "name": employee_name,
                "dept": department,
                "time": time_str,
                "status": status,
                "type": status_type,
                "initials": initials
            },
            "message": f"{log_type} logged successfully. General status now {new_general_status}."
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

# ==============================================================================
# ENDPOINT: Get Today's Attendance for All Employees (For Admin Dashboard)
# ==============================================================================

@app.route("/admin/employees/attendance", methods=["GET"])
def get_employee_attendance():
    """
    Returns event attendance records for employees, including event name.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                ea.attendance_id,
                e.employee_name,
                d.department_name as department,
                ev.event_name,
                ei.event_date,
                DATE_FORMAT(ea.first_in, '%h:%i %p') as time_in,
                DATE_FORMAT(ea.last_out, '%h:%i %p') as time_out,
                ea.status
            FROM event_attendance ea
            JOIN event_instances ei ON ea.instance_id = ei.instance_id
            JOIN events ev ON ei.event_id = ev.event_id
            JOIN employees e ON ea.user_id = e.user_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            WHERE ea.first_in IS NOT NULL  -- only show employees who actually attended
            ORDER BY ei.event_date DESC, e.employee_name ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            name = row['employee_name']
            name_parts = name.split()[:2]
            initials = ''.join(part[0] for part in name_parts).upper()
            
            dept = row['department'] or 'N/A'
            event_name = row['event_name']
            time_in = row['time_in'] or '--:--'
            time_out = row['time_out'] or '--:--'
            if time_in.startswith('0'): time_in = time_in[1:]
            if time_out.startswith('0'): time_out = time_out[1:]
            
            status = row['status']
            if status == 'Present':
                status_class = 'success'
            elif status == 'Late':
                status_class = 'warning'
            elif status == 'Excused':
                status_class = 'info'
            else:
                status_class = 'secondary'
            
            result.append({
                "attendance_id": row['attendance_id'],
                "initials": initials,
                "name": name,
                "dept": dept,               # department only (not combined)
                "event_name": event_name,   # new field
                "date": row['event_date'].strftime('%Y-%m-%d') if row['event_date'] else '',
                "in": time_in,
                "out": time_out,
                "status": status,
                "status_class": status_class
            })

        return jsonify({"success": True, "logs": result}), 200

    except Exception as e:
        print(f"Error in get_employee_attendance: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

# ==============================================================================
# ENDPOINT: Delete an Attendance Record (For Admin Corrections)
# ==============================================================================

@app.route("/admin/attendance/<int:attendance_id>", methods=["DELETE"])
def delete_attendance_record(attendance_id):
    """
    Delete an attendance record from event_attendance table.
    Also deletes associated event_log entries for that user and event instance on that day.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        cursor = conn.cursor(dictionary=True)

        # First, get the user_id and instance_id to also delete event_log entries
        cursor.execute("SELECT user_id, instance_id FROM event_attendance WHERE attendance_id = %s", (attendance_id,))
        record = cursor.fetchone()
        if not record:
            return jsonify({"success": False, "message": "Attendance record not found"}), 404

        user_id = record['user_id']
        instance_id = record['instance_id']

        # Delete from event_attendance
        cursor.execute("DELETE FROM event_attendance WHERE attendance_id = %s", (attendance_id,))
        
        # Delete related event_log entries for this user and event instance
        # Get event_id from instance
        cursor.execute("SELECT event_id FROM event_instances WHERE instance_id = %s", (instance_id,))
        event = cursor.fetchone()
        if event:
            event_id = event['event_id']
            cursor.execute("DELETE FROM event_log WHERE user_id = %s AND event_id = %s", (user_id, event_id))
        
        conn.commit()
        
        return jsonify({"success": True, "message": "Attendance record deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

# ==============================================================================
# ENDPOINT: Time in/Time out Log in Kiosk Event
# ==============================================================================

@app.route("/admin/instances/<int:instance_id>/get-logs", methods=["GET"])
def get_instance_logs(instance_id):
    """
    Returns all event_log entries for a specific event instance.
    Each row corresponds to a single swipe (Entry or Exit).
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                el.log_id,
                el.user_id,
                el.log_type,
                el.timestamp,
                COALESCE(e.employee_name, s.student_name, 'Unknown') as user_name,
                COALESCE(d.department_name, 'N/A') as department,
                el.log_type as action
            FROM event_log el
            JOIN event_instances ei ON el.event_id = ei.event_id
            LEFT JOIN employees e ON el.user_id = e.user_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            LEFT JOIN students s ON el.user_id = s.user_id
            WHERE ei.instance_id = %s
            ORDER BY el.timestamp DESC
        """
        cursor.execute(query, (instance_id,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            name = row['user_name']
            name_parts = name.split()[:2]
            initials = ''.join(part[0] for part in name_parts).upper()
            time_str = row['timestamp'].strftime("%I:%M %p")
            if time_str.startswith('0'):
                time_str = time_str[1:]

            result.append({
                "initials": initials,
                "name": name,
                "dept": row['department'],
                "time": time_str,
                "log_type": row['log_type'],   # "Entry" or "Exit"
                "type": "success" if row['log_type'] == 'Entry' else "secondary"
            })

        return jsonify({"success": True, "logs": result}), 200

    except Exception as e:
        print(f"Error in get_instance_logs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
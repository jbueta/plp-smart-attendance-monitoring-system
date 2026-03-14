print("FILE LOADED", flush=True)
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, request, g
from datetime import date, timedelta, datetime
from db_connect import Database

import json
import os
import logging
import mysql.connector as connector
from mysql.connector import pooling

        
app = Flask(__name__)
app.secret_key = 'plp_secure_key_2026'  # Required for session management

app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(logging.StreamHandler())
app.logger.addHandler(logging.FileHandler('logs/app.log'))


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

# 1. Create the pool once 
dbconfig = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_monitoring',
    'use_pure': True
}

try:
    print("Creating database connection pool...")
    # Initialize globally
    global_pool = pooling.MySQLConnectionPool(pool_name="main_entry_exit", pool_size=20, autocommit=True, **dbconfig)
    print("Database connection pool created.")
except Exception as err:
    print(f"Warning: Could not connect to database: {err}")
    global_pool = None

def connect_db():
    if 'db' not in g:        
        try:
            if global_pool is None:
                g.db = None
            else:
                g.db = global_pool.get_connection() # Borrow from pool
        except Exception as err:
            print(f"Pool exhausted or error: {err}")
            g.db = None
    return g.db

def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        # returns used connection to the pool.
        db.close()

@app.route('/admin/user/authentication', methods=['POST'])
def user_authenticate():
    conn = None
    try:
        print("Authenticating...")
        data = request.get_json()

        if not data or not data.get('id'):
            return jsonify({"error": "ID is required. No ID string attached"}), 400
        
        scan_id = data.get('id')
        
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. AUTHENTICATE
        db = Database(conn, (scan_id, scan_id))
        result = db.authenticate_user()

        if not result or len(result) == 0:
            return jsonify({"Invalid": "Invalid ID!"}), 404

        # 2. GET USER DATA
        user_data = result[0]
        user_id = user_data['user_id']
        role = user_data['role']
        current_status = user_data['current_status']

        print(f"User found: ID {user_id}, Role: {role}, Status: {current_status}")

        # 3. CHANGE STATUS
        # We now pass user_id, current_status, and role so it updates the correct table
        db_status_param = (user_id, current_status, role)
        db_status = Database(conn, db_status_param)
        
        db_status_result = db_status.change_status()
        if not db_status_result:
            return jsonify({"success": False, "message": "Failed to update user status in database."}), 500

        # 4. DETERMINE LOG TYPE & INSERT LOG
        new_status = db_status_result['status']
        log_type = 'Entry' if new_status == 'Inside' else 'Exit'
        gate = 'Gate 1' if new_status == 'Inside' else 'Gate 2'

        log_params = (user_id, formatted_time, log_type, gate)
        db_insert_log = Database(conn, log_params)
        
        print(f"Inserting {log_type} log...")
        db_insert_log_result = db_insert_log.insert_general_log()
        
        if not db_insert_log_result:
            return jsonify({"success": False, "message": "Status changed, but failed to insert log."}), 500

        return jsonify({"success": True, "message": f"User authenticated. Status updated to {new_status}."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error during authentication: {str(e)}"}), 500
    
    finally:
        # Always a good habit to close the connection if you are opening it per-route!
        if conn and conn.is_connected():
            conn.close()


# ==============================================================================
# EVENTS ENDPOINT
# ==============================================================================

@app.route('/admin/add-events', methods=['POST'])
def add_events():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500  

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        required_fields = ['event_name', 'event_type', 'frequency', 'location', 'start_date', 'end_date', 'time_start', 'time_end', 'participants_type']
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

        sd = data.get('start_date')
        ed = data.get('end_date')

        try:
            start_date_obj = datetime.strptime(sd, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(ed, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
        if start_date_obj > end_date_obj:
            return jsonify({"success": False, "error": "Start Date cannot be after End Date"}), 400

        frequency = data.get('frequency')
        if frequency == 'WEEKLY':
            day = data.get('day')
            if not day:
                return jsonify({"success": False, "error": "Day is required"}), 400
        elif frequency == 'ONCE':
            if sd != ed:
                return jsonify({"success": False, "error": "Start Date and End Date must be the same for one-time event"}), 400
            
        event_name = data.get('event_name')
        event_type = data.get('event_type')
        day = data.get('day')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        time_start = data.get('time_start')
        time_end = data.get('time_end')
        location = data.get('location')

        db = Database(conn, (event_name, event_type, frequency, day, start_date, end_date, time_start, time_end, location, participants, participants_type))
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
    finally:
        close_db(conn)


# ==========================================
# ENDPOINT 1: The Weekly Generator (Triggered by Cron)
# ==========================================
@app.route("/admin/generate-weekly-instances", methods=["POST"])
def generate_weekly_instances():
    """
    Triggered every Sunday at 11:59 PM by a cron job or cloud scheduler.
    Preps the database for the upcoming 7 days.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        today = date.today()
        
        # Loop through the next 7 days
        for i in range(1, 8):
            target_date = today + timedelta(days=i)
            day_name = target_date.strftime("%A") # e.g., 'Monday'

            database = Database(conn, (day_name,))
            events = database.check_events()

            if not events:
                continue
            
            for event in events:
                event_id = event['event_id']

                new_db = Database(conn, (event_id, target_date))
                instance_result = new_db.add_event_instances()

                if instance_result.get('success') == False:
                    # Log the error, but don't kill the whole loop
                    print(f"Failed to add instance for Event {event_id}: {instance_result['message']}")
        
        return jsonify({"success": True, "message": "Upcoming week generated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        close_db(conn)

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
    finally:
        close_db(conn)

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
    finally:
        if conn:
            close_db(conn)

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
                        "message": f"Event satus updated to {status}.",
                        "date": events.get('data')
                      }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

# ====================================================
# ENDPOINT 5: Get All Events
# ====================================================
@app.route("/admin/get-events", methods=["GET"])
def get_all_events():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        db = Database(conn)
        events = db.get_all_events()

        return jsonify({"success": True, "data": events}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

# ====================================================
# ENDPOINT 6: Get Roster & Attendance for an Instance
# ====================================================
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
            return jsonify({"success": False, "message": "Database offline"}), 500

        db = Database(conn, (instance_id,))
        roster = db.get_instance_attendance()

        if roster is None:
            return jsonify({"success": False, "message": "Error fetching roster"}), 500

        return jsonify({"success": True, "data": roster}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
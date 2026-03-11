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

@app.teardown_appcontext
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
        # data = json.loads(data)

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        id = data.get('id')
        if not id:
            return jsonify({"error": "ID is required. No ID string attached"}), 400
        
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        current_date = date()
        parameter = (id, id)
        db = Database(conn, parameter)
        result = db.authenticate_user()

        if not result or len(result) == 0:
            return jsonify({"Invalid": "Invalid ID!"}), 404
        elif result and len(result) > 0:

            # =========================================================
            # # CHECKING LOGS FOR STUDENT STATUS
            # =========================================================
            print("Getting student status...")

            status = result[0]['status']
            db_status_param = (student_id, status)
            db_status = Database(conn, db_status_param)

            # =========================================================
            # # CHANGING STUDENT STATUS
            # =========================================================
            try:
                db_status_result = db_status.change_status()
            except Exception as e:
                return jsonify({"success": False, "message": f"Error changing status: {e}"}), 500  # Internal Server Error status 
                
            if db_status_result['status'] == 'Inside':
                log_type = 'Entry'
                gate = 'Gate 1'
            elif db_status_result['status'] == 'Outside':
                log_type = 'Exit'
                gate = 'Gate 2'

            user_id = result[0]['user_id']
            log_params = (user_id, formatted_time, log_type, gate)
            db_insert_log = Database(conn, log_params)
            print("Inserting log...")

            try:
                db_insert_log_result = db_insert_log.insert_general_log()
            except Exception as e:
                return jsonify({"success": False, "message": f"Error inserting log: {e}"}), 500  # Internal Server Error status 

            return jsonify({"success": True, "message": "User authenticated and log updated"}), 200

    except Exception as e:
            return jsonify({"success": False, "message": f"Error during authentication: {str(e)}"}), 500


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

        required_fields = ['event_name', 'event_type', 'frequency', 'participants', 'location', 'start_date', 'end_date', 'time_start', 'time_end']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        frequency = data.get('frequency')
        if frequency == 'WEEKLY':
            day = data.get('day')
            if not day:
                return jsonify({"error": "Day is required"}), 400

        event_name = data.get('event_name')
        event_type = data.get('event_type')
        day = data.get('day')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        time_start = data.get('time_start')
        time_end = data.get('time_end')
        location = data.get('location')
        participants = data.get('participants')

        db = Database(conn, (event_name, event_type, frequency, day, start_date, end_date, time_start, time_end, location, participants))
        db_result = db.add_event()
        
        if not db_result or db_result.get('success') is False:
            error_msg = db_result.get('message', 'Error adding event') if db_result else 'Unknown database error'
            return jsonify({"success": False, "message": error_msg}), 400
            
        return jsonify({"success": True, "message": f"Event '{event_name}' added successfully"}), 200
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
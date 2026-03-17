print("FILE LOADED", flush=True)
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, request, g
from datetime import datetime
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
# MOCK DATA (Prototype State)
# ==============================================================================

# Default events that cannot be deleted in this prototype
DEFAULT_EVENTS = [
    {
        'id': 1, 
        'name': 'Flag Ceremony Entrance/Exit', 
        'type': 'Mandatory', 
        'dept': 'All Departments', 
        'time': '07:00 AM', 
        'date': date.today().strftime('%Y-%m-%d')
    },
    {
        'id': 2, 
        'name': 'Flag Retreat', 
        'type': 'Mandatory', 
        'dept': 'All Departments', 
        'time': '05:00 PM', 
        'date': date.today().strftime('%Y-%m-%d')
    }
]

EVENTS = list(DEFAULT_EVENTS)
VISITORS = []

# --- Database Transition Mock Models ---
MOCK_DASHBOARD_STATS = {
    "total_entries": "14,520",
    "entries_trend": "+12%",
    "flag_ceremony_compliance": "87.5%",
    "flag_ceremony_raw": "2,450 / 2,800",
    "currently_inside": "3,412",
    "traffic_chart": [450, 2100, 1800, 1200, 900, 600, 1100, 1400, 800, 600, 1500, 900],
    "alerts": [
        {"type": "warning", "icon": "exclamation-triangle-fill", "title": "High Density: North Gate", "time": "15 minutes ago"},
        {"type": "danger", "icon": "slash-circle-fill", "title": "Flag Ceremony < 70%", "time": "College of Arts"}
    ]
}

MOCK_EMPLOYEE_STATS = {
    "attendance_data": [60, 15, 15, 10], 
    "tardiness_data": [15, 12, 5, 8, 25, 18, 10]
}

MOCK_EMPLOYEE_LOGS = [
    {"initials": "JD", "name": "Juan Dela Cruz", "dept": "Civil Engineering", "in": "07:45 AM", "out": "05:00 PM", "status": "Present", "status_class": "success"},
    {"initials": "MS", "name": "Maria Santos", "dept": "College of Nursing", "in": "08:15 AM", "out": "--:--", "status": "Late +15m", "status_class": "warning"},
    {"initials": "JR", "name": "Jose Rizal", "dept": "Arts & Letters", "in": "--:--", "out": "--:--", "status": "Absent", "status_class": "danger"}
]

MOCK_STUDENT_STATS = {
    "total_entries": "12,450",
    "entries_trend": "+12%",
    "peak_hour": "07:00 AM",
    "peak_load": "85%",
    "currently_inside": "3,120",
    "avg_stay": "6.5 Hrs",
    "curfew_trigger": "09:40:00 PM",
    "watchlist": []  # Empty for clear state
}

MOCK_KIOSK_DATA = {
    "bulletin": {
        "tag": "ANNOUNCEMENT", 
        "author": "Admin Office", 
        "title": "Midterm Examinations Week", 
        "body": "Please ensure your test permits are validated before entering the examination rooms. Library hours are extended until 8:00 PM."
    },
    "recent_student_logs": [
        {"type": "in", "name": "Maria Clara", "course": "BS Psychology", "time": "07:30 AM"},
        {"type": "out", "name": "Jose Rizal", "course": "BS Accountancy", "time": "05:15 PM"}
    ],
    "recent_employee_logs": [
        {"initials": "JD", "name": "Juan Dela Cruz", "dept": "Engineering", "time": "07:45 AM", "type": "success"},
        {"initials": "MS", "name": "Maria Santos", "dept": "Nursing", "time": "08:15 AM", "type": "warning"}
    ]
}

MOCK_REPORTS = [
    {"icon": "shield-exclamation text-danger", "name": "Curfew_Violations_Feb09.pdf", "time": "Generated 1 hr ago"},
    {"icon": "file-earmark-spreadsheet text-success", "name": "Student_Logs_Week4.csv", "time": "Generated Yesterday"},
    {"icon": "file-earmark-pdf text-gold", "name": "Flag_Ceremony_Attendance.pdf", "time": "Generated Feb 03, 2026"}
]

# ==============================================================================
# MIDDLEWARE / DECORATORS
# ==============================================================================

def login_required(f):
    """Decorator to protect admin routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded credentials for prototype demonstration
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            flash('Welcome back, Admin.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ==============================================================================
# PUBLIC KIOSK ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Main landing page / Kiosk Mode selection."""
    session.pop('logged_in', None)  # Auto-logout admin if they return to home
    return render_template('index.html')

@app.route('/kiosk/student')
def kiosk_student():
    session.pop('logged_in', None)
    active_visitors = [v for v in VISITORS if v['status'] == 'Checked In']
    return render_template('kiosk_student.html', active_visitors=active_visitors, kiosk_data=MOCK_KIOSK_DATA)

@app.route('/kiosk/employee/select-event')
def kiosk_employee_select_event():
    session.pop('logged_in', None)
    return render_template('kiosk_event_select.html', events=EVENTS)

@app.route('/kiosk/employee')
def kiosk_employee():
    session.pop('logged_in', None)
    event_id = request.args.get('event_id', type=int)
    selected_event = next((e for e in EVENTS if e['id'] == event_id), None)
    event_name = selected_event['name'] if selected_event else "General Attendance"
    return render_template('kiosk_employee.html', event_name=event_name, kiosk_data=MOCK_KIOSK_DATA)

@app.route('/kiosk/visitor')
def kiosk_visitor():
    session.pop('logged_in', None)
    active_visitors = [v for v in VISITORS if v['status'] == 'Checked In']
    return render_template('kiosk_visitor.html', active_visitors=active_visitors)

# ==============================================================================
# VISITOR MANAGEMENT API
# ==============================================================================

@app.route('/api/visitor/checkin', methods=['POST'])
def visitor_checkin():
    name = request.form.get('name')
    purpose = request.form.get('purpose')
    details = request.form.get('details')
    source = request.form.get('source')
    
    if name and purpose:
        new_id = len(VISITORS) + 1
        now = datetime.now()
        
        VISITORS.append({
            'id': new_id,
            'name': name,
            'purpose': purpose,
            'details': details or 'N/A',
            'time_in': now.strftime('%I:%M %p'),
            'date': now.strftime('%Y-%m-%d'),
            'time_out': None,
            'status': 'Checked In'
        })
        flash(f'Welcome, {name}. Check-in successful.', 'success')
    else:
        flash('Check-in failed. Name and Purpose are required.', 'danger')
        
    return redirect(url_for(source if source else 'kiosk_visitor'))

@app.route('/api/visitor/checkout/<int:visitor_id>', methods=['POST'])
def visitor_checkout(visitor_id):
    visitor = next((v for v in VISITORS if v['id'] == visitor_id), None)
    source = request.args.get('source', 'kiosk_visitor')
    
    if visitor:
        visitor['status'] = 'Checked Out'
        visitor['time_out'] = datetime.now().strftime('%I:%M %p')
        flash(f'Goodbye, {visitor["name"]}. Check-out successful.', 'success')
    else:
        flash('Visitor not found.', 'danger')
        
    return redirect(url_for(source))

# ==============================================================================
# ADMIN DASHBOARD ROUTES
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', events=EVENTS, stats=MOCK_DASHBOARD_STATS)

@app.route('/events')
@login_required
def manage_events():
    return render_template('events.html', events=EVENTS)

@app.route('/admin/visitors')
@login_required
def admin_visitors():
    return render_template('admin_visitors.html', visitors=VISITORS)

@app.route('/analytics/employee')
@login_required
def analytics_employee():
    return render_template('analytics_employee.html', events=EVENTS, stats=MOCK_EMPLOYEE_STATS, logs=MOCK_EMPLOYEE_LOGS)

@app.route('/analytics/students')
@login_required
def analytics_students():
    return render_template('analytics_students.html', stats=MOCK_STUDENT_STATS)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', events=EVENTS, reports=MOCK_REPORTS)

# ==============================================================================
# ADMIN MANAGEMENT API
# ==============================================================================

@app.route('/admin/events/add', methods=['POST'])
@login_required
def add_event():
    name = request.form.get('name')
    etype = request.form.get('type')
    dept = request.form.get('dept')
    edate = request.form.get('date')
    time = request.form.get('time')
    
    if name and etype and edate and time:
        new_id = max([e['id'] for e in EVENTS]) + 1 if EVENTS else 1
        EVENTS.append({
            'id': new_id,
            'name': name,
            'type': etype,
            'dept': dept or 'All Departments',
            'date': edate,
            'time': time
        })
        flash(f'Event "{name}" added successfully.', 'success')
    else:
        flash('Failed to add event. All fields are required.', 'danger')
        
    return redirect(url_for('manage_events'))

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    if event_id <= 2:
        flash('Cannot delete default system events.', 'warning')
        return redirect(url_for('dashboard'))

    global EVENTS
    EVENTS = [e for e in EVENTS if e['id'] != event_id]
    flash('Event deleted successfully.', 'info')
    return redirect(url_for('manage_events'))

@app.route('/admin/events/delete/bulk', methods=['POST'])
@login_required
def bulk_delete_events():
    event_ids = request.form.getlist('event_ids')
    
    if not event_ids:
        flash('No events selected for deletion.', 'warning')
        return redirect(url_for('manage_events'))

    try:
        event_ids = [int(eid) for eid in event_ids]
    except ValueError:
        flash('Invalid event IDs provided.', 'danger')
        return redirect(url_for('manage_events'))

    safe_ids = [eid for eid in event_ids if eid > 2]
    skipped_count = len(event_ids) - len(safe_ids)

    global EVENTS
    initial_count = len(EVENTS)
    EVENTS = [e for e in EVENTS if e['id'] not in safe_ids]
    deleted_count = initial_count - len(EVENTS)

    msg = f'{deleted_count} events deleted successfully.'
    if skipped_count > 0:
        msg += f' {skipped_count} default events were protected.'
    
    flash(msg, 'info')
    return redirect(url_for('manage_events'))

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def update_profile():
    flash('Admin profile updated successfully.', 'success')
    return redirect(url_for('dashboard'))

# ==============================================================================
# STUDENT API (MOCK)
# ==============================================================================

@app.route('/api/check_student_status', methods=['POST'])
def check_student_status():
    data = request.get_json()
    student_id = data.get('student_id')
    
    mock_students = {
        '2026-001': {'name': 'Maria Clara', 'course': 'BS Psychology', 'status': 'TIMED IN'},
        '2026-002': {'name': 'Jose Rizal', 'course': 'BS Accountancy', 'status': 'TIMED OUT'},
        '2026-003': {'name': 'Andres Bonifacio', 'course': 'BS Criminology', 'status': 'TIMED IN'}
    }
    
    student = mock_students.get(student_id)
    if student:
        return {
            'status': 'found',
            'name': student['name'],
            'course': student['course'],
            'attendance_status': student['status']
        }
    return {'status': 'not_found'}

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

pool = None
def create_pool():
    print("Creating database connection pool...")
    dbconfig = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'smart_monitoring',
        'use_pure': True
    }
    try:
        pool = pooling.MySQLConnectionPool (pool_name="main_entry_exit", pool_size=20, autocommit=True, **dbconfig)
        print("Database connection pool created.")
        return pool
    except SystemExit as e:
        print(f"S`ystemExit caught: {e}", flush=True)
    except BaseException as e:
        print(f"BaseException caught: {type(e).__name__}: {e}", flush=True)
    except Exception as err:
        print(f"Warning: Could not connect to database: {err}")
        print("App will run in mock/offline mode.")

def connect_db():
    if 'db' not in g:        
        try:
            c_pool = create_pool()
            if c_pool is None:
                g.db = None
            else:
                g.db = c_pool.get_connection()
        except Exception as err:
            print(f"Pool exhausted or error: {err}")
            g.db = None
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        # It simply returns used connection to the 'attendance_pool' so another request can use it.
        db.close()

@app.route('/authenticate', methods=['POST'])
def authenticate():
    try:
        print("Authenticating...")
        data = request.get_json()
        # data = json.loads(data)

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        event = data.get('event') 
        if not event:
            return jsonify({"error": "Event is required"}), 400
        
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({"error": "Student ID is required"}), 400
        
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        date = now.strftime("%Y-%m-%d")
        parameter = (student_id,)
        print(parameter)
        db = Database(conn, parameter)
        result = db.authenticate_user()

        if not result or len(result) == 0:
            return jsonify({"Invalid": "Student does not found!"}), 404
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
    
if __name__ == '__main__':
    # ssl_context='adhoc' enables HTTPS so the browser allows camera access.
    # Requires: pip install pyopenssl
    # Access via: https://192.168.1.15:5000  (click Advanced → Proceed on the warning)
    app.run(debug=True, host='0.0.0.0', port=5000)
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import csv
import io
import uuid

from app_tasks import fetch_report_data     #reports generator
from extensions import cache
from database import connect_db
from db_connect import Database

app = Flask(__name__)
app.secret_key = 'plp_secure_key_2026'  # Required for session management

# Configure and initialize cache (SimpleCache for development)
app.config['CACHE_TYPE'] = 'SimpleCache'
cache.init_app(app)

# ==============================================================================
# MOCK DATA (Prototype State)
# ==============================================================================

# Default events that cannot be deleted in this prototype
DEFAULT_EVENTS = [
    {}
]

VISITORS = []

LIVE_DEPARTMENTS = [
    {}
]

# --- Database Transition Mock Models ---
MOCK_DASHBOARD_STATS = {
    "total_entries": "14,520",
    "entries_trend": "+12%",
    "event_attendance_rate": "89.5%",
    "event_attendance_raw": "2,506 / 2,800 Attendees",
    "currently_inside": "3,412",
    "avg_dwell_time": "5 hrs 45 mins",
    "peak_hour": "07:30 AM",
    "traffic_chart": [450, 2100, 1800, 1200, 900, 600, 1100, 1400, 800, 600, 1500, 900],
    "dept_distribution": [35, 25, 20, 15, 5], # Percentages for top 5 depts
    "alerts": [
        {"type": "warning", "icon": "exclamation-triangle-fill", "title": "High Density: North Gate", "time": "15 minutes ago"},
        {"type": "info", "icon": "info-circle-fill", "title": "Peak Hour Detected", "time": "07:30 AM"}
    ]
}

EVENTS = list(DEFAULT_EVENTS)

MOCK_EMPLOYEE_STATS = {
    "attendance_data": [75, 20, 5], 
    "tardiness_data": [15, 12, 5, 8, 25, 18, 10],
    "dept_participation": [
        {"name": "College of Education", "value": 85},
        {"name": "College of Engineering", "value": 92},
        {"name": "College of Nursing", "value": 78},
        {"name": "Arts & Sciences", "value": 88},
        {"name": "Business Admin", "value": 90}
    ],
    "avg_tardiness": "12 mins",
    "on_time_rate": "88%"
}

MOCK_EMPLOYEE_LOGS = [
    {"id": "EMP-001", "initials": "JD", "name": "Juan Dela Cruz", "dept": "Civil Engineering", "position": "Professor", "in": "07:45 AM", "out": "05:00 PM", "status": "Present", "status_class": "success", "date": "2026-04-09"},
    {"id": "EMP-002", "initials": "MS", "name": "Maria Santos", "dept": "College of Nursing", "position": "Dean", "in": "08:15 AM", "out": "--:--", "status": "Late +15m", "status_class": "warning", "date": "2026-04-09"},
    {"id": "EMP-003", "initials": "AL", "name": "Antonio Luna", "dept": "Arts & Letters", "position": "Lecturer", "in": "08:30 AM", "out": "04:30 PM", "status": "Late", "status_class": "warning", "date": "2026-04-09"},
    {"id": "EMP-004", "initials": "CR", "name": "Carmen Reyes", "dept": "Business Admin", "position": "Assistant Professor", "in": "07:30 AM", "out": "05:30 PM", "status": "Present", "status_class": "success", "date": "2026-04-09"},
    {"id": "EMP-005", "initials": "RG", "name": "Roberto Garcia", "dept": "Engineering", "position": "Instructor", "in": "08:00 AM", "out": "--:--", "status": "Inside", "status_class": "success", "date": "2026-04-09"},
    {"id": "EMP-006", "initials": "LM", "name": "Lourdes Mendoza", "dept": "Education", "position": "Professor", "in": "07:50 AM", "out": "04:45 PM", "status": "Present", "status_class": "success", "date": "2026-04-09"},
    {"id": "EMP-007", "initials": "FT", "name": "Fernando Torres", "dept": "Arts & Sciences", "position": "Lecturer", "in": "08:20 AM", "out": "--:--", "status": "Late +20m", "status_class": "warning", "date": "2026-04-09"},
    {"id": "EMP-008", "initials": "EV", "name": "Elena Valdez", "dept": "Nursing", "position": "Clinical Instructor", "in": "07:40 AM", "out": "05:10 PM", "status": "Present", "status_class": "success", "date": "2026-04-09"},
    {"id": "EMP-009", "initials": "HP", "name": "Hector Perez", "dept": "Business Admin", "position": "Department Head", "in": "08:10 AM", "out": "04:50 PM", "status": "Late", "status_class": "warning", "date": "2026-04-09"},
    {"id": "EMP-010", "initials": "IS", "name": "Isabel Santos", "dept": "Education", "position": "Assistant Professor", "in": "07:55 AM", "out": "--:--", "status": "Inside", "status_class": "success", "date": "2026-04-09"}
]

MOCK_STUDENT_STATS = {
    "total_entries": "12,450",
    "entries_trend": "+12%",
    "peak_hour": "07:00 AM",
    "peak_load": "85%",
    "currently_inside": "3,120",
    "avg_stay": "6.5 Hrs",
    "curfew_trigger": "09:40:00 PM",
    "watchlist": [],
    "hourly_traffic": [300, 1800, 1500, 900, 700, 500, 900, 1200, 600, 400, 1200, 700]
}

MOCK_STUDENT_LOGS = [
    {"id": "2026-0001", "name": "Juan Dela Cruz", "course": "BSCS", "time_in": "07:30 AM", "time_out": "05:00 PM", "status": "Out", "status_class": "secondary"},
    {"id": "2026-0089", "name": "Maria Clara", "course": "BSN", "time_in": "08:15 AM", "time_out": "--:--", "status": "Inside", "status_class": "success"},
    {"id": "2026-0152", "name": "Jose Rizal", "course": "BSA", "time_in": "07:45 AM", "time_out": "05:15 PM", "status": "Out", "status_class": "secondary"}
]

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

def get_active_visitors():
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT visitor_id AS id, visitor_name AS name, purpose, status FROM visitors WHERE status = 'Inside'")
            return cursor.fetchall()
        except Exception:
            pass
        finally:
            if 'cursor' in locals(): cursor.close()
    return []

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request."}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "message": "Please enter a username and password."})

        result = helper_admin_login(username, password)
        
        if result and result.get('success'):
            data = result.get('data')
            session['logged_in'] = True
            return jsonify({ "success": True, "redirect_url": url_for('dashboard', user=data.get('username')) })
        else:
            return jsonify({"success": False, "message": result.get('message')})
            
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

@app.route('/kiosk/entrance')
def kiosk_entrance():
    session.pop('logged_in', None)
    active_visitors = get_active_visitors()
    logs = helper_kiosk_live_student_logs()
    return render_template('kiosk_entrance.html', active_visitors=active_visitors, kiosk_data=logs)

@app.route('/kiosk/exit')
def kiosk_exit():
    session.pop('logged_in', None)
    logs = helper_kiosk_live_student_logs()
    return render_template('kiosk_exit.html', kiosk_data=logs)

@app.route('/kiosk/employee/select-event')
def kiosk_employee_select_event():
    session.pop('logged_in', None)
    events = helper_kiosk_live_events()
    return render_template('kiosk_event_select.html', events=events)

@app.route('/kiosk/employee')
def kiosk_employee():
    session.pop('logged_in', None)
    instance_id = request.args.get('instance_id', type=int)
    events = helper_kiosk_live_events()
    print(events)
    selected_event = next((e for e in events if e['instance_id'] == instance_id), None)
    event_name = selected_event['name'] if selected_event else "General Attendance"
    return render_template('kiosk_employee.html', event_name=event_name, kiosk_data=MOCK_KIOSK_DATA)

@app.route('/kiosk/visitor')
def kiosk_visitor():
    session.pop('logged_in', None)
    active_visitors = get_active_visitors()
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
        conn = connect_db()
        if conn:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (role, active) VALUES ('visitor', 1)")
                user_id = cursor.lastrowid
                import uuid
                visitor_id = f"V-{str(uuid.uuid4())[:6].upper()}"
                cursor.execute(
                    "INSERT INTO visitors (user_id, visitor_id, visitor_name, purpose, details, status) VALUES (%s, %s, %s, %s, %s, 'Inside')",
                    (user_id, visitor_id, name, purpose, details)
                )
                cursor.execute("INSERT INTO general_log (user_id, timestamp, log_type, gate) VALUES (%s, NOW(), 'Entry', 'Gate 1')", (user_id,))
                conn.commit()
                flash(f'Welcome, {name}. Check-in successful.', 'success')
            except Exception as e:
                if conn: conn.rollback()
                flash(f'Check-in failed. Error: {str(e)}', 'danger')
            finally:
                if cursor: cursor.close()
        else:
            flash('Check-in failed. Database offline.', 'danger')
    else:
        flash('Check-in failed. Name and Purpose are required.', 'danger')
        
    return redirect(url_for(source if source else 'kiosk_entrance'))

@app.route('/api/visitor/checkout/<string:visitor_id>', methods=['POST'])
def visitor_checkout(visitor_id):
    source = request.args.get('source', 'kiosk_entrance')
    conn = connect_db()
    if conn:
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT u.user_id, v.visitor_name FROM visitors v JOIN users u ON v.user_id = u.user_id WHERE v.visitor_id = %s", (visitor_id,))
            visitor = cursor.fetchone()
            if visitor:
                user_id = visitor['user_id']
                cursor.execute("UPDATE visitors SET status = 'Outside' WHERE user_id = %s", (user_id,))
                cursor.execute("INSERT INTO general_log (user_id, timestamp, log_type, gate) VALUES (%s, NOW(), 'Exit', 'Gate 1')", (user_id,))
                conn.commit()
                flash(f'Goodbye, {visitor["visitor_name"]}. Check-out successful.', 'success')
            else:
                flash('Visitor not found.', 'danger')
        except Exception as e:
            if conn: conn.rollback()
            flash(f'Check-out failed. Error: {str(e)}', 'danger')
        finally:
            if cursor: cursor.close()
    else:
        flash('Check-out failed. Database offline.', 'danger')
        
    return redirect(url_for(source))

# ==============================================================================
# ADMIN DASHBOARD ROUTES
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():

    USER_NAME = request.args.get('user', 'Admin')

    events = helper_admin_live_events()
    # Pass structured stats for different tabs
    return render_template('dashboard.html', 
                           events=events, 
                           overall_stats=MOCK_DASHBOARD_STATS,
                           student_stats=MOCK_STUDENT_STATS,
                           employee_stats=MOCK_EMPLOYEE_STATS,
                           logs=MOCK_EMPLOYEE_LOGS,
                           user=USER_NAME)

@app.route('/events')
@login_required
def manage_events():
    events = helper_admin_live_events()
    departments = helper_admin_live_departments()
    return render_template('events.html', events=events, departments=departments)

@app.route('/admin/students')
@login_required
def admin_students():
    conn = connect_db()
    db_students = []
    if conn:
        db_students = Database.get_student_logs_full(conn)
    return render_template('student_logs.html', logs=db_students)

@app.route('/admin/employees')
@login_required
def admin_employees():
    conn = connect_db()
    db_employees = []
    if conn:
        db_employees = Database.get_employee_logs_full(conn)
    return render_template('employee_logs.html', logs=db_employees)

@app.route('/admin/visitors')
@login_required
def admin_visitors():
    conn = connect_db()
    visitors_data = []
    if conn:
        visitors_data = Database.get_visitor_logs(conn)
    return render_template('admin_visitors.html', visitors=visitors_data)

@app.route('/analytics/employee')
@login_required
def analytics_employee():
    return redirect(url_for('admin_employees'))

@app.route('/analytics/students')
@login_required
def analytics_students():
    return redirect(url_for('admin_students'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', events=EVENTS, reports=MOCK_REPORTS)

@app.route('/reports/sample')
@login_required
def sample_report():
    return render_template('sample_report.html', current_date=datetime.now().strftime('%B %d, %Y - %I:%M %p'))

# ==============================================================================
# ADMIN MANAGEMENT API
# ==============================================================================

@app.route('/admin/events/add', methods=['POST'])
@login_required
def add_event():
    name = request.form.get('name')
    etype = request.form.get('type')

    edate = request.form.get('event_date')
    eday = request.form.get('day_of_week')
    time_start = request.form.get('time_start')
    time_end = request.form.get('time_end')
    location = request.form.get('location')
    
    dept_ids = request.form.getlist('dept')
    custom_depts_file = request.files.get('roster_file')
    
    frequency = request.form.get('frequency').upper()
    participants_type = ''

    if frequency == 'ONE-TIME':
        frequency = 'ONCE'
        if edate is None:
            flash('Failed to add event. For one time events, date is required.', 'danger')
            return redirect(url_for('manage_events'))
    elif frequency == 'WEEKLY':
        if eday is None:
            flash('Failed to add event. For weekly events, day of week is required.', 'danger')
            return redirect(url_for('manage_events'))

    has_file = bool(custom_depts_file and custom_depts_file.filename != '')

    if not dept_ids and not has_file:
        flash('Failed to add event. At least one department is required or upload a custom roster file.', 'danger')
        return redirect(url_for('manage_events'))
    
    if dept_ids and has_file:
        participants_type = 'hybrid'
    elif dept_ids and not has_file:
        participants_type = 'grouped'
    elif not dept_ids and has_file:
        participants_type = 'custom'

    extracted_custom_participants = []
    
    if has_file:
        if custom_depts_file.filename.endswith('.csv'):
            try:
                file_contents = custom_depts_file.read().decode('utf-8-sig')
                csv_stream = io.StringIO(file_contents)
                csv_reader = csv.DictReader(csv_stream)
                target_column = 'ID' 
                for row in csv_reader:
                    if target_column in row and row[target_column].strip():
                        extracted_custom_participants.append(row[target_column].strip())
                csv_stream.close()            
            except Exception as e:
                flash(f"Failed to process the CSV file: {str(e)}", "danger")
                return redirect(url_for('manage_events'))
        else:
            flash("Please upload a valid .csv file.", "warning")
            return redirect(url_for('manage_events'))

    try:
        event_payload = {
            "event_name": name,
            "event_type": etype,
            "frequency": frequency,
            "location": location,
            "event_date": edate,
            "time_start": time_start,
            "time_end": time_end,
            "day": eday,
            "participants_type": participants_type, 
            "grouped_participants": dept_ids,
            "custom_participants": extracted_custom_participants
        }

        api_url = "http://127.0.0.1:5001/admin/dashboard/add-events"
        response = requests.post(api_url, json=event_payload, timeout=5)
        
        if response.status_code in [200, 201]:
            api_data = response.json()
            
            if api_data.get('success'):
                flash(f'Event "{name}" added successfully.', 'success')
            else:
                error_msg = api_data.get('message', 'Unknown API error')
                flash(f'Failed to add event: {error_msg}', 'danger')
        else:
            flash(f'Server error. Status code: {response.status_code}', 'danger')
                
    except requests.exceptions.RequestException as e:
        print(f"Backend API Connection Error: {e}")
        flash(f'Event "{name}" failed to add. Could not connect to the database.', 'danger')

    return redirect(url_for('manage_events'))

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    if event_id <= 2:
        return jsonify({'success': False, 'message': 'Cannot delete default system events.'}), 403

    result = helper_admin_delete_events(event_id, 'single')

    if result and result.get('success'):
        return jsonify({'success': True, 'message': result.get('message', 'Event deleted successfully.')}), 200
    else:
        return jsonify({'success': False, 'message': result.get('message', 'Failed to delete event.')}), 500

@app.route('/admin/events/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_events():
    data = request.get_json()
    event_ids = data.get('event_ids', [])

    if not event_ids:
        return jsonify({'success': False, 'message': 'No events selected.'}), 400

    # Protect default system events from bulk deletion
    valid_ids = [str(eid) for eid in event_ids if int(eid) > 2]
    
    if not valid_ids:
        return jsonify({'success': False, 'message': 'Cannot delete default system events.'}), 403

    try:
        helper_admin_delete_events(valid_ids, 'bulk')
            
        return jsonify({'success': True, 'message': f'{len(valid_ids)} events deleted successfully.'}), 200
        
    except Exception as e:
        print(f"Bulk delete error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during bulk deletion.'}), 500

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def update_profile():
    flash('Admin profile updated successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_student', methods=['POST'])
@login_required
def add_student():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("id") or "").strip()
    name = (data.get("name") or "").strip()
    course = (data.get("course") or "").strip()

    if not student_id or not name or not course:
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    conn = connect_db()
    if not conn:
        return jsonify({"success": False, "error": "Database offline"}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course,))
        res = cursor.fetchone()
        if res:
            course_id = res['course_id']
        else:
            cursor.execute("INSERT INTO courses (course_name) VALUES (%s)", (course,))
            course_id = cursor.lastrowid
            
        cursor.execute("INSERT INTO users (role, active) VALUES ('student', 1)")
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO students (user_id, student_id, student_name, course_id, status) VALUES (%s, %s, %s, %s, 'Outside')",
            (user_id, student_id, name, course_id)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor: cursor.close()

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    data = request.get_json(silent=True) or {}
    emp_id = (data.get("id") or "").strip()
    name = (data.get("name") or "").strip()
    dept = (data.get("department") or "").strip()
    position = (data.get("position") or "").strip()

    if not emp_id or not name or not dept:
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    conn = connect_db()
    if not conn:
        return jsonify({"success": False, "error": "Database offline"}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT department_id FROM departments WHERE department_name = %s", (dept,))
        res = cursor.fetchone()
        if res:
            dept_id = res['department_id']
        else:
            cursor.execute("INSERT INTO departments (department_name) VALUES (%s)", (dept,))
            dept_id = cursor.lastrowid
            
        cursor.execute("INSERT INTO users (role, active) VALUES ('employee', 1)")
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO employees (user_id, employee_id, employee_name, department_id, position, status) VALUES (%s, %s, %s, %s, %s, 'Outside')",
            (user_id, emp_id, name, dept_id, position)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor: cursor.close()

@app.route('/add_visitor', methods=['POST'])
@login_required
def add_visitor():
    data = request.get_json(silent=True) or {}
    visitor_id = (data.get("id") or "").strip()
    visitor_name = (data.get("name") or "").strip()
    purpose = (data.get("purpose") or "").strip()
    details = (data.get("details") or "").strip()

    if not visitor_id or not visitor_name or not purpose:
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    conn = connect_db()
    if not conn:
        return jsonify({"success": False, "error": "Database offline"}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (role, active) VALUES ('visitor', 1)")
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO visitors (user_id, visitor_id, visitor_name, purpose, details, status) VALUES (%s, %s, %s, %s, %s, 'Outside')",
            (user_id, visitor_id, visitor_name, purpose, details)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor: cursor.close()

@app.route('/update_student', methods=['POST'])
@login_required
def update_student():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()
    student_name = (data.get("student_name") or "").strip()
    course = (data.get("course") or "").strip()

    if not student_id or not student_name or not course:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET student_name = %s, course = %s WHERE student_id = %s",
            (student_name, course, student_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Student not found."}), 404
        return jsonify({"success": True})
    except Exception as err:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/delete_student', methods=['POST'])
@login_required
def delete_student():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()

    if not student_id:
        return jsonify({"success": False, "error": "Missing student_id."}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Student not found."}), 404
        return jsonify({"success": True})
    except Exception as err:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

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
# STATIC/ROUTE BASED GETTER METHODS
# ==============================================================================
@app.route('/api/kiosk/live-events')
def kiosk_live_event():    
    try:
        response = requests.get("http://127.0.0.1:5001/kiosk/employee/select-event", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json()) 
            
    except requests.exceptions.RequestException as e:
        print(f"API Bridge Error: {e}")


@app.route('/api/admin/live-events')
def admin_live_event():    
    try:
        response = requests.get("http://127.0.0.1:5001/admin/dashboard/live-events", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json()) 
            
    except requests.exceptions.RequestException as e:
        print(f"API Bridge Error: {e}")

@app.route('/api/admin/live-departments')
def admin_live_departments():    
    try:
        response = requests.get("http://127.0.0.1:5001/admin/dashboard/events/live-departments", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json()) 
            
    except requests.exceptions.RequestException as e:
        print(f"API Bridge Error: {e}")


# ==============================================================================
# HELPER
# ==============================================================================

def helper_admin_login(username, password):
    url = "http://127.0.0.1:5001/admin/login/auth"
    headers = {"Content-Type": "application/json"}
    payload = {"username": username, "password": password}   

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()   
    except requests.exceptions.RequestException as e:
        print(f"API for admin authentication bridge error: {e}")
        return {"success": False, "message": f"Authentication service unavailable: {str(e)}"}

@app.route('/api/retrieve/events')
def helper_kiosk_live_events():    
    current_kiosk_events = list(DEFAULT_EVENTS)
    
    try:
        response = requests.get("http://127.0.0.1:5001/kiosk/employee/select-event", timeout=5)
        
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                real_events = []
                for event in api_data.get('events', []):
                    real_events.append({
                        'event_id': event.get('event_id', ''),
                        'name': event.get('name', 'Unknown'),
                        'type': event.get('type', 'Unknown'),
                        'frequency': event.get('frequency', 'dd/mm/yyyy'),
                        'date': event.get('date', 'Unknown'),
                        'time_start': event.get('time_start', 'Unknown'),
                        'time_end': event.get('time_end', 'Unknown'),
                        'location': event.get('location', 'Unknown')
                    })
                
                current_kiosk_events = real_events
                
    except requests.exceptions.RequestException as e:
        print(f"Backend API Error: {e}")
        
    return current_kiosk_events 

def helper_kiosk_live_student_logs():    
    current_kiosk_data = dict(MOCK_KIOSK_DATA)
    
    try:
        response = requests.get("http://127.0.0.1:5001/kiosk/students/student-logs", timeout=5)
        
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                real_logs = []
                for log in api_data.get('logs', []):
                    real_logs.append({
                        'type': 'in' if log.get('type') in ['in', 'entry'] else 'out',
                        'name': log.get('name', 'Unknown'),
                        'course': log.get('course', 'Unknown'),
                        'time': log.get('time', '')
                    })
                
                current_kiosk_data['recent_student_logs'] = real_logs
                
    except requests.exceptions.RequestException as e:
        print(f"Backend API Error: {e}")
        
    return current_kiosk_data 

@app.route('/api/retrieve/departments')
def helper_admin_live_departments(): 
    current_live_departments = list(LIVE_DEPARTMENTS)
    
    try:
        response = requests.get("http://127.0.0.1:5001/admin/dashboard/events/live-departments", timeout=5)
        
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                real_departments = []
                for dept in api_data.get('departments', []):
                    real_departments.append({
                        'department_id': dept.get('dept_id', ''),
                        'department_name': dept.get('dept_name', 'Unknown')
                    })
                
                current_live_departments = real_departments
                
    except requests.exceptions.RequestException as e:
        print(f"Backend API Error: {e}")
        
    return current_live_departments 

def helper_admin_live_events():    
    current_kiosk_events = list(DEFAULT_EVENTS)
    
    try:
        response = requests.get("http://127.0.0.1:5001/admin/dashboard/live-events", timeout=5)
        
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                real_events = []
                for event in api_data.get('events', []):
                    real_events.append({
                        'event_id': event.get('event_id', ''),
                        'name': event.get('name', 'Unknown'),
                        'type': event.get('type', 'Unknown'),
                        'date': event.get('date', 'Unknown'),
                        'dept': event.get('dept', 'Unknown'),
                        'time_start': event.get('time_start', 'Unknown'),
                        'time_end': event.get('time_end', 'Unknown'),
                        'location': event.get('location', 'Unknown')
                    })
                
                current_kiosk_events = real_events
                
    except requests.exceptions.RequestException as e:
        print(f"Backend API Error: {e}")
        
    return current_kiosk_events 


def helper_admin_delete_events(event_id, delete_type):
    """
    Call the backend API to soft‑delete an event.
    Returns the JSON response from the backend.
    """
    if delete_type == 'single':
        url = "http://127.0.0.1:5001/admin/events/delete-event"
    elif delete_type == 'bulk':
        url = "http://127.0.0.1:5001/admin/events/delete-events"
    headers = {"Content-Type": "application/json"}
    payload = {"event_id": str(event_id)}   

    try:
        response = requests.put(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()          
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Backend API Error: {e}")
        return {"success": False, "message": f"Backend error: {e}"}

# ==============================================================================
# REPORTS GENERATION FUNCTION
# ==============================================================================

@app.route('/generate_report')
def generate_report():
    category = request.args.get('category')
    report_type = request.args.get('type')
    filter_val = request.args.get('filter', 'All')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Validate date range
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                error_msg = f"Invalid date range: 'From' date ({start_date}) cannot be after 'To' date ({end_date})."
                return f"<h1>Report Error</h1><p>{error_msg}</p>", 400
        except ValueError as e:
            return f"<h1>Report Error</h1><p>Invalid date format. Please use YYYY-MM-DD format.</p>", 400
    
    report_results = fetch_report_data(category, report_type, filter_val, start_date, end_date)
    
    # 3. Handle any errors returned by the service
    if "error" in report_results:
        return f"<h1>Report Error</h1><p>{report_results['error']}</p>", 500
        
    # 4. Render the template using the clean dictionaries returned by tasks.py
    return render_template(
        'sample_report.html',
        current_date=datetime.now().strftime('%B %d, %Y - %I:%M %p'),
        report=report_results['report_data'],
        metrics=report_results['metrics_data'],
        logs=report_results['logs']
    )
    
# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

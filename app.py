from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from db_connect import Database
from mysql.connector import pooling

app = Flask(__name__)
app.secret_key = 'plp_secure_key_2026'  # Required for session management

dbconfig = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_monitoring',
    'use_pure': True
}

try:
    global_pool = pooling.MySQLConnectionPool(
        pool_name="visitor_frontend_pool",
        pool_size=10,
        autocommit=False,
        **dbconfig
    )
except Exception:
    global_pool = None

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
    {"initials": "JD", "name": "Juan Dela Cruz", "dept": "Civil Engineering", "in": "07:45 AM", "out": "05:00 PM", "status": "Present", "status_class": "success"},
    {"initials": "MS", "name": "Maria Santos", "dept": "College of Nursing", "in": "08:15 AM", "out": "--:--", "status": "Late +15m", "status_class": "warning"},
    {"initials": "AL", "name": "Antonio Luna", "dept": "Arts & Letters", "in": "08:30 AM", "out": "04:30 PM", "status": "Late", "status_class": "warning"}
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


def connect_db():
    if 'db' not in g:
        try:
            if global_pool is None:
                g.db = None
            else:
                g.db = global_pool.get_connection()
        except Exception:
            g.db = None
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def resolve_visitor_source(source, fallback='kiosk_entrance'):
    if source and source in app.view_functions:
        return source
    return fallback


def fetch_visitor_logs(status=None):
    conn = connect_db()
    if not conn:
        return []

    db = Database(conn)
    logs = db.get_visitor_logs() or []

    if status:
        logs = [log for log in logs if log.get('status') == status]

    return logs


def build_recent_kiosk_feed(limit=6):
    visitor_feed = []
    for visitor in fetch_visitor_logs()[:limit]:
        is_checked_in = visitor.get('status') == 'Checked In'
        visitor_feed.append({
            'type': 'in' if is_checked_in else 'out',
            'name': visitor.get('name'),
            'course': f"Visitor - {visitor.get('purpose', 'N/A')}",
            'time': visitor.get('time_in') if is_checked_in else (visitor.get('time_out') or visitor.get('time_in'))
        })

    return (visitor_feed + list(MOCK_KIOSK_DATA['recent_student_logs']))[:limit]


def get_kiosk_data_with_live_feed():
    kiosk_data = dict(MOCK_KIOSK_DATA)
    kiosk_data['recent_activity_logs'] = build_recent_kiosk_feed()
    return kiosk_data

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

@app.route('/kiosk/entrance')
def kiosk_entrance():
    session.pop('logged_in', None)
    active_visitors = fetch_visitor_logs(status='Checked In')
    return render_template('kiosk_entrance.html', active_visitors=active_visitors, kiosk_data=get_kiosk_data_with_live_feed())

@app.route('/kiosk/exit')
def kiosk_exit():
    session.pop('logged_in', None)
    return render_template('kiosk_exit.html', kiosk_data=get_kiosk_data_with_live_feed())

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
    active_visitors = fetch_visitor_logs(status='Checked In')
    return render_template('kiosk_visitor.html', active_visitors=active_visitors)

# ==============================================================================
# VISITOR MANAGEMENT API
# ==============================================================================

@app.route('/api/visitor/checkin', methods=['POST'])
def visitor_checkin():
    name = (request.form.get('name') or '').strip()
    purpose = (request.form.get('purpose') or '').strip()
    details = request.form.get('details')
    source = resolve_visitor_source(request.form.get('source'))
    
    if name and purpose:
        conn = connect_db()
        if not conn:
            flash('Check-in failed. Visitor database is unavailable.', 'danger')
        else:
            db = Database(conn, (name, purpose, 'Gate 1'))
            result = db.add_visitor_log()
            if result and result.get('success'):
                flash(f'Welcome, {name}. Check-in successful.', 'success')
            else:
                flash(result.get('message', 'Check-in failed.') if result else 'Check-in failed.', 'danger')
    else:
        flash('Check-in failed. Name and Purpose are required.', 'danger')
        
    return redirect(url_for(source))

@app.route('/api/visitor/checkout/<int:visitor_id>', methods=['POST'])
def visitor_checkout(visitor_id):
    source = resolve_visitor_source(request.args.get('source'), fallback='kiosk_entrance')
    
    conn = connect_db()
    if not conn:
        flash('Check-out failed. Visitor database is unavailable.', 'danger')
    else:
        db = Database(conn, (visitor_id, 'Gate 2'))
        result = db.checkout_visitor_log()
        if result and result.get('success'):
            flash(f'Goodbye, {result.get("name", "Visitor")}. Check-out successful.', 'success')
        else:
            flash(result.get('message', 'Visitor not found.') if result else 'Visitor not found.', 'danger')
        
    return redirect(url_for(source))

# ==============================================================================
# ADMIN DASHBOARD ROUTES
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    # Pass structured stats for different tabs
    return render_template('dashboard.html', 
                           events=EVENTS, 
                           overall_stats=MOCK_DASHBOARD_STATS,
                           student_stats=MOCK_STUDENT_STATS,
                           employee_stats=MOCK_EMPLOYEE_STATS,
                           logs=MOCK_EMPLOYEE_LOGS)

@app.route('/events')
@login_required
def manage_events():
    return render_template('events.html', events=EVENTS)

@app.route('/admin/students')
@login_required
def admin_students():
    return render_template('student_logs.html', logs=MOCK_STUDENT_LOGS)

@app.route('/admin/employees')
@login_required
def admin_employees():
    return render_template('employee_logs.html', logs=MOCK_EMPLOYEE_LOGS)

@app.route('/admin/visitors')
@login_required
def admin_visitors():
    return render_template('admin_visitors.html', visitors=fetch_visitor_logs())

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
    dept_list = request.form.getlist('dept')
    custom_depts_raw = request.form.getlist('custom_dept')
    edate = request.form.get('date')
    time = request.form.get('time')
    
    # Format department string
    if not dept_list or 'All Departments' in dept_list:
        dept_str = 'All Departments'
    else:
        dept_str = ', '.join(dept_list)
        
    custom_depts = [c.strip() for c in custom_depts_raw if c.strip()]
    if custom_depts:
        custom_str = ', '.join(custom_depts)
        if dept_str == 'All Departments':
            dept_str = f"All Departments, {custom_str}"
        else:
            dept_str = f"{dept_str}, {custom_str}"
    
    if name and etype and edate and time:
        new_id = max([e['id'] for e in EVENTS]) + 1 if EVENTS else 1
        EVENTS.append({
            'id': new_id,
            'name': name,
            'type': etype,
            'dept': dept_str,
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
# LIVE API ENDPOINT
# ==============================================================================

@app.route('/api/kiosk/live-events')
def api_live_events():
    return jsonify({
        "status": "success",
        "events": EVENTS
    })

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from datetime import date, datetime
from functools import wraps
import csv
import io
import os

import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from app_tasks import fetch_report_data
from config import get_config
from database import close_db, connect_db, init_db_pool
from db_connect import Database
from extensions import cache


app = Flask(__name__)
app.config.from_object(get_config())

os.makedirs(os.path.dirname(app.config["LOG_FILE"]) or ".", exist_ok=True)
cache.init_app(app)

with app.app_context():
    init_db_pool()

app.teardown_appcontext(close_db)


DEFAULT_EVENTS = []
MOCK_REPORTS = [
    {"icon": "shield-exclamation text-danger", "name": "Curfew_Violations_Feb09.pdf", "time": "Generated 1 hr ago"},
    {"icon": "file-earmark-spreadsheet text-success", "name": "Student_Logs_Week4.csv", "time": "Generated Yesterday"},
    {"icon": "file-earmark-pdf text-gold", "name": "Flag_Ceremony_Attendance.pdf", "time": "Generated Feb 03, 2026"},
]

MOCK_DASHBOARD_STATS = {
    "total_entries": "0",
    "entries_trend": "N/A",
    "event_attendance_rate": "N/A",
    "event_attendance_raw": "0 / 0 Attendees",
    "currently_inside": "0",
    "avg_dwell_time": "0 hrs 0 mins",
    "peak_hour": "N/A",
    "traffic_chart": [0] * 12,
    "dept_distribution": [0] * 5,
    "alerts": [],
}

MOCK_EMPLOYEE_STATS = {
    "attendance_data": [0, 0, 0],
    "tardiness_data": [0] * 7,
    "dept_participation": [],
    "avg_tardiness": "0 mins",
    "on_time_rate": "N/A",
}

MOCK_STUDENT_STATS = {
    "total_entries": "0",
    "entries_trend": "N/A",
    "peak_hour": "N/A",
    "peak_load": "0%",
    "currently_inside": "0",
    "avg_stay": "0.0 Hrs",
    "curfew_trigger": "09:40:00 PM",
    "watchlist": [],
    "hourly_traffic": [0] * 12,
}

MOCK_KIOSK_DATA = {
    "bulletin": {
        "tag": "ANNOUNCEMENT",
        "author": "Admin Office",
        "title": "Midterm Examinations Week",
        "body": "Please ensure your test permits are validated before entering the examination rooms. Library hours are extended until 8:00 PM.",
    },
    "recent_student_logs": [
        {"type": "in", "name": "Maria Clara", "course": "BS Psychology", "time": "07:30 AM"},
        {"type": "out", "name": "Jose Rizal", "course": "BS Accountancy", "time": "05:15 PM"},
    ],
}

_instance_generator_run = False


def backend_url(path):
    base_url = app.config["BACKEND_API_URL"].rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def backend_request(method, path, **kwargs):
    kwargs.setdefault("timeout", app.config["BACKEND_TIMEOUT"])
    return requests.request(method, backend_url(path), **kwargs)


@app.context_processor
def inject_template_config():
    return {"backend_api_url": app.config["BACKEND_API_URL"]}


@app.before_request
def generate_instances_on_sunday():
    global _instance_generator_run

    if _instance_generator_run:
        return

    _instance_generator_run = True
    if date.today().weekday() != 6:
        return

    try:
        response = backend_request("POST", "/admin/generate-daily-instances", timeout=10)
        if response.ok:
            payload = response.json()
            app.logger.info(
                "Generated weekly instances: created=%s failed=%s",
                payload.get("created", 0),
                payload.get("failed", 0),
            )
        else:
            app.logger.error("Failed generating weekly instances: status=%s", response.status_code)
    except requests.RequestException as err:
        app.logger.error("Could not generate weekly instances on startup: %s", err)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def resolve_visitor_source(source, fallback="kiosk_entrance"):
    if source and source in app.view_functions:
        return source
    return fallback


def fetch_visitor_logs(status=None, search_term=None, visit_date=None, include_inactive=False):
    conn = connect_db()
    if not conn:
        return []

    logs = Database(conn).get_visitor_logs(
        search_term=search_term,
        visit_date=visit_date,
        include_inactive=include_inactive,
    )

    if status:
        logs = [log for log in logs if log.get("status") == status]

    return logs


def fetch_live_student_logs():
    current_kiosk_data = dict(MOCK_KIOSK_DATA)
    try:
        response = backend_request("GET", "/kiosk/students/student-logs")
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                current_kiosk_data["recent_student_logs"] = payload.get("logs", [])
    except requests.RequestException as err:
        app.logger.warning("Could not fetch student logs: %s", err)

    return current_kiosk_data


def build_recent_kiosk_feed(limit=6):
    visitor_feed = []
    for visitor in fetch_visitor_logs()[:limit]:
        is_checked_in = visitor.get("status") == "Checked In"
        visitor_label = visitor.get("details") if visitor.get("purpose") == "Other" and visitor.get("details") else visitor.get("purpose", "N/A")
        visitor_feed.append(
            {
                "type": "in" if is_checked_in else "out",
                "name": visitor.get("name"),
                "course": f"Visitor - {visitor_label}",
                "time": visitor.get("time_in") if is_checked_in else (visitor.get("time_out") or visitor.get("time_in")),
            }
        )
    return visitor_feed


def get_kiosk_data_with_live_feed(limit=6):
    kiosk_data = fetch_live_student_logs()
    kiosk_data["recent_activity_logs"] = (
        build_recent_kiosk_feed(limit=limit) + kiosk_data.get("recent_student_logs", [])
    )[:limit]
    return kiosk_data


def fetch_backend_events():
    try:
        response = backend_request("GET", "/admin/dashboard/events")
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                return payload.get("events", [])
    except requests.RequestException as err:
        app.logger.warning("Could not fetch dashboard events: %s", err)
    return []


def fetch_kiosk_live_events():
    try:
        response = backend_request("GET", "/kiosk/employee/select-event")
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                return payload.get("events", [])
    except requests.RequestException as err:
        app.logger.warning("Could not fetch kiosk events: %s", err)
    return []


def fetch_report_events():
    try:
        response = backend_request("GET", "/api/reports/all-events")
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                return payload.get("events", [])
    except requests.RequestException as err:
        app.logger.warning("Could not fetch report events: %s", err)
    return []


def fetch_departments():
    try:
        response = backend_request("GET", "/admin/dashboard/events/live-departments")
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                return [
                    {
                        "department_id": dept.get("dept_id"),
                        "department_name": dept.get("dept_name"),
                    }
                    for dept in payload.get("departments", [])
                ]
    except requests.RequestException as err:
        app.logger.warning("Could not fetch departments: %s", err)
    return []


def fetch_employee_attendance():
    conn = connect_db()
    if not conn:
        return []
    return Database.get_admin_employee_activity(conn)


def fetch_admin_students_page_data():
    conn = connect_db()
    if not conn:
        return [], [], []

    logs = Database.get_admin_student_activity(conn)
    records = Database.get_admin_student_records(conn)
    course_options = sorted(
        {
            item.get("course")
            for item in [*logs, *records]
            if item.get("course") and item.get("course") != "N/A"
        }
    )
    return logs, records, course_options


def fetch_admin_employees_page_data():
    conn = connect_db()
    if not conn:
        return [], [], []

    logs = Database.get_admin_employee_activity(conn)
    records = Database.get_admin_employee_records(conn)
    department_options = sorted(
        {
            item.get("dept")
            for item in [*logs, *records]
            if item.get("dept") and item.get("dept") != "N/A"
        }
    )
    return logs, records, department_options


def fetch_dashboard_stats(path, fallback):
    try:
        response = backend_request("GET", path)
        if response.ok:
            payload = response.json()
            if payload.get("success"):
                return payload.get("data", fallback)
    except requests.RequestException as err:
        app.logger.warning("Could not fetch dashboard stats from %s: %s", path, err)
    return fallback


def helper_admin_login(username, password):
    try:
        response = backend_request(
            "POST",
            "/admin/login/auth",
            json={"username": username, "password": password},
        )
        return response.json()
    except requests.RequestException as err:
        app.logger.error("Authentication backend is unavailable: %s", err)
        return {"success": False, "message": "Authentication service is unavailable."}


def helper_delete_events(event_id, delete_type):
    if delete_type == "single":
        payload = {"event_id": event_id}
        path = "/admin/events/delete-event"
    else:
        payload = {"event_ids": event_id}
        path = "/admin/events/delete-events"

    try:
        response = backend_request("PUT", path, json=payload)
        return response.json()
    except requests.RequestException as err:
        app.logger.error("Could not delete event(s): %s", err)
        return {"success": False, "message": "Backend service is unavailable."}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""

        if not username or not password:
            return jsonify({"success": False, "message": "Please enter a username and password."}), 400

        result = helper_admin_login(username, password)
        if result.get("success"):
            session.clear()
            session.permanent = True
            session["logged_in"] = True
            session["admin_username"] = result.get("data", {}).get("username", username)
            return jsonify({"success": True, "redirect_url": url_for("dashboard")})

        return jsonify({"success": False, "message": result.get("message", "Incorrect username or password.")})

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/kiosk/entrance")
def kiosk_entrance():
    session.clear()
    return render_template(
        "kiosk_entrance.html",
        active_visitors=fetch_visitor_logs(status="Checked In"),
        kiosk_data=get_kiosk_data_with_live_feed(),
    )


@app.route("/kiosk/exit")
def kiosk_exit():
    session.clear()
    return render_template("kiosk_exit.html", kiosk_data=get_kiosk_data_with_live_feed())


@app.route("/kiosk/employee/select-event")
def kiosk_employee_select_event():
    session.clear()
    return render_template("kiosk_event_select.html", events=fetch_kiosk_live_events())


@app.route("/kiosk/employee")
def kiosk_employee():
    session.clear()
    instance_id = request.args.get("instance_id", type=int)
    events = fetch_kiosk_live_events()
    selected_event = next((event for event in events if event.get("instance_id") == instance_id), None)

    return render_template(
        "kiosk_employee.html",
        event_name=selected_event.get("name", "General Attendance") if selected_event else "General Attendance",
        event_id=selected_event.get("event_id") if selected_event else None,
        instance_id=instance_id,
        kiosk_data=get_kiosk_data_with_live_feed(),
    )


@app.route("/kiosk/visitor")
def kiosk_visitor():
    session.clear()
    return render_template(
        "kiosk_visitor.html",
        active_visitors=fetch_visitor_logs(status="Checked In"),
    )


@app.route("/api/visitor/checkin", methods=["POST"])
def visitor_checkin():
    name = (request.form.get("name") or "").strip()
    purpose = (request.form.get("purpose") or "").strip()
    details = (request.form.get("details") or "").strip()
    source = resolve_visitor_source(request.form.get("source"), fallback="kiosk_visitor")

    if not name or not purpose:
        flash("Check-in failed. Name and purpose are required.", "danger")
        return redirect(url_for(source))

    conn = connect_db()
    if not conn:
        flash("Check-in failed. Visitor database is unavailable.", "danger")
        return redirect(url_for(source))

    result = Database(conn, (name, purpose, details, "Gate 1")).add_visitor_log()
    flash(
        f"Welcome, {name}. Check-in successful." if result.get("success") else result.get("message", "Check-in failed."),
        "success" if result.get("success") else "danger",
    )
    return redirect(url_for(source))


@app.route("/api/visitor/checkout/<visitor_id>", methods=["POST"])
def visitor_checkout(visitor_id):
    source = resolve_visitor_source(request.args.get("source"), fallback="kiosk_entrance")
    conn = connect_db()
    if not conn:
        flash("Check-out failed. Visitor database is unavailable.", "danger")
        return redirect(url_for(source))

    result = Database(conn, (visitor_id, "Gate 2")).checkout_visitor_log()
    flash(
        f"Goodbye, {result.get('name', 'Visitor')}. Check-out successful."
        if result.get("success")
        else result.get("message", "Visitor not found."),
        "success" if result.get("success") else "danger",
    )
    return redirect(url_for(source))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        events=fetch_backend_events(),
        overall_stats=fetch_dashboard_stats("/admin/dashboard/analytics/overall", dict(MOCK_DASHBOARD_STATS)),
        student_stats=fetch_dashboard_stats("/admin/dashboard/analytics/students", dict(MOCK_STUDENT_STATS)),
        employee_stats=fetch_dashboard_stats("/admin/dashboard/analytics/employees", dict(MOCK_EMPLOYEE_STATS)),
        logs=fetch_employee_attendance(),
        user=session.get("admin_username", "Admin"),
    )


@app.route("/events")
@login_required
def manage_events():
    return render_template(
        "events.html",
        events=fetch_backend_events(),
        departments=fetch_departments(),
    )


@app.route("/admin/students")
@login_required
def admin_students():
    logs, records, course_options = fetch_admin_students_page_data()
    return render_template(
        "student_logs.html",
        logs=logs,
        records=records,
        course_options=course_options,
    )


@app.route("/admin/employees")
@login_required
def admin_employees():
    logs, records, department_options = fetch_admin_employees_page_data()
    return render_template(
        "employee_logs.html",
        logs=logs,
        records=records,
        department_options=department_options,
    )


@app.route("/admin/visitors")
@login_required
def admin_visitors():
    search_term = (request.args.get("search") or "").strip()
    visit_date = (request.args.get("date") or "").strip()
    visitors = fetch_visitor_logs(search_term=search_term or None, visit_date=visit_date or None)
    return render_template(
        "admin_visitors.html",
        visitors=visitors,
        search_term=search_term,
        visit_date=visit_date,
    )


@app.route("/admin/visitors/<visitor_id>", methods=["PUT"])
@login_required
def update_visitor(visitor_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    purpose = (data.get("purpose") or "").strip()
    details = (data.get("details") or "").strip()

    conn = connect_db()
    if not conn:
        return jsonify({"success": False, "message": "Database offline"}), 500

    result = Database(conn, (visitor_id, name, purpose, details)).update_visitor_record()
    return jsonify(result), (200 if result.get("success") else 400)


@app.route("/admin/visitors/<visitor_id>", methods=["DELETE"])
@login_required
def delete_visitor(visitor_id):
    conn = connect_db()
    if not conn:
        return jsonify({"success": False, "message": "Database offline"}), 500

    result = Database(conn, (visitor_id,)).delete_visitor_record()
    return jsonify(result), (200 if result.get("success") else 404)


@app.route("/analytics/employee")
@login_required
def analytics_employee():
    return redirect(url_for("admin_employees"))


@app.route("/analytics/students")
@login_required
def analytics_students():
    return redirect(url_for("admin_students"))


@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html", events=fetch_report_events(), reports=MOCK_REPORTS)


@app.route("/reports/sample")
@login_required
def sample_report():
    return render_template("sample_report.html", current_date=datetime.now().strftime("%B %d, %Y - %I:%M %p"))


@app.route("/admin/events/add", methods=["POST"])
@login_required
def add_event():
    name = request.form.get("name")
    event_type = request.form.get("type")
    event_date = request.form.get("event_date")
    day_of_week = request.form.get("day_of_week")
    time_start = request.form.get("time_start")
    time_end = request.form.get("time_end")
    location = request.form.get("location")
    department_ids = request.form.getlist("dept")
    roster_file = request.files.get("roster_file")

    frequency = (request.form.get("frequency") or "").upper()
    if frequency == "ONE-TIME":
        frequency = "ONCE"

    has_file = bool(roster_file and roster_file.filename)
    if not department_ids and not has_file:
        flash("Failed to add event. Select at least one department or upload a roster file.", "danger")
        return redirect(url_for("manage_events"))

    participants_type = "hybrid" if department_ids and has_file else "grouped" if department_ids else "custom"
    custom_participants = []

    if has_file:
        if not roster_file.filename.lower().endswith(".csv"):
            flash("Please upload a valid .csv file.", "warning")
            return redirect(url_for("manage_events"))
        try:
            file_contents = roster_file.read().decode("utf-8-sig")
            csv_stream = io.StringIO(file_contents)
            for row in csv.DictReader(csv_stream):
                if row.get("ID"):
                    custom_participants.append(row["ID"].strip())
        except Exception as err:
            flash(f"Failed to process the CSV file: {err}", "danger")
            return redirect(url_for("manage_events"))

    payload = {
        "event_name": name,
        "event_type": event_type,
        "frequency": frequency,
        "location": location,
        "event_date": event_date,
        "time_start": time_start,
        "time_end": time_end,
        "day": day_of_week,
        "participants_type": participants_type,
        "grouped_participants": department_ids,
        "custom_participants": custom_participants,
    }

    try:
        response = backend_request("POST", "/admin/dashboard/add-events", json=payload)
        api_data = response.json()
        if response.ok and api_data.get("success"):
            flash(f'Event "{name}" added successfully.', "success")
        else:
            flash(f'Failed to add event: {api_data.get("message", "Unknown API error")}', "danger")
    except requests.RequestException as err:
        app.logger.error("Could not add event: %s", err)
        flash(f'Event "{name}" failed to add. Could not connect to the backend.', "danger")

    return redirect(url_for("manage_events"))


@app.route("/admin/events/delete/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    if event_id <= 2:
        return jsonify({"success": False, "message": "Cannot delete default system events."}), 403

    result = helper_delete_events(event_id, "single")
    return jsonify(result), (200 if result.get("success") else 500)


@app.route("/admin/events/bulk-delete", methods=["POST"])
@login_required
def bulk_delete_events():
    data = request.get_json(silent=True) or {}
    event_ids = data.get("event_ids", [])
    valid_ids = [str(event_id) for event_id in event_ids if int(event_id) > 2]

    if not valid_ids:
        return jsonify({"success": False, "message": "Cannot delete default system events."}), 403

    result = helper_delete_events(valid_ids, "bulk")
    return jsonify(result), (200 if result.get("success") else 500)


@app.route("/admin/profile/update", methods=["POST"])
@login_required
def update_profile():
    flash("Admin profile updated successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/check_student_status", methods=["POST"])
def check_student_status():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")

    mock_students = {
        "2026-001": {"name": "Maria Clara", "course": "BS Psychology", "status": "TIMED IN"},
        "2026-002": {"name": "Jose Rizal", "course": "BS Accountancy", "status": "TIMED OUT"},
        "2026-003": {"name": "Andres Bonifacio", "course": "BS Information Technology", "status": "TIMED IN"},
    }

    if student_id in mock_students:
        student = mock_students[student_id]
        return jsonify(
            {
                "status": "found",
                "name": student["name"],
                "course": student["course"],
                "attendance_status": student["status"],
            }
        )

    return jsonify({"status": "not_found"})


@app.route("/api/kiosk/live-events")
def kiosk_live_event():
    try:
        response = backend_request("GET", "/kiosk/employee/select-event")
        return jsonify(response.json()), response.status_code
    except requests.RequestException as err:
        app.logger.error("Kiosk live events bridge failed: %s", err)
        return jsonify({"success": False, "message": "Backend service unavailable."}), 503


@app.route("/api/admin/live-events")
def admin_live_event():
    try:
        response = backend_request("GET", "/admin/dashboard/events")
        return jsonify(response.json()), response.status_code
    except requests.RequestException as err:
        app.logger.error("Admin live events bridge failed: %s", err)
        return jsonify({"success": False, "message": "Backend service unavailable."}), 503


@app.route("/api/admin/live-departments")
def admin_live_departments():
    try:
        response = backend_request("GET", "/admin/dashboard/events/live-departments")
        return jsonify(response.json()), response.status_code
    except requests.RequestException as err:
        app.logger.error("Admin live departments bridge failed: %s", err)
        return jsonify({"success": False, "message": "Backend service unavailable."}), 503


@app.route("/api/retrieve/events")
def retrieve_all_events_for_reports():
    return jsonify(fetch_report_events())


@app.route("/api/retrieve/departments")
def retrieve_departments():
    return jsonify(fetch_departments())


@app.route("/api/attendance/update", methods=["POST"])
@login_required
def update_attendance_proxy():
    data = request.get_json(silent=True) or {}
    if not data.get("attendance_id") or not data.get("status"):
        return jsonify({"success": False, "message": "Missing attendance_id or status."}), 400

    try:
        response = backend_request("POST", "/api/attendance/update", json=data)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as err:
        app.logger.error("Attendance update proxy failed: %s", err)
        return jsonify({"success": False, "message": "Backend service unavailable."}), 503


@app.route("/generate_report")
@login_required
def generate_report():
    category = request.args.get("category")
    report_type = request.args.get("type")
    filter_value = request.args.get("filter", "All")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if start > end:
                return "<h1>Report Error</h1><p>Invalid date range. 'From' date cannot be after 'To' date.</p>", 400
        except ValueError:
            return "<h1>Report Error</h1><p>Invalid date format. Please use YYYY-MM-DD.</p>", 400

    report_results = fetch_report_data(category, report_type, filter_value, start_date, end_date)
    if "error" in report_results:
        return f"<h1>Report Error</h1><p>{report_results['error']}</p>", 500

    return render_template(
        "sample_report.html",
        current_date=datetime.now().strftime("%B %d, %Y - %I:%M %p"),
        report=report_results["report_data"],
        metrics=report_results["metrics_data"],
        logs=report_results["logs"],
    )


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)

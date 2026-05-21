
import logging
import os
import threading
import time
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import get_config
from database import close_db, connect_db, init_db_pool, release_db_connection
from db_connect import Database, ensure_visitor_valid_until_schema, expire_expired_visitor_accounts


app = Flask(__name__)
app.config.from_object(get_config())
app.secret_key = app.config["SECRET_KEY"]

os.makedirs(os.path.dirname(app.config["LOG_FILE"]) or ".", exist_ok=True)

app.logger.setLevel(getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO))
if not any(isinstance(handler, logging.StreamHandler) for handler in app.logger.handlers):
    app.logger.addHandler(logging.StreamHandler())

log_file = os.path.abspath(app.config["LOG_FILE"])
if not any(
    isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", None) == log_file
    for handler in app.logger.handlers
):
    app.logger.addHandler(logging.FileHandler(log_file))

CORS(app, origins=app.config["ALLOWED_ORIGINS"])
app.teardown_appcontext(close_db)

EVENT_TYPES = {"Meeting", "Training", "Seminar", "Workshop", "Drill", "Activity", "Flag Ceremony", "Other"}
EVENT_FREQUENCIES = {"ONCE", "DAILY", "WEEKLY"}
EVENT_DAYS = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}


def clean_text(value):
    return str(value).strip() if value is not None else ""


def normalize_event_frequency(value):
    frequency = clean_text(value).upper().replace("_", "-")
    if frequency in {"ONE-TIME", "ONETIME"}:
        return "ONCE"
    return frequency


def parse_event_time(value):
    for time_format in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, time_format).time()
        except ValueError:
            continue
    raise ValueError("Invalid time format")


def normalize_requested_log_type(value):
    action = clean_text(value).lower().replace("_", " ").replace("-", " ")
    if action in {"entry", "entrance", "in", "time in"}:
        return "Entry"
    if action in {"exit", "out", "outside", "time out"}:
        return "Exit"
    return None


def get_kiosk_actor_label(role):
    actor = clean_text(role).lower()
    if actor in {"student", "employee", "visitor"}:
        return actor
    return "user"


def build_kiosk_block_message(requested_log_type, current_status, role):
    action = "Entry" if requested_log_type == "Entry" else "Exit"
    status = "inside" if clean_text(current_status).lower() == "inside" else "outside"
    actor = get_kiosk_actor_label(role)
    return f"{action} denied: {actor} is already {status}."


def validation_error(errors):
    message = " ".join(errors)
    return jsonify({"success": False, "message": message, "error": message, "errors": errors}), 400


INSTANCE_GENERATOR_CHECK_SECONDS = int(os.getenv("INSTANCE_GENERATOR_CHECK_SECONDS", "60"))
INSTANCE_GENERATOR_RUN_INTERVAL_SECONDS = int(os.getenv("INSTANCE_GENERATOR_RUN_INTERVAL_SECONDS", "3600"))
INSTANCE_GENERATOR_LOOKAHEAD_DAYS = int(os.getenv("INSTANCE_GENERATOR_LOOKAHEAD_DAYS", "7"))
INSTANCE_GENERATOR_STATE = {
    "running": False,
    "last_started_at": None,
    "last_finished_at": None,
    "last_success_at": None,
    "last_error": None,
    "last_result": None,
    "last_trigger": None,
    "next_check_at": None,
    "next_run_at": None,
    "run_interval_seconds": INSTANCE_GENERATOR_RUN_INTERVAL_SECONDS,
    "lookahead_days": INSTANCE_GENERATOR_LOOKAHEAD_DAYS,
}
_instance_generator_lock = threading.Lock()
_instance_generator_thread_started = False
_last_scheduled_generation_at = None


def _iso_timestamp(value):
    return value.isoformat(sep=" ", timespec="seconds") if value else None


def _copy_instance_generator_state():
    with _instance_generator_lock:
        return dict(INSTANCE_GENERATOR_STATE)


def generate_event_instances_for_range(start_date=None, days=7, trigger="manual"):
    conn = connect_db()
    if not conn:
        return {
            "success": False,
            "message": "Database offline",
            "created": 0,
            "existing": 0,
            "matched": 0,
            "failed": 0,
            "trigger": trigger,
        }

    start_date = start_date or date.today()
    days = max(1, int(days or 1))
    target_dates = [start_date + timedelta(days=i) for i in range(days)]
    created_count = 0
    existing_count = 0
    matched_count = 0
    failed_count = 0

    for target_date in target_dates:
        day_name = target_date.strftime("%A")
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT event_id, event_name, frequency, event_date
                FROM events
                WHERE active = 1 AND (
                    (frequency = 'WEEKLY' AND day = %s AND event_date <= %s) OR
                    (frequency = 'DAILY' AND event_date <= %s) OR
                    (frequency = 'ONCE' AND event_date = %s)
                )
                """,
                (day_name, target_date, target_date, target_date),
            )
            events = cursor.fetchall()
        finally:
            cursor.close()

        matched_count += len(events)
        for event in events:
            event_id = event["event_id"]
            check_cursor = conn.cursor(dictionary=True)
            try:
                check_cursor.execute(
                    """
                    SELECT instance_id
                    FROM event_instances
                    WHERE event_id = %s AND event_date = %s
                    LIMIT 1
                    """,
                    (event_id, target_date),
                )
                already_exists = bool(check_cursor.fetchone())
            finally:
                check_cursor.close()

            instance_result = Database(conn, (event_id, target_date)).add_event_instances()
            if instance_result.get("success"):
                if already_exists:
                    existing_count += 1
                else:
                    created_count += 1
            else:
                failed_count += 1
                app.logger.error(
                    "Failed to add instance for event_id=%s date=%s: %s",
                    event_id,
                    target_date,
                    instance_result.get("message"),
                )

    return {
        "success": failed_count == 0,
        "message": f"Event instances generated for the next {days} day(s).",
        "created": created_count,
        "existing": existing_count,
        "matched": matched_count,
        "failed": failed_count,
        "date_range": f"{target_dates[0]} to {target_dates[-1]}",
        "trigger": trigger,
    }


def run_instance_generation_job(trigger="manual", start_date=None, days=None):
    now = datetime.now()
    generation_days = days or INSTANCE_GENERATOR_LOOKAHEAD_DAYS
    with _instance_generator_lock:
        if INSTANCE_GENERATOR_STATE["running"]:
            return {
                "success": False,
                "message": "Event instance generation is already running.",
                "state": dict(INSTANCE_GENERATOR_STATE),
            }
        INSTANCE_GENERATOR_STATE.update(
            {
                "running": True,
                "last_started_at": _iso_timestamp(now),
                "last_finished_at": None,
                "last_error": None,
                "last_trigger": trigger,
            }
        )

    try:
        result = generate_event_instances_for_range(
            start_date=start_date,
            days=generation_days,
            trigger=trigger,
        )
        finished_at = datetime.now()
        with _instance_generator_lock:
            INSTANCE_GENERATOR_STATE.update(
                {
                    "running": False,
                    "last_finished_at": _iso_timestamp(finished_at),
                    "last_success_at": _iso_timestamp(finished_at) if result.get("success") else INSTANCE_GENERATOR_STATE["last_success_at"],
                    "last_error": None if result.get("success") else result.get("message"),
                    "last_result": result,
                }
            )
        app.logger.info(
            "Event instance generation finished: trigger=%s created=%s existing=%s failed=%s",
            trigger,
            result.get("created", 0),
            result.get("existing", 0),
            result.get("failed", 0),
        )
        return result
    except Exception as err:
        finished_at = datetime.now()
        result = {
            "success": False,
            "message": str(err),
            "created": 0,
            "existing": 0,
            "matched": 0,
            "failed": 1,
            "trigger": trigger,
        }
        with _instance_generator_lock:
            INSTANCE_GENERATOR_STATE.update(
                {
                    "running": False,
                    "last_finished_at": _iso_timestamp(finished_at),
                    "last_error": str(err),
                    "last_result": result,
                }
            )
        app.logger.exception("Event instance generation failed")
        return result


def _instance_generation_scheduler_loop():
    global _last_scheduled_generation_at

    while True:
        now = datetime.now()
        next_check = now + timedelta(seconds=INSTANCE_GENERATOR_CHECK_SECONDS)
        next_run = (
            now
            if _last_scheduled_generation_at is None
            else _last_scheduled_generation_at + timedelta(seconds=INSTANCE_GENERATOR_RUN_INTERVAL_SECONDS)
        )
        with _instance_generator_lock:
            INSTANCE_GENERATOR_STATE["next_check_at"] = _iso_timestamp(next_check)
            INSTANCE_GENERATOR_STATE["next_run_at"] = _iso_timestamp(next_run)

        should_run = (
            now >= next_run
            and not _copy_instance_generator_state().get("running")
        )

        if should_run:
            app.logger.info(
                "Hourly event instance scheduler starting for %s day(s).",
                INSTANCE_GENERATOR_LOOKAHEAD_DAYS,
            )
            with app.app_context():
                result = run_instance_generation_job(trigger="scheduler")
                close_db(None)
            _last_scheduled_generation_at = datetime.now()

        time.sleep(INSTANCE_GENERATOR_CHECK_SECONDS)


def start_instance_generation_scheduler():
    global _instance_generator_thread_started

    if _instance_generator_thread_started:
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    scheduler_thread = threading.Thread(
        target=_instance_generation_scheduler_loop,
        name="event-instance-generator",
        daemon=True,
    )
    scheduler_thread.start()
    _instance_generator_thread_started = True
    app.logger.info("Event instance background scheduler started.")

# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

with app.app_context():
    init_db_pool()
    conn = connect_db()
    if conn:
        ensure_visitor_valid_until_schema(conn, logger=app.logger)
        release_db_connection(conn)

app.teardown_appcontext(close_db)


@app.before_request
def disable_expired_visitor_accounts():
    if request.endpoint == "static":
        return

    conn = connect_db()
    if not conn:
        return

    expire_expired_visitor_accounts(conn, logger=app.logger)


# ==============================================================================
# ADMIN AUTHENTICATION
# ==============================================================================

@app.route('/admin/login/auth', methods=['POST'])
def login():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

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
        data = request.get_json(silent=True) or {}
        print(data)

        if not data or not data.get('id'):
            return jsonify({"success": False, "message": "ID is required. No ID string attached"}), 400
        
        scan_id = clean_text(data.get('id'))
        requested_log_type = None
        if data.get('requested_log_type'):
            requested_log_type = normalize_requested_log_type(data.get('requested_log_type'))
            if not requested_log_type:
                return jsonify({"success": False, "message": "Invalid kiosk action requested."}), 400
        
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
        current_status_normalized = clean_text(current_status).lower() or "outside"

        full_name = user_data.get('full_name', 'Unknown User')
        affiliation = user_data.get('affiliation', 'N/A')

        print(f"User found: ID {user_id}, Role: {role}, Status: {current_status}")

        if requested_log_type == "Entry" and current_status_normalized == "inside":
            return jsonify({
                "success": False,
                "message": "Cannot allow entry. User is currently inside.",
                "status": "blocked",
                "error_code": "already_inside",
                "current_status": "Inside",
                "requested_log_type": requested_log_type,
                "name": full_name,
                "affiliation": affiliation,
            }), 409

        if requested_log_type == "Exit" and current_status_normalized != "inside":
            return jsonify({
                "success": False,
                "message": "Cannot allow exit. User is currently outside.",
                "status": "blocked",
                "error_code": "already_outside",
                "current_status": "Outside",
                "requested_log_type": requested_log_type,
                "name": full_name,
                "affiliation": affiliation,
            }), 409

        # 3. CHANGE STATUS
        db_status_param = (user_id, current_status, role, requested_log_type)
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

        data = request.get_json(silent=True) or {}
        if not data:
            return validation_error(["No JSON data provided."])

        event_name = clean_text(data.get('event_name'))
        event_type = clean_text(data.get('event_type'))
        frequency = normalize_event_frequency(data.get('frequency'))
        ed = clean_text(data.get('event_date'))
        day = clean_text(data.get('day'))
        time_start = clean_text(data.get('time_start'))
        time_end = clean_text(data.get('time_end'))
        location = clean_text(data.get('location'))
        participants_type = clean_text(data.get('participants_type')).lower()

        validation_errors = []
        if not event_name:
            validation_errors.append("Event name is required.")
        if event_type not in EVENT_TYPES:
            validation_errors.append("Select a valid event type.")
        if frequency not in EVENT_FREQUENCIES:
            validation_errors.append("Select a valid event frequency.")
        if not location:
            validation_errors.append("Location is required.")
        if not time_start:
            validation_errors.append("Start time is required.")
        if not time_end:
            validation_errors.append("End time is required.")
        if frequency != 'DAILY' and not ed:
            validation_errors.append("Event date is required.")
        if frequency == 'WEEKLY' and day not in EVENT_DAYS:
            validation_errors.append("Event day is required for weekly events.")

        participants = None
        if participants_type == 'grouped':
            participants = [
                clean_text(item)
                for item in data.get('grouped_participants') or []
                if clean_text(item).isdigit()
            ]
            if not participants:
                validation_errors.append("Select at least one participant department.")
        elif participants_type == 'custom':
            participants = [clean_text(item) for item in data.get('custom_participants') or [] if clean_text(item)]
            if not participants:
                validation_errors.append("Provide at least one participant ID.")
        elif participants_type == 'hybrid':
            participants = {
                "grouped_participants": [
                    clean_text(item)
                    for item in data.get('grouped_participants') or []
                    if clean_text(item).isdigit()
                ],
                "custom_participants": [
                    clean_text(item) for item in data.get('custom_participants') or [] if clean_text(item)
                ],
            }
            if not participants["grouped_participants"] and not participants["custom_participants"]:
                validation_errors.append("Select departments or provide participant IDs.")
        else:
            validation_errors.append("Select a valid participants type.")

        if validation_errors:
            return validation_error(validation_errors)

        cd = date.today()

        if frequency == 'DAILY' and not ed:
            ed = cd.isoformat()

        try:
            event_date = datetime.strptime(ed, '%Y-%m-%d').date()
            current_date = cd
        except ValueError:
            return validation_error(["Event date must use YYYY-MM-DD format."])
            
        if event_date < current_date:
            return validation_error(["Event date cannot be in the past."])

        try:
            parsed_start = parse_event_time(time_start)
            parsed_end = parse_event_time(time_end)
        except ValueError:
            return validation_error(["Start time and end time must use HH:MM format."])

        if parsed_end <= parsed_start:
            return validation_error(["End time must be later than start time."])

        event_date = ed

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
# ENDPOINT 1: Event Instance Generator (manual, scheduler, or external cron)

@app.route("/admin/generate-daily-instances", methods=["POST"])
def generate_daily_instances():
    """
    Triggered by the background scheduler or an external cron/Task Scheduler.
    Generates instances for the configured lookahead window including:
    - WEEKLY events for their scheduled days
    - DAILY events for every day
    - ONCE events on their scheduled date
    """
    result = run_instance_generation_job(trigger="manual")
    return jsonify(result), (200 if result.get("success") else 409)


@app.route("/admin/generate-daily-instances/status", methods=["GET"])
def generate_daily_instances_status():
    return jsonify({"success": True, "job": _copy_instance_generator_state()}), 200


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
@app.route("/admin/update-attendance", methods=["PUT", "POST"])
@app.route("/api/attendance/update", methods=["POST"])
def update_attendance():
    conn = None
    try:
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        data = request.get_json() or {}
        status = data.get('status')
        remarks = data.get('remarks', None)

        if status not in ['Present', 'Absent', 'Late', 'Excused']:
            return jsonify({"success": False, "message": "Invalid status option"}), 400

        attendance_id = data.get('attendance_id')
        if attendance_id:
            params = (status, remarks, attendance_id)
        else:
            user_id = data.get('user_id')
            instance_id = data.get('instance_id')
            if not user_id or not instance_id:
                return jsonify({"success": False, "message": "Missing attendance_id or user_id + instance_id"}), 400
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
                        "data": events
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

        try:
            event_id = int(data['event_id'])
        except (KeyError, TypeError, ValueError):
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

        limit = request.args.get("limit", default=6, type=int) or 6
        limit = min(max(limit, 1), 20)
        logs = Database.get_student_logs(conn, limit=limit)

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
        instance_id = (request.args.get("instance_id") or "").strip() or None
        conn = connect_db()
        if not conn:
            return jsonify({"success": False, "message": "Database offline"}), 500

        stats = Database.get_employee_dashboard_stats(conn, instance_id=instance_id)
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
            release_db_connection(conn)

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
            release_db_connection(conn)

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
            release_db_connection(conn)

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
            release_db_connection(conn)

start_instance_generation_scheduler()

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], host='0.0.0.0', port=5001)

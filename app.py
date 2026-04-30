from datetime import date, datetime, timedelta
from functools import wraps
import csv
import glob
import io
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, urlsplit

import requests
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.routing import BuildError
from werkzeug.utils import secure_filename

from app_tasks import fetch_report_data
from config import get_config
from database import close_db, connect_db, init_db_pool, release_db_connection
from db_connect import Database, EmployeeModel, StudentModel, VISITOR_PURPOSES, normalize_visitor_purpose
from extensions import cache
from utils.employee_schema import (
    build_person_name_match_keys,
    build_employee_signature,
    department_lookup_key,
    normalize_text,
    validate_department_name,
    validate_employee_fields,
)
from utils.sendEmail import send_email
from utils.student_schema import (
    normalize_course_name,
    normalize_student_id,
    normalize_student_name,
    validate_course_name,
    validate_student_fields,
)


app = Flask(__name__)
app.config.from_object(get_config())
app.permanent_session_lifetime = timedelta(minutes=3)

os.makedirs(os.path.dirname(app.config["LOG_FILE"]) or ".", exist_ok=True)
REPORT_ARCHIVE_DIR = os.path.join(app.static_folder, "reports")
LEGACY_REPORT_PATTERNS = ("attendance_report.pdf", "report_*.pdf")
os.makedirs(REPORT_ARCHIVE_DIR, exist_ok=True)
employee_model = EmployeeModel()
student_model = StudentModel()
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
    "tardiness_labels": ["N/A"] * 7,
    "dept_participation": [],
    "avg_tardiness": "0 mins",
    "on_time_rate": "N/A",
    "on_time_percentage": 0,
    "participation_level": "N/A",
    "target_date": "N/A",
    "upcoming_events": [],
    "recent_activity": [],
    "leaderboard": [],
    "dept_comparison": [],
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

EVENT_TYPES = {"Meeting", "Training", "Seminar", "Workshop", "Drill", "Activity", "Flag Ceremony", "Other"}
EVENT_FREQUENCIES = {"ONCE", "DAILY", "WEEKLY"}
EVENT_DAYS = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}
EMPLOYEE_UPLOAD_REQUIRED_COLUMNS = ["EMPLOYEE NAME", "DEPARTMENT"]
EMPLOYEE_UPLOAD_OPTIONAL_COLUMNS = ["POSITION"]
STUDENT_UPLOAD_REQUIRED_COLUMNS = ["STUDENT ID", "STUDENT NAME"]
STUDENT_UPLOAD_OPTIONAL_COLUMNS = ["COURSE", "COURSE ID", "STATUS"]


def sanitize_report_archive_filename(filename, default_stem="report"):
    candidate = secure_filename(os.path.basename(filename or "")).strip("._")
    if not candidate:
        candidate = f"{default_stem}.pdf"

    stem, ext = os.path.splitext(candidate)
    stem = re.sub(r"_+", "_", stem).strip("._") or default_stem
    ext = ".pdf" if ext.lower() != ".pdf" else ext.lower()
    return f"{stem[:120]}{ext}"


def build_report_archive_filename(category, report_data):
    pieces = [
        category or "report",
        report_data.get("event_name") or report_data.get("title") or "",
        report_data.get("department") or "",
        report_data.get("date_range") or "",
    ]
    normalized_parts = []
    for piece in pieces:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(piece).strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        if cleaned and cleaned.lower() != "all":
            normalized_parts.append(cleaned[:40])

    archive_stem = "_".join(normalized_parts) or "report"
    return sanitize_report_archive_filename(f"{archive_stem}.pdf")


def get_unique_report_archive_path(filename):
    archive_name = sanitize_report_archive_filename(filename)
    archive_path = os.path.join(REPORT_ARCHIVE_DIR, archive_name)
    if not os.path.exists(archive_path):
        return archive_path, archive_name

    stem, ext = os.path.splitext(archive_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    counter = 1
    while True:
        candidate_name = f"{stem}_{timestamp}_{counter}{ext}"
        candidate_path = os.path.join(REPORT_ARCHIVE_DIR, candidate_name)
        if not os.path.exists(candidate_path):
            return candidate_path, candidate_name
        counter += 1


def relocate_legacy_report_files():
    project_root = os.path.abspath(app.root_path)
    moved_reports = []

    for pattern in LEGACY_REPORT_PATTERNS:
        for source_path in glob.glob(os.path.join(project_root, pattern)):
            if not os.path.isfile(source_path):
                continue

            archive_path, archive_name = get_unique_report_archive_path(os.path.basename(source_path))
            if os.path.abspath(source_path) == os.path.abspath(archive_path):
                continue

            os.replace(source_path, archive_path)
            moved_reports.append((os.path.basename(source_path), archive_name))

    if moved_reports:
        app.logger.info("Relocated %s legacy report file(s) into %s.", len(moved_reports), REPORT_ARCHIVE_DIR)


def _format_report_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_value = float(size_bytes)
    for unit in ("KB", "MB", "GB"):
        size_value /= 1024.0
        if size_value < 1024 or unit == "GB":
            return f"{size_value:.1f} {unit}"

    return f"{size_bytes} B"


def get_archived_reports():
    reports = []
    for entry in os.scandir(REPORT_ARCHIVE_DIR):
        if not entry.is_file() or not entry.name.lower().endswith(".pdf"):
            continue

        stats = entry.stat()
        modified_at = datetime.fromtimestamp(stats.st_mtime)
        reports.append(
            {
                "icon": "file-earmark-pdf text-danger",
                "name": entry.name,
                "time": modified_at.strftime("Generated %b %d, %Y %I:%M %p"),
                "size": _format_report_file_size(stats.st_size),
                "url": url_for("static", filename=f"reports/{entry.name}"),
                "sort_timestamp": stats.st_mtime,
            }
        )

    return sorted(reports, key=lambda report: report["sort_timestamp"], reverse=True)


relocate_legacy_report_files()


def build_sample_report_payload():
    return {
        "title": "Report Preview",
        "event_name": "",
        "department": "ALL",
        "date_range": datetime.now().strftime("%Y-%m-%d"),
        "archive_filename": "report_preview.pdf",
    }


def resolve_archive_report_url():
    try:
        return url_for("archive_report")
    except BuildError:
        return url_for("sample_report")


def resolve_report_context(category, report_type, filter_value, start_date, end_date):
    report_results = fetch_report_data(category, report_type, filter_value, start_date, end_date)
    if "error" in report_results:
        return None, report_results["error"]

    report_data = dict(report_results["report_data"])
    report_data["archive_filename"] = build_report_archive_filename(category, report_data)
    return report_data, None


def load_archived_report_attachment(category, report_type, filter_value, start_date, end_date):
    report_data, error = resolve_report_context(category, report_type, filter_value, start_date, end_date)
    if error:
        return None, None, error

    archive_path = os.path.join(REPORT_ARCHIVE_DIR, report_data["archive_filename"])
    if not os.path.exists(archive_path):
        return (
            None,
            report_data,
            "Archived PDF not found yet. Use 'Download and Archive PDF' first, then send it by email.",
        )

    with open(archive_path, "rb") as archived_pdf:
        return archived_pdf.read(), report_data, None

def normalize_event_frequency(value):
    frequency = (value or "").strip().upper().replace("_", "-")
    if frequency in {"ONE-TIME", "ONETIME"}:
        return "ONCE"
    return frequency


def split_manual_participant_ids(values):
    participant_ids = []
    for value in values:
        for token in re.split(r"[,;\n\r]+", value or ""):
            participant_id = token.strip()
            if participant_id:
                participant_ids.append(participant_id)
    return participant_ids


def unique_values(values):
    seen = set()
    unique = []
    for value in values:
        key = value.upper() if isinstance(value, str) else value
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique


def clean_upload_text(text):
    return normalize_text(text)


def build_name_match_lookup(names):
    lookup = {}
    for name in names:
        register_name_match_source(lookup, name, name)
    return lookup


def register_name_match_source(lookup, name, source):
    for key in build_person_name_match_keys(name):
        lookup.setdefault(key, set()).add(source)


def find_name_match_sources(name, lookup):
    matches = set()
    for key in build_person_name_match_keys(name):
        matches.update(lookup.get(key, set()))
    return matches


def has_name_match_conflict(name, lookup, exclude_sources=None):
    matches = find_name_match_sources(name, lookup)
    if exclude_sources:
        matches.difference_update(
            {
                source
                for source in exclude_sources
                if source is not None and str(source).strip() != ""
            }
        )
    return bool(matches)


def same_role_name_conflict_error(role):
    return (
        f"A similar name already exists in {role} records. "
        "Please review the existing records first."
    )


def cross_role_name_conflict_error(source_role, counterpart_role):
    source_article = "an" if source_role == "employee" else "a"
    counterpart_article = "an" if counterpart_role == "employee" else "a"
    return (
        f"A similar name already exists in {counterpart_role} records. "
        f"A person cannot be both {source_article} {source_role} and {counterpart_article} {counterpart_role}. "
        "Please review the existing records first."
    )


def _excel_column_index(cell_ref):
    match = re.match(r"([A-Z]+)", (cell_ref or "").upper())
    if not match:
        return 0

    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - ord("A") + 1)
    return max(index - 1, 0)


def _xlsx_cell_value(cell, shared_strings, namespace):
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//a:t", namespace))

    value_node = cell.find("a:v", namespace)
    raw_value = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s" and raw_value != "":
        try:
            return shared_strings[int(raw_value)]
        except (ValueError, IndexError):
            return raw_value

    return raw_value


def _read_xlsx_rows(file):
    namespace = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    relationship_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

    try:
        workbook_bytes = file.read()
        with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as workbook:
            shared_strings = []
            if "xl/sharedStrings.xml" in workbook.namelist():
                root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
                for string_item in root.findall("a:si", namespace):
                    shared_strings.append(
                        "".join(text.text or "" for text in string_item.findall(".//a:t", namespace))
                    )

            workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
            rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
            rel_map = {
                rel.attrib["Id"]: rel.attrib["Target"]
                for rel in rels_root
                if rel.attrib.get("Id") and rel.attrib.get("Target")
            }

            sheets = workbook_root.find("a:sheets", namespace)
            if sheets is None or not list(sheets):
                return {"success": False, "error": "The workbook does not contain any sheets."}

            first_sheet = list(sheets)[0]
            relationship_id = first_sheet.attrib.get(relationship_ns)
            target = rel_map.get(relationship_id)
            if not target:
                return {"success": False, "error": "Could not resolve the first worksheet in the workbook."}

            sheet_path = target if target.startswith("xl/") else f"xl/{target}"
            sheet_root = ET.fromstring(workbook.read(sheet_path))

            rows = []
            for row in sheet_root.findall(".//a:sheetData/a:row", namespace):
                source_row_number = int(row.attrib.get("r") or 0)
                values_by_index = {}
                max_index = -1

                for cell in row.findall("a:c", namespace):
                    column_index = _excel_column_index(cell.attrib.get("r"))
                    values_by_index[column_index] = _xlsx_cell_value(cell, shared_strings, namespace)
                    max_index = max(max_index, column_index)

                row_values = [
                    values_by_index.get(index, "")
                    for index in range(max_index + 1)
                ] if max_index >= 0 else []

                rows.append({"source_row_number": source_row_number, "values": row_values})

            return {"success": True, "rows": rows}
    except zipfile.BadZipFile:
        return {"success": False, "error": "The uploaded .xlsx file is not a valid Excel workbook."}
    except ET.ParseError as err:
        return {"success": False, "error": f"Could not read the Excel workbook structure: {err}"}
    except Exception as err:
        return {"success": False, "error": f"Could not read the Excel workbook: {err}"}
    finally:
        file.seek(0)


def _read_csv_rows(file):
    try:
        content = file.read()
        if isinstance(content, bytes):
            text = content.decode("utf-8-sig")
        else:
            text = str(content)

        reader = csv.reader(io.StringIO(text))
        rows = []
        for index, values in enumerate(reader, start=1):
            rows.append({"source_row_number": index, "values": values})

        return {"success": True, "rows": rows}
    except UnicodeDecodeError as err:
        return {"success": False, "error": f"Could not decode the CSV file: {err}"}
    except Exception as err:
        return {"success": False, "error": f"Could not read the CSV file: {err}"}
    finally:
        file.seek(0)


def _extract_upload_rows(file, file_ext):
    if file_ext == ".xlsx":
        return _read_xlsx_rows(file)
    if file_ext == ".csv":
        return _read_csv_rows(file)
    if file_ext == ".xls":
        return {
            "success": False,
            "error": "Legacy .xls files are not supported by the current server runtime yet. Please save the file as .xlsx or .csv and try again.",
        }

    return {"success": False, "error": "Please upload a valid Excel or CSV file."}


def parse_employee_upload_file(file):
    if not file or not file.filename:
        return {"success": False, "error": "No file uploaded"}

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in {".xls", ".xlsx", ".csv"}:
        return {"success": False, "error": "Please upload a valid Excel or CSV file."}

    extracted = _extract_upload_rows(file, file_ext)
    if not extracted.get("success"):
        return extracted

    required_column_set = set(EMPLOYEE_UPLOAD_REQUIRED_COLUMNS)
    source_rows = extracted.get("rows", [])

    header_index = None
    header_source_row_number = None
    normalized_headers = []

    for index, row in enumerate(source_rows):
        row_values = {
            clean_upload_text(value).upper()
            for value in row.get("values", [])
            if clean_upload_text(value)
        }
        if required_column_set.issubset(row_values):
            header_index = index
            header_source_row_number = row.get("source_row_number") or (index + 1)
            normalized_headers = [clean_upload_text(value).upper() for value in row.get("values", [])]
            break

    if header_index is None:
        return {
            "success": False,
            "error": "Could not find the required headers: Employee Name and Department.",
        }

    missing_columns = [column.title() for column in EMPLOYEE_UPLOAD_REQUIRED_COLUMNS if column not in normalized_headers]
    if missing_columns:
        return {
            "success": False,
            "error": f"Missing required column(s): {', '.join(missing_columns)}",
        }

    parsed_rows = []
    for row in source_rows[header_index + 1:]:
        row_values = list(row.get("values", []))
        row_map = {}
        for column_index, header in enumerate(normalized_headers):
            if not header:
                continue
            row_map[header] = clean_upload_text(row_values[column_index]) if column_index < len(row_values) else ""

        required_values = [row_map.get(column, "") for column in EMPLOYEE_UPLOAD_REQUIRED_COLUMNS]
        optional_values = [row_map.get(column, "") for column in EMPLOYEE_UPLOAD_OPTIONAL_COLUMNS]
        if not any(value.strip() for value in [*required_values, *optional_values]):
            continue

        parsed_rows.append(
            {
                "row_number": row.get("source_row_number") or (header_source_row_number + 1),
                "employee_name": row_map.get("EMPLOYEE NAME", ""),
                "department_name": row_map.get("DEPARTMENT", ""),
                "position": row_map.get("POSITION", ""),
            }
        )

    return {
        "success": True,
        "required_columns": EMPLOYEE_UPLOAD_REQUIRED_COLUMNS,
        "optional_columns": EMPLOYEE_UPLOAD_OPTIONAL_COLUMNS,
        "parsed_rows": parsed_rows,
    }


def validate_employee_upload_rows(conn, parsed_rows):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT department_id, department_name
            FROM departments
            """
        )
        department_lookup = {}
        for department_id, department_name in cursor.fetchall():
            key = department_lookup_key(department_name)
            if key:
                department_lookup.setdefault(key, []).append(
                    {
                        "department_id": department_id,
                        "department_name": clean_upload_text(department_name),
                    }
                )

        cursor.execute(
            """
            SELECT
                employee_name,
                UPPER(TRIM(employee_name)) AS employee_name_key,
                department_id,
                UPPER(TRIM(COALESCE(position, ''))) AS position_key,
                COALESCE(u.active, 1) AS is_active
            FROM employees e
            JOIN users u ON e.user_id = u.user_id
            """
        )
        employee_rows = cursor.fetchall()
        active_signatures = set()
        inactive_signatures = set()
        employee_name_lookup = {}
        for row in employee_rows:
            signature = (row[1], str(row[2]), row[3])
            target = active_signatures if bool(row[4]) else inactive_signatures
            target.add(signature)
            register_name_match_source(employee_name_lookup, row[0], signature)

        cursor.execute(
            """
            SELECT student_name
            FROM students
            """
        )
        student_name_lookup = build_name_match_lookup(row[0] for row in cursor.fetchall())

        valid_rows = []
        errors = []
        seen_signatures = {}
        seen_name_rows = {}

        for row in parsed_rows:
            employee_name = clean_upload_text(row.get("employee_name"))
            department_name = clean_upload_text(row.get("department_name"))
            position = clean_upload_text(row.get("position"))
            row_number = row.get("row_number")

            missing_fields = []
            if not employee_name:
                missing_fields.append("Employee Name")
            if not department_name:
                missing_fields.append("Department")
            if missing_fields:
                errors.append(f"Row {row_number}: Missing {', '.join(missing_fields)}")
                continue

            employee_field_errors = validate_employee_fields(
                employee_name=employee_name,
                position=position,
                require_position=False,
            )
            department_errors = validate_department_name(department_name)
            if employee_field_errors or department_errors:
                errors.append(
                    f"Row {row_number}: {(employee_field_errors + department_errors)[0]}"
                )
                continue

            dept_key = department_lookup_key(department_name)
            department_matches = department_lookup.get(dept_key, [])
            if not department_matches:
                errors.append(f"Row {row_number}: Department not found: {department_name}")
                continue
            if len(department_matches) > 1:
                errors.append(f"Row {row_number}: Department is ambiguous: {department_name}")
                continue
            department_match = department_matches[0]
            department_id = department_match["department_id"]
            resolved_department_name = department_match["department_name"]

            signature = build_employee_signature(employee_name, department_id, position)
            if signature in seen_signatures:
                errors.append(
                    f"Row {row_number}: Duplicate of row {seen_signatures[signature]} in the uploaded file."
                )
                continue

            duplicate_name_rows = find_name_match_sources(employee_name, seen_name_rows)
            if duplicate_name_rows:
                errors.append(
                    f"Row {row_number}: Similar name already appears in row {min(duplicate_name_rows)} of the uploaded file."
                )
                continue

            if signature in active_signatures:
                errors.append(
                    f"Row {row_number}: Employee already exists ({employee_name} / {resolved_department_name} / {position or 'N/A'})."
                )
                continue

            if has_name_match_conflict(
                employee_name,
                employee_name_lookup,
                exclude_sources={signature} if signature in inactive_signatures else None,
            ):
                errors.append(
                    f"Row {row_number}: {same_role_name_conflict_error('employee')}"
                )
                continue

            if has_name_match_conflict(employee_name, student_name_lookup):
                errors.append(
                    f"Row {row_number}: {cross_role_name_conflict_error('employee', 'student')}"
                )
                continue

            seen_signatures[signature] = row_number
            register_name_match_source(seen_name_rows, employee_name, row_number)

            valid_rows.append(
                {
                    "row_number": row_number,
                    "employee_name": employee_name,
                    "department_name": resolved_department_name,
                    "department_id": department_id,
                    "position": position,
                    "action": "reactivate" if signature in inactive_signatures else "create",
                    "source_department_name": department_name,
                }
            )

        return {"success": True, "valid_rows": valid_rows, "errors": errors}
    finally:
        cursor.close()


class InternalBackendResponse:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.ok = 200 <= response.status_code < 300
        self.text = response.get_data(as_text=True)

    def json(self):
        data = self._response.get_json(silent=True)
        if data is not None:
            return data
        if not self.text:
            return {}
        return json.loads(self.text)


def backend_url(path):
    base_url = app.config["BACKEND_API_URL"].rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def should_use_internal_backend_fallback():
    parsed = urlsplit(app.config["BACKEND_API_URL"])
    return parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == 5001


def internal_backend_request(method, path, **kwargs):
    from app_extension import app as backend_app

    request_path = path
    params = kwargs.get("params")
    if params:
        query_string = urlencode(params, doseq=True)
        separator = "&" if "?" in request_path else "?"
        request_path = f"{request_path}{separator}{query_string}"

    request_kwargs = {}
    if "json" in kwargs:
        request_kwargs["json"] = kwargs["json"]
    elif "data" in kwargs:
        request_kwargs["data"] = kwargs["data"]

    with backend_app.test_client() as client:
        response = client.open(request_path, method=method.upper(), **request_kwargs)
    return InternalBackendResponse(response)


def backend_request(method, path, **kwargs):
    kwargs.setdefault("timeout", app.config["BACKEND_TIMEOUT"])
    try:
        return requests.request(method, backend_url(path), **kwargs)
    except requests.RequestException:
        if should_use_internal_backend_fallback():
            app.logger.warning("Backend service unavailable on port 5001. Falling back to in-process backend for %s %s.", method.upper(), path)
            return internal_backend_request(method, path, **kwargs)
        raise


@app.context_processor
def inject_template_config():
    return {
        "backend_api_url": app.config["BACKEND_API_URL"],
        "is_logged_in": bool(session.get("logged_in")),
    }


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@app.errorhandler(Exception)
def handle_app_exception(err):
    if request.path.startswith("/upload_employees"):
        if isinstance(err, HTTPException):
            return jsonify({"success": False, "error": err.description}), err.code

        app.logger.exception("Unhandled upload route exception on %s", request.path)
        return jsonify({"success": False, "error": f"Unhandled upload error: {err}"}), 500

    if isinstance(err, HTTPException):
        return err

    app.logger.exception("Unhandled application exception.")
    return "Internal Server Error", 500


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


def split_employee_departments(departments):
    office_keywords = (
        "office",
        "library",
        "human resources",
        "hr",
        "registrar",
        "accounting",
        "mis",
    )

    teaching_departments = []
    office_departments = []

    for dept in departments:
        dept_name = str(dept.get("department_name") or "").strip()
        if not dept_name:
            continue

        target_list = (
            office_departments
            if any(keyword in dept_name.lower() for keyword in office_keywords)
            else teaching_departments
        )
        target_list.append(dept)

    return teaching_departments, office_departments


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


def proxy_backend_json(method, path, **kwargs):
    try:
        response = backend_request(method, path, **kwargs)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as err:
        app.logger.error("Backend proxy failed for %s %s: %s", method.upper(), path, err)
        return jsonify({"success": False, "message": "Backend service unavailable."}), 503


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
    visitor_welcome = session.pop("visitor_welcome", None)
    session.pop("logged_in", None)
    session.pop("admin_username", None)
    return render_template(
        "kiosk_entrance.html",
        active_visitors=fetch_visitor_logs(status="Checked In"),
        kiosk_data=get_kiosk_data_with_live_feed(),
        visitor_welcome=visitor_welcome,
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
    visitor_welcome = session.pop("visitor_welcome", None)
    session.pop("logged_in", None)
    session.pop("admin_username", None)
    return render_template(
        "kiosk_visitor.html",
        active_visitors=fetch_visitor_logs(status="Checked In"),
        visitor_welcome=visitor_welcome,
    )


@app.route("/api/visitor/checkin", methods=["POST"])
def visitor_checkin():
    name = (request.form.get("name") or "").strip()
    purpose = normalize_visitor_purpose(request.form.get("purpose"))
    details = (request.form.get("details") or "").strip()
    source = resolve_visitor_source(request.form.get("source"), fallback="kiosk_visitor")
    wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not name:
        if wants_json:
            return jsonify({"success": False, "message": "Check-in failed. Visitor name is required."}), 400
        flash("Check-in failed. Visitor name is required.", "danger")
        return redirect(url_for(source))
    if not purpose:
        if wants_json:
            return jsonify({"success": False, "message": "Check-in failed. Select a valid visitor purpose."}), 400
        flash("Check-in failed. Select a valid visitor purpose.", "danger")
        return redirect(url_for(source))
    if purpose == "Other" and not details:
        if wants_json:
            return jsonify({"success": False, "message": "Check-in failed. Visit description is required when purpose is Other."}), 400
        flash("Check-in failed. Visit description is required when purpose is Other.", "danger")
        return redirect(url_for(source))

    conn = connect_db()
    if not conn:
        if wants_json:
            return jsonify({"success": False, "message": "Check-in failed. Visitor database is unavailable."}), 503
        flash("Check-in failed. Visitor database is unavailable.", "danger")
        return redirect(url_for(source))

    result = Database(conn, (name, purpose, details, "Gate 1")).add_visitor_log()
    if result.get("success"):
        session["visitor_welcome"] = {
            "name": name,
            "visitor_id": result.get("visitor_id") or "Pending ID",
        }
        if wants_json:
            return jsonify(
                {
                    "success": True,
                    "message": f"Welcome, {name}. Check-in successful.",
                    "visitor": {
                        "name": name,
                        "visitor_id": result.get("visitor_id") or "Pending ID",
                        "purpose": details if purpose.lower() == "other" and details else purpose,
                    },
                }
            ), 200

    if wants_json:
        return jsonify({"success": False, "message": result.get("message", "Check-in failed.")}), 400

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
    departments = fetch_departments()
    teaching_departments, office_departments = split_employee_departments(departments)

    if not departments:
        departments = [
            {"department_id": "", "department_name": department}
            for department in department_options
        ]
        teaching_departments, office_departments = departments, []

    return render_template(
        "employee_logs.html",
        logs=logs,
        records=records,
        employees=records,
        department_options=department_options,
        departments=departments,
        teaching_departments=teaching_departments,
        office_departments=office_departments,
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
    purpose = normalize_visitor_purpose(data.get("purpose"))
    details = (data.get("details") or "").strip()

    if not name:
        return jsonify({"success": False, "message": "Visitor name is required."}), 400
    if not purpose:
        return jsonify({"success": False, "message": "Select a valid visitor purpose."}), 400
    if purpose == "Other" and not details:
        return jsonify({"success": False, "message": "Visit description is required when purpose is Other."}), 400

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
    relocate_legacy_report_files()
    return render_template("reports.html", events=fetch_report_events(), reports=get_archived_reports())


@app.route("/reports/sample")
@login_required
def sample_report():
    return render_template(
        "sample_report.html",
        current_date=datetime.now().strftime("%B %d, %Y - %I:%M %p"),
        report=build_sample_report_payload(),
        metrics={},
        logs=[],
        archive_report_url=resolve_archive_report_url(),
    )


@app.route("/admin/events/add", methods=["POST"])
@login_required
def add_event():
    name = (request.form.get("name") or "").strip()
    event_type = (request.form.get("type") or "").strip()
    event_date = (request.form.get("event_date") or "").strip()
    day_of_week = (request.form.get("day_of_week") or "").strip()
    time_start = (request.form.get("time_start") or "").strip()
    time_end = (request.form.get("time_end") or "").strip()
    location = (request.form.get("location") or "").strip()
    department_ids = [
        dept_id.strip()
        for dept_id in request.form.getlist("dept")
        if dept_id and dept_id.strip().isdigit()
    ]
    manual_participant_ids = split_manual_participant_ids(request.form.getlist("custom_dept"))
    roster_file = request.files.get("roster_file")

    frequency = normalize_event_frequency(request.form.get("frequency"))

    validation_errors = []
    if not name:
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
    if frequency != "DAILY" and not event_date:
        validation_errors.append("Event date is required.")
    if frequency == "WEEKLY" and day_of_week not in EVENT_DAYS:
        validation_errors.append("Event day is required for weekly events.")

    if event_date:
        try:
            parsed_event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
            if parsed_event_date < date.today():
                validation_errors.append("Event date cannot be in the past.")
        except ValueError:
            validation_errors.append("Event date must use YYYY-MM-DD format.")

    if time_start and time_end:
        try:
            parsed_start = datetime.strptime(time_start, "%H:%M").time()
            parsed_end = datetime.strptime(time_end, "%H:%M").time()
            if parsed_end <= parsed_start:
                validation_errors.append("End time must be later than start time.")
        except ValueError:
            validation_errors.append("Start time and end time must use HH:MM format.")

    has_file = bool(roster_file and roster_file.filename)
    if not department_ids and not has_file and not manual_participant_ids:
        validation_errors.append("Select at least one department, upload a CSV roster, or enter participant IDs.")

    if validation_errors:
        flash(" ".join(validation_errors), "danger")
        return redirect(url_for("manage_events"))

    custom_participants = list(manual_participant_ids)

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

    custom_participants = unique_values(custom_participants)
    if not department_ids and not custom_participants:
        flash("Failed to add event. Provide at least one valid participant ID or select a department.", "danger")
        return redirect(url_for("manage_events"))

    participants_type = "hybrid" if department_ids and custom_participants else "grouped" if department_ids else "custom"

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
            api_error = api_data.get("message") or api_data.get("error") or "Unknown API error"
            flash(f"Failed to add event: {api_error}", "danger")
    except requests.RequestException as err:
        app.logger.error("Could not add event: %s", err)
        flash(f'Event "{name}" failed to add. Could not connect to the backend.', "danger")
    except ValueError:
        flash(f'Event "{name}" failed to add. Backend returned an invalid response.', "danger")

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


@app.route("/api/backend/admin/user/authentication", methods=["POST"])
def backend_user_authentication_proxy():
    return proxy_backend_json("POST", "/admin/user/authentication", json=request.get_json(silent=True) or {})


@app.route("/api/backend/events/manual-entry", methods=["POST"])
def backend_manual_event_entry_proxy():
    return proxy_backend_json("POST", "/api/events/manual_entry", json=request.get_json(silent=True) or {})


@app.route("/api/backend/admin/event/<int:event_id>/instances")
def backend_event_instances_proxy(event_id):
    return proxy_backend_json("GET", f"/admin/event/{event_id}/instances")


@app.route("/api/backend/admin/instances/<int:instance_id>/attendance")
def backend_instance_attendance_proxy(instance_id):
    return proxy_backend_json("GET", f"/admin/instances/{instance_id}/get-attendance")


@app.route("/api/backend/admin/instances/<int:instance_id>/logs")
def backend_instance_logs_proxy(instance_id):
    return proxy_backend_json("GET", f"/admin/instances/{instance_id}/get-logs")


@app.route("/api/retrieve/events")
def retrieve_all_events_for_reports():
    return jsonify(fetch_report_events())


@app.route("/api/retrieve/departments")
def retrieve_departments():
    return jsonify(fetch_departments())


@app.route("/api/retrieve/courses")
def retrieve_courses():
    conn = connect_db()
    if not conn:
        return jsonify([])

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT course_id, course_name
            FROM courses
            ORDER BY course_name ASC
            """
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()


@app.route("/api/retrieve/visitor-purposes")
def retrieve_visitor_purposes():
    return jsonify(list(VISITOR_PURPOSES))


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

    report_data = dict(report_results["report_data"])
    report_data["archive_filename"] = build_report_archive_filename(category, report_data)

    return render_template(
        "sample_report.html",
        current_date=datetime.now().strftime("%B %d, %Y - %I:%M %p"),
        report=report_data,
        metrics=report_results["metrics_data"],
        logs=report_results["logs"],
        archive_report_url=resolve_archive_report_url(),
    )


@app.route("/reports/archive", methods=["POST"])
@login_required
def archive_report():
    report_file = request.files.get("report_file")
    requested_filename = (request.form.get("filename") or "").strip()

    if not report_file or not report_file.filename:
        return jsonify({"success": False, "message": "Missing report file."}), 400

    incoming_name = requested_filename or report_file.filename
    if not str(incoming_name).lower().endswith(".pdf"):
        return jsonify({"success": False, "message": "Only PDF report files can be archived."}), 400

    archive_path, archive_name = get_unique_report_archive_path(incoming_name)
    report_file.save(archive_path)

    return (
        jsonify(
            {
                "success": True,
                "filename": archive_name,
                "url": url_for("static", filename=f"reports/{archive_name}"),
            }
        ),
        201,
    )


@app.route("/send_report_email", methods=["POST"])
@login_required
def send_report_email():
    recipient = (request.form.get("email") or "").strip()
    category = (request.form.get("category") or "").strip()
    report_type = (request.form.get("type") or "").strip()
    filter_value = (request.form.get("filter") or "All").strip()
    start_date = (request.form.get("start") or "").strip()
    end_date = (request.form.get("end") or "").strip()
    report_title = (request.form.get("report_title") or "PLP Report").strip()
    report_scope = (request.form.get("report_scope") or "ALL").strip()
    report_date_range = (request.form.get("report_date_range") or f"{start_date} to {end_date}").strip()
    requested_filename = (request.form.get("filename") or "").strip()
    uploaded_report = request.files.get("report_file")

    if not recipient:
        return jsonify({"success": False, "message": "Recipient email is required."}), 400

    attachment_data = None
    attachment_filename = sanitize_report_archive_filename(requested_filename or "report.pdf")

    if uploaded_report and uploaded_report.filename:
        attachment_data = uploaded_report.read()
        attachment_filename = sanitize_report_archive_filename(requested_filename or uploaded_report.filename)
    else:
        attachment_data, resolved_report_data, error = load_archived_report_attachment(
            category,
            report_type,
            filter_value,
            start_date,
            end_date,
        )
        if error:
            return jsonify({"success": False, "message": error}), 400

        attachment_filename = resolved_report_data["archive_filename"]
        report_title = (resolved_report_data.get("event_name") or resolved_report_data.get("title") or report_title).strip()
        report_scope = (resolved_report_data.get("department") or report_scope).strip()
        report_date_range = (resolved_report_data.get("date_range") or report_date_range).strip()

    if not attachment_data:
        return jsonify({"success": False, "message": "No report PDF is available to attach."}), 400

    email_subject = f"PLP Report - {report_title}"
    email_body = (
        "Attached is the requested PLP report.\n\n"
        f"Report: {report_title}\n"
        f"Scope: {report_scope}\n"
        f"Date Range: {report_date_range}\n"
        f"Generated By: {session.get('admin_username', 'PLP Admin')}\n"
    )

    try:
        send_email(
            subject=email_subject,
            body=email_body,
            recipient=recipient,
            attachment_data=attachment_data,
            filename=attachment_filename,
        )
    except ValueError as err:
        return jsonify({"success": False, "message": str(err)}), 400
    except Exception as err:
        app.logger.exception("Failed to send report email to %s", recipient)
        return jsonify({"success": False, "message": f"Failed to send the report email: {err}"}), 500

    return jsonify({"success": True, "message": f"Report emailed successfully to {recipient}."}), 200


@app.route("/get_courses")
@login_required
def get_courses():
    conn = connect_db()
    if not conn:
        return jsonify([])

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT course_id, course_name
            FROM courses
            ORDER BY course_name ASC
            """
        )
        rows = cursor.fetchall()
        return jsonify(
            [
                {
                    "course_id": row["course_id"],
                    "course_name": row["course_name"],
                    "name": (row["course_name"] or "").upper(),
                }
                for row in rows
            ]
        )
    finally:
        cursor.close()


def parse_student_upload_file(file):
    if not file or not file.filename:
        return {"success": False, "error": "No file uploaded"}

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in {".xls", ".xlsx", ".csv"}:
        return {"success": False, "error": "Please upload a valid Excel or CSV file."}

    extracted = _extract_upload_rows(file, file_ext)
    if not extracted.get("success"):
        return extracted

    source_rows = extracted.get("rows", [])
    header_index = None
    header_source_row_number = None
    normalized_headers = []

    for index, row in enumerate(source_rows):
        row_headers = [clean_upload_text(value).upper() for value in row.get("values", [])]
        header_values = {header for header in row_headers if header}
        has_required = set(STUDENT_UPLOAD_REQUIRED_COLUMNS).issubset(header_values)
        has_course = "COURSE" in header_values or "COURSE ID" in header_values
        if has_required and has_course:
            header_index = index
            header_source_row_number = row.get("source_row_number") or (index + 1)
            normalized_headers = row_headers
            break

    if header_index is None:
        return {
            "success": False,
            "error": "Could not find the required headers: Student ID, Student Name, and Course or Course ID.",
        }

    missing_columns = [
        column.title() for column in STUDENT_UPLOAD_REQUIRED_COLUMNS if column not in normalized_headers
    ]
    if "COURSE" not in normalized_headers and "COURSE ID" not in normalized_headers:
        missing_columns.append("Course or Course ID")
    if missing_columns:
        return {
            "success": False,
            "error": f"Missing required column(s): {', '.join(missing_columns)}",
        }

    parsed_rows = []
    for row in source_rows[header_index + 1:]:
        row_values = list(row.get("values", []))
        row_map = {}
        for column_index, header in enumerate(normalized_headers):
            if not header:
                continue
            row_map[header] = clean_upload_text(row_values[column_index]) if column_index < len(row_values) else ""

        relevant_values = [
            row_map.get(column, "")
            for column in STUDENT_UPLOAD_REQUIRED_COLUMNS + STUDENT_UPLOAD_OPTIONAL_COLUMNS
        ]
        if not any(value.strip() for value in relevant_values):
            continue

        course_id = str(row_map.get("COURSE ID", "") or "").strip()
        if course_id.endswith(".0"):
            course_id = course_id[:-2]

        parsed_rows.append(
            {
                "row_number": row.get("source_row_number") or (header_source_row_number + 1),
                "student_id": row_map.get("STUDENT ID", ""),
                "student_name": row_map.get("STUDENT NAME", ""),
                "course_name": row_map.get("COURSE", ""),
                "course_id": course_id,
                "status": row_map.get("STATUS", ""),
            }
        )

    return {
        "success": True,
        "required_columns": STUDENT_UPLOAD_REQUIRED_COLUMNS,
        "optional_columns": STUDENT_UPLOAD_OPTIONAL_COLUMNS,
        "parsed_rows": parsed_rows,
    }


def validate_student_upload_rows(conn, parsed_rows):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT course_id, course_name
            FROM courses
            """
        )
        course_lookup_by_id = {}
        course_lookup_by_name = {}
        for course_id, course_name in cursor.fetchall():
            normalized_course = normalize_course_name(course_name)
            course_data = {
                "course_id": course_id,
                "course_name": normalized_course,
            }
            course_lookup_by_id[str(course_id)] = course_data
            if normalized_course:
                course_lookup_by_name.setdefault(normalized_course.upper(), []).append(course_data)

        cursor.execute(
            """
            SELECT s.student_id, s.student_name, COALESCE(u.active, 1) AS is_active
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            """
        )
        active_ids = set()
        inactive_ids = set()
        student_name_lookup = {}
        for student_id, student_name, is_active in cursor.fetchall():
            normalized_id = normalize_student_id(student_id)
            register_name_match_source(student_name_lookup, student_name, normalized_id)
            if bool(is_active):
                active_ids.add(normalized_id)
            else:
                inactive_ids.add(normalized_id)

        cursor.execute(
            """
            SELECT employee_name
            FROM employees
            """
        )
        employee_name_lookup = build_name_match_lookup(row[0] for row in cursor.fetchall())

        valid_rows = []
        errors = []
        seen_ids = {}
        seen_name_rows = {}

        for row in parsed_rows:
            student_id = normalize_student_id(row.get("student_id"))
            student_name = normalize_student_name(row.get("student_name"))
            course_name = normalize_course_name(row.get("course_name"))
            course_id = str(row.get("course_id") or "").strip()
            if course_id.endswith(".0"):
                course_id = course_id[:-2]
            status = clean_upload_text(row.get("status"))
            row_number = row.get("row_number")

            missing_fields = []
            if not student_id:
                missing_fields.append("Student ID")
            if not student_name:
                missing_fields.append("Student Name")
            if not course_id and not course_name:
                missing_fields.append("Course or Course ID")
            if missing_fields:
                errors.append(f"Row {row_number}: Missing {', '.join(missing_fields)}")
                continue

            field_errors = validate_student_fields(student_id=student_id, student_name=student_name)
            course_errors = validate_course_name(course_name) if course_name else []
            if field_errors or course_errors:
                errors.append(f"Row {row_number}: {(field_errors + course_errors)[0]}")
                continue

            if course_id:
                course_match = course_lookup_by_id.get(course_id)
                if not course_match:
                    errors.append(f"Row {row_number}: Course ID not found: {course_id}")
                    continue
                resolved_course = course_match
            else:
                course_matches = course_lookup_by_name.get(course_name.upper(), [])
                if not course_matches:
                    errors.append(f"Row {row_number}: Course not found: {course_name}")
                    continue
                if len(course_matches) > 1:
                    errors.append(f"Row {row_number}: Course is ambiguous: {course_name}")
                    continue
                resolved_course = course_matches[0]

            if student_id in seen_ids:
                errors.append(
                    f"Row {row_number}: Duplicate of row {seen_ids[student_id]} in the uploaded file."
                )
                continue

            duplicate_name_rows = find_name_match_sources(student_name, seen_name_rows)
            if duplicate_name_rows:
                errors.append(
                    f"Row {row_number}: Similar name already appears in row {min(duplicate_name_rows)} of the uploaded file."
                )
                continue

            if student_id in active_ids:
                errors.append(f"Row {row_number}: Student already exists with ID {student_id}.")
                continue

            if has_name_match_conflict(
                student_name,
                student_name_lookup,
                exclude_sources={student_id} if student_id in inactive_ids else None,
            ):
                errors.append(
                    f"Row {row_number}: {same_role_name_conflict_error('student')}"
                )
                continue

            if has_name_match_conflict(student_name, employee_name_lookup):
                errors.append(
                    f"Row {row_number}: {cross_role_name_conflict_error('student', 'employee')}"
                )
                continue

            seen_ids[student_id] = row_number
            register_name_match_source(seen_name_rows, student_name, row_number)

            valid_rows.append(
                {
                    "row_number": row_number,
                    "student_id": student_id,
                    "student_name": student_name,
                    "course_id": resolved_course["course_id"],
                    "course_name": resolved_course["course_name"],
                    "status": status or "Outside",
                    "action": "reactivate" if student_id in inactive_ids else "create",
                }
            )

        return {"success": True, "valid_rows": valid_rows, "errors": errors}
    finally:
        cursor.close()


@app.route("/add_student_manual", methods=["POST"])
@login_required
def add_student_manual():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()
    student_name = (data.get("student_name") or "").strip()
    course_id = (data.get("course_id") or "").strip()
    status = (data.get("status") or "Outside").strip()

    validation_errors = validate_student_fields(student_id=student_id, student_name=student_name)
    if not course_id:
        return jsonify({"success": False, "error": "Course is required."}), 400
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400

    result = student_model.add_student(
        student_id=student_id,
        student_name=student_name,
        course_id=course_id,
        status=status,
    )
    return jsonify(result), (200 if result.get("success") else 400)


@app.route("/upload_students", methods=["POST"])
@login_required
def upload_students():
    preview_response, preview_status = preview_students_upload()
    if preview_status != 200:
        return preview_response, preview_status

    preview_data = preview_response.get_json(silent=True) or {}
    valid_rows = preview_data.get("preview_rows", [])
    if not valid_rows:
        return jsonify({"success": False, "error": "No valid student rows to upload."}), 400

    return commit_students_upload_payload(valid_rows)


@app.route("/upload_students/template.csv", methods=["GET"])
@login_required
def download_student_upload_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["STUDENT ID", "STUDENT NAME", "COURSE"])
    writer.writerow(["23-00312", "Juan Dela Cruz", "BS Information Technology"])
    writer.writerow(["24-00101", "Maria Santos", "BS Nursing"])
    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_upload_template.csv"},
    )


@app.route("/upload_students/preview", methods=["POST"])
@login_required
def preview_students_upload():
    try:
        file = request.files.get("file")
        app.logger.info(
            "Student upload preview requested. filename=%s",
            getattr(file, "filename", None),
        )
        parsed = parse_student_upload_file(file)
        if not parsed.get("success"):
            app.logger.warning(
                "Student upload parsing rejected. filename=%s error=%s",
                getattr(file, "filename", None),
                parsed.get("error"),
            )
            return jsonify(parsed), 400
    except Exception as err:
        app.logger.exception("Unexpected student upload parsing failure.")
        return jsonify({"success": False, "error": f"Upload parsing failed: {err}"}), 500

    conn = connect_db()
    if conn is None:
        app.logger.error("Student upload preview failed: database connection unavailable.")
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        validation = validate_student_upload_rows(conn, parsed.get("parsed_rows", []))
        app.logger.info(
            "Student upload preview validated. valid_rows=%s errors=%s",
            len(validation.get("valid_rows", [])),
            len(validation.get("errors", [])),
        )
        return jsonify(
            {
                "success": True,
                "required_columns": parsed.get("required_columns", []),
                "optional_columns": parsed.get("optional_columns", []),
                "preview_rows": validation.get("valid_rows", []),
                "errors": validation.get("errors", []),
            }
        )
    except Exception as err:
        app.logger.exception("Student upload validation failed unexpectedly.")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        release_db_connection(conn)


def commit_students_upload_payload(rows):
    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    inserted = 0
    reactivated = 0
    errors = []
    try:
        for row in rows:
            student_id = normalize_student_id(row.get("student_id"))
            student_name = normalize_student_name(row.get("student_name"))
            course_id = str(row.get("course_id") or "").strip()
            course_name = normalize_course_name(row.get("course_name"))
            status = clean_upload_text(row.get("status")) or "Outside"
            row_number = row.get("row_number") or "Unknown"

            if not student_id or not student_name or not course_id:
                errors.append(f"Row {row_number}: Missing Student ID, Student Name, or Course.")
                continue

            result = student_model.add_student_excel(
                conn=conn,
                student_id=student_id,
                student_name=student_name,
                course_id=course_id,
                course_name=course_name,
                status=status,
            )
            if result.get("success"):
                if result.get("reactivated"):
                    reactivated += 1
                else:
                    inserted += 1
            else:
                errors.append(f"Row {row_number}: {result.get('error')}")

        return jsonify(
            {
                "success": True,
                "inserted": inserted,
                "reactivated": reactivated,
                "errors": errors,
            }
        ), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        release_db_connection(conn)


@app.route("/upload_students/commit", methods=["POST"])
@login_required
def commit_students_upload():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return jsonify({"success": False, "error": "No student rows provided for upload."}), 400

    return commit_students_upload_payload(rows)


@app.route("/update_student", methods=["POST"])
@login_required
def update_student():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()
    student_name = (data.get("student_name") or "").strip()
    course_id = (data.get("course_id") or "").strip()

    validation_errors = validate_student_fields(student_id=student_id, student_name=student_name)
    if not course_id:
        return jsonify({"success": False, "error": "Course is required."}), 400
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = None
    try:
        if not conn.in_transaction:
            conn.start_transaction()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id
            FROM students
            WHERE student_id = %s
            LIMIT 1
            """,
            (normalize_student_id(student_id),),
        )
        student = cursor.fetchone()
        if not student:
            conn.rollback()
            return jsonify({"success": False, "error": "Student not found."}), 404

        cursor.execute(
            """
            SELECT course_id, course_name
            FROM courses
            WHERE course_id = %s
            LIMIT 1
            """,
            (course_id,),
        )
        course = cursor.fetchone()
        if not course:
            conn.rollback()
            return jsonify({"success": False, "error": "Selected course does not exist."}), 400

        cursor.execute(
            """
            UPDATE students
            SET student_name = %s,
                course_id = %s
            WHERE student_id = %s
            """,
            (
                normalize_student_name(student_name),
                course[0],
                normalize_student_id(student_id),
            ),
        )
        conn.commit()
        return jsonify(
            {
                "success": True,
                "course_id": course[0],
                "course_name": normalize_course_name(course[1]),
            }
        )
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


@app.route("/delete_student", methods=["POST"])
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
        if not conn.in_transaction:
            conn.start_transaction()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.user_id, COALESCE(u.active, 1) AS is_active
            FROM students s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.student_id = %s
            LIMIT 1
            """,
            (normalize_student_id(student_id),),
        )
        student = cursor.fetchone()
        if not student:
            conn.rollback()
            return jsonify({"success": False, "error": "Student not found."}), 404

        if not bool(student[1]):
            conn.rollback()
            return jsonify({"success": True, "already_inactive": True})

        cursor.execute("UPDATE users SET active = 0 WHERE user_id = %s", (student[0],))
        cursor.execute("UPDATE students SET status = %s WHERE user_id = %s", ("Outside", student[0]))
        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


@app.route("/add_employee", methods=["POST"])
@login_required
def add_employee():
    data = request.get_json(silent=True) or {}

    result = employee_model.add_employee(
        employee_name=(data.get("employee_name") or "").strip(),
        department_id=(data.get("department_id") or "").strip(),
        position=(data.get("position") or "").strip(),
    )

    return jsonify(result), (200 if result.get("success") else 400)


@app.route("/upload_employees", methods=["POST"])
@login_required
def upload_employees():
    preview_response, preview_status = preview_employees_upload()
    if preview_status != 200:
        return preview_response, preview_status

    preview_data = preview_response.get_json(silent=True) or {}
    valid_rows = preview_data.get("preview_rows", [])
    if not valid_rows:
        return jsonify({"success": False, "error": "No valid employee rows to upload."}), 400

    return commit_employees_upload_payload(valid_rows)


@app.route("/upload_employees/template.csv", methods=["GET"])
@login_required
def download_employee_upload_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(EMPLOYEE_UPLOAD_REQUIRED_COLUMNS + EMPLOYEE_UPLOAD_OPTIONAL_COLUMNS)
    writer.writerow(["Juan Dela Cruz", "College of Information Technology", "Instructor I"])
    writer.writerow(["Maria Santos", "Registrar's Office", "Admin Officer"])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee_upload_template.csv"},
    )


@app.route("/upload_employees/preview", methods=["POST"])
@login_required
def preview_employees_upload():
    try:
        file = request.files.get("file")
        app.logger.info(
            "Employee upload preview requested. filename=%s",
            getattr(file, "filename", None),
        )
        parsed = parse_employee_upload_file(file)
        if not parsed.get("success"):
            app.logger.warning(
                "Employee upload parsing rejected. filename=%s error=%s",
                getattr(file, "filename", None),
                parsed.get("error"),
            )
            return jsonify(parsed), 400
    except Exception as err:
        app.logger.exception("Unexpected employee upload parsing failure.")
        return jsonify({"success": False, "error": f"Upload parsing failed: {err}"}), 500

    conn = connect_db()
    if conn is None:
        app.logger.error("Employee upload preview failed: database connection unavailable.")
        return jsonify({"success": False, "error": "Database connection failed"}), 500
    try:
        validation = validate_employee_upload_rows(conn, parsed.get("parsed_rows", []))
        app.logger.info(
            "Employee upload preview validated. valid_rows=%s errors=%s",
            len(validation.get("valid_rows", [])),
            len(validation.get("errors", [])),
        )
        return jsonify(
            {
                "success": True,
                "required_columns": parsed.get("required_columns", []),
                "optional_columns": parsed.get("optional_columns", []),
                "preview_rows": validation.get("valid_rows", []),
                "errors": validation.get("errors", []),
            }
        )
    except Exception as err:
        app.logger.exception("Employee upload validation failed unexpectedly.")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        release_db_connection(conn)


def commit_employees_upload_payload(rows):
    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    inserted = 0
    reactivated = 0
    errors = []
    try:
        for row in rows:
            employee_name = clean_upload_text(row.get("employee_name"))
            department_name = clean_upload_text(row.get("department_name"))
            department_id = str(row.get("department_id") or "").strip()
            position = clean_upload_text(row.get("position"))
            row_number = row.get("row_number") or "Unknown"

            if not employee_name or not department_name:
                errors.append(f"Row {row_number}: Missing Employee Name or Department.")
                continue

            result = employee_model.add_employee_excel(
                conn=conn,
                employee_name=employee_name,
                department_id=department_id,
                department_name=department_name,
                position=position,
            )
            if result.get("success"):
                if result.get("reactivated"):
                    reactivated += 1
                else:
                    inserted += 1
            else:
                errors.append(f"Row {row_number}: {result.get('error')}")

        return jsonify(
            {
                "success": True,
                "inserted": inserted,
                "reactivated": reactivated,
                "errors": errors,
            }
        ), 200
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        release_db_connection(conn)


@app.route("/upload_employees/commit", methods=["POST"])
@login_required
def commit_employees_upload():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return jsonify({"success": False, "error": "No employee rows provided for upload."}), 400

    return commit_employees_upload_payload(rows)


@app.route("/update_employee", methods=["POST"])
@login_required
def update_employee():
    data = request.get_json(silent=True) or {}
    employee_id = (data.get("employee_id") or "").strip()
    employee_name = (data.get("employee_name") or "").strip()
    department_id = (data.get("department_id") or "").strip()
    position = (data.get("position") or "").strip()

    validation_errors = validate_employee_fields(
        employee_name=employee_name,
        position=position,
        require_position=False,
    )
    if not employee_id or not department_id:
        return jsonify({"success": False, "error": "Employee ID and Department are required."}), 400
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = None
    try:
        if not conn.in_transaction:
            conn.start_transaction()

        cursor = conn.cursor()
        normalized_employee_name = clean_upload_text(employee_name)
        normalized_position = clean_upload_text(position)

        cursor.execute(
            """
            SELECT user_id
            FROM employees
            WHERE employee_id = %s
            LIMIT 1
            """,
            (employee_id,),
        )
        employee = cursor.fetchone()
        if not employee:
            conn.rollback()
            return jsonify({"success": False, "error": "Employee not found."}), 404

        cursor.execute(
            """
            SELECT department_id
            FROM departments
            WHERE department_id = %s
            LIMIT 1
            """,
            (department_id,),
        )
        department = cursor.fetchone()

        if not department:
            conn.rollback()
            return jsonify({"success": False, "error": "Selected department does not exist."}), 400

        cursor.execute(
            """
            SELECT employee_id
            FROM employees
            WHERE UPPER(TRIM(employee_name)) = UPPER(TRIM(%s))
              AND department_id = %s
              AND UPPER(TRIM(COALESCE(position, ''))) = UPPER(TRIM(%s))
              AND employee_id <> %s
            LIMIT 1
            """,
            (normalized_employee_name, department[0], normalized_position, employee_id),
        )
        duplicate = cursor.fetchone()
        if duplicate:
            conn.rollback()
            return jsonify(
                {
                    "success": False,
                    "error": f"Another employee already uses this combination ({duplicate[0]}).",
                }
            ), 400

        cursor.execute(
            """
            UPDATE employees
            SET employee_name = %s,
                department_id = %s,
                position = %s
            WHERE employee_id = %s
            """,
            (normalized_employee_name, department[0], normalized_position or None, employee_id),
        )

        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


@app.route("/delete_employee", methods=["POST"])
@login_required
def delete_employee():
    data = request.get_json(silent=True) or {}
    employee_id = (data.get("employee_id") or "").strip()

    if not employee_id:
        return jsonify({"success": False, "error": "Missing employee_id."}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    cursor = None
    try:
        if not conn.in_transaction:
            conn.start_transaction()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.user_id, COALESCE(u.active, 1) AS is_active
            FROM employees e
            JOIN users u ON e.user_id = u.user_id
            WHERE e.employee_id = %s
            LIMIT 1
            """,
            (employee_id,),
        )
        employee = cursor.fetchone()

        if not employee:
            conn.rollback()
            return jsonify({"success": False, "error": "Employee not found."}), 404

        if not bool(employee[1]):
            conn.rollback()
            return jsonify({"success": True, "already_inactive": True})

        cursor.execute("UPDATE users SET active = 0 WHERE user_id = %s", (employee[0],))
        cursor.execute("UPDATE employees SET status = %s WHERE user_id = %s", ("Outside", employee[0]))
        conn.commit()
        return jsonify({"success": True})
    except Exception as err:
        conn.rollback()
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)

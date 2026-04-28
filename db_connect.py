from database import connect_db
from datetime import date, datetime, timedelta

import mysql.connector as connector
from werkzeug.security import check_password_hash


VISITOR_PURPOSES = (
    "Official Business",
    "Document Submission",
    "Inquiry",
    "Meeting",
    "Delivery",
    "Other",
)


def normalize_visitor_purpose(value):
    raw_value = (value or "").strip()
    for purpose in VISITOR_PURPOSES:
        if raw_value.lower() == purpose.lower():
            return purpose
    return None


def _format_hour_label(hour_value):
    if hour_value is None:
        return "N/A"
    return datetime.strptime(f"{int(hour_value):02d}:00", "%H:%M").strftime("%I:%M %p").lstrip("0")


def _format_department_label(department_name):
    if not department_name:
        return "N/A"

    initials = [
        token[0].upper()
        for token in str(department_name).replace("&", " ").split()
        if token.lower() not in {"college", "of", "and"}
    ]
    return "".join(initials) or str(department_name)[:6]


class Database:
    def __init__(self, conn, parameter=None):
        if not conn:
            raise ValueError("Failed to connect to the database.")

        self.conn = conn
        self.parameter = parameter or ()
        self.cursor = self.conn.cursor(dictionary=True)

    @staticmethod
    def _serialize_row(row):
        serialized = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat(sep=" ")
            elif isinstance(value, date):
                serialized[key] = value.isoformat()
            elif isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                serialized[key] = f"{hours:02d}:{minutes:02d}"
            else:
                serialized[key] = value
        return serialized

    @staticmethod
    def _password_matches(stored_password, provided_password):
        if not stored_password:
            return False
        if stored_password == provided_password:
            return True
        try:
            return check_password_hash(stored_password, provided_password)
        except ValueError:
            return False

    def admin_login(self):
        try:
            username, password = self.parameter
            self.cursor.execute(
                "SELECT * FROM admin WHERE username = %s LIMIT 1",
                (username,),
            )
            result = self.cursor.fetchone()

            if result and self._password_matches(result.get("password"), password):
                return result

            return []
        except connector.Error as err:
            print(f"Error during admin login: {err}")
            return None

    def authenticate_user(self):
        try:
            query = """
                SELECT
                    u.user_id,
                    u.role,
                    u.active,
                    COALESCE(s.student_id, e.employee_id, v.visitor_id) AS scan_id,
                    COALESCE(s.status, e.status, v.status, 'Outside') AS current_status,
                    COALESCE(s.student_name, e.employee_name, v.visitor_name, a.username, 'Unknown User') AS full_name,
                    CASE
                        WHEN u.role = 'student' THEN COALESCE(c.course_name, 'N/A')
                        WHEN u.role = 'employee' THEN COALESCE(d.department_name, 'N/A')
                        WHEN u.role = 'visitor' THEN COALESCE(
                            CASE
                                WHEN LOWER(COALESCE(v.purpose, '')) = 'other'
                                THEN NULLIF(TRIM(v.details), '')
                                ELSE NULLIF(TRIM(v.purpose), '')
                            END,
                            'Visitor'
                        )
                        ELSE 'Admin'
                    END AS affiliation
                FROM users u
                LEFT JOIN students s ON u.user_id = s.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                LEFT JOIN employees e ON u.user_id = e.user_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                LEFT JOIN visitors v ON u.user_id = v.user_id
                LEFT JOIN admin a ON u.user_id = a.user_id
                WHERE u.active = 1
                  AND (
                      s.student_id = %s
                      OR e.employee_id = %s
                      OR v.visitor_id = %s
                  )
                LIMIT 1
            """
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchall()
            return result if result else []
        except connector.Error as err:
            print(f"Error authenticating user: {err}")
            return None

    def change_status(self):
        try:
            user_id, current_status, role = self.parameter[:3]
            requested_log_type = self.parameter[3] if len(self.parameter) > 3 else None
            current_status = (current_status or "Outside").lower()

            self.cursor.execute(
                """
                SELECT timestamp, log_type
                FROM general_log
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (user_id,),
            )
            last_log = self.cursor.fetchone()

            now = datetime.now()
            today_date = now.date()
            forgot_to_timeout = False

            if requested_log_type == "Entry":
                new_status = "Inside"
            elif requested_log_type == "Exit":
                new_status = "Outside"
            elif current_status == "inside":
                if last_log and last_log["timestamp"].date() == today_date:
                    new_status = "Outside"
                else:
                    new_status = "Inside"
                    forgot_to_timeout = bool(last_log)
            else:
                new_status = "Inside"

            if role == "student":
                query = "UPDATE students SET status = %s WHERE user_id = %s"
            elif role == "employee":
                query = "UPDATE employees SET status = %s WHERE user_id = %s"
            elif role == "visitor":
                query = "UPDATE visitors SET status = %s WHERE user_id = %s"
            else:
                return None

            self.cursor.execute(query, (new_status, user_id))
            self.conn.commit()

            return {
                "status": new_status,
                "new_status": new_status,
                "forgot_to_timeout": forgot_to_timeout,
            }
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error changing status: {err}")
            return None

    def insert_general_log(self):
        try:
            self.cursor.execute(
                """
                INSERT INTO general_log (user_id, timestamp, log_type, gate)
                VALUES (%s, %s, %s, %s)
                """,
                self.parameter,
            )
            self.conn.commit()

            if self.cursor.rowcount > 0:
                return {"success": True, "message": "Log inserted successfully."}

            return {"success": False, "message": "No log was inserted."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error inserting log: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def add_visitor_log(self):
        try:
            visitor_name = (self.parameter[0] or "").strip()
            purpose = normalize_visitor_purpose(self.parameter[1])
            details = (self.parameter[2] or "").strip() if len(self.parameter) > 2 else ""
            gate = self.parameter[3] if len(self.parameter) > 3 else "Gate 1"

            if not visitor_name:
                return {"success": False, "message": "Visitor name is required."}
            if not purpose:
                return {"success": False, "message": "Select a valid visitor purpose."}
            if purpose == "Other" and not details:
                return {"success": False, "message": "Visit description is required when purpose is Other."}

            normalized_details = details if purpose == "Other" else None

            self.cursor.execute(
                "INSERT INTO users (role, active) VALUES (%s, %s)",
                ("visitor", 1),
            )
            user_id = int(self.cursor.lastrowid)

            self.cursor.execute(
                """
                INSERT INTO visitors (user_id, visitor_name, purpose, details, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, visitor_name, purpose, normalized_details, "Inside"),
            )

            self.cursor.execute(
                """
                SELECT visitor_id
                FROM visitors
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            visitor = self.cursor.fetchone()

            self.cursor.execute(
                """
                INSERT INTO general_log (user_id, timestamp, log_type, gate)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, datetime.now(), "Entry", gate),
            )

            self.conn.commit()
            return {
                "success": True,
                "visitor_id": visitor["visitor_id"] if visitor else None,
                "user_id": user_id,
                "message": "Visitor logged successfully.",
            }
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error adding visitor log: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def checkout_visitor_log(self):
        try:
            visitor_id = self.parameter[0]
            gate = self.parameter[1] if len(self.parameter) > 1 else "Gate 2"

            self.cursor.execute(
                """
                SELECT visitor_id, user_id, visitor_name, status
                FROM visitors v
                JOIN users u ON v.user_id = u.user_id
                WHERE v.visitor_id = %s AND u.active = 1
                LIMIT 1
                """,
                (visitor_id,),
            )
            visitor = self.cursor.fetchone()

            if not visitor:
                return {"success": False, "message": "Visitor not found."}

            if visitor["status"] == "Outside":
                return {"success": False, "message": "Visitor is already checked out."}

            self.cursor.execute(
                "UPDATE visitors SET status = %s WHERE visitor_id = %s",
                ("Outside", visitor_id),
            )
            self.cursor.execute(
                """
                INSERT INTO general_log (user_id, timestamp, log_type, gate)
                VALUES (%s, %s, %s, %s)
                """,
                (visitor["user_id"], datetime.now(), "Exit", gate),
            )

            self.conn.commit()
            return {
                "success": True,
                "name": visitor["visitor_name"],
                "message": "Visitor checked out successfully.",
            }
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error checking out visitor: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def get_visitor_logs(self, search_term=None, visit_date=None, include_inactive=False):
        try:
            where_clauses = []
            params = []

            if not include_inactive:
                where_clauses.append("COALESCE(u.active, 1) = 1")

            if search_term:
                like_term = f"%{search_term.strip().lower()}%"
                where_clauses.append(
                    """
                    (
                        LOWER(v.visitor_id) LIKE %s
                        OR LOWER(v.visitor_name) LIKE %s
                        OR LOWER(COALESCE(v.purpose, '')) LIKE %s
                        OR LOWER(COALESCE(v.details, '')) LIKE %s
                    )
                    """
                )
                params.extend([like_term, like_term, like_term, like_term])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            having_sql = ""

            if visit_date:
                having_sql = """
                    HAVING DATE(MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END)) = %s
                """
                params.append(visit_date)

            query = f"""
                SELECT
                    v.visitor_id AS id,
                    v.visitor_name AS name,
                    COALESCE(NULLIF(TRIM(v.purpose), ''), 'N/A') AS purpose,
                    CASE
                        WHEN LOWER(COALESCE(v.purpose, '')) = 'other'
                        THEN COALESCE(NULLIF(TRIM(v.details), ''), 'N/A')
                        ELSE NULL
                    END AS details,
                    DATE_FORMAT(MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END), '%Y-%m-%d') AS date,
                    TRIM(DATE_FORMAT(MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END), '%l:%i %p')) AS time_in,
                    TRIM(DATE_FORMAT(MAX(CASE WHEN gl.log_type = 'Exit' THEN gl.timestamp END), '%l:%i %p')) AS time_out,
                    CASE
                        WHEN v.status = 'Inside' THEN 'Checked In'
                        ELSE 'Checked Out'
                    END AS status,
                    COALESCE(u.active, 1) AS active,
                    COALESCE(MAX(gl.timestamp), v.visitor_last_updated) AS last_activity
                FROM visitors v
                JOIN users u ON v.user_id = u.user_id
                LEFT JOIN general_log gl ON gl.user_id = v.user_id
                {where_sql}
                GROUP BY
                    v.seq, v.visitor_id, v.visitor_name, v.purpose, v.details,
                    v.status, u.active, v.visitor_last_updated
                {having_sql}
                ORDER BY last_activity DESC, v.seq DESC
            """
            self.cursor.execute(query, tuple(params))
            result = self.cursor.fetchall()
            return result if result else []
        except connector.Error as err:
            print(f"Error fetching visitor logs: {err}")
            return []

    def update_visitor_record(self):
        try:
            visitor_id = self.parameter[0]
            visitor_name = self.parameter[1]
            purpose = normalize_visitor_purpose(self.parameter[2])
            details = self.parameter[3] if len(self.parameter) > 3 else ""
            visitor_name = (visitor_name or "").strip()
            details = (details or "").strip()

            if not visitor_name:
                return {"success": False, "message": "Visitor name is required."}
            if not purpose:
                return {"success": False, "message": "Select a valid visitor purpose."}
            if purpose == "Other" and not details:
                return {"success": False, "message": "Visit description is required when purpose is Other."}

            normalized_details = details if purpose == "Other" else None

            self.cursor.execute(
                """
                SELECT v.visitor_id
                FROM visitors v
                JOIN users u ON v.user_id = u.user_id
                WHERE v.visitor_id = %s AND u.active = 1
                LIMIT 1
                """,
                (visitor_id,),
            )
            if not self.cursor.fetchone():
                return {"success": False, "message": "Visitor not found."}

            self.cursor.execute(
                """
                UPDATE visitors
                SET visitor_name = %s, purpose = %s, details = %s
                WHERE visitor_id = %s
                """,
                (visitor_name, purpose, normalized_details, visitor_id),
            )
            self.conn.commit()

            return {"success": True, "message": "Visitor updated successfully."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error updating visitor: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def delete_visitor_record(self):
        try:
            visitor_id = self.parameter[0]

            self.cursor.execute(
                """
                SELECT v.user_id
                FROM visitors v
                JOIN users u ON v.user_id = u.user_id
                WHERE v.visitor_id = %s AND u.active = 1
                LIMIT 1
                """,
                (visitor_id,),
            )
            visitor = self.cursor.fetchone()

            if not visitor:
                return {"success": False, "message": "Visitor not found."}

            self.cursor.execute(
                "UPDATE users SET active = 0 WHERE user_id = %s",
                (visitor["user_id"],),
            )
            self.cursor.execute(
                "UPDATE visitors SET status = 'Outside' WHERE visitor_id = %s",
                (visitor_id,),
            )
            self.conn.commit()

            return {"success": True, "message": "Visitor archived successfully."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error deleting visitor: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def _get_user_ids_from_departments(self, department_ids):
        if not department_ids:
            return set()

        placeholders = ", ".join(["%s"] * len(department_ids))
        query = f"""
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN employees e ON u.user_id = e.user_id
            WHERE u.active = 1
              AND e.department_id IN ({placeholders})
        """
        self.cursor.execute(query, tuple(department_ids))
        return {row["user_id"] for row in self.cursor.fetchall()}

    def _get_user_ids_from_scan_ids(self, raw_ids):
        if not raw_ids:
            return set()

        placeholders = ", ".join(["%s"] * len(raw_ids))
        query = f"""
            SELECT DISTINCT u.user_id
            FROM users u
            LEFT JOIN students s ON u.user_id = s.user_id
            LEFT JOIN employees e ON u.user_id = e.user_id
            LEFT JOIN visitors v ON u.user_id = v.user_id
            WHERE u.active = 1
              AND (
                    s.student_id IN ({placeholders})
                    OR e.employee_id IN ({placeholders})
                    OR v.visitor_id IN ({placeholders})
              )
        """
        params = tuple(raw_ids + raw_ids + raw_ids)
        self.cursor.execute(query, params)
        return {row["user_id"] for row in self.cursor.fetchall()}

    def _attach_event_participants(self, event_id, participants, participants_type):
        participant_user_ids = set()

        if participants_type == "grouped":
            participant_user_ids.update(self._get_user_ids_from_departments(participants or []))
        elif participants_type == "custom":
            participant_user_ids.update(self._get_user_ids_from_scan_ids(participants or []))
        elif participants_type == "hybrid":
            participant_user_ids.update(
                self._get_user_ids_from_departments((participants or {}).get("grouped_participants", []))
            )
            participant_user_ids.update(
                self._get_user_ids_from_scan_ids((participants or {}).get("custom_participants", []))
            )

        if not participant_user_ids:
            return 0

        participant_data = [(event_id, user_id) for user_id in participant_user_ids]
        self.cursor.executemany(
            "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)",
            participant_data,
        )
        return len(participant_user_ids)

    def _ensure_event_instance(self, event_id, event_date):
        self.cursor.execute(
            """
            INSERT IGNORE INTO event_instances (event_id, event_date, status)
            VALUES (%s, %s, 'Scheduled')
            """,
            (event_id, event_date),
        )

        if self.cursor.rowcount > 0:
            instance_id = int(self.cursor.lastrowid)
        else:
            self.cursor.execute(
                """
                SELECT instance_id
                FROM event_instances
                WHERE event_id = %s AND event_date = %s
                LIMIT 1
                """,
                (event_id, event_date),
            )
            instance = self.cursor.fetchone()
            instance_id = instance["instance_id"] if instance else None

        if instance_id:
            self.cursor.execute(
                """
                INSERT IGNORE INTO event_attendance (instance_id, user_id, event_date, status)
                SELECT %s, user_id, %s, 'Absent'
                FROM event_participants
                WHERE event_id = %s
                """,
                (instance_id, event_date, event_id),
            )

        return instance_id

    def add_event(self):
        try:
            (
                event_name,
                event_type,
                frequency,
                day,
                event_date,
                time_start,
                time_end,
                location,
                participants,
                participants_type,
            ) = self.parameter

            def is_blank(value):
                return value is None or str(value).strip() == ""

            required_values = {
                "event name": event_name,
                "event type": event_type,
                "frequency": frequency,
                "start time": time_start,
                "end time": time_end,
                "location": location,
                "participants type": participants_type,
            }
            missing_values = [label for label, value in required_values.items() if is_blank(value)]
            if missing_values:
                return {"success": False, "message": f"Missing required fields: {', '.join(missing_values)}."}

            event_name = str(event_name).strip()
            event_type = str(event_type).strip()
            frequency = str(frequency).strip().upper()
            day = str(day).strip() if day is not None else None
            location = str(location).strip()
            participants_type = str(participants_type).strip().lower()
            if frequency not in {"ONCE", "DAILY", "WEEKLY"}:
                return {"success": False, "message": "Invalid event frequency."}

            if frequency == "DAILY" and not event_date:
                event_date = date.today().isoformat()

            if frequency != "DAILY" and is_blank(event_date):
                return {"success": False, "message": "Event date is required."}

            if frequency == "WEEKLY" and str(day or "").strip() not in {
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            }:
                return {"success": False, "message": "Event day is required for weekly events."}

            try:
                parsed_event_date = (
                    event_date
                    if isinstance(event_date, date)
                    else datetime.strptime(str(event_date), "%Y-%m-%d").date()
                )
            except ValueError:
                return {"success": False, "message": "Event date must use YYYY-MM-DD format."}

            if parsed_event_date < date.today():
                return {"success": False, "message": "Event date cannot be in the past."}

            try:
                parsed_start = datetime.strptime(str(time_start), "%H:%M:%S").time()
            except ValueError:
                try:
                    parsed_start = datetime.strptime(str(time_start), "%H:%M").time()
                except ValueError:
                    return {"success": False, "message": "Start time must use HH:MM format."}

            try:
                parsed_end = datetime.strptime(str(time_end), "%H:%M:%S").time()
            except ValueError:
                try:
                    parsed_end = datetime.strptime(str(time_end), "%H:%M").time()
                except ValueError:
                    return {"success": False, "message": "End time must use HH:MM format."}

            if parsed_end <= parsed_start:
                return {"success": False, "message": "End time must be later than start time."}

            if frequency == "WEEKLY":
                query = """
                    INSERT INTO events (
                        event_name, event_type, frequency, day, event_date,
                        time_start, time_end, location, active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                """
                params = (
                    event_name,
                    event_type,
                    frequency,
                    day,
                    event_date,
                    time_start,
                    time_end,
                    location,
                )
            else:
                query = """
                    INSERT INTO events (
                        event_name, event_type, frequency, event_date,
                        time_start, time_end, location, active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """
                params = (
                    event_name,
                    event_type,
                    frequency,
                    event_date,
                    time_start,
                    time_end,
                    location,
                )

            self.cursor.execute(query, params)
            event_id = int(self.cursor.lastrowid)

            attached_count = self._attach_event_participants(event_id, participants, participants_type)
            if attached_count == 0:
                self.conn.rollback()
                return {"success": False, "message": "No valid participants were found for this event."}

            if frequency == "ONCE":
                self._ensure_event_instance(event_id, event_date)

            self.conn.commit()
            return {"success": True, "message": "Event created successfully.", "event_id": event_id}
        except connector.IntegrityError:
            self.conn.rollback()
            return {"success": False, "message": "An event with the same name, date, and start time already exists."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error adding event: {err}")
            return {"success": False, "message": f"Database Error: {err}"}

    def add_event_instances(self):
        try:
            event_id, target_date = self.parameter
            instance_id = self._ensure_event_instance(event_id, target_date)
            self.conn.commit()

            return {
                "success": True,
                "message": "Event instances generated successfully.",
                "instance_id": instance_id,
            }
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def check_last_swipe(self):
        try:
            self.cursor.execute(
                """
                SELECT log_type
                FROM event_log
                WHERE user_id = %s
                  AND event_id = %s
                  AND DATE(timestamp) = CURRENT_DATE()
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                self.parameter,
            )
            return self.cursor.fetchone()
        except connector.Error as err:
            return {"success": False, "message": f"Database Error: {err}"}

    def events_authentication(self):
        try:
            user_id, event_id, log_type = self.parameter
            self._ensure_event_instance(event_id, date.today())

            self.cursor.execute(
                """
                INSERT INTO event_log (user_id, event_id, log_type)
                VALUES (%s, %s, %s)
                """,
                (user_id, event_id, log_type),
            )

            if log_type.lower() == "entry":
                attendance_query = """
                    UPDATE event_attendance ea
                    JOIN event_instances ei ON ea.instance_id = ei.instance_id
                    JOIN events e ON ei.event_id = e.event_id
                    SET
                        ea.status = IF(CURRENT_TIME() > ADDTIME(e.time_start, '00:15:00'), 'Late', 'Present'),
                        ea.first_in = COALESCE(ea.first_in, NOW())
                    WHERE ea.user_id = %s
                      AND ei.event_id = %s
                      AND ea.event_date = CURRENT_DATE()
                      AND ea.status IN ('Absent', 'Excused')
                """
            elif log_type.lower() == "exit":
                attendance_query = """
                    UPDATE event_attendance ea
                    JOIN event_instances ei ON ea.instance_id = ei.instance_id
                    SET ea.last_out = NOW()
                    WHERE ea.user_id = %s
                      AND ei.event_id = %s
                      AND ea.event_date = CURRENT_DATE()
                """
            else:
                return {"success": False, "message": "Invalid log type."}

            self.cursor.execute(attendance_query, (user_id, event_id))
            self.conn.commit()
            return {"success": True, "message": "Event logging completed successfully."}
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def update_attendance_status(self):
        try:
            if len(self.parameter) == 3:
                status, remarks, attendance_id = self.parameter
                query = """
                    UPDATE event_attendance
                    SET status = %s, remarks = %s
                    WHERE attendance_id = %s
                """
                params = (status, remarks, attendance_id)
            elif len(self.parameter) == 4:
                status, remarks, user_id, instance_id = self.parameter
                query = """
                    UPDATE event_attendance
                    SET status = %s, remarks = %s
                    WHERE user_id = %s AND instance_id = %s
                """
                params = (status, remarks, user_id, instance_id)
            else:
                return {"success": False, "message": "Invalid attendance update parameters."}

            self.cursor.execute(query, params)
            if self.cursor.rowcount == 0:
                return {"success": False, "message": "No matching attendance record found."}

            self.conn.commit()
            return {"success": True, "message": "Attendance updated successfully."}
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def update_instance_status(self):
        try:
            new_status, instance_id = self.parameter
            self.cursor.execute(
                "UPDATE event_instances SET status = %s WHERE instance_id = %s",
                (new_status, instance_id),
            )
            self.conn.commit()

            if self.cursor.rowcount == 0:
                return {"success": False, "message": "No event instance was updated."}

            return {"success": True, "message": f"Event instance updated to {new_status}."}
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def delete_event(self):
        try:
            event_id = int(self.parameter[0])
            self.cursor.execute("UPDATE events SET active = 0 WHERE event_id = %s", (event_id,))
            self.conn.commit()
            return {"success": self.cursor.rowcount > 0, "message": "Event archived successfully."}
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid event ID."}
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def delete_bulk_events(self):
        try:
            event_ids = [int(event_id) for event_id in self.parameter[0]]
            if not event_ids:
                return {"success": False, "message": "No valid event IDs provided."}

            placeholders = ", ".join(["%s"] * len(event_ids))
            query = f"UPDATE events SET active = 0 WHERE event_id IN ({placeholders})"
            self.cursor.execute(query, tuple(event_ids))
            self.conn.commit()
            return {"success": True, "message": f"{len(event_ids)} events archived successfully."}
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid event IDs."}
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def get_all_events(self):
        try:
            self.cursor.execute("SELECT * FROM events WHERE active = 1 ORDER BY event_id DESC")
            result = self.cursor.fetchall()
            return [self._serialize_row(row) for row in result]
        except connector.Error as err:
            print(f"Error fetching all events: {err}")
            return []

    @staticmethod
    def get_events_dashboard(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM departments")
            total_departments = cursor.fetchone()["total"] or 0

            cursor.execute(
                """
                SELECT
                    e.event_id AS event_id,
                    e.event_name AS name,
                    e.event_type AS type,
                    e.frequency AS frequency,
                    DATE_FORMAT(e.event_date, '%Y-%m-%d') AS date,
                    TRIM(DATE_FORMAT(e.time_start, '%l:%i %p')) AS time_start,
                    TRIM(DATE_FORMAT(e.time_end, '%l:%i %p')) AS time_end,
                    e.location AS location,
                    GROUP_CONCAT(DISTINCT d.department_name ORDER BY d.department_name SEPARATOR ', ') AS dept,
                    COUNT(DISTINCT d.department_id) AS dept_count,
                    COUNT(DISTINCT ep.user_id) AS participant_count
                FROM events e
                LEFT JOIN event_participants ep ON e.event_id = ep.event_id
                LEFT JOIN users u ON ep.user_id = u.user_id AND u.active = 1
                LEFT JOIN employees emp ON ep.user_id = emp.user_id
                LEFT JOIN departments d ON emp.department_id = d.department_id
                WHERE e.active = 1
                GROUP BY
                    e.event_id, e.event_name, e.event_type, e.frequency,
                    e.event_date, e.time_start, e.time_end, e.location
                ORDER BY e.event_date DESC, e.event_id DESC
                """
            )
            result = cursor.fetchall()

            for row in result:
                row["all_departments"] = bool(total_departments and row["dept_count"] == total_departments)
                if not row["dept"]:
                    row["dept"] = "Custom Participants" if row["participant_count"] else "No Participants"

            return result
        except connector.Error as err:
            print(f"Error fetching dashboard events: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_events_kiosk(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    ei.instance_id AS instance_id,
                    e.event_id AS event_id,
                    e.event_name AS name,
                    e.event_type AS type,
                    e.frequency AS frequency,
                    ei.event_date AS date,
                    TRIM(DATE_FORMAT(e.time_start, '%l:%i %p')) AS time_start,
                    TRIM(DATE_FORMAT(e.time_end, '%l:%i %p')) AS time_end,
                    e.location AS location
                FROM event_instances ei
                JOIN events e ON ei.event_id = e.event_id
                WHERE ei.event_date = CURDATE()
                  AND ei.status = 'Scheduled'
                  AND e.active = 1
                ORDER BY e.time_start ASC, e.event_name ASC
                """
            )
            result = cursor.fetchall()
            for row in result:
                if isinstance(row.get("date"), date):
                    row["date"] = row["date"].isoformat()
            return result
        except connector.Error as err:
            print(f"Error fetching kiosk events: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_all_events_for_reports(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT DISTINCT
                    ei.instance_id AS instance_id,
                    e.event_id AS event_id,
                    e.event_name AS name,
                    e.event_type AS type,
                    e.frequency AS frequency,
                    ei.event_date AS date,
                    TRIM(DATE_FORMAT(e.time_start, '%l:%i %p')) AS time_start,
                    TRIM(DATE_FORMAT(e.time_end, '%l:%i %p')) AS time_end,
                    e.location AS location,
                    e.active AS active
                FROM event_instances ei
                JOIN events e ON ei.event_id = e.event_id
                ORDER BY ei.event_date DESC, e.event_name ASC
                """
            )
            result = cursor.fetchall()
            for row in result:
                if isinstance(row.get("date"), date):
                    row["date"] = row["date"].isoformat()
            return result
        except connector.Error as err:
            print(f"Error fetching report events: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_admin_departments(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT department_id AS dept_id, department_name AS dept_name
                FROM departments
                ORDER BY department_name ASC
                """
            )
            return cursor.fetchall()
        except connector.Error as err:
            print(f"Error fetching departments: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_student_logs(conn, limit=6):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    gl.log_type,
                    s.student_name,
                    c.course_name,
                    gl.timestamp
                FROM general_log gl
                JOIN students s ON gl.user_id = s.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE DATE(gl.timestamp) = CURDATE()
                ORDER BY gl.timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
            result = cursor.fetchall()

            logs = []
            for row in result:
                logs.append(
                    {
                        "type": "in" if row["log_type"] == "Entry" else "out",
                        "name": row.get("student_name", "Unknown User"),
                        "course": row.get("course_name", "N/A"),
                        "time": row["timestamp"].strftime("%I:%M %p").lstrip("0"),
                    }
                )
            return logs
        except connector.Error as err:
            print(f"Error fetching student logs: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_admin_student_activity(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    s.student_id,
                    COALESCE(NULLIF(TRIM(s.student_name), ''), 'Unknown Student') AS student_name,
                    COALESCE(NULLIF(TRIM(c.course_name), ''), 'N/A') AS course_name,
                    DATE(gl.timestamp) AS log_date,
                    MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END) AS first_entry,
                    MAX(CASE WHEN gl.log_type = 'Exit' THEN gl.timestamp END) AS last_exit,
                    CASE
                        WHEN MAX(CASE WHEN gl.log_type = 'Exit' THEN gl.timestamp END) IS NULL THEN 'Inside'
                        ELSE 'Out'
                    END AS attendance_status
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                JOIN students s ON gl.user_id = s.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE u.active = 1
                GROUP BY s.user_id, s.student_id, s.student_name, c.course_name, DATE(gl.timestamp)
                HAVING MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END) IS NOT NULL
                ORDER BY log_date DESC, first_entry DESC, student_name ASC
                """
            )
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                status = row["attendance_status"] or "Out"
                logs.append(
                    {
                        "id": row["student_id"],
                        "name": row["student_name"],
                        "course": row["course_name"],
                        "date": row["log_date"].isoformat() if row.get("log_date") else "",
                        "time_in": row["first_entry"].strftime("%I:%M %p").lstrip("0") if row.get("first_entry") else "--:--",
                        "time_out": row["last_exit"].strftime("%I:%M %p").lstrip("0") if row.get("last_exit") else "--:--",
                        "status": status,
                        "status_class": "success" if status == "Inside" else "secondary",
                    }
                )

            return logs
        except connector.Error as err:
            print(f"Error fetching admin student activity: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_admin_student_records(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    s.student_id,
                    COALESCE(NULLIF(TRIM(s.student_name), ''), 'Unknown Student') AS student_name,
                    COALESCE(NULLIF(TRIM(c.course_name), ''), 'N/A') AS course_name,
                    COALESCE(u.active, 1) AS is_active
                FROM students s
                JOIN users u ON s.user_id = u.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                ORDER BY is_active DESC, student_name ASC
                """
            )
            rows = cursor.fetchall()

            records = []
            for row in rows:
                is_active = bool(row.get("is_active"))
                records.append(
                    {
                        "id": row["student_id"],
                        "name": row["student_name"],
                        "course": row["course_name"],
                        "status": "Active" if is_active else "Inactive",
                        "status_class": "success" if is_active else "secondary",
                    }
                )

            return records
        except connector.Error as err:
            print(f"Error fetching admin student records: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_admin_employee_activity(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    ea.attendance_id,
                    e.employee_id,
                    COALESCE(NULLIF(TRIM(e.employee_name), ''), 'Unknown Employee') AS employee_name,
                    COALESCE(NULLIF(TRIM(d.department_name), ''), 'N/A') AS department_name,
                    COALESCE(NULLIF(TRIM(e.position), ''), 'N/A') AS position,
                    COALESCE(NULLIF(TRIM(ev.event_name), ''), 'N/A') AS event_name,
                    ei.event_date,
                    ea.first_in,
                    ea.last_out,
                    ea.status
                FROM event_attendance ea
                JOIN event_instances ei ON ea.instance_id = ei.instance_id
                JOIN events ev ON ei.event_id = ev.event_id
                JOIN employees e ON ea.user_id = e.user_id
                JOIN users u ON e.user_id = u.user_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                WHERE ea.first_in IS NOT NULL
                  AND u.active = 1
                ORDER BY ei.event_date DESC, ea.first_in DESC, employee_name ASC
                """
            )
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                name = row["employee_name"]
                initials = "".join(part[0] for part in name.split()[:2]).upper() or name[:1].upper()
                status = row.get("status") or "Absent"
                status_class = {
                    "Present": "success",
                    "Late": "warning",
                    "Excused": "info",
                }.get(status, "secondary")

                logs.append(
                    {
                        "attendance_id": row["attendance_id"],
                        "id": row["employee_id"],
                        "initials": initials,
                        "name": name,
                        "dept": row["department_name"],
                        "position": row["position"],
                        "event_name": row["event_name"],
                        "date": row["event_date"].isoformat() if row.get("event_date") else "",
                        "date_formatted": row["event_date"].strftime("%b %d, %Y") if row.get("event_date") else "",
                        "in": row["first_in"].strftime("%I:%M %p").lstrip("0") if row.get("first_in") else "--:--",
                        "out": row["last_out"].strftime("%I:%M %p").lstrip("0") if row.get("last_out") else "--:--",
                        "status": status,
                        "status_class": status_class,
                    }
                )

            return logs
        except connector.Error as err:
            print(f"Error fetching admin employee activity: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_admin_employee_records(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    e.employee_id,
                    COALESCE(NULLIF(TRIM(e.employee_name), ''), 'Unknown Employee') AS employee_name,
                    COALESCE(NULLIF(TRIM(d.department_name), ''), 'N/A') AS department_name,
                    COALESCE(NULLIF(TRIM(e.position), ''), 'N/A') AS position,
                    COALESCE(u.active, 1) AS is_active
                FROM employees e
                JOIN users u ON e.user_id = u.user_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                ORDER BY is_active DESC, employee_name ASC
                """
            )
            rows = cursor.fetchall()

            records = []
            for row in rows:
                is_active = bool(row.get("is_active"))
                records.append(
                    {
                        "id": row["employee_id"],
                        "name": row["employee_name"],
                        "dept": row["department_name"],
                        "position": row["position"],
                        "status": "Active" if is_active else "Inactive",
                        "status_class": "success" if is_active else "secondary",
                    }
                )

            return records
        except connector.Error as err:
            print(f"Error fetching admin employee records: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_event_instances(conn, event_id):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    instance_id,
                    DATE_FORMAT(event_date, '%b %e, %Y') AS event_date,
                    status
                FROM event_instances
                WHERE event_id = %s
                ORDER BY event_date ASC
                """,
                (event_id,),
            )
            return cursor.fetchall()
        except connector.Error as err:
            print(f"Error fetching event instances: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_instance_attendance(conn, instance_id):
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    ea.attendance_id,
                    ea.user_id,
                    ea.status,
                    LOWER(TRIM(DATE_FORMAT(ea.first_in, '%l:%i %p'))) AS first_in,
                    LOWER(TRIM(DATE_FORMAT(ea.last_out, '%l:%i %p'))) AS last_out,
                    ea.remarks,
                    COALESCE(s.student_name, e.employee_name, v.visitor_name) AS user_name,
                    COALESCE(d.department_name, c.course_name, 'Visitor') AS department
                FROM event_attendance ea
                LEFT JOIN users u ON ea.user_id = u.user_id
                LEFT JOIN visitors v ON u.user_id = v.user_id
                LEFT JOIN students s ON u.user_id = s.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                LEFT JOIN employees e ON u.user_id = e.user_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                WHERE ea.instance_id = %s
                ORDER BY user_name ASC
                """,
                (instance_id,),
            )
            return cursor.fetchall()
        except connector.Error as err:
            print(f"Error fetching instance attendance: {err}")
            return []
        finally:
            cursor.close()

    @staticmethod
    def get_report_queries(conn, category, report_type, department_filter, start_date, end_date):
        cursor = conn.cursor(dictionary=True)
        normalized_category = {
            "general": "General Logs",
            "visitor": "Visitor Logs",
            "event": "Event Attendance",
            "violation": "Violations",
        }.get((category or "").lower(), category or "General Logs")

        report_title = "System Report"
        event_name_display = "Campus Activity"
        col_headers = ["Name", "Detail", "Time", "Status", "Remarks"]
        raw_logs = []
        total_expected = 0
        total_present = 0
        filter_display = "All"

        try:
            filter_value = str(department_filter or "All").strip()

            if normalized_category == "Event Attendance":
                report_title = "Event Attendance Report"
                event_name_display = "Scheduled Event"
                col_headers = ["Participant Name", "Role / Affiliation", "Time In", "Time Out", "Status", "Remarks"]
                dept_condition = ""
                dept_params = []
                if filter_value.lower() != "all":
                    dept_condition = "AND d.department_id = %s"
                    dept_params = [filter_value]
                    cursor.execute(
                        "SELECT department_name FROM departments WHERE department_id = %s",
                        (filter_value,),
                    )
                    dept_row = cursor.fetchone()
                    filter_display = dept_row["department_name"] if dept_row else filter_value
                else:
                    filter_display = "All Departments"

                cursor.execute("SELECT event_name FROM events WHERE event_id = %s", (report_type,))
                event_info = cursor.fetchone()
                if event_info:
                    event_name_display = event_info["event_name"]

                query = f"""
                    SELECT
                        COALESCE(e.employee_name, 'Unknown Employee') AS name,
                        CONCAT(
                            'EMPLOYEE - ',
                            COALESCE(d.department_name, 'N/A')
                        ) AS detail,
                        LOWER(TRIM(DATE_FORMAT(ea.first_in, '%l:%i %p'))) AS time_in,
                        LOWER(TRIM(DATE_FORMAT(ea.last_out, '%l:%i %p'))) AS time_out,
                        ea.status AS status,
                        COALESCE(ea.remarks, 'N/A') AS remarks
                    FROM event_attendance ea
                    JOIN event_instances ei ON ea.instance_id = ei.instance_id
                    JOIN users u ON ea.user_id = u.user_id
                    JOIN employees e ON u.user_id = e.user_id
                    LEFT JOIN departments d ON e.department_id = d.department_id
                    WHERE ei.event_id = %s
                      AND ei.event_date BETWEEN %s AND %s
                      AND u.role = 'employee'
                      {dept_condition}
                    ORDER BY ea.first_in ASC, name ASC
                """
                cursor.execute(query, [report_type, start_date, end_date] + dept_params)
                raw_logs = cursor.fetchall()

                expected_query = f"""
                    SELECT COUNT(*) AS count
                    FROM event_participants ep
                    JOIN users u ON ep.user_id = u.user_id
                    JOIN employees e ON ep.user_id = e.user_id
                    LEFT JOIN departments d ON e.department_id = d.department_id
                    WHERE ep.event_id = %s
                      AND u.role = 'employee'
                      {dept_condition}
                """
                cursor.execute(expected_query, [report_type] + dept_params)
                expected_result = cursor.fetchone()
                total_expected = expected_result["count"] if expected_result else 0
                total_present = sum(1 for log in raw_logs if log["status"] in {"Present", "Late"})

            elif normalized_category == "Visitor Logs":
                report_title = "Visitor Logs Report"
                event_name_display = "Visitor Activity"
                col_headers = ["Visitor Name", "Purpose", "Time In", "Time Out", "Visitor ID"]
                purpose_condition = ""
                purpose_params = []
                if filter_value.lower() != "all":
                    purpose_condition = "AND COALESCE(NULLIF(TRIM(v.purpose), ''), 'N/A') = %s"
                    purpose_params = [filter_value]
                    filter_display = filter_value
                else:
                    filter_display = "All Purposes"

                query = f"""
                    SELECT
                        v.visitor_name AS name,
                        COALESCE(NULLIF(TRIM(v.purpose), ''), 'N/A') AS detail,
                        LOWER(TRIM(DATE_FORMAT(MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END), '%l:%i %p'))) AS time_in,
                        LOWER(TRIM(DATE_FORMAT(MAX(CASE WHEN gl.log_type = 'Exit' THEN gl.timestamp END), '%l:%i %p'))) AS time_out,
                        v.visitor_id AS remarks
                    FROM visitors v
                    JOIN users u ON v.user_id = u.user_id
                    LEFT JOIN general_log gl ON gl.user_id = v.user_id
                    WHERE COALESCE(u.active, 1) = 1
                      AND u.role = 'visitor'
                      {purpose_condition}
                    GROUP BY v.seq, v.visitor_id, v.visitor_name, v.purpose
                    HAVING DATE(MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END)) BETWEEN %s AND %s
                    ORDER BY MIN(CASE WHEN gl.log_type = 'Entry' THEN gl.timestamp END) DESC
                """
                cursor.execute(query, purpose_params + [start_date, end_date])
                raw_logs = cursor.fetchall()
                total_expected = len(raw_logs)
                total_present = len(raw_logs)

            elif normalized_category == "Violations":
                report_title = "Violations Report"
                event_name_display = "Security Violations"
                col_headers = ["User Name", "Description", "Time", "Status", "Remarks"]
                role_condition = ""
                role_params = []
                if filter_value.lower() in {"student", "visitor", "employee"}:
                    role_condition = "AND u.role = %s"
                    role_params = [filter_value.lower()]
                    filter_display = f"{filter_value.capitalize()}s"
                else:
                    filter_display = "All Subjects"

                query = f"""
                    SELECT
                        COALESCE(e.employee_name, s.student_name, v.visitor_name, 'Unknown User') AS name,
                        violation.description AS detail,
                        LOWER(TRIM(DATE_FORMAT(violation.created_at, '%l:%i %p'))) AS time,
                        'Violation' AS status,
                        violation.description AS remarks
                    FROM violations violation
                    JOIN users u ON violation.user_id = u.user_id
                    LEFT JOIN employees e ON u.user_id = e.user_id
                    LEFT JOIN departments d ON e.department_id = d.department_id
                    LEFT JOIN students s ON u.user_id = s.user_id
                    LEFT JOIN visitors v ON u.user_id = v.user_id
                    WHERE DATE(violation.created_at) BETWEEN %s AND %s
                      {role_condition}
                    ORDER BY violation.created_at DESC
                """
                cursor.execute(query, [start_date, end_date] + role_params)
                raw_logs = cursor.fetchall()
                total_expected = len(raw_logs)
                total_present = len(raw_logs)

            else:
                report_title = "Student Campus Access Logs"
                event_name_display = "Student Gates Entry / Exit"
                col_headers = ["Student Name", "Program", "Time In", "Time Out", "Gate"]
                course_condition = ""
                course_params = []
                if filter_value.lower() != "all":
                    course_condition = "AND c.course_id = %s"
                    course_params = [filter_value]
                    cursor.execute(
                        "SELECT course_name FROM courses WHERE course_id = %s",
                        (filter_value,),
                    )
                    course_row = cursor.fetchone()
                    filter_display = course_row["course_name"] if course_row else filter_value
                else:
                    filter_display = "All Programs"

                query = f"""
                    SELECT
                        COALESCE(s.student_name, 'Unknown Student') AS name,
                        COALESCE(c.course_name, 'N/A') AS detail,
                        TIME_FORMAT(gl.timestamp, '%h:%i %p') AS time,
                        gl.log_type AS status,
                        COALESCE(gl.gate, 'Main Gate') AS remarks
                    FROM general_log gl
                    JOIN users u ON gl.user_id = u.user_id
                    JOIN students s ON u.user_id = s.user_id
                    LEFT JOIN courses c ON s.course_id = c.course_id
                    WHERE DATE(gl.timestamp) BETWEEN %s AND %s
                      AND u.role = 'student'
                      {course_condition}
                    ORDER BY gl.timestamp DESC
                """
                cursor.execute(query, [start_date, end_date] + course_params)
                raw_logs = cursor.fetchall()
                total_expected = len(raw_logs)
                total_present = len(raw_logs)

            return {
                "report_title": report_title,
                "event_name_display": event_name_display,
                "col_headers": col_headers,
                "raw_logs": raw_logs,
                "total_expected": total_expected,
                "total_present": total_present,
                "filter_display": filter_display,
            }
        except connector.Error as err:
            print(f"Error fetching report data: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_overall_dashboard_stats(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            today = datetime.now().date()

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                """,
                (today,),
            )
            total_entries = cursor.fetchone()["total"] or 0

            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM students s JOIN users u ON s.user_id = u.user_id WHERE s.status = 'Inside' AND u.active = 1)
                    + (SELECT COUNT(*) FROM employees e JOIN users u ON e.user_id = u.user_id WHERE e.status = 'Inside' AND u.active = 1)
                    + (SELECT COUNT(*) FROM visitors v JOIN users u ON v.user_id = u.user_id WHERE v.status = 'Inside' AND u.active = 1)
                    AS inside
                """
            )
            currently_inside = cursor.fetchone()["inside"] or 0

            cursor.execute(
                """
                SELECT AVG(TIMESTAMPDIFF(MINUTE, e.timestamp, x.timestamp)) AS avg_dwell
                FROM general_log e
                JOIN general_log x
                  ON e.user_id = x.user_id
                 AND DATE(e.timestamp) = DATE(x.timestamp)
                 AND e.log_type = 'Entry'
                 AND x.log_type = 'Exit'
                 AND x.timestamp > e.timestamp
                WHERE DATE(e.timestamp) = %s
                """,
                (today,),
            )
            avg_minutes = cursor.fetchone()["avg_dwell"] or 0
            avg_dwell = f"{int(avg_minutes // 60)} hrs {int(avg_minutes % 60)} mins"

            cursor.execute(
                """
                SELECT HOUR(timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                GROUP BY HOUR(timestamp)
                ORDER BY cnt DESC
                LIMIT 1
                """,
                (today,),
            )
            peak_row = cursor.fetchone()
            peak_hour = _format_hour_label(peak_row["hr"]) if peak_row else "N/A"

            cursor.execute(
                """
                SELECT HOUR(timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                GROUP BY HOUR(timestamp)
                """,
                (today,),
            )
            hourly = {row["hr"]: row["cnt"] for row in cursor.fetchall()}
            traffic_chart = [hourly.get(hour, 0) for hour in range(6, 18)]

            cursor.execute(
                """
                SELECT COUNT(*) AS total, SUM(status IN ('Present', 'Late')) AS attended
                FROM event_attendance
                WHERE event_date = %s
                """,
                (today,),
            )
            event_row = cursor.fetchone()
            total_invited = event_row["total"] or 0
            total_attended = int(event_row["attended"] or 0)
            attendance_rate = (
                f"{round((total_attended / total_invited) * 100, 1)}%"
                if total_invited
                else "N/A"
            )
            attendance_raw = f"{total_attended:,} / {total_invited:,} Attendees"

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                """,
                (today - timedelta(days=1),),
            )
            yesterday_total = cursor.fetchone()["total"] or 0
            if yesterday_total > 0:
                trend = f"{round(((total_entries - yesterday_total) / yesterday_total) * 100):+d}%"
            else:
                trend = "N/A"

            cursor.execute(
                """
                SELECT d.department_name, COUNT(*) AS cnt
                FROM general_log gl
                JOIN employees emp ON gl.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE DATE(gl.timestamp) = %s
                  AND gl.log_type = 'Entry'
                  AND u.active = 1
                GROUP BY d.department_name
                ORDER BY cnt DESC
                LIMIT 5
                """,
                (today,),
            )
            department_rows = cursor.fetchall()
            total_department_entries = sum(row["cnt"] for row in department_rows) or 1
            dept_distribution = [
                round((row["cnt"] / total_department_entries) * 100)
                for row in department_rows
            ]
            while len(dept_distribution) < 5:
                dept_distribution.append(0)

            return {
                "total_entries": f"{total_entries:,}",
                "entries_trend": trend,
                "currently_inside": f"{currently_inside:,}",
                "avg_dwell_time": avg_dwell,
                "peak_hour": peak_hour,
                "traffic_chart": traffic_chart,
                "event_attendance_rate": attendance_rate,
                "event_attendance_raw": attendance_raw,
                "dept_distribution": dept_distribution,
                "alerts": [],
            }
        except connector.Error as err:
            print(f"Error fetching overall dashboard stats: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_student_dashboard_stats(conn):
        cursor = conn.cursor(dictionary=True)
        try:
            today = datetime.now().date()

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student'
                  AND DATE(gl.timestamp) = %s
                  AND gl.log_type = 'Entry'
                """,
                (today,),
            )
            total_entries = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT COUNT(*) AS inside FROM students WHERE status = 'Inside'")
            currently_inside = cursor.fetchone()["inside"] or 0

            cursor.execute(
                """
                SELECT AVG(TIMESTAMPDIFF(MINUTE, e.timestamp, x.timestamp)) AS avg_stay
                FROM general_log e
                JOIN general_log x
                  ON e.user_id = x.user_id
                 AND DATE(e.timestamp) = DATE(x.timestamp)
                 AND e.log_type = 'Entry'
                 AND x.log_type = 'Exit'
                 AND x.timestamp > e.timestamp
                JOIN users u ON e.user_id = u.user_id
                WHERE u.role = 'student' AND DATE(e.timestamp) = %s
                """,
                (today,),
            )
            avg_minutes = cursor.fetchone()["avg_stay"] or 0
            avg_stay = f"{round(avg_minutes / 60, 1)} Hrs"

            cursor.execute(
                """
                SELECT HOUR(gl.timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student'
                  AND DATE(gl.timestamp) = %s
                  AND gl.log_type = 'Entry'
                GROUP BY HOUR(gl.timestamp)
                ORDER BY cnt DESC
                LIMIT 1
                """,
                (today,),
            )
            peak_row = cursor.fetchone()
            peak_hour = _format_hour_label(peak_row["hr"]) if peak_row else "N/A"

            cursor.execute("SELECT COUNT(*) AS total FROM students")
            total_students = cursor.fetchone()["total"] or 1
            peak_load = f"{round((currently_inside / total_students) * 100)}%"

            cursor.execute(
                """
                SELECT HOUR(gl.timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student'
                  AND DATE(gl.timestamp) = %s
                  AND gl.log_type = 'Entry'
                GROUP BY HOUR(gl.timestamp)
                """,
                (today,),
            )
            hourly = {row["hr"]: row["cnt"] for row in cursor.fetchall()}
            hourly_traffic = [hourly.get(hour, 0) for hour in range(6, 18)]

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student'
                  AND DATE(gl.timestamp) = %s
                  AND gl.log_type = 'Entry'
                """,
                (today - timedelta(days=1),),
            )
            yesterday_total = cursor.fetchone()["total"] or 0
            if yesterday_total > 0:
                trend = f"{round(((total_entries - yesterday_total) / yesterday_total) * 100):+d}%"
            else:
                trend = "N/A"

            return {
                "total_entries": f"{total_entries:,}",
                "entries_trend": trend,
                "peak_hour": peak_hour,
                "peak_load": peak_load,
                "currently_inside": f"{currently_inside:,}",
                "avg_stay": avg_stay,
                "hourly_traffic": hourly_traffic,
                "watchlist": [],
                "curfew_trigger": "09:40:00 PM",
            }
        except connector.Error as err:
            print(f"Error fetching student dashboard stats: {err}")
            return None
        finally:
            cursor.close()

    @staticmethod
    def get_employee_dashboard_stats(conn, instance_id=None):
        cursor = conn.cursor(dictionary=True)
        try:
            today = datetime.now().date()

            # 1. Fetch past event instances for the dropdown
            cursor.execute(
                """
                SELECT ei.instance_id, e.event_name, DATE_FORMAT(ei.event_date, '%b %d, %Y') as date_str
                FROM event_instances ei
                JOIN events e ON ei.event_id = e.event_id
                WHERE ei.event_date <= CURDATE()
                ORDER BY ei.event_date DESC, ei.instance_id DESC
                LIMIT 20
                """
            )
            event_instances_list = cursor.fetchall()

            # 2. Determine target instance and date
            if instance_id:
                target_instance_id = int(instance_id)
                cursor.execute("SELECT event_date FROM event_instances WHERE instance_id = %s", (target_instance_id,))
                target_date_row = cursor.fetchone()
                target_date = target_date_row["event_date"] if target_date_row else today
            else:
                cursor.execute(
                    """
                    SELECT MAX(ea.instance_id) AS latest_instance, MAX(ea.event_date) as latest_date
                    FROM event_attendance ea
                    JOIN employees emp ON ea.user_id = emp.user_id
                    JOIN users u ON emp.user_id = u.user_id
                    WHERE u.active = 1
                    """
                )
                latest_row = cursor.fetchone()
                target_instance_id = latest_row["latest_instance"] if latest_row and latest_row["latest_instance"] else None
                target_date = latest_row["latest_date"] if latest_row and latest_row["latest_date"] else today
            
            if not target_instance_id and event_instances_list:
                target_instance_id = event_instances_list[0]['instance_id']

            # 3. Overall Attendance for the event
            cursor.execute(
                """
                SELECT ea.status, COUNT(*) AS cnt
                FROM event_attendance ea
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                WHERE ea.instance_id = %s
                  AND u.active = 1
                GROUP BY ea.status
                """,
                (target_instance_id,)
            )
            attendance_map = {row["status"]: row["cnt"] for row in cursor.fetchall()}
            attendance_data = [
                attendance_map.get("Present", 0),
                attendance_map.get("Late", 0),
                attendance_map.get("Absent", 0),
            ]

            total_invited = sum(attendance_map.values())
            present_count = attendance_map.get("Present", 0)
            late_count = attendance_map.get("Late", 0)
            attendees_count = present_count + late_count

            on_time_rate = (
                f"{round((present_count / attendees_count) * 100)}%"
                if attendees_count
                else "N/A"
            )
            on_time_percentage = round((present_count / attendees_count) * 100) if attendees_count > 0 else 0

            participation_pct = (attendees_count / total_invited * 100) if total_invited > 0 else 0
            if total_invited == 0:
                participation_level = "N/A"
            elif participation_pct > 80:
                participation_level = "High"
            elif participation_pct > 50:
                participation_level = "Medium"
            else:
                participation_level = "Low"

            # 4. Tardiness and Peak Check-in Time
            cursor.execute(
                """
                SELECT AVG(
                    TIMESTAMPDIFF(
                        MINUTE,
                        TIMESTAMP(ei.event_date, e.time_start),
                        ea.first_in
                    )
                ) AS avg_late
                FROM event_attendance ea
                JOIN event_instances ei ON ea.instance_id = ei.instance_id
                JOIN events e ON ei.event_id = e.event_id
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                WHERE ea.instance_id = %s
                  AND ea.status = 'Late'
                  AND u.active = 1
                """,
                (target_instance_id,)
            )
            avg_late = cursor.fetchone()["avg_late"] or 0
            avg_tardiness = f"{int(avg_late)} mins"

            # Peak check-in time
            cursor.execute(
                """
                SELECT 
                    TIME_FORMAT(ea.first_in, '%h:%i %p') AS time_val,
                    CONCAT(DATE_FORMAT(ea.first_in, '%h:'), LPAD(FLOOR(MINUTE(ea.first_in)/15)*15, 2, '0'), DATE_FORMAT(ea.first_in, ' %p')) AS time_bucket,
                    COUNT(*) AS checkins
                FROM event_attendance ea
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                WHERE ea.instance_id = %s
                  AND ea.first_in IS NOT NULL
                  AND u.active = 1
                GROUP BY time_bucket
                ORDER BY MIN(ea.first_in) ASC
                """,
                (target_instance_id,)
            )
            peak_rows = cursor.fetchall()
            peak_checkin_data = [row["checkins"] for row in peak_rows]
            peak_checkin_labels = [row["time_bucket"] for row in peak_rows]

            # 5. Department Participation
            cursor.execute(
                """
                SELECT
                    d.department_name AS name,
                    CAST(ROUND(SUM(ea.status IN ('Present', 'Late')) / COUNT(*) * 100) AS UNSIGNED) AS value
                FROM event_attendance ea
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE ea.instance_id = %s
                  AND u.active = 1
                GROUP BY d.department_name
                ORDER BY value DESC, d.department_name ASC
                LIMIT 5
                """,
                (target_instance_id,)
            )
            dept_participation = [
                {"name": row["name"], "value": row["value"]}
                for row in cursor.fetchall()
            ]

            # 6. Upcoming Events
            cursor.execute(
                """
                SELECT
                    e.event_name,
                    DATE_FORMAT(ei.event_date, '%b %d') AS date,
                    TIME_FORMAT(e.time_start, '%h:%i %p') AS time,
                    e.location
                FROM event_instances ei
                JOIN events e ON ei.event_id = e.event_id
                JOIN event_participants ep ON ei.event_id = ep.event_id
                JOIN employees emp ON ep.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                WHERE ei.event_date >= CURDATE()
                  AND ei.status = 'Scheduled'
                  AND u.active = 1
                GROUP BY ei.instance_id, e.event_name, ei.event_date, e.time_start, e.location
                ORDER BY ei.event_date ASC, e.time_start ASC
                LIMIT 3
                """
            )
            upcoming_events = cursor.fetchall()

            # 7. Recent Activity
            cursor.execute(
                """
                SELECT
                    emp.employee_name,
                    el.log_type AS type,
                    TIME_FORMAT(el.timestamp, '%h:%i %p') AS time,
                    e.event_name AS event
                FROM event_log el
                JOIN employees emp ON el.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                JOIN events e ON el.event_id = e.event_id
                WHERE u.active = 1
                ORDER BY el.timestamp DESC
                LIMIT 5
                """
            )
            recent_activity = cursor.fetchall()

            # 8. Leaderboard (still 30 days)
            cursor.execute(
                """
                SELECT
                    emp.employee_name,
                    COUNT(*) AS present_count
                FROM event_attendance ea
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                WHERE ea.status = 'Present'
                  AND ea.event_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                  AND u.active = 1
                GROUP BY emp.user_id, emp.employee_name
                ORDER BY present_count DESC, emp.employee_name ASC
                LIMIT 5
                """
            )
            leaderboard = cursor.fetchall()

            # 9. Dept Comparison
            cursor.execute(
                """
                SELECT
                    d.department_name AS dept,
                    COUNT(*) AS invited,
                    SUM(ea.status IN ('Present', 'Late')) AS attended,
                    CAST(ROUND(SUM(ea.status IN ('Present', 'Late')) / COUNT(*) * 100) AS UNSIGNED) AS rate
                FROM event_attendance ea
                JOIN employees emp ON ea.user_id = emp.user_id
                JOIN users u ON emp.user_id = u.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE ea.instance_id = %s
                  AND u.active = 1
                GROUP BY d.department_id, d.department_name
                ORDER BY rate DESC, d.department_name ASC
                """,
                (target_instance_id,)
            )
            dept_comparison = cursor.fetchall()

            return {
                "attendance_data": attendance_data,
                "peak_checkin_data": peak_checkin_data if peak_checkin_data else [0] * 5,
                "peak_checkin_labels": peak_checkin_labels if peak_checkin_labels else ["N/A"] * 5,
                "dept_participation": dept_participation,
                "avg_tardiness": avg_tardiness,
                "on_time_rate": on_time_rate,
                "on_time_percentage": on_time_percentage,
                "participation_level": participation_level,
                "target_date": str(target_date),
                "upcoming_events": upcoming_events,
                "recent_activity": recent_activity,
                "leaderboard": leaderboard,
                "dept_comparison": dept_comparison,
                "event_instances_list": event_instances_list,
                "selected_instance_id": target_instance_id,
            }
        except connector.Error as err:
            print(f"Error fetching employee dashboard stats: {err}")
            return None
        finally:
            cursor.close()


class EmployeeModel:
    def add_employee(self, employee_id, employee_name, department_id, position):
        conn = connect_db()
        if conn is None:
            return {"success": False, "error": "Database connection failed"}

        cursor = None
        try:
            employee_id = str(employee_id or "").strip()
            employee_name = str(employee_name or "").strip()
            department_id = str(department_id or "").strip()
            position = str(position or "").strip()

            if not employee_id or not employee_name or not department_id or not position:
                return {"success": False, "error": "All employee fields are required."}

            cursor = conn.cursor()
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
                return {"success": False, "error": "Selected department does not exist."}

            cursor.execute(
                """
                SELECT employee_id
                FROM employees
                WHERE employee_id = %s
                LIMIT 1
                """,
                (employee_id,),
            )
            if cursor.fetchone():
                return {"success": False, "error": f"Employee already exists: {employee_id}"}

            cursor.execute(
                """
                INSERT INTO users (role, active)
                VALUES (%s, %s)
                """,
                ("employee", 1),
            )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO employees
                    (user_id, employee_id, employee_name, department_id, position, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, employee_id, employee_name, department_id, position, "Outside"),
            )
            conn.commit()
            return {"success": True}
        except Exception as err:
            conn.rollback()
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def add_employee_excel(self, conn, employee_id, employee_name, department_name, position):
        cursor = None
        try:
            cursor = conn.cursor()

            employee_id = str(employee_id or "").strip()
            employee_name = str(employee_name or "").strip().title()
            department_name = str(department_name or "").strip().upper().replace("\u2019", "'")
            position = str(position or "").strip()

            if not employee_id or not employee_name or not department_name:
                return {"success": False, "error": "Missing required fields"}

            cursor.execute(
                """
                SELECT department_id
                FROM departments
                WHERE UPPER(TRIM(department_name)) = TRIM(%s)
                LIMIT 1
                """,
                (department_name,),
            )
            department = cursor.fetchone()
            if not department:
                return {"success": False, "error": f"Department not found: {department_name}"}

            department_id = department[0]

            cursor.execute(
                """
                SELECT employee_id
                FROM employees
                WHERE employee_id = %s
                LIMIT 1
                """,
                (employee_id,),
            )
            if cursor.fetchone():
                return {"success": False, "error": f"Employee already exists: {employee_id}"}

            cursor.execute(
                """
                INSERT INTO users (role, active)
                VALUES (%s, %s)
                """,
                ("employee", 1),
            )
            user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO employees
                    (user_id, employee_id, employee_name, department_id, position, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, employee_id, employee_name, department_id, position or None, "Outside"),
            )
            conn.commit()
            return {"success": True}
        except Exception as err:
            if conn:
                conn.rollback()
            return {"success": False, "error": str(err)}
        finally:
            if cursor:
                cursor.close()

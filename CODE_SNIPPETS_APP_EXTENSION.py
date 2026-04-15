# ==============================================================================
# BACKEND: app_extension.py - Event Manual Entry + Live Logs
# ==============================================================================
# Copy these two endpoints to your app_extension.py file

# ENDPOINT 1: Manual Event Entry (Line 545+)
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

        # 4. Retrieve attendance with pre-formatted times
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
        
        # Generate initials from employee name
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


# ENDPOINT 2: Get Event Logs for Live Feed (Line 803+)
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
            
            # Remove leading zero
            if time_str.startswith('0'):
                time_str = time_str[1:]

            result.append({
                "initials": initials,
                "name": name,
                "dept": row['department'],
                "time": time_str,
                "log_type": row['log_type'],
                "type": "success" if row['log_type'] == 'Entry' else "secondary"
            })

        return jsonify({"success": True, "logs": result}), 200

    except Exception as e:
        print(f"Error in get_instance_logs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)

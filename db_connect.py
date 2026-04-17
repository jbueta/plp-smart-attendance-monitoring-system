import mysql.connector as connector
from datetime import date, datetime, timedelta

class Database:
    
    def __init__(self, conn, parameter):
        self.conn = conn
        self.parameter = parameter

        if self.conn:
            self.cursor = self.conn.cursor(dictionary=True)
        else:
            raise Exception("Failed to connect to the database.")
        

    #============================================================
    # ADMIN LOGIN AUTHENTICATION
    # =============================================================
    def admin_login(self):
        try:
            query = """ SELECT * FROM admin WHERE username = %s AND password = %s LIMIT 1 """
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchone()
            return result if result else []

        except connector.Error as err:
            print(f"Error: {err}")
            return None
    
    # =============================================================
    # GENERAL ENTRY/EXIT MODEL LOGIC
    # =============================================================

    def authenticate_user(self):
        try:
            query = """ 
                SELECT u.user_id, u.role, u.active,
                    COALESCE(s.student_id, e.employee_id, CAST(v.visitor_id AS CHAR)) as scan_id,
                    COALESCE(s.status, e.status, v.status) as current_status,
                    COALESCE(s.student_name, e.employee_name, v.visitor_name) as full_name,
                    COALESCE(c.course_name, d.department_name, 'Visitor') as affiliation
                FROM users u 
                LEFT JOIN students s ON u.user_id = s.user_id 
                LEFT JOIN employees e ON u.user_id = e.user_id
                LEFT JOIN visitors v ON u.user_id = v.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                WHERE s.student_id = %s OR e.employee_id = %s OR v.visitor_id = %s
            """
            print(self.parameter)
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchall()
            return result if result else []
            
        except connector.Error as err:
            print(f"Error authenticating: {err}")
            return err

    def change_status(self):
        try:
            user_id = self.parameter[0]
            current_status = self.parameter[1]
            role = self.parameter[2]

            # check user last scanned
            last_log_query = """
                SELECT timestamp, log_type 
                FROM general_log 
                WHERE user_id = %s 
                ORDER BY timestamp DESC LIMIT 1
            """
            self.cursor.execute(last_log_query, (user_id,))
            last_log = self.cursor.fetchone()

            new_status = 'Inside'
            now = datetime.now()
            today_date = now.date()
            forgot_to_timeout = False

            if last_log:
                last_time = last_log['timestamp']
                last_type = last_log['log_type']
                last_date = last_time.date()

                if current_status.lower() == 'inside':
                    if last_date < today_date:
                        forgot_to_timeout = True
                        new_status = 'Inside'
                    else:
                        new_status = 'Outside'
                else:
                    new_status = 'Inside'
            else:
                 new_status = 'Inside'

            if role == 'student':
                query = "UPDATE students SET status = %s WHERE user_id = %s"
            elif role == 'employee':
                query = "UPDATE employees SET status = %s WHERE user_id = %s"
            else:
                query = "UPDATE visitors SET status = %s WHERE user_id = %s" 

            self.cursor.execute(query, (new_status, user_id))
            self.conn.commit()
            
            return {
                'status': new_status,
                'new_status': new_status,
                'forgot_to_timeout': forgot_to_timeout
            }
            
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error changing status: {err}")
            return None

    def insert_general_log(self):
        try:
            insert_log_query = """INSERT INTO general_log (user_id, timestamp, log_type, gate) VALUES (%s, %s, %s, %s)"""
            self.cursor.execute(insert_log_query, self.parameter)
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                return "Log inserted successfully!"
            return None 
            
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error inserting log: {err}")
            return None

    def retrieve_log(self):
        try:
            log_query = """SELECT * FROM general_log WHERE user_id = %s AND DATE(timestamp) = %s"""
            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()
            return result if result else []
            
        except connector.Error as err:
            print(f"Error retrieving log: {err}")
            return None


    def add_user(self):
        try:
            query = """INSERT INTO users (user_name, user_type) VALUES (%s, %s)"""

            self.cursor.execute(query, self.parameter)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:   
                last_id = int(self.cursor.lastrowid)
                match self.parameter[1]:
                    case 'employee':
                        new_query = "INSERT INTO employees (user_id, department, position, gender, age) VALUES (%s, %s, %s, %s, %s)"
                        params = (last_id, self.parameter.metadata['Department'], self.parameter.metadata['Position'], self.parameter.metadata['Gender'], self.parameter.metadata['Age'])
                        self.cursor.execute(new_query, params)
                    case 'student':
                        new_query = "INSERT INTO students (user_id, student_no, course) VALUES (%s, %s, %s)"
                        params = (last_id, self.parameter.metadata['student_no'], self.parameter.metadata['course'])
                        self.cursor.execute(new_query, params)
                    case 'visitor':
                        new_query = "INSERT INTO visitors (user_id, purpose) VALUES (%s, %s)"
                        params = (last_id, self.parameter.metadata['purpose'])
                        self.cursor.execute(new_query, params)
                match self.parameter[1]:
                    case 'employee':
                        new_query = "INSERT INTO employees (user_id, department, position, gender, age) VALUES (%s, %s, %s, %s, %s)"
                        params = (last_id, self.parameter.metadata['Department'], self.parameter.metadata['Position'], self.parameter.metadata['Gender'], self.parameter.metadata['Age'])
                        self.cursor.execute(new_query, params)
                    case 'student':
                        new_query = "INSERT INTO students (user_id, student_no, course) VALUES (%s, %s, %s)"
                        params = (last_id, self.parameter.metadata['student_no'], self.parameter.metadata['course'])
                        self.cursor.execute(new_query, params)
                    case 'visitor':
                        new_query = "INSERT INTO visitors (user_id, purpose) VALUES (%s, %s)"
                        params = (last_id, self.parameter.metadata['purpose'])
                        self.cursor.execute(new_query, params)
            self.conn.commit()
            return "User added successfully!"
        except connector.Error as err:
            self.conn.rollback()
            self.conn.rollback()
            print(f"Error: {err}")
            return None

    def delete_user(self):
        query = """DELETE FROM users WHERE user_id = %s"""
        try:
            self.cursor.execute(query, self.parameter)
            self.conn.commit()
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                return "User deleted successfully!"
            else:
                return None  # User did not exist
        
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error: {err}")
            return None


    # =============================================================
    # EVENTS MODEL LOGIC
    # =============================================================

    def add_event(self):
        try:
            if self.parameter[2] == 'WEEKLY':
                query = """INSERT IGNORE INTO events 
                           (event_name, event_type, frequency, day, event_date,
                            time_start, time_end, location, active) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[2], self.parameter[3], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], 1)

            else:
                query = """INSERT IGNORE INTO events 
                           (event_name, event_type, frequency, event_date, time_start, time_end, location, active) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[2], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], 1)

            self.cursor.execute(query, params)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                print("Event created!")

                event_id = int(self.cursor.lastrowid)

                match (self.parameter[9]):
                    case 'grouped':
                        departments = self.parameter[8]
                        
                        if departments and isinstance(departments, list):
                            print(f"Retrieving user_ids for {len(departments)} departments...")

                            format_strings = ','.join(['%s'] * len(departments))

                            get_users_query = f"""
                                SELECT user_id 
                                FROM employees 
                                WHERE department_id IN ({format_strings})
                            """

                            self.cursor.execute(get_users_query, tuple(departments))
                            fetched_users = self.cursor.fetchall()

                            print(fetched_users)
                            actual_user_ids = [row['user_id'] if isinstance(row, dict) else row[0] for row in fetched_users]

                            if actual_user_ids:
                                new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                                participant_data = [(event_id, uid) for uid in actual_user_ids]
                                self.cursor.executemany(new_query, participant_data)
                                print(f"Successfully attached {len(actual_user_ids)} valid participants from grouped departments!")
                            else:
                                print("Warning: No employees found in the provided departments.")
                    case 'custom':
                        raw_ids = self.parameter[8]
                        if raw_ids and isinstance(raw_ids, list):
                            print(f"Translating {len(raw_ids)} raw IDs to user_ids...")

                            format_strings = ','.join(['%s'] * len(raw_ids))

                            get_users_query = f"""
                                SELECT u.user_id 
                                FROM users u
                                LEFT JOIN students s ON u.user_id = s.user_id
                                LEFT JOIN employees e ON u.user_id = e.user_id
                                LEFT JOIN visitors v ON u.user_id = v.user_id
                                WHERE s.student_id IN ({format_strings})
                                OR e.employee_id IN ({format_strings})
                                OR v.visitor_id IN ({format_strings})
                            """

                            query_params = tuple(raw_ids + raw_ids + raw_ids)

                            self.cursor.execute(get_users_query, query_params)
                            fetched_users = self.cursor.fetchall()

                            actual_user_ids = [row['user_id'] if isinstance(row, dict) else row[0] for row in fetched_users]

                            if actual_user_ids:
                                new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                                participant_data = [(event_id, uid) for uid in actual_user_ids]
                                self.cursor.executemany(new_query, participant_data)
                                print(f"Successfully attached {len(actual_user_ids)} valid participants!")
                            else:
                                print("Warning: None of the provided IDs matched any users in the database.")

                    case 'hybrid':
                        hybrid_data = self.parameter[8]
                        
                        grouped_deps = hybrid_data.get('grouped_participants', [])
                        custom_raw_ids = hybrid_data.get('custom_participants', [])
                        
                        final_user_ids = set()

                        # 2. PROCESS GROUPED DEPARTMENTS
                        if grouped_deps:
                            print(f"Fetching users for {len(grouped_deps)} departments...")
                            format_strings = ','.join(['%s'] * len(grouped_deps))
                            get_dept_query = f"""
                                SELECT user_id FROM employees WHERE department_id IN ({format_strings})
                            """
                            self.cursor.execute(get_dept_query, tuple(grouped_deps))
                            dept_users = self.cursor.fetchall()
                            
                            # Add it to set
                            for row in dept_users:
                                final_user_ids.add(row['user_id'] if isinstance(row, dict) else row[0])

                        # 3. PROCESS CUSTOM IDS
                        if custom_raw_ids:
                            print(f"Fetching users for {len(custom_raw_ids)} custom IDs...")
                            format_strings = ','.join(['%s'] * len(custom_raw_ids))
                            get_custom_query = f"""
                                SELECT u.user_id FROM users u
                                LEFT JOIN students s ON u.user_id = s.user_id
                                LEFT JOIN employees e ON u.user_id = e.user_id
                                LEFT JOIN visitors v ON u.user_id = v.user_id
                                WHERE s.student_id IN ({format_strings})
                                OR e.employee_id IN ({format_strings})
                                OR v.visitor_id IN ({format_strings})
                            """
                            self.cursor.execute(get_custom_query, tuple(custom_raw_ids + custom_raw_ids + custom_raw_ids))
                            custom_users = self.cursor.fetchall()
                            
                            # Add it to set
                            for row in custom_users:
                                final_user_ids.add(row['user_id'] if isinstance(row, dict) else row[0])

                        # 4. INSERT EVERYONE AT ONCE
                        if final_user_ids:
                            new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                            participant_data = [(event_id, uid) for uid in final_user_ids]
                            self.cursor.executemany(new_query, participant_data)
                            print(f"Successfully attached {len(final_user_ids)} unique hybrid participants!")
                        else:
                            print("Warning: No valid participants found in either hybrid list.")

                print ("Participants attached successfully!")

                # ==========================================
                # ONCE TIME EVENT INSTANCE GENERATOR
                # ==========================================
                frequency = self.parameter[2]
                start_date = self.parameter[4]

                if frequency not in ['WEEKLY', 'DAILY', 'MONTHLY', 'YEARLY']: 
                    instance_query = """ INSERT IGNORE INTO event_instances (event_id, event_date, status) 
                                         VALUES (%s, %s, 'Scheduled') """
                    self.cursor.execute(instance_query, (event_id, start_date))
                    instance_id = int(self.cursor.lastrowid)

                    attendance_query = """ INSERT IGNORE INTO event_attendance (instance_id, user_id, event_date, status) 
                                           SELECT %s, user_id, %s, 'Absent' FROM event_participants WHERE event_id = %s """
                    self.cursor.execute(attendance_query, (instance_id, start_date, event_id))
                    
                    self.conn.commit()
                    print(f"One-time instance and roster generated for {start_date}!")

                self.conn.commit()
                return {"message": "Event created successfully!", "success": True}
            else:
                return {"success": False, "message": "Event already exists or could not be created."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error: {err}")
            return {"success": False, "message": f"Database crash: {err}"}

    def check_event_logs(self):
        
        try:
            log_query = """SELECT * FROM event_log WHERE user_id = %s AND DATE(timestamp) = %s"""

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None

    def check_events(self):
            try:
                query = """ SELECT event_id, event_date FROM events 
                            WHERE active = 1 
                            AND (
                                (frequency = 'WEEKLY' AND day = %s) 
                                OR frequency = 'DAILY'
                            )"""
                self.cursor.execute(query, self.parameter)
                result = self.cursor.fetchall()

                return result if result else []
                
            except connector.Error as err:
                print(f"Error: {err}")
                return None

    def add_event_instances(self):
        try:
            query = """ INSERT IGNORE INTO event_instances (event_id, event_date, status) 
                        VALUES (%s, %s, 'Scheduled') """

            self.cursor.execute(query, self.parameter)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:   
                instance_id = int(self.cursor.lastrowid)

                new_query = """ INSERT IGNORE INTO event_attendance (instance_id, user_id, event_date, status) 
                                SELECT %s, user_id, %s, 'Absent' FROM event_participants WHERE event_id = %s """
                params = (instance_id, self.parameter[1], self.parameter[0])
                self.cursor.execute(new_query, params)
                
                self.conn.commit()
            return {"message": "Event weekly instances added successfully!", "success": True}
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Error: {err}", "success": False}

    def check_last_swipe(self):
        try:
            query = """ SELECT log_type FROM event_log WHERE user_id = %s AND event_id = %s 
                        AND DATE(timestamp) = CURRENT_DATE() ORDER BY timestamp DESC LIMIT 1
                    """
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchone()
            return result if result else None
        except connector.Error as err:
            return {"message": f"Error: {err}", "success": False}


    def events_authentication(self):
        try:
            query = """ INSERT INTO event_log (user_id, event_id, log_type) 
                        VALUES (%s, %s, %s) """
            self.cursor.execute(query, self.parameter)

            log_type = self.parameter[2]
            
            if log_type.lower() == 'entry':
                log_query = """ UPDATE event_attendance 
                                JOIN event_instances ON event_attendance.instance_id = event_instances.instance_id
                                JOIN events ON event_instances.event_id = events.event_id
                                SET 
                                    event_attendance.status = IF(CURRENT_TIME() > ADDTIME(events.time_start, '00:15:00'), 'Late', 'Present'), 
                                    event_attendance.first_in = NOW()
                                WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE() 
                                AND event_attendance.status IN ('Absent', 'Excused')
                            """
            elif log_type.lower() == 'exit':
                log_query = """ UPDATE event_attendance JOIN event_instances ON event_attendance.instance_id = event_instances.instance_id
                                SET event_attendance.last_out = NOW() WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE()
                            """
            else:
                return {"message": "Invalid log type.", "success": False}

            params = (self.parameter[0], self.parameter[1])
            self.cursor.execute(log_query, params)
            self.conn.commit()

            return {"message": "Event logging successfully!", "success": True}
            
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Error: {err}", "success": False}

    def update_attendance_status(self):
        try:
            query = """ UPDATE event_attendance 
                        SET status = %s, remarks = %s 
                        WHERE user_id = %s AND instance_id = %s """
            
            self.cursor.execute(query, self.parameter)
            
            if self.cursor.rowcount == 0:
                return {"success": False, "message": "No matching attendance record found."}
                
            self.conn.commit()
            return {"success": True, "message": "Status updated successfully!"}
            
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def update_instance_status(self):
        """
        Updates the status of a specific event instance (e.g., to 'Completed' or 'Cancelled').
        Expected new_status values: 'Scheduled', 'Completed', 'Cancelled'
        """
        try:
            new_status = self.parameter[0]
            instance_id = self.parameter[1]
            
            query = "UPDATE event_instances SET status = %s WHERE instance_id = %s"
            self.cursor.execute(query, (new_status, instance_id))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                return {"message": f"Event instance successfully marked as {new_status}!", "success": True}
            else:
                return {"message": "No event found with that ID, or status was already set.", "success": False}
                
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Database Error: {err}", "success": False}

    def delete_event(self):
        """
        Soft deletion of events to prevent data loss if needed
        """
        try: 
            query = "UPDATE events SET active = 0 WHERE event_id = %s"
            self.cursor.execute(query, self.parameter)
            self.conn.commit()
            return {"message": "Event deleted successfully!", "success": True}
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Database Error: {err}", "success": False}

    def delete_bulk_events(self):
        """
        Soft deletion of events to prevent data loss if needed
        """
        try: 
            query = "UPDATE events SET active = 0 WHERE event_id = %s"
            self.cursor.execute(query, self.parameter)
            self.conn.commit()
            return {"message": "Event deleted successfully!", "success": True}
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Database Error: {err}", "success": False}

    # =============================================================
    # GET (READ) METHODS
    # =============================================================

    def get_all_events(self):
        try:
            query = """ SELECT * FROM events ORDER BY event_id DESC WHERE active = 1 """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            cleaned_events = []
            for row in result:
                if isinstance(row, dict):
                    for key, val in row.items():
                        if isinstance(val, (timedelta, date, datetime)):
                            row[key] = str(val)
                    cleaned_events.append(row)
                else:
                    cleaned_row = tuple(
                        str(val) if isinstance(val, (timedelta, date, datetime)) else val 
                        for val in row
                    )
                    cleaned_events.append(cleaned_row)

            return cleaned_events
            
        except connector.Error as err:
            print(f"Error fetching events: {err}")
            return []


    # =============================================================
    # EVENTS MODEL LOGIC
    # =============================================================

    def add_event(self):
        try:
            if self.parameter[2] == 'WEEKLY':
                query = """INSERT IGNORE INTO events 
                           (event_name, event_type, frequency, day, event_date,
                            time_start, time_end, location, active) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[2], self.parameter[3], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], 1)

            else:
                query = """INSERT IGNORE INTO events 
                           (event_name, event_type, frequency, event_date, time_start, time_end, location, active) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[2], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], 1)

            self.cursor.execute(query, params)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                print("Event created!")

                event_id = int(self.cursor.lastrowid)

                match (self.parameter[9]):
                    case 'grouped':
                        departments = self.parameter[8]
                        
                        if departments and isinstance(departments, list):
                            print(f"Retrieving user_ids for {len(departments)} departments...")

                            format_strings = ','.join(['%s'] * len(departments))

                            get_users_query = f"""
                                SELECT user_id 
                                FROM employees 
                                WHERE department_id IN ({format_strings})
                            """

                            self.cursor.execute(get_users_query, tuple(departments))
                            fetched_users = self.cursor.fetchall()

                            print(fetched_users)
                            actual_user_ids = [row['user_id'] if isinstance(row, dict) else row[0] for row in fetched_users]

                            if actual_user_ids:
                                new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                                participant_data = [(event_id, uid) for uid in actual_user_ids]
                                self.cursor.executemany(new_query, participant_data)
                                print(f"Successfully attached {len(actual_user_ids)} valid participants from grouped departments!")
                            else:
                                print("Warning: No employees found in the provided departments.")
                    case 'custom':
                        raw_ids = self.parameter[8]
                        if raw_ids and isinstance(raw_ids, list):
                            print(f"Translating {len(raw_ids)} raw IDs to user_ids...")

                            format_strings = ','.join(['%s'] * len(raw_ids))

                            get_users_query = f"""
                                SELECT u.user_id 
                                FROM users u
                                LEFT JOIN students s ON u.user_id = s.user_id
                                LEFT JOIN employees e ON u.user_id = e.user_id
                                LEFT JOIN visitors v ON u.user_id = v.user_id
                                WHERE s.student_id IN ({format_strings})
                                OR e.employee_id IN ({format_strings})
                                OR v.visitor_id IN ({format_strings})
                            """

                            query_params = tuple(raw_ids + raw_ids + raw_ids)

                            self.cursor.execute(get_users_query, query_params)
                            fetched_users = self.cursor.fetchall()

                            actual_user_ids = [row['user_id'] if isinstance(row, dict) else row[0] for row in fetched_users]

                            if actual_user_ids:
                                new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                                participant_data = [(event_id, uid) for uid in actual_user_ids]
                                self.cursor.executemany(new_query, participant_data)
                                print(f"Successfully attached {len(actual_user_ids)} valid participants!")
                            else:
                                print("Warning: None of the provided IDs matched any users in the database.")

                    case 'hybrid':
                        hybrid_data = self.parameter[8]
                        
                        grouped_deps = hybrid_data.get('grouped_participants', [])
                        custom_raw_ids = hybrid_data.get('custom_participants', [])
                        
                        final_user_ids = set()

                        # 2. PROCESS GROUPED DEPARTMENTS
                        if grouped_deps:
                            print(f"Fetching users for {len(grouped_deps)} departments...")
                            format_strings = ','.join(['%s'] * len(grouped_deps))
                            get_dept_query = f"""
                                SELECT user_id FROM employees WHERE department_id IN ({format_strings})
                            """
                            self.cursor.execute(get_dept_query, tuple(grouped_deps))
                            dept_users = self.cursor.fetchall()
                            
                            # Add it to set
                            for row in dept_users:
                                final_user_ids.add(row['user_id'] if isinstance(row, dict) else row[0])

                        # 3. PROCESS CUSTOM IDS
                        if custom_raw_ids:
                            print(f"Fetching users for {len(custom_raw_ids)} custom IDs...")
                            format_strings = ','.join(['%s'] * len(custom_raw_ids))
                            get_custom_query = f"""
                                SELECT u.user_id FROM users u
                                LEFT JOIN students s ON u.user_id = s.user_id
                                LEFT JOIN employees e ON u.user_id = e.user_id
                                LEFT JOIN visitors v ON u.user_id = v.user_id
                                WHERE s.student_id IN ({format_strings})
                                OR e.employee_id IN ({format_strings})
                                OR v.visitor_id IN ({format_strings})
                            """
                            self.cursor.execute(get_custom_query, tuple(custom_raw_ids + custom_raw_ids + custom_raw_ids))
                            custom_users = self.cursor.fetchall()
                            
                            # Add it to set
                            for row in custom_users:
                                final_user_ids.add(row['user_id'] if isinstance(row, dict) else row[0])

                        # 4. INSERT EVERYONE AT ONCE
                        if final_user_ids:
                            new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                            participant_data = [(event_id, uid) for uid in final_user_ids]
                            self.cursor.executemany(new_query, participant_data)
                            print(f"Successfully attached {len(final_user_ids)} unique hybrid participants!")
                        else:
                            print("Warning: No valid participants found in either hybrid list.")

                print ("Participants attached successfully!")

                # ==========================================
                # ONCE TIME EVENT INSTANCE GENERATOR
                # ==========================================
                frequency = self.parameter[2]
                start_date = self.parameter[4]

                if frequency not in ['WEEKLY', 'DAILY', 'MONTHLY', 'YEARLY']: 
                    instance_query = """ INSERT IGNORE INTO event_instances (event_id, event_date, status) 
                                         VALUES (%s, %s, 'Scheduled') """
                    self.cursor.execute(instance_query, (event_id, start_date))
                    instance_id = int(self.cursor.lastrowid)

                    attendance_query = """ INSERT IGNORE INTO event_attendance (instance_id, user_id, event_date, status) 
                                           SELECT %s, user_id, %s, 'Absent' FROM event_participants WHERE event_id = %s """
                    self.cursor.execute(attendance_query, (instance_id, start_date, event_id))
                    
                    self.conn.commit()
                    print(f"One-time instance and roster generated for {start_date}!")

                self.conn.commit()
                return {"message": "Event created successfully!", "success": True}
            else:
                return {"success": False, "message": "Event already exists or could not be created."}
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error: {err}")
            return {"success": False, "message": f"Database crash: {err}"}

    def check_event_logs(self):
        
        try:
            log_query = """SELECT * FROM event_log WHERE user_id = %s AND DATE(timestamp) = %s"""

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None

    def check_events(self):
            try:
                query = """ SELECT event_id, event_date FROM events 
                            WHERE active = 1 
                            AND (
                                (frequency = 'WEEKLY' AND day = %s) 
                                OR frequency = 'DAILY'
                            )"""
                self.cursor.execute(query, self.parameter)
                result = self.cursor.fetchall()

                return result if result else []
                
            except connector.Error as err:
                print(f"Error: {err}")
                return None

    def add_event_instances(self):
        try:
            query = """ INSERT IGNORE INTO event_instances (event_id, event_date, status) 
                        VALUES (%s, %s, 'Scheduled') """

            self.cursor.execute(query, self.parameter)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:   
                instance_id = int(self.cursor.lastrowid)

                new_query = """ INSERT IGNORE INTO event_attendance (instance_id, user_id, event_date, status) 
                                SELECT %s, user_id, %s, 'Absent' FROM event_participants WHERE event_id = %s """
                params = (instance_id, self.parameter[1], self.parameter[0])
                self.cursor.execute(new_query, params)
                
                self.conn.commit()
            return {"message": "Event weekly instances added successfully!", "success": True}
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Error: {err}", "success": False}

    def check_last_swipe(self):
        try:
            query = """ SELECT log_type FROM event_log WHERE user_id = %s AND event_id = %s 
                        AND DATE(timestamp) = CURRENT_DATE() ORDER BY timestamp DESC LIMIT 1
                    """
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchone()
            return result if result else None
        except connector.Error as err:
            return {"message": f"Error: {err}", "success": False}


    def events_authentication(self):
        try:
            query = """ INSERT INTO event_log (user_id, event_id, log_type) 
                        VALUES (%s, %s, %s) """
            self.cursor.execute(query, self.parameter)

            log_type = self.parameter[2]
            
            if log_type.lower() == 'entry':
                log_query = """ UPDATE event_attendance 
                                JOIN event_instances ON event_attendance.instance_id = event_instances.instance_id
                                JOIN events ON event_instances.event_id = events.event_id
                                SET 
                                    event_attendance.status = IF(CURRENT_TIME() > ADDTIME(events.time_start, '00:15:00'), 'Late', 'Present'), 
                                    event_attendance.first_in = NOW()
                                WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE() 
                                AND event_attendance.status IN ('Absent', 'Excused')
                            """
            elif log_type.lower() == 'exit':
                log_query = """ UPDATE event_attendance JOIN event_instances ON event_attendance.instance_id = event_instances.instance_id
                                SET event_attendance.last_out = NOW() WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE()
                            """
            else:
                return {"message": "Invalid log type.", "success": False}

            params = (self.parameter[0], self.parameter[1])
            self.cursor.execute(log_query, params)
            self.conn.commit()

            return {"message": "Event logging successfully!", "success": True}
            
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Error: {err}", "success": False}

    def update_attendance_status(self):
        try:
            query = """ UPDATE event_attendance 
                        SET status = %s, remarks = %s 
                        WHERE user_id = %s AND instance_id = %s """
            
            self.cursor.execute(query, self.parameter)
            
            if self.cursor.rowcount == 0:
                return {"success": False, "message": "No matching attendance record found."}
                
            self.conn.commit()
            return {"success": True, "message": "Status updated successfully!"}
            
        except connector.Error as err:
            self.conn.rollback()
            return {"success": False, "message": f"Database Error: {err}"}

    def update_instance_status(self):
        """
        Updates the status of a specific event instance (e.g., to 'Completed' or 'Cancelled').
        Expected new_status values: 'Scheduled', 'Completed', 'Cancelled'
        """
        try:
            new_status = self.parameter[0]
            instance_id = self.parameter[1]
            
            query = "UPDATE event_instances SET status = %s WHERE instance_id = %s"
            self.cursor.execute(query, (new_status, instance_id))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                return {"message": f"Event instance successfully marked as {new_status}!", "success": True}
            else:
                return {"message": "No event found with that ID, or status was already set.", "success": False}
                
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Database Error: {err}", "success": False}

    # ==============================================================================
    # STATIC GETTER METHODS
    # ==============================================================================

    @staticmethod
    def get_events_dashboard(conn):
        try:
            if conn:
                cursor = conn.cursor(dictionary=True)
            else:
                raise Exception("Failed to connect to the database.")
            
            query = """
                SELECT 
                    e.event_id AS event_id, 
                    e.event_name AS name, 
                    e.event_type AS type, 
                    e.frequency AS frequency,
                    DATE_FORMAT(e.event_date, '%b %e, %Y') AS date,
                    TRIM(DATE_FORMAT(e.time_start, '%l:%i %p')) AS time_start, 
                    TRIM(DATE_FORMAT(e.time_end, '%l:%i %p')) AS time_end, 
                    e.location AS location,
                    GROUP_CONCAT(DISTINCT d.department_name SEPARATOR ', ') AS dept,
                    (COUNT(DISTINCT d.department_id) = (SELECT COUNT(*) FROM departments)) AS all_departments
                FROM event_participants ep
                JOIN events e ON ep.event_id = e.event_id
                JOIN employees emp ON ep.user_id = emp.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE e.active = 1
                GROUP BY e.event_id
                ORDER BY e.event_date DESC;
            """

            cursor.execute(query)
            result = cursor.fetchall()
            
            if result:
                for row in result:
                    row['all_departments'] = bool(row['all_departments'])
            
            print(result)
            return result if result else []
            
        except Exception as err: 
            print(f"Error fetching events: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()


    @staticmethod
    def get_events_kiosk(conn):
        try:
            if conn:
                cursor = conn.cursor(dictionary=True)
            else:
                raise Exception("Failed to connect to the database.")
            query = """
                        SELECT 
                            ei.instance_id AS instance_id,
                            e.event_id AS event_id,
                            e.event_name AS name, 
                            e.event_type AS type, 
                            e.frequency AS frequency,
                            ei.event_date AS date, 
                            e.time_start, 
                            e.time_end, 
                            e.location AS location
                        FROM event_instances ei
                        JOIN events e ON ei.event_id = e.event_id
                        WHERE ei.event_date = CURDATE() 
                        AND ei.status = 'Scheduled'
                        AND e.active = 1
                    """
            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                for row in result:
                    if row.get('date'):
                        row['date'] = str(row['date'])
                    if row.get('time_start'):
                        row['time_start'] = str(row['time_start'])
                    if row.get('time_end'):
                        row['time_end'] = str(row['time_end'])
                        
            return result if result else []
            
        except connector.Error as err:
            print(f"Error fetching events: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def get_all_events_for_reports(conn):
        """
        Fetches all scheduled event instances for reports dropdown.
        Used in the Reports tab detailed report type selection.
        """
        try:
            if conn:
                cursor = conn.cursor(dictionary=True)
            else:
                raise Exception("Failed to connect to the database.")
            query = """
                        SELECT DISTINCT
                            ei.instance_id AS instance_id,
                            e.event_id AS event_id,
                            e.event_name AS name, 
                            e.event_type AS type, 
                            e.frequency AS frequency,
                            ei.event_date AS date, 
                            e.time_start, 
                            e.time_end, 
                            e.location AS location,
                            e.active AS active
                        FROM event_instances ei
                        JOIN events e ON ei.event_id = e.event_id
                        WHERE ei.status = 'Scheduled'
                        ORDER BY ei.event_date DESC
                    """
            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                for row in result:
                    if row.get('date'):
                        row['date'] = str(row['date'])
                    if row.get('time_start'):
                        row['time_start'] = str(row['time_start'])
                    if row.get('time_end'):
                        row['time_end'] = str(row['time_end'])
                        
            return result if result else []
            
        except connector.Error as err:
            print(f"Error fetching events for reports: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def get_admin_departments(conn):
        try:
            cursor = conn.cursor(dictionary=True)
            query = """ 
                SELECT 
                    d.department_id AS dept_id, 
                    d.department_name AS dept_name
                FROM departments d
            """
            cursor.execute(query)
            result = cursor.fetchall()
            
            return result if result else []
            
        except connector.Error as err:
            print(f"Error fetching attendance: {err}")
            return [] 
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def get_student_logs(conn, limit=6):
        try:
            if conn:
                cursor = conn.cursor(dictionary=True)
            else:
                raise Exception("Failed to connect to the database.")

            query = """
                SELECT 
                    gl.log_type, 
                    s.student_name, 
                    c.course_name, 
                    gl.timestamp
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                JOIN students s ON u.user_id = s.user_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                ORDER BY gl.timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            result = cursor.fetchall()

            formatted_logs = []

            if result:
                for row in result:
                    mapped_type = "in" if row['log_type'] == "Entry" else "out"
                    
                    formatted_time = ""
                    if row.get('timestamp'):
                        if isinstance(row['timestamp'], datetime):
                            formatted_time = row['timestamp'].strftime('%I:%M %p')
                        else:
                            dt_obj = datetime.strptime(str(row['timestamp']), '%Y-%m-%d %H:%M:%S')
                            formatted_time = dt_obj.strftime('%I:%M %p')

                    formatted_logs.append({
                        "type": mapped_type,
                        "name": row.get('student_name', 'Unknown User'),
                        "course": row.get('course_name', 'N/A'),
                        "time": formatted_time
                    })

            return formatted_logs
        except connector.Error as err:
            print(f"Error fetching recent student logs: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def get_event_instances(conn, event_id):
        try:
            cursor = conn.cursor(dictionary=True)
            query = """ 
                SELECT 
                    instance_id,
                    DATE_FORMAT(event_date, '%b %e, %Y') AS event_date, 
                    status 
                FROM event_instances 
                WHERE event_id = %s 
                ORDER BY event_date ASC 
            """
            cursor.execute(query, (event_id,))
            result = cursor.fetchall()
            
            cleaned_instances = []
            for row in result:
                for key, val in row.items():
                    if isinstance(val, (timedelta, date, datetime)):
                        row[key] = str(val)
                cleaned_instances.append(row)

            return cleaned_instances
            
        except connector.Error as err:
            print(f"Error fetching event instances: {err}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def get_instance_attendance(conn, instance_id):
        try:
            cursor = conn.cursor(dictionary=True)
            query = """ 
                SELECT 
                    ea.attendance_id, ea.user_id, ea.status, 
                    LOWER(TRIM(DATE_FORMAT(ea.first_in, '%l:%i %p'))) AS first_in,
                    LOWER(TRIM(DATE_FORMAT(ea.last_out, '%l:%i %p'))) AS last_out,
                    ea.remarks, 
                    COALESCE(s.student_name, e.employee_name, v.visitor_name) AS user_name,
                    COALESCE(d.department_name, 'N/A') AS department
                FROM event_attendance ea
                LEFT JOIN users u ON ea.user_id = u.user_id
                LEFT JOIN visitors v ON u.user_id = v.user_id
                LEFT JOIN students s ON u.user_id = s.user_id
                LEFT JOIN employees e ON u.user_id = e.user_id
                LEFT JOIN departments d ON (e.department_id = d.department_id)
                WHERE ea.instance_id = %s
                ORDER BY user_name ASC
            """
            cursor.execute(query, (instance_id,))
            result = cursor.fetchall()
            
            cleaned_attendance = []
            for row in result:
                cleaned_attendance.append(row)

            return cleaned_attendance
            
        except connector.Error as err:
            print(f"Error fetching attendance: {err}")
            return [] 
        finally:
            if 'cursor' in locals():
                cursor.close()

    @staticmethod
    def generate_report(conn,):
        try:
            cursor = conn.cursor(dictionary=True)
            if category == 'event':
                query = """
                    SELECT 
                        e.employee_name, 
                        d.department_name, 
                        LOWER(TRIM(DATE_FORMAT(ea.first_in, '%l:%i %p'))) AS time_in, 
                        ea.status, 
                        ea.remarks
                    FROM event_attendance ea
                    JOIN event_instances ei ON ea.instance_id = ei.instance_id
                    JOIN users u ON ea.user_id = u.user_id
                    JOIN employees e ON u.user_id = e.user_id
                    JOIN departments d ON e.department_id = d.department_id
                    WHERE ei.event_date BETWEEN %s AND %s
                    ORDER BY ea.first_in ASC
                """
            cursor.execute(query, (start_date, end_date))
            result = cursor.fetchall()
            
            cleaned_attendance = []
            for row in result:
                for key, val in row.items():
                    if isinstance(val, (timedelta, date, datetime)):
                        if isinstance(val, timedelta):
                            total_seconds = int(val.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            row[key] = f"{hours:02d}:{minutes:02d}"
                        else:
                            row[key] = str(val)
                cleaned_attendance.append(row)

            return cleaned_attendance
            
        except connector.Error as err:
            print(f"Error fetching attendance: {err}")
            return [] 
        finally:
            if 'cursor' in locals():
                cursor.close()


    # =============================================================
    # REPORTS GENERATION LOGIC
    # =============================================================

    @staticmethod
    def get_report_queries(conn, category, report_type, department_filter, start_date, end_date):
        """Fetches raw report data based on the category with optional department filtering."""
        cursor = conn.cursor(dictionary=True) 
        
        # Normalize category values from form
        category_map = {
            'general': 'General Logs',
            'visitor': 'Visitor Logs',
            'event': 'Event Attendance',
            'violation': 'Violations'
        }
        normalized_category = category_map.get(category.lower(), category)
        
        # Default values
        report_title = "System Report"
        event_name_display = "Campus Activity"
        col_headers = ["Name", "Detail", "Time", "Status", "Remarks"]
        raw_logs = []
        total_expected = 0
        total_present = 0

        try:
            # Build department filter condition
            dept_condition = ""
            dept_params = []
            
            if department_filter and department_filter.lower() != 'all':
                dept_condition = "AND d.department_id = %s"
                dept_params = [department_filter]
            
            match normalized_category: 
                case 'Event Attendance':
                    report_title = "Event Attendance Report"
                    col_headers = ["Participant Name", "Role / Affiliation", "Time In", "Time Out", "Status", "Remarks"]
                    
                    cursor.execute("SELECT event_name FROM events WHERE event_id = %s", (report_type,))
                    event_info = cursor.fetchone()
                    if event_info:
                        event_name_display = event_info['event_name']
                    
                    query = f"""
                        SELECT 
                            COALESCE(e.employee_name, s.student_name, v.visitor_name, a.username, 'Unknown User') AS name,
                            CONCAT(UPPER(u.role), ' - ', COALESCE(d.department_name, c.course_name, v.purpose, 'N/A')) AS detail,
                            LOWER(TRIM(DATE_FORMAT(ea.first_in, '%l:%i %p'))) AS time_in,
                            LOWER(TRIM(DATE_FORMAT(ea.last_out, '%l:%i %p'))) AS time_out,
                            ea.status AS status,
                            COALESCE(ea.remarks, 'N/A') AS remarks
                        FROM event_attendance ea
                        JOIN event_instances ei ON ea.instance_id = ei.instance_id
                        JOIN users u ON ea.user_id = u.user_id
                        LEFT JOIN employees e ON u.user_id = e.user_id
                        LEFT JOIN departments d ON e.department_id = d.department_id
                        LEFT JOIN students s ON u.user_id = s.user_id
                        LEFT JOIN courses c ON s.course_id = c.course_id
                        LEFT JOIN visitors v ON u.user_id = v.user_id
                        LEFT JOIN admin a ON u.user_id = a.user_id
                        WHERE ei.event_id = %s AND ei.event_date BETWEEN %s AND %s {dept_condition}
                        ORDER BY ea.first_in ASC
                    """
                    cursor.execute(query, [report_type, start_date, end_date] + dept_params)
                    raw_logs = cursor.fetchall()
                    
                    cursor.execute("SELECT COUNT(*) as count FROM event_participants WHERE event_id = %s", (report_type,))
                    expected_result = cursor.fetchone()
                    total_expected = expected_result['count'] if expected_result else 0
                    total_present = sum(1 for log in raw_logs if log['status'] in ['Present', 'Late'])

                case 'General Logs' | 'Visitor Logs':
                    report_title = "General Campus Access Logs"

                    if report_type == 'student_entry_exit':
                        event_name_display = "Campus Gates Entry/Exit"
                        col_headers = ["User Name", "Role / Affiliation", "Time", "Action", "Gate"]
                        
                        query = f"""
                            SELECT 
                                COALESCE(e.employee_name, s.student_name, v.visitor_name, a.username, 'Unknown User') AS name,
                                CONCAT(UPPER(u.role), ' - ', COALESCE(d.department_name, c.course_name, v.purpose, 'N/A')) AS detail,
                                TIME_FORMAT(gl.timestamp, '%h:%i %p') AS time,
                                gl.log_type AS status,
                                COALESCE(gl.gate, 'Main Gate') AS remarks
                            FROM general_log gl
                            JOIN users u ON gl.user_id = u.user_id
                            LEFT JOIN employees e ON u.user_id = e.user_id
                            LEFT JOIN departments d ON e.department_id = d.department_id
                            LEFT JOIN students s ON u.user_id = s.user_id
                            LEFT JOIN courses c ON s.course_id = c.course_id
                            LEFT JOIN visitors v ON u.user_id = v.user_id
                            LEFT JOIN admin a ON u.user_id = a.user_id
                            WHERE DATE(gl.timestamp) BETWEEN %s AND %s {dept_condition}
                            ORDER BY gl.timestamp DESC
                        """
                        cursor.execute(query, [start_date, end_date] + dept_params)
                        raw_logs = cursor.fetchall()
                    elif report_type == 'daily_traffic':
                        event_name_display = "Daily Traffic Analysis"
                        col_headers = ["Hour Time", "Role / Affiliation", "Time", "Action", "Gate"]
                        
                        query = f"""
                            SELECT 
                                COALESCE(e.employee_name, s.student_name, v.visitor_name, a.username, 'Unknown User') AS name,
                                CONCAT(UPPER(u.role), ' - ', COALESCE(d.department_name, c.course_name, v.purpose, 'N/A')) AS detail,
                                TIME_FORMAT(gl.timestamp, '%h:%i %p') AS time,
                                gl.log_type AS status,
                                COALESCE(gl.gate, 'Main Gate') AS remarks
                            FROM general_log gl
                            JOIN users u ON gl.user_id = u.user_id
                            LEFT JOIN employees e ON u.user_id = e.user_id
                            LEFT JOIN departments d ON e.department_id = d.department_id
                            LEFT JOIN students s ON u.user_id = s.user_id
                            LEFT JOIN courses c ON s.course_id = c.course_id
                            LEFT JOIN visitors v ON u.user_id = v.user_id
                            LEFT JOIN admin a ON u.user_id = a.user_id
                            WHERE DATE(gl.timestamp) BETWEEN %s AND %s {dept_condition}
                            ORDER BY gl.timestamp DESC
                        """
                        cursor.execute(query, [start_date, end_date] + dept_params)
                        raw_logs = cursor.fetchall()
                    
                    total_present = len(raw_logs)
                    total_expected = len(raw_logs)

            return {
                "report_title": report_title,
                "event_name_display": event_name_display,
                "col_headers": col_headers,
                "raw_logs": raw_logs,
                "total_expected": total_expected,
                "total_present": total_present
            }

        except Exception as e:
            print(f"Database Error: {e}")
            return None
        finally:
            cursor.close()

# ==============================================================================
    # ANALYTICS / DASHBOARD STATS
    # ==============================================================================

    @staticmethod
    def get_overall_dashboard_stats(conn):
        try:
            cursor = conn.cursor(dictionary=True)
            today = datetime.now().date()

            cursor.execute("""
                SELECT COUNT(*) AS total FROM general_log 
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
            """, (today,))
            total_entries = cursor.fetchone()['total']

            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM students WHERE status = 'Inside') +
                    (SELECT COUNT(*) FROM employees WHERE status = 'Inside') AS inside
            """)
            currently_inside = cursor.fetchone()['inside']

            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, e.timestamp, x.timestamp)) AS avg_dwell
                FROM general_log e
                JOIN general_log x 
                    ON e.user_id = x.user_id
                    AND DATE(e.timestamp) = DATE(x.timestamp)
                    AND e.log_type = 'Entry'
                    AND x.log_type = 'Exit'
                    AND x.timestamp > e.timestamp
                WHERE DATE(e.timestamp) = %s
            """, (today,))
            avg_mins = cursor.fetchone()['avg_dwell'] or 0
            avg_dwell = f"{int(avg_mins // 60)} hrs {int(avg_mins % 60)} mins"

            cursor.execute("""
                SELECT HOUR(timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                GROUP BY HOUR(timestamp)
                ORDER BY cnt DESC
                LIMIT 1
            """, (today,))
            peak_row = cursor.fetchone()
            peak_hour = f"{peak_row['hr']:02d}:00" if peak_row else "N/A"

            cursor.execute("""
                SELECT HOUR(timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
                GROUP BY HOUR(timestamp)
            """, (today,))
            hourly = {row['hr']: row['cnt'] for row in cursor.fetchall()}
            traffic_chart = [hourly.get(h, 0) for h in range(6, 18)]

            cursor.execute("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(status IN ('Present', 'Late')) AS attended
                FROM event_attendance
                WHERE event_date = %s
            """, (today,))
            event_row = cursor.fetchone()
            total_invited = event_row['total'] or 0
            total_attended = int(event_row['attended'] or 0)
            rate = f"{round((total_attended / total_invited) * 100, 1)}%" if total_invited > 0 else "N/A"
            raw = f"{total_attended:,} / {total_invited:,} Attendees"

            cursor.execute("""
                SELECT COUNT(*) AS total FROM general_log
                WHERE DATE(timestamp) = %s AND log_type = 'Entry'
            """, (today - timedelta(days=1),))
            yesterday = cursor.fetchone()['total'] or 1
            trend = f"+{round(((total_entries - yesterday) / yesterday) * 100)}%" if yesterday else "N/A"

            cursor.execute("""
                SELECT d.department_name, COUNT(*) AS cnt
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                JOIN employees emp ON u.user_id = emp.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE DATE(gl.timestamp) = %s AND gl.log_type = 'Entry'
                GROUP BY d.department_name
                ORDER BY cnt DESC
                LIMIT 5
            """, (today,))
            dist_rows = cursor.fetchall()
            total_dept_entries = sum(r['cnt'] for r in dist_rows) or 1
            dept_distribution = [round((r['cnt'] / total_dept_entries) * 100) for r in dist_rows]

            while len(dept_distribution) < 5:
                dept_distribution.append(0)
                
            return {
                "total_entries": f"{total_entries:,}",
                "entries_trend": trend,
                "currently_inside": f"{currently_inside:,}",
                "avg_dwell_time": avg_dwell,
                "peak_hour": peak_hour,
                "traffic_chart": traffic_chart,
                "event_attendance_rate": rate,
                "event_attendance_raw": raw,
                "dept_distribution": dept_distribution,
                "alerts": []
            }

        except connector.Error as err:
            print(f"Error fetching overall stats: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()


    @staticmethod
    def get_student_dashboard_stats(conn):
        try:
            cursor = conn.cursor(dictionary=True)
            today = datetime.now().date()

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student' AND DATE(gl.timestamp) = %s AND gl.log_type = 'Entry'
            """, (today,))
            total_entries = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS inside FROM students WHERE status = 'Inside'")
            currently_inside = cursor.fetchone()['inside']

            cursor.execute("""
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
            """, (today,))
            avg_mins = cursor.fetchone()['avg_stay'] or 0
            avg_stay = f"{round(avg_mins / 60, 1)} Hrs"

            cursor.execute("""
                SELECT HOUR(gl.timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student' AND DATE(gl.timestamp) = %s AND gl.log_type = 'Entry'
                GROUP BY HOUR(gl.timestamp)
                ORDER BY cnt DESC LIMIT 1
            """, (today,))
            peak_row = cursor.fetchone()
            peak_hour = f"{peak_row['hr']:02d}:00 AM" if peak_row else "N/A"

            cursor.execute("SELECT COUNT(*) AS total FROM students")
            total_students = cursor.fetchone()['total'] or 1
            peak_load = f"{round((currently_inside / total_students) * 100)}%"

            cursor.execute("""
                SELECT HOUR(gl.timestamp) AS hr, COUNT(*) AS cnt
                FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student' AND DATE(gl.timestamp) = %s AND gl.log_type = 'Entry'
                GROUP BY HOUR(gl.timestamp)
            """, (today,))
            hourly = {row['hr']: row['cnt'] for row in cursor.fetchall()}
            hourly_traffic = [hourly.get(h, 0) for h in range(6, 18)]

            cursor.execute("""
                SELECT COUNT(*) AS total FROM general_log gl
                JOIN users u ON gl.user_id = u.user_id
                WHERE u.role = 'student' AND DATE(gl.timestamp) = %s AND gl.log_type = 'Entry'
            """, (today - timedelta(days=1),))
            yesterday = cursor.fetchone()['total'] or 1
            trend = f"+{round(((total_entries - yesterday) / yesterday) * 100)}%" if yesterday else "N/A"

            return {
                "total_entries": f"{total_entries:,}",
                "entries_trend": trend,
                "peak_hour": peak_hour,
                "peak_load": peak_load,
                "currently_inside": f"{currently_inside:,}",
                "avg_stay": avg_stay,
                "hourly_traffic": hourly_traffic,
                "watchlist": [],
                "curfew_trigger": "09:40:00 PM"
            }

        except connector.Error as err:
            print(f"Error fetching student stats: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()


    @staticmethod
    def get_employee_dashboard_stats(conn):
        try:
            cursor = conn.cursor(dictionary=True)
            today = datetime.now().date()

            cursor.execute("""
                SELECT status, COUNT(*) AS cnt
                FROM event_attendance
                WHERE event_date = %s
                GROUP BY status
            """, (today,))
            attendance_map = {row['status']: row['cnt'] for row in cursor.fetchall()}
            attendance_data = [
                attendance_map.get('Present', 0),
                attendance_map.get('Late', 0),
                attendance_map.get('Absent', 0)
            ]

            total_attendance = sum(attendance_data)
            on_time = attendance_data[0]
            on_time_rate = f"{round((on_time / total_attendance) * 100)}%" if total_attendance > 0 else "N/A"

            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, 
                    TIMESTAMP(ea.event_date, e.time_start), 
                    ea.first_in
                )) AS avg_late
                FROM event_attendance ea
                JOIN event_instances ei ON ea.instance_id = ei.instance_id
                JOIN events e ON ei.event_id = e.event_id
                WHERE ea.event_date = %s AND ea.status = 'Late'
            """, (today,))
            avg_late = cursor.fetchone()['avg_late'] or 0
            avg_tardiness = f"{int(avg_late)} mins"

            cursor.execute("""
                SELECT d.department_name AS dept, 
                       AVG(TIMESTAMPDIFF(MINUTE,
                           TIMESTAMP(ea.event_date, e.time_start),
                           ea.first_in
                       )) AS avg_late
                FROM event_attendance ea
                JOIN event_instances ei ON ea.instance_id = ei.instance_id
                JOIN events e ON ei.event_id = e.event_id
                JOIN users u ON ea.user_id = u.user_id
                JOIN employees emp ON u.user_id = emp.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE ea.event_date = %s AND ea.status = 'Late'
                GROUP BY d.department_name
                ORDER BY avg_late DESC
                LIMIT 7
            """, (today,))
            tardiness_rows = cursor.fetchall()
            tardiness_data = [round(row['avg_late'] or 0) for row in tardiness_rows]

            cursor.execute("""
                SELECT d.department_name AS name,
                       ROUND(SUM(ea.status IN ('Present','Late')) / COUNT(*) * 100) AS value
                FROM event_attendance ea
                JOIN users u ON ea.user_id = u.user_id
                JOIN employees emp ON u.user_id = emp.user_id
                JOIN departments d ON emp.department_id = d.department_id
                WHERE ea.event_date = %s
                GROUP BY d.department_name
                ORDER BY value DESC
                LIMIT 5
            """, (today,))
            dept_participation = [
                {"name": row['name'], "value": row['value']}
                for row in cursor.fetchall()
            ]

            return {
                "attendance_data": attendance_data,
                "tardiness_data": tardiness_data if tardiness_data else [0] * 7,
                "dept_participation": dept_participation,
                "avg_tardiness": avg_tardiness,
                "on_time_rate": on_time_rate
            }

        except connector.Error as err:
            print(f"Error fetching employee stats: {err}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
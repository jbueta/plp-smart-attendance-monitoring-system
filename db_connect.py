import mysql.connector as connector

class Database:
    
    def __init__(self, conn, parameter):
        self.conn = conn
        self.parameter = parameter

        if self.conn:
            self.cursor = self.conn.cursor(dictionary=True)
        else:
            raise Exception("Failed to connect to the database.")
        
    
    # =============================================================
    # GENERAL ENTRY/EXIT MODEL LOGIC
    # =============================================================

    def authenticate_user(self):
        try:
            query = """ SELECT * FROM users LEFT JOIN students USING (user_id) LEFT JOIN employees USING (user_id)
                        WHERE student_id = %s OR employee_id = %s
                    """
            print(self.parameter)
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None


    def change_status(self):
        try:
            query = """UPDATE students SET status = %s WHERE student_id = %s"""
            if self.parameter[1].lower() == 'inside':
                status = 'Outside'
            else: 
                status = 'Inside'

            new_param = (status, self.parameter[0])
            self.cursor.execute(query, new_param)
            rows_affected = self.cursor.rowcount

            id = self.parameter[0]

            if rows_affected > 0:
                data = {"message": f"{id} status changed sucessfully!", "status": status}
                return data
            else:
                return None
        
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error: {err}")
            return None

    def check_general_logs(self):
        
        try:
            log_query = """SELECT * FROM general_log WHERE user_id = %s AND DATE(timestamp) = %s"""

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        
    def insert_general_log(self):
        try:
            insert_log_query = """INSERT INTO general_log (user_id, timestamp, log_type, gate) VALUES (%s, %s, %s, %s)"""
            self.cursor.execute(insert_log_query, self.parameter)
            self.conn.commit()
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                return "Log inserted successfully!"
            else:
                return None  # No rows inserted
        
        except connector.Error as err:
            self.conn.rollback()
            print(f"Error: {err}")
            return None

    def retrieve_log(self):
        try:
            log_query = """SELECT * FROM general_log WHERE person_id = %s AND DATE(timestamp) = %s"""

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
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
            self.conn.commit()
            return "User added successfully!"
        except connector.Error as err:
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
                           (event_name, event_type, frequency, day, start_date, 
                           end_date, time_start, time_end, location, active) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[2], self.parameter[3], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], self.parameter[8], 1)

            else:
                query = """INSERT IGNORE INTO events (event_name, event_type, start_date, end_date, time_start, time_end, location, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (self.parameter[0], self.parameter[1], self.parameter[4], self.parameter[5], self.parameter[6], self.parameter[7], self.parameter[8], 1)

            self.cursor.execute(query, params)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                print("Event created!")

                event_id = int(self.cursor.lastrowid)
                participants = self.parameter[9]

                if participants and isinstance(participants, list):
                    new_query = "INSERT IGNORE INTO event_participants (event_id, user_id) VALUES (%s, %s)"
                    #List ([1, "23-00314"], [2, "23-00315"])
                    participant_data = [(event_id, user_id) for user_id in participants]
                    self.cursor.executemany(new_query, participant_data)

                self.conn.commit()
                print ("Participants attached successfully!")
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
                query = """ SELECT event_id FROM events 
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
            
            if log_type == 'Entry':
                log_query = """ UPDATE event_attendance JOIN event_instances ON 
                                event_attendance.instance_id = event_instances.instance_id
                                SET event_attendance.status = 'Present', event_attendance.first_in = NOW()
                                WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE() 
                                AND event_attendance.status = 'Absent'
                            """
            elif log_type == 'Exit':
                log_query = """ UPDATE event_attendance JOIN event_instances ON event_attendance.instance_id = event_instances.instance_id
                                SET event_attendance.last_out = NOW() WHERE event_attendance.user_id = %s 
                                AND event_instances.event_id = %s 
                                AND event_attendance.event_date = CURRENT_DATE()
                            """

            params = (self.parameter[0], self.parameter[1])
            self.cursor.execute(log_query, params)
            self.conn.commit()

            return {"message": "Event logging successfully!", "success": True}
            
        except connector.Error as err:
            self.conn.rollback()
            return {"message": f"Error: {err}", "success": False}

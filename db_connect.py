import mysql.connector as connector

def connect_db():
        try:
            conn = connector.connect(
                host='localhost',
                user='root',
                password='',
                database='schema'
            )
            return conn
        
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        
class Database:
    
    def __init__(self, parameter):
        self.conn = connect_db()
        self.parameter = parameter

        if self.conn:
            self.cursor = self.conn.cursor(dictionary=True)
        else:
            raise Exception("Failed to connect to the database.")
        
    
    def authenticate_user(self):
        try:
            query = "SELECT * FROM students WHERE student_no = %s LEFT JOIN user using (user_id)"
            self.cursor.execute(query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            self.cursor.close()
            self.conn.close()

    def change_status(self):
        try:
            query = "UPDATE students SET status = %s" \
                    " WHERE student_no = %s"
            if self.parameter.status.lower() == 'inside':
                status = 'outside'
            else: 
                status = 'inside'

            new_param = (status, self.parameter.student_id)
            self.cursor.execute(query, new_param)
            rows_affected = self.cursor.rowcount

            if rows_affected > 0:
                return f"{self.parameter.student_id} status changed sucessfully!"
            else:
                return None


    def check_logs(self):
        
        try:
            log_query = "SELECT * FROM attendance_log WHERE person_id = %s AND DATE(log_time) = %s"

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            self.cursor.close()
            self.conn.close()
        
    def insert_log(self):
        try:
            insert_log_query = "INSERT INTO attendance_log (user_id, action, log_time) VALUES (%s, %s, %s)"
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
        finally:
            self.cursor.close()
            self.conn.close()

    def retrieve_log(self):
        try:
            log_query = "SELECT * FROM attendance_log WHERE person_id = %s AND DATE(log_time) = %s"

            self.cursor.execute(log_query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            self.cursor.close()
            self.conn.close()

    def get_analytics(self):
        try:
            self.cursor.execute(self.query, self.parameter)
            result = self.cursor.fetchall()

            return result if result else []
            
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            self.cursor.close()
            self.conn.close()

    def add_user(self):
        try:
            query = "INSERT INTO users (user_name, user_type) VALUES (%s, %s)"

            self.cursor.execute(query, self.parameter)
            rows_affected = self.cursor.rowcount
            if rows_affected > 0:
                last_id = int(self.cursor.lastrowid)
                if self.parameter.user_type== 'employee':
                    new_query = "INSERT INTO employees (user_id, department, position, gender, age) VALUES (%i, %s, %s, %s, %s)"
                    params = (last_id, self.parameter.metadata['Department'], self.parameter.metadata['Position'], self.parameter.metadata['Gender'], self.parameter.metadata['Age'])
                    self.cursor.execute(new_query, params)
                elif self.parameter.user_type == 'student':
                    new_query = "INSERT INTO students (user_id, student_no, course) VALUES (%i, %s, %s)"
                    params = (last_id, self.parameter.metadata['student_no'], self.parameter.metadata['course'])
                    self.cursor.execute(new_query, params)
                elif self.parameter.user_type == 'visitor':
                    new_query = "INSERT INTO visitors (user_id, purpose) VALUES (%i, %s)"
                    params = (last_id, self.parameter.metadata['purpose'])
                    self.cursor.execute(new_query, params)
            self.conn.commit()
            return "User added successfully!"
        except connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            self.cursor.close()
            self.conn.close()

    def delete_user(self):
        query = "DELETE FROM users WHERE user_id = %s"
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
        finally:
            self.cursor.close()
            self.conn.close()
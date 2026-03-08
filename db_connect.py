import mysql.connector as connector

class Database:
    
    def __init__(self, conn, parameter):
        self.conn = conn
        self.parameter = parameter

        if self.conn:
            self.cursor = self.conn.cursor(dictionary=True)
        else:
            raise Exception("Failed to connect to the database.")
        
    
    def authenticate_user(self):
        try:
            query = """SELECT * FROM students LEFT JOIN users USING (user_id) WHERE student_id = %s"""
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

    def check_logs(self):
        
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

    def get_analytics(self):
        try:
            self.cursor.execute(self.query, self.parameter)
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
                if self.parameter.user_type== 'employee':
                    new_query = "INSERT INTO employees (user_id, department, position, gender, age) VALUES (%s, %s, %s, %s, %s)"
                    params = (last_id, self.parameter.metadata['Department'], self.parameter.metadata['Position'], self.parameter.metadata['Gender'], self.parameter.metadata['Age'])
                    self.cursor.execute(new_query, params)
                elif self.parameter.user_type == 'student':
                    new_query = "INSERT INTO students (user_id, student_no, course) VALUES (%s, %s, %s)"
                    params = (last_id, self.parameter.metadata['student_no'], self.parameter.metadata['course'])
                    self.cursor.execute(new_query, params)
                elif self.parameter.user_type == 'visitor':
                    new_query = "INSERT INTO visitors (user_id, purpose) VALUES (%s, %s)"
                    params = (last_id, self.parameter.metadata['purpose'])
                    self.cursor.execute(new_query, params)
            self.conn.commit()
            return "User added successfully!"
        except connector.Error as err:
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
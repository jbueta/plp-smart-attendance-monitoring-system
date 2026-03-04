

# NEVER MIND THIS
# REFERENCE KO TO SA INITIAL NA GAWA KO
# THANK U, BERIMATSU

from flask import Flask, jsonify, request
# from flask_cors import CORS
from db_connect import Database
from datetime import datetime


app = Flask(__name__)
# CORS(app)

@app.route('/')
def home():
    return "Welcome to the API!"

@app.route('/authenticate', methods=['POST'])
def authenticate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        date = now.strftime("%Y-%m-%d")

        parameter = (user_id,)

        db = Database(parameter)
        result = db.authenticate_user()

        if not result or len(result) == 0:
            return jsonify({"Invalid": "User does not exist in the database"}), 404
        elif result and len(result) > 0:

            params = (user_id, date)
            db_log = Database(params)
            log_result = db_log.check_logs()


            match log_result:
                case None:
                    log_params = (user_id, "Entry", formatted_time)
                    db_insert_log = Database(log_params)
                    db_insert_log.insert_log()
                case lst if isinstance(lst, list):
                    entry = 0
                    exit = 0

                    for log in lst:
                        log_action = log.get('action', '').lower()
                        if log_action == 'entry':
                            entry += 1
                        elif log_action == 'exit':
                            exit += 1

                    if entry > exit:
                        log_params = (user_id, "Exit", formatted_time)
                    elif entry == 0 or entry == exit:
                        log_params = (user_id, "Entry", formatted_time)
                    else:
                        return jsonify({"success": False, "message": f"Error inserting log: Invalid log state"}), 500

                    db_insert_log = Database(log_params)
                    db_insert_log.insert_log()

            return jsonify({"success": True, "message": "User authenticated and log updated"}), 200

        
    except Exception as e:
            return jsonify({"success": False, "message": f"Error during authentication: {str(e)}"}), 500

@app.route('/add-user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        name = data.get('name')
        gender = data.get('gender')
        age = data.get('age')
        user_type = data.get('user_type')

        if not all([name, gender, age, user_type]):
            return jsonify({"error": "All fields (name, gender, age, user_type) are required"}), 400
        
        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "name must be a non-empty string"}), 400
        
        try:
            age = int(age)
            if age < 0 or age > 150:
                return jsonify({"error": "Age must be between 0 and 150"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Age must be a valid number"}), 400
        
        valid_user_types = ['employee', 'student', 'visitor']
        if user_type.lower() not in valid_user_types:
            return jsonify({"error": f"User type must be one of: {', '.join(valid_user_types)}"}), 400

        if user_type.lower() == 'employee':
            metadata = {"Department": data.get('department'),
                        "Position": data.get('position'),
                        "Gender": data.get('gender'),
                        "Age": int(data.get('age'))
                        }
        elif user_type.lower() == 'student':
            metadata = {"student_no": data.get('student_no'),
                        "course": data.get('course'),
                        }
        elif user_type.lower() == 'visitor':
            metadata = {"purpose": data.get('purpose'),
                        }
        else:
            return jsonify({"error": "Invalid user type"}), 400
        
        parameter = (name, gender, age, user_type.lower(), metadata)

        db = Database(parameter)
        result = db.add_user()
        if result is None:
            return jsonify({"success": False, "message": "Error has occured in adding user."}), 201
        return jsonify({"success": True, "message": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 201

@app.route('/delete-user', methods=['DELETE'])
def delete_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        parameter = (user_id,)

        db = Database(parameter)
        result = db.delete_user()
        if result is None:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"success": True, "message": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 201

@app.route('/retrieve_logs', method='GET')
def retrieve_logs():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        params = (date)
        db = Database(params)
        result = db.check_logs()
        if result is None and len(result) == 0:
            return jsonify({"success": False, "message": "No logs retrieved in the specified date."}), 201
        elif len(result) > 0:
            return jsonify({"success": True, "message": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 201

@app.route('/retrieve-analytics', methods=['GET', 'POST'])
def retrieve_analytics():
    try:
        user_id = None
        
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            user_id = data.get('user_id')
        
        elif request.method == 'GET':
            user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        parameter = (user_id,)

        db = Database(parameter)
        result = db.get_analytics()
        if result is None:
            return jsonify({"error": "Database error occurred"}), 500
        elif isinstance(result, list) and result:
            return jsonify({"success": True, "data": result}), 200
        else:
            return jsonify({"success": False, "message": "No analytics found"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)

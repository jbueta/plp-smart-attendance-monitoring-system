import uuid
from extensions import cache
from database import connect_db
from db_connect import Database

def pair_entry_exit_records(raw_logs):
    """
    Pair entry and exit records for the same user into single rows.
    Entry/Exit pairs are combined so one row = one complete session.
    """
    from collections import defaultdict
    
    user_logs = defaultdict(list)
    for log in raw_logs:
        timestamp = log.get('timestamp')
        log_date = timestamp.date() if hasattr(timestamp, 'date') else None
        user_key = log.get('user_id') or log.get('name', 'Unknown')
        user_logs[(user_key, log_date)].append(log)
    
    paired_records = []
    
    # Pair only chronological logs from the same user and day.
    for _group_key, logs in user_logs.items():
        sorted_logs = sorted(
            logs,
            key=lambda x: (
                x.get('timestamp') or '',
                x.get('log_id') or 0,
            ),
        )
        
        entry_record = None
        for log in sorted_logs:
            status = log.get('status', '').lower()
            
            if status == 'entry' and entry_record is None:
                entry_record = log.copy()
                entry_record['time_in'] = log.get('time', '')
                entry_record['time_out'] = None
                
            elif status == 'entry' and entry_record is not None:
                entry_record['time_out'] = 'N/A'
                entry_record['status'] = 'In Progress'
                paired_records.append(entry_record)
                entry_record = log.copy()
                entry_record['time_in'] = log.get('time', '')
                entry_record['time_out'] = None

            elif (status == 'exit' or status == 'absent') and entry_record is not None:
                entry_record['time_out'] = log.get('time', '')
                entry_record['status'] = 'Present' if status == 'exit' else 'Absent'
                paired_records.append(entry_record)
                entry_record = None
        
        if entry_record is not None:
            entry_record['time_out'] = 'N/A'
            entry_record['status'] = 'In Progress'
            paired_records.append(entry_record)
    
    return sorted(
        paired_records,
        key=lambda x: (
            x.get('timestamp') or '',
            x.get('log_id') or 0,
        ),
        reverse=True,
    )

def calculate_general_logs_metrics(paired_logs):
    """
    Calculate metrics for General Logs:
    - Total Entry: Count of unique users
    - Peak Time Hour: Hour with most entries
    - Average Time Spent: Average duration between entry and exit
    """
    if not paired_logs:
        return {
            "total_entry": 0,
            "peak_hour": "N/A",
            "avg_time_spent": "0h 0m"
        }
    
    unique_users = set()
    hour_counts = {}
    total_duration_minutes = 0
    users_with_duration = 0
    
    for log in paired_logs:
        user_name = log.get('name', 'Unknown')
        unique_users.add(user_name)
        
        time_in = log.get('time_in', '')
        if time_in and time_in != 'N/A':
            try:
                hour_str = time_in.split(':')[0]
                hour_counts[hour_str] = hour_counts.get(hour_str, 0) + 1
            except:
                pass
        
        time_in = log.get('time_in', '')
        time_out = log.get('time_out', '')
        if time_in and time_out and time_in != 'N/A' and time_out != 'N/A':
            try:
                import datetime
                time_in_obj = datetime.datetime.strptime(time_in, '%I:%M %p')
                time_out_obj = datetime.datetime.strptime(time_out, '%I:%M %p')
                
                if time_out_obj < time_in_obj:
                    time_out_obj = time_out_obj.replace(day=time_out_obj.day + 1)
                
                duration = time_out_obj - time_in_obj
                total_duration_minutes += int(duration.total_seconds() / 60)
                users_with_duration += 1
            except Exception as e:
                print(f"Error parsing time: {e}")
                pass
    
    peak_hour = "N/A"
    if hour_counts:
        peak_hour = max(hour_counts, key=hour_counts.get) + ":00"
    
    avg_minutes = 0
    if users_with_duration > 0:
        avg_minutes = int(total_duration_minutes / users_with_duration)
    
    hours = avg_minutes // 60
    minutes = avg_minutes % 60
    avg_time_spent = f"{hours}h {minutes}m"
    
    return {
        "total_entry": len(unique_users),
        "peak_hour": peak_hour,
        "avg_time_spent": avg_time_spent
    }

@cache.memoize(timeout=600) 
def fetch_report_data(category, report_type, filter_val, start_date, end_date):
    conn = None
    try:
        # Debug logging
        print(f"[REPORT DEBUG] Category: {category}, Type: {report_type}, Filter: {filter_val}, Start: {start_date}, End: {end_date}")
        
        conn = connect_db()
        if not conn:
            return {"error": "Database offline"}
    
        data = Database.get_report_queries(conn, category, report_type, filter_val, start_date, end_date)
        print(f"[REPORT DEBUG] Query returned: {data}")
        
        if not data:
            return {"error": "Failed to generate report data"}

        logs = []
        
        # For General Logs category, pair entry/exit records and calculate special metrics
        if category.lower() == 'general':
            pair_logs = pair_entry_exit_records(data['raw_logs'])
            for index, row in enumerate(pair_logs, start=1):
                row['id'] = index
                if 'detail' in row and 'dept' not in row:
                    row['dept'] = row['detail']
                logs.append(row)
            
            # Calculate General Logs specific metrics
            general_metrics = calculate_general_logs_metrics(pair_logs)
        else:
            # For other categories, process normally
            for index, row in enumerate(data['raw_logs'], start=1):
                row['id'] = index
                if 'detail' in row and 'dept' not in row:
                    row['dept'] = row['detail']
                logs.append(row)
            
            # Calculate standard metrics for non-general categories
            attendance_rate = "0.0"
            if data['total_expected'] > 0:
                attendance_rate = str(round((data['total_present'] / data['total_expected']) * 100, 1))
            elif (category or '').lower() in ['general', 'visitor']:
                attendance_rate = "100.0"
            general_metrics = None 

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    return {
        "report_data": {
            "title": data['report_title'],
            "reference_id": f"PLP-{category[:3].upper()}-{uuid.uuid4().hex[:6].upper()}",
            "event_name": data['event_name_display'],
            "department": data.get('filter_display', filter_val),
            "date_range": f"{start_date} to {end_date}",
            "headers": data['col_headers']
        },
        "metrics_data": general_metrics if (category.lower() == 'general' and general_metrics) else {
            "expected": data['total_expected'],
            "present": data['total_present'],
            "rate": f"{attendance_rate}%"
        },
        "logs": logs,
        "category": category
    }

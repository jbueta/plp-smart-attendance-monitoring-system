import uuid
from extensions import cache
from database import connect_db
from db_connect import Database

@cache.memoize(timeout=600) 
def fetch_report_data(category, report_type, filter_val, start_date, end_date):
    conn = None
    try:
        # Debug logging
        print(f"[REPORT DEBUG] Category: {category}, Type: {report_type}, Filter: {filter_val}, Start: {start_date}, End: {end_date}")
        
        conn = connect_db()
        if not conn:
            return {"error": "Database offline"}
    
        data = Database.get_report_queries(conn, category, report_type, start_date, end_date)
        print(f"[REPORT DEBUG] Query returned: {data}")
        
        if not data:
            return {"error": "Failed to generate report data"}

        logs = []
        for index, row in enumerate(data['raw_logs'], start=1):
            row['id'] = index
            # Align database field 'detail' to template field 'dept'
            if 'detail' in row and 'dept' not in row:
                row['dept'] = row['detail']
            logs.append(row)
            
        attendance_rate = "0.0"
        if data['total_expected'] > 0:
            attendance_rate = str(round((data['total_present'] / data['total_expected']) * 100, 1))
        elif category in ['General Logs', 'Visitor Logs']:
            attendance_rate = "100.0" 

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    return {
        "report_data": {
            "title": data['report_title'],
            "reference_id": f"PLP-{category[:3].upper()}-{uuid.uuid4().hex[:6].upper()}",
            "event_name": data['event_name_display'],
            "department": filter_val,
            "date_range": f"{start_date} to {end_date}",
            "headers": data['col_headers']
        },
        "metrics_data": {
            "expected": data['total_expected'],
            "present": data['total_present'],
            "rate": f"{attendance_rate}%"
        },
        "logs": logs
    }
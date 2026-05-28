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
                entry_record['entry_timestamp'] = log.get('timestamp')
                entry_record['time_out'] = None
                entry_record['exit_timestamp'] = None
                
            elif status == 'entry' and entry_record is not None:
                entry_record['time_out'] = 'N/A'
                entry_record['exit_timestamp'] = None
                entry_record['status'] = 'In Progress'
                paired_records.append(entry_record)
                entry_record = log.copy()
                entry_record['time_in'] = log.get('time', '')
                entry_record['entry_timestamp'] = log.get('timestamp')
                entry_record['time_out'] = None
                entry_record['exit_timestamp'] = None

            elif (status == 'exit' or status == 'absent') and entry_record is not None:
                entry_record['time_out'] = log.get('time', '')
                entry_record['exit_timestamp'] = log.get('timestamp')
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


def _format_hour_label(hour):
    try:
        hour = int(hour)
    except (TypeError, ValueError):
        return "N/A"
    if hour == 0:
        return "12:00 AM"
    if hour < 12:
        return f"{hour}:00 AM"
    if hour == 12:
        return "12:00 PM"
    return f"{hour - 12}:00 PM"


def calculate_daily_traffic_summary(raw_logs):
    from collections import defaultdict
    if not raw_logs:
        return {
            "daily_rows": [],
            "metrics": {
                "total_entries": 0,
                "total_exits": 0,
                "peak_hour": "N/A",
                "avg_time_spent": "0h 0m",
                "gate1_entries": 0,
                "gate2_entries": 0,
                "gate3_entries": 0,
            }
        }

    daily = {}
    total_entries = 0
    total_exits = 0
    gate_totals = {"Gate 1": 0, "Gate 2": 0, "Gate 3": 0}
    hourly_counts = {}

    for row in raw_logs:
        timestamp = row.get("timestamp")
        if not timestamp:
            continue
        log_date = timestamp.date().isoformat()
        entry_time = timestamp
        status = str(row.get("status") or "").lower()
        gate = str(row.get("gate") or "Gate 1")

        day = daily.setdefault(log_date, {
            "date": log_date,
            "entries": 0,
            "exits": 0,
            "gate1_entries": 0,
            "gate2_entries": 0,
            "gate3_entries": 0,
            "hour_counts": {},
            "duration_minutes": [],
        })

        if status == "entry":
            day["entries"] += 1
            total_entries += 1
            if gate in gate_totals:
                day[f"{gate.lower().replace(' ', '')}_entries"] += 1
                gate_totals[gate] += 1
            else:
                gate_totals[gate] = gate_totals.get(gate, 0) + 1
            hour = entry_time.hour
            day["hour_counts"][hour] = day["hour_counts"].get(hour, 0) + 1
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        elif status == "exit":
            day["exits"] += 1
            total_exits += 1

    paired = pair_entry_exit_records(raw_logs)
    for record in paired:
        entry_timestamp = record.get("entry_timestamp")
        exit_timestamp = record.get("exit_timestamp")
        if not entry_timestamp or not exit_timestamp:
            continue
        log_date = entry_timestamp.date().isoformat()
        if log_date not in daily:
            continue
        try:
            duration = int((exit_timestamp - entry_timestamp).total_seconds() / 60)
            if duration >= 0:
                daily[log_date]["duration_minutes"].append(duration)
        except Exception:
            continue

    daily_rows = []
    for date_key in sorted(daily.keys()):
        day = daily[date_key]
        durations = day.get("duration_minutes", [])
        avg_duration = 0
        if durations:
            avg_duration = int(sum(durations) / len(durations))
        hours = avg_duration // 60
        minutes = avg_duration % 60
        peak_hour = "N/A"
        if day["hour_counts"]:
            peak_hour = _format_hour_label(max(day["hour_counts"], key=day["hour_counts"].get))

        daily_rows.append({
            "date": date_key,
            "entries": day["entries"],
            "exits": day["exits"],
            "peak_hour": peak_hour,
            "avg_time_spent": f"{hours}h {minutes}m",
            "gate1_entries": day["gate1_entries"],
            "gate2_entries": day["gate2_entries"],
            "gate3_entries": day["gate3_entries"],
        })

    overall_peak_hour = "N/A"
    if hourly_counts:
        overall_peak_hour = _format_hour_label(max(hourly_counts, key=hourly_counts.get))

    overall_avg = 0
    all_durations = [duration for day in daily.values() for duration in day.get("duration_minutes", [])]
    if all_durations:
        avg_val = int(sum(all_durations) / len(all_durations))
        overall_avg = f"{avg_val // 60}h {avg_val % 60}m"
    else:
        overall_avg = "0h 0m"

    return {
        "daily_rows": daily_rows,
        "metrics": {
            "total_entries": total_entries,
            "total_exits": total_exits,
            "peak_hour": overall_peak_hour,
            "avg_time_spent": overall_avg,
            "gate1_entries": gate_totals.get("Gate 1", 0),
            "gate2_entries": gate_totals.get("Gate 2", 0),
            "gate3_entries": gate_totals.get("Gate 3", 0),
        }
    }

@cache.memoize(timeout=600) 
def fetch_report_data(category, report_type, filter_val, start_date, end_date):
    conn = None
    try:
        category_key = (category or "").lower()
        if category_key == "violation":
            category_key = "violations"

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
        metrics_data = None
        
        if category_key == 'general' and report_type == 'daily_traffic':
            traffic_summary = calculate_daily_traffic_summary(data['raw_logs'])
            for index, row in enumerate(traffic_summary['daily_rows'], start=1):
                row['id'] = index
                logs.append(row)
            metrics_data = traffic_summary['metrics']
        elif category_key == 'general':
            pair_logs = pair_entry_exit_records(data['raw_logs'])
            for index, row in enumerate(pair_logs, start=1):
                row['id'] = index
                if 'detail' in row and 'dept' not in row:
                    row['dept'] = row['detail']
                logs.append(row)
            
            # Calculate General Logs specific metrics
            metrics_data = calculate_general_logs_metrics(pair_logs)
        elif category_key == 'visitor' and report_type == 'visitor_purpose':
            total_visitors = sum(row.get('visitor_count', 0) for row in data['raw_logs'])
            for index, row in enumerate(data['raw_logs'], start=1):
                visitor_count = row.get('visitor_count', 0)
                row['id'] = index
                row['visitor_count'] = visitor_count
                row['percentage'] = f"{round((visitor_count / total_visitors) * 100, 1)}%" if total_visitors else "0.0%"
                logs.append(row)
            metrics_data = {
                'total_visitors': total_visitors,
                'purpose_categories': len(data['raw_logs']),
                'filter_display': data.get('filter_display', filter_val)
            }
        elif category_key == 'violations' and report_type == 'curfew_violations':
            total_violations = sum(row.get('violation_count', 0) for row in data['raw_logs'])
            for index, row in enumerate(data['raw_logs'], start=1):
                row['id'] = index
                row['violation_count'] = row.get('violation_count', 0)
                logs.append(row)

            metrics_data = {
                'total_violations': total_violations,
                'peak_days': data.get('peak_day_stats', []),
                'top_offenders': data.get('top_offenders', []),
                'filter_display': data.get('filter_display', filter_val)
            }
        else:
            # For other categories, process normally
            for index, row in enumerate(data['raw_logs'], start=1):
                row['id'] = index
                if 'detail' in row and 'dept' not in row:
                    row['dept'] = row['detail']
                logs.append(row)
            
            # Calculate standard metrics for non-special categories
            attendance_rate = "0.0"
            if data['total_expected'] > 0:
                attendance_rate = str(round((data['total_present'] / data['total_expected']) * 100, 1))
            elif category_key in ['general', 'visitor']:
                attendance_rate = "100.0"
            metrics_data = {
                "expected": data['total_expected'],
                "present": data['total_present'],
                "rate": f"{attendance_rate}%"
            }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    return {
        "report_data": {
            "title": data['report_title'],
            "reference_id": f"PLP-{category_key[:3].upper()}-{uuid.uuid4().hex[:6].upper()}",
            "event_name": data['event_name_display'],
            "department": data.get('filter_display', filter_val),
            "date_range": f"{start_date} to {end_date}",
            "headers": data['col_headers']
        },
        "metrics_data": metrics_data,
        "logs": logs,
        "category": category_key
    }

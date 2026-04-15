# Event-Specific Manual Entry + Live Feed Implementation Guide

**Status:** ✅ Production-Ready  
**Branch:** feat/inocencio_backend  
**Date:** April 15, 2026

---

## 📋 Table of Contents
1. [Backend Endpoints (app_extension.py)](#backend-endpoints)
2. [Frontend JavaScript (static/js/kiosk.js)](#frontend-javascript)
3. [HTML Template (templates/kiosk_employee.html)](#html-template)
4. [Integration Checklist](#integration-checklist)

---

## Backend Endpoints

### 1. POST `/api/events/manual_entry` - Manual Event Entry with Live Feed Response

**Location:** `app_extension.py` (Lines 545-665)

```python
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
        
        # Generate initials from employee name (first letters of first two words)
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
```

**Expected Response:**
```json
{
  "success": true,
  "log_type": "Entry",
  "log": {
    "name": "Juan Dela Cruz",
    "dept": "Civil Engineering",
    "time": "7:45 AM",
    "status": "Present",
    "type": "success",
    "initials": "JD"
  },
  "message": "Entry logged successfully. General status now Inside."
}
```

---

### 2. GET `/admin/instances/{id}/get-logs` - Fetch Event Logs for Live Feed

**Location:** `app_extension.py` (Lines 803-856)

```python
@app.route("/admin/instances/<int:instance_id>/get-logs", methods=["GET"])
def get_instance_logs(instance_id):
    """
    Returns all event_log entries for a specific event instance.
    Each row corresponds to a single swipe (Entry or Exit).
    Used to populate the live feed on page load.
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
            
            # Remove leading zero (e.g., "08:15 AM" → "8:15 AM")
            if time_str.startswith('0'):
                time_str = time_str[1:]

            result.append({
                "initials": initials,
                "name": name,
                "dept": row['department'],
                "time": time_str,
                "log_type": row['log_type'],   # "Entry" or "Exit"
                "type": "success" if row['log_type'] == 'Entry' else "secondary"
            })

        return jsonify({"success": True, "logs": result}), 200

    except Exception as e:
        print(f"Error in get_instance_logs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            close_db(conn)
```

**Expected Response:**
```json
{
  "success": true,
  "logs": [
    {
      "initials": "JD",
      "name": "Juan Dela Cruz",
      "dept": "Civil Engineering",
      "time": "7:45 AM",
      "log_type": "Entry",
      "type": "success"
    },
    {
      "initials": "MS",
      "name": "Maria Santos",
      "dept": "College of Nursing",
      "time": "8:15 AM",
      "log_type": "Entry",
      "type": "success"
    }
  ]
}
```

---

## Frontend JavaScript

### Complete kiosk.js Implementation

**Location:** `static/js/kiosk.js`

```javascript
/* Kiosk functionality - Student and Employee */

/**
 * Format a datetime string to 12-hour time (e.g., "7:45 AM")
 */
function formatTime(datetimeStr) {
    if (!datetimeStr) return '';
    const date = new Date(datetimeStr);
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    const minutesStr = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutesStr} ${ampm}`;
}

/**
 * Get initials from a full name (first two words)
 */
function getInitials(name) {
    if (!name) return '';
    const parts = name.split(' ').slice(0, 2);
    return parts.map(p => p[0]).join('').toUpperCase();
}

/**
 * Escape HTML to prevent injection
 */
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

/**
 * Create a new log row element
 * @param {Object} log - contains name, dept, time, type, initials
 * @param {string} logType - 'Entry' or 'Exit'
 */
function createLogRow(log, logType) {
    // Build descriptive text for the badge
    const actionText = logType === 'Entry' ? 'Time In' : 'Time Out';
    const badgeText = `${actionText}: ${log.time}`;
    
    // Badge color: success/warning for entry, secondary for exit
    let badgeType = logType === 'Entry' ? log.type : 'secondary';
    
    const logDiv = document.createElement('div');
    logDiv.className = 'd-flex align-items-center p-3 rounded position-relative overflow-hidden';
    logDiv.style.background = 'rgba(255,255,255,0.03)';
    logDiv.innerHTML = `
        <div class="position-absolute start-0 top-0 bottom-0 bg-${badgeType}" style="width: 4px;"></div>
        <div class="rounded-circle bg-white bg-opacity-10 p-2 me-3 text-white" style="width: 40px; height: 40px; display:grid; place-items:center;">${escapeHtml(log.initials)}</div>
        <div class="flex-grow-1">
            <h6 class="mb-0">${escapeHtml(log.name)}</h6>
            <small class="text-white-50">${escapeHtml(log.dept)}</small>
        </div>
        <span class="badge bg-${badgeType} bg-opacity-25 text-${badgeType}">${escapeHtml(badgeText)}</span>
    `;
    return logDiv;
}

/**
 * Add a new log row to the feed (always appends/prepends, never updates existing)
 * @param {Object} log - log data
 * @param {string} logType - 'Entry' or 'Exit'
 */
function addNewLog(log, logType) {
    const feedContainer = document.getElementById('liveLogsContainer');
    if (!feedContainer) return;
    
    const newRow = createLogRow(log, logType);
    feedContainer.prepend(newRow);
    
    // Keep only the latest 6 logs
    while (feedContainer.children.length > 6) {
        feedContainer.removeChild(feedContainer.lastChild);
    }
}

/**
 * Load attendance for a specific event instance and populate the live feed
 * This loads initial entry logs for page initialization.
 */
function loadEventAttendance(instanceId) {
    console.log(`Loading event logs for instance ${instanceId}`);
    fetch(`http://127.0.0.1:5001/admin/instances/${instanceId}/get-logs`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (!data.success) throw new Error(data.message);
            const feedContainer = document.getElementById('liveLogsContainer');
            if (!feedContainer) return;
            feedContainer.innerHTML = '';
            // Take only the 6 most recent logs
            const recentLogs = data.logs.slice(0, 6);
            recentLogs.forEach(log => {
                addNewLog(log, log.log_type);
            });
        })
        .catch(err => console.error('Error loading event logs:', err));
}

/**
 * Handle manual ID entry – supports both general and event kiosks
 * @param {string} type - 'student' or 'employee'
 * @param {string|null} manualId - optional ID for scanner
 */
function submitManualEntry(type, manualId = null) {
    const idField = type === 'employee' ? 'manual-employee-id' : 'manual-student-id';
    const id = manualId !== null ? manualId : document.getElementById(idField).value.trim();
    
    if (!id) {
        alert("Please enter an ID");
        return;
    }
    
    const modalEl = document.getElementById('manualEntryModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
    
    // Determine if this is an event kiosk (employee event page has currentEventId)
    const isEventKiosk = type === 'employee' && window.currentEventId && window.currentEventId !== null;
    
    if (isEventKiosk) {
        console.log('Sending manual entry request:', { employee_id: id, event_id: window.currentEventId });
        fetch('http://127.0.0.1:5001/api/events/manual_entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                employee_id: id,
                event_id: window.currentEventId
            })
        })
        .then(async r => {
            if (!r.ok) {
                let errorMsg = `HTTP ${r.status}`;
                try {
                    const errorData = await r.json();
                    errorMsg = errorData.message || errorMsg;
                } catch (e) {}
                throw new Error(errorMsg);
            }
            return r.json();
        })
        .then(data => {
            console.log('Manual entry response:', data);
            if (data.success) {
                // Add a new row for both entry and exit (no overwriting)
                addNewLog(data.log, data.log_type);
                // Show overlay with correct message and color
                if (typeof showSuccessOverlay === 'function') {
                    const overlayType = data.log_type.toLowerCase();
                    showSuccessOverlay(overlayType, {
                        id: id,
                        name: data.log.name,
                        affiliation: data.log.dept
                    });
                }
                if (manualId === null) {
                    document.getElementById(idField).value = '';
                }
            } else {
                alert(data.message || "Failed to log attendance.");
                if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
            }
        })
        .catch(err => {
            console.error('Manual entry error:', err);
            alert(`Error: ${err.message}`);
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        });
    } else {
        // Fallback to general authentication (students, visitor, etc.)
        fetch('http://127.0.0.1:5001/admin/user/authentication', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        })
        .then(r => {
            if (!r.ok && r.status !== 404) throw new Error('Server error');
            return r.json();
        })
        .then(data => {
            if (data.success) {
                const logType = data.attendance_status.toLowerCase();
                const bannerType = logType === 'entry' ? 'in' : 'out';
                
                if (typeof showScanBanner === 'function') {
                    showScanBanner(bannerType, {
                        id:     id,
                        name:   data.name,
                        course: data.affiliation
                    });
                }
                
                if (typeof showSuccessOverlay === 'function') {
                    showSuccessOverlay(logType, {
                        id: id,
                        name: data.name,
                        affiliation: data.affiliation
                    });
                }
                if (manualId === null) {
                    document.getElementById(idField).value = '';
                }
            } else {
                alert(data.Invalid || "ID not found!");
                if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
            }
        })
        .catch(err => {
            console.error('General auth error:', err);
            alert("Connection error. Please try again.");
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        });
    }
}
```

---

## HTML Template

### kiosk_employee.html - Critical Setup Section

**Location:** `templates/kiosk_employee.html` (at the end, in `{% block extra_js %}`)

```html
{% block extra_js %}
<script src="{{ url_for('static', filename='js/kiosk.js') }}"></script>
<script>
    // CRITICAL: Pass event and instance IDs to JavaScript
    window.currentEventId = JSON.parse('{{ event_id|tojson|safe }}');
    window.currentInstanceId = JSON.parse('{{ instance_id|tojson|safe }}');

    // Live clock 
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateString = now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
        document.querySelectorAll('.live-clock').forEach(el => {
            el.innerHTML = `<i class="bi bi-clock me-2"></i>${timeString} <span class="ms-2 opacity-50">| ${dateString}</span>`;
        });
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Scanner variables
    let barcodeBuffer = "";
    let scanTimeout = null;

    document.addEventListener('keydown', function (e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
            return;
        }

        if (e.key === 'Enter') {
            if (barcodeBuffer.length > 3) {
                const feedText = document.getElementById('scanner-text');
                const frame = document.querySelector('.scanner-frame');
                frame.style.borderColor = '#F5DD00';
                frame.style.boxShadow = '0 0 30px rgba(245, 221, 0, 0.3)';
                feedText.innerText = "VERIFYING EMPLOYEE ID...";
                feedText.className = "position-absolute w-100 h-100 d-flex align-items-center justify-content-center text-gold font-monospace fw-bold scanning-text";

                setTimeout(() => {
                    submitManualEntry('employee', barcodeBuffer);
                    frame.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                    frame.style.boxShadow = 'none';
                    feedText.innerText = "[QR CAMERA FEED]";
                    feedText.className = "position-absolute w-100 h-100 d-flex align-items-center justify-content-center text-gold-50 small font-monospace";
                }, 500);
            }
            barcodeBuffer = "";
            if (scanTimeout) clearTimeout(scanTimeout);
        } else if (e.key.length === 1) {
            barcodeBuffer += e.key;
            if (scanTimeout) clearTimeout(scanTimeout);
            scanTimeout = setTimeout(() => { barcodeBuffer = ""; }, 50);
        }
    });

    // Load real attendance data if we have a valid instance_id
    if (window.currentInstanceId && window.currentInstanceId !== null) {
        loadEventAttendance(window.currentInstanceId);
    }
</script>
{% endblock %}
```

### kiosk_employee.html - Live Feed Container

```html
<!-- Right: Activity Feed -->
<div class="col-md-6">
    <div class="card-glass p-4 h-100 d-flex flex-column">
        <h4 class="h5 mb-4 d-flex align-items-center">
            <i class="bi bi-list-check text-gold me-2"></i>Live Logs
        </h4>
        <div class="vstack gap-3 flex-grow-1" id="liveLogsContainer" style="max-height: 400px; overflow-y: auto;">
            <!-- Logs will be inserted here by JavaScript -->
        </div>
    </div>
</div>
```

---

## Integration Checklist

When applying to another branch, ensure:

### ✅ Backend (app_extension.py)
- [ ] Add `from datetime import datetime` import
- [ ] Add connection helpers (`connect_db()`, `close_db()`)
- [ ] Import `Database` class from `db_connect.py`
- [ ] Copy entire `/api/events/manual_entry` endpoint
- [ ] Copy entire `/admin/instances/{id}/get-logs` endpoint
- [ ] Verify `database.py` has `init_db_pool()`, `connect_db()`, `close_db()`

### ✅ Frontend (static/js/kiosk.js)
- [ ] Replace entire file with provided code OR merge functions
- [ ] Ensure `#liveLogsContainer` exists in HTML
- [ ] Ensure `window.currentEventId` and `window.currentInstanceId` are set
- [ ] Test scanner barcode input detection

### ✅ HTML (templates/kiosk_employee.html)
- [ ] Include `#liveLogsContainer` div in template
- [ ] Add `window.currentEventId` and `window.currentInstanceId` assignments
- [ ] Call `loadEventAttendance(window.currentInstanceId)` on page load
- [ ] Include scanner event listener code

### ✅ Database Requirements
- [ ] Table: `event_log` (with `log_id`, `user_id`, `event_id`, `log_type`, `timestamp`)
- [ ] Table: `event_attendance` (with `first_in`, `last_out`, `status`, `remarks`)
- [ ] Table: `event_instances` (with `instance_id`, `event_id`, `event_date`)
- [ ] Table: `employees` (with `user_id`, `status`)
- [ ] Table: `general_log` (with `user_id`, `timestamp`, `log_type`, `gate`)
- [ ] Table: `departments` (with `department_name`)

### ✅ Routes in app.py
- [ ] Ensure `/kiosk/employee` route passes `event_id` and `instance_id` to template
- [ ] Verify template inheritance with `base.html`

---

## Testing Quick Start

```bash
# 1. Test manual entry endpoint
curl -X POST http://127.0.0.1:5001/api/events/manual_entry \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "2026-FAC-001", "event_id": 1}'

# 2. Test log fetch endpoint
curl http://127.0.0.1:5001/admin/instances/1/get-logs

# 3. Open kiosk employee page
# http://127.0.0.1:5000/kiosk/employee?instance_id=1

# 4. Test manual entry in UI
# Click "Enter ID Manually" button
# Type employee ID and press Enter
```

---

**Ready to deploy! Copy these code blocks to your target branch.** 🚀

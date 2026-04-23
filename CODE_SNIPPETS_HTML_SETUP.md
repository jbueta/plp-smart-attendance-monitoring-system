# HTML Template Snippets for kiosk_employee.html

## 1. Live Feed Container
# Add this to your kiosk_employee.html (Right side panel)

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
        <!-- Optional: Bulletin for context -->
        <div class="mt-3 pt-3 border-top border-secondary">
            <div class="d-flex align-items-center mb-1">
                <i class="bi bi-info-circle-fill text-info me-2"></i>
                <small class="fw-bold text-info">HR MEMO</small>
            </div>
            <p class="small text-white-50 mb-0">Real-time attendance tracking for {{ event_name }}</p>
        </div>
    </div>
</div>
```

---

## 2. JavaScript Block - Add to {% block extra_js %}

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

---

## 3. Manual Entry Modal

```html
<!-- Manual Entry Modal -->
<div class="modal fade" id="manualEntryModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content card-glass border-secondary">
            <div class="modal-header border-secondary">
                <h5 class="modal-title text-white">Manual Attendance Entry</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"
                    aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label for="manual-employee-id" class="form-label text-white-50">Employee ID Number</label>
                    <input type="text" class="form-control bg-transparent text-white border-secondary"
                        id="manual-employee-id" placeholder="e.g. 2026-FAC-001">
                </div>
                <div class="d-grid gap-2">
                    <button type="button" class="btn btn-primary-gold" onclick="submitManualEntry('employee')">Log
                        Attendance</button>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 4. Scanner Button

```html
<!-- Add this button to your scanner area -->
<div class="mt-4">
    <button class="btn btn-outline-light rounded-pill px-4 text-white-50 small" data-bs-toggle="modal"
        data-bs-target="#manualEntryModal">
        <i class="bi bi-keyboard me-2"></i>Enter ID Manually
    </button>
</div>
```

---

## Key Requirements

### In app.py - kiosk_employee route:
```python
@app.route('/kiosk/employee')
def kiosk_employee():
    session.pop('logged_in', None)
    instance_id = request.args.get('instance_id', type=int)
    events = helper_kiosk_live_events()
    selected_event = next((e for e in events if e['instance_id'] == instance_id), None)
    event_name = selected_event['name'] if selected_event else "General Attendance"
    event_id = selected_event.get('event_id') if selected_event else None
    
    return render_template('kiosk_employee.html',
                       event_name=event_name,
                       event_id=event_id,              # MUST PASS THIS
                       instance_id=instance_id,        # MUST PASS THIS
                       kiosk_data=MOCK_KIOSK_DATA)
```

## Database Requirements

Ensure these tables exist and have the required columns:

### event_log
- log_id (INT, PK)
- user_id (INT, FK)
- event_id (INT, FK)
- log_type (VARCHAR: Entry/Exit)
- timestamp (DATETIME)

### event_attendance
- attendance_id (INT, PK)
- instance_id (INT, FK)
- user_id (INT, FK)
- event_date (DATE)
- status (VARCHAR: Present/Late/Absent/Excused)
- first_in (DATETIME)
- last_out (DATETIME)
- remarks (TEXT)

### event_instances
- instance_id (INT, PK)
- event_id (INT, FK)
- event_date (DATE)
- status (VARCHAR: Scheduled/Completed/Cancelled)

### employees
- user_id (INT, FK)
- employee_id (VARCHAR, UNIQUE)
- employee_name (VARCHAR)
- department_id (INT, FK)
- status (VARCHAR: Inside/Outside)

### general_log
- log_id (INT, PK)
- user_id (INT, FK)
- timestamp (DATETIME)
- log_type (VARCHAR: Entry/Exit)
- gate (VARCHAR: Gate 1/Gate 2/etc)

---

## Testing Checklist

- [ ] Backend endpoints respond correctly (test with curl or Postman)
- [ ] Live feed container renders on kiosk_employee page
- [ ] Manual entry modal opens on button click
- [ ] Scanner barcode detection works (Enter key triggers submitManualEntry)
- [ ] Manual entry button submits data to /api/events/manual_entry
- [ ] New logs appear in live feed after submission
- [ ] Live feed maintains max 6 rows
- [ ] Error messages display correctly
- [ ] Page load calls loadEventAttendance() and populates initial logs

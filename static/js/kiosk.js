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
 * Add a new log to the live feed (for event kiosk)
 * @param {Object} log - Log object with name, dept, time, type, initials
 */
function addEventLogToFeed(log) {
    const feedContainer = document.querySelector('.vstack.gap-3');
    if (!feedContainer) return;

    // Check if employee already in feed (to update instead of duplicate)
    let existing = null;
    for (let child of feedContainer.children) {
        const nameElem = child.querySelector('h6');
        if (nameElem && nameElem.innerText === log.name) {
            existing = child;
            break;
        }
    }

    if (existing) {
        // Update existing row and move to top
        const timeBadge = existing.querySelector('.badge');
        if (timeBadge) {
            timeBadge.innerText = log.time;
            timeBadge.className = `badge bg-${log.type} bg-opacity-25 text-${log.type}`;
        }
        feedContainer.prepend(existing);
    } else {
        // Create new row
        const logDiv = document.createElement('div');
        logDiv.className = 'd-flex align-items-center p-3 rounded position-relative overflow-hidden';
        logDiv.style.background = 'rgba(255,255,255,0.03)';
        logDiv.innerHTML = `
            <div class="position-absolute start-0 top-0 bottom-0 bg-${log.type}" style="width: 4px;"></div>
            <div class="rounded-circle bg-white bg-opacity-10 p-2 me-3 text-white" style="width: 40px; height: 40px; display:grid; place-items:center;">${escapeHtml(log.initials)}</div>
            <div class="flex-grow-1">
                <h6 class="mb-0">${escapeHtml(log.name)}</h6>
                <small class="text-white-50">${escapeHtml(log.dept)}</small>
            </div>
            <span class="badge bg-${log.type} bg-opacity-25 text-${log.type}">${escapeHtml(log.time)}</span>
        `;
        feedContainer.prepend(logDiv);
    }

    // Keep only the latest 10 logs
    while (feedContainer.children.length > 10) {
        feedContainer.removeChild(feedContainer.lastChild);
    }
}

/**
 * Load attendance for a specific event instance and populate the live feed
 * @param {number} instanceId - Event instance ID
 */
function loadEventAttendance(instanceId) {
    console.log(`Loading attendance for instance ${instanceId}`);
    fetch(`http://127.0.0.1:5001/admin/instances/${instanceId}/get-attendance`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(attendanceList => {
            console.log('Attendance list:', attendanceList);
            const feedContainer = document.querySelector('.vstack.gap-3');
            if (!feedContainer) return;

            // Clear existing content (mock data)
            feedContainer.innerHTML = '';

            // Filter users who have checked in (first_in not null)
            const checkedIn = attendanceList.filter(a => a.first_in);
            // Sort by first_in descending (most recent first)
            checkedIn.sort((a, b) => new Date(b.first_in) - new Date(a.first_in));

            checkedIn.forEach(record => {
                const name = record.user_name || 'Unknown';
                const dept = record.department || 'N/A';
                const time = formatTime(record.first_in);
                const status = record.status;
                const type = status === 'Present' ? 'success' : (status === 'Late' ? 'warning' : 'secondary');
                const initials = getInitials(name);
                addEventLogToFeed({
                    name: name,
                    dept: dept,
                    time: time,
                    type: type,
                    initials: initials
                });
            });
        })
        .catch(err => console.error('Error loading attendance:', err));
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
                // Update feed only for entry (arrival)
                if (data.log_type === 'Entry') {
                    addEventLogToFeed(data.log);
                }
                // Show overlay with correct message and color
                if (typeof showSuccessOverlay === 'function') {
                    // Convert log_type to lowercase for overlay function
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
            
                if (typeof appendToLiveFeed === 'function') {
                appendToLiveFeed(data.name, data.affiliation, logType);
            }

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
        document.getElementById(idField).value = '';
    }
}

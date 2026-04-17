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
 * This loads initial entry logs only (since backend returns only first_in for each user).
 * To also show exit logs on load, you would need a separate endpoint for general_log.
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

                appendToLiveFeed(data.name, data.affiliation, logType);
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

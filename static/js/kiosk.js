/* Kiosk functionality - Student and Employee */

const frontendBaseUrl = window.location.origin;
const backendProxyBaseUrl = `${frontendBaseUrl}/api/backend`;

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
    return String(str).replace(/[&<>"']/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        if (m === '"') return '&quot;';
        if (m === "'") return '&#39;';
        return m;
    });
}

function getKioskAuthErrorMessage(data, fallback = 'ID not found!') {
    if (!data || typeof data !== 'object') return fallback;
    return data.message || data.Invalid || fallback;
}

function normalizeManualKioskId(value, type) {
    const normalized = String(value || '').trim().toUpperCase();
    
    if (normalized.startsWith('V') || normalized.startsWith('T') || normalized.startsWith('VT')) {
        let nums = normalized.replace(/[^0-9]/g, '');
        if (nums.length > 0) {
            return 'VT-' + nums.substring(0, 5);
        }
        
        if (normalized.includes('-')) {
            return 'VT-';
        }
        return normalized.replace(/[^A-Z]/g, '');
    }
    
    if (normalized.includes('-')) {
        let parts = normalized.replace(/[^0-9-]/g, '').split('-');
        if (parts.length > 1) {
            return parts[0].substring(0, 2) + '-' + parts[1].substring(0, 5);
        }
    }
    
    let digits = normalized.replace(/[^0-9]/g, '');
    if (digits.length > 5) {
        return digits.substring(0, 2) + '-' + digits.substring(2, 7);
    }
    
    return digits;
}

function isGeneralKioskScanId(value) {
    return /^(?:[0-9]{2}-[0-9]{5}|VT-[0-9]{5})$/.test(normalizeManualKioskId(value, 'student'));
}

function extractGeneralKioskQrId(rawText) {
    const scannedText = String(rawText || '').trim();
    const bracketMatch = scannedText.match(/(.*?)\[(.*?)\](.*)/s);
    const candidateId = bracketMatch ? bracketMatch[2].trim() : scannedText;
    const normalizedId = normalizeManualKioskId(candidateId, 'student');

    return isGeneralKioskScanId(normalizedId) ? normalizedId : "";
}

function clearManualEntryInput(idField) {
    const input = document.getElementById(idField);
    if (input) {
        input.value = "";
        input.setCustomValidity("");
    }
}

function initGeneralManualIdFormatting() {
    document.querySelectorAll('#manual-student-id, #manual-employee-id').forEach(input => {
        input.addEventListener('input', () => {
            input.value = normalizeManualKioskId(input.value, 'student');
        });

        input.addEventListener('keydown', event => {
            if (event.key !== 'Enter') return;

            event.preventDefault();
            event.stopPropagation();
            
            // Determine type based on input ID
            const inputType = input.id === 'manual-employee-id' ? 'employee' : 'student';
            submitManualEntry(inputType);
        });
    });

    const manualEntryModal = document.getElementById('manualEntryModal');
    if (manualEntryModal) {
        manualEntryModal.addEventListener('shown.bs.modal', () => {
            const input = document.getElementById('manual-student-id') || document.getElementById('manual-employee-id');
            if (input) {
                input.focus({ preventScroll: true });
                input.select();
            }
        });

        manualEntryModal.addEventListener('hidden.bs.modal', () => {
            clearManualEntryInput('manual-student-id');
            clearManualEntryInput('manual-employee-id');
        });
    }

    // Globally enforce focus removal after any modal closes so that
    // physical keyboard / scanner 'Enter' keys don't accidentally re-trigger the modal.
    document.addEventListener('hidden.bs.modal', () => {
        setTimeout(() => {
            if (document.activeElement && document.activeElement !== document.body) {
                document.activeElement.blur();
            }
        }, 50);
    });
}

/**
 * Parse a fetch response without losing backend validation messages on non-2xx replies.
 */
async function parseJsonResponse(response, fallbackMessage = 'Server error') {
    const data = await response.json().catch(() => ({}));

    if (!response.ok && !data.message && !data.error && !data.Invalid) {
        throw new Error(fallbackMessage);
    }

    return data;
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
 * Shared live feed for the student entrance and exit kiosks.
 */
const liveFeedLimit = 6;
let liveFeedRefreshTimer = null;
let liveFeedRefreshInFlight = false;
let liveFeedLastLocalAppendAt = 0;

function normalizeLiveFeedType(type) {
    const normalized = String(type || '').toLowerCase();
    return normalized === 'out' || normalized === 'exit' || normalized === 'time out' ? 'out' : 'in';
}

function formatLiveFeedTime(value) {
    if (!value) {
        return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    const rawValue = String(value);
    const parsed = new Date(rawValue);
    if (!Number.isNaN(parsed.getTime())) {
        return parsed.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    return rawValue;
}

function buildLiveFeedItem(log) {
    log = log || {};
    const type = normalizeLiveFeedType(log.type || log.logType || log.attendance_status);
    const isEntry = type === 'in';
    const iconBg = isEntry ? 'bg-success text-success' : 'bg-secondary text-white';
    const iconClass = isEntry ? 'bi-check-lg' : 'bi-arrow-right';
    const badgeClass = isEntry ? 'bg-success text-success' : 'bg-secondary text-white';
    const badgeText = isEntry ? 'TIME IN' : 'TIME OUT';
    const name = log.name || 'Unknown';
    const affiliation = log.course || log.affiliation || log.department || 'N/A';
    const time = formatLiveFeedTime(log.time || log.created_at || log.timestamp);

    return `
        <div class="d-flex align-items-center p-2 rounded live-feed-item" style="background: rgba(255,255,255,0.03);">
            <div class="rounded-circle ${iconBg} bg-opacity-25 p-2 me-3">
                <i class="bi ${iconClass}"></i>
            </div>
            <div class="flex-grow-1 lh-1">
                <h6 class="mb-0 small">${escapeHtml(name)}</h6>
                <small class="text-white-50" style="font-size: 0.75rem">${escapeHtml(affiliation)}</small>
            </div>
            <div class="text-end">
                <div class="badge ${badgeClass} bg-opacity-10 mb-1">${badgeText}</div>
                <div class="font-monospace small text-white-50">${escapeHtml(time)}</div>
            </div>
        </div>
    `;
}

function renderLiveFeed(logs) {
    const feedContainer = document.getElementById('live-feed-list');
    if (!feedContainer) return;

    const feedLogs = Array.isArray(logs) ? logs : [];
    feedContainer.innerHTML = feedLogs
        .slice(0, liveFeedLimit)
        .map(buildLiveFeedItem)
        .join('');
}

async function refreshLiveFeed() {
    const feedContainer = document.getElementById('live-feed-list');
    if (!feedContainer || liveFeedRefreshInFlight) return;

    const requestStartedAt = Date.now();
    liveFeedRefreshInFlight = true;
    try {
        const response = await fetch(`/api/kiosk/live-feed?limit=${liveFeedLimit}`, {
            headers: { Accept: 'application/json' },
            cache: 'no-store'
        });
        const payload = await parseJsonResponse(response, 'Unable to refresh live feed');
        if (payload.success) {
            if (requestStartedAt < liveFeedLastLocalAppendAt) {
                window.setTimeout(refreshLiveFeed, 300);
                return;
            }
            renderLiveFeed(payload.logs || []);
        }
    } catch (error) {
        console.warn('Live feed refresh failed:', error);
    } finally {
        liveFeedRefreshInFlight = false;
    }
}

function initLiveFeedRefresh() {
    if (!document.getElementById('live-feed-list') || liveFeedRefreshTimer) return;

    refreshLiveFeed();
    liveFeedRefreshTimer = window.setInterval(refreshLiveFeed, 4000);
}

/**
 * Add a log entry to the live feed for general kiosk (entrance/exit)
 * @param {string} name - participant name
 * @param {string} affiliation - department/course affiliation
 * @param {string} logType - 'entry', 'exit', 'Entry', 'Exit'
 */
function appendToLiveFeed(name, affiliation, logType) {
    const feedContainer = document.getElementById('live-feed-list');
    if (!feedContainer) return;

    liveFeedLastLocalAppendAt = Date.now();
    feedContainer.insertAdjacentHTML('afterbegin', buildLiveFeedItem({
        type: normalizeLiveFeedType(logType),
        name,
        course: affiliation,
        time: new Date()
    }));

    // Keep only the latest 6 logs
    while (feedContainer.children.length > liveFeedLimit) {
        feedContainer.lastElementChild.remove();
    }

    window.setTimeout(refreshLiveFeed, 800);
}

window.appendToLiveFeed = appendToLiveFeed;
window.refreshLiveFeed = refreshLiveFeed;
window.renderLiveFeed = renderLiveFeed;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initLiveFeedRefresh();
        initGeneralManualIdFormatting();
    });
} else {
    initLiveFeedRefresh();
    initGeneralManualIdFormatting();
}

/**
 * Load attendance for a specific event instance and populate the live feed
 * This loads initial entry logs only (since backend returns only first_in for each user).
 * To also show exit logs on load, you would need a separate endpoint for general_log.
 */
function loadEventAttendance(instanceId) {
    console.log(`Loading event logs for instance ${instanceId}`);
    fetch(`${backendProxyBaseUrl}/admin/instances/${instanceId}/logs`)
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
    const inputElement = manualId === null ? document.getElementById(idField) : null;
    const rawId = manualId !== null ? manualId : (inputElement ? inputElement.value : "");
    const id = type === 'employee'
        ? normalizeManualKioskId(rawId, type)
        : (extractGeneralKioskQrId(rawId) || normalizeManualKioskId(rawId, type));

    if (inputElement) {
        inputElement.value = id;
    }
    
    if (!id) {
        window.showSystemFeedback("Please enter an ID", 'error');
        return;
    }


    if (inputElement && !inputElement.checkValidity()) {
        inputElement.reportValidity();
        return;
    }
    
    const modalEl = document.getElementById('manualEntryModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
    if (manualId === null) {
        clearManualEntryInput(idField);
    }
    
    // Determine if this is an event kiosk (employee event page has currentEventId)
    const isEventKiosk = type === 'employee' && window.currentEventId && window.currentEventId !== null;
    
    if (isEventKiosk) {
        console.log('Sending manual entry request:', { employee_id: id, event_id: window.currentEventId });
        fetch(`${backendProxyBaseUrl}/events/manual-entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                employee_id: id,
                event_id: window.currentEventId
            })
        })
        .then(r => parseJsonResponse(r, 'Failed to contact the event attendance service.'))
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
                // [ANNOUNCEMENT FEATURE] - Update context for targeted/departmental bulletins
                window.lastScannedId = id;
                window.currentDept = data.log ? data.log.dept : null;
                if (typeof window.fetchBulletins === 'function') window.fetchBulletins();
                if (typeof window.fetchActiveAlerts === 'function') window.fetchActiveAlerts();

            } else {
                window.showSystemFeedback(data.message || "Failed to log attendance.", 'error');
                if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
            }

        })
        .catch(err => {
            console.error('Manual entry error:', err);
            window.showSystemFeedback(`Error: ${err.message}`, 'error');
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        });

    } else {
        // Fallback to general authentication (students, visitor, etc.)
        const requestedLogType = window.GENERAL_KIOSK_ACTION || null;
        fetch(`${backendProxyBaseUrl}/admin/user/authentication`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id,
                requested_log_type: requestedLogType
            })
        })
        .then(r => parseJsonResponse(r, 'Server error'))
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
                        affiliation: data.affiliation,
                        // pass through student_type when available so overlay can display Regular/Irregular
                        student_type: data.student_type || data.status
                    });
                }
                // [ANNOUNCEMENT FEATURE] - Update context for targeted/departmental bulletins
                window.lastScannedId = id;
                window.currentDept = data.affiliation;
                if (typeof window.fetchBulletins === 'function') window.fetchBulletins();
                if (typeof window.fetchActiveAlerts === 'function') window.fetchActiveAlerts();

                appendToLiveFeed(data.name, data.affiliation, logType);
            } else {
                window.showSystemFeedback(getKioskAuthErrorMessage(data, 'ID not found!'), 'error');
                if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
            }

        })
        .catch(err => {
            console.error('General auth error:', err);
            const message = err.message
                ? `Connection error: ${err.message}. Please try again.`
                : 'Connection error. Please try again.';
            window.showSystemFeedback(message, 'error');
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        });

    }
}

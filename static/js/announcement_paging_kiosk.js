// [ANNOUNCEMENT FEATURE] - Paging/Alert Logic for Kiosks
let activeAlertId = null;

function fetchActiveAlerts() {
    const targetId = window.lastScannedId || null;
    const targetDept = window.currentDept || null;
    const targetEvent = window.currentEventName || (document.title.includes('Entrance') ? 'General Attendance' : null);
    
    const params = new URLSearchParams({
        target_id: targetId,
        target_dept: targetDept,
        target_event: targetEvent
    });

    fetch(`/api/kiosk/alerts?${params.toString()}`)
        .then(res => res.json())
        .then(res => {
            if (res.success && res.alerts.length > 0) {
                const alert = res.alerts[0];
                if (alert.alert_id !== activeAlertId) {
                    displayAlertOverlay(alert);
                    activeAlertId = alert.alert_id;
                }
            } else {
                hideAlertOverlay();
                activeAlertId = null;
            }
        })
        .catch(err => console.error('Error fetching alerts:', err));
}

function displayAlertOverlay(alert) {
    let overlay = document.getElementById('paging-alert-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'paging-alert-overlay';
        overlay.className = 'position-fixed top-0 start-0 w-100 p-3 z-3 shadow-lg alert-slide-down';
        overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
        overlay.style.zIndex = '9999';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <div class="container d-flex align-items-center justify-content-between text-white">
            <div>
                <span class="badge bg-white text-danger me-2">URGENT PAGING</span>
                <strong>${alert.from_source}:</strong> ${alert.message}
            </div>
            <button class="btn btn-sm btn-outline-light" onclick="this.parentElement.parentElement.remove()">Dismiss</button>
        </div>
    `;
    overlay.style.display = 'block';
}

function hideAlertOverlay() {
    const overlay = document.getElementById('paging-alert-overlay');
    if (overlay) overlay.style.display = 'none';
}

// Expose to window for triggering after scan
window.fetchActiveAlerts = fetchActiveAlerts;

// High frequency polling for alerts (e.g., every 15 seconds)
fetchActiveAlerts();
setInterval(fetchActiveAlerts, 15000);

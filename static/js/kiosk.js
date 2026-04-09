/* Kiosk functionality - Student and Employee */

/**
 * Handle manual ID entry for both students and employees
 * @param {string} type - 'student' or 'employee'
 */
function submitManualEntry(type) {
    const idField = type === 'employee' ? 'manual-employee-id' : 'manual-student-id';
    const id = document.getElementById(idField).value.trim();

    if (!id) {
        alert("Please enter an ID");
        return;
    }

    const modalEl = document.getElementById('manualEntryModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

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

        } else {
            alert(data.Invalid || "ID not found!");
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        }
    })
    .catch(err => {
        console.error(err);
        alert("Connection error. Please try again.");
        if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
    });

    document.getElementById(idField).value = '';
}

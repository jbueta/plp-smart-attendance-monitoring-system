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
    .then(r => r.json())
    .then(data => {
        if (data.status === 'found') {
            const bannerType = data.log_type.toLowerCase() === 'entry' ? 'in' : 'out';

            if (typeof showScanBanner === 'function') {
                showScanBanner(bannerType, {
                    id:     id,
                    name:   data.name,
                    course: data.affiliation
                });
            }

            if (typeof showSuccessOverlay === 'function') {
                showSuccessOverlay(data.log_type, { 
                    id: id, 
                    name: data.name,
                    affiliation: data.affiliation
                });
            }

        } else {
            if (typeof showScanBanner === 'function') {
                showScanBanner('error', { id: id });
            }
        }
    })
    .catch(() => {
        if (typeof showScanBanner === 'function') {
            showScanBanner('error', { id: id });
        }
    });

    document.getElementById(idField).value = '';
}
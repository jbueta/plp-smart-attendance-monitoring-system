/* Kiosk functionality - Student and Employee */

/**
 * Handle manual ID entry for both students and employees
 * @param {string} type - 'entry', 'exit', or 'employee'
 */
function submitManualEntry(type) {
    const idField = type === 'employee' ? 'manual-employee-id' : 'manual-student-id';
    const id = document.getElementById(idField).value.trim();

    if (!id) {
        alert("Please enter an ID");
        return;
    }

    // Close Modal
    const modalEl = document.getElementById('manualEntryModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

    // Fetch student status first, then show appropriate banner
    fetch('/api/check_student_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: id })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'found') {
            const bannerType = type === 'entry' ? 'in' : 'out';

            // Show live feed banner (defined in kiosk_student.html)
            if (typeof showScanBanner === 'function') {
                showScanBanner(bannerType, {
                    id:     id,
                    name:   data.name,
                    course: data.course
                });
            }

            // Show full-screen overlay (defined in main.js)
            if (typeof showSuccessOverlay === 'function') {
                showSuccessOverlay(type, { id: id, name: data.name });
            }

        } else {
            // ID not found — show red failed banner
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
/* Kiosk functionality - Student and Employee */

/**
 * Handle manual ID entry for both students and employees
 * @param {string} type - 'entry', 'exit', or 'employee'
 */
function submitManualEntry(type) {
    const idField = type === 'employee' ? 'manual-employee-id' : 'manual-student-id';
    const id = document.getElementById(idField).value;

    if (!id) {
        alert("Please enter an ID");
        return;
    }

    // Close Modal
    const modalEl = document.getElementById('manualEntryModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

    // Trigger Success Overlay with Manual Data
    // showSuccessOverlay is defined in main.js
    if (typeof showSuccessOverlay === 'function') {
        showSuccessOverlay(type, {
            id: id,
            name: "Manual Entry" // In a real app, we'd fetch the name first
        });
    }

    document.getElementById(idField).value = '';
}

/**
 * Check student status via API
 */
async function checkStudentStatus() {
    const id = document.getElementById('search-id').value;
    const resultDiv = document.getElementById('search-result');

    if (!id) return;

    resultDiv.classList.remove('d-none');
    resultDiv.innerHTML = '<div class="text-white-50"><span class="spinner-border spinner-border-sm me-2"></span>Checking...</div>';

    try {
        const response = await fetch('/api/check_student_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: id })
        });
        const data = await response.json();

        if (data.status === 'found') {
            let badgeClass = data.attendance_status === 'TIMED IN' ? 'bg-success' : 'bg-secondary';
            resultDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">
                    <h6 class="text-white mb-0">${data.name}</h6>
                    <small class="text-white-50">${data.course}</small>
                </div>
                <span class="badge ${badgeClass}">${data.attendance_status}</span>
            </div>
        `;
        } else {
            resultDiv.innerHTML = `<div class="text-danger small"><i class="bi bi-x-circle me-1"></i>Student not found</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="text-danger small">Error connecting to server</div>`;
    }
}

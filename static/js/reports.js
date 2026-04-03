/* Reports management functionality */

function generateReport() {
    const type = document.getElementById('report-type').value;
    const start = document.getElementById('report-start').value;
    const end = document.getElementById('report-end').value;

    // Validation: Start Date is always required
    if (!start) {
        alert("Please select a Start Date (From).");
        return;
    }

    // Validation: Date Range Order (only if End Date is provided)
    if (end && start > end) {
        alert("Start Date cannot be after End Date.");
        return;
    }

    // Determine Report Mode based on End Date
    let rangeText = "";
    let modeText = "";

    if (!end || start === end) {
        modeText = "Single Date Report";
        rangeText = `Date: ${start}`;
    } else {
        modeText = "Date Range Report";
        rangeText = `Range: ${start} to ${end}`;
    }

    const btn = document.querySelector('.btn-primary-gold');
    const originalText = btn.innerHTML;

    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
    btn.disabled = true;

    setTimeout(() => {
        window.open('/reports/sample?autoprint=true', '_blank');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 1500);
}

document.addEventListener('DOMContentLoaded', function () {
    const categorySelect = document.getElementById('report-category');
    const reportTypeSelect = document.getElementById('report-type');
    const filterLabel = document.getElementById('filter-label');
    const filterSelect = document.getElementById('report-filter');

    // Stored options for each category
    const options = {
        general: [
            "Student Entry/Exit Logs",
            "Daily Traffic Analysis"
        ],
        visitor: [
            "Daily Visitor Log",
            "Visitor Purpose Summary"
        ],
        event: [
            "Employee Attendance (Flag Ceremony)",
            "Employee Attendance (General Assembly)"
        ],
        violation: [
            "Curfew Violations Report",
            "Overstaying Vehicles"
        ]
    };

    function updateOptions() {
        if (!categorySelect || !reportTypeSelect) return;
        const category = categorySelect.value;

        reportTypeSelect.innerHTML = '';
        options[category].forEach(opt => {
            const el = document.createElement('option');
            el.textContent = opt;
            el.value = opt;
            reportTypeSelect.appendChild(el);
        });

        if (!filterLabel || !filterSelect) return;

        // Tweak the filter label
        if (category === 'visitor') {
            filterLabel.textContent = "Visitor Purpose";
            filterSelect.innerHTML = '<option>All Purposes</option><option>Official Business</option><option>Delivery</option><option>Other</option>';
        } else if (category === 'violation') {
            filterLabel.textContent = "Status";
            filterSelect.innerHTML = '<option>All</option><option>Resolved</option><option>Pending</option>';
        } else {
            filterLabel.textContent = "Department / Filter";
            filterSelect.innerHTML = '<option>All Departments</option><option>College of Engineering</option><option>College of Nursing</option>';
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', updateOptions);
    }


    // =====================================================================================
    // BACKEND FUCTIONALITY
    // =====================================================================================

    async function authenticateRequest(studentId) {
        const url = "http://localhost:5000/authenticate";
        const data = { student_id: studentId,
                       date: new Date().toISOString().split('T')[0],
                       time: new Date().toISOString().split('T')[1].split('.')[0],
                       ip_address: "127.0.0.1"
         };
        const options = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        };

        try {
            const response = await fetch(url, options);
            const result = await response.json();
            return result;
        } catch (error) {
            console.error(error);
        }
    }

});

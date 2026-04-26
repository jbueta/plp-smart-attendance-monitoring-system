/* Main.js - PLP Smart System Interactions */

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initAnimations();
    initInstanceGeneratorToast();
    populateRandomStudentRecords();
});

function initInstanceGeneratorToast() {
    const toast = document.getElementById('instance-generator-toast');
    if (!toast) return;

    const title = document.getElementById('instance-generator-title');
    const message = document.getElementById('instance-generator-message');
    const spinner = document.getElementById('instance-generator-spinner');
    const successIcon = document.getElementById('instance-generator-success');
    const errorIcon = document.getElementById('instance-generator-error');
    const backendUrl = window.APP_CONFIG?.backendApiUrl || 'http://127.0.0.1:5001';
    const statusUrl = `${backendUrl}/admin/generate-daily-instances/status`;
    let lastShownFinishedAt = sessionStorage.getItem('instanceGeneratorLastShown') || '';
    let hideTimer = null;

    function showToast(mode, heading, details) {
        title.textContent = heading;
        message.textContent = details;
        spinner.classList.toggle('d-none', mode !== 'running');
        successIcon.classList.toggle('d-none', mode !== 'success');
        errorIcon.classList.toggle('d-none', mode !== 'error');
        toast.classList.remove('d-none');

        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }

        if (mode !== 'running') {
            hideTimer = setTimeout(() => toast.classList.add('d-none'), 9000);
        }
    }

    function hideToast() {
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
        toast.classList.add('d-none');
    }

    function formatResult(result) {
        if (!result) return 'No run details available yet.';
        const created = Number(result.created || 0);
        const existing = Number(result.existing || 0);
        const failed = Number(result.failed || 0);
        const range = result.date_range ? ` ${result.date_range}` : '';
        return `Created ${created}, already existing ${existing}, failed ${failed}.${range}`;
    }

    async function pollStatus() {
        try {
            const response = await fetch(statusUrl, { cache: 'no-store' });
            if (!response.ok) {
                hideToast();
                return;
            }

            const payload = await response.json();
            const job = payload.job || {};
            if (job.running) {
                showToast('running', 'Generating event instances', 'Preparing upcoming event attendance records...');
                return;
            }

            if (job.last_finished_at && job.last_finished_at !== lastShownFinishedAt) {
                lastShownFinishedAt = job.last_finished_at;
                sessionStorage.setItem('instanceGeneratorLastShown', lastShownFinishedAt);

                if (job.last_error) {
                    showToast('error', 'Event generation failed', job.last_error);
                } else {
                    showToast('success', 'Event instances ready', formatResult(job.last_result));
                }
            }
        } catch (error) {
            hideToast();
        }
    }

    pollStatus();
    setInterval(pollStatus, 8000);
}

// --- Real-time Clock ---
function initClock() {
    const clockElements = document.querySelectorAll('.live-clock');
    const heroClock = document.getElementById('hero-clock');

    if (clockElements.length === 0 && !heroClock) return;

    function updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateString = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

        // Default for standard clocks
        clockElements.forEach(el => {
            el.innerHTML = `<i class="bi bi-clock me-1 text-gold"></i> ${timeString} <span class="mx-2 opacity-50">|</span> <i class="bi bi-calendar3 me-1 text-gold"></i> ${dateString}`;
        });

        if (heroClock) {
            heroClock.innerHTML = `
                <div class="h5 text-gold mb-0 text-uppercase letter-spacing-2 opacity-75">${dateString}</div>
                <div class="display-4 fw-bold text-white text-shadow-lg" style="line-height: 1;">${timeString}</div>
            `;
        }
    }

    updateTime();
    setInterval(updateTime, 1000);
}

// --- Kiosk Logic (State Machine) ---
let isScanning = false;
let scanState = {}; 

function showSuccessOverlay(type, manualData = null) {
    const overlay = document.getElementById('scan-overlay');
    const overlayTitle = document.getElementById('scan-title');
    const overlayName = document.getElementById('scan-name');
    const overlayId = document.getElementById('scan-id');
    const overlayStatus = document.getElementById('scan-status');
    const overlayRing = document.getElementById('scan-ring');

    // Randomize Data (if not manual)
    const names = ["Juan Dela Cruz", "Maria Clara", "Jose Rizal", "Andres Bonifacio"];
    const depts = ["College of Computer Studies", "College of Nursing", "College of Engineering", "College of Arts"];
    let randIndex = Math.floor(Math.random() * names.length);

    let name = names[randIndex];
    let dept = depts[randIndex];
    let id = "2026-00" + Math.floor(Math.random() * 9000 + 1000);

    // Override with Manual Data if provided
    if (manualData) {
        name = manualData.name || "Unknown User";
        id = manualData.id || "N/A";
        // Dept is mocked for manual entry for now
        dept = manualData.affiliation
    }

    overlayName.innerText = name;
    overlayId.innerText = "ID: " + id;

    if (type === 'entry') {
        overlayTitle.innerText = "ACCESS GRANTED";
        overlayTitle.className = "display-6 fw-bold text-success mb-2";
        overlayStatus.innerText = "ENTRY RECORDED • " + dept;
        overlayRing.className = "rounded-circle border border-5 border-success p-1 mb-3";
    } else if (type === 'employee') {
        overlayTitle.innerText = "ATTENDANCE LOGGED";
        overlayTitle.className = "display-6 fw-bold text-gold mb-2";
        overlayStatus.innerText = "FLAG CEREMONY: PRESENT";
        overlayRing.className = "rounded-circle border border-5 border-warning p-1 mb-3";
    } else if (type === 'employee-out') {
        overlayTitle.innerText = "LOGGED OUT";
        overlayTitle.className = "display-6 fw-bold text-info mb-2";
        overlayStatus.innerText = "TIME OUT RECORDED";
        overlayRing.className = "rounded-circle border border-5 border-info p-1 mb-3";
    } else {
        overlayTitle.innerText = "EXIT RECORDED";
        overlayTitle.className = "display-6 fw-bold text-info mb-2";
        overlayStatus.innerText = "SEE YOU TOMORROW • " + dept;
        overlayRing.className = "rounded-circle border border-5 border-info p-1 mb-3";
    }

    overlay.classList.remove('d-none');
    overlay.classList.add('d-flex');

    setTimeout(() => {
        overlay.classList.remove('d-flex');
        overlay.classList.add('d-none');
    }, 1500);
}

function initAnimations() {
    const cards = document.querySelectorAll('.transition-hover');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            // subtle effect
        });
    });
}

function populateRandomStudentRecords() {
    const tableBody = document.getElementById('studentTableBody');
    if (!tableBody) return;

    const collegeOptions = [
        'College of Education',
        'College of Business and Accountancy',
        'College of Nursing',
        'College of Engineering',
        'College of Computer Studies',
        'College of International Hospitality Management'
    ];

    const randomNames = [
        'Ana Marie Santos',
        'Carlos Miguel dela Cruz',
        'Isabela Reyes',
        'Miguel Antonio Garcia',
        'Riza Lorena Aquino',
        'Jomar Peña',
        'Lara Mae Villar',
        'Noel Gabriel Ramos',
        'Karen Faith Soriano',
        'Ethan Mark Bautista',
        'Janella Cruz',
        'Marco Angelo dela Rosa',
        'Sofia Anne Navarro',
        'David Lee Tan',
        'Aiza Mae Lopez'
    ];

    const existingRows = tableBody.querySelectorAll('.student-row').length;
    const rowsToAdd = Math.max(0, 10 - existingRows);

    // Remove empty placeholder when adding sample records
    const emptyRow = document.getElementById('emptyRow');
    if (emptyRow && rowsToAdd > 0) {
        emptyRow.remove();
    }

    for (let i = 0; i < rowsToAdd; i++) {
        const name = randomNames[Math.floor(Math.random() * randomNames.length)];
        const college = collegeOptions[Math.floor(Math.random() * collegeOptions.length)];
        const id = `23-00${Math.floor(Math.random() * 900 + 100)}${Math.floor(Math.random() * 10)}`;
        const timeIn = `${Math.floor(Math.random() * 3 + 7).toString().padStart(2, '0')}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`;
        const timeOut = `${Math.floor(Math.random() * 3 + 11).toString().padStart(2, '0')}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`;
        const statusActive = Math.random() > 0.5;
        const status = statusActive ? 'Checked In' : 'Checked Out';
        const statusClass = statusActive ? 'success' : 'danger';

        const row = document.createElement('tr');
        row.className = 'student-row';
        row.dataset.id = id.toLowerCase();
        row.dataset.name = name.toLowerCase();
        row.dataset.course = college;
        row.dataset.date = '';
        row.innerHTML = `
            <td class="font-monospace text-white-50 ps-4">${id}</td>
            <td class="fw-bold text-white">${name}</td>
            <td class="text-white-50">${college}</td>
            <td class="text-success font-monospace small">${timeIn}</td>
            <td class="text-danger font-monospace small">${timeOut}</td>
            <td class="text-end" style="padding-right: 3rem;">
                <span class="badge bg-${statusClass} bg-opacity-25 border border-${statusClass} text-${statusClass} rounded-pill px-3">
                    ${status}
                </span>
            </td>
            <td class="text-center align-middle" style="width: 80px;">
                <div class="dropdown h-100 d-flex align-items-center justify-content-center">
                    <button class="btn btn-sm btn-outline-light p-0 border-0 d-flex align-items-center justify-content-center fs-4" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        &hellip;
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end shadow-sm student-action-menu">
                        <li><button type="button" class="dropdown-item edit-student text-white" data-id="${id}">Edit</button></li>
                        <li><button type="button" class="dropdown-item text-danger delete-student" data-id="${id}">Delete</button></li>
                    </ul>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    }
}

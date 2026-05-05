/* Kiosk functionality - Student and Employee */

function showVerificationOverlay(state, data = {}) {
    console.log(data)
    let overlay = document.getElementById('modern-verify-overlay');
    
    if (!overlay) {
        // Create overlay if it doesn't exist
        const overlayHtml = `
        <style>
            .kiosk-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.85);
                z-index: 10000;
                opacity: 0; pointer-events: none;
                display: flex; justify-content: center; align-items: center;
                transition: opacity 0.25s ease;
            }
            
            .kiosk-card {
                width: fit-content; /* Allows card to expand based on content */
                min-width: 580px; /* Maintains base size for shorter names */
                max-width: 95vw;
                background-color: #1a2724;
                border-radius: 12px;
                overflow: hidden;
                /* Base shadow and transparent border for transitions */
                box-shadow: 0 15px 40px rgba(0,0,0,0.8);
                border: 3px solid transparent; 
                transform: translateY(20px);
                transition: transform 0.25s ease, box-shadow 0.3s ease, border-color 0.3s ease;
                display: flex; flex-direction: column;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            /* Glowing shadows and colored borders based on card state */
            .kiosk-card-granted { 
                box-shadow: 0 15px 40px rgba(0,0,0,0.8), 0 0 45px rgba(32, 141, 91, 0.55); 
                border-color: #208d5b; 
            }
            .kiosk-card-denied { 
                box-shadow: 0 15px 40px rgba(0,0,0,0.8), 0 0 45px rgba(220, 53, 69, 0.55); 
                border-color: #dc3545; 
            }
            .kiosk-card-invalid { 
                box-shadow: 0 15px 40px rgba(0,0,0,0.8), 0 0 45px rgba(255, 193, 7, 0.45); 
                border-color: #ffc107; 
            }
            .kiosk-card-exit { 
                box-shadow: 0 15px 40px rgba(0,0,0,0.8), 0 0 45px rgba(13, 202, 240, 0.55); 
                border-color: #0dcaf0; 
            }

            .kiosk-header {
                width: 100%;
                padding: 0 24px;
                line-height: 1.1; 
                text-align: center;
                font-size: 3.8rem; 
                font-weight: 800;
                letter-spacing: 1.5px;
                color: #ffffff;
                text-transform: uppercase;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                white-space: nowrap; /* Prevents header from double-lining */
            }
            .kiosk-header-granted { background-color: #208d5b; }
            .kiosk-header-denied { background-color: #dc3545; }
            .kiosk-header-invalid { background-color: #ffc107; color: #000; text-shadow: none; }
            .kiosk-header-exit { background-color: #0dcaf0; color: #000; text-shadow: none; }

            .kiosk-body {
                display: flex;
                padding: 35px 40px;
                color: #ffffff;
            }
            
            .kiosk-left {
                display: flex;
                justify-content: center;
                align-items: center;
                border-right: 1px solid rgba(255, 255, 255, 0.15);
                padding-right: 35px;
                margin-right: 35px;
            }
            
            .kiosk-right {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .kiosk-icon-wrapper {
                width: 110px;
                height: 110px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 4.5rem;
            }
            .kiosk-icon-granted { background-color: #276342; color: #68d391; }
            .kiosk-icon-denied { background-color: rgba(220, 53, 69, 0.2); color: #dc3545; }
            .kiosk-icon-invalid { background-color: rgba(255, 193, 7, 0.2); color: #ffc107; }
            .kiosk-icon-exit { background-color: rgba(13, 202, 240, 0.2); color: #0dcaf0; }

            .kiosk-detail-group {
                margin-bottom: 18px;
            }
            .kiosk-detail-group:last-child {
                margin-bottom: 0;
            }
            .kiosk-detail-row {
                display: flex;
                gap: 40px;
                margin-bottom: 18px;
            }
            .kiosk-detail-row .kiosk-detail-group {
                margin-bottom: 0;
            }
            
            .kiosk-label {
                font-size: 0.8rem;
                color: #8db5a2;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
                display: block;
                font-weight: 500;
            }
            .kiosk-value {
                font-size: 1.6rem; 
                font-weight: 700;
                color: #ffffff;
                white-space: nowrap; /* Prevents data values from double-lining */
            }
            .kiosk-message {
                font-size: 1.4rem;
                color: #e0e0e0;
                line-height: 1.5;
            }
            .kiosk-message strong {
                color: #ffffff;
            }
        </style>
        <div id="modern-verify-overlay" class="kiosk-overlay">
            <div id="modern-verify-card" class="kiosk-card">
                <div id="modern-verify-content" style="display: contents;">
                    <!-- Dynamic Content -->
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', overlayHtml);
        overlay = document.getElementById('modern-verify-overlay');

        // Close on key press
        document.addEventListener('keydown', (e) => {
            if (overlay.style.opacity === '1') {
                closeVerificationOverlay();
            }
        });
    }

    const card = document.getElementById('modern-verify-card');
    const content = document.getElementById('modern-verify-content');
    const id = data.id || '';
    const name = data.name || 'Unknown';
    const affiliation = data.affiliation || 'N/A';
    const course_name = data.course_name || 'N/A';

    // Apply the specific glow/border class based on the state
    card.className = `kiosk-card kiosk-card-${state}`;

    if (state === 'granted') {
        content.innerHTML = `
            <div class="kiosk-header kiosk-header-granted">
                ACCESS GRANTED
            </div>
            <div class="kiosk-body">
                <div class="kiosk-left">
                    <div class="kiosk-icon-wrapper kiosk-icon-granted">
                        <i class="bi bi-check-lg"></i>
                    </div>
                </div>
                <div class="kiosk-right">
                    <div class="kiosk-detail-group">
                        <span class="kiosk-label">STUDENT NAME</span>
                        <div class="kiosk-value">${name}</div>
                    </div>
                    <div class="kiosk-detail-row">
                        <div class="kiosk-detail-group">
                            <span class="kiosk-label">STUDENT NUMBER</span>
                            <div class="kiosk-value">${id}</div>
                        </div>
                        <div class="kiosk-detail-group">
                            <span class="kiosk-label">DEPARTMENT</span>
                            <div class="kiosk-value">${course_name}</div>
                        </div>
                    </div>
                    <div class="kiosk-detail-group">
                        <span class="kiosk-label">COURSE</span>
                        <div class="kiosk-value">${affiliation}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (state === 'denied') {
        content.innerHTML = `
            <div class="kiosk-header kiosk-header-denied">
                ACCESS DENIED
            </div>
            <div class="kiosk-body">
                <div class="kiosk-left">
                    <div class="kiosk-icon-wrapper kiosk-icon-denied">
                        <i class="bi bi-x-lg"></i>
                    </div>
                </div>
                <div class="kiosk-right">
                    <div class="kiosk-message">
                        <strong>${id}</strong> is not registered within the system’s database.
                    </div>
                </div>
            </div>
        `;
    } else if (state === 'invalid') {
        content.innerHTML = `
            <div class="kiosk-header kiosk-header-invalid">
                INVALID INPUT
            </div>
            <div class="kiosk-body">
                <div class="kiosk-left">
                    <div class="kiosk-icon-wrapper kiosk-icon-invalid">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                    </div>
                </div>
                <div class="kiosk-right">
                    <div class="kiosk-message">
                        <strong>${id || 'Empty'}</strong> is not a valid input.<br>
                        Please enter valid inputs only.
                    </div>
                </div>
            </div>
        `;
    } else if (state === 'exit') {
        content.innerHTML = `
            <div class="kiosk-header kiosk-header-exit">
                EXIT LOGGED
            </div>
            <div class="kiosk-body">
                <div class="kiosk-left">
                    <div class="kiosk-icon-wrapper kiosk-icon-exit">
                        <i class="bi bi-box-arrow-right"></i>
                    </div>
                </div>
                <div class="kiosk-right">
                    <div class="kiosk-detail-group">
                        <span class="kiosk-label">STUDENT NAME</span>
                        <div class="kiosk-value">${name}</div>
                    </div>
                    <div class="kiosk-detail-row">
                        <div class="kiosk-detail-group">
                            <span class="kiosk-label">STUDENT NUMBER</span>
                            <div class="kiosk-value">${id}</div>
                        </div>
                        <div class="kiosk-detail-group">
                            <span class="kiosk-label">DEPARTMENT</span>
                            <div class="kiosk-value">${course_name}</div>
                        </div>
                    </div>
                    <div class="kiosk-detail-group">
                        <span class="kiosk-label">COURSE</span>
                        <div class="kiosk-value">${affiliation}</div>
                    </div>
                </div>
            </div>
        `;
    }

    overlay.style.opacity = '1';
    overlay.style.pointerEvents = 'auto';
    card.style.transform = 'translateY(0)';
}

function closeVerificationOverlay() {
    const overlay = document.getElementById('modern-verify-overlay');
    const card = document.getElementById('modern-verify-card');
    if (overlay && card) {
        overlay.style.opacity = '0';
        overlay.style.pointerEvents = 'none';
        card.style.transform = 'translateY(20px)';
    }
}

/**
 * Handle manual ID entry for both students and employees
 * @param {string} type - 'student' or 'employee'
 */
function submitManualEntry(type) {
    const idField = type === 'employee' ? 'manual-employee-id' : 'manual-student-id';
    const id = document.getElementById(idField).value.trim();
    const idRegex = /^[0-9\-]+$/;

    const modalEl = document.getElementById('manualEntryModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        if (modal) modal.hide();
    }

    // Check if empty or contains invalid characters
    if (!id || !idRegex.test(id)) {
        let invalidDisplay = 'Empty';
        
        if (id) {
            // Find all characters that are NOT a number or a hyphen
            const invalidCharsMatch = id.match(/[^0-9\-]/g);
            if (invalidCharsMatch) {
                // Get unique invalid characters and join them (e.g. "@ =")
                invalidDisplay = [...new Set(invalidCharsMatch)].join(' ');
            } else {
                invalidDisplay = 'Format';
            }
        }
        
        showVerificationOverlay('invalid', { id: invalidDisplay });
        document.getElementById(idField).value = '';
        return;
    }

    // Tester override exactly like previous overlay request
    if (id === '99-99999') {
        showVerificationOverlay('denied', { id: id });
        document.getElementById(idField).value = '';
        return;
    }

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
            const stateType = logType === 'exit' ? 'exit' : 'granted';
            
            if (typeof appendToLiveFeed === 'function') {
                appendToLiveFeed(data.name, data.affiliation, logType);
            }

            if (typeof showScanBanner === 'function') {
                showScanBanner(bannerType, {
                    id:     id,
                    name:   data.name,
                    course: data.course_name || data.course || 'N/A'
                });
            }

            showVerificationOverlay(stateType, { 
                id: id, 
                name: data.name,
                affiliation: data.affiliation,
                course_name: data.course_name || data.course || 'N/A'
            });

        } else {
            showVerificationOverlay('denied', { id: id });
            if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
        }
    })
    .catch(err => {
        console.error(err);
        showVerificationOverlay('invalid', { id: "Connection Error" });
        if (typeof showScanBanner === 'function') showScanBanner('error', { id: id });
    });

    document.getElementById(idField).value = '';
}
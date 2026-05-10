// [ANNOUNCEMENT FEATURE] - Bulletin Display Logic for Kiosks
function fetchBulletins() {
    // Detect context
    const targetId = window.lastScannedId || null;
    const targetDept = window.currentDept || null;

    // Improved detection: Check if it's any kiosk page (Entrance, Exit, Employee)
    const isKiosk = document.title.includes('Kiosk') || document.title.includes('Entrance') || document.title.includes('Exit');
    const targetEvent = window.currentEventName || (isKiosk ? 'General Attendance' : null);

    // FIX: Use local date instead of UTC to prevent timezone mismatches (e.g., late night/early morning)
    const now = new Date();
    const localDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

    const params = new URLSearchParams({
        target_id: targetId,
        target_dept: targetDept,
        target_event: targetEvent,
        scheduled_date: localDate
    });

    fetch(`/api/kiosk/bulletins?${params.toString()}`)
        .then(res => res.json())
        .then(res => {
            if (res.success && res.bulletins.length > 0) {
                // If we have targeted bulletins, they will be first (after model update)
                updateBulletinUI(res.bulletins[0]);
            } else {
                showDefaultBulletin();
            }
        })
        .catch(err => console.error('Error fetching bulletins:', err));
}

function updateBulletinUI(bulletin) {
    const titleEl = document.querySelector('.bulletin-title') || document.querySelector('#bulletin-title');
    const bodyEl = document.querySelector('.bulletin-body') || document.querySelector('#bulletin-body');
    const sourceEl = document.querySelector('.bulletin-source') || document.querySelector('#bulletin-source');

    // FIX: We no longer update the categoryEl.innerText dynamicially as per USER requirement.
    // The labels 'ANNOUNCEMENTS' and 'HR MEMO' are now static in their respective templates.

    if (titleEl) titleEl.innerText = bulletin.category || 'Status Update';
    if (bodyEl) bodyEl.innerText = bulletin.content;
    if (sourceEl) sourceEl.innerText = bulletin.from_source || 'PLP Attendance Monitoring System';

    // Add a subtle animation to indicate update
    const container = document.querySelector('.bulletin-container');
    if (container) {
        container.style.animation = 'none';
        container.offsetHeight; // trigger reflow
        container.style.animation = 'pulse-gold 1s ease-in-out';
    }
}

function showDefaultBulletin() {
    const titleEl = document.querySelector('.bulletin-title') || document.querySelector('#bulletin-title');
    const bodyEl = document.querySelector('.bulletin-body') || document.querySelector('#bulletin-body');
    const sourceEl = document.querySelector('.bulletin-source') || document.querySelector('#bulletin-source');

    if (titleEl) titleEl.innerText = 'Status Update';
    if (bodyEl) bodyEl.innerText = 'No announcements displayed at this time.';
    if (sourceEl) sourceEl.innerText = 'PLP Attendance Monitoring System';
}

// Expose to window for triggering after scan
window.fetchBulletins = fetchBulletins;

// Initial fetch
fetchBulletins();
// Refresh every 5 minutes
setInterval(fetchBulletins, 300000);

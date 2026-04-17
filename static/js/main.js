/* Main.js - PLP Smart System Interactions */

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initAnimations();
});

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

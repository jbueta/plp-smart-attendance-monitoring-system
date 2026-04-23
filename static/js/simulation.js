/*
 * SIMULATION MANAGER (Currently Inactive)
 * ---------------------------------------
 * This file contains logic for simulating data flows, chart updates,
 * and automated scanning events.
 *
 * It is currently disconnected from the main templates to allow the
 * system to prepare for real database integration.
 *
 * To re-activate these features once data is available:
 * 1. Uncomment the script tag for `simulation.js` in `base.html` or specific templates.
 * 2. Ensure the DOM elements referenced below exist in your updated data-driven UI.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Simulation manager loaded (Currently Inactive).");
    // ------------------------------------------------------------------------
    // [ARCHIVE] Auto-Scan Simulation Logic
    // ------------------------------------------------------------------------
    /*
    const autoScanBtn = document.getElementById('btn-auto-scan');
    if (autoScanBtn) {
        let isSimulating = false;
        let simInterval;

        autoScanBtn.addEventListener('click', () => {
            isSimulating = !isSimulating;

            if (isSimulating) {
                autoScanBtn.classList.replace('btn-outline-gold', 'btn-danger');
                autoScanBtn.innerHTML = '<i class="bi bi-stop-circle me-2"></i>Stop Simulating';

                // Simulate a scan every 4 seconds
                simInterval = setInterval(() => {
                    const mockIds = ['2023-001', '2023-002', '2023-003', 'EMP-001'];
                    const randomId = mockIds[Math.floor(Math.random() * mockIds.length)];

                    const inputField = document.getElementById('scanner-input');
                    if (inputField) {
                        inputField.value = randomId;
                        // Trigger the form submission
                        const form = inputField.closest('form');
                        if(form) form.dispatchEvent(new Event('submit'));
                    }
                }, 4000);
            } else {
                autoScanBtn.classList.replace('btn-danger', 'btn-outline-gold');
                autoScanBtn.innerHTML = '<i class="bi bi-play-circle me-2"></i>Simulate Auto-Scan';
                clearInterval(simInterval);
            }
        });
    }
    */

    // ------------------------------------------------------------------------
    // [ARCHIVE] Dynamic Chart Updates Simulation
    // ------------------------------------------------------------------------
    /*
    function simulateLiveTraffic() {
        const trafficCanvas = document.getElementById('trafficChart');
        // Assuming Chart.js is bound to this canvas in the view
        if (trafficCanvas && window.trafficChartInstance) {
            setInterval(() => {
                const data = window.trafficChartInstance.data.datasets[0].data;
                // Add minor random fluctuations to the last data point
                let lastVal = data[data.length - 1];
                let diff = Math.floor(Math.random() * 21) - 10; // -10 to +10
                let newVal = Math.max(0, lastVal + diff);

                data[data.length - 1] = newVal;
                window.trafficChartInstance.update();
            }, 5000);
        }
    }
    // simulateLiveTraffic();
    */
});

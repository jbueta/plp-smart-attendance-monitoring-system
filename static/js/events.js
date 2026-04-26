/* Event management functionality */

var selectionMode = false;
const frontendBaseUrl = window.location.origin;
const backendBaseUrl = window.APP_CONFIG?.backendApiUrl || 'http://127.0.0.1:5001';

function getLocalDateString(date = new Date()) {
    const localDate = new Date(date);
    localDate.setMinutes(localDate.getMinutes() - localDate.getTimezoneOffset());
    return localDate.toISOString().split('T')[0];
}

function parseTimeToMinutes(value) {
    if (!value) return null;
    const parts = value.split(':').map(Number);
    if (parts.length < 2 || parts.some(Number.isNaN)) return null;
    return (parts[0] * 60) + parts[1];
}

function toggleSelectionMode() {
    selectionMode = !selectionMode;
    const btn = document.getElementById('select-mode-btn');
    const bulkActions = document.getElementById('bulk-actions');
    const selectionCols = document.querySelectorAll('.selection-col');

    if (selectionMode) {
        btn.innerHTML = '<i class="bi bi-x-lg me-2"></i>Cancel';
        btn.classList.replace('btn-outline-light', 'btn-outline-danger');
        bulkActions.classList.remove('d-none');
        selectionCols.forEach(col => col.classList.remove('d-none'));
    } else {
        btn.innerHTML = '<i class="bi bi-check2-square me-2"></i>Select';
        btn.classList.replace('btn-outline-danger', 'btn-outline-light');
        bulkActions.classList.add('d-none');
        selectionCols.forEach(col => col.classList.add('d-none'));

        // Reset Selections
        document.querySelectorAll('.event-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;
        updateDeleteButton();
    }
}

function toggleSelectAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.event-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
    updateDeleteButton();
}

function updateDeleteButton() {
    const checkedCount = document.querySelectorAll('.event-checkbox:checked').length;
    const btn = document.getElementById('delete-selected-btn');
    const countSpan = document.getElementById('selected-count');

    if (countSpan) countSpan.textContent = checkedCount;
    if (btn) btn.disabled = checkedCount === 0;
}

// ==========================================
// GLOBAL VARIABLES & FUNCTIONS FOR VIEW MODAL
// ==========================================
var currentEventId = null;
var currentInstanceId = null;

function openViewModal(eventId, name, type, date, time, deptsStr) {
    currentEventId = eventId;
    
    const detailsTabEl = document.querySelector('#details-tab');
    if (detailsTabEl) {
        const detailsTab = new bootstrap.Tab(detailsTabEl);
        detailsTab.show();
    }

    // 2. Set Basic Info
    document.getElementById('view-event-title').innerText = name;
    document.getElementById('view-event-type').innerText = type;
    document.getElementById('view-event-date').innerText = date;
    document.getElementById('view-event-time').innerText = time;

    // 3. Handle Departments Badges
    const deptsContainer = document.getElementById('view-event-depts');
    deptsContainer.innerHTML = ''; 
    if (deptsStr && deptsStr.trim() !== '') {
        const deptsArray = deptsStr.split(', ');
        deptsArray.forEach(dept => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary-gold bg-opacity-25 text-gold border border-gold mb-1 me-1';
            badge.innerText = dept;
            deptsContainer.appendChild(badge);
        });
    } else {
        deptsContainer.innerHTML = '<span class="text-white-50 small fst-italic">No departments specified</span>';
    }

    // 4. Trigger fetching of Instances first
    fetchEventInstances(eventId);
}

function fetchEventInstances(eventId) {
    const selectContainer = document.getElementById('instanceSelectionContainer');
    const selectElement = document.getElementById('instanceSelect');
    const tbody = document.getElementById('attendance-table-body');
    
    tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-white-50"><div class="spinner-border spinner-border-sm text-info me-2"></div> Loading instances...</td></tr>';
    
    fetch(`${backendBaseUrl}/admin/event/${eventId}/instances`)
        .then(response => response.json())
        .then(instances => {
            console.log("Fetched instances:", instances);
            selectElement.innerHTML = ''; // Clear previous options

            if (instances && instances.length > 0) {
                selectContainer.style.display = 'block';
                
                instances.forEach(inst => {
                    let option = document.createElement('option');
                    option.value = inst.instance_id;
                    option.textContent = `${inst.event_date} (${inst.status})`; 
                    selectElement.appendChild(option);
                });

                currentInstanceId = instances[0].instance_id;
                fetchAttendanceData(currentInstanceId);
            } else {
                selectContainer.style.display = 'none';
                tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-white-50">No instances found for this event.</td></tr>';
                updateAttendanceVisuals([]); // Reset visuals to 0
            }
        })
        .catch(error => {
            console.error("Error fetching instances:", error);
            selectContainer.style.display = 'none';
            tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load event data.</td></tr>`;
        });
}

function fetchAttendanceData(instanceId) {
    if (!instanceId) return;
    
    const tbody = document.getElementById('attendance-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-white-50"><div class="spinner-border spinner-border-sm text-info me-2"></div> Loading attendance...</td></tr>';

    fetch(`${backendBaseUrl}/admin/instances/${instanceId}/get-attendance`)
        .then(response => response.json())
        .then(data => {
            console.log("Fetched attendance:", data);
            renderAttendanceTable(data);
            updateAttendanceVisuals(data);
        })
        .catch(error => {
            console.error("Error fetching attendance:", error);
            tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-danger">Failed to load attendance. Check backend connection.</td></tr>`;
        });
}

function renderAttendanceTable(participants) {
    const tbody = document.getElementById('attendance-table-body');
    tbody.innerHTML = '';

    if (!participants || participants.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-white-50">No participants found.</td></tr>';
        return;
    }

    participants.forEach(p => {
        const statusColors = {
            'Present': 'text-success',
            'Absent': 'text-danger',
            'Late': 'text-warning',
            'Excused': 'text-warning'
        };
        const activeColor = statusColors[p.status] || 'text-white';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="ps-3">
                <div class="fw-bold text-white">${p.user_name}</div>
                <div class="text-white-50" style="font-size: 0.75rem;">${p.department || 'N/A'}</div>
            </td>
            <td class="font-monospace text-white-50 small">
                In: ${p.first_in ? p.first_in : '--:--'}<br>
                Out: ${p.last_out ? p.last_out : '--:--'}
            </td>
            <td class="text-end pe-3">
                <select class="form-select form-select-sm bg-dark border-secondary ${activeColor} d-inline-block w-auto" 
                        onchange="updateStatus(${p.attendance_id}, this.value, this)">
                    <option value="Present" class="text-success" ${p.status === 'Present' ? 'selected' : ''}>Present</option>
                    <option value="Late" class="text-warning" ${p.status === 'Late' ? 'selected' : ''}>Late</option>
                    <option value="Excused" class="text-warning" ${p.status === 'Excused' ? 'selected' : ''}>Excused</option>
                    <option value="Absent" class="text-danger" ${p.status === 'Absent' ? 'selected' : ''}>Absent</option>
                </select>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateAttendanceVisuals(participants) {
    if (!participants) return;
    
    let total = participants.length;
    let present = 0, absent = 0, excused = 0, late = 0;

    participants.forEach(p => {
        if (p.status === 'Present') present++;
        else if (p.status === 'Absent') absent++;
        else if (p.status === 'Excused') excused++;
        else if (p.status === 'Late') late++;
    });

    document.getElementById('attendance-total').innerText = `${total} Total`;
    // Grouping Late with Present for the overall progress bar
    document.getElementById('count-present').innerText = present + late; 
    document.getElementById('count-excused').innerText = excused;
    document.getElementById('count-absent').innerText = absent;

    let pPct = total > 0 ? ((present + late) / total) * 100 : 0;
    let ePct = total > 0 ? (excused / total) * 100 : 0;
    let aPct = total > 0 ? (absent / total) * 100 : 0;

    document.getElementById('bar-present').style.width = pPct + '%';
    document.getElementById('bar-excused').style.width = ePct + '%';
    document.getElementById('bar-absent').style.width = aPct + '%';
}

function updateStatus(attendanceId, newStatus, selectElement) {
    selectElement.className = `form-select form-select-sm bg-dark border-secondary d-inline-block w-auto text-${newStatus === 'Present' ? 'success' : newStatus === 'Absent' ? 'danger' : 'warning'}`;

    fetch(`/api/attendance/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attendance_id: attendanceId, status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            fetchAttendanceData(currentInstanceId); 
        } else {
            alert('Failed to update status.');
        }
    })
    .catch(error => console.error("Update Error:", error));
}

function deleteSingleEvent(eventId) {
    if (!confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
        return;
    }

    fetch(`${frontendBaseUrl}/admin/events/delete/${eventId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 3. Find the table row and remove it from the screen smoothly
            const row = document.getElementById(`event-row-${eventId}`);
            if (row) {
                // Optional: add a Bootstrap fade out effect before removing
                row.style.transition = "opacity 0.3s ease";
                row.style.opacity = "0";
                setTimeout(() => row.remove(), 300);
            }
            
            console.log(data.message); 
        } else {
            alert(data.message || 'Failed to delete event.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('A network error occurred while trying to delete the event.');
    });
}

function deleteSelectedEvents() {
    const selectedCheckboxes = document.querySelectorAll('.event-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        alert("Please select at least one event to delete.");
        return;
    }

    const eventIds = Array.from(selectedCheckboxes).map(cb => cb.value);

    if (!confirm(`Are you sure you want to delete ${eventIds.length} events? This action cannot be undone.`)) {
        return;
    }

    fetch(`${frontendBaseUrl}/admin/events/bulk-delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ event_ids: eventIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            eventIds.forEach(id => {
                const row = document.getElementById(`event-row-${id}`);
                if (row) {
                    row.style.transition = "opacity 0.3s ease";
                    row.style.opacity = "0";
                    setTimeout(() => row.remove(), 300);
                }
            });

            toggleSelectionMode(); 
            console.log(data.message);
        } else {
            alert(data.message || 'Failed to delete selected events.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('A network error occurred while trying to delete events.');
    });
}

function filterEvents() {

    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const dateQuery = document.getElementById('dateFilter').value; 

    const tableRows = document.querySelectorAll('tr[id^="event-row-"]');

    tableRows.forEach(row => {
        const nameCell = row.cells[1]; 
        const dateCell = row.cells[4]; 

        if (nameCell && dateCell) {
            const eventName = nameCell.textContent.toLowerCase();
            const eventDate = dateCell.textContent.trim();

            const matchesSearch = eventName.includes(searchQuery);
            const matchesDate = (dateQuery === "") || (eventDate === dateQuery);

            if (matchesSearch && matchesDate) {
                row.style.display = "";
            } else {
                row.style.display = "none"; 
            }
        }
    });
}

// ==========================================
// DOM CONTENT LOADED (EVENT LISTENERS)
// ==========================================
document.addEventListener('DOMContentLoaded', function () {

    const tabs = document.querySelectorAll('#eventViewTabs .nav-link');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            tabs.forEach(t => {
                t.classList.remove('text-white', 'fw-bold', 'border-bottom', 'border-info', 'border-3');
                t.classList.add('text-white-50');
            });
            event.target.classList.remove('text-white-50');
            event.target.classList.add('text-white', 'fw-bold', 'border-bottom', 'border-info', 'border-3');
        });
    });

    const frequencySelect = document.getElementById('event-frequency');
    const dateInput = document.getElementById('event-date-input');
    const daySelect = document.getElementById('event-day-select');
    const dateLabel = document.getElementById('date-label');
    const wrapper = document.querySelector('.date-filter-wrapper');
    const datepicker = document.getElementById('dateFilter');
    const addEventForm = document.getElementById('add-event-form');
    const rosterInput = addEventForm ? addEventForm.querySelector('input[name="roster_file"]') : null;
    const startInput = addEventForm ? addEventForm.querySelector('input[name="time_start"]') : null;
    const endInput = addEventForm ? addEventForm.querySelector('input[name="time_end"]') : null;
    const todayString = getLocalDateString();

    if (dateInput) {
        dateInput.min = todayString;
    }

    if (daySelect && frequencySelect && frequencySelect.value !== 'weekly') {
        daySelect.disabled = true;
    }

    function validateAddEventForm() {
        if (!addEventForm) return true;

        if (allDeptCheck) allDeptCheck.setCustomValidity('');
        if (rosterInput) rosterInput.setCustomValidity('');
        if (dateInput) dateInput.setCustomValidity('');
        if (endInput) endInput.setCustomValidity('');

        const hasDepartment = Array.from(document.querySelectorAll('.dept-cb')).some(cb => cb.checked);
        const hasRoster = Boolean(rosterInput && rosterInput.files && rosterInput.files.length > 0);
        const hasManualParticipants = Array.from(addEventForm.querySelectorAll('input[name="custom_dept"]'))
            .some(input => input.value.trim() !== '');

        if (!hasDepartment && !hasRoster && !hasManualParticipants && allDeptCheck) {
            allDeptCheck.setCustomValidity('Select a department, upload a CSV roster, or enter participant IDs.');
        }

        if (hasRoster && rosterInput && !rosterInput.files[0].name.toLowerCase().endsWith('.csv')) {
            rosterInput.setCustomValidity('Upload a CSV roster file.');
        }

        if (frequencySelect && frequencySelect.value !== 'daily' && dateInput && !dateInput.value) {
            dateInput.setCustomValidity('Event date is required.');
        } else if (dateInput && dateInput.value && dateInput.value < todayString) {
            dateInput.setCustomValidity('Event date cannot be in the past.');
        }

        const startMinutes = startInput ? parseTimeToMinutes(startInput.value) : null;
        const endMinutes = endInput ? parseTimeToMinutes(endInput.value) : null;
        if (startMinutes !== null && endMinutes !== null && endMinutes <= startMinutes && endInput) {
            endInput.setCustomValidity('End time must be later than start time.');
        }

        return addEventForm.checkValidity();
    }

    if (wrapper && datepicker) {
        wrapper.addEventListener('click', function(e) {
            if (e.target === datepicker) {
                return; 
            }

            try {
                if (typeof datepicker.showPicker === 'function') {
                    datepicker.showPicker(); 
                } else {
                    datepicker.focus();      
                }
            } catch (error) {
                console.warn("Could not open date picker programmatically:", error);
            }
        });
    }

    if (frequencySelect) {
        frequencySelect.addEventListener('change', function () {
            if (this.value === 'weekly') {
                dateInput.classList.remove('d-none');
                dateInput.setAttribute('required', 'required');
                dateInput.disabled = false;
                
                daySelect.classList.remove('d-none');
                daySelect.setAttribute('required', 'required');
                daySelect.disabled = false;
                
                dateLabel.innerHTML = 'Start Date / Event Day <span class="text-danger">*</span>';
                
            } else if (this.value === 'daily') {
                daySelect.classList.add('d-none');
                daySelect.removeAttribute('required');
                daySelect.disabled = true;
                
                dateInput.classList.add('d-none');
                dateInput.removeAttribute('required');
                dateInput.disabled = true;
                dateInput.value = ''; 
                
                dateLabel.innerHTML = 'Event Date <span class="text-white-50">(N/A)</span>';
                
            } else {
                daySelect.classList.add('d-none');
                daySelect.removeAttribute('required');
                daySelect.disabled = true;
                
                dateInput.classList.remove('d-none');
                dateInput.setAttribute('required', 'required');
                dateInput.disabled = false;
                
                dateLabel.innerHTML = 'Event Date <span class="text-danger">*</span>';
            }

            validateAddEventForm();
        });
    }

    const allDeptCheck = document.getElementById('dept-all');
    const deptChecks = document.querySelectorAll('.dept-cb');

    if (allDeptCheck && deptChecks.length > 0) {
        allDeptCheck.addEventListener('change', function () {
            deptChecks.forEach(cb => cb.checked = this.checked);
            validateAddEventForm();
        });

        deptChecks.forEach(cb => {
            cb.addEventListener('change', function () {
                const allChecked = Array.from(deptChecks).every(c => c.checked);
                allDeptCheck.checked = allChecked;
                validateAddEventForm();
            });
        });
    }

    const container = document.getElementById('custom-participants-container');
    const addBtn = document.getElementById('add-custom-participant-btn');

    if (container && addBtn) {
        addBtn.addEventListener('click', function () {
            const row = document.createElement('div');
            row.className = 'd-flex align-items-center mt-2';
            row.innerHTML = `
                <input type="text" name="custom_dept" class="form-control bg-dark text-white border-secondary form-control-sm" placeholder="e.g. EMP-0001, ST-0001">
                <button type="button" class="btn btn-sm btn-outline-danger ms-2 remove-custom-btn" title="Remove">
                    <i class="bi bi-x"></i>
                </button>
            `;
            container.appendChild(row);

            updateRemoveButtons();

            const removeBtn = row.querySelector('.remove-custom-btn');
            removeBtn.addEventListener('click', function () {
                row.remove();
                updateRemoveButtons();
                validateAddEventForm();
            });
        });

        function updateRemoveButtons() {
            const rows = container.querySelectorAll('.d-flex');
            rows.forEach((row) => {
                const btn = row.querySelector('.remove-custom-btn');
                if (btn) {
                    btn.style.display = rows.length > 1 ? 'block' : 'none';
                }
            });
        }
    }

    if (addEventForm) {
        addEventForm.addEventListener('input', validateAddEventForm);
        addEventForm.addEventListener('change', validateAddEventForm);
        addEventForm.addEventListener('submit', function (event) {
            if (!validateAddEventForm()) {
                event.preventDefault();
                event.stopPropagation();
                addEventForm.classList.add('was-validated');
                addEventForm.reportValidity();
            }
        });
    }
    
    const instanceSelect = document.getElementById('instanceSelect');
    if (instanceSelect) {
        instanceSelect.addEventListener('change', function(e) {
            currentInstanceId = e.target.value;
            fetchAttendanceData(currentInstanceId);
        });
    }
});

function toggleDepts(button, hiddenCount) {
    const container = button.closest('td');
    const row = button.closest('tr');
    const allBadges = container.querySelectorAll('.dept-badge:not(.badge-more)');
    
    // Check if currently hidden (before toggling)
    const isCurrentlyHidden = allBadges.length > 3 && allBadges[3].classList.contains('hidden-dept');
    
    // Toggle badge visibility
    for (let i = 3; i < allBadges.length; i++) {
        if (isCurrentlyHidden) {
            allBadges[i].classList.remove('hidden-dept');
        } else {
            allBadges[i].classList.add('hidden-dept');
        }
    }
    
    // Apply font size changes to specific columns (indices 1, 4, 5 for Event Name, Date, Schedule)
    const cells = row.cells;
    if (cells.length >= 7) {
        const eventNameCell = cells[1];   // 2nd column
        const dateCell = cells[4];        // 5th column
        const scheduleCell = cells[5];    // 6th column
        
        if (isCurrentlyHidden) {
            // Expanding → add shrink class
            eventNameCell.classList.add('shrink-font');
            dateCell.classList.add('shrink-font-date');
            scheduleCell.classList.add('shrink-font-date');
        } else {
            // Collapsing → remove shrink class
            eventNameCell.classList.remove('shrink-font');
            dateCell.classList.remove('shrink-font-date');
            scheduleCell.classList.remove('shrink-font-date');
        }
    }
    
    button.textContent = isCurrentlyHidden ? "Show Less" : "+" + hiddenCount;
}

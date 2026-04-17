/* Reports management functionality */

function generateReport() {

    const category = document.getElementById('report-category').value;
    const typeSelect = document.getElementById('report-type');
    const type = typeSelect.value;
    const selectedOption = typeSelect.options[typeSelect.selectedIndex];
    const filter = document.getElementById('report-filter').value;
    
    console.log(document.getElementById('report-start').value);
    console.log(document.getElementById('report-end').value);

    let startDate = convertDate(document.getElementById('report-start').value);
    let endDate = convertDate(document.getElementById('report-end').value);

    const isOneTimeEvent = selectedOption && selectedOption.getAttribute('data-type') === 'one-time';

    if (isOneTimeEvent) {
        const displayDate = convertDate(document.getElementById('displayEventDate').textContent);
        console.log(displayDate);
        startDate = displayDate;
        endDate = displayDate;

        console.log(startDate);
        console.log(endDate);

    } else {
        if (!startDate || !endDate) {
            alert("Please select a date range.");
            return;
        }
        
        // Validate that start date is not after end date
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        if (start > end) {
            alert("Invalid date range: 'From' date cannot be after 'To' date.\n\nExample of invalid range: From April 1, 2025 to March 31, 2025");
            return;
        }
    }

    const params = new URLSearchParams({
        category: category,
        type: type,
        filter: filter,
        start: startDate,
        end: endDate,
        // autoprint: 'true'
    });

    // Open the generated report in a new tab
    const reportUrl = `/generate_report?${params.toString()}`;
    window.open(reportUrl, '_blank');
}

function convertDate (stringDate) {
    if (!stringDate) return ''; 
    
    const date = new Date(stringDate);
    
    if (isNaN(date.getTime())) {
        console.warn('Invalid date:', stringDate);
        return '';
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formatted = `${year}-${month}-${day}`;

    return formatted;
}

let reportMapping = {
    'general': [
        { value: 'student_entry_exit', text: 'Student Entry/Exit Logs' },
        { value: 'daily_traffic', text: 'Daily Traffic Analysis' }
    ],
    'visitor': [
        { value: 'daily_visitor', text: 'Daily Visitor Log' },
        { value: 'visitor_purpose', text: 'Visitor Purpose Summary' }
    ],
    'event': [
        { value: '1', text: 'Employee Attendance (Flag Ceremony)' },
        { value: '2', text: 'Employee Attendance (General Assembly)' }
    ],
    'violation': [
        { value: 'curfew_violations', text: 'Curfew Violations Report' },
        { value: 'overstaying_vehicles', text: 'Overstaying Vehicles' }
    ]
};

function fetch_events() {
    fetch('http://127.0.0.1:5000/api/retrieve/events')
        .then(response => response.json())
        .then(data => {   
            // Clear existing event mapping to avoid duplicates on re-fetch
            reportMapping.event = []; 

            data.forEach(event => {
                const eventName = event.active ? event.name : event.name + ' (Deleted)';
                if (event.frequency.toLowerCase() == 'once') {
                    reportMapping.event.push({
                        value: event.event_id.toString(),
                        text: eventName,
                        constraint: 'once',
                        date: event.date // Make sure this is in YYYY-MM-DD format from backend
                    });
                } else {
                    reportMapping.event.push({
                        value: event.event_id.toString(),
                        text: eventName
                    });
                }
            });
            
            // Once fetched, populate the dropdown based on the default selected category
            const initialCategory = document.getElementById('report-category').value;
            populateReportTypes(initialCategory);
        })
        .catch(error => console.error("Error fetching events:", error));
}

function populateReportTypes(category) {
    const typeSelect = document.getElementById('report-type');
    typeSelect.innerHTML = ''; // Clear current options

    if (reportMapping[category]) {
        reportMapping[category].forEach(item => {
            const option = document.createElement('option');
            option.value = item.value;
            option.textContent = item.text;
            
            // Embed data attributes if it's a one-time event
            if (item.constraint === 'once') {
                option.setAttribute('data-type', 'one-time');
                option.setAttribute('data-date', item.date);
            }
            
            typeSelect.appendChild(option);
        });
    }

    // Manually trigger the change event to ensure date UI matches the first populated option
    typeSelect.dispatchEvent(new Event('change'));
}

function fetch_departments() {
    fetch('http://127.0.0.1:5000/api/retrieve/departments')
        .then(response => response.json())
        .then(data => {
            populateDepartmentTypes(data);
        })
        .catch(error => console.error("Error fetching departments:", error));
}

function populateDepartmentTypes(departments) {
    const filterSelect = document.getElementById('report-filter');
    filterSelect.innerHTML = ''; 

    const defaultOption = document.createElement('option');
    defaultOption.value = 'All'; 
    defaultOption.textContent = 'All Departments';
    filterSelect.appendChild(defaultOption);

    if (departments && departments.length > 0) {
        departments.forEach(dept => {
            const option = document.createElement('option');
            
            option.value = dept.department_id; 
            option.textContent = 'College of ' + dept.department_name;
            
            filterSelect.appendChild(option);
        });
    }
}

function handleDateConstraint() {
    const typeSelect = document.getElementById('report-type');
    const selectedOption = typeSelect.options[typeSelect.selectedIndex];
    
    const startDateInput = document.getElementById('report-start');
    const endDateInput = document.getElementById('report-end');
    const dateRangeGroup = document.getElementById('dateRangeInputs');
    const singleDateGroup = document.getElementById('singleDateDisplay');
    const displayEventDate = document.getElementById('displayEventDate');
    const dateLabel = document.getElementById('date-label');

    // Check if the selected option has the data-type='one-time' attribute
    if (selectedOption && selectedOption.getAttribute('data-type') === 'one-time') {
        const eventDate = selectedOption.getAttribute('data-date');
        
        // 1. Force hidden inputs to the exact event date
        startDateInput.value = eventDate;
        endDateInput.value = eventDate;
        
        // 2. Swap the UI Elements
        dateRangeGroup.classList.add('d-none');
        singleDateGroup.classList.remove('d-none');
        
        // 3. Update Text Visually
        dateLabel.innerText = "Event Date";
        displayEventDate.textContent = eventDate; 
    } else {
        // Restore normal Date Range behavior
        startDateInput.value = '';
        endDateInput.value = '';
        
        singleDateGroup.classList.add('d-none');
        dateRangeGroup.classList.remove('d-none');
        dateLabel.innerText = "Select Date Range";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    
    fetch_departments();
    fetch_events();

    const categorySelect = document.getElementById('report-category');
    const typeSelect = document.getElementById('report-type');

    // 2. Listen for Category Changes to populate the Detailed Report Type dropdown
    categorySelect.addEventListener('change', function() {
        populateReportTypes(this.value);
    });

    // 3. Listen for Report Type changes to toggle the Date Constraint UI
    typeSelect.addEventListener('change', handleDateConstraint);

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


    
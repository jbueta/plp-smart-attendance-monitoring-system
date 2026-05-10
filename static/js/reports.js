/* Reports management functionality */

const frontendBaseUrl = window.location.origin;
let reportDepartments = [];
let reportCourses = [];
let visitorPurposes = ["Official Business", "Document Submission", "Inquiry", "Meeting", "Delivery", "Other"];
const eventInstancesByEventId = new Map();

let reportMapping = {
    general: [
        { value: "student_entry_exit", text: "Student Entry/Exit Logs" },
        { value: "daily_traffic", text: "Daily Traffic Analysis" }
    ],
    visitor: [
        { value: "daily_visitor", text: "Daily Visitor Log" },
        { value: "visitor_purpose", text: "Visitor Purpose Summary" }
    ],
    event: [
        { value: "1", text: "Employee Attendance (Flag Ceremony)", constraint: "once", date: "" },
        { value: "2", text: "Employee Attendance (General Assembly)", constraint: "once", date: "" }
    ],
    violation: [
        { value: "curfew_violations", text: "Curfew Violations Report" },
        { value: "overstaying_vehicles", text: "Overstaying Vehicles" }
    ]
};

function convertDate(stringDate) {
    if (!stringDate) return "";

    const trimmedDate = String(stringDate).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmedDate)) {
        return trimmedDate;
    }

    const date = new Date(trimmedDate);
    if (Number.isNaN(date.getTime())) {
        console.warn("Invalid date:", stringDate);
        return "";
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function formatReportDate(dateString) {
    if (!dateString) return "";
    const date = new Date(`${dateString}T00:00:00`);
    const options = { year: "numeric", month: "short", day: "numeric" };
    return date.toLocaleDateString("en-US", options);
}

function getReportDateElements() {
    return {
        dateLabel: document.getElementById("date-label"),
        startDateInput: document.getElementById("report-start"),
        endDateInput: document.getElementById("report-end"),
        dateRangeGroup: document.getElementById("dateRangeInputs"),
        singleDateGroup: document.getElementById("singleDateDisplay"),
        displayEventDate: document.getElementById("displayEventDate"),
        eventInstanceGroup: document.getElementById("eventInstanceGroup"),
        eventInstanceSelect: document.getElementById("event-instance-select"),
        eventInstanceHelp: document.getElementById("eventInstanceHelp")
    };
}

function showDateRangeMode() {
    const {
        dateLabel,
        startDateInput,
        endDateInput,
        dateRangeGroup,
        singleDateGroup,
        displayEventDate,
        eventInstanceGroup,
        eventInstanceSelect,
        eventInstanceHelp
    } = getReportDateElements();

    dateLabel.innerText = "Select Date Range";
    dateRangeGroup.classList.remove("d-none");
    singleDateGroup.classList.add("d-none");
    eventInstanceGroup.classList.add("d-none");
    displayEventDate.textContent = "--";

    if (eventInstanceSelect) {
        eventInstanceSelect.innerHTML = '<option value="">Select an event instance date</option>';
        eventInstanceSelect.disabled = false;
    }
    if (eventInstanceHelp) {
        eventInstanceHelp.textContent = "Choose which generated date instance of the recurring event you want to report on.";
    }

    if (!startDateInput.value) startDateInput.value = "";
    if (!endDateInput.value) endDateInput.value = "";
}

function showFixedEventDateMode(eventDate) {
    const {
        dateLabel,
        startDateInput,
        endDateInput,
        dateRangeGroup,
        singleDateGroup,
        displayEventDate,
        eventInstanceGroup
    } = getReportDateElements();

    startDateInput.value = eventDate || "";
    endDateInput.value = eventDate || "";
    dateRangeGroup.classList.add("d-none");
    singleDateGroup.classList.remove("d-none");
    eventInstanceGroup.classList.add("d-none");
    dateLabel.innerText = "Event Date";
    displayEventDate.textContent = eventDate || "--";
}

function syncSelectedEventInstanceDate() {
    const { startDateInput, endDateInput, eventInstanceSelect } = getReportDateElements();
    const selectedOption = eventInstanceSelect?.options[eventInstanceSelect.selectedIndex];
    const selectedDate = selectedOption?.dataset.date || eventInstanceSelect?.value || "";
    startDateInput.value = selectedDate;
    endDateInput.value = selectedDate;
}

function showEventInstanceLoading() {
    const {
        dateLabel,
        startDateInput,
        endDateInput,
        dateRangeGroup,
        singleDateGroup,
        eventInstanceGroup,
        eventInstanceSelect,
        eventInstanceHelp
    } = getReportDateElements();

    startDateInput.value = "";
    endDateInput.value = "";
    dateRangeGroup.classList.add("d-none");
    singleDateGroup.classList.add("d-none");
    eventInstanceGroup.classList.remove("d-none");
    dateLabel.innerText = "Event Date Instance";

    if (eventInstanceSelect) {
        eventInstanceSelect.disabled = true;
        eventInstanceSelect.innerHTML = '<option value="">Loading event dates...</option>';
    }
    if (eventInstanceHelp) {
        eventInstanceHelp.textContent = "Fetching generated dates for the selected recurring event.";
    }
}

function showEventInstancesMode(instances, emptyMessage = "No generated event instances are available for this recurring event yet.") {
    const {
        dateLabel,
        startDateInput,
        endDateInput,
        dateRangeGroup,
        singleDateGroup,
        eventInstanceGroup,
        eventInstanceSelect,
        eventInstanceHelp
    } = getReportDateElements();

    startDateInput.value = "";
    endDateInput.value = "";
    dateRangeGroup.classList.add("d-none");
    singleDateGroup.classList.add("d-none");
    eventInstanceGroup.classList.remove("d-none");
    dateLabel.innerText = "Event Date Instance";

    if (!eventInstanceSelect) {
        return;
    }

    eventInstanceSelect.innerHTML = "";

    if (!instances.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = emptyMessage;
        eventInstanceSelect.appendChild(option);
        eventInstanceSelect.disabled = true;
        if (eventInstanceHelp) {
            eventInstanceHelp.textContent = "Generate or wait for event instances before creating a recurring event attendance report.";
        }
        return;
    }

    instances.forEach((instance, index) => {
        const option = document.createElement("option");
        option.value = instance.event_date_value;
        option.dataset.date = instance.event_date_value;
        option.dataset.instanceId = instance.instance_id;
        option.textContent = `${instance.event_date}${instance.status ? ` (${instance.status})` : ""}`;
        if (index === 0) {
            option.selected = true;
        }
        eventInstanceSelect.appendChild(option);
    });

    eventInstanceSelect.disabled = false;
    syncSelectedEventInstanceDate();

    if (eventInstanceHelp) {
        eventInstanceHelp.textContent = "Select the exact generated date instance of this recurring event to use for the report.";
    }
}

function normalizeEventInstance(instance) {
    return {
        instance_id: instance.instance_id,
        event_date_value: instance.event_date_value || convertDate(instance.event_date),
        event_date: instance.event_date || formatReportDate(instance.event_date_value || ""),
        status: instance.status || ""
    };
}

async function fetchEventInstancesForReport(eventId) {
    const cacheKey = String(eventId);
    if (eventInstancesByEventId.has(cacheKey)) {
        return eventInstancesByEventId.get(cacheKey);
    }

    const response = await fetch(`${frontendBaseUrl}/api/backend/admin/event/${eventId}/instances`);
    if (!response.ok) {
        throw new Error(`Failed to fetch event instances. Status ${response.status}`);
    }

    const payload = await response.json();
    const instances = Array.isArray(payload)
        ? payload.map(normalizeEventInstance).filter((instance) => instance.event_date_value)
        : [];

    eventInstancesByEventId.set(cacheKey, instances);
    return instances;
}

function generateReport() {
    const category = document.getElementById("report-category").value;
    const typeSelect = document.getElementById("report-type");
    const selectedOption = typeSelect.options[typeSelect.selectedIndex];
    const type = typeSelect.value;
    const filter = document.getElementById("report-filter").value;

    let startDate = convertDate(document.getElementById("report-start").value);
    let endDate = convertDate(document.getElementById("report-end").value);

    if (category === "event") {
        if (!selectedOption || !type) {
            window.showSystemFeedback("Please select an event.", 'error');
            return;
        }


        const dateMode = selectedOption.getAttribute("data-date-mode");
        if (dateMode === "fixed") {
            const eventDate = selectedOption.getAttribute("data-date") || "";
            if (!eventDate) {
                window.showSystemFeedback("This event does not have a valid date yet.", 'error');
                return;
            }

            startDate = eventDate;
            endDate = eventDate;
        } else {
            const { eventInstanceSelect } = getReportDateElements();
            const selectedInstance = eventInstanceSelect?.options[eventInstanceSelect.selectedIndex];
            const instanceDate = selectedInstance?.dataset.date || eventInstanceSelect?.value || "";

            if (!instanceDate) {
                window.showSystemFeedback("Please select which recurring event date instance to generate the report from.", 'error');
                return;
            }


            startDate = instanceDate;
            endDate = instanceDate;
        }
    } else {
        if (!startDate || !endDate) {
            window.showSystemFeedback("Please select a date range.", 'error');
            return;
        }


        const start = new Date(startDate);
        const end = new Date(endDate);
        if (start > end) {
            window.showSystemFeedback("Invalid date range: 'From' date cannot be after 'To' date.", 'error');
            return;
        }

    }

    const params = new URLSearchParams({
        category,
        type,
        filter,
        start: startDate,
        end: endDate
    });

    const reportUrl = `/generate_report?${params.toString()}`;
    window.open(reportUrl, "_blank");
}

function buildUniqueReportEvents(events) {
    const groupedEvents = new Map();

    events.forEach((event) => {
        const eventId = String(event.event_id || "").trim();
        if (!eventId) {
            return;
        }

        const frequency = String(event.frequency || "").trim().toLowerCase();
        const existing = groupedEvents.get(eventId);
        const isDeleted = event.active === false || event.active === 0;
        const label = `${event.name || "Unnamed Event"}${isDeleted ? " (Deleted)" : ""}`;
        const eventDate = convertDate(event.date);

        if (!existing) {
            groupedEvents.set(eventId, {
                value: eventId,
                text: label,
                constraint: frequency === "once" ? "once" : "instances",
                date: eventDate,
                frequency
            });
            return;
        }

        if (!existing.date && eventDate) {
            existing.date = eventDate;
        }
    });

    return Array.from(groupedEvents.values());
}

function fetch_events() {
    fetch(`${frontendBaseUrl}/api/retrieve/events`)
        .then((response) => response.json())
        .then((data) => {
            reportMapping.event = buildUniqueReportEvents(Array.isArray(data) ? data : []);
            const initialCategory = document.getElementById("report-category").value;
            populateReportTypes(initialCategory);
        })
        .catch((error) => console.error("Error fetching events:", error));
}

function populateReportTypes(category) {
    const typeSelect = document.getElementById("report-type");
    typeSelect.innerHTML = "";

    if (reportMapping[category]) {
        reportMapping[category].forEach((item) => {
            const option = document.createElement("option");
            option.value = item.value;
            option.textContent = item.text;

            if (category === "event") {
                option.setAttribute("data-date-mode", item.constraint === "once" ? "fixed" : "instances");
                option.setAttribute("data-event-frequency", item.frequency || "");
            }

            if (item.constraint === "once") {
                option.setAttribute("data-type", "one-time");
                option.setAttribute("data-date", item.date || "");
            }

            typeSelect.appendChild(option);
        });
    }

    typeSelect.dispatchEvent(new Event("change"));
}

function fetch_departments() {
    fetch(`${frontendBaseUrl}/api/retrieve/departments`)
        .then((response) => response.json())
        .then((data) => {
            reportDepartments = Array.isArray(data) ? data : [];
            populateFilterOptions(document.getElementById("report-category").value);
        })
        .catch((error) => console.error("Error fetching departments:", error));
}

function fetch_courses() {
    fetch(`${frontendBaseUrl}/api/retrieve/courses`)
        .then((response) => response.json())
        .then((data) => {
            reportCourses = Array.isArray(data) ? data : [];
            populateFilterOptions(document.getElementById("report-category").value);
        })
        .catch((error) => console.error("Error fetching courses:", error));
}

function fetch_visitor_purposes() {
    fetch(`${frontendBaseUrl}/api/retrieve/visitor-purposes`)
        .then((response) => response.json())
        .then((data) => {
            visitorPurposes = Array.isArray(data) && data.length > 0 ? data : visitorPurposes;
            populateFilterOptions(document.getElementById("report-category").value);
        })
        .catch((error) => console.error("Error fetching visitor purposes:", error));
}

function addFilterOption(select, value, text) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = text;
    select.appendChild(option);
}

function populateFilterOptions(category) {
    const filterSelect = document.getElementById("report-filter");
    const filterLabel = document.getElementById("report-filter-label");
    filterSelect.innerHTML = "";

    if (category === "general") {
        filterLabel.textContent = "Student Program";
        addFilterOption(filterSelect, "All", "All Programs");
        reportCourses.forEach((course) => {
            addFilterOption(filterSelect, course.course_id, course.course_name);
        });
        return;
    }

    if (category === "visitor") {
        filterLabel.textContent = "Visitor Purpose";
        addFilterOption(filterSelect, "All", "All Purposes");
        visitorPurposes.forEach((purpose) => {
            addFilterOption(filterSelect, purpose, purpose);
        });
        return;
    }

    if (category === "event") {
        filterLabel.textContent = "Employee Department";
        addFilterOption(filterSelect, "All", "All Departments");
        reportDepartments.forEach((dept) => {
            addFilterOption(filterSelect, dept.department_id, dept.department_name);
        });
        return;
    }

    filterLabel.textContent = "Violation Subject";
    addFilterOption(filterSelect, "All", "All Subjects");
    addFilterOption(filterSelect, "student", "Students");
    addFilterOption(filterSelect, "visitor", "Visitors");
    addFilterOption(filterSelect, "employee", "Employees");
}

async function handleDateConstraint() {
    const category = document.getElementById("report-category").value;
    const typeSelect = document.getElementById("report-type");
    const selectedOption = typeSelect.options[typeSelect.selectedIndex];

    if (category !== "event") {
        showDateRangeMode();
        return;
    }

    if (!selectedOption || !selectedOption.value) {
        showDateRangeMode();
        return;
    }

    const dateMode = selectedOption.getAttribute("data-date-mode");
    if (dateMode === "fixed") {
        const eventDate = selectedOption.getAttribute("data-date") || "";
        showFixedEventDateMode(eventDate);
        return;
    }

    showEventInstanceLoading();

    try {
        const instances = await fetchEventInstancesForReport(selectedOption.value);
        showEventInstancesMode(instances);
    } catch (error) {
        console.error("Error fetching recurring event instances:", error);
        showEventInstancesMode([], "Could not load event instances. Please try again.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    fetch_departments();
    fetch_courses();
    fetch_visitor_purposes();
    fetch_events();

    const categorySelect = document.getElementById("report-category");
    const typeSelect = document.getElementById("report-type");
    const { eventInstanceSelect } = getReportDateElements();

    categorySelect.addEventListener("change", function () {
        populateReportTypes(this.value);
        populateFilterOptions(this.value);
    });

    typeSelect.addEventListener("change", () => {
        handleDateConstraint();
    });

    eventInstanceSelect?.addEventListener("change", syncSelectedEventInstanceDate);

    async function authenticateRequest(studentId) {
        const url = `${frontendBaseUrl}/authenticate`;
        const data = {
            student_id: studentId,
            date: new Date().toISOString().split("T")[0],
            time: new Date().toISOString().split("T")[1].split(".")[0],
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

    void authenticateRequest;
});

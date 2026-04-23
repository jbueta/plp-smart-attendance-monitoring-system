# An Integrated Smart Entrance, Exit, and Attendance Monitoring System with Data Analytics for Institutional Decision Support at Pamantasan ng Lungsod ng Pasig

Entrance and Exit Monitoring PLP Students  
Employee Attendance System for Flag Ceremonies with Entrance and Exit Analytics at PLP

## 🎯 Project Objective
The primary goal of this project is to design and develop an Integrated Smart Entrance, Exit, and Attendance Monitoring System for Pamantasan ng Lungsod ng Pasig (PLP). The system aims to automate the tracking of students and employees using machine learning and QR code technology to enhance institutional security and provide data-driven insights for decision support.

It streamlines the tracking of student movement in and out of the campus to ensure safety, enforce campus hours, and provide data for facility management. Furthermore, it incorporates a specialized attendance tracking system designed for university events (e.g., Flag Ceremonies, Seminars) and daily employee timekeeping.

### Specific Objectives
- **Automated Monitoring:** Utilize QR code scanning for seamless, real-time logging of user IDs, names, roles, and college affiliations.
- **Machine Learning Analytics:** Track participation rates for events like Flag Ceremonies and provide department-specific attendance reports.
- **Enhanced Security:** Integrate an automated "Overstaying Alert" system and flag unauthorized or unregistered IDs.
- **Streamlined Communication:** Send automated SMS notifications with real-time updates and attendance alerts to Department Heads.
- **Centralized Dashboard:** Generate analytical reports on student and employee movement, assisting the administration in institutional decision-making.
- **User-Friendly Interface:** Create a desktop application requiring minimal manual intervention, styled with the official color scheme and branding of the PLP College of Computer Studies.

---

## ⚙️ System Functionality

Smart entry and exit logging using QR code scanning automatically logs the User ID, Name, Role, College, and Time-in/Time-out.

### Student Entrance/Exit System Features:
- **QR Scanning:** Fast, contactless entry and exit using student IDs.
- **Real-time Logging:** Immediate database updates of student location (Inside/Outside).
- **Status Display:** Visual confirmation (Green/Red) on the kiosk screen upon scan.
- **Admin Alerts:** Notifications for students staying past curfew or for unauthorized entries.

### Employee Events Entrance/Exit Monitoring System Features:
- **Event-Based Mode:** Tracks attendance against a specific scheduled event (e.g., Flag Ceremony 7:00 AM - 8:00 AM).
- **Attendance Marking:** Automatically flags entries after the grace period as "Absent".
- **Department Analytics:** Aggregates attendance data by department (e.g., "College of Nursing - 90% Present").
- **Exit Analytics:** Tracks the time employees leave to ensure compliance with working hours.

---

## 📊 System Analytics
- **Flag Ceremony Participation:** Analytics for participation rates and employee attendance per department.
- **Peak Flow & Congestion Heatmaps:** Analyze entrance bottlenecks during specific times to inform decisions on opening more entry points or staggering class times.
- **Average Stay Duration:** Determines the average amount of hours an individual spends within the campus.
- **Tardiness Heatmap:** Analyzes late attendees for every flag ceremony, categorized by department.
- **Security & Loitering Analytics:** Identifies individuals who stay on campus beyond allotted hours or in unapproved areas, improving campus safety.

---

## 🌟 Unique and Innovative Features
- **Automated SMS:** Real-time notifications sent directly to Department Heads.
- **Security Flags:** Automatically flags unauthorized and unregistered IDs.
- **Overstay & Safety Monitoring:** Monitors individuals remaining on campus beyond closing hours, triggering alerts for potential violations or emergencies.
- **Predictive Attendance & Anomaly Detection:**
  - *Forecast Crowds:* Predicts expected queue times at gates based on historical arrival rates.
  - *Anomaly Detection:* Flags unusual timestamps (e.g., logging out at 2 AM) for security review.

---

## 🛠️ Implementation Plan & Tech Stack
- **Frontend / Interface:** HTML, CSS (Bootstrap 5, Glassmorphism UI), JavaScript
- **Backend System:** Python (Flask)
- **Database Architecture:** MySQL

### Project Structure
```text
plp_monitoring_system/
├── app.py              # Main Flask application logic
├── requirements.txt    # Python dependencies
├── schema.sql          # Database schema (Prototype)
├── static/
│   ├── css/
│   │   ├── style.css       # Consolidated system styles
│   │   └── background.css  # Background aesthetics
│   └── js/
│       ├── main.js         # Core interactions and clock
│       ├── kiosk.js        # Kiosk-specific logic
│       ├── events.js       # Event management logic
│       ├── reports.js      # Reporting functionality
│       └── simulation.js   # Inactive data simulation/chart updates
└── templates/          # HTML templates (Jinja2)
```

### Project Execution / Local Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd plp_monitoring_system
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Configuration:**
   Copy `.env.template` to `.env` and set your local database credentials, secrets, and allowed origins.
4. **Database Configuration:**
   Ensure your MySQL server is running and initialize the database using `schema.sql`. The checked-in schema now includes the visitor and employee `is_active` / formatted-ID updates expected by the current codebase.
5. **Run the Application:**
   ```bash
   python app.py
   python app_extension.py
   ```
6. **Access the System:**
   Navigate to `http://127.0.0.1:5000` in your web browser. *(Prototype Admin Credentials: Username: `admin`, Password: `admin123`)*

`app.py` serves the frontend/UI on port `5000`.
`app_extension.py` serves the API/backend on port `5001`.

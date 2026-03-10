-- ==============================================================================
-- PLP Smart Monitoring System - Database Schema
-- ==============================================================================

-- DEPARTMENTS TABLE
-- Stores organizational units within the university
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USERS TABLE
-- Stores students and employees details
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qr_code VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    user_type ENUM('student', 'employee') NOT NULL,
    department_id INT,
    profile_image_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- ATTENDANCE SCHEDULES TABLE
-- Defines events or time periods for attendance logging (e.g., Flag Ceremony)
CREATE TABLE IF NOT EXISTS attendance_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    grace_period_minutes INT DEFAULT 15,
    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ATTENDANCE LOGS TABLE
-- Records actual entrance/exit events
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    schedule_id INT NULL, -- NULL if normal entry/exit, populated if tied to a scheduled event
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_type ENUM('entry', 'exit') NOT NULL,
    status ENUM('present', 'late', 'on_leave', 'absent', 'normal') DEFAULT 'normal',
    location VARCHAR(100) DEFAULT 'Main Gate',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (schedule_id) REFERENCES attendance_schedules(id)
);


-- ATTENDANCE LOG
-- 1. Create the base 'user' table first since other tables depend on it
CREATE TABLE IF NOT EXISTS user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_type ENUM('Student', 'Visitor', 'Employee') NOT NULL
);

-- 2. Create the 'employee' table
CREATE TABLE IF NOT EXISTS employee (
    user_id INT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    department VARCHAR(10),
    status ENUM('Inside', 'Outside') NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- 3. Create the 'students' table
CREATE TABLE IF NOT EXISTS students (
    user_id INT PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL,
    course VARCHAR(10),
    status ENUM('Inside', 'Outside') NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- 4. Create the 'visitors' table
CREATE TABLE IF NOT EXISTS visitors (
    person_id INT PRIMARY KEY,
    purpose VARCHAR(200) NOT NULL,
    status ENUM('Inside', 'Outside') NOT NULL,
    FOREIGN KEY (person_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- 5. Create the 'attendance_log' table
CREATE TABLE IF NOT EXISTS attendance_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    action ENUM('Entry', 'Exit') NOT NULL,
    gate ENUM('Gate 1', 'Gate 2', 'Gate 3', 'Gate 4') NOT NULL,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- EVENTS

-- 2. Events Table
CREATE TABLE events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(200),
    event_type ENUM('flag_ceremony', 'seminar', 'other'),
    scheduled_date DATE,
    time_start TIME,
    time_end TIME,
    location VARCHAR(200)
);

-- 3. Event Attendance Logs Table
CREATE TABLE event_attendance_logs (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    user_id INT,
    timestamp DATETIME,
    log_type ENUM('entrance', 'exit'),
    status ENUM('present', 'late', 'absent'),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) on delete cascade
);

-- 4. Student Details Table
CREATE TABLE student_details (
    user_id INT PRIMARY KEY,
    student_id VARCHAR(20),
    college VARCHAR(100),
    section VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) on delete cascade
);

-- 5. Employee Details Table
CREATE TABLE employee_details (
    user_id INT PRIMARY KEY,
    employee_id VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id) on delete cascade
);

-- 6. Visitor Details Table
CREATE TABLE visitor_details (
    user_id INT PRIMARY KEY,
    details VARCHAR(20),
    purpose ENUM('Active', 'Completed'),
    date DATE,         -- Inferred type (blank in document)
    time_in TIME,      -- Inferred type (blank in document)
    time_out TIME,     -- Inferred type (blank in document)
    status VARCHAR(50),-- Inferred type (blank in document)
    FOREIGN KEY (user_id) REFERENCES users(user_id) on delete cascade
);


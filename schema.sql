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


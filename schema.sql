-- ==============================================================================
-- PLP Smart Monitoring System - Database Schema
-- ==============================================================================

-- ======================================================================
-- 1. BASE ENTITIES
-- ======================================================================

CREATE TABLE IF NOT EXISTS courses (
    course_id INT(11) NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id)
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT(11) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (department_id)
);

CREATE TABLE IF NOT EXISTS reports (
    report_id INT(11) NOT NULL,
    report_name VARCHAR(100) NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generated_by INT(11) NOT NULL
    PRIMARY KEY (report_id)
    FOREIGN KEY (generated_by) REFERENCES users(user_id)
);

-- ======================================================================
-- 2. USER TABLES
-- ======================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id INT(11) NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(100) DEFAULT NULL,
    role ENUM('student','employee','visitor') DEFAULT NULL,
    active TINYINT(1) DEFAULT 1,
    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS students (
    user_id INT(11) NOT NULL,
    student_id VARCHAR(8) DEFAULT NULL,
    student_name VARCHAR(80) DEFAULT NULL,
    course_id INT(11) NOT NULL,
    status ENUM('Inside','Outside') DEFAULT NULL,
    stud_last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS employees (
    user_id INT(11) NOT NULL,
    employee_id VARCHAR(20) DEFAULT NULL,
    employee_name VARCHAR(80) DEFAULT NULL,
    department_id INT(11) NOT NULL,
    position VARCHAR(100) DEFAULT NULL,
    status ENUM('Inside','Outside') DEFAULT NULL,
    emp_last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS visitors (
    visitor_id INT(11) NOT NULL,
    user_id INT(11) NOT NULL,
    visitor_name VARCHAR(80) DEFAULT NULL,
    purpose VARCHAR(100) DEFAULT NULL,
    status ENUM('Inside','Outside') DEFAULT NULL,
    visitor_last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (visitor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ======================================================================
-- 3. EVENT TABLES
-- ======================================================================

CREATE TABLE IF NOT EXISTS events (
    event_id INT(11) NOT NULL AUTO_INCREMENT,
    event_name VARCHAR(200) DEFAULT NULL,
    event_type ENUM('flag_ceremony','seminar','other') DEFAULT NULL,
    frequency ENUM('ONCE','DAILY','WEEKLY','MONTHLY','YEARLY') DEFAULT NULL,
    day ENUM('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') DEFAULT NULL,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    time_start TIME DEFAULT NULL,
    time_end TIME DEFAULT NULL,
    location VARCHAR(200) DEFAULT NULL,
    active TINYINT(1) DEFAULT 1,
    PRIMARY KEY (event_id)
);

CREATE TABLE IF NOT EXISTS event_instances (
    instance_id INT(11) NOT NULL AUTO_INCREMENT,
    event_id INT(11) NOT NULL,
    event_date DATE NOT NULL,
    status ENUM('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled',
    PRIMARY KEY (instance_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_participants (
    event_id INT(11) NOT NULL,
    user_id INT(11) NOT NULL,
    PRIMARY KEY (event_id, user_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ======================================================================
-- 4. ATTENDANCE & LOGS
-- ======================================================================

CREATE TABLE IF NOT EXISTS event_attendance (
    attendance_id INT(11) NOT NULL AUTO_INCREMENT,
    instance_id INT(11) NOT NULL,
    user_id INT(11) NOT NULL,
    event_date DATE NOT NULL,
    status ENUM('Present','Absent','Late','Excused') DEFAULT 'Absent',
    first_in DATETIME DEFAULT NULL,
    last_out DATETIME DEFAULT NULL,
    remarks VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (attendance_id),
    FOREIGN KEY (instance_id) REFERENCES event_instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_log (
    log_id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) DEFAULT NULL,
    event_id INT(11) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    log_type ENUM('Entry','Exit') DEFAULT NULL,
    PRIMARY KEY (log_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS general_log (
    log_id INT(11) NOT NULL AUTO_INCREMENT,
    user_id INT(11) DEFAULT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    log_type ENUM('Entry','Exit') DEFAULT NULL,
    gate ENUM('Gate 1','Gate 2','Gate 3') DEFAULT NULL,
    PRIMARY KEY (log_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);
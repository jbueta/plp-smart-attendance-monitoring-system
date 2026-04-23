-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 15, 2026 at 03:39 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smart_monitoring`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
CREATE TABLE `admin` (
  `user_id` int(11) NOT NULL,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `admin`
--

TRUNCATE TABLE `admin`;
--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`user_id`, `username`, `password`) VALUES
(21, 'admin', 'admin123');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

DROP TABLE IF EXISTS `courses`;
CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `courses`
--

TRUNCATE TABLE `courses`;
--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `created_at`) VALUES
(1, 'BS Psychology', '2026-03-12 14:31:47'),
(2, 'BS Accountancy', '2026-03-12 14:31:47'),
(3, 'BS Information Technology', '2026-03-12 14:31:47'),
(4, 'BS Computer Science', '2026-03-12 14:31:47'),
(5, 'BS Nursing', '2026-03-12 14:31:47'),
(6, 'BS Education', '2026-03-12 14:31:47'),
(7, 'BS Electrical Engineering', '2026-03-12 14:31:47'),
(8, 'BS Hospitality Management', '2026-03-12 14:31:47');

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
  `department_id` int(11) NOT NULL,
  `department_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `departments`
--

TRUNCATE TABLE `departments`;
--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`department_id`, `department_name`, `created_at`) VALUES
(1, 'College of Electrical Engineering', '2026-03-12 14:18:04'),
(2, 'College of Arts & Sciences', '2026-03-12 14:18:33'),
(3, 'College of Nursing', '2026-04-15 00:00:00'),
(4, 'College of Information Technology', '2026-04-15 00:00:00'),
(5, 'College of Business and Accountancy', '2026-04-15 00:00:00'),
(6, 'College of International Hospitality Management', '2026-04-15 00:00:00'),
(7, 'College of Education', '2026-04-15 00:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (
  `user_id` int(11) NOT NULL,
  `employee_id` varchar(8) NOT NULL,
  `employee_name` varchar(80) DEFAULT NULL,
  `department_id` int(11) NOT NULL,
  `position` varchar(100) DEFAULT NULL,
  `status` enum('Inside','Outside') DEFAULT NULL,
  `emp_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `employees`
--

TRUNCATE TABLE `employees`;
--
-- Dumping data for table `employees`
--

INSERT INTO `employees` (`user_id`, `employee_id`, `employee_name`, `department_id`, `position`, `status`, `emp_last_updated`) VALUES
(23, 'EMP-0001', 'Gregoria De Jesus', 3, 'Professor', 'Outside', '2026-04-15 08:56:17'),
(24, 'EMP-0002', 'Melchora Aquino', 4, 'Dean', 'Outside', '2026-04-15 08:56:17'),
(25, 'EMP-0003', 'Antonio Luna', 5, 'Faculty', 'Outside', '2026-04-15 08:56:17'),
(26, 'EMP-0004', 'Gabriela Silang', 6, 'Department Chair', 'Outside', '2026-04-15 08:56:17'),
(27, 'EMP-0005', 'Josefa Llanes Escoda', 7, 'Registrar', 'Outside', '2026-04-15 08:56:17'),
(5, 'EMP-1098', 'Apolinario Mabini', 2, 'Dean', 'Outside', '2026-04-15 13:36:17'),
(4, 'EMP-2015', 'Juan Dela Cruz', 1, 'Faculty', 'Inside', '2026-03-12 14:22:44');

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
CREATE TABLE `events` (
  `event_id` int(11) NOT NULL,
  `event_name` varchar(200) DEFAULT NULL,
  `event_type` enum('Meeting','Training','Seminar','Workshop','Drill','Activity','Flag Ceremony','Other') DEFAULT NULL,
  `frequency` enum('ONCE','DAILY','WEEKLY') DEFAULT 'ONCE',
  `day` enum('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') DEFAULT NULL,
  `event_date` date DEFAULT NULL,
  `time_start` time DEFAULT NULL,
  `time_end` time DEFAULT NULL,
  `location` varchar(200) DEFAULT NULL,
  `active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `events`
--

TRUNCATE TABLE `events`;
--
-- Dumping data for table `events`
--

INSERT INTO `events` (`event_id`, `event_name`, `event_type`, `frequency`, `day`, `event_date`, `time_start`, `time_end`, `location`, `active`) VALUES
(1, 'Flag Ceremony', 'Flag Ceremony', 'WEEKLY', 'Monday', '2026-04-20', '08:00:00', '08:40:00', 'Facade', 1),
(2, 'Flag Retreat', 'Other', 'WEEKLY', 'Monday', '2026-04-20', '09:00:00', '09:40:00', 'Facade', 1),
(3, 'Wildrift Tournament', 'Activity', 'ONCE', NULL, '2026-04-15', '22:00:00', '23:30:00', 'COMSOC', 0),
(4, 'Wildrift Tournament', 'Activity', 'ONCE', NULL, '2026-04-15', '23:00:00', '12:30:00', 'COMSOC', 1);

-- --------------------------------------------------------

--
-- Table structure for table `event_attendance`
--

DROP TABLE IF EXISTS `event_attendance`;
CREATE TABLE `event_attendance` (
  `attendance_id` int(11) NOT NULL,
  `instance_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `event_date` date NOT NULL,
  `status` enum('Present','Absent','Late','Excused') DEFAULT 'Absent',
  `first_in` datetime DEFAULT NULL,
  `last_out` datetime DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `event_attendance`
--

TRUNCATE TABLE `event_attendance`;
--
-- Dumping data for table `event_attendance`
--

INSERT INTO `event_attendance` (`attendance_id`, `instance_id`, `user_id`, `event_date`, `status`, `first_in`, `last_out`, `remarks`) VALUES
(1, 1, 5, '2026-04-15', 'Present', '2026-04-15 21:10:55', NULL, NULL),
(2, 1, 24, '2026-04-15', 'Absent', NULL, NULL, NULL),
(4, 2, 4, '2026-04-15', 'Absent', NULL, NULL, NULL),
(5, 2, 5, '2026-04-15', 'Present', '2026-04-15 21:33:04', '2026-04-15 21:35:06', NULL),
(6, 2, 23, '2026-04-15', 'Absent', NULL, NULL, NULL),
(7, 2, 24, '2026-04-15', 'Absent', NULL, NULL, NULL),
(8, 2, 25, '2026-04-15', 'Absent', NULL, NULL, NULL),
(9, 2, 26, '2026-04-15', 'Absent', NULL, NULL, NULL),
(10, 2, 27, '2026-04-15', 'Absent', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `event_instances`
--

DROP TABLE IF EXISTS `event_instances`;
CREATE TABLE `event_instances` (
  `instance_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `event_date` date NOT NULL,
  `status` enum('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `event_instances`
--

TRUNCATE TABLE `event_instances`;
--
-- Dumping data for table `event_instances`
--

INSERT INTO `event_instances` (`instance_id`, `event_id`, `event_date`, `status`) VALUES
(1, 3, '2026-04-15', 'Scheduled'),
(2, 4, '2026-04-15', 'Scheduled');

-- --------------------------------------------------------

--
-- Table structure for table `event_log`
--

DROP TABLE IF EXISTS `event_log`;
CREATE TABLE `event_log` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `event_id` int(11) NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `log_type` enum('Entry','Exit') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `event_log`
--

TRUNCATE TABLE `event_log`;
--
-- Dumping data for table `event_log`
--

INSERT INTO `event_log` (`log_id`, `user_id`, `event_id`, `timestamp`, `log_type`) VALUES
(1, 5, 3, '2026-04-15 21:10:55', 'Entry'),
(2, 5, 4, '2026-04-15 21:33:04', 'Entry'),
(3, 5, 4, '2026-04-15 21:33:11', 'Exit'),
(4, 5, 4, '2026-04-15 21:35:00', 'Entry'),
(5, 5, 4, '2026-04-15 21:35:06', 'Exit');

-- --------------------------------------------------------

--
-- Table structure for table `event_participants`
--

DROP TABLE IF EXISTS `event_participants`;
CREATE TABLE `event_participants` (
  `event_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `event_participants`
--

TRUNCATE TABLE `event_participants`;
--
-- Dumping data for table `event_participants`
--

INSERT INTO `event_participants` (`event_id`, `user_id`) VALUES
(1, 4),
(1, 5),
(1, 23),
(1, 24),
(1, 25),
(1, 26),
(1, 27),
(2, 4),
(2, 5),
(2, 23),
(2, 24),
(2, 25),
(2, 26),
(2, 27),
(3, 5),
(3, 24),
(4, 4),
(4, 5),
(4, 23),
(4, 24),
(4, 25),
(4, 26),
(4, 27);

-- --------------------------------------------------------

--
-- Table structure for table `general_log`
--

DROP TABLE IF EXISTS `general_log`;
CREATE TABLE `general_log` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `log_type` enum('Entry','Exit') DEFAULT NULL,
  `gate` enum('Gate 1','Gate 2','Gate 3') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `general_log`
--

TRUNCATE TABLE `general_log`;
--
-- Dumping data for table `general_log`
--

INSERT INTO `general_log` (`log_id`, `user_id`, `timestamp`, `log_type`, `gate`) VALUES
(1, 1, '2026-03-04 22:26:21', 'Entry', 'Gate 1'),
(2, 2, '2026-03-04 22:26:21', 'Entry', 'Gate 2'),
(3, 2, '2026-03-04 22:26:21', 'Exit', 'Gate 2'),
(4, 4, '2026-03-04 22:26:21', 'Entry', 'Gate 1'),
(5, 6, '2026-03-04 22:26:21', 'Entry', 'Gate 3'),
(6, 2, '2026-03-05 00:05:29', 'Exit', 'Gate 2'),
(7, 1, '2026-03-05 00:06:34', 'Exit', 'Gate 2'),
(8, 1, '2026-03-05 00:06:42', 'Entry', 'Gate 1'),
(9, 1, '2026-03-05 00:06:56', 'Exit', 'Gate 2'),
(10, 1, '2026-03-05 00:07:00', 'Entry', 'Gate 1'),
(11, 1, '2026-03-05 16:05:41', 'Exit', 'Gate 2'),
(12, 1, '2026-03-05 16:05:48', 'Entry', 'Gate 1'),
(13, 1, '2026-03-14 00:21:17', 'Exit', 'Gate 2'),
(14, 1, '2026-03-14 00:22:00', 'Entry', 'Gate 1'),
(15, 1, '2026-03-14 00:23:13', 'Exit', 'Gate 2'),
(16, 19, '2026-03-17 23:48:13', 'Entry', 'Gate 1'),
(17, 19, '2026-03-17 23:48:38', 'Exit', 'Gate 2'),
(18, 19, '2026-03-17 23:58:25', 'Entry', 'Gate 1'),
(19, 19, '2026-03-17 23:58:34', 'Exit', 'Gate 2'),
(20, 19, '2026-03-18 00:07:25', 'Entry', 'Gate 1'),
(21, 19, '2026-03-18 00:07:34', 'Exit', 'Gate 2'),
(22, 19, '2026-03-18 00:08:37', 'Entry', 'Gate 1'),
(23, 19, '2026-03-18 00:10:59', 'Exit', 'Gate 2'),
(24, 19, '2026-03-18 00:11:11', 'Entry', 'Gate 1'),
(25, 19, '2026-03-18 00:11:32', 'Exit', 'Gate 2'),
(26, 1, '2026-04-14 19:31:05', 'Exit', 'Gate 2'),
(27, 1, '2026-04-14 19:31:16', 'Exit', 'Gate 2'),
(28, 1, '2026-04-14 19:31:33', 'Exit', 'Gate 2'),
(29, 1, '2026-04-14 19:32:04', 'Exit', 'Gate 2'),
(30, 1, '2026-04-14 19:33:08', 'Exit', 'Gate 2'),
(31, 1, '2026-04-14 19:36:22', 'Exit', 'Gate 2'),
(32, 1, '2026-04-14 19:36:32', 'Exit', 'Gate 2'),
(33, 1, '2026-04-14 19:40:03', 'Exit', 'Gate 2'),
(34, 1, '2026-04-14 19:40:11', 'Entry', 'Gate 1'),
(35, 1, '2026-04-14 19:40:31', 'Exit', 'Gate 2'),
(36, 1, '2026-04-14 19:40:38', 'Entry', 'Gate 1'),
(37, 1, '2026-04-15 20:12:20', 'Entry', 'Gate 1'),
(38, 1, '2026-04-15 20:22:42', 'Exit', 'Gate 2'),
(39, 5, '2026-04-15 20:23:42', 'Entry', 'Gate 1'),
(40, 5, '2026-04-15 21:04:53', 'Exit', 'Gate 2'),
(41, 5, '2026-04-15 21:05:29', 'Entry', 'Gate 1'),
(42, 5, '2026-04-15 21:06:38', 'Exit', 'Gate 2'),
(43, 5, '2026-04-15 21:10:55', 'Entry', 'Gate 1'),
(44, 5, '2026-04-15 21:14:27', 'Exit', 'Gate 2'),
(45, 5, '2026-04-15 21:14:41', 'Entry', 'Gate 1'),
(46, 5, '2026-04-15 21:14:49', 'Exit', 'Gate 2'),
(47, 5, '2026-04-15 21:25:33', 'Entry', 'Gate 1'),
(48, 5, '2026-04-15 21:25:38', 'Exit', 'Gate 2'),
(49, 5, '2026-04-15 21:26:42', 'Entry', 'Gate 1'),
(50, 5, '2026-04-15 21:27:45', 'Exit', 'Gate 2'),
(51, 5, '2026-04-15 21:33:04', 'Entry', 'Gate 1'),
(52, 5, '2026-04-15 21:33:11', 'Exit', 'Gate 2'),
(53, 5, '2026-04-15 21:35:00', 'Entry', 'Gate 1'),
(54, 5, '2026-04-15 21:35:06', 'Exit', 'Gate 2'),
(55, 5, '2026-04-15 21:36:13', 'Entry', 'Gate 1'),
(56, 5, '2026-04-15 21:36:17', 'Exit', 'Gate 2');

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

DROP TABLE IF EXISTS `reports`;
CREATE TABLE `reports` (
  `report_id` int(11) NOT NULL,
  `report_name` varchar(100) NOT NULL,
  `generated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `generated_by` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `reports`
--

TRUNCATE TABLE `reports`;
-- --------------------------------------------------------

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `user_id` int(11) NOT NULL,
  `student_id` varchar(8) NOT NULL,
  `student_name` varchar(80) DEFAULT NULL,
  `course_id` int(11) NOT NULL,
  `status` enum('Inside','Outside') DEFAULT 'Outside',
  `stud_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `students`
--

TRUNCATE TABLE `students`;
--
-- Dumping data for table `students`
--

INSERT INTO `students` (`user_id`, `student_id`, `student_name`, `course_id`, `status`, `stud_last_updated`) VALUES
(2, '22-01582', 'Jose Rizal', 1, 'Outside', '2026-03-12 14:32:43'),
(19, '23-00312', 'JERICHO PAUL D. SALVADOR', 4, 'Outside', '2026-03-17 16:11:32'),
(1, '23-00314', 'Maria Clara', 5, 'Outside', '2026-04-15 12:22:42'),
(3, '24-00101', 'Andres Bonifacio', 3, 'Inside', '2026-03-12 14:32:52');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `role` enum('student','employee','visitor','admin') NOT NULL,
  `active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `users`
--

TRUNCATE TABLE `users`;
--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `role`, `active`) VALUES
(1, 'student', 1),
(2, 'student', 1),
(3, 'student', 1),
(4, 'employee', 1),
(5, 'employee', 1),
(6, 'visitor', 1),
(7, 'student', 1),
(8, 'student', 1),
(9, 'student', 1),
(10, 'employee', 1),
(11, 'employee', 1),
(12, 'visitor', 1),
(13, 'student', 1),
(14, 'student', 1),
(15, 'student', 1),
(16, 'employee', 1),
(17, 'employee', 1),
(18, 'visitor', 1),
(19, 'student', 1),
(20, '', 1),
(21, 'admin', 1),
(22, 'student', 1),
(23, 'employee', 1),
(24, 'employee', 1),
(25, 'employee', 1),
(26, 'employee', 1),
(27, 'employee', 1);

-- --------------------------------------------------------

--
-- Table structure for table `violations`
--

DROP TABLE IF EXISTS `violations`;
CREATE TABLE `violations` (
  `violation_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `violations`
--

TRUNCATE TABLE `violations`;
-- --------------------------------------------------------

--
-- Table structure for table `visitors`
--

DROP TABLE IF EXISTS `visitors`;
CREATE TABLE `visitors` (
  `user_id` int(11) DEFAULT NULL,
  `visitor_id` varchar(8) NOT NULL,
  `visitor_name` varchar(80) DEFAULT NULL,
  `purpose` varchar(100) DEFAULT NULL,
  `status` enum('Inside','Outside') DEFAULT NULL,
  `visitor_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Truncate table before insert `visitors`
--

TRUNCATE TABLE `visitors`;
--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`);

--
-- Indexes for table `departments`
--
ALTER TABLE `departments`
  ADD PRIMARY KEY (`department_id`);

--
-- Indexes for table `employees`
--
ALTER TABLE `employees`
  ADD PRIMARY KEY (`employee_id`),
  ADD KEY `employees_fk_departments` (`department_id`),
  ADD KEY `employees_ibfk_1` (`user_id`);

--
-- Indexes for table `events`
--
ALTER TABLE `events`
  ADD PRIMARY KEY (`event_id`),
  ADD UNIQUE KEY `unique_event_combo` (`event_name`,`event_date`,`time_start`);

--
-- Indexes for table `event_attendance`
--
ALTER TABLE `event_attendance`
  ADD PRIMARY KEY (`attendance_id`),
  ADD UNIQUE KEY `unique_attendance` (`instance_id`,`user_id`,`event_date`);

--
-- Indexes for table `event_instances`
--
ALTER TABLE `event_instances`
  ADD PRIMARY KEY (`instance_id`),
  ADD UNIQUE KEY `unique_instance` (`event_id`,`event_date`);

--
-- Indexes for table `event_log`
--
ALTER TABLE `event_log`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `event_log_ibfk_2` (`event_id`);

--
-- Indexes for table `event_participants`
--
ALTER TABLE `event_participants`
  ADD PRIMARY KEY (`event_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `general_log`
--
ALTER TABLE `general_log`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`report_id`),
  ADD KEY `generated_by` (`generated_by`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`student_id`),
  ADD KEY `stud_fk1` (`course_id`),
  ADD KEY `students_ibfk_1` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- Indexes for table `violations`
--
ALTER TABLE `violations`
  ADD PRIMARY KEY (`violation_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `visitors`
--
ALTER TABLE `visitors`
  ADD PRIMARY KEY (`visitor_id`),
  ADD KEY `visitors_usersFK` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `department_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `events`
--
ALTER TABLE `events`
  MODIFY `event_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `event_attendance`
--
ALTER TABLE `event_attendance`
  MODIFY `attendance_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `event_instances`
--
ALTER TABLE `event_instances`
  MODIFY `instance_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `event_log`
--
ALTER TABLE `event_log`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `general_log`
--
ALTER TABLE `general_log`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=57;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admin`
--
ALTER TABLE `admin`
  ADD CONSTRAINT `admin_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `employees`
--
ALTER TABLE `employees`
  ADD CONSTRAINT `employees_fk_departments` FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `event_attendance`
--
ALTER TABLE `event_attendance`
  ADD CONSTRAINT `event_attendance_ibfk_1` FOREIGN KEY (`instance_id`) REFERENCES `event_instances` (`instance_id`) ON DELETE CASCADE;

--
-- Constraints for table `event_instances`
--
ALTER TABLE `event_instances`
  ADD CONSTRAINT `event_instances_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`) ON DELETE CASCADE;

--
-- Constraints for table `event_log`
--
ALTER TABLE `event_log`
  ADD CONSTRAINT `event_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `event_log_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`) ON DELETE CASCADE;

--
-- Constraints for table `event_participants`
--
ALTER TABLE `event_participants`
  ADD CONSTRAINT `event_participants_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `event_participants_ibfk_3` FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`) ON DELETE CASCADE;

--
-- Constraints for table `general_log`
--
ALTER TABLE `general_log`
  ADD CONSTRAINT `general_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`generated_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `students`
--
ALTER TABLE `students`
  ADD CONSTRAINT `stud_fk1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `violations`
--
ALTER TABLE `violations`
  ADD CONSTRAINT `violations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `visitors`
--
ALTER TABLE `visitors`
  ADD CONSTRAINT `visitors_usersFK` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);
SET FOREIGN_KEY_CHECKS=1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

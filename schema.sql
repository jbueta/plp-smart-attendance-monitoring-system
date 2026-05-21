-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 21, 2026 at 07:28 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

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

CREATE TABLE `admin` (
  `user_id` int(11) NOT NULL,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`user_id`, `username`, `password`) VALUES
(21, 'admin', 'admin123');

-- --------------------------------------------------------

--
-- Table structure for table `bulletins`
--

CREATE TABLE `bulletins` (
  `bulletin_id` int(11) NOT NULL,
  `from_source` varchar(120) NOT NULL,
  `category` varchar(80) DEFAULT NULL,
  `content` text NOT NULL,
  `visibility_scope` enum('global','targeted','departmental','event_specific') NOT NULL DEFAULT 'global',
  `target_id` varchar(64) DEFAULT NULL,
  `target_department` varchar(150) DEFAULT NULL,
  `target_event` varchar(255) DEFAULT NULL,
  `scheduled_date` date DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bulletins`
--

INSERT INTO `bulletins` (`bulletin_id`, `from_source`, `category`, `content`, `visibility_scope`, `target_id`, `target_department`, `target_event`, `scheduled_date`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'HR Department', 'IMPORTANT NOTICE', 'This is a demo message', 'global', '', 'Accounting Office', 'General Attendance', '2026-05-11', 0, '2026-05-10 17:47:50', '2026-05-15 17:27:06');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

CREATE TABLE `departments` (
  `department_id` int(11) NOT NULL,
  `department_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
(7, 'College of Education', '2026-04-15 00:00:00'),
(8, 'College of Engineering', '2026-05-01 10:14:51'),
(10, 'College of Computer Studies', '2026-05-01 10:14:51'),
(15, 'Registrar\'s Office', '2026-05-01 10:14:52'),
(16, 'Accounting Office', '2026-05-01 10:14:52'),
(17, 'Human Resources', '2026-05-01 10:14:52'),
(18, 'MIS Office', '2026-05-01 10:14:52'),
(19, 'Library', '2026-05-01 10:14:52');

-- --------------------------------------------------------

--
-- Table structure for table `employees`
--

CREATE TABLE `employees` (
  `user_id` int(11) NOT NULL,
  `employee_id` int(5) UNSIGNED ZEROFILL NOT NULL,
  `employee_name` varchar(80) DEFAULT NULL,
  `department_id` int(11) NOT NULL,
  `position` varchar(100) DEFAULT NULL,
  `status` enum('Inside','Outside') DEFAULT 'Outside',
  `emp_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `employees`
--

INSERT INTO `employees` (`user_id`, `employee_id`, `employee_name`, `department_id`, `position`, `status`, `emp_last_updated`) VALUES
(23, 00001, 'Gregoria De Jesus', 3, 'Professor', 'Inside', '2026-05-08 05:36:17'),
(24, 00002, 'Melchora Aquino', 4, 'Dean', 'Inside', '2026-05-08 04:37:01'),
(25, 00003, 'Antonio Luna', 5, 'Faculty', 'Outside', '2026-05-01 06:18:40'),
(26, 00004, 'Gabriela Silang', 6, 'Department Chair', 'Inside', '2026-05-08 04:38:36'),
(27, 00005, 'Josefa Llanes Escoda', 7, 'Registrar', 'Inside', '2026-05-08 04:48:52'),
(29, 00008, 'Jason Jay M. Recto', 3, 'Professor I', 'Inside', '2026-05-16 13:34:56'),
(30, 00009, 'GONATO, VINCE RUSSEL H.', 4, 'PROFESSOR I', 'Inside', '2026-05-21 04:54:58'),
(31, 00010, 'GONATO, RHEA VIANCA H.', 3, 'PROFESSOR II', 'Outside', '2026-05-01 06:18:40'),
(32, 00011, 'HENSON, HONEYPEARL CHARISSE B.', 5, 'INSTRUCTOR I', 'Outside', '2026-05-01 06:18:40'),
(33, 00012, 'CABUGUANG, JUAN MIGUEL', 3, 'PROFESSOR I', 'Outside', '2026-05-01 06:18:40'),
(34, 00013, 'GUNGON, KARL', 1, 'PROFESSOR II', 'Outside', '2026-05-01 06:18:40'),
(35, 00014, 'Moncada, Ashanti Martir M.', 5, 'Dean', 'Outside', '2026-05-01 06:18:40'),
(38, 00015, 'Maryjoy Bernabe', 2, 'Professor I', 'Outside', '2026-05-01 15:01:47'),
(44, 00016, 'GONATO, VINCE', 1, 'PROFESSOR I', 'Inside', '2026-05-01 15:22:17'),
(45, 00017, 'Gonato, Rhea Vianca H.', 3, 'PROFESSOR II', 'Inside', '2026-05-01 15:00:26'),
(46, 00018, 'Henson, Honeypearl Charisse B.', 5, 'INSTRUCTOR I', 'Outside', '2026-05-01 06:18:40'),
(47, 00019, 'Ed Sheeran', 3, 'Instructor II', 'Outside', '2026-05-20 15:27:25'),
(105, 00022, 'Miley Cyrus', 8, 'Clerk', 'Outside', '2026-05-20 15:28:41'),
(106, 00025, 'John Cena', 10, 'Admin Aide', 'Outside', '2026-05-20 15:30:25'),
(107, 00027, 'Anne Marie', 8, 'Admin Officer', 'Outside', '2026-05-20 15:35:32'),
(108, 00029, 'Post Malone', 6, 'Professor I', 'Outside', '2026-05-20 17:10:25'),
(51, 00031, 'Ashanti Moncada', 19, 'Admin Aide', 'Outside', '2026-05-01 14:26:49'),
(111, 00035, 'Juan Perez', 17, 'Director', 'Outside', '2026-05-21 03:06:07'),
(49, 00201, 'Nellyn Moncada Recto', 2, 'Professor II', 'Outside', '2026-05-01 06:28:59'),
(50, 00202, 'Rogelio Recto Sr.', 5, 'Professor', 'Outside', '2026-05-01 06:43:47'),
(5, 01098, 'Apolinario Mabini Sr.', 2, 'Dean', 'Outside', '2026-05-01 06:43:31'),
(4, 02015, 'Juan Dela Cruz Jr.', 1, 'Faculty', 'Outside', '2026-05-01 06:51:47');

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

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
-- Dumping data for table `events`
--

INSERT INTO `events` (`event_id`, `event_name`, `event_type`, `frequency`, `day`, `event_date`, `time_start`, `time_end`, `location`, `active`) VALUES
(1, 'Flag Ceremony', 'Flag Ceremony', 'WEEKLY', 'Monday', '2026-04-20', '08:00:00', '08:40:00', 'Facade', 1),
(2, 'Flag Retreat', 'Other', 'WEEKLY', 'Monday', '2026-04-20', '09:00:00', '09:40:00', 'Facade', 1),
(3, 'Wildrift Tournament', 'Activity', 'ONCE', NULL, '2026-04-15', '22:00:00', '23:30:00', 'COMSOC', 0),
(4, 'Wildrift Tournament', 'Activity', 'ONCE', NULL, '2026-04-15', '23:00:00', '12:30:00', 'COMSOC', 1),
(5, 'ML', 'Activity', 'ONCE', NULL, '2026-04-24', '10:53:00', '10:55:00', 'Auditorium', 0),
(6, 'test', 'Meeting', 'ONCE', NULL, '2026-05-09', '10:00:00', '14:00:00', 'COMSOC', 1),
(7, 'ML', 'Flag Ceremony', 'ONCE', NULL, '2026-04-30', '06:22:00', '22:27:00', 'COMSOC', 0),
(8, 'test2', 'Training', 'ONCE', NULL, '2026-05-01', '23:00:00', '23:50:00', 'Facade', 1),
(9, 'asdasdasda', 'Training', 'ONCE', NULL, '2026-05-02', '16:16:00', '16:20:00', 'dasdasd', 1),
(10, 'Testing', 'Meeting', 'ONCE', NULL, '2026-05-07', '20:25:00', '21:25:00', 'Auditorium', 1),
(11, 'Flag Ceremony', 'Flag Ceremony', 'ONCE', NULL, '2026-05-08', '13:00:00', '13:30:00', 'Quad', 0),
(12, 'Test Event 2', 'Meeting', 'ONCE', NULL, '2026-05-08', '12:36:00', '12:40:00', 'Audi', 1),
(13, 'Flag Ceremony Test', 'Flag Ceremony', 'ONCE', NULL, '2026-05-08', '13:35:00', '15:35:00', 'Quad', 1),
(14, 'Wildrift Tournament', 'Meeting', 'ONCE', NULL, '2026-05-16', '20:15:00', '20:20:00', 'Auditorium', 0),
(15, 'Wildrift Tournament', 'Meeting', 'ONCE', NULL, '2026-05-16', '21:36:00', '21:40:00', 'Auditorium', 1),
(16, 'Demo Event', 'Meeting', 'ONCE', NULL, '2026-05-21', '14:30:00', '17:30:00', 'Main Hall', 1);

-- --------------------------------------------------------

--
-- Table structure for table `event_attendance`
--

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
(10, 2, 27, '2026-04-15', 'Absent', NULL, NULL, NULL),
(11, 3, 4, '2026-04-24', 'Absent', NULL, NULL, NULL),
(12, 3, 5, '2026-04-24', 'Absent', NULL, NULL, NULL),
(13, 3, 23, '2026-04-24', 'Absent', NULL, NULL, NULL),
(14, 3, 24, '2026-04-24', 'Absent', NULL, NULL, NULL),
(15, 3, 25, '2026-04-24', 'Absent', NULL, NULL, NULL),
(16, 3, 26, '2026-04-24', 'Absent', NULL, NULL, NULL),
(17, 3, 27, '2026-04-24', 'Absent', NULL, NULL, NULL),
(18, 4, 4, '2026-05-09', 'Absent', NULL, NULL, NULL),
(19, 4, 5, '2026-05-09', 'Absent', NULL, NULL, NULL),
(20, 4, 23, '2026-05-09', 'Absent', NULL, NULL, NULL),
(21, 4, 24, '2026-05-09', 'Absent', NULL, NULL, NULL),
(22, 4, 25, '2026-05-09', 'Absent', NULL, NULL, NULL),
(23, 4, 26, '2026-05-09', 'Absent', NULL, NULL, NULL),
(24, 4, 27, '2026-05-09', 'Absent', NULL, NULL, NULL),
(25, 5, 4, '2026-04-30', 'Absent', NULL, NULL, NULL),
(26, 5, 5, '2026-04-30', 'Absent', NULL, NULL, NULL),
(27, 5, 23, '2026-04-30', 'Absent', NULL, NULL, NULL),
(28, 5, 24, '2026-04-30', 'Absent', NULL, NULL, NULL),
(29, 5, 25, '2026-04-30', 'Absent', NULL, NULL, NULL),
(30, 5, 26, '2026-04-30', 'Absent', NULL, NULL, NULL),
(31, 5, 27, '2026-04-30', 'Absent', NULL, NULL, NULL),
(32, 6, 4, '2026-04-27', 'Absent', NULL, NULL, NULL),
(33, 6, 5, '2026-04-27', 'Absent', NULL, NULL, NULL),
(34, 6, 23, '2026-04-27', 'Absent', NULL, NULL, NULL),
(35, 6, 24, '2026-04-27', 'Absent', NULL, NULL, NULL),
(36, 6, 25, '2026-04-27', 'Absent', NULL, NULL, NULL),
(37, 6, 26, '2026-04-27', 'Absent', NULL, NULL, NULL),
(38, 6, 27, '2026-04-27', 'Absent', NULL, NULL, NULL),
(39, 7, 4, '2026-04-27', 'Absent', NULL, NULL, NULL),
(40, 7, 5, '2026-04-27', 'Absent', NULL, NULL, NULL),
(41, 7, 23, '2026-04-27', 'Absent', NULL, NULL, NULL),
(42, 7, 24, '2026-04-27', 'Absent', NULL, NULL, NULL),
(43, 7, 25, '2026-04-27', 'Absent', NULL, NULL, NULL),
(44, 7, 26, '2026-04-27', 'Absent', NULL, NULL, NULL),
(45, 7, 27, '2026-04-27', 'Absent', NULL, NULL, NULL),
(48, 10, 5, '2026-05-01', 'Absent', NULL, NULL, NULL),
(49, 10, 23, '2026-05-01', 'Absent', NULL, NULL, NULL),
(50, 10, 24, '2026-05-01', 'Absent', NULL, NULL, NULL),
(51, 10, 25, '2026-05-01', 'Absent', NULL, NULL, NULL),
(52, 10, 26, '2026-05-01', 'Absent', NULL, NULL, NULL),
(53, 10, 27, '2026-05-01', 'Absent', NULL, NULL, NULL),
(54, 10, 29, '2026-05-01', 'Late', '2026-05-01 23:22:25', NULL, NULL),
(55, 10, 30, '2026-05-01', 'Absent', NULL, NULL, NULL),
(56, 10, 31, '2026-05-01', 'Absent', NULL, NULL, NULL),
(57, 10, 32, '2026-05-01', 'Absent', NULL, NULL, NULL),
(58, 10, 33, '2026-05-01', 'Absent', NULL, NULL, NULL),
(59, 10, 34, '2026-05-01', 'Absent', NULL, NULL, NULL),
(60, 10, 35, '2026-05-01', 'Absent', NULL, NULL, NULL),
(61, 10, 38, '2026-05-01', 'Present', '2026-05-01 23:01:33', '2026-05-01 23:01:47', NULL),
(62, 10, 44, '2026-05-01', 'Present', '2026-05-01 23:00:33', '2026-05-01 23:02:02', NULL),
(63, 10, 45, '2026-05-01', 'Present', '2026-05-01 23:00:26', NULL, NULL),
(64, 10, 46, '2026-05-01', 'Absent', NULL, NULL, NULL),
(65, 10, 49, '2026-05-01', 'Absent', NULL, NULL, NULL),
(66, 10, 50, '2026-05-01', 'Absent', NULL, NULL, NULL),
(67, 10, 51, '2026-05-01', 'Absent', NULL, NULL, NULL),
(88, 20, 5, '2026-05-02', 'Absent', NULL, NULL, NULL),
(89, 20, 23, '2026-05-02', 'Absent', NULL, NULL, NULL),
(90, 20, 24, '2026-05-02', 'Absent', NULL, NULL, NULL),
(91, 20, 25, '2026-05-02', 'Absent', NULL, NULL, NULL),
(92, 20, 26, '2026-05-02', 'Absent', NULL, NULL, NULL),
(93, 20, 27, '2026-05-02', 'Absent', NULL, NULL, NULL),
(94, 20, 29, '2026-05-02', 'Present', '2026-05-02 16:15:35', '2026-05-02 16:15:42', NULL),
(95, 20, 30, '2026-05-02', 'Absent', NULL, NULL, NULL),
(96, 20, 31, '2026-05-02', 'Absent', NULL, NULL, NULL),
(97, 20, 32, '2026-05-02', 'Absent', NULL, NULL, NULL),
(98, 20, 33, '2026-05-02', 'Absent', NULL, NULL, NULL),
(99, 20, 34, '2026-05-02', 'Absent', NULL, NULL, NULL),
(100, 20, 35, '2026-05-02', 'Absent', NULL, NULL, NULL),
(101, 20, 38, '2026-05-02', 'Absent', NULL, NULL, NULL),
(102, 20, 44, '2026-05-02', 'Absent', NULL, NULL, NULL),
(103, 20, 45, '2026-05-02', 'Absent', NULL, NULL, NULL),
(104, 20, 46, '2026-05-02', 'Absent', NULL, NULL, NULL),
(105, 20, 49, '2026-05-02', 'Absent', NULL, NULL, NULL),
(106, 20, 50, '2026-05-02', 'Absent', NULL, NULL, NULL),
(107, 20, 51, '2026-05-02', 'Absent', NULL, NULL, NULL),
(121, 23, 4, '2026-05-04', 'Absent', NULL, NULL, NULL),
(122, 23, 5, '2026-05-04', 'Absent', NULL, NULL, NULL),
(123, 23, 23, '2026-05-04', 'Absent', NULL, NULL, NULL),
(124, 23, 24, '2026-05-04', 'Absent', NULL, NULL, NULL),
(125, 23, 25, '2026-05-04', 'Absent', NULL, NULL, NULL),
(126, 23, 26, '2026-05-04', 'Absent', NULL, NULL, NULL),
(127, 23, 27, '2026-05-04', 'Absent', NULL, NULL, NULL),
(128, 24, 4, '2026-05-04', 'Absent', NULL, NULL, NULL),
(129, 24, 5, '2026-05-04', 'Absent', NULL, NULL, NULL),
(130, 24, 23, '2026-05-04', 'Absent', NULL, NULL, NULL),
(131, 24, 24, '2026-05-04', 'Absent', NULL, NULL, NULL),
(132, 24, 25, '2026-05-04', 'Absent', NULL, NULL, NULL),
(133, 24, 26, '2026-05-04', 'Absent', NULL, NULL, NULL),
(134, 24, 27, '2026-05-04', 'Absent', NULL, NULL, NULL),
(136, 26, 5, '2026-05-07', 'Absent', NULL, NULL, NULL),
(137, 26, 23, '2026-05-07', 'Absent', NULL, NULL, NULL),
(138, 26, 24, '2026-05-07', 'Absent', NULL, NULL, NULL),
(139, 26, 25, '2026-05-07', 'Absent', NULL, NULL, NULL),
(140, 26, 26, '2026-05-07', 'Absent', NULL, NULL, NULL),
(141, 26, 27, '2026-05-07', 'Absent', NULL, NULL, NULL),
(142, 26, 29, '2026-05-07', 'Absent', NULL, NULL, NULL),
(143, 26, 30, '2026-05-07', 'Absent', NULL, NULL, NULL),
(144, 26, 31, '2026-05-07', 'Absent', NULL, NULL, NULL),
(145, 26, 32, '2026-05-07', 'Absent', NULL, NULL, NULL),
(146, 26, 33, '2026-05-07', 'Absent', NULL, NULL, NULL),
(147, 26, 34, '2026-05-07', 'Absent', NULL, NULL, NULL),
(148, 26, 35, '2026-05-07', 'Absent', NULL, NULL, NULL),
(149, 26, 38, '2026-05-07', 'Absent', NULL, NULL, NULL),
(150, 26, 44, '2026-05-07', 'Absent', NULL, NULL, NULL),
(151, 26, 45, '2026-05-07', 'Absent', NULL, NULL, NULL),
(152, 26, 46, '2026-05-07', 'Absent', NULL, NULL, NULL),
(153, 26, 49, '2026-05-07', 'Absent', NULL, NULL, NULL),
(154, 26, 50, '2026-05-07', 'Absent', NULL, NULL, NULL),
(155, 26, 51, '2026-05-07', 'Absent', NULL, NULL, NULL),
(156, 27, 5, '2026-05-08', 'Absent', NULL, NULL, NULL),
(157, 27, 23, '2026-05-08', 'Present', '2026-05-08 12:31:08', '2026-05-08 12:31:16', NULL),
(158, 27, 24, '2026-05-08', 'Absent', NULL, NULL, NULL),
(159, 27, 25, '2026-05-08', 'Absent', NULL, NULL, NULL),
(160, 27, 26, '2026-05-08', 'Absent', NULL, NULL, NULL),
(161, 27, 27, '2026-05-08', 'Absent', NULL, NULL, NULL),
(162, 27, 29, '2026-05-08', 'Absent', NULL, NULL, NULL),
(163, 27, 30, '2026-05-08', 'Absent', NULL, NULL, NULL),
(164, 27, 31, '2026-05-08', 'Absent', NULL, NULL, NULL),
(165, 27, 32, '2026-05-08', 'Absent', NULL, NULL, NULL),
(166, 27, 33, '2026-05-08', 'Absent', NULL, NULL, NULL),
(167, 27, 34, '2026-05-08', 'Absent', NULL, NULL, NULL),
(168, 27, 35, '2026-05-08', 'Absent', NULL, NULL, NULL),
(169, 27, 38, '2026-05-08', 'Absent', NULL, NULL, NULL),
(170, 27, 44, '2026-05-08', 'Absent', NULL, NULL, NULL),
(171, 27, 45, '2026-05-08', 'Absent', NULL, NULL, NULL),
(172, 27, 46, '2026-05-08', 'Absent', NULL, NULL, NULL),
(173, 27, 49, '2026-05-08', 'Absent', NULL, NULL, NULL),
(174, 27, 50, '2026-05-08', 'Absent', NULL, NULL, NULL),
(175, 27, 51, '2026-05-08', 'Absent', NULL, NULL, NULL),
(189, 30, 5, '2026-05-08', 'Absent', NULL, NULL, NULL),
(190, 30, 23, '2026-05-08', 'Absent', NULL, NULL, NULL),
(191, 30, 24, '2026-05-08', 'Present', '2026-05-08 12:37:01', NULL, NULL),
(192, 30, 25, '2026-05-08', 'Absent', NULL, NULL, NULL),
(193, 30, 26, '2026-05-08', 'Present', '2026-05-08 12:38:36', NULL, NULL),
(194, 30, 27, '2026-05-08', 'Present', '2026-05-08 12:48:52', NULL, NULL),
(195, 30, 29, '2026-05-08', 'Absent', NULL, NULL, NULL),
(196, 30, 30, '2026-05-08', 'Absent', NULL, NULL, NULL),
(197, 30, 31, '2026-05-08', 'Absent', NULL, NULL, NULL),
(198, 30, 32, '2026-05-08', 'Absent', NULL, NULL, NULL),
(199, 30, 33, '2026-05-08', 'Absent', NULL, NULL, NULL),
(200, 30, 34, '2026-05-08', 'Absent', NULL, NULL, NULL),
(201, 30, 35, '2026-05-08', 'Absent', NULL, NULL, NULL),
(202, 30, 38, '2026-05-08', 'Absent', NULL, NULL, NULL),
(203, 30, 44, '2026-05-08', 'Absent', NULL, NULL, NULL),
(204, 30, 45, '2026-05-08', 'Absent', NULL, NULL, NULL),
(205, 30, 46, '2026-05-08', 'Absent', NULL, NULL, NULL),
(206, 30, 49, '2026-05-08', 'Absent', NULL, NULL, NULL),
(207, 30, 50, '2026-05-08', 'Absent', NULL, NULL, NULL),
(208, 30, 51, '2026-05-08', 'Absent', NULL, NULL, NULL),
(223, 34, 5, '2026-05-08', 'Absent', NULL, NULL, NULL),
(224, 34, 23, '2026-05-08', 'Present', '2026-05-08 13:36:17', NULL, NULL),
(225, 34, 24, '2026-05-08', 'Absent', NULL, NULL, NULL),
(226, 34, 25, '2026-05-08', 'Absent', NULL, NULL, NULL),
(227, 34, 26, '2026-05-08', 'Absent', NULL, NULL, NULL),
(228, 34, 27, '2026-05-08', 'Absent', NULL, NULL, NULL),
(229, 34, 29, '2026-05-08', 'Absent', NULL, NULL, NULL),
(230, 34, 30, '2026-05-08', 'Absent', NULL, NULL, NULL),
(231, 34, 31, '2026-05-08', 'Absent', NULL, NULL, NULL),
(232, 34, 32, '2026-05-08', 'Absent', NULL, NULL, NULL),
(233, 34, 33, '2026-05-08', 'Absent', NULL, NULL, NULL),
(234, 34, 34, '2026-05-08', 'Absent', NULL, NULL, NULL),
(235, 34, 35, '2026-05-08', 'Absent', NULL, NULL, NULL),
(236, 34, 38, '2026-05-08', 'Absent', NULL, NULL, NULL),
(237, 34, 44, '2026-05-08', 'Absent', NULL, NULL, NULL),
(238, 34, 45, '2026-05-08', 'Absent', NULL, NULL, NULL),
(239, 34, 46, '2026-05-08', 'Absent', NULL, NULL, NULL),
(240, 34, 49, '2026-05-08', 'Absent', NULL, NULL, NULL),
(241, 34, 50, '2026-05-08', 'Absent', NULL, NULL, NULL),
(242, 34, 51, '2026-05-08', 'Absent', NULL, NULL, NULL),
(255, 36, 4, '2026-05-11', 'Absent', NULL, NULL, NULL),
(256, 36, 5, '2026-05-11', 'Absent', NULL, NULL, NULL),
(257, 36, 23, '2026-05-11', 'Absent', NULL, NULL, NULL),
(258, 36, 24, '2026-05-11', 'Absent', NULL, NULL, NULL),
(259, 36, 25, '2026-05-11', 'Absent', NULL, NULL, NULL),
(260, 36, 26, '2026-05-11', 'Absent', NULL, NULL, NULL),
(261, 36, 27, '2026-05-11', 'Absent', NULL, NULL, NULL),
(262, 37, 4, '2026-05-11', 'Absent', NULL, NULL, NULL),
(263, 37, 5, '2026-05-11', 'Absent', NULL, NULL, NULL),
(264, 37, 23, '2026-05-11', 'Absent', NULL, NULL, NULL),
(265, 37, 24, '2026-05-11', 'Absent', NULL, NULL, NULL),
(266, 37, 25, '2026-05-11', 'Absent', NULL, NULL, NULL),
(267, 37, 26, '2026-05-11', 'Absent', NULL, NULL, NULL),
(268, 37, 27, '2026-05-11', 'Absent', NULL, NULL, NULL),
(271, 40, 4, '2026-05-18', 'Absent', NULL, NULL, NULL),
(272, 40, 5, '2026-05-18', 'Absent', NULL, NULL, NULL),
(273, 40, 23, '2026-05-18', 'Absent', NULL, NULL, NULL),
(274, 40, 24, '2026-05-18', 'Absent', NULL, NULL, NULL),
(275, 40, 25, '2026-05-18', 'Absent', NULL, NULL, NULL),
(276, 40, 26, '2026-05-18', 'Absent', NULL, NULL, NULL),
(277, 40, 27, '2026-05-18', 'Absent', NULL, NULL, NULL),
(278, 41, 4, '2026-05-18', 'Absent', NULL, NULL, NULL),
(279, 41, 5, '2026-05-18', 'Absent', NULL, NULL, NULL),
(280, 41, 23, '2026-05-18', 'Absent', NULL, NULL, NULL),
(281, 41, 24, '2026-05-18', 'Absent', NULL, NULL, NULL),
(282, 41, 25, '2026-05-18', 'Absent', NULL, NULL, NULL),
(283, 41, 26, '2026-05-18', 'Absent', NULL, NULL, NULL),
(284, 41, 27, '2026-05-18', 'Absent', NULL, NULL, NULL),
(367, 124, 5, '2026-05-16', 'Absent', NULL, NULL, NULL),
(368, 124, 23, '2026-05-16', 'Absent', NULL, NULL, NULL),
(369, 124, 24, '2026-05-16', 'Absent', NULL, NULL, NULL),
(370, 124, 25, '2026-05-16', 'Absent', NULL, NULL, NULL),
(371, 124, 26, '2026-05-16', 'Absent', NULL, NULL, NULL),
(372, 124, 27, '2026-05-16', 'Absent', NULL, NULL, NULL),
(373, 124, 29, '2026-05-16', 'Absent', NULL, NULL, NULL),
(374, 124, 30, '2026-05-16', 'Absent', NULL, NULL, NULL),
(375, 124, 31, '2026-05-16', 'Absent', NULL, NULL, NULL),
(376, 124, 32, '2026-05-16', 'Absent', NULL, NULL, NULL),
(377, 124, 33, '2026-05-16', 'Absent', NULL, NULL, NULL),
(378, 124, 34, '2026-05-16', 'Absent', NULL, NULL, NULL),
(379, 124, 35, '2026-05-16', 'Absent', NULL, NULL, NULL),
(380, 124, 38, '2026-05-16', 'Absent', NULL, NULL, NULL),
(381, 124, 44, '2026-05-16', 'Absent', NULL, NULL, NULL),
(382, 124, 45, '2026-05-16', 'Absent', NULL, NULL, NULL),
(383, 124, 46, '2026-05-16', 'Absent', NULL, NULL, NULL),
(384, 124, 49, '2026-05-16', 'Absent', NULL, NULL, NULL),
(385, 124, 50, '2026-05-16', 'Absent', NULL, NULL, NULL),
(386, 124, 51, '2026-05-16', 'Absent', NULL, NULL, NULL),
(392, 130, 5, '2026-05-16', 'Absent', NULL, NULL, NULL),
(393, 130, 23, '2026-05-16', 'Absent', NULL, NULL, NULL),
(394, 130, 24, '2026-05-16', 'Absent', NULL, NULL, NULL),
(395, 130, 25, '2026-05-16', 'Absent', NULL, NULL, NULL),
(396, 130, 26, '2026-05-16', 'Absent', NULL, NULL, NULL),
(397, 130, 27, '2026-05-16', 'Absent', NULL, NULL, NULL),
(398, 130, 29, '2026-05-16', 'Present', '2026-05-16 21:34:56', NULL, NULL),
(399, 130, 30, '2026-05-16', 'Absent', NULL, NULL, NULL),
(400, 130, 31, '2026-05-16', 'Absent', NULL, NULL, NULL),
(401, 130, 32, '2026-05-16', 'Absent', NULL, NULL, NULL),
(402, 130, 33, '2026-05-16', 'Absent', NULL, NULL, NULL),
(403, 130, 34, '2026-05-16', 'Absent', NULL, NULL, NULL),
(404, 130, 35, '2026-05-16', 'Absent', NULL, NULL, NULL),
(405, 130, 38, '2026-05-16', 'Absent', NULL, NULL, NULL),
(406, 130, 44, '2026-05-16', 'Absent', NULL, NULL, NULL),
(407, 130, 45, '2026-05-16', 'Absent', NULL, NULL, NULL),
(408, 130, 46, '2026-05-16', 'Absent', NULL, NULL, NULL),
(409, 130, 49, '2026-05-16', 'Absent', NULL, NULL, NULL),
(410, 130, 50, '2026-05-16', 'Absent', NULL, NULL, NULL),
(411, 130, 51, '2026-05-16', 'Absent', NULL, NULL, NULL),
(433, 141, 4, '2026-05-25', 'Absent', NULL, NULL, NULL),
(434, 141, 5, '2026-05-25', 'Absent', NULL, NULL, NULL),
(435, 141, 23, '2026-05-25', 'Absent', NULL, NULL, NULL),
(436, 141, 24, '2026-05-25', 'Absent', NULL, NULL, NULL),
(437, 141, 25, '2026-05-25', 'Absent', NULL, NULL, NULL),
(438, 141, 26, '2026-05-25', 'Absent', NULL, NULL, NULL),
(439, 141, 27, '2026-05-25', 'Absent', NULL, NULL, NULL),
(440, 142, 4, '2026-05-25', 'Absent', NULL, NULL, NULL),
(441, 142, 5, '2026-05-25', 'Absent', NULL, NULL, NULL),
(442, 142, 23, '2026-05-25', 'Absent', NULL, NULL, NULL),
(443, 142, 24, '2026-05-25', 'Absent', NULL, NULL, NULL),
(444, 142, 25, '2026-05-25', 'Absent', NULL, NULL, NULL),
(445, 142, 26, '2026-05-25', 'Absent', NULL, NULL, NULL),
(446, 142, 27, '2026-05-25', 'Absent', NULL, NULL, NULL),
(493, 189, 1, '2026-05-21', 'Absent', NULL, NULL, NULL),
(494, 189, 5, '2026-05-21', 'Absent', NULL, NULL, NULL),
(495, 189, 23, '2026-05-21', 'Absent', NULL, NULL, NULL),
(496, 189, 24, '2026-05-21', 'Absent', NULL, NULL, NULL),
(497, 189, 25, '2026-05-21', 'Absent', NULL, NULL, NULL),
(498, 189, 26, '2026-05-21', 'Absent', NULL, NULL, NULL),
(499, 189, 27, '2026-05-21', 'Absent', NULL, NULL, NULL),
(500, 189, 29, '2026-05-21', 'Absent', NULL, NULL, NULL),
(501, 189, 30, '2026-05-21', 'Present', '2026-05-21 12:54:58', NULL, NULL),
(502, 189, 31, '2026-05-21', 'Absent', NULL, NULL, NULL),
(503, 189, 32, '2026-05-21', 'Absent', NULL, NULL, NULL),
(504, 189, 33, '2026-05-21', 'Absent', NULL, NULL, NULL),
(505, 189, 34, '2026-05-21', 'Absent', NULL, NULL, NULL),
(506, 189, 35, '2026-05-21', 'Absent', NULL, NULL, NULL),
(507, 189, 38, '2026-05-21', 'Absent', NULL, NULL, NULL),
(508, 189, 44, '2026-05-21', 'Absent', NULL, NULL, NULL),
(509, 189, 45, '2026-05-21', 'Absent', NULL, NULL, NULL),
(510, 189, 46, '2026-05-21', 'Absent', NULL, NULL, NULL),
(511, 189, 47, '2026-05-21', 'Absent', NULL, NULL, NULL),
(512, 189, 49, '2026-05-21', 'Absent', NULL, NULL, NULL),
(513, 189, 50, '2026-05-21', 'Absent', NULL, NULL, NULL),
(514, 189, 51, '2026-05-21', 'Absent', NULL, NULL, NULL),
(515, 189, 108, '2026-05-21', 'Absent', NULL, NULL, NULL),
(516, 189, 111, '2026-05-21', 'Absent', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `event_instances`
--

CREATE TABLE `event_instances` (
  `instance_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `event_date` date NOT NULL,
  `status` enum('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `event_instances`
--

INSERT INTO `event_instances` (`instance_id`, `event_id`, `event_date`, `status`) VALUES
(1, 3, '2026-04-15', 'Scheduled'),
(2, 4, '2026-04-15', 'Scheduled'),
(3, 5, '2026-04-24', 'Scheduled'),
(4, 6, '2026-05-09', 'Scheduled'),
(5, 7, '2026-04-30', 'Scheduled'),
(6, 1, '2026-04-27', 'Scheduled'),
(7, 2, '2026-04-27', 'Scheduled'),
(10, 8, '2026-05-01', 'Scheduled'),
(20, 9, '2026-05-02', 'Scheduled'),
(23, 1, '2026-05-04', 'Scheduled'),
(24, 2, '2026-05-04', 'Scheduled'),
(26, 10, '2026-05-07', 'Scheduled'),
(27, 11, '2026-05-08', 'Scheduled'),
(30, 12, '2026-05-08', 'Scheduled'),
(34, 13, '2026-05-08', 'Scheduled'),
(36, 1, '2026-05-11', 'Scheduled'),
(37, 2, '2026-05-11', 'Scheduled'),
(40, 1, '2026-05-18', 'Scheduled'),
(41, 2, '2026-05-18', 'Scheduled'),
(124, 14, '2026-05-16', 'Scheduled'),
(130, 15, '2026-05-16', 'Scheduled'),
(141, 1, '2026-05-25', 'Scheduled'),
(142, 2, '2026-05-25', 'Scheduled'),
(189, 16, '2026-05-21', 'Scheduled');

-- --------------------------------------------------------

--
-- Table structure for table `event_log`
--

CREATE TABLE `event_log` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `event_id` int(11) NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `log_type` enum('Entry','Exit') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `event_log`
--

INSERT INTO `event_log` (`log_id`, `user_id`, `event_id`, `timestamp`, `log_type`) VALUES
(1, 5, 3, '2026-04-15 21:10:55', 'Entry'),
(2, 5, 4, '2026-04-15 21:33:04', 'Entry'),
(3, 5, 4, '2026-04-15 21:33:11', 'Exit'),
(4, 5, 4, '2026-04-15 21:35:00', 'Entry'),
(5, 5, 4, '2026-04-15 21:35:06', 'Exit'),
(6, 45, 8, '2026-05-01 23:00:26', 'Entry'),
(7, 44, 8, '2026-05-01 23:00:33', 'Entry'),
(8, 38, 8, '2026-05-01 23:01:33', 'Entry'),
(9, 44, 8, '2026-05-01 23:01:39', 'Exit'),
(10, 38, 8, '2026-05-01 23:01:47', 'Exit'),
(11, 44, 8, '2026-05-01 23:01:53', 'Entry'),
(12, 44, 8, '2026-05-01 23:02:02', 'Exit'),
(13, 44, 8, '2026-05-01 23:22:17', 'Entry'),
(14, 29, 8, '2026-05-01 23:22:25', 'Entry'),
(15, 29, 9, '2026-05-02 16:15:35', 'Entry'),
(16, 29, 9, '2026-05-02 16:15:42', 'Exit'),
(17, 23, 11, '2026-05-08 12:31:08', 'Entry'),
(18, 23, 11, '2026-05-08 12:31:16', 'Exit'),
(19, 24, 12, '2026-05-08 12:37:01', 'Entry'),
(20, 26, 12, '2026-05-08 12:38:36', 'Entry'),
(21, 27, 12, '2026-05-08 12:48:52', 'Entry'),
(22, 23, 13, '2026-05-08 13:36:16', 'Entry'),
(23, 29, 15, '2026-05-16 21:34:56', 'Entry'),
(24, 30, 16, '2026-05-21 12:54:58', 'Entry');

-- --------------------------------------------------------

--
-- Table structure for table `event_participants`
--

CREATE TABLE `event_participants` (
  `event_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
(4, 27),
(5, 4),
(5, 5),
(5, 23),
(5, 24),
(5, 25),
(5, 26),
(5, 27),
(6, 4),
(6, 5),
(6, 23),
(6, 24),
(6, 25),
(6, 26),
(6, 27),
(7, 4),
(7, 5),
(7, 23),
(7, 24),
(7, 25),
(7, 26),
(7, 27),
(8, 5),
(8, 23),
(8, 24),
(8, 25),
(8, 26),
(8, 27),
(8, 29),
(8, 30),
(8, 31),
(8, 32),
(8, 33),
(8, 34),
(8, 35),
(8, 38),
(8, 44),
(8, 45),
(8, 46),
(8, 49),
(8, 50),
(8, 51),
(9, 5),
(9, 23),
(9, 24),
(9, 25),
(9, 26),
(9, 27),
(9, 29),
(9, 30),
(9, 31),
(9, 32),
(9, 33),
(9, 34),
(9, 35),
(9, 38),
(9, 44),
(9, 45),
(9, 46),
(9, 49),
(9, 50),
(9, 51),
(10, 5),
(10, 23),
(10, 24),
(10, 25),
(10, 26),
(10, 27),
(10, 29),
(10, 30),
(10, 31),
(10, 32),
(10, 33),
(10, 34),
(10, 35),
(10, 38),
(10, 44),
(10, 45),
(10, 46),
(10, 49),
(10, 50),
(10, 51),
(11, 5),
(11, 23),
(11, 24),
(11, 25),
(11, 26),
(11, 27),
(11, 29),
(11, 30),
(11, 31),
(11, 32),
(11, 33),
(11, 34),
(11, 35),
(11, 38),
(11, 44),
(11, 45),
(11, 46),
(11, 49),
(11, 50),
(11, 51),
(12, 5),
(12, 23),
(12, 24),
(12, 25),
(12, 26),
(12, 27),
(12, 29),
(12, 30),
(12, 31),
(12, 32),
(12, 33),
(12, 34),
(12, 35),
(12, 38),
(12, 44),
(12, 45),
(12, 46),
(12, 49),
(12, 50),
(12, 51),
(13, 5),
(13, 23),
(13, 24),
(13, 25),
(13, 26),
(13, 27),
(13, 29),
(13, 30),
(13, 31),
(13, 32),
(13, 33),
(13, 34),
(13, 35),
(13, 38),
(13, 44),
(13, 45),
(13, 46),
(13, 49),
(13, 50),
(13, 51),
(14, 5),
(14, 23),
(14, 24),
(14, 25),
(14, 26),
(14, 27),
(14, 29),
(14, 30),
(14, 31),
(14, 32),
(14, 33),
(14, 34),
(14, 35),
(14, 38),
(14, 44),
(14, 45),
(14, 46),
(14, 49),
(14, 50),
(14, 51),
(15, 5),
(15, 23),
(15, 24),
(15, 25),
(15, 26),
(15, 27),
(15, 29),
(15, 30),
(15, 31),
(15, 32),
(15, 33),
(15, 34),
(15, 35),
(15, 38),
(15, 44),
(15, 45),
(15, 46),
(15, 49),
(15, 50),
(15, 51),
(16, 1),
(16, 5),
(16, 23),
(16, 24),
(16, 25),
(16, 26),
(16, 27),
(16, 29),
(16, 30),
(16, 31),
(16, 32),
(16, 33),
(16, 34),
(16, 35),
(16, 38),
(16, 44),
(16, 45),
(16, 46),
(16, 47),
(16, 49),
(16, 50),
(16, 51),
(16, 108),
(16, 111);

-- --------------------------------------------------------

--
-- Table structure for table `general_log`
--

CREATE TABLE `general_log` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `log_type` enum('Entry','Exit') DEFAULT NULL,
  `gate` enum('Gate 1','Gate 2','Gate 3') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
(56, 5, '2026-04-15 21:36:17', 'Exit', 'Gate 2'),
(57, 28, '2026-04-24 00:09:17', 'Entry', 'Gate 1'),
(58, 28, '2026-04-24 00:10:13', 'Exit', 'Gate 2'),
(59, 28, '2026-04-24 04:09:59', 'Entry', 'Gate 1'),
(60, 28, '2026-04-24 04:10:06', 'Exit', 'Gate 2'),
(61, 28, '2026-04-24 04:10:54', 'Entry', 'Gate 1'),
(62, 28, '2026-04-24 04:11:01', 'Exit', 'Gate 2'),
(63, 28, '2026-04-24 04:11:16', 'Entry', 'Gate 1'),
(64, 28, '2026-04-24 04:11:23', 'Exit', 'Gate 2'),
(65, 28, '2026-04-24 04:15:47', 'Entry', 'Gate 1'),
(66, 28, '2026-04-24 04:16:21', 'Exit', 'Gate 2'),
(67, 28, '2026-04-24 04:16:25', 'Entry', 'Gate 1'),
(68, 1, '2026-04-26 17:35:27', 'Entry', 'Gate 1'),
(69, 1, '2026-04-26 17:35:46', 'Exit', 'Gate 2'),
(70, 1, '2026-04-26 17:35:53', 'Entry', 'Gate 1'),
(71, 1, '2026-04-26 22:56:55', 'Exit', 'Gate 2'),
(72, 1, '2026-04-26 22:57:07', 'Entry', 'Gate 1'),
(73, 1, '2026-04-26 22:57:23', 'Exit', 'Gate 2'),
(74, 1, '2026-04-27 22:43:09', 'Entry', 'Gate 1'),
(75, 1, '2026-04-27 22:43:20', 'Exit', 'Gate 2'),
(76, 1, '2026-04-28 13:13:02', 'Entry', 'Gate 1'),
(77, 1, '2026-04-28 13:13:18', 'Exit', 'Gate 2'),
(78, 1, '2026-04-30 19:31:42', 'Entry', 'Gate 1'),
(79, 36, '2026-04-30 19:31:57', 'Entry', 'Gate 1'),
(80, 37, '2026-04-30 19:32:07', 'Entry', 'Gate 1'),
(81, 1, '2026-04-30 19:32:17', 'Exit', 'Gate 2'),
(82, 1, '2026-05-01 19:55:02', 'Entry', 'Gate 1'),
(83, 1, '2026-05-01 19:55:12', 'Exit', 'Gate 2'),
(84, 1, '2026-05-01 19:56:44', 'Entry', 'Gate 1'),
(85, 1, '2026-05-01 20:10:14', 'Exit', 'Gate 2'),
(86, 1, '2026-05-01 20:10:22', 'Entry', 'Gate 1'),
(87, 1, '2026-05-01 20:11:51', 'Exit', 'Gate 2'),
(88, 45, '2026-05-01 23:00:26', 'Entry', 'Gate 1'),
(89, 44, '2026-05-01 23:00:33', 'Entry', 'Gate 1'),
(90, 38, '2026-05-01 23:01:33', 'Entry', 'Gate 1'),
(91, 44, '2026-05-01 23:01:39', 'Exit', 'Gate 2'),
(92, 38, '2026-05-01 23:01:47', 'Exit', 'Gate 2'),
(93, 44, '2026-05-01 23:01:53', 'Entry', 'Gate 1'),
(94, 44, '2026-05-01 23:02:02', 'Exit', 'Gate 2'),
(95, 44, '2026-05-01 23:22:17', 'Entry', 'Gate 1'),
(96, 29, '2026-05-01 23:22:25', 'Entry', 'Gate 1'),
(97, 1, '2026-05-02 15:59:06', 'Entry', 'Gate 1'),
(98, 1, '2026-05-02 16:00:18', 'Exit', 'Gate 2'),
(99, 1, '2026-05-02 16:06:24', 'Entry', 'Gate 1'),
(100, 1, '2026-05-02 16:06:42', 'Exit', 'Gate 2'),
(101, 29, '2026-05-02 16:15:35', 'Entry', 'Gate 1'),
(102, 29, '2026-05-02 16:15:42', 'Exit', 'Gate 2'),
(103, 1, '2026-05-02 16:44:36', 'Entry', 'Gate 1'),
(104, 1, '2026-05-02 16:44:57', 'Exit', 'Gate 2'),
(105, 1, '2026-05-02 16:45:35', 'Entry', 'Gate 1'),
(106, 1, '2026-05-02 16:46:07', 'Exit', 'Gate 2'),
(107, 19, '2026-05-07 20:30:01', 'Entry', 'Gate 1'),
(108, 19, '2026-05-07 20:28:09', 'Exit', 'Gate 2'),
(109, 19, '2026-05-07 20:31:18', 'Entry', 'Gate 1'),
(110, 19, '2026-05-07 20:29:23', 'Exit', 'Gate 2'),
(111, 19, '2026-05-08 12:27:45', 'Entry', 'Gate 1'),
(112, 23, '2026-05-08 12:31:07', 'Entry', 'Gate 1'),
(113, 23, '2026-05-08 12:31:14', 'Exit', 'Gate 2'),
(114, 24, '2026-05-08 12:37:00', 'Entry', 'Gate 1'),
(115, 26, '2026-05-08 12:38:34', 'Entry', 'Gate 1'),
(116, 27, '2026-05-08 12:48:51', 'Entry', 'Gate 1'),
(117, 68, '2026-05-08 12:50:15', 'Entry', 'Gate 1'),
(118, 68, '2026-05-08 12:50:37', 'Exit', 'Gate 2'),
(119, 19, '2026-05-08 13:03:19', 'Exit', 'Gate 2'),
(120, 87, '2026-05-08 13:07:56', 'Entry', 'Gate 1'),
(121, 88, '2026-05-08 13:07:56', 'Entry', 'Gate 1'),
(122, 89, '2026-05-08 13:07:56', 'Entry', 'Gate 1'),
(123, 58, '2026-05-08 13:10:30', 'Entry', 'Gate 1'),
(124, 58, '2026-05-08 13:10:46', 'Exit', 'Gate 2'),
(125, 58, '2026-05-08 13:11:54', 'Entry', 'Gate 1'),
(126, 66, '2026-05-08 13:11:59', 'Entry', 'Gate 1'),
(127, 56, '2026-05-08 13:12:13', 'Entry', 'Gate 1'),
(128, 1, '2026-05-08 13:12:17', 'Entry', 'Gate 1'),
(129, 68, '2026-05-08 13:12:49', 'Entry', 'Gate 1'),
(130, 90, '2026-05-08 13:15:32', 'Entry', 'Gate 1'),
(131, 1, '2026-05-08 13:17:42', 'Exit', 'Gate 2'),
(132, 66, '2026-05-08 13:17:46', 'Exit', 'Gate 2'),
(133, 78, '2026-05-08 13:18:06', 'Entry', 'Gate 1'),
(134, 78, '2026-05-08 13:18:22', 'Exit', 'Gate 2'),
(135, 90, '2026-05-08 13:17:14', 'Exit', 'Gate 2'),
(136, 66, '2026-05-08 13:27:40', 'Entry', 'Gate 1'),
(137, 78, '2026-05-08 13:28:15', 'Entry', 'Gate 1'),
(138, 54, '2026-05-08 13:28:23', 'Entry', 'Gate 1'),
(139, 60, '2026-05-08 13:28:29', 'Entry', 'Gate 1'),
(140, 81, '2026-05-08 13:28:49', 'Entry', 'Gate 1'),
(141, 59, '2026-05-08 13:28:55', 'Entry', 'Gate 1'),
(142, 57, '2026-05-08 13:28:59', 'Entry', 'Gate 1'),
(143, 53, '2026-05-08 13:29:03', 'Entry', 'Gate 1'),
(144, 64, '2026-05-08 13:29:28', 'Entry', 'Gate 1'),
(145, 85, '2026-05-08 13:29:33', 'Entry', 'Gate 1'),
(146, 77, '2026-05-08 13:29:37', 'Entry', 'Gate 1'),
(147, 72, '2026-05-08 13:29:52', 'Entry', 'Gate 1'),
(148, 75, '2026-05-08 13:30:19', 'Entry', 'Gate 1'),
(149, 76, '2026-05-08 13:30:27', 'Entry', 'Gate 1'),
(150, 63, '2026-05-08 13:30:41', 'Entry', 'Gate 1'),
(151, 65, '2026-05-08 13:30:59', 'Entry', 'Gate 1'),
(152, 74, '2026-05-08 13:31:05', 'Entry', 'Gate 1'),
(153, 61, '2026-05-08 13:31:10', 'Entry', 'Gate 1'),
(154, 55, '2026-05-08 13:31:15', 'Entry', 'Gate 1'),
(155, 79, '2026-05-08 13:31:19', 'Entry', 'Gate 1'),
(156, 71, '2026-05-08 13:31:25', 'Entry', 'Gate 1'),
(157, 73, '2026-05-08 13:31:32', 'Entry', 'Gate 1'),
(158, 86, '2026-05-08 13:31:54', 'Entry', 'Gate 1'),
(159, 67, '2026-05-08 13:32:00', 'Entry', 'Gate 1'),
(160, 70, '2026-05-08 13:32:33', 'Entry', 'Gate 1'),
(161, 52, '2026-05-08 13:32:37', 'Entry', 'Gate 1'),
(162, 1, '2026-05-08 13:32:46', 'Entry', 'Gate 1'),
(163, 82, '2026-05-08 13:33:30', 'Entry', 'Gate 1'),
(164, 80, '2026-05-08 13:33:51', 'Entry', 'Gate 1'),
(165, 83, '2026-05-08 13:36:02', 'Entry', 'Gate 1'),
(166, 69, '2026-05-08 13:36:11', 'Entry', 'Gate 1'),
(167, 23, '2026-05-08 13:36:15', 'Entry', 'Gate 1'),
(168, 64, '2026-05-08 13:37:40', 'Exit', 'Gate 2'),
(169, 66, '2026-05-08 13:37:50', 'Exit', 'Gate 2'),
(170, 57, '2026-05-08 13:37:56', 'Exit', 'Gate 2'),
(171, 54, '2026-05-08 13:37:59', 'Exit', 'Gate 2'),
(172, 76, '2026-05-08 13:38:05', 'Exit', 'Gate 2'),
(173, 65, '2026-05-08 13:38:08', 'Exit', 'Gate 2'),
(174, 59, '2026-05-08 13:38:12', 'Exit', 'Gate 2'),
(175, 85, '2026-05-08 13:38:19', 'Exit', 'Gate 2'),
(176, 67, '2026-05-08 13:38:23', 'Exit', 'Gate 2'),
(177, 77, '2026-05-08 13:38:27', 'Exit', 'Gate 2'),
(178, 72, '2026-05-08 13:38:31', 'Exit', 'Gate 2'),
(179, 75, '2026-05-08 13:38:36', 'Exit', 'Gate 2'),
(180, 71, '2026-05-08 13:38:40', 'Exit', 'Gate 2'),
(181, 63, '2026-05-08 13:38:46', 'Exit', 'Gate 2'),
(182, 70, '2026-05-08 13:38:59', 'Exit', 'Gate 2'),
(183, 74, '2026-05-08 13:39:04', 'Exit', 'Gate 2'),
(184, 81, '2026-05-08 13:39:09', 'Exit', 'Gate 2'),
(185, 61, '2026-05-08 13:39:14', 'Exit', 'Gate 2'),
(186, 79, '2026-05-08 13:39:19', 'Exit', 'Gate 2'),
(187, 86, '2026-05-08 13:39:24', 'Exit', 'Gate 2'),
(188, 55, '2026-05-08 13:39:30', 'Exit', 'Gate 2'),
(189, 78, '2026-05-08 13:39:39', 'Exit', 'Gate 2'),
(190, 53, '2026-05-08 13:40:13', 'Exit', 'Gate 2'),
(191, 69, '2026-05-08 13:40:15', 'Exit', 'Gate 2'),
(192, 52, '2026-05-08 13:40:17', 'Exit', 'Gate 2'),
(193, 60, '2026-05-08 13:40:21', 'Exit', 'Gate 2'),
(194, 83, '2026-05-08 13:40:31', 'Exit', 'Gate 2'),
(195, 82, '2026-05-08 13:40:38', 'Exit', 'Gate 2'),
(196, 80, '2026-05-08 13:40:42', 'Exit', 'Gate 2'),
(197, 19, '2026-05-08 13:41:54', 'Entry', 'Gate 1'),
(198, 56, '2026-05-08 13:41:58', 'Exit', 'Gate 2'),
(199, 19, '2026-05-08 13:42:07', 'Exit', 'Gate 2'),
(200, 1, '2026-05-08 13:43:27', 'Exit', 'Gate 2'),
(201, 73, '2026-05-08 13:44:02', 'Exit', 'Gate 2'),
(202, 1, '2026-05-11 00:34:25', 'Entry', 'Gate 1'),
(203, 1, '2026-05-11 00:34:52', 'Exit', 'Gate 2'),
(204, 1, '2026-05-11 00:35:06', 'Entry', 'Gate 1'),
(205, 1, '2026-05-11 00:35:18', 'Exit', 'Gate 2'),
(206, 1, '2026-05-11 00:39:54', 'Entry', 'Gate 1'),
(207, 1, '2026-05-11 00:40:17', 'Exit', 'Gate 2'),
(208, 1, '2026-05-11 00:42:15', 'Entry', 'Gate 1'),
(209, 1, '2026-05-11 00:42:27', 'Exit', 'Gate 2'),
(210, 1, '2026-05-11 00:46:45', 'Entry', 'Gate 1'),
(211, 1, '2026-05-11 00:47:13', 'Exit', 'Gate 2'),
(212, 91, '2026-05-11 00:47:30', 'Entry', 'Gate 1'),
(213, 1, '2026-05-11 01:26:54', 'Entry', 'Gate 1'),
(214, 1, '2026-05-11 01:27:09', 'Exit', 'Gate 2'),
(215, 1, '2026-05-11 01:44:18', 'Entry', 'Gate 1'),
(216, 92, '2026-05-11 01:44:27', 'Entry', 'Gate 1'),
(217, 1, '2026-05-11 01:44:43', 'Exit', 'Gate 2'),
(218, 1, '2026-05-11 01:49:23', 'Entry', 'Gate 1'),
(219, 1, '2026-05-11 01:49:41', 'Exit', 'Gate 2'),
(220, 1, '2026-05-11 23:24:06', 'Entry', 'Gate 1'),
(221, 1, '2026-05-11 23:24:18', 'Exit', 'Gate 2'),
(222, 1, '2026-05-11 23:40:37', 'Entry', 'Gate 1'),
(223, 1, '2026-05-11 23:49:02', 'Exit', 'Gate 2'),
(224, 1, '2026-05-12 00:01:51', 'Entry', 'Gate 1'),
(225, 1, '2026-05-12 00:09:09', 'Exit', 'Gate 2'),
(226, 3, '2026-05-12 00:10:10', 'Exit', 'Gate 2'),
(227, 3, '2026-05-12 00:10:23', 'Entry', 'Gate 1'),
(228, 3, '2026-05-12 00:10:29', 'Exit', 'Gate 2'),
(229, 58, '2026-05-12 15:24:39', 'Exit', 'Gate 2'),
(230, 93, '2026-05-12 15:38:09', 'Entry', 'Gate 1'),
(231, 1, '2026-05-12 16:20:22', 'Entry', 'Gate 1'),
(232, 93, '2026-05-12 16:26:39', 'Exit', 'Gate 2'),
(233, 1, '2026-05-12 16:26:45', 'Exit', 'Gate 2'),
(234, 1, '2026-05-12 16:27:58', 'Entry', 'Gate 1'),
(235, 1, '2026-05-12 16:28:12', 'Exit', 'Gate 2'),
(236, 1, '2026-05-12 16:28:23', 'Entry', 'Gate 1'),
(237, 1, '2026-05-12 16:28:28', 'Exit', 'Gate 2'),
(238, 1, '2026-05-12 16:30:00', 'Entry', 'Gate 1'),
(239, 1, '2026-05-12 16:30:27', 'Exit', 'Gate 2'),
(240, 1, '2026-05-12 21:45:36', 'Entry', 'Gate 1'),
(241, 1, '2026-05-12 21:46:24', 'Exit', 'Gate 2'),
(242, 1, '2026-05-15 17:11:05', 'Entry', 'Gate 1'),
(243, 1, '2026-05-15 17:11:24', 'Exit', 'Gate 2'),
(244, 1, '2026-05-15 18:03:46', 'Entry', 'Gate 1'),
(245, 1, '2026-05-15 18:04:02', 'Exit', 'Gate 2'),
(246, 94, '2026-05-16 01:33:11', 'Entry', 'Gate 1'),
(247, 95, '2026-05-16 17:16:09', 'Entry', 'Gate 1'),
(248, 96, '2026-05-16 17:16:09', 'Entry', 'Gate 1'),
(249, 97, '2026-05-16 17:16:09', 'Entry', 'Gate 1'),
(250, 98, '2026-05-16 18:13:51', 'Entry', 'Gate 1'),
(251, 99, '2026-05-16 18:13:51', 'Entry', 'Gate 1'),
(252, 100, '2026-05-16 18:13:51', 'Entry', 'Gate 1'),
(253, 29, '2026-05-16 21:34:56', 'Entry', 'Gate 1'),
(254, 101, '2026-05-20 21:24:31', 'Entry', 'Gate 1'),
(255, 102, '2026-05-20 21:24:31', 'Entry', 'Gate 1'),
(256, 103, '2026-05-20 21:24:31', 'Entry', 'Gate 1'),
(257, 104, '2026-05-20 21:25:00', 'Entry', 'Gate 1'),
(258, 104, '2026-05-20 21:25:57', 'Exit', 'Gate 2'),
(259, 69, '2026-05-20 21:30:52', 'Entry', 'Gate 1'),
(260, 69, '2026-05-20 21:31:37', 'Exit', 'Gate 2'),
(261, 19, '2026-05-07 20:30:39', 'Exit', 'Gate 2'),
(262, 19, '2026-05-07 20:31:48', 'Exit', 'Gate 2'),
(263, 58, '2026-05-08 13:12:54', 'Exit', 'Gate 2'),
(264, 68, '2026-05-08 13:13:49', 'Exit', 'Gate 2'),
(265, 1, '2026-05-20 21:44:50', 'Entry', 'Gate 1'),
(266, 1, '2026-05-20 21:45:11', 'Exit', 'Gate 2'),
(267, 1, '2026-05-20 21:47:52', 'Entry', 'Gate 1'),
(268, 109, '2026-05-20 23:55:14', 'Entry', 'Gate 1'),
(269, 1, '2026-05-21 12:52:34', 'Exit', 'Gate 2'),
(270, 1, '2026-05-21 12:52:45', 'Entry', 'Gate 1'),
(271, 30, '2026-05-21 12:54:58', 'Entry', 'Gate 1'),
(272, 1, '2026-05-21 13:09:07', 'Exit', 'Gate 2'),
(273, 1, '2026-05-21 13:10:10', 'Entry', 'Gate 1');

-- --------------------------------------------------------

--
-- Table structure for table `paging_alerts`
--

CREATE TABLE `paging_alerts` (
  `alert_id` int(11) NOT NULL,
  `from_source` varchar(120) NOT NULL,
  `message` text NOT NULL,
  `visibility_scope` enum('global','targeted','departmental','event_specific') NOT NULL DEFAULT 'global',
  `target_id` varchar(64) DEFAULT NULL,
  `target_department` varchar(150) DEFAULT NULL,
  `target_event` varchar(255) DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `report_id` int(11) NOT NULL,
  `report_name` varchar(100) NOT NULL,
  `generated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `generated_by` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `user_id` int(11) NOT NULL,
  `student_id` varchar(8) NOT NULL,
  `student_name` varchar(80) DEFAULT NULL,
  `student_type` enum('regular','irregular') NOT NULL DEFAULT 'regular',
  `course_id` int(11) NOT NULL,
  `status` enum('Inside','Outside') DEFAULT 'Outside',
  `stud_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`user_id`, `student_id`, `student_name`, `student_type`, `course_id`, `status`, `stud_last_updated`) VALUES
(2, '22-01582', 'Jose Rizal', 'irregular', 1, 'Outside', '2026-05-20 15:53:05'),
(110, '23-00078', 'Wiz Khalifa', 'regular', 8, 'Outside', '2026-05-20 17:11:46'),
(84, '23-00162', 'VENTURA, CARL VINCENT T.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(52, '23-00177', 'ABARADO JR., ARMANDO R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(83, '23-00182', 'TORRALBA, XERXES JAN R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(78, '23-00198', 'PAGSUYUIN, WARREN V.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(62, '23-00219', 'CASTILLO, JESTALY JOSEPH A.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(66, '23-00227', 'DELA CRUZ, DENISE J.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(82, '23-00230', 'TEOPACO, MARK JEROME B.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(71, '23-00232', 'LAWANG, HARRY B.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(72, '23-00233', 'LLAVE, ALRAZEL R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(57, '23-00240', 'BETONIO, CHARLES JEFFERSON A.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(54, '23-00242', 'AUSTRIA, NEON LOUIS M.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(59, '23-00252', 'CABUG, JOHN AIM VREZYMIER T.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(65, '23-00253', 'DAHUG, JENNEFER A.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(85, '23-00271', 'VILLAMOR, MA. GABRIELLE V.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(69, '23-00276', 'INOCENCIO, RON ALEXANDER A.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(64, '23-00278', 'CUEVAS, RENZO U.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(79, '23-00279', 'RAMOS, JAMES S.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(55, '23-00286', 'BALTAZAR, ALLIAH KIANA R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(58, '23-00291', 'BUETA, MARK JOSHUA R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(61, '23-00297', 'CAGUIOA, TRISHA T.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(77, '23-00302', 'PACAMPARA JR., ARMANDO B.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(70, '23-00305', 'JUANILLAS, JAMIELIN BERYL', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(67, '23-00310', 'GAPOL, FRANCIS ADRIAN H.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(19, '23-00312', 'JERICHO PAUL D. SALVADOR', 'regular', 4, 'Outside', '2026-05-20 15:47:45'),
(1, '23-00314', 'RECTO, JASON JAY M.', 'regular', 5, 'Inside', '2026-05-21 05:10:10'),
(60, '23-00318', 'CABUGUANG, JUAN MIGUEL P.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(76, '23-00322', 'ONDA, JULIA ASHLEY C.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(63, '23-00337', 'CRESPO, KARL JOHN P.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(86, '23-00722', 'VITO, JOSHUA DANIEL S.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(80, '23-00952', 'RONQUILLO, CARL C.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(53, '23-01048', 'ALVIS, DAVID ANDREI R.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(73, '23-01066', 'LOPEZ, MARVIN S.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(75, '23-01067', 'MARTINEZ, NATHAN JOHN I.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(74, '23-01110', 'MANGONDATO, JEZPEARL C.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(56, '23-01120', 'BERNABE, MARY JOY C.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(68, '23-01263', 'GUNGON, KARL ISHMAEL L.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(3, '24-00101', 'Andres Bonifacio', 'irregular', 3, 'Outside', '2026-05-20 15:53:05'),
(39, '24-00102', 'Maria Santos', 'irregular', 5, 'Outside', '2026-05-20 15:53:05'),
(42, '24-00254', 'Sasuke Uchiha', 'irregular', 5, 'Outside', '2026-05-20 15:53:05'),
(43, '24-00256', 'Madara Uchiha', 'irregular', 7, 'Outside', '2026-05-20 15:53:05'),
(48, '24-00458', 'Martin Del Rosario', 'irregular', 1, 'Outside', '2026-05-20 15:53:05'),
(81, '24-01203', 'SESE, MARY YNAH BRAZIL A.', 'regular', 3, 'Outside', '2026-05-20 15:49:14'),
(40, '26-00251', 'Kulangot', 'irregular', 3, 'Outside', '2026-05-20 15:53:05'),
(41, '26-00252', 'Naruto', 'irregular', 5, 'Outside', '2026-05-20 15:53:05');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `role` enum('student','employee','visitor','admin') NOT NULL,
  `active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `role`, `active`) VALUES
(1, 'student', 1),
(2, 'student', 1),
(3, 'student', 1),
(4, 'employee', 0),
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
(21, 'admin', 1),
(22, 'student', 1),
(23, 'employee', 1),
(24, 'employee', 1),
(25, 'employee', 1),
(26, 'employee', 1),
(27, 'employee', 1),
(28, 'visitor', 0),
(29, 'employee', 1),
(30, 'employee', 1),
(31, 'employee', 1),
(32, 'employee', 1),
(33, 'employee', 1),
(34, 'employee', 1),
(35, 'employee', 1),
(36, 'visitor', 0),
(37, 'visitor', 0),
(38, 'employee', 1),
(39, 'student', 1),
(40, 'student', 1),
(41, 'student', 1),
(42, 'student', 1),
(43, 'student', 1),
(44, 'employee', 1),
(45, 'employee', 1),
(46, 'employee', 1),
(47, 'employee', 1),
(48, 'student', 0),
(49, 'employee', 1),
(50, 'employee', 1),
(51, 'employee', 1),
(52, 'student', 1),
(53, 'student', 1),
(54, 'student', 1),
(55, 'student', 1),
(56, 'student', 1),
(57, 'student', 1),
(58, 'student', 1),
(59, 'student', 1),
(60, 'student', 1),
(61, 'student', 1),
(62, 'student', 1),
(63, 'student', 1),
(64, 'student', 1),
(65, 'student', 1),
(66, 'student', 1),
(67, 'student', 1),
(68, 'student', 1),
(69, 'student', 1),
(70, 'student', 1),
(71, 'student', 1),
(72, 'student', 1),
(73, 'student', 1),
(74, 'student', 1),
(75, 'student', 1),
(76, 'student', 1),
(77, 'student', 1),
(78, 'student', 1),
(79, 'student', 1),
(80, 'student', 1),
(81, 'student', 1),
(82, 'student', 1),
(83, 'student', 1),
(84, 'student', 1),
(85, 'student', 1),
(86, 'student', 1),
(87, 'visitor', 0),
(88, 'visitor', 0),
(89, 'visitor', 0),
(90, 'visitor', 0),
(91, 'visitor', 0),
(92, 'visitor', 0),
(93, 'visitor', 0),
(94, 'visitor', 0),
(95, 'visitor', 0),
(96, 'visitor', 0),
(97, 'visitor', 0),
(98, 'visitor', 0),
(99, 'visitor', 0),
(100, 'visitor', 0),
(101, 'visitor', 0),
(102, 'visitor', 0),
(103, 'visitor', 0),
(104, 'visitor', 0),
(105, 'employee', 0),
(106, 'employee', 0),
(107, 'employee', 0),
(108, 'employee', 1),
(109, 'visitor', 1),
(110, 'student', 1),
(111, 'employee', 1);

-- --------------------------------------------------------

--
-- Table structure for table `violations`
--

CREATE TABLE `violations` (
  `violation_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `visitors`
--

CREATE TABLE `visitors` (
  `seq` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `visitor_id` varchar(12) NOT NULL,
  `visitor_name` varchar(80) DEFAULT NULL,
  `purpose` enum('Official Business','Document Submission','Inquiry','Meeting','Delivery','Other') NOT NULL,
  `details` varchar(200) DEFAULT NULL,
  `status` enum('Inside','Outside') DEFAULT 'Outside',
  `valid_until` timestamp NULL DEFAULT NULL,
  `visitor_last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `visitors`
--

INSERT INTO `visitors` (`seq`, `user_id`, `visitor_id`, `visitor_name`, `purpose`, `details`, `status`, `valid_until`, `visitor_last_updated`) VALUES
(1, 28, 'VT-00001', 'Vico Sotto', 'Other', 'Monitor Campus facilities and staff', 'Outside', '2026-04-26 15:59:59', '2026-05-16 11:07:18'),
(2, 36, 'VT-00002', 'Ron Alexander Inocencio', 'Official Business', NULL, 'Outside', '2026-04-30 15:59:59', '2026-05-16 11:07:18'),
(3, 37, 'VT-00003', 'Ron Alexander Inocencio', 'Official Business', NULL, 'Outside', '2026-05-01 15:59:59', '2026-05-16 11:07:18'),
(4, 87, 'VT-00004', 'Jason Jay Recto', 'Meeting', NULL, 'Outside', '2026-05-08 15:59:59', '2026-05-16 11:07:18'),
(5, 88, 'VT-00005', 'Carl Vincent Ventura', 'Other', 'Campus Visit', 'Outside', '2026-05-08 15:59:59', '2026-05-16 11:07:18'),
(6, 89, 'VT-00006', 'Ron Alexander Incocencio', 'Campus Visit', NULL, 'Outside', '2026-05-08 15:59:59', '2026-05-16 11:07:18'),
(7, 90, 'VT-00007', 'Jericho Salvador', 'Official Business', NULL, 'Outside', '2026-05-08 15:59:59', '2026-05-16 11:07:18'),
(8, 91, 'VT-00008', 'Recto, Jason Jay, M.', 'Official Business', NULL, 'Outside', '2026-05-11 15:59:59', '2026-05-16 11:07:18'),
(9, 92, 'VT-00009', 'Recto, Jason Jay, M.', 'Official Business', NULL, 'Outside', '2026-05-11 15:59:59', '2026-05-16 11:07:18'),
(10, 93, 'VT-00010', 'Ron Alexander Inocencio', 'Other', 'Monitor Campus facilities and staff', 'Outside', '2026-05-12 15:59:59', '2026-05-16 11:07:18'),
(11, 94, 'VT-00011', 'Bondat', 'Document Submission', NULL, 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(12, 95, 'VT-00012', 'Ronald Stone', 'Meeting', NULL, 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(13, 96, 'VT-00013', 'Robin Hood', 'Other', 'Campus Visit', 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(14, 97, 'VT-00014', 'Alan Peter Griffin', 'Delivery', NULL, 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(15, 98, 'VT-00015', 'Ronald Stone', 'Meeting', NULL, 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(16, 99, 'VT-00016', 'Robin Hood', 'Other', 'Campus Visit', 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(17, 100, 'VT-00017', 'Alan Peter Griffin', 'Delivery', NULL, 'Outside', '2026-05-16 15:59:59', '2026-05-20 12:30:04'),
(18, 101, 'VT-00018', 'Ronald Stone', 'Meeting', NULL, 'Outside', '2026-05-20 15:59:59', '2026-05-20 16:00:01'),
(19, 102, 'VT-00019', 'Robin Hood', 'Other', 'Campus Visit', 'Outside', '2026-05-20 15:59:59', '2026-05-20 16:00:01'),
(20, 103, 'VT-00020', 'Alan Peter Griffin', 'Delivery', NULL, 'Outside', '2026-05-20 15:59:59', '2026-05-20 16:00:01'),
(21, 104, 'VT-00021', 'Ron Alexander Inocencio', 'Official Business', NULL, 'Outside', '2026-05-20 15:59:59', '2026-05-20 13:25:57'),
(22, 109, 'VT-00022', 'Bondat', 'Document Submission', NULL, 'Inside', '2026-05-28 15:59:59', '2026-05-20 15:55:14');

--
-- Triggers `visitors`
--
DELIMITER $$
CREATE TRIGGER `visitor_id_format` BEFORE INSERT ON `visitors` FOR EACH ROW BEGIN
    DECLARE next_seq INT;

    SELECT AUTO_INCREMENT INTO next_seq
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'visitors';

    IF next_seq IS NULL THEN
        SET next_seq = 1;
    END IF;

    SET NEW.visitor_id = CONCAT('VT-', LPAD(next_seq, 5, '0'));
END
$$
DELIMITER ;

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
-- Indexes for table `bulletins`
--
ALTER TABLE `bulletins`
  ADD PRIMARY KEY (`bulletin_id`),
  ADD KEY `idx_bulletins_active_scope` (`is_active`,`visibility_scope`),
  ADD KEY `idx_bulletins_target_id` (`target_id`),
  ADD KEY `idx_bulletins_target_department` (`target_department`),
  ADD KEY `idx_bulletins_target_event` (`target_event`),
  ADD KEY `idx_bulletins_scheduled_date` (`scheduled_date`);

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
-- Indexes for table `paging_alerts`
--
ALTER TABLE `paging_alerts`
  ADD PRIMARY KEY (`alert_id`),
  ADD KEY `idx_paging_alerts_active_scope` (`is_active`,`visibility_scope`),
  ADD KEY `idx_paging_alerts_target_id` (`target_id`),
  ADD KEY `idx_paging_alerts_target_department` (`target_department`),
  ADD KEY `idx_paging_alerts_target_event` (`target_event`),
  ADD KEY `idx_paging_alerts_expires_at` (`expires_at`);

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
  ADD UNIQUE KEY `visitors_seq_unique` (`seq`),
  ADD KEY `visitors_usersFK` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bulletins`
--
ALTER TABLE `bulletins`
  MODIFY `bulletin_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `department_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `employees`
--
ALTER TABLE `employees`
  MODIFY `employee_id` int(5) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2016;

--
-- AUTO_INCREMENT for table `events`
--
ALTER TABLE `events`
  MODIFY `event_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `event_attendance`
--
ALTER TABLE `event_attendance`
  MODIFY `attendance_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=528;

--
-- AUTO_INCREMENT for table `event_instances`
--
ALTER TABLE `event_instances`
  MODIFY `instance_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=194;

--
-- AUTO_INCREMENT for table `event_log`
--
ALTER TABLE `event_log`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT for table `general_log`
--
ALTER TABLE `general_log`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=274;

--
-- AUTO_INCREMENT for table `paging_alerts`
--
ALTER TABLE `paging_alerts`
  MODIFY `alert_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=112;

--
-- AUTO_INCREMENT for table `visitors`
--
ALTER TABLE `visitors`
  MODIFY `seq` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

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
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

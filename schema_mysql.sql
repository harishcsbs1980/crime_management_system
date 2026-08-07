-- ============================================================
-- Crime Management System — MySQL schema
-- Run this once against MySQL if you prefer to create tables
-- manually instead of letting SQLAlchemy (`flask init-db`) do it.
-- ============================================================

CREATE DATABASE IF NOT EXISTS crime_management_system
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE crime_management_system;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'officer',
    badge_number VARCHAR(40) UNIQUE,
    phone VARCHAR(20),
    is_active_user BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE complainants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120),
    address VARCHAR(255),
    gender VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE firs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fir_number VARCHAR(40) NOT NULL UNIQUE,
    crime_type VARCHAR(80) NOT NULL,
    location VARCHAR(200) NOT NULL,
    date_of_incident DATE NOT NULL,
    date_filed DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'Registered',
    complainant_id INT NOT NULL,
    filed_by_id INT,
    FOREIGN KEY (complainant_id) REFERENCES complainants(id) ON DELETE CASCADE,
    FOREIGN KEY (filed_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(40) NOT NULL UNIQUE,
    fir_id INT NOT NULL,
    officer_id INT,
    status VARCHAR(30) DEFAULT 'Open',
    description TEXT,
    priority VARCHAR(20) DEFAULT 'Medium',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    FOREIGN KEY (fir_id) REFERENCES firs(id) ON DELETE CASCADE,
    FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE evidence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    file_path VARCHAR(255),
    uploaded_by_id INT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE witnesses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    statement TEXT NOT NULL,
    recorded_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE investigation_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    note TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_id INT,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE charge_sheets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    file_path VARCHAR(255),
    summary TEXT,
    filed_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE court_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    hearing_date DATE NOT NULL,
    court_status VARCHAR(40) DEFAULT 'Scheduled',
    judge_name VARCHAR(120),
    remarks TEXT,
    judgment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Seed an initial admin (password 'admin123' — CHANGE IMMEDIATELY).
-- Hash below is a Werkzeug pbkdf2:sha256 hash — easier to just run
-- `flask init-db` instead, which creates this account for you.

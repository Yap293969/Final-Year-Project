-- Is this a scam? -- the accounts database (MySQL 8 / MariaDB, as shipped with Laragon).
--
-- Run this once to create the database and its three tables:
--   Laragon -> Database (opens HeidiSQL) -> File -> Run SQL file... -> pick this file
-- or, from Laragon's Terminal:
--   mysql -u root < database/schema.sql
--
-- Running it again is safe: nothing that already exists is dropped or changed.
--
-- users         one row per account (email, first name, last name, password hash)
-- scan_results  one row per check made on Checker.html while logged in
-- game_attempts one row per finished round of "Scam or Safe?" (Game.html) while logged in
--
-- Passwords are never stored. Only the hash from PHP's password_hash() is kept,
-- so not even someone who can read this database can see a password.

CREATE DATABASE IF NOT EXISTS isthisascam
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE isthisascam;

CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  email         VARCHAR(254) NOT NULL,          -- stored in lower case
  first_name    VARCHAR(50)  NOT NULL,
  last_name     VARCHAR(50)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,          -- password_hash(), never the password itself
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS scan_results (
  id                   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id              INT UNSIGNED NOT NULL,
  scan_type            ENUM('email', 'url') NOT NULL,
  -- What was checked. A link is kept whole; for an email only the subject and the
  -- first 200 characters of the message are kept, not the whole message.
  url                  VARCHAR(2048) NULL,
  email_subject        VARCHAR(255)  NULL,
  email_preview        VARCHAR(200)  NULL,
  -- The model's answer, as the model server sent it.
  verdict              ENUM('phishing', 'legitimate') NOT NULL,
  confidence           DECIMAL(5, 2) NOT NULL,      -- 0.00 to 100.00
  phishing_probability DECIMAL(5, 2) NOT NULL,      -- 0.00 to 100.00
  top_reason           VARCHAR(255)  NULL,          -- links only: the strongest SHAP reason
  created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_scan_results_user (user_id, created_at),
  CONSTRAINT fk_scan_results_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS game_attempts (
  id            INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  user_id       INT UNSIGNED     NOT NULL,
  score         SMALLINT UNSIGNED NOT NULL,   -- 100 per right answer, 50 if the hint was used
  correct_count TINYINT UNSIGNED NOT NULL,
  total_rounds  TINYINT UNSIGNED NOT NULL,
  scams_caught  TINYINT UNSIGNED NOT NULL,
  scams_total   TINYINT UNSIGNED NOT NULL,
  safe_trusted  TINYINT UNSIGNED NOT NULL,
  safe_total    TINYINT UNSIGNED NOT NULL,
  best_streak   TINYINT UNSIGNED NOT NULL,
  hints_used    TINYINT UNSIGNED NOT NULL,
  passed        TINYINT(1)       NOT NULL,    -- 1 when correct_count reached the pass mark (api/config.php)
  created_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_game_attempts_user (user_id, created_at),
  CONSTRAINT fk_game_attempts_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB;

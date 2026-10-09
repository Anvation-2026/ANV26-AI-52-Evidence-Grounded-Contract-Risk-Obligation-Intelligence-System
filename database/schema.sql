-- MySQL 8+ schema for Contract Risk Intelligence.
-- The FastAPI app can also create tables automatically on startup.
CREATE DATABASE IF NOT EXISTS contract_risk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE contract_risk_db;

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contracts (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_name VARCHAR(255) NOT NULL,
  owner_id INT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(50),
  version_number INT DEFAULT 1,
  parent_contract_id BIGINT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_contracts_owner_id (owner_id),
  CONSTRAINT fk_contracts_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_contracts_parent FOREIGN KEY (parent_contract_id) REFERENCES contracts(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS clauses (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT NOT NULL,
  clause_number VARCHAR(100),
  clause_title VARCHAR(255),
  clause_text TEXT NOT NULL,
  page_number INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_clauses_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS findings (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT NOT NULL,
  clause_id BIGINT NULL,
  rule_id VARCHAR(100) NOT NULL,
  category VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL,
  severity VARCHAR(50) NOT NULL,
  evidence TEXT,
  expected TEXT,
  actual TEXT,
  reason TEXT,
  recommended_action TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_findings_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_findings_clause FOREIGN KEY (clause_id) REFERENCES clauses(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS obligations (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT NOT NULL,
  clause_id BIGINT NULL,
  actor VARCHAR(255),
  action TEXT,
  deadline VARCHAR(255),
  trigger_condition TEXT,
  evidence TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_obligations_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_obligations_clause FOREIGN KEY (clause_id) REFERENCES clauses(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_events (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT NOT NULL,
  event_type VARCHAR(80) NOT NULL,
  description TEXT NOT NULL,
  details_json TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_audit_events_contract_id (contract_id),
  CONSTRAINT fk_audit_events_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS review_actions (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT NOT NULL,
  finding_id BIGINT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'OPEN',
  note TEXT,
  reviewer VARCHAR(120),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_review_actions_contract_id (contract_id),
  INDEX ix_review_actions_finding_id (finding_id),
  CONSTRAINT fk_review_actions_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_review_actions_finding FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

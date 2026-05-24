CREATE DATABASE IF NOT EXISTS ai_novel_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE ai_novel_platform;

CREATE TABLE IF NOT EXISTS ai_novel_project (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  genre VARCHAR(80) NULL,
  premise TEXT NULL,
  style_guide_path VARCHAR(500) NULL,
  root_dir VARCHAR(500) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_chapter (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  volume_no INT NOT NULL DEFAULT 1,
  chapter_no INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  outline TEXT NULL,
  summary TEXT NULL,
  draft_path VARCHAR(500) NULL,
  final_path VARCHAR(500) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'planned',
  word_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_project_chapter (project_id, volume_no, chapter_no),
  KEY idx_project_status (project_id, status),
  CONSTRAINT fk_chapter_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_entity (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  entity_type VARCHAR(40) NOT NULL,
  name VARCHAR(120) NOT NULL,
  alias JSON NULL,
  description TEXT NULL,
  current_state TEXT NULL,
  detail_path VARCHAR(500) NULL,
  importance TINYINT NOT NULL DEFAULT 3,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_project_entity (project_id, entity_type, name),
  KEY idx_project_type (project_id, entity_type),
  CONSTRAINT fk_entity_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_plot_thread (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  thread_type VARCHAR(40) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  setup_chapter_id BIGINT NULL,
  payoff_chapter_id BIGINT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'open',
  notes_path VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_project_status (project_id, status),
  CONSTRAINT fk_plot_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE,
  CONSTRAINT fk_plot_setup_chapter FOREIGN KEY (setup_chapter_id) REFERENCES ai_novel_chapter(id) ON DELETE SET NULL,
  CONSTRAINT fk_plot_payoff_chapter FOREIGN KEY (payoff_chapter_id) REFERENCES ai_novel_chapter(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_timeline_event (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  chapter_id BIGINT NULL,
  event_order DECIMAL(12,3) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NULL,
  involved_entities JSON NULL,
  certainty VARCHAR(30) NOT NULL DEFAULT 'canon',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_project_order (project_id, event_order),
  CONSTRAINT fk_timeline_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE,
  CONSTRAINT fk_timeline_chapter FOREIGN KEY (chapter_id) REFERENCES ai_novel_chapter(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_task (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  chapter_id BIGINT NULL,
  task_type VARCHAR(40) NOT NULL,
  title VARCHAR(200) NOT NULL,
  instruction_path VARCHAR(500) NOT NULL,
  context_path VARCHAR(500) NULL,
  output_path VARCHAR(500) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'pending',
  priority TINYINT NOT NULL DEFAULT 5,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP NULL,
  finished_at TIMESTAMP NULL,
  KEY idx_project_status_priority (project_id, status, priority),
  CONSTRAINT fk_task_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE,
  CONSTRAINT fk_task_chapter FOREIGN KEY (chapter_id) REFERENCES ai_novel_chapter(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS ai_novel_review_issue (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  project_id BIGINT NOT NULL,
  chapter_id BIGINT NULL,
  task_id BIGINT NULL,
  issue_type VARCHAR(50) NOT NULL,
  severity TINYINT NOT NULL DEFAULT 3,
  title VARCHAR(200) NOT NULL,
  detail TEXT NULL,
  suggestion TEXT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'open',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP NULL,
  KEY idx_project_status (project_id, status),
  CONSTRAINT fk_review_project FOREIGN KEY (project_id) REFERENCES ai_novel_project(id) ON DELETE CASCADE,
  CONSTRAINT fk_review_chapter FOREIGN KEY (chapter_id) REFERENCES ai_novel_chapter(id) ON DELETE SET NULL,
  CONSTRAINT fk_review_task FOREIGN KEY (task_id) REFERENCES ai_novel_task(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

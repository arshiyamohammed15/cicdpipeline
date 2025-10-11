-- ZEROUI Extension Configuration Database Schema
-- Following Rule 4: Use Settings Files, Not Hardcoded Numbers
-- Following Rule 5: Keep Good Records + Keep Good Logs
-- Following Rule 3: Protect People's Privacy (local database)

-- Extension Configuration Table
CREATE TABLE IF NOT EXISTS extension_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- TypeScript Configuration Table
CREATE TABLE IF NOT EXISTS typescript_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Build Configuration Table
CREATE TABLE IF NOT EXISTS build_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Runtime Configuration Table
CREATE TABLE IF NOT EXISTS runtime_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Configuration Change Log Table (Rule 5: Keep Good Records)
CREATE TABLE IF NOT EXISTS config_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    key_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    change_type TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    user_id TEXT DEFAULT 'system',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

-- Configuration Backup Table (Rule 7: Never Break Things During Updates)
CREATE TABLE IF NOT EXISTS config_backup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    backup_data TEXT NOT NULL, -- JSON of all config tables
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    version INTEGER DEFAULT 1
);

-- Configuration Validation Schema Table
CREATE TABLE IF NOT EXISTS config_schema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    key_name TEXT NOT NULL,
    schema_definition TEXT NOT NULL, -- JSON schema
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance (Rule 8: Make Things Fast)
CREATE INDEX IF NOT EXISTS idx_extension_config_key ON extension_config(key);
CREATE INDEX IF NOT EXISTS idx_extension_config_category ON extension_config(category);
CREATE INDEX IF NOT EXISTS idx_typescript_config_key ON typescript_config(key);
CREATE INDEX IF NOT EXISTS idx_build_config_key ON build_config(key);
CREATE INDEX IF NOT EXISTS idx_runtime_config_key ON runtime_config(key);
CREATE INDEX IF NOT EXISTS idx_config_change_log_timestamp ON config_change_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_config_backup_created_at ON config_backup(created_at);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_extension_config_timestamp 
    AFTER UPDATE ON extension_config
    BEGIN
        UPDATE extension_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_typescript_config_timestamp 
    AFTER UPDATE ON typescript_config
    BEGIN
        UPDATE typescript_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_build_config_timestamp 
    AFTER UPDATE ON build_config
    BEGIN
        UPDATE build_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_runtime_config_timestamp 
    AFTER UPDATE ON runtime_config
    BEGIN
        UPDATE runtime_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

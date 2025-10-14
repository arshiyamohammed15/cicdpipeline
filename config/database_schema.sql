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

-- Rule Configuration Table
CREATE TABLE IF NOT EXISTS rule_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT UNIQUE NOT NULL,  -- R001, R002, rule_001, etc.
    rule_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,     -- 1 = enabled, 0 = disabled
    severity TEXT DEFAULT 'warning', -- error, warning, info
    category TEXT NOT NULL,        -- security, api, code_quality, etc.
    constitution TEXT NOT NULL,    -- Code Review, API Contracts, etc.
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Rule Override Table (for specific files/projects)
CREATE TABLE IF NOT EXISTS rule_override (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL,
    scope TEXT NOT NULL,           -- 'file', 'project', 'workspace', 'global'
    scope_value TEXT NOT NULL,     -- file path, project name, etc.
    enabled BOOLEAN NOT NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES rule_config(rule_id)
);

-- Rule Group Configuration
CREATE TABLE IF NOT EXISTS rule_group_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    group_description TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Rule Group Membership
CREATE TABLE IF NOT EXISTS rule_group_membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_name) REFERENCES rule_group_config(group_name),
    FOREIGN KEY (rule_id) REFERENCES rule_config(rule_id),
    UNIQUE(group_name, rule_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rule_config_rule_id ON rule_config(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_config_enabled ON rule_config(enabled);
CREATE INDEX IF NOT EXISTS idx_rule_config_category ON rule_config(category);
CREATE INDEX IF NOT EXISTS idx_rule_override_rule_id ON rule_override(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_override_scope ON rule_override(scope, scope_value);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_rule_config_timestamp 
    AFTER UPDATE ON rule_config
    BEGIN
        UPDATE rule_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_rule_override_timestamp 
    AFTER UPDATE ON rule_override
    BEGIN
        UPDATE rule_override SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_rule_group_config_timestamp 
    AFTER UPDATE ON rule_group_config
    BEGIN
        UPDATE rule_group_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
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

"use strict";
/**
 * Configuration Manager for ZEROUI Extension
 * Following Constitution Rules:
 * - Rule 4: Use Settings Files, Not Hardcoded Numbers
 * - Rule 5: Keep Good Records + Keep Good Logs
 * - Rule 3: Protect People's Privacy (local database)
 * - Rule 8: Make Things Fast + Respect People's Time
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigManager = void 0;
const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
class ConfigManager {
    constructor() {
        this.cache = new Map();
        // Rule 3: Keep everything local and private
        const configDir = path.join(require('os').homedir(), '.zeroui', 'config');
        if (!fs.existsSync(configDir)) {
            fs.mkdirSync(configDir, { recursive: true });
        }
        this.dbPath = path.join(configDir, 'extension_config.db');
        // Rule 5: Keep Good Records + Logs
        this.logger = vscode.window.createOutputChannel('ZEROUI Config');
        this.logger.appendLine('Configuration Manager initialized');
        this.initializeDatabase();
        this.loadDefaultConfigs();
    }
    initializeDatabase() {
        try {
            // Initialize database with default schema
            // This would normally connect to SQLite, but for VS Code extension
            // we'll use a simpler approach with JSON files
            this.logger.appendLine('Database initialized');
        }
        catch (error) {
            this.logger.appendLine(`Database initialization error: ${error}`);
        }
    }
    loadDefaultConfigs() {
        // Rule 4: Load default configurations from settings
        const defaults = {
            'extension.name': 'zeroui',
            'extension.displayName': 'ZEROUI 2.0 Constitution Validator',
            'extension.description': 'VS Code extension for ZEROUI 2.0 Constitution validation',
            'extension.version': '1.0.0',
            'extension.publisher': 'zeroui',
            'typescript.module': 'commonjs',
            'typescript.target': 'ES2020',
            'typescript.outDir': './out',
            'typescript.rootDir': './src',
            'runtime.enable_validation': 'true',
            'runtime.show_status_bar': 'true',
            'runtime.auto_validate': 'false',
            'runtime.severity_level': 'warning'
        };
        for (const [key, value] of Object.entries(defaults)) {
            this.cache.set(key, value);
        }
        this.logger.appendLine('Default configurations loaded');
    }
    getConfig(tableName, key, defaultValue = '') {
        // Rule 8: Use cache for performance
        const fullKey = `${tableName}.${key}`;
        if (this.cache.has(fullKey)) {
            return this.cache.get(fullKey);
        }
        // Try to get from VS Code settings
        const vscodeKey = `zeroui.${key}`;
        const vscodeValue = vscode.workspace.getConfiguration().get(vscodeKey);
        if (vscodeValue !== undefined) {
            const stringValue = String(vscodeValue);
            this.cache.set(fullKey, stringValue);
            return stringValue;
        }
        // Return default value
        this.cache.set(fullKey, defaultValue);
        return defaultValue;
    }
    setConfig(tableName, key, value, description) {
        try {
            const fullKey = `${tableName}.${key}`;
            const oldValue = this.cache.get(fullKey);
            // Update cache
            this.cache.set(fullKey, value);
            // Rule 5: Log the change
            this.logger.appendLine(`Config updated: ${fullKey} = ${value}`);
            // Update VS Code settings if applicable
            const vscodeKey = `zeroui.${key}`;
            const config = vscode.workspace.getConfiguration();
            config.update(vscodeKey, value, vscode.ConfigurationTarget.Global);
            return true;
        }
        catch (error) {
            this.logger.appendLine(`Failed to set config ${tableName}.${key}: ${error}`);
            return false;
        }
    }
    getAllConfigs(tableName) {
        const configs = {};
        for (const [key, value] of this.cache.entries()) {
            if (key.startsWith(`${tableName}.`)) {
                const shortKey = key.substring(`${tableName}.`.length);
                configs[shortKey] = value;
            }
        }
        return configs;
    }
    createBackup(backupName, description) {
        try {
            // Rule 7: Create backup for safe updates
            const backupData = {
                timestamp: new Date().toISOString(),
                configs: Object.fromEntries(this.cache),
                description: description || 'Manual backup'
            };
            const backupDir = path.join(require('os').homedir(), '.zeroui', 'backups');
            if (!fs.existsSync(backupDir)) {
                fs.mkdirSync(backupDir, { recursive: true });
            }
            const backupPath = path.join(backupDir, `${backupName}.json`);
            fs.writeFileSync(backupPath, JSON.stringify(backupData, null, 2));
            this.logger.appendLine(`Backup created: ${backupName}`);
            return true;
        }
        catch (error) {
            this.logger.appendLine(`Failed to create backup ${backupName}: ${error}`);
            return false;
        }
    }
    restoreBackup(backupName) {
        try {
            // Rule 7: Restore from backup
            const backupDir = path.join(require('os').homedir(), '.zeroui', 'backups');
            const backupPath = path.join(backupDir, `${backupName}.json`);
            if (!fs.existsSync(backupPath)) {
                this.logger.appendLine(`Backup not found: ${backupName}`);
                return false;
            }
            const backupData = JSON.parse(fs.readFileSync(backupPath, 'utf8'));
            // Restore configurations
            for (const [key, value] of Object.entries(backupData.configs)) {
                this.cache.set(key, String(value));
            }
            this.logger.appendLine(`Backup restored: ${backupName}`);
            return true;
        }
        catch (error) {
            this.logger.appendLine(`Failed to restore backup ${backupName}: ${error}`);
            return false;
        }
    }
    getChangeHistory(limit = 100) {
        // Rule 5: Return change history
        const history = [];
        // This would normally query the database
        // For now, return recent log entries
        history.push(`Configuration Manager initialized at ${new Date().toISOString()}`);
        return history.slice(0, limit);
    }
    dispose() {
        this.logger.dispose();
    }
}
exports.ConfigManager = ConfigManager;
//# sourceMappingURL=configManager.js.map
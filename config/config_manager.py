"""
ZEROUI Extension Configuration Manager
Following Constitution Rules:
- Rule 4: Use Settings Files, Not Hardcoded Numbers
- Rule 5: Keep Good Records + Keep Good Logs  
- Rule 3: Protect People's Privacy (local database)
- Rule 8: Make Things Fast + Respect People's Time
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class ConfigManager:
    def __init__(self, db_path: str = None):
        """
        Initialize configuration manager with local SQLite database
        
        Args:
            db_path: Path to SQLite database file (defaults to local config directory)
        """
        if db_path is None:
            # Rule 3: Keep everything local and private
            config_dir = Path.home() / '.zeroui' / 'config'
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(config_dir / 'extension_config.db')
        
        self.db_path = db_path
        self.cache = {}  # Rule 8: Cache for performance
        self.logger = self._setup_logging()
        
        # Initialize database
        self._init_database()
        self._load_default_configs()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging following Rule 5: Keep Good Records + Logs"""
        logger = logging.getLogger('zeroui_config')
        logger.setLevel(logging.INFO)
        
        # Rule 3: Keep logs local
        log_dir = Path.home() / '.zeroui' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'config_manager.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize database with schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Read and execute schema
                schema_path = Path(__file__).parent / 'database_schema.sql'
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                conn.executescript(schema_sql)
                conn.commit()
                
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _load_default_configs(self):
        """Load default configuration values"""
        defaults = {
            'extension_config': {
                'name': 'zeroui',
                'displayName': 'ZEROUI 2.0 Constitution Validator',
                'description': 'VS Code extension for ZEROUI 2.0 Constitution validation',
                'version': '1.0.0',
                'publisher': 'zeroui',
                'vscode_engine': '^1.74.0',
                'main_file': './out/extension.js',
                'activation_event': 'onStartupFinished'
            },
            'typescript_config': {
                'module': 'commonjs',
                'target': 'ES2020',
                'outDir': './out',
                'rootDir': './src',
                'sourceMap': 'true',
                'strict': 'true',
                'lib': '["ES2020"]'
            },
            'build_config': {
                'compile_command': 'tsc -p ./',
                'watch_command': 'tsc -watch -p ./',
                'prepublish_command': 'npm run compile'
            },
            'runtime_config': {
                'enable_validation': 'true',
                'show_status_bar': 'true',
                'auto_validate': 'false',
                'severity_level': 'warning',
                'cache_ttl_seconds': '300',
                'max_file_size_mb': '10'
            }
        }
        
        for table_name, configs in defaults.items():
            for key, value in configs.items():
                self.set_config(table_name, key, value, f"Default {key} value")
    
    def set_config(self, table_name: str, key: str, value: str, description: str = None) -> bool:
        """
        Set configuration value with logging and validation
        
        Args:
            table_name: Name of configuration table
            key: Configuration key
            value: Configuration value
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if key exists
                cursor = conn.execute(
                    f"SELECT id, value FROM {table_name} WHERE key = ?",
                    (key,)
                )
                existing = cursor.fetchone()
                
                old_value = existing[1] if existing else None
                
                if existing:
                    # Update existing
                    conn.execute(
                        f"UPDATE {table_name} SET value = ?, description = ?, version = version + 1 WHERE key = ?",
                        (value, description, key)
                    )
                    change_type = 'UPDATE'
                else:
                    # Insert new
                    conn.execute(
                        f"INSERT INTO {table_name} (key, value, description) VALUES (?, ?, ?)",
                        (key, value, description)
                    )
                    change_type = 'INSERT'
                
                # Log the change (Rule 5: Keep Good Records)
                conn.execute(
                    "INSERT INTO config_change_log (table_name, key_name, old_value, new_value, change_type, reason) VALUES (?, ?, ?, ?, ?, ?)",
                    (table_name, key, old_value, value, change_type, description or 'Manual update')
                )
                
                conn.commit()
                
                # Update cache (Rule 8: Performance)
                if table_name not in self.cache:
                    self.cache[table_name] = {}
                self.cache[table_name][key] = value
                
                self.logger.info(f"Config updated: {table_name}.{key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set config {table_name}.{key}: {e}")
            return False
    
    def get_config(self, table_name: str, key: str, default: str = None) -> Optional[str]:
        """
        Get configuration value with caching
        
        Args:
            table_name: Name of configuration table
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        # Check cache first (Rule 8: Performance)
        if table_name in self.cache and key in self.cache[table_name]:
            return self.cache[table_name][key]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    f"SELECT value FROM {table_name} WHERE key = ?",
                    (key,)
                )
                result = cursor.fetchone()
                
                value = result[0] if result else default
                
                # Update cache
                if table_name not in self.cache:
                    self.cache[table_name] = {}
                self.cache[table_name][key] = value
                
                return value
                
        except Exception as e:
            self.logger.error(f"Failed to get config {table_name}.{key}: {e}")
            return default
    
    def get_all_configs(self, table_name: str) -> Dict[str, str]:
        """
        Get all configurations from a table
        
        Args:
            table_name: Name of configuration table
            
        Returns:
            Dictionary of all configurations
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"SELECT key, value FROM {table_name}")
                results = cursor.fetchall()
                
                configs = {key: value for key, value in results}
                
                # Update cache
                self.cache[table_name] = configs
                
                return configs
                
        except Exception as e:
            self.logger.error(f"Failed to get all configs from {table_name}: {e}")
            return {}
    
    def create_backup(self, backup_name: str, description: str = None) -> bool:
        """
        Create configuration backup (Rule 7: Never Break Things During Updates)
        
        Args:
            backup_name: Name for the backup
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Collect all configuration data
            backup_data = {}
            tables = ['extension_config', 'typescript_config', 'build_config', 'runtime_config']
            
            for table in tables:
                backup_data[table] = self.get_all_configs(table)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO config_backup (backup_name, backup_data, description) VALUES (?, ?, ?)",
                    (backup_name, json.dumps(backup_data), description)
                )
                conn.commit()
            
            self.logger.info(f"Backup created: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup {backup_name}: {e}")
            return False
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore configuration from backup (Rule 7: Never Break Things During Updates)
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT backup_data FROM config_backup WHERE backup_name = ? ORDER BY created_at DESC LIMIT 1",
                    (backup_name,)
                )
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error(f"Backup not found: {backup_name}")
                    return False
                
                backup_data = json.loads(result[0])
                
                # Restore each table
                for table_name, configs in backup_data.items():
                    # Clear existing data
                    conn.execute(f"DELETE FROM {table_name}")
                    
                    # Insert backup data
                    for key, value in configs.items():
                        conn.execute(
                            f"INSERT INTO {table_name} (key, value) VALUES (?, ?)",
                            (key, value)
                        )
                
                conn.commit()
                
                # Clear cache
                self.cache.clear()
                
                self.logger.info(f"Backup restored: {backup_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False
    
    def get_change_history(self, table_name: str = None, limit: int = 100) -> List[Dict]:
        """
        Get configuration change history (Rule 5: Keep Good Records)
        
        Args:
            table_name: Optional table name filter
            limit: Maximum number of records to return
            
        Returns:
            List of change records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if table_name:
                    cursor = conn.execute(
                        "SELECT * FROM config_change_log WHERE table_name = ? ORDER BY timestamp DESC LIMIT ?",
                        (table_name, limit)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM config_change_log ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    )
                
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            self.logger.error(f"Failed to get change history: {e}")
            return []

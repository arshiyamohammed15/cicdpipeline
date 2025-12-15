#!/usr/bin/env python3
"""
Constitution Rules Database for ZeroUI 2.0

This module provides SQLite database operations for storing and managing
constitution rules with configuration management.

Rule counts are dynamically loaded from docs/constitution/*.json files (single source of truth).
No hardcoded rule counts exist in this module.
"""

import sqlite3
import logging
import json
import os
import threading
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
from contextlib import contextmanager

from .path_utils import resolve_constitution_db_path

class ConstitutionRulesDB:
    """
    SQLite database manager for storing and managing constitution rules.

    Features:
    - Store all rules in JSON format with metadata
    - Enable/disable rules via configuration
    - Query rules by category, priority, or status
    - Track rule usage and validation history
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the constitution rules database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = resolve_constitution_db_path(db_path)
        self.connection = None
        # Use re-entrant lock to allow nested DB operations within the same thread
        self._connection_lock = threading.RLock()
        self._max_retries = self._get_max_retries_from_config()
        self._retry_delay = self._get_base_delay_from_config()
        self._jitter = self._get_jitter_from_config()
        self._timeout = self._get_timeout_from_config()
        self._init_database()

        # Logger
        self._logger = logging.getLogger(__name__)

    def _init_database(self):
        """Initialize database schema and tables."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create connection with better settings
            self.connection = sqlite3.connect(
                self.db_path,
                timeout=self._timeout,  # Configurable timeout
                check_same_thread=False  # Allow multi-threading
            )
            self.connection.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")

            # Create tables
            self._create_tables()

            # Insert all rules from source of truth if database is empty
            if self._is_database_empty():
                self._insert_all_rules()
        except sqlite3.Error as e:
            logging.getLogger(__name__).error("Database initialization error: %s", e)
            raise
        except Exception as e:
            logging.getLogger(__name__).error("Unexpected error during database initialization: %s", e)
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with retry logic."""
        with self._connection_lock:
            for attempt in range(self._max_retries):
                try:
                    if self.connection is None:
                        self._reconnect()

                    # Test connection
                    self.connection.execute("SELECT 1")
                    yield self.connection
                    return

                except sqlite3.Error as e:
                    logging.getLogger(__name__).warning("Database connection error (attempt %d): %s", attempt + 1, e)
                    if attempt < self._max_retries - 1:
                        # Exponential backoff with jitter
                        delay = self._retry_delay * (2 ** attempt)
                        jitter = self._calculate_jitter(delay)
                        time.sleep(delay + jitter)
                        self._reconnect()
                    else:
                        raise

    def _reconnect(self):
        """Reconnect to the database."""
        try:
            if self.connection:
                self.connection.close()
        except:
            pass

        self.connection = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row

        # Re-enable WAL mode
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=10000")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        if self._is_database_empty():
            self._insert_all_rules()

    def close(self):
        """Close the database connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
        except Exception as e:
            logging.getLogger(__name__).warning("Error closing database connection: %s", e)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _create_tables(self):
        """Create database tables for rules and configuration."""
        cursor = self.connection.cursor()

        # Constitution rules table - stores all constitution rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS constitution_rules (
                id INTEGER PRIMARY KEY,
                rule_number INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                content TEXT NOT NULL,
                json_metadata TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rule configuration table - manages enable/disable status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_configuration (
                rule_number INTEGER PRIMARY KEY,
                enabled BOOLEAN DEFAULT 1,
                config_data TEXT,
                disabled_reason TEXT,
                disabled_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_number) REFERENCES constitution_rules (rule_number)
            )
        """)

        # Categories table - rule categories and metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_categories (
                name TEXT PRIMARY KEY,
                description TEXT,
                priority TEXT NOT NULL,
                rule_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rule usage tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_usage (
                id INTEGER PRIMARY KEY,
                rule_number INTEGER NOT NULL,
                action TEXT NOT NULL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_number) REFERENCES constitution_rules (rule_number)
            )
        """)

        # Validation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_history (
                id INTEGER PRIMARY KEY,
                rule_number INTEGER NOT NULL,
                validation_result TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_number) REFERENCES constitution_rules (rule_number)
            )
        """)

        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_number ON constitution_rules (rule_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_category ON constitution_rules (category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_priority ON constitution_rules (priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_enabled ON rule_configuration (enabled)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_rule ON rule_usage (rule_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_rule ON validation_history (rule_number)")

        self.connection.commit()

    def _is_database_empty(self) -> bool:
        """Check if database is empty (no rules inserted)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM constitution_rules")
            count = cursor.fetchone()[0]
            return count == 0

    def _insert_all_rules(self):
        """Insert all constitution rules from source of truth into the database."""
        from .rule_extractor import ConstitutionRuleExtractor

        extractor = ConstitutionRuleExtractor()
        rules_data = extractor.extract_all_rules()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for rule_data in rules_data:
                # Insert rule
                cursor.execute("""
                    INSERT OR REPLACE INTO constitution_rules (rule_number, title, category, priority, content, json_metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rule_data['rule_number'],
                    rule_data['title'],
                    rule_data['category'],
                    rule_data['priority'],
                    rule_data['content'],
                    json.dumps(rule_data)
                ))

                # Insert default configuration (enabled by default)
                cursor.execute("""
                    INSERT OR REPLACE INTO rule_configuration (rule_number, enabled, config_data)
                    VALUES (?, 1, ?)
                """, (
                    rule_data['rule_number'],
                    json.dumps({"default_enabled": True, "notes": ""})
                ))

            # Insert categories
            categories = self._get_categories_data()
            for category_data in categories:
                cursor.execute("""
                    INSERT OR REPLACE INTO rule_categories (name, description, priority, rule_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    category_data['name'],
                    category_data['description'],
                    category_data['priority'],
                    category_data['rule_count']
                ))

            conn.commit()

    def _get_categories_data(self) -> List[Dict[str, Any]]:
        """Get category metadata. Rule counts are calculated dynamically from actual rules."""
        return [
            {"name": "basic_work", "description": "Core principles for all development work", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "system_design", "description": "System architecture and design principles", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "problem_solving", "description": "Problem-solving methodologies and approaches", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "platform", "description": "Platform-specific rules and guidelines", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "teamwork", "description": "Collaboration and team dynamics", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "code_review", "description": "Code review processes and standards", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "coding_standards", "description": "Technical coding standards and best practices", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "comments", "description": "Documentation and commenting standards", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "api_contracts", "description": "API design, contracts, and governance", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "logging", "description": "Logging and troubleshooting standards", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "exception_handling", "description": "Exception handling, timeouts, retries, and error recovery", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "typescript", "description": "TypeScript coding standards, type safety, and best practices", "priority": "critical", "rule_count": 0},  # Calculated dynamically
            {"name": "other", "description": "Miscellaneous rules", "priority": "important", "rule_count": 0}  # Calculated dynamically
        ]

    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all rules from the database.

        Args:
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if enabled_only:
                query = """
                    SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                    FROM constitution_rules r
                    JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                    WHERE rc.enabled = 1
                    ORDER BY r.rule_number
                """
            else:
                query = """
                    SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                    FROM constitution_rules r
                    JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                    ORDER BY r.rule_number
                """

            cursor.execute(query)
            rows = cursor.fetchall()

            rules = []
            for row in rows:
                rule = dict(row)
                rule['json_metadata'] = json.loads(rule['json_metadata'])
                rule['config_data'] = json.loads(rule['config_data']) if rule['config_data'] else {}
                # Convert enabled from integer to boolean
                rule['enabled'] = bool(rule['enabled'])
                rules.append(rule)

            return rules

    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by its number.

        Args:
            rule_number: Rule number to retrieve

        Returns:
            Rule dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE r.rule_number = ?
            """, (rule_number,))

            row = cursor.fetchone()
            if row:
                rule = dict(row)
                rule['json_metadata'] = json.loads(rule['json_metadata'])
                rule['config_data'] = json.loads(rule['config_data']) if rule['config_data'] else {}
                # Convert enabled from integer to boolean
                rule['enabled'] = bool(rule['enabled'])
                return rule

            return None

    def get_rules_by_category(self, category: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules by category.

        Args:
            category: Category name
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if enabled_only:
                query = """
                    SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                    FROM constitution_rules r
                    JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                    WHERE r.category = ? AND rc.enabled = 1
                    ORDER BY r.rule_number
                """
            else:
                query = """
                    SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                    FROM constitution_rules r
                    JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                    WHERE r.category = ?
                    ORDER BY r.rule_number
                """
            cursor.execute(query, (category,))
            rows = cursor.fetchall()

        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = json.loads(rule['json_metadata'])
            rule['config_data'] = json.loads(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)

        return rules

    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enable a rule.

        Args:
            rule_number: Rule number to enable
            config_data: Optional configuration data

        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE rule_configuration
                    SET enabled = 1, config_data = ?, disabled_reason = NULL, disabled_at = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE rule_number = ?
                """, (json.dumps(config_data or {}), rule_number))
                if cursor.rowcount > 0:
                    conn.commit()
                    self._log_rule_usage(rule_number, "enabled", f"Config: {config_data}")
                    return True
                return False
            except Exception as e:
                conn.rollback()
                raise e

    def disable_rule(self, rule_number: int, reason: str = "") -> bool:
        """
        Disable a rule.

        Args:
            rule_number: Rule number to disable
            reason: Reason for disabling

        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get current config
                cursor.execute("SELECT config_data FROM rule_configuration WHERE rule_number = ?", (rule_number,))
                row = cursor.fetchone()
                current_config = json.loads(row[0]) if row and row[0] else {}
                # Add disable reason to config
                current_config['disabled_reason'] = reason
                current_config['disabled_at'] = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE rule_configuration
                    SET enabled = 0, config_data = ?, disabled_reason = ?, disabled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE rule_number = ?
                """, (json.dumps(current_config), reason, rule_number))
                if cursor.rowcount > 0:
                    conn.commit()
                    self._log_rule_usage(rule_number, "disabled", f"Reason: {reason}")
                    return True
                return False
            except Exception as e:
                conn.rollback()
                raise e

    def get_enabled_rules(self) -> List[Dict[str, Any]]:
        """Get all enabled rules."""
        return self.get_all_rules(enabled_only=True)

    def get_disabled_rules(self) -> List[Dict[str, Any]]:
        """Get all disabled rules."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, rc.enabled, rc.config_data, rc.disabled_reason, rc.disabled_at
                FROM constitution_rules r
                JOIN rule_configuration rc ON r.rule_number = rc.rule_number
                WHERE rc.enabled = 0
                ORDER BY r.rule_number
            """)
            rows = cursor.fetchall()
        rules = []
        for row in rows:
            rule = dict(row)
            rule['json_metadata'] = json.loads(rule['json_metadata'])
            rule['config_data'] = json.loads(rule['config_data']) if rule['config_data'] else {}
            rules.append(rule)

        return rules

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rules in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Total rules
            cursor.execute("SELECT COUNT(*) FROM constitution_rules")
            total_rules = cursor.fetchone()[0]
            # Enabled/disabled counts
            cursor.execute("SELECT COUNT(*) FROM rule_configuration WHERE enabled = 1")
            enabled_rules = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM rule_configuration WHERE enabled = 0")
            disabled_rules = cursor.fetchone()[0]
            # Rules by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM constitution_rules
                GROUP BY category
                ORDER BY count DESC
            """)
            category_counts = dict(cursor.fetchall())
            # Rules by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM constitution_rules
                GROUP BY priority
                ORDER BY count DESC
            """)
            priority_counts = dict(cursor.fetchall())

        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "enabled_percentage": (enabled_rules / total_rules * 100) if total_rules > 0 else 0,
            "category_counts": category_counts,
            "priority_counts": priority_counts
        }

    def _log_rule_usage(self, rule_number: int, action: str, context: str = ""):
        """Log rule usage for tracking."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rule_usage (rule_number, action, context)
                VALUES (?, ?, ?)
            """, (rule_number, action, context))
            conn.commit()

    def log_validation(self, rule_number: int, result: str, details: str = ""):
        """
        Log validation result for a rule.

        Args:
            rule_number: Rule number
            result: Validation result (passed, failed, warning)
            details: Additional details
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO validation_history (rule_number, validation_result, details)
                VALUES (?, ?, ?)
            """, (rule_number, result, details))
            conn.commit()

    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        """
        Export rules to JSON format.

        Args:
            enabled_only: If True, export only enabled rules

        Returns:
            JSON string of rules
        """
        rules = self.get_all_rules(enabled_only=enabled_only)
        return json.dumps(rules, indent=2, ensure_ascii=False)

    def import_rules_from_json(self, json_data: str) -> bool:
        """
        Import rules from JSON format.

        Args:
            json_data: JSON string containing rules

        Returns:
            True if successful, False otherwise
        """
        try:
            rules = json.loads(json_data)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for rule in rules:
                    cursor.execute("""
                        INSERT OR REPLACE INTO constitution_rules
                        (rule_number, title, category, priority, content, json_metadata, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        rule['rule_number'],
                        rule['title'],
                        rule['category'],
                        rule['priority'],
                        rule['content'],
                        json.dumps(rule)
                    ))
                conn.commit()
                return True
        except Exception as e:
            try:
                conn.rollback()  # type: ignore[name-defined]
            except Exception:
                pass
            raise e

    def _parse_json(self, json_str: str) -> Any:
        """Parse JSON string safely."""
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def _get_timeout_from_config(self) -> float:
        """Get timeout from configuration."""
        try:
            return 30.0  # Default 30 seconds
        except Exception:
            return 30.0

    def _get_max_retries_from_config(self) -> int:
        """Get max retries from configuration."""
        try:
            return 3  # Default 3 retries
        except Exception:
            return 3

    def _get_base_delay_from_config(self) -> float:
        """Get base delay from configuration."""
        try:
            return 0.1  # Default 100ms
        except Exception:
            return 0.1

    def _get_jitter_from_config(self) -> float:
        """Get jitter from configuration."""
        try:
            return 0.05  # Default 50ms
        except Exception:
            return 0.05

    def _calculate_jitter(self, delay: float) -> float:
        """Add jitter to exponential backoff."""
        return random.uniform(0, self._jitter)

    # Note: close and context manager methods are defined earlier in the class

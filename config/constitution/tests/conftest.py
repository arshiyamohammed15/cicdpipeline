#!/usr/bin/env python3
"""
Pytest configuration and fixtures for constitution database tests.

This module provides common fixtures and test utilities for all
constitution database system tests.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add the project root to the path
import sys
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

# Import with proper path handling
try:
    from config.constitution.database import ConstitutionRulesDB
    from config.constitution.constitution_rules_json import ConstitutionRulesJSON
    from config.constitution.config_manager import ConstitutionRuleManager
    from config.constitution.config_manager_json import ConstitutionRuleManagerJSON
    from config.constitution.backend_factory import ConstitutionBackendFactory
    from config.constitution.sync_manager import ConstitutionSyncManager
    from config.constitution.migration import ConstitutionMigration
except ImportError as e:
    # Fallback for testing environment
    import os
    os.chdir(project_root)
    from config.constitution.database import ConstitutionRulesDB
    from config.constitution.constitution_rules_json import ConstitutionRulesJSON
    from config.constitution.config_manager import ConstitutionRuleManager
    from config.constitution.config_manager_json import ConstitutionRuleManagerJSON
    from config.constitution.backend_factory import ConstitutionBackendFactory
    from config.constitution.sync_manager import ConstitutionSyncManager
    from config.constitution.migration import ConstitutionMigration


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config_dir(temp_dir):
    """Create a test configuration directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def test_db_path(temp_dir):
    """Create a test database path."""
    return temp_dir / "test_constitution.db"


@pytest.fixture
def test_json_path(temp_dir):
    """Create a test JSON database path."""
    return temp_dir / "test_constitution.json"


@pytest.fixture
def sample_rule_data():
    """Sample rule data for testing."""
    return {
        "rule_number": 1,
        "title": "Test Rule",
        "category": "basic_work",
        "priority": "critical",
        "content": "This is a test rule for unit testing.",
        "json_metadata": {
            "rule_number": 1,
            "title": "Test Rule",
            "category": "basic_work",
            "priority": "critical",
            "content": "This is a test rule for unit testing.",
            "enabled": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def sample_rules_data():
    """Sample multiple rules data for testing."""
    return [
        {
            "rule_number": 1,
            "title": "Test Rule 1",
            "category": "basic_work",
            "priority": "critical",
            "content": "This is test rule 1.",
            "json_metadata": {
                "rule_number": 1,
                "title": "Test Rule 1",
                "category": "basic_work",
                "priority": "critical",
                "content": "This is test rule 1.",
                "enabled": True
            }
        },
        {
            "rule_number": 2,
            "title": "Test Rule 2",
            "category": "system_design",
            "priority": "important",
            "content": "This is test rule 2.",
            "json_metadata": {
                "rule_number": 2,
                "title": "Test Rule 2",
                "category": "system_design",
                "priority": "important",
                "content": "This is test rule 2.",
                "enabled": True
            }
        }
    ]


@pytest.fixture
def mock_constitution_config():
    """Mock constitution configuration for testing."""
    return {
        "constitution_version": "2.0",
        "total_rules": 149,
        "default_enabled": True,
        "backend": "sqlite",
        "fallback_backend": "json",
        "auto_fallback": True,
        "auto_sync": True,
        "sync_interval": 60,
        "database_path": "config/constitution_rules.db",
        "last_updated": "2024-01-01T00:00:00Z",
        "description": "Test Configuration for ZeroUI 2.0 Constitution Rules Database",
        "features": {
            "auto_extract_rules": True,
            "sync_with_database": True,
            "enable_by_default": True,
            "track_usage": True,
            "validation_logging": True
        },
        "categories": {
            "basic_work": {
                "description": "Core principles for all development work",
                "priority": "critical",
                "rule_count": 18,
                "enabled_by_default": True
            },
            "system_design": {
                "description": "System architecture and design principles",
                "priority": "critical",
                "rule_count": 12,
                "enabled_by_default": True
            }
        },
        "rules": {
            "1": {
                "enabled": 1,
                "config": {
                    "test": True
                },
                "updated_at": "2024-01-01T00:00:00Z"
            },
            "2": {
                "enabled": 1,
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        "backends": {
            "sqlite": {
                "enabled": True,
                "path": "config/constitution_rules.db",
                "primary": True
            },
            "json": {
                "enabled": True,
                "path": "config/constitution_rules.json",
                "primary": False
            }
        }
    }


@pytest.fixture
def sqlite_db(test_db_path, sample_rules_data):
    """Create a test SQLite database with sample data."""
    db = ConstitutionRulesDB(str(test_db_path))
    
    # Insert sample rules
    with db.get_connection() as conn:
        cursor = conn.cursor()
        for rule_data in sample_rules_data:
            cursor.execute("""
                INSERT OR REPLACE INTO constitution_rules 
                (rule_number, title, category, priority, content, json_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule_data['rule_number'],
                rule_data['title'],
                rule_data['category'],
                rule_data['priority'],
                rule_data['content'],
                json.dumps(rule_data['json_metadata'])
            ))
            
            cursor.execute("""
                INSERT OR REPLACE INTO rule_configuration 
                (rule_number, enabled, config_data)
                VALUES (?, 1, ?)
            """, (
                rule_data['rule_number'],
                json.dumps({"default_enabled": True, "notes": ""})
            ))
        
        conn.commit()
    
    yield db
    db.close()


@pytest.fixture
def json_db(test_json_path, sample_rules_data):
    """Create a test JSON database with sample data."""
    json_db = ConstitutionRulesJSON(str(test_json_path))
    
    # Initialize with sample data
    json_db.data = {
        "constitution_version": "2.0",
        "total_rules": len(sample_rules_data),
        "rules": {},
        "categories": {
            "basic_work": {
                "description": "Core principles for all development work",
                "priority": "critical",
                "rule_count": 1,
                "enabled_by_default": True
            },
            "system_design": {
                "description": "System architecture and design principles",
                "priority": "critical",
                "rule_count": 1,
                "enabled_by_default": True
            }
        },
        "database_info": {
            "created_at": "2024-01-01T00:00:00Z",
            "last_updated": "2024-01-01T00:00:00Z",
            "version": "2.0"
        },
        "statistics": {
            "total_rules": len(sample_rules_data),
            "enabled_rules": len(sample_rules_data),
            "disabled_rules": 0,
            "rules_by_category": {
                "basic_work": 1,
                "system_design": 1
            }
        }
    }
    
    # Add sample rules
    for rule_data in sample_rules_data:
        rule_number = str(rule_data['rule_number'])
        json_db.data["rules"][rule_number] = {
            "rule_number": rule_data['rule_number'],
            "title": rule_data['title'],
            "category": rule_data['category'],
            "priority": rule_data['priority'],
            "content": rule_data['content'],
            "enabled": True,
            "config": {"default_enabled": True},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    json_db._save_database()
    yield json_db


@pytest.fixture
def sqlite_manager(test_config_dir, test_db_path, mock_constitution_config):
    """Create a test SQLite manager."""
    # Create config file
    config_file = test_config_dir / "constitution_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(mock_constitution_config, f, indent=2)
    
    manager = ConstitutionRuleManager(str(test_config_dir), str(test_db_path))
    yield manager


@pytest.fixture
def json_manager(test_config_dir, test_json_path, mock_constitution_config):
    """Create a test JSON manager."""
    # Create config file
    config_file = test_config_dir / "constitution_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(mock_constitution_config, f, indent=2)
    
    manager = ConstitutionRuleManagerJSON(str(test_config_dir), str(test_json_path))
    yield manager


@pytest.fixture
def backend_factory(test_config_dir, mock_constitution_config):
    """Create a test backend factory."""
    # Create config file
    config_file = test_config_dir / "constitution_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(mock_constitution_config, f, indent=2)
    
    factory = ConstitutionBackendFactory(str(test_config_dir))
    yield factory


@pytest.fixture
def sync_manager(test_config_dir):
    """Create a test sync manager."""
    return ConstitutionSyncManager(str(test_config_dir))


@pytest.fixture
def migration_manager(test_config_dir):
    """Create a test migration manager."""
    return ConstitutionMigration(str(test_config_dir))


class TestHelpers:
    """Helper methods for tests."""
    
    @staticmethod
    def create_corrupted_json_file(file_path: Path) -> None:
        """Create a corrupted JSON file for testing."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json content}')  # Invalid JSON
    
    @staticmethod
    def create_empty_json_file(file_path: Path) -> None:
        """Create an empty JSON file for testing."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')
    
    @staticmethod
    def create_large_json_file(file_path: Path, num_rules: int = 1000) -> None:
        """Create a large JSON file for performance testing."""
        data = {
            "constitution_version": "2.0",
            "total_rules": num_rules,
            "rules": {},
            "categories": {},
            "database_info": {
                "created_at": "2024-01-01T00:00:00Z",
                "last_updated": "2024-01-01T00:00:00Z",
                "version": "2.0"
            }
        }
        
        for i in range(1, num_rules + 1):
            data["rules"][str(i)] = {
                "rule_number": i,
                "title": f"Test Rule {i}",
                "category": "basic_work",
                "priority": "critical",
                "content": f"This is test rule {i}.",
                "enabled": True,
                "config": {"default_enabled": True},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def assert_rule_equals(rule1: Dict[str, Any], rule2: Dict[str, Any]) -> None:
        """Assert that two rules are equal (ignoring timestamps)."""
        # Remove timestamp fields for comparison
        fields_to_ignore = ['created_at', 'updated_at', 'last_updated']
        
        for field in fields_to_ignore:
            rule1.pop(field, None)
            rule2.pop(field, None)
        
        assert rule1 == rule2, f"Rules not equal: {rule1} != {rule2}"
    
    @staticmethod
    def assert_database_healthy(db) -> bool:
        """Assert that a database is healthy."""
        try:
            health = db.health_check()
            assert health.get('healthy', False), f"Database not healthy: {health}"
            return True
        except Exception as e:
            pytest.fail(f"Database health check failed: {e}")


@pytest.fixture
def test_helpers():
    """Provide test helper methods."""
    return TestHelpers

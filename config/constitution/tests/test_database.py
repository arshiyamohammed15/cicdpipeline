#!/usr/bin/env python3
"""
Test suite for ConstitutionRulesDB (SQLite backend).

This module tests all core database functionality including:
- Database initialization and schema creation
- Rule CRUD operations
- Connection pooling and retry logic
- Data integrity validation
- Backup and restore operations
"""

import pytest
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from config.constitution.database import ConstitutionRulesDB


class TestConstitutionRulesDB:
    """Test suite for ConstitutionRulesDB class."""
    
    def test_database_initialization(self, temp_dir, test_db_path):
        """Test database initialization and schema creation."""
        # Test database creation
        db = ConstitutionRulesDB(str(test_db_path))
        
        # Verify database file exists
        assert test_db_path.exists(), "Database file should be created"
        
        # Verify tables exist
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'constitution_rules',
                'rule_configuration', 
                'rule_categories',
                'rule_usage',
                'validation_history'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} should exist"
        
        db.close()
    
    def test_database_initialization_with_existing_file(self, temp_dir, test_db_path):
        """Test database initialization with existing file."""
        # Create existing database file
        test_db_path.touch()
        
        # Should not raise error
        db = ConstitutionRulesDB(str(test_db_path))
        assert test_db_path.exists()
        db.close()
    
    def test_connection_context_manager(self, sqlite_db):
        """Test connection context manager functionality."""
        with sqlite_db.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_retry_logic(self, temp_dir, test_db_path):
        """Test connection retry logic with failures."""
        db = ConstitutionRulesDB(str(test_db_path))
        
        # Mock connection to fail first, then succeed
        original_connect = sqlite3.connect
        call_count = 0
        
        def mock_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise sqlite3.Error("Connection failed")
            return original_connect(*args, **kwargs)
        
        with patch('sqlite3.connect', side_effect=mock_connect):
            # Should retry and eventually succeed
            with db.get_connection() as conn:
                assert conn is not None
                assert call_count == 2  # Should have retried once
        
        db.close()
    
    def test_connection_max_retries_exceeded(self, temp_dir, test_db_path):
        """Test behavior when max retries are exceeded."""
        db = ConstitutionRulesDB(str(test_db_path))
        
        # Mock connection to always fail
        with patch('sqlite3.connect', side_effect=sqlite3.Error("Always fails")):
            with pytest.raises(sqlite3.Error):
                with db.get_connection() as conn:
                    pass
        
        db.close()
    
    def test_wal_mode_enabled(self, sqlite_db):
        """Test that WAL mode is enabled for better concurrency."""
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == "WAL", "WAL mode should be enabled"
    
    def test_database_performance_settings(self, sqlite_db):
        """Test that performance settings are applied."""
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check synchronous setting
            cursor.execute("PRAGMA synchronous")
            sync_mode = cursor.fetchone()[0]
            assert sync_mode == 1, "Synchronous mode should be NORMAL (1)"
            
            # Check cache size
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            assert cache_size == 10000, "Cache size should be 10000"
            
            # Check temp store
            cursor.execute("PRAGMA temp_store")
            temp_store = cursor.fetchone()[0]
            assert temp_store == 2, "Temp store should be MEMORY (2)"
    
    def test_rule_insertion(self, sqlite_db, sample_rule_data):
        """Test inserting a new rule."""
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert rule
            cursor.execute("""
                INSERT INTO constitution_rules 
                (rule_number, title, category, priority, content, json_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sample_rule_data['rule_number'],
                sample_rule_data['title'],
                sample_rule_data['category'],
                sample_rule_data['priority'],
                sample_rule_data['content'],
                json.dumps(sample_rule_data['json_metadata'])
            ))
            
            # Insert configuration
            cursor.execute("""
                INSERT INTO rule_configuration 
                (rule_number, enabled, config_data)
                VALUES (?, 1, ?)
            """, (
                sample_rule_data['rule_number'],
                json.dumps({"default_enabled": True})
            ))
            
            conn.commit()
            
            # Verify insertion
            cursor.execute("SELECT * FROM constitution_rules WHERE rule_number = ?", 
                         (sample_rule_data['rule_number'],))
            result = cursor.fetchone()
            assert result is not None
            assert result[1] == sample_rule_data['title']
    
    def test_rule_retrieval(self, sqlite_db):
        """Test retrieving rules from database."""
        rules = sqlite_db.get_all_rules()
        
        assert len(rules) == 2, "Should have 2 test rules"
        
        # Check rule structure
        for rule in rules:
            assert 'rule_number' in rule
            assert 'title' in rule
            assert 'category' in rule
            assert 'priority' in rule
            assert 'content' in rule
            assert 'enabled' in rule
    
    def test_rule_retrieval_by_number(self, sqlite_db):
        """Test retrieving a specific rule by number."""
        rule = sqlite_db.get_rule_by_number(1)
        
        assert rule is not None
        assert rule['rule_number'] == 1
        assert rule['title'] == "Test Rule 1"
        assert rule['category'] == "basic_work"
    
    def test_rule_retrieval_nonexistent(self, sqlite_db):
        """Test retrieving a non-existent rule."""
        rule = sqlite_db.get_rule_by_number(999)
        assert rule is None
    
    def test_rule_enable_disable(self, sqlite_db):
        """Test enabling and disabling rules."""
        # Disable rule 1
        success = sqlite_db.update_rule_configuration(1, enabled=False, reason="Test disable")
        assert success
        
        # Verify rule is disabled
        rule = sqlite_db.get_rule_by_number(1)
        assert not rule['enabled']
        
        # Enable rule 1
        success = sqlite_db.update_rule_configuration(1, enabled=True, reason="Test enable")
        assert success
        
        # Verify rule is enabled
        rule = sqlite_db.get_rule_by_number(1)
        assert rule['enabled']
    
    def test_rule_search(self, sqlite_db):
        """Test searching rules by content."""
        results = sqlite_db.search_rules("test")
        
        assert len(results) >= 1, "Should find at least one rule with 'test'"
        
        for result in results:
            assert 'test' in result['title'].lower() or 'test' in result['content'].lower()
    
    def test_rule_statistics(self, sqlite_db):
        """Test rule statistics generation."""
        stats = sqlite_db.get_rule_statistics()
        
        assert 'total_rules' in stats
        assert 'enabled_rules' in stats
        assert 'disabled_rules' in stats
        assert 'enabled_percentage' in stats
        assert 'category_counts' in stats
        assert 'priority_counts' in stats
        
        assert stats['total_rules'] == 2
        assert stats['enabled_rules'] == 2
        assert stats['disabled_rules'] == 0
        assert stats['enabled_percentage'] == 100.0
    
    def test_rule_usage_tracking(self, sqlite_db):
        """Test rule usage tracking."""
        # Record usage
        success = sqlite_db.record_rule_usage(1, "test_operation", {"test": True})
        assert success
        
        # Get usage history
        usage = sqlite_db.get_rule_usage_history(1)
        assert len(usage) >= 1
        
        latest_usage = usage[0]
        assert latest_usage['rule_number'] == 1
        assert latest_usage['operation'] == "test_operation"
    
    def test_validation_history_tracking(self, sqlite_db):
        """Test validation history tracking."""
        # Record validation
        success = sqlite_db.record_validation(1, "test_file.py", True, "No violations found")
        assert success
        
        # Get validation history
        history = sqlite_db.get_validation_history(1)
        assert len(history) >= 1
        
        latest_validation = history[0]
        assert latest_validation['rule_number'] == 1
        assert latest_validation['file_path'] == "test_file.py"
        assert latest_validation['passed'] == True
    
    def test_database_backup(self, sqlite_db, temp_dir):
        """Test database backup functionality."""
        backup_path = temp_dir / "backup.db"
        
        success = sqlite_db.backup_database(str(backup_path))
        assert success
        assert backup_path.exists()
        
        # Verify backup contains data
        backup_db = ConstitutionRulesDB(str(backup_path))
        rules = backup_db.get_all_rules()
        assert len(rules) == 2
        backup_db.close()
    
    def test_database_restore(self, sqlite_db, temp_dir):
        """Test database restore functionality."""
        # Create backup
        backup_path = temp_dir / "backup.db"
        sqlite_db.backup_database(str(backup_path))
        
        # Create new database and restore
        new_db_path = temp_dir / "restored.db"
        new_db = ConstitutionRulesDB(str(new_db_path))
        
        success = new_db.restore_database(str(backup_path))
        assert success
        
        # Verify restored data
        rules = new_db.get_all_rules()
        assert len(rules) == 2
        new_db.close()
    
    def test_database_health_check(self, sqlite_db):
        """Test database health check."""
        health = sqlite_db.health_check()
        
        assert 'healthy' in health
        assert 'database_exists' in health
        assert 'database_readable' in health
        assert 'database_writable' in health
        assert 'data_valid' in health
        
        assert health['healthy'] == True
        assert health['database_exists'] == True
        assert health['database_readable'] == True
        assert health['database_writable'] == True
        assert health['data_valid'] == True
    
    def test_database_health_check_corrupted(self, temp_dir, test_db_path):
        """Test database health check with corrupted database."""
        # Create corrupted database file
        with open(test_db_path, 'w') as f:
            f.write("corrupted data")
        
        db = ConstitutionRulesDB(str(test_db_path))
        health = db.health_check()
        
        assert health['healthy'] == False
        assert health['database_exists'] == True
        assert health['database_readable'] == False
        assert health['database_writable'] == False
        assert health['data_valid'] == False
        
        db.close()
    
    def test_concurrent_access(self, sqlite_db):
        """Test concurrent database access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with sqlite_db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT rule_number FROM constitution_rules LIMIT 1")
                    result = cursor.fetchone()
                    results.append((worker_id, result[0]))
                    time.sleep(0.1)  # Simulate work
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors and all threads got results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    
    def test_database_close(self, sqlite_db):
        """Test database close functionality."""
        # Should not raise error
        sqlite_db.close()
        
        # Should handle multiple close calls
        sqlite_db.close()
    
    def test_context_manager_support(self, temp_dir, test_db_path):
        """Test database context manager support."""
        with ConstitutionRulesDB(str(test_db_path)) as db:
            assert db is not None
            rules = db.get_all_rules()
            assert isinstance(rules, list)
        
        # Database should be closed after context exit
        # (This is implicit - no explicit test needed as close() is called in __exit__)
    
    def test_database_performance_large_dataset(self, temp_dir, test_db_path):
        """Test database performance with large dataset."""
        db = ConstitutionRulesDB(str(test_db_path))
        
        # Insert many rules
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for i in range(1000):
                cursor.execute("""
                    INSERT INTO constitution_rules 
                    (rule_number, title, category, priority, content, json_metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    i + 1000,  # Start from 1000 to avoid conflicts
                    f"Performance Test Rule {i}",
                    "basic_work",
                    "critical",
                    f"This is performance test rule {i}.",
                    json.dumps({"test": True, "rule_number": i + 1000})
                ))
                
                cursor.execute("""
                    INSERT INTO rule_configuration 
                    (rule_number, enabled, config_data)
                    VALUES (?, 1, ?)
                """, (
                    i + 1000,
                    json.dumps({"default_enabled": True})
                ))
            
            conn.commit()
        
        # Test retrieval performance
        start_time = time.time()
        rules = db.get_all_rules()
        end_time = time.time()
        
        assert len(rules) == 1002  # 2 original + 1000 new
        assert (end_time - start_time) < 1.0, "Retrieval should be fast"
        
        db.close()
    
    def test_database_error_handling(self, temp_dir, test_db_path):
        """Test database error handling."""
        db = ConstitutionRulesDB(str(test_db_path))
        
        # Test invalid SQL
        with pytest.raises(sqlite3.Error):
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INVALID SQL STATEMENT")
        
        # Test invalid data types
        with pytest.raises(sqlite3.Error):
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO constitution_rules (rule_number) VALUES (?)", ("invalid",))
        
        db.close()
    
    def test_database_transaction_rollback(self, sqlite_db):
        """Test database transaction rollback."""
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Insert rule
            cursor.execute("""
                INSERT INTO constitution_rules 
                (rule_number, title, category, priority, content, json_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                999,
                "Test Rollback Rule",
                "basic_work",
                "critical",
                "This rule should be rolled back.",
                json.dumps({"test": True})
            ))
            
            # Rollback transaction
            conn.rollback()
            
            # Verify rule was not inserted
            cursor.execute("SELECT * FROM constitution_rules WHERE rule_number = 999")
            result = cursor.fetchone()
            assert result is None
    
    def test_database_indexes(self, sqlite_db):
        """Test that database indexes are created."""
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check indexes exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_rules_category',
                'idx_rules_priority',
                'idx_config_enabled',
                'idx_usage_rule',
                'idx_validation_rule'
            ]
            
            for index in expected_indexes:
                assert index in indexes, f"Index {index} should exist"

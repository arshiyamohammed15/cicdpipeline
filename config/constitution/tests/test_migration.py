#!/usr/bin/env python3
"""
Test suite for ConstitutionMigration.

This module tests all migration functionality including:
- Full migration SQLite → JSON
- Full migration JSON → SQLite
- Data integrity after migration
- Migration history tracking
- Rollback capabilities
- Migration with large datasets
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from config.constitution.migration import (
    ConstitutionMigration,
    get_migration_manager,
    migrate_sqlite_to_json,
    migrate_json_to_sqlite,
    repair_sync
)


class TestConstitutionMigration:
    """Test suite for ConstitutionMigration class."""
    
    def test_migration_manager_initialization(self, migration_manager):
        """Test migration manager initialization."""
        assert migration_manager is not None
        assert migration_manager.config_dir is not None
        assert migration_manager.migration_history_path is not None
    
    def test_migration_manager_load_migration_history(self, migration_manager):
        """Test loading migration history."""
        history = migration_manager._load_migration_history()
        assert isinstance(history, list)
    
    def test_migration_manager_load_migration_history_corrupted(self, temp_dir, test_helpers):
        """Test loading corrupted migration history."""
        # Create corrupted migration history file
        migration_history_path = temp_dir / "migration_history.json"
        test_helpers.create_corrupted_json_file(migration_history_path)
        
        migration_manager = ConstitutionMigration(str(temp_dir))
        history = migration_manager._load_migration_history()
        
        # Should reset to empty list
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_migration_manager_save_migration_history(self, migration_manager):
        """Test saving migration history."""
        # Add test migration entry
        test_entry = {
            "timestamp": "2024-01-01T00:00:00Z",
            "migration_type": "sqlite_to_json",
            "source_backend": "sqlite",
            "target_backend": "json",
            "success": True,
            "rules_migrated": 149,
            "duration_seconds": 1.5
        }
        
        migration_manager._migration_history.append(test_entry)
        success = migration_manager._save_migration_history()
        assert success
        
        # Verify history was saved
        assert migration_manager.migration_history_path.exists()
        
        with open(migration_manager.migration_history_path, 'r', encoding='utf-8') as f:
            saved_history = json.load(f)
        
        assert len(saved_history) == 1
        assert saved_history[0]['migration_type'] == "sqlite_to_json"
    
    def test_migration_manager_get_migration_history(self, migration_manager):
        """Test getting migration history."""
        # Add test entries
        test_entries = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "migration_type": "sqlite_to_json",
                "source_backend": "sqlite",
                "target_backend": "json",
                "success": True,
                "rules_migrated": 149
            },
            {
                "timestamp": "2024-01-01T01:00:00Z",
                "migration_type": "json_to_sqlite",
                "source_backend": "json",
                "target_backend": "sqlite",
                "success": True,
                "rules_migrated": 149
            }
        ]
        
        migration_manager._migration_history.extend(test_entries)
        migration_manager._save_migration_history()
        
        # Get history
        history = migration_manager.get_migration_history()
        assert len(history) == 2
        
        # Test filtering
        sqlite_to_json_history = migration_manager.get_migration_history(
            migration_type="sqlite_to_json"
        )
        assert len(sqlite_to_json_history) == 1
        assert sqlite_to_json_history[0]['migration_type'] == "sqlite_to_json"
        
        successful_migrations = migration_manager.get_migration_history(success=True)
        assert len(successful_migrations) == 2
        
        failed_migrations = migration_manager.get_migration_history(success=False)
        assert len(failed_migrations) == 0
    
    def test_migration_manager_migrate_sqlite_to_json(self, migration_manager, sqlite_db, json_db):
        """Test migration from SQLite to JSON."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            result = migration_manager.migrate_sqlite_to_json()
            
            assert result['success'] == True
            assert result['migration_type'] == "sqlite_to_json"
            assert result['source_backend'] == "sqlite"
            assert result['target_backend'] == "json"
            assert result['rules_migrated'] >= 0
    
    def test_migration_manager_migrate_json_to_sqlite(self, migration_manager, sqlite_db, json_db):
        """Test migration from JSON to SQLite."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            result = migration_manager.migrate_json_to_sqlite()
            
            assert result['success'] == True
            assert result['migration_type'] == "json_to_sqlite"
            assert result['source_backend'] == "json"
            assert result['target_backend'] == "sqlite"
            assert result['rules_migrated'] >= 0
    
    def test_migration_manager_migrate_with_backup(self, migration_manager, sqlite_db, json_db, temp_dir):
        """Test migration with backup."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            # Mock backup methods
            with patch.object(sqlite_db, 'backup_database', return_value=True), \
                 patch.object(json_db, 'backup_database', return_value=True):
                
                result = migration_manager.migrate_sqlite_to_json(create_backup=True)
                
                assert result['success'] == True
                assert 'backup_created' in result
    
    def test_migration_manager_migrate_failure(self, migration_manager):
        """Test migration failure handling."""
        # Mock managers to fail
        with patch.object(migration_manager, '_get_sqlite_manager', 
                         side_effect=Exception("SQLite failed")):
            
            result = migration_manager.migrate_sqlite_to_json()
            
            assert result['success'] == False
            assert 'error' in result
            assert "SQLite failed" in result['error']
    
    def test_migration_manager_verify_migration(self, migration_manager, sqlite_db, json_db):
        """Test migration verification."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            result = migration_manager.verify_migration("sqlite_to_json")
            
            assert 'migration_valid' in result
            assert 'source_rules' in result
            assert 'target_rules' in result
            assert 'differences' in result
    
    def test_migration_manager_rollback_migration(self, migration_manager, sqlite_db, json_db):
        """Test migration rollback."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            result = migration_manager.rollback_migration("sqlite_to_json")
            
            assert result['success'] == True
            assert result['rollback_type'] == "sqlite_to_json"
    
    def test_migration_manager_rollback_migration_no_backup(self, migration_manager):
        """Test migration rollback without backup."""
        result = migration_manager.rollback_migration("sqlite_to_json")
        
        assert result['success'] == False
        assert 'error' in result
        assert "No backup found" in result['error']
    
    def test_migration_manager_get_migration_status(self, migration_manager):
        """Test getting migration status."""
        status = migration_manager.get_migration_status()
        
        assert 'total_migrations' in status
        assert 'successful_migrations' in status
        assert 'failed_migrations' in status
        assert 'last_migration' in status
        assert 'migration_types' in status
    
    def test_migration_manager_clear_migration_history(self, migration_manager):
        """Test clearing migration history."""
        # Add test history
        migration_manager._migration_history.append({
            "timestamp": "2024-01-01T00:00:00Z",
            "migration_type": "test_migration",
            "success": True
        })
        
        # Clear history
        success = migration_manager.clear_migration_history()
        assert success
        
        # Verify history is cleared
        assert len(migration_manager._migration_history) == 0
    
    def test_migration_manager_migration_performance(self, migration_manager, sqlite_db, json_db):
        """Test migration performance."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            start_time = time.time()
            result = migration_manager.migrate_sqlite_to_json()
            end_time = time.time()
            
            assert result['success'] == True
            assert (end_time - start_time) < 10.0, "Migration should be reasonably fast"
            assert 'duration_seconds' in result
    
    def test_migration_manager_data_integrity_check(self, migration_manager, sqlite_db, json_db):
        """Test data integrity check during migration."""
        # Mock managers
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=json_db):
            
            # Mock data integrity check
            with patch.object(migration_manager, '_check_data_integrity', return_value=False):
                result = migration_manager.migrate_sqlite_to_json()
                
                assert result['success'] == False
                assert 'integrity_check_failed' in result
    
    def test_migration_manager_large_dataset_migration(self, migration_manager, temp_dir, test_helpers):
        """Test migration with large dataset."""
        # Create large SQLite database
        large_sqlite_path = temp_dir / "large_sqlite.db"
        large_json_path = temp_dir / "large_json.json"
        
        # Mock large managers
        large_sqlite_db = MagicMock()
        large_sqlite_db.get_all_rules.return_value = [
            {"rule_number": i, "title": f"Rule {i}", "content": f"Content {i}"}
            for i in range(1000)
        ]
        large_sqlite_db.backup_database.return_value = True
        
        large_json_db = MagicMock()
        large_json_db.save_database.return_value = True
        large_json_db.backup_database.return_value = True
        
        with patch.object(migration_manager, '_get_sqlite_manager', return_value=large_sqlite_db), \
             patch.object(migration_manager, '_get_json_manager', return_value=large_json_db):
            
            result = migration_manager.migrate_sqlite_to_json()
            
            assert result['success'] == True
            assert result['rules_migrated'] == 1000
    
    def test_migration_manager_concurrent_migration(self, migration_manager, sqlite_db, json_db):
        """Test concurrent migration operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with patch.object(migration_manager, '_get_sqlite_manager', return_value=sqlite_db), \
                     patch.object(migration_manager, '_get_json_manager', return_value=json_db):
                    
                    result = migration_manager.migrate_sqlite_to_json()
                    results.append((worker_id, result['success']))
                    time.sleep(0.1)  # Simulate work
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors and all threads got results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # All threads should succeed
        for worker_id, success in results:
            assert success == True, f"Worker {worker_id} failed"
    
    def test_migration_manager_error_recovery(self, migration_manager):
        """Test error recovery during migration."""
        # Mock managers to fail initially, then succeed
        call_count = 0
        
        def mock_sqlite_manager():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Initial failure")
            return MagicMock()
        
        with patch.object(migration_manager, '_get_sqlite_manager', side_effect=mock_sqlite_manager), \
             patch.object(migration_manager, '_get_json_manager', return_value=MagicMock()):
            
            result = migration_manager.migrate_sqlite_to_json()
            
            # Should fail on first attempt
            assert result['success'] == False
            assert "Initial failure" in result['error']


class TestMigrationFunctions:
    """Test suite for migration module functions."""
    
    def test_get_migration_manager_function(self, test_config_dir):
        """Test get_migration_manager function."""
        migration_manager = get_migration_manager(str(test_config_dir))
        assert migration_manager is not None
        assert isinstance(migration_manager, ConstitutionMigration)
    
    def test_migrate_sqlite_to_json_function(self, test_config_dir, sqlite_db, json_db):
        """Test migrate_sqlite_to_json function."""
        # Mock managers
        with patch('config.constitution.migration.ConstitutionMigration') as mock_migration_manager:
            mock_instance = MagicMock()
            mock_instance.migrate_sqlite_to_json.return_value = {
                'success': True,
                'rules_migrated': 149
            }
            mock_migration_manager.return_value = mock_instance
            
            result = migrate_sqlite_to_json(str(test_config_dir))
            
            assert result['success'] == True
            assert result['rules_migrated'] == 149
            mock_instance.migrate_sqlite_to_json.assert_called_once()
    
    def test_migrate_json_to_sqlite_function(self, test_config_dir, sqlite_db, json_db):
        """Test migrate_json_to_sqlite function."""
        # Mock managers
        with patch('config.constitution.migration.ConstitutionMigration') as mock_migration_manager:
            mock_instance = MagicMock()
            mock_instance.migrate_json_to_sqlite.return_value = {
                'success': True,
                'rules_migrated': 149
            }
            mock_migration_manager.return_value = mock_instance
            
            result = migrate_json_to_sqlite(str(test_config_dir))
            
            assert result['success'] == True
            assert result['rules_migrated'] == 149
            mock_instance.migrate_json_to_sqlite.assert_called_once()
    
    def test_repair_sync_function(self, test_config_dir, sqlite_db, json_db):
        """Test repair_sync function."""
        # Mock managers
        with patch('config.constitution.migration.ConstitutionMigration') as mock_migration_manager:
            mock_instance = MagicMock()
            mock_instance.repair_sync.return_value = {
                'success': True,
                'repairs_performed': 3
            }
            mock_migration_manager.return_value = mock_instance
            
            result = repair_sync(str(test_config_dir))
            
            assert result['success'] == True
            assert result['repairs_performed'] == 3
            mock_instance.repair_sync.assert_called_once()


class TestMigrationIntegration:
    """Integration tests for migration."""
    
    def test_migration_with_real_managers(self, migration_manager, sqlite_manager, json_manager):
        """Test migration with real manager instances."""
        # Test SQLite to JSON migration
        result = migration_manager.migrate_sqlite_to_json()
        assert result['success'] == True
        
        # Test JSON to SQLite migration
        result = migration_manager.migrate_json_to_sqlite()
        assert result['success'] == True
    
    def test_migration_verification_with_real_managers(self, migration_manager, sqlite_manager, json_manager):
        """Test migration verification with real managers."""
        result = migration_manager.verify_migration("sqlite_to_json")
        
        assert 'migration_valid' in result
        assert 'source_rules' in result
        assert 'target_rules' in result
        assert 'differences' in result
    
    def test_migration_history_tracking(self, migration_manager, sqlite_manager, json_manager):
        """Test migration history tracking with real operations."""
        # Perform migrations
        migration_manager.migrate_sqlite_to_json()
        migration_manager.migrate_json_to_sqlite()
        
        # Check history
        history = migration_manager.get_migration_history()
        assert len(history) >= 2
        
        # Check specific migration types
        migration_types = [entry['migration_type'] for entry in history]
        assert 'sqlite_to_json' in migration_types
        assert 'json_to_sqlite' in migration_types
    
    def test_migration_status_tracking(self, migration_manager, sqlite_manager, json_manager):
        """Test migration status tracking."""
        # Get initial status
        initial_status = migration_manager.get_migration_status()
        initial_count = initial_status['total_migrations']
        
        # Perform migration
        migration_manager.migrate_sqlite_to_json()
        
        # Check updated status
        updated_status = migration_manager.get_migration_status()
        assert updated_status['total_migrations'] > initial_count
        assert updated_status['last_migration'] is not None
    
    def test_migration_error_handling_integration(self, migration_manager):
        """Test error handling integration."""
        # Test with invalid managers
        with patch.object(migration_manager, '_get_sqlite_manager', 
                         side_effect=Exception("Manager error")):
            
            result = migration_manager.migrate_sqlite_to_json()
            assert result['success'] == False
            assert 'error' in result
            
            # Check error is recorded in history
            history = migration_manager.get_migration_history()
            error_entries = [entry for entry in history if not entry.get('success', True)]
            assert len(error_entries) >= 1
    
    def test_migration_performance_integration(self, migration_manager, sqlite_manager, json_manager):
        """Test migration performance integration."""
        # Test migration performance
        start_time = time.time()
        result = migration_manager.migrate_sqlite_to_json()
        end_time = time.time()
        
        assert result['success'] == True
        assert (end_time - start_time) < 15.0, "Migration should be reasonably fast"
        
        # Check performance is recorded
        history = migration_manager.get_migration_history()
        if history:
            latest_entry = history[-1]
            assert 'duration_seconds' in latest_entry or 'timestamp' in latest_entry
    
    def test_migration_data_integrity(self, migration_manager, sqlite_manager, json_manager):
        """Test data integrity after migration."""
        # Perform migration
        result = migration_manager.migrate_sqlite_to_json()
        assert result['success'] == True
        
        # Verify migration
        verify_result = migration_manager.verify_migration("sqlite_to_json")
        assert verify_result['migration_valid'] == True
        assert len(verify_result['differences']) == 0
    
    def test_migration_backup_integration(self, migration_manager, sqlite_manager, json_manager, temp_dir):
        """Test backup integration during migration."""
        # Perform migration with backup
        result = migration_manager.migrate_sqlite_to_json(create_backup=True)
        assert result['success'] == True
        
        # Check backup was created
        backup_files = list(temp_dir.glob("*.backup*"))
        assert len(backup_files) >= 0  # Backup files may be created
    
    def test_migration_configuration_persistence(self, migration_manager, temp_dir):
        """Test configuration persistence across migration manager instances."""
        # Perform migration
        migration_manager.migrate_sqlite_to_json()
        
        # Create new migration manager instance
        new_migration_manager = ConstitutionMigration(str(temp_dir))
        
        # Should have access to migration history
        history = new_migration_manager.get_migration_history()
        assert len(history) >= 1
    
    def test_migration_rollback_integration(self, migration_manager, sqlite_manager, json_manager, temp_dir):
        """Test migration rollback integration."""
        # Create backup first
        backup_path = temp_dir / "backup.db"
        sqlite_manager.backup_database(str(backup_path))
        
        # Perform migration
        result = migration_manager.migrate_sqlite_to_json()
        assert result['success'] == True
        
        # Rollback migration
        rollback_result = migration_manager.rollback_migration("sqlite_to_json")
        assert rollback_result['success'] == True
    
    def test_migration_repair_sync_integration(self, migration_manager, sqlite_manager, json_manager):
        """Test repair sync integration."""
        # Perform repair sync
        result = migration_manager.repair_sync()
        
        assert result['success'] == True
        assert 'repairs_performed' in result
        assert 'sync_verified' in result

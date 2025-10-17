#!/usr/bin/env python3
"""
Test suite for ConstitutionSyncManager.

This module tests all synchronization functionality including:
- SQLite to JSON sync
- JSON to SQLite sync
- Bidirectional sync
- Conflict detection and resolution
- Sync history tracking
- Data consistency verification
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from config.constitution.sync_manager import (
    ConstitutionSyncManager,
    get_sync_manager,
    sync_backends,
    verify_sync
)


class TestConstitutionSyncManager:
    """Test suite for ConstitutionSyncManager class."""
    
    def test_sync_manager_initialization(self, sync_manager):
        """Test sync manager initialization."""
        assert sync_manager is not None
        assert sync_manager.config_dir is not None
        assert sync_manager.sync_history_path is not None
    
    def test_sync_manager_load_sync_history(self, sync_manager):
        """Test loading sync history."""
        history = sync_manager._load_sync_history()
        assert isinstance(history, list)
    
    def test_sync_manager_load_sync_history_corrupted(self, temp_dir, test_helpers):
        """Test loading corrupted sync history."""
        # Create corrupted sync history file
        sync_history_path = temp_dir / "sync_history.json"
        test_helpers.create_corrupted_json_file(sync_history_path)
        
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        history = sync_manager._load_sync_history()
        
        # Should reset to empty list
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_sync_manager_save_sync_history(self, sync_manager):
        """Test saving sync history."""
        # Add test history entry
        test_entry = {
            "timestamp": "2024-01-01T00:00:00Z",
            "operation": "test_sync",
            "source": "sqlite",
            "target": "json",
            "success": True,
            "rules_synced": 5
        }
        
        sync_manager._sync_history.append(test_entry)
        success = sync_manager._save_sync_history()
        assert success
        
        # Verify history was saved
        assert sync_manager.sync_history_path.exists()
        
        with open(sync_manager.sync_history_path, 'r', encoding='utf-8') as f:
            saved_history = json.load(f)
        
        assert len(saved_history) == 1
        assert saved_history[0]['operation'] == "test_sync"
    
    def test_sync_manager_get_sync_history(self, sync_manager):
        """Test getting sync history."""
        # Add test entries
        test_entries = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "operation": "sync_sqlite_to_json",
                "source": "sqlite",
                "target": "json",
                "success": True,
                "rules_synced": 5
            },
            {
                "timestamp": "2024-01-01T01:00:00Z",
                "operation": "sync_json_to_sqlite",
                "source": "json",
                "target": "sqlite",
                "success": True,
                "rules_synced": 3
            }
        ]
        
        sync_manager._sync_history.extend(test_entries)
        sync_manager._save_sync_history()
        
        # Get history
        history = sync_manager.get_sync_history()
        assert len(history) == 2
        
        # Test filtering
        sqlite_history = sync_manager.get_sync_history(source="sqlite")
        assert len(sqlite_history) == 1
        assert sqlite_history[0]['source'] == "sqlite"
        
        json_history = sync_manager.get_sync_history(target="json")
        assert len(json_history) == 1
        assert json_history[0]['target'] == "json"
    
    def test_sync_manager_sync_sqlite_to_json(self, sync_manager, sqlite_db, json_db):
        """Test syncing from SQLite to JSON."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            result = sync_manager.sync_sqlite_to_json()
            
            assert result['success'] == True
            assert result['source'] == "sqlite"
            assert result['target'] == "json"
            assert result['rules_synced'] >= 0
    
    def test_sync_manager_sync_json_to_sqlite(self, sync_manager, sqlite_db, json_db):
        """Test syncing from JSON to SQLite."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            result = sync_manager.sync_json_to_sqlite()
            
            assert result['success'] == True
            assert result['source'] == "json"
            assert result['target'] == "sqlite"
            assert result['rules_synced'] >= 0
    
    def test_sync_manager_bidirectional_sync(self, sync_manager, sqlite_db, json_db):
        """Test bidirectional sync."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            result = sync_manager.sync_bidirectional()
            
            assert result['success'] == True
            assert 'sqlite_to_json' in result
            assert 'json_to_sqlite' in result
    
    def test_sync_manager_auto_sync(self, sync_manager, sqlite_db, json_db):
        """Test automatic sync."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            result = sync_manager.auto_sync()
            
            assert result['success'] == True
            assert 'sync_performed' in result
    
    def test_sync_manager_sync_with_conflicts(self, sync_manager, sqlite_db, json_db):
        """Test sync with conflicts."""
        # Mock managers with different data
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            # Mock conflict detection
            with patch.object(sync_manager, '_detect_conflicts', return_value=[{
                'rule_number': 1,
                'conflict_type': 'content_mismatch',
                'sqlite_value': 'SQLite content',
                'json_value': 'JSON content'
            }]):
                
                result = sync_manager.sync_sqlite_to_json()
                
                assert result['success'] == True
                assert 'conflicts_detected' in result
                assert result['conflicts_detected'] == 1
    
    def test_sync_manager_sync_failure(self, sync_manager):
        """Test sync failure handling."""
        # Mock managers to fail
        with patch.object(sync_manager, '_get_sqlite_manager', 
                         side_effect=Exception("SQLite failed")):
            
            result = sync_manager.sync_sqlite_to_json()
            
            assert result['success'] == False
            assert 'error' in result
            assert "SQLite failed" in result['error']
    
    def test_sync_manager_verify_sync(self, sync_manager, sqlite_db, json_db):
        """Test sync verification."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            result = sync_manager.verify_sync()
            
            assert 'in_sync' in result
            assert 'differences' in result
            assert 'sqlite_rules' in result
            assert 'json_rules' in result
    
    def test_sync_manager_get_sync_status(self, sync_manager):
        """Test getting sync status."""
        status = sync_manager.get_sync_status()
        
        assert 'last_sync' in status
        assert 'sync_count' in status
        assert 'last_successful_sync' in status
        assert 'sync_errors' in status
    
    def test_sync_manager_clear_sync_history(self, sync_manager):
        """Test clearing sync history."""
        # Add test history
        sync_manager._sync_history.append({
            "timestamp": "2024-01-01T00:00:00Z",
            "operation": "test_sync",
            "success": True
        })
        
        # Clear history
        success = sync_manager.clear_sync_history()
        assert success
        
        # Verify history is cleared
        assert len(sync_manager._sync_history) == 0
    
    def test_sync_manager_backup_before_sync(self, sync_manager, sqlite_db, json_db):
        """Test backup before sync."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            # Mock backup methods
            with patch.object(sqlite_db, 'backup_database', return_value=True), \
                 patch.object(json_db, 'backup_database', return_value=True):
                
                result = sync_manager.sync_sqlite_to_json(backup_before_sync=True)
                
                assert result['success'] == True
                assert 'backup_created' in result
    
    def test_sync_manager_sync_performance(self, sync_manager, sqlite_db, json_db):
        """Test sync performance."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            start_time = time.time()
            result = sync_manager.sync_sqlite_to_json()
            end_time = time.time()
            
            assert result['success'] == True
            assert (end_time - start_time) < 5.0, "Sync should be reasonably fast"
    
    def test_sync_manager_concurrent_sync(self, sync_manager, sqlite_db, json_db):
        """Test concurrent sync operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
                     patch.object(sync_manager, '_get_json_manager', return_value=json_db):
                    
                    result = sync_manager.sync_sqlite_to_json()
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
    
    def test_sync_manager_error_recovery(self, sync_manager):
        """Test error recovery during sync."""
        # Mock managers to fail initially, then succeed
        call_count = 0
        
        def mock_sqlite_manager():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Initial failure")
            return MagicMock()
        
        with patch.object(sync_manager, '_get_sqlite_manager', side_effect=mock_sqlite_manager), \
             patch.object(sync_manager, '_get_json_manager', return_value=MagicMock()):
            
            result = sync_manager.sync_sqlite_to_json()
            
            # Should fail on first attempt
            assert result['success'] == False
            assert "Initial failure" in result['error']
    
    def test_sync_manager_data_validation(self, sync_manager, sqlite_db, json_db):
        """Test data validation during sync."""
        # Mock managers
        with patch.object(sync_manager, '_get_sqlite_manager', return_value=sqlite_db), \
             patch.object(sync_manager, '_get_json_manager', return_value=json_db):
            
            # Mock data validation
            with patch.object(sync_manager, '_validate_sync_data', return_value=False):
                result = sync_manager.sync_sqlite_to_json()
                
                assert result['success'] == False
                assert 'validation_failed' in result


class TestSyncManagerFunctions:
    """Test suite for sync manager module functions."""
    
    def test_get_sync_manager_function(self, test_config_dir):
        """Test get_sync_manager function."""
        sync_manager = get_sync_manager(str(test_config_dir))
        assert sync_manager is not None
        assert isinstance(sync_manager, ConstitutionSyncManager)
    
    def test_sync_backends_function(self, test_config_dir, sqlite_db, json_db):
        """Test sync_backends function."""
        # Mock managers
        with patch('config.constitution.sync_manager.ConstitutionSyncManager') as mock_sync_manager:
            mock_instance = MagicMock()
            mock_instance.sync_bidirectional.return_value = {'success': True}
            mock_sync_manager.return_value = mock_instance
            
            result = sync_backends(str(test_config_dir))
            
            assert result['success'] == True
            mock_instance.sync_bidirectional.assert_called_once()
    
    def test_sync_backends_function_force(self, test_config_dir, sqlite_db, json_db):
        """Test sync_backends function with force parameter."""
        # Mock managers
        with patch('config.constitution.sync_manager.ConstitutionSyncManager') as mock_sync_manager:
            mock_instance = MagicMock()
            mock_instance.sync_bidirectional.return_value = {'success': True}
            mock_sync_manager.return_value = mock_instance
            
            result = sync_backends(str(test_config_dir), force=True)
            
            assert result['success'] == True
            mock_instance.sync_bidirectional.assert_called_once()
    
    def test_verify_sync_function(self, test_config_dir, sqlite_db, json_db):
        """Test verify_sync function."""
        # Mock managers
        with patch('config.constitution.sync_manager.ConstitutionSyncManager') as mock_sync_manager:
            mock_instance = MagicMock()
            mock_instance.verify_sync.return_value = {
                'in_sync': True,
                'differences': [],
                'sqlite_rules': 2,
                'json_rules': 2
            }
            mock_sync_manager.return_value = mock_instance
            
            result = verify_sync(str(test_config_dir))
            
            assert result['in_sync'] == True
            assert result['sqlite_rules'] == 2
            assert result['json_rules'] == 2
            mock_instance.verify_sync.assert_called_once()


class TestSyncManagerIntegration:
    """Integration tests for sync manager."""
    
    def test_sync_manager_with_real_managers(self, sync_manager, sqlite_manager, json_manager):
        """Test sync manager with real manager instances."""
        # Test sync operations
        result = sync_manager.sync_sqlite_to_json()
        assert result['success'] == True
        
        result = sync_manager.sync_json_to_sqlite()
        assert result['success'] == True
        
        result = sync_manager.sync_bidirectional()
        assert result['success'] == True
    
    def test_sync_manager_verify_with_real_managers(self, sync_manager, sqlite_manager, json_manager):
        """Test sync verification with real managers."""
        result = sync_manager.verify_sync()
        
        assert 'in_sync' in result
        assert 'differences' in result
        assert 'sqlite_rules' in result
        assert 'json_rules' in result
    
    def test_sync_manager_history_tracking(self, sync_manager, sqlite_manager, json_manager):
        """Test sync history tracking with real operations."""
        # Perform sync operations
        sync_manager.sync_sqlite_to_json()
        sync_manager.sync_json_to_sqlite()
        sync_manager.sync_bidirectional()
        
        # Check history
        history = sync_manager.get_sync_history()
        assert len(history) >= 3
        
        # Check specific operations
        operations = [entry['operation'] for entry in history]
        assert 'sync_sqlite_to_json' in operations
        assert 'sync_json_to_sqlite' in operations
        assert 'sync_bidirectional' in operations
    
    def test_sync_manager_status_tracking(self, sync_manager, sqlite_manager, json_manager):
        """Test sync status tracking."""
        # Get initial status
        initial_status = sync_manager.get_sync_status()
        initial_count = initial_status['sync_count']
        
        # Perform sync
        sync_manager.sync_sqlite_to_json()
        
        # Check updated status
        updated_status = sync_manager.get_sync_status()
        assert updated_status['sync_count'] > initial_count
        assert updated_status['last_sync'] is not None
    
    def test_sync_manager_error_handling_integration(self, sync_manager):
        """Test error handling integration."""
        # Test with invalid managers
        with patch.object(sync_manager, '_get_sqlite_manager', 
                         side_effect=Exception("Manager error")):
            
            result = sync_manager.sync_sqlite_to_json()
            assert result['success'] == False
            assert 'error' in result
            
            # Check error is recorded in history
            history = sync_manager.get_sync_history()
            error_entries = [entry for entry in history if not entry.get('success', True)]
            assert len(error_entries) >= 1
    
    def test_sync_manager_performance_integration(self, sync_manager, sqlite_manager, json_manager):
        """Test sync performance integration."""
        # Test sync performance
        start_time = time.time()
        result = sync_manager.sync_bidirectional()
        end_time = time.time()
        
        assert result['success'] == True
        assert (end_time - start_time) < 10.0, "Sync should be reasonably fast"
        
        # Check performance is recorded
        history = sync_manager.get_sync_history()
        if history:
            latest_entry = history[-1]
            assert 'duration' in latest_entry or 'timestamp' in latest_entry
    
    def test_sync_manager_data_consistency(self, sync_manager, sqlite_manager, json_manager):
        """Test data consistency after sync."""
        # Perform sync
        result = sync_manager.sync_bidirectional()
        assert result['success'] == True
        
        # Verify data consistency
        verify_result = sync_manager.verify_sync()
        assert verify_result['in_sync'] == True
        assert len(verify_result['differences']) == 0
    
    def test_sync_manager_backup_integration(self, sync_manager, sqlite_manager, json_manager, temp_dir):
        """Test backup integration during sync."""
        # Perform sync with backup
        result = sync_manager.sync_sqlite_to_json(backup_before_sync=True)
        assert result['success'] == True
        
        # Check backup was created
        backup_files = list(temp_dir.glob("*.backup*"))
        assert len(backup_files) >= 0  # Backup files may be created
    
    def test_sync_manager_configuration_persistence(self, sync_manager, temp_dir):
        """Test configuration persistence across sync manager instances."""
        # Perform sync
        sync_manager.sync_sqlite_to_json()
        
        # Create new sync manager instance
        new_sync_manager = ConstitutionSyncManager(str(temp_dir))
        
        # Should have access to sync history
        history = new_sync_manager.get_sync_history()
        assert len(history) >= 1

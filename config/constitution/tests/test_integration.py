#!/usr/bin/env python3
"""
End-to-end integration tests for the hybrid constitution database system.

This module tests complete workflows including:
- Full system initialization
- Backend switching and fallback
- Data synchronization
- Migration workflows
- CLI integration
- Error recovery
- Performance under load
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading
import concurrent.futures

from config.constitution.database import ConstitutionRulesDB
from config.constitution.constitution_rules_json import ConstitutionRulesJSON
from config.constitution.config_manager import ConstitutionRuleManager
from config.constitution.config_manager_json import ConstitutionRuleManagerJSON
from config.constitution.backend_factory import ConstitutionBackendFactory
from config.constitution.sync_manager import ConstitutionSyncManager
from config.constitution.migration import ConstitutionMigration


class TestEndToEndIntegration:
    """End-to-end integration tests for the constitution system."""
    
    def test_full_system_initialization(self, temp_dir, mock_constitution_config):
        """Test complete system initialization."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize all components
        sqlite_db = ConstitutionRulesDB(str(temp_dir / "constitution.db"))
        json_db = ConstitutionRulesJSON(str(temp_dir / "constitution.json"))
        sqlite_manager = ConstitutionRuleManager(str(temp_dir), str(temp_dir / "constitution.db"))
        json_manager = ConstitutionRuleManagerJSON(str(temp_dir), str(temp_dir / "constitution.json"))
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        migration_manager = ConstitutionMigration(str(temp_dir))
        
        # Verify all components are working
        assert sqlite_db is not None
        assert json_db is not None
        assert sqlite_manager is not None
        assert json_manager is not None
        assert backend_factory is not None
        assert sync_manager is not None
        assert migration_manager is not None
        
        # Test basic operations
        sqlite_rules = sqlite_manager.get_all_rules()
        json_rules = json_manager.get_all_rules()
        
        assert len(sqlite_rules) >= 0
        assert len(json_rules) >= 0
        
        # Cleanup
        sqlite_db.close()
    
    def test_backend_switching_workflow(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test complete backend switching workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Start with SQLite backend
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Add some test data
        for rule_data in sample_rules_data:
            manager.update_rule_configuration(
                rule_data['rule_number'], 
                enabled=True, 
                reason="Test data"
            )
        
        # Switch to JSON backend
        success = backend_factory.switch_backend("json")
        assert success
        
        # Verify switch
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "json"
        
        # Verify data is accessible
        rules = manager.get_all_rules()
        assert len(rules) >= len(sample_rules_data)
        
        # Switch back to SQLite
        success = backend_factory.switch_backend("sqlite")
        assert success
        
        # Verify switch back
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
    
    def test_data_synchronization_workflow(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test complete data synchronization workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        sqlite_manager = ConstitutionRuleManager(str(temp_dir), str(temp_dir / "constitution.db"))
        json_manager = ConstitutionRuleManagerJSON(str(temp_dir), str(temp_dir / "constitution.json"))
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        
        # Add data to SQLite
        for rule_data in sample_rules_data:
            sqlite_manager.update_rule_configuration(
                rule_data['rule_number'], 
                enabled=True, 
                reason="Test data"
            )
        
        # Sync SQLite to JSON
        result = sync_manager.sync_sqlite_to_json()
        assert result['success'] == True
        
        # Verify data in JSON
        json_rules = json_manager.get_all_rules()
        assert len(json_rules) >= len(sample_rules_data)
        
        # Modify data in JSON
        json_manager.update_rule_configuration(1, enabled=False, reason="Test disable")
        
        # Sync JSON to SQLite
        result = sync_manager.sync_json_to_sqlite()
        assert result['success'] == True
        
        # Verify data in SQLite
        sqlite_rule = sqlite_manager.get_rule_by_number(1)
        assert sqlite_rule is not None
        assert not sqlite_rule['enabled']
        
        # Test bidirectional sync
        result = sync_manager.sync_bidirectional()
        assert result['success'] == True
        
        # Verify sync
        verify_result = sync_manager.verify_sync()
        assert verify_result['in_sync'] == True
    
    def test_migration_workflow(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test complete migration workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        sqlite_manager = ConstitutionRuleManager(str(temp_dir), str(temp_dir / "constitution.db"))
        json_manager = ConstitutionRuleManagerJSON(str(temp_dir), str(temp_dir / "constitution.json"))
        migration_manager = ConstitutionMigration(str(temp_dir))
        
        # Add data to SQLite
        for rule_data in sample_rules_data:
            sqlite_manager.update_rule_configuration(
                rule_data['rule_number'], 
                enabled=True, 
                reason="Test data"
            )
        
        # Migrate SQLite to JSON
        result = migration_manager.migrate_sqlite_to_json()
        assert result['success'] == True
        
        # Verify migration
        verify_result = migration_manager.verify_migration("sqlite_to_json")
        assert verify_result['migration_valid'] == True
        
        # Migrate JSON to SQLite
        result = migration_manager.migrate_json_to_sqlite()
        assert result['success'] == True
        
        # Verify migration
        verify_result = migration_manager.verify_migration("json_to_sqlite")
        assert verify_result['migration_valid'] == True
        
        # Check migration history
        history = migration_manager.get_migration_history()
        assert len(history) >= 2
        
        migration_types = [entry['migration_type'] for entry in history]
        assert 'sqlite_to_json' in migration_types
        assert 'json_to_sqlite' in migration_types
    
    def test_error_recovery_workflow(self, temp_dir, mock_constitution_config):
        """Test complete error recovery workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Test auto-fallback when SQLite fails
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite failed")):
            manager = backend_factory.get_manager("auto")
            assert manager.get_backend_type() == "json"
        
        # Test recovery when SQLite becomes available again
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Test sync error recovery
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        
        with patch.object(sync_manager, '_get_sqlite_manager', 
                         side_effect=Exception("Sync failed")):
            result = sync_manager.sync_sqlite_to_json()
            assert result['success'] == False
            assert 'error' in result
        
        # Test migration error recovery
        migration_manager = ConstitutionMigration(str(temp_dir))
        
        with patch.object(migration_manager, '_get_sqlite_manager', 
                         side_effect=Exception("Migration failed")):
            result = migration_manager.migrate_sqlite_to_json()
            assert result['success'] == False
            assert 'error' in result
    
    def test_performance_under_load(self, temp_dir, mock_constitution_config):
        """Test system performance under load."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        
        def worker(worker_id):
            """Worker function for load testing."""
            try:
                manager = backend_factory.get_manager("auto")
                
                # Perform various operations
                rules = manager.get_all_rules()
                stats = manager.get_rule_statistics()
                
                # Enable/disable rules
                for i in range(10):
                    rule_number = (worker_id * 10 + i) % 149 + 1
                    manager.update_rule_configuration(
                        rule_number, 
                        enabled=(i % 2 == 0), 
                        reason=f"Load test {worker_id}"
                    )
                
                return True
            except Exception as e:
                return False
        
        # Run concurrent workers
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # Verify all workers succeeded
        assert all(results), "Some workers failed"
        
        # Verify performance
        duration = end_time - start_time
        assert duration < 30.0, f"Load test took too long: {duration:.2f} seconds"
    
    def test_data_consistency_under_concurrent_access(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test data consistency under concurrent access."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        sqlite_manager = ConstitutionRuleManager(str(temp_dir), str(temp_dir / "constitution.db"))
        json_manager = ConstitutionRuleManagerJSON(str(temp_dir), str(temp_dir / "constitution.json"))
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        
        # Add initial data
        for rule_data in sample_rules_data:
            sqlite_manager.update_rule_configuration(
                rule_data['rule_number'], 
                enabled=True, 
                reason="Initial data"
            )
        
        def sqlite_worker(worker_id):
            """SQLite worker function."""
            try:
                for i in range(5):
                    rule_number = (worker_id * 5 + i) % len(sample_rules_data) + 1
                    sqlite_manager.update_rule_configuration(
                        rule_number, 
                        enabled=(i % 2 == 0), 
                        reason=f"SQLite worker {worker_id}"
                    )
                    time.sleep(0.01)  # Small delay
                return True
            except Exception as e:
                return False
        
        def json_worker(worker_id):
            """JSON worker function."""
            try:
                for i in range(5):
                    rule_number = (worker_id * 5 + i) % len(sample_rules_data) + 1
                    json_manager.update_rule_configuration(
                        rule_number, 
                        enabled=(i % 2 == 1), 
                        reason=f"JSON worker {worker_id}"
                    )
                    time.sleep(0.01)  # Small delay
                return True
            except Exception as e:
                return False
        
        def sync_worker():
            """Sync worker function."""
            try:
                for i in range(3):
                    sync_manager.sync_bidirectional()
                    time.sleep(0.1)  # Small delay
                return True
            except Exception as e:
                return False
        
        # Run concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # Start workers
            sqlite_futures = [executor.submit(sqlite_worker, i) for i in range(3)]
            json_futures = [executor.submit(json_worker, i) for i in range(3)]
            sync_futures = [executor.submit(sync_worker) for i in range(2)]
            
            # Wait for completion
            sqlite_results = [future.result() for future in sqlite_futures]
            json_results = [future.result() for future in json_futures]
            sync_results = [future.result() for future in sync_futures]
        
        # Verify all workers succeeded
        assert all(sqlite_results), "Some SQLite workers failed"
        assert all(json_results), "Some JSON workers failed"
        assert all(sync_results), "Some sync workers failed"
        
        # Verify final consistency
        verify_result = sync_manager.verify_sync()
        assert verify_result['in_sync'] == True
    
    def test_backup_and_restore_workflow(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test complete backup and restore workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        sqlite_db = ConstitutionRulesDB(str(temp_dir / "constitution.db"))
        json_db = ConstitutionRulesJSON(str(temp_dir / "constitution.json"))
        
        # Add test data
        with sqlite_db.get_connection() as conn:
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
            conn.commit()
        
        # Create backups
        sqlite_backup_path = temp_dir / "sqlite_backup.db"
        json_backup_path = temp_dir / "json_backup.json"
        
        sqlite_backup_success = sqlite_db.backup_database(str(sqlite_backup_path))
        json_backup_success = json_db.backup_database(str(json_backup_path))
        
        assert sqlite_backup_success
        assert json_backup_success
        assert sqlite_backup_path.exists()
        assert json_backup_path.exists()
        
        # Clear original data
        with sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM constitution_rules")
            conn.commit()
        
        json_db.data['rules'] = {}
        json_db._save_database()
        
        # Verify data is cleared
        sqlite_rules = sqlite_db.get_all_rules()
        json_rules = json_db.get_all_rules()
        assert len(sqlite_rules) == 0
        assert len(json_rules) == 0
        
        # Restore from backups
        sqlite_restore_success = sqlite_db.restore_database(str(sqlite_backup_path))
        json_restore_success = json_db.restore_database(str(json_backup_path))
        
        assert sqlite_restore_success
        assert json_restore_success
        
        # Verify data is restored
        sqlite_rules = sqlite_db.get_all_rules()
        json_rules = json_db.get_all_rules()
        assert len(sqlite_rules) >= len(sample_rules_data)
        assert len(json_rules) >= len(sample_rules_data)
        
        sqlite_db.close()
    
    def test_health_monitoring_workflow(self, temp_dir, mock_constitution_config):
        """Test complete health monitoring workflow."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Check health of all backends
        status = backend_factory.get_all_backend_status()
        
        assert 'sqlite' in status
        assert 'json' in status
        assert 'auto' in status
        
        for backend_type, health in status.items():
            assert 'healthy' in health
            assert 'backend_type' in health
            assert health['backend_type'] == backend_type
        
        # Test health check with failing backend
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("Health check failed")):
            health = backend_factory.check_backend_health("sqlite")
            assert health['healthy'] == False
            assert "Health check failed" in health['error']
        
        # Test auto-fallback based on health
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite unhealthy")):
            manager = backend_factory.get_manager("auto")
            assert manager.get_backend_type() == "json"
    
    def test_configuration_management_workflow(self, temp_dir, mock_constitution_config):
        """Test complete configuration management workflow."""
        # Create initial config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize system
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Test configuration loading
        config = backend_factory._load_config()
        assert config['backend'] == "sqlite"
        assert config['fallback_backend'] == "json"
        
        # Test configuration modification
        config['backend'] = "json"
        config['auto_sync'] = False
        
        success = backend_factory._save_config(config)
        assert success
        
        # Verify configuration was saved
        with open(config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        assert saved_config['backend'] == "json"
        assert saved_config['auto_sync'] == False
        
        # Test configuration persistence across instances
        new_backend_factory = ConstitutionBackendFactory(str(temp_dir))
        new_config = new_backend_factory._load_config()
        assert new_config['backend'] == "json"
        assert new_config['auto_sync'] == False
    
    def test_complete_workflow_simulation(self, temp_dir, mock_constitution_config, sample_rules_data):
        """Test complete workflow simulation."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Initialize all components
        backend_factory = ConstitutionBackendFactory(str(temp_dir))
        sync_manager = ConstitutionSyncManager(str(temp_dir))
        migration_manager = ConstitutionMigration(str(temp_dir))
        
        # Step 1: Start with SQLite backend
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Step 2: Add data
        for rule_data in sample_rules_data:
            manager.update_rule_configuration(
                rule_data['rule_number'], 
                enabled=True, 
                reason="Initial setup"
            )
        
        # Step 3: Sync to JSON
        result = sync_manager.sync_sqlite_to_json()
        assert result['success'] == True
        
        # Step 4: Switch to JSON backend
        success = backend_factory.switch_backend("json")
        assert success
        
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "json"
        
        # Step 5: Modify data in JSON
        manager.update_rule_configuration(1, enabled=False, reason="Modified in JSON")
        
        # Step 6: Sync back to SQLite
        result = sync_manager.sync_json_to_sqlite()
        assert result['success'] == True
        
        # Step 7: Switch back to SQLite
        success = backend_factory.switch_backend("sqlite")
        assert success
        
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Step 8: Verify data consistency
        rule = manager.get_rule_by_number(1)
        assert rule is not None
        assert not rule['enabled']
        
        # Step 9: Perform migration
        result = migration_manager.migrate_sqlite_to_json()
        assert result['success'] == True
        
        # Step 10: Verify migration
        verify_result = migration_manager.verify_migration("sqlite_to_json")
        assert verify_result['migration_valid'] == True
        
        # Step 11: Check all histories
        sync_history = sync_manager.get_sync_history()
        migration_history = migration_manager.get_migration_history()
        
        assert len(sync_history) >= 2
        assert len(migration_history) >= 1
        
        # Step 12: Final health check
        status = backend_factory.get_all_backend_status()
        assert status['sqlite']['healthy'] == True
        assert status['json']['healthy'] == True
        
        # Step 13: Verify final sync
        verify_sync_result = sync_manager.verify_sync()
        assert verify_sync_result['in_sync'] == True

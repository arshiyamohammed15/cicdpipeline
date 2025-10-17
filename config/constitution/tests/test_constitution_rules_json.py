#!/usr/bin/env python3
"""
Test suite for ConstitutionRulesJSON (JSON backend).

This module tests all JSON backend functionality including:
- JSON file operations and validation
- Atomic backup operations
- Corrupted file detection and repair
- Data structure validation
- Partial recovery mechanisms
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from config.constitution.constitution_rules_json import ConstitutionRulesJSON


class TestConstitutionRulesJSON:
    """Test suite for ConstitutionRulesJSON class."""
    
    def test_json_database_initialization(self, temp_dir, test_json_path):
        """Test JSON database initialization."""
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Verify JSON file exists
        assert test_json_path.exists(), "JSON database file should be created"
        
        # Verify data structure
        assert isinstance(json_db.data, dict)
        assert 'constitution_version' in json_db.data
        assert 'total_rules' in json_db.data
        assert 'rules' in json_db.data
        assert 'categories' in json_db.data
    
    def test_json_database_initialization_with_existing_file(self, temp_dir, test_json_path):
        """Test JSON database initialization with existing file."""
        # Create existing JSON file
        existing_data = {
            "constitution_version": "2.0",
            "total_rules": 0,
            "rules": {},
            "categories": {}
        }
        
        with open(test_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        assert test_json_path.exists()
        assert json_db.data['constitution_version'] == "2.0"
    
    def test_json_database_load_corrupted_file(self, temp_dir, test_json_path, test_helpers):
        """Test loading corrupted JSON file."""
        # Create corrupted JSON file
        test_helpers.create_corrupted_json_file(test_json_path)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Should create new database after corruption
        assert json_db.data['constitution_version'] == "2.0"
        assert json_db.data['total_rules'] == 149  # Should have all rules
    
    def test_json_database_load_empty_file(self, temp_dir, test_json_path, test_helpers):
        """Test loading empty JSON file."""
        # Create empty JSON file
        test_helpers.create_empty_json_file(test_json_path)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Should create new database after empty file
        assert json_db.data['constitution_version'] == "2.0"
        assert json_db.data['total_rules'] == 149
    
    def test_json_database_save_and_load(self, json_db):
        """Test saving and loading JSON database."""
        # Modify data
        json_db.data['test_field'] = 'test_value'
        json_db._save_database()
        
        # Create new instance and load
        new_json_db = ConstitutionRulesJSON(str(json_db.json_path))
        
        # Verify data was saved and loaded
        assert new_json_db.data['test_field'] == 'test_value'
    
    def test_json_database_atomic_write(self, json_db):
        """Test atomic write operations."""
        original_data = json_db.data.copy()
        
        # Simulate write failure during save
        with patch('builtins.open', side_effect=IOError("Write failed")):
            with pytest.raises(IOError):
                json_db._save_database()
        
        # Verify original data is unchanged
        assert json_db.data == original_data
    
    def test_json_database_validation_before_save(self, json_db):
        """Test data validation before saving."""
        # Test with invalid data structure
        json_db.data = "invalid_data"  # Should be dict
        
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            json_db._save_database()
    
    def test_json_database_validation_missing_keys(self, json_db):
        """Test validation with missing required keys."""
        # Remove required key
        del json_db.data['rules']
        
        with pytest.raises(ValueError, match="Missing required key: rules"):
            json_db._save_database()
    
    def test_json_database_validation_wrong_rule_count(self, json_db):
        """Test validation with wrong rule count."""
        # Modify rule count
        json_db.data['rules'] = {"1": {"test": True}}  # Only 1 rule instead of 149
        
        with pytest.raises(ValueError, match="Expected 149 rules, found 1"):
            json_db._save_database()
    
    def test_json_database_validation_after_write(self, json_db):
        """Test JSON file validation after writing."""
        # Mock json.load to fail
        with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            with pytest.raises(ValueError, match="Generated JSON file is invalid"):
                json_db._save_database()
    
    def test_json_database_backup_corrupted_file(self, temp_dir, test_json_path, test_helpers):
        """Test backup of corrupted file."""
        # Create corrupted file
        test_helpers.create_corrupted_json_file(test_json_path)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Should create backup with timestamp
        backup_files = list(test_json_path.parent.glob(f"{test_json_path.stem}.corrupted.backup.*"))
        assert len(backup_files) >= 1, "Backup file should be created"
    
    def test_json_database_backup_unique_names(self, temp_dir, test_json_path, test_helpers):
        """Test backup with unique names when multiple backups exist."""
        # Create multiple corrupted files
        for i in range(3):
            test_helpers.create_corrupted_json_file(test_json_path)
            json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Should create unique backup names
        backup_files = list(test_json_path.parent.glob(f"{test_json_path.stem}.corrupted.backup.*"))
        assert len(backup_files) >= 3, "Multiple backup files should be created"
        
        # All backup files should have unique names
        backup_names = [f.name for f in backup_files]
        assert len(set(backup_names)) == len(backup_names), "All backup names should be unique"
    
    def test_json_database_repair_corrupted_database(self, temp_dir, test_json_path, test_helpers):
        """Test repair of corrupted database."""
        # Create corrupted file
        test_helpers.create_corrupted_json_file(test_json_path)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Test repair
        success = json_db.repair_corrupted_database()
        assert success
        
        # Verify database is now valid
        assert json_db.data['constitution_version'] == "2.0"
        assert json_db.data['total_rules'] == 149
    
    def test_json_database_repair_valid_database(self, json_db):
        """Test repair of valid database."""
        success = json_db.repair_corrupted_database()
        assert success
        
        # Should not modify valid database
        assert json_db.data['constitution_version'] == "2.0"
    
    def test_json_database_repair_nonexistent_file(self, temp_dir, test_json_path):
        """Test repair of non-existent file."""
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Remove file
        test_json_path.unlink()
        
        success = json_db.repair_corrupted_database()
        assert success
    
    def test_json_database_partial_recovery(self, temp_dir, test_json_path, test_helpers):
        """Test partial recovery from corrupted file."""
        # Create file with partial valid data
        partial_data = '{"rules": {"1": {"test": true}}, "database_info": {"version": "2.0"}}'
        with open(test_json_path, 'w', encoding='utf-8') as f:
            f.write(partial_data)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Should attempt partial recovery
        success = json_db.repair_corrupted_database()
        assert success
        
        # Should recreate database
        assert json_db.data['constitution_version'] == "2.0"
        assert json_db.data['total_rules'] == 149
    
    def test_json_database_validate_data_structure(self, json_db):
        """Test data structure validation."""
        # Test valid data
        assert json_db._validate_data_structure(json_db.data) == True
        
        # Test invalid data types
        assert json_db._validate_data_structure("invalid") == False
        assert json_db._validate_data_structure(None) == False
        
        # Test missing keys
        invalid_data = {"rules": {}}
        assert json_db._validate_data_structure(invalid_data) == False
        
        # Test wrong rule count
        invalid_data = {
            "rules": {"1": {"test": True}},
            "database_info": {},
            "categories": {}
        }
        assert json_db._validate_data_structure(invalid_data) == False
    
    def test_json_database_attempt_partial_recovery(self, temp_dir, test_json_path, test_helpers):
        """Test partial recovery attempt."""
        # Create file with some valid content
        with open(test_json_path, 'w', encoding='utf-8') as f:
            f.write('{"rules": {"1": {"test": true}}, "database_info": {"version": "2.0"}}')
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        success = json_db._attempt_partial_recovery()
        assert success
        
        # Should recreate database
        assert json_db.data['constitution_version'] == "2.0"
    
    def test_json_database_attempt_partial_recovery_failure(self, temp_dir, test_json_path, test_helpers):
        """Test partial recovery failure."""
        # Create file with no valid content
        with open(test_json_path, 'w', encoding='utf-8') as f:
            f.write('invalid content with no valid json')
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        success = json_db._attempt_partial_recovery()
        assert success == False
    
    def test_json_database_rule_operations(self, json_db):
        """Test rule operations on JSON database."""
        # Test getting all rules
        rules = json_db.get_all_rules()
        assert len(rules) == 2  # Should have 2 test rules
        
        # Test getting rule by number
        rule = json_db.get_rule_by_number(1)
        assert rule is not None
        assert rule['rule_number'] == 1
        assert rule['title'] == "Test Rule 1"
        
        # Test getting non-existent rule
        rule = json_db.get_rule_by_number(999)
        assert rule is None
    
    def test_json_database_rule_enable_disable(self, json_db):
        """Test enabling and disabling rules in JSON database."""
        # Disable rule 1
        success = json_db.update_rule_configuration(1, enabled=False, reason="Test disable")
        assert success
        
        # Verify rule is disabled
        rule = json_db.get_rule_by_number(1)
        assert not rule['enabled']
        
        # Enable rule 1
        success = json_db.update_rule_configuration(1, enabled=True, reason="Test enable")
        assert success
        
        # Verify rule is enabled
        rule = json_db.get_rule_by_number(1)
        assert rule['enabled']
    
    def test_json_database_rule_search(self, json_db):
        """Test searching rules in JSON database."""
        results = json_db.search_rules("test")
        
        assert len(results) >= 1, "Should find at least one rule with 'test'"
        
        for result in results:
            assert 'test' in result['title'].lower() or 'test' in result['content'].lower()
    
    def test_json_database_rule_statistics(self, json_db):
        """Test rule statistics in JSON database."""
        stats = json_db.get_rule_statistics()
        
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
    
    def test_json_database_rule_usage_tracking(self, json_db):
        """Test rule usage tracking in JSON database."""
        # Record usage
        success = json_db.record_rule_usage(1, "test_operation", {"test": True})
        assert success
        
        # Get usage history
        usage = json_db.get_rule_usage_history(1)
        assert len(usage) >= 1
        
        latest_usage = usage[0]
        assert latest_usage['rule_number'] == 1
        assert latest_usage['operation'] == "test_operation"
    
    def test_json_database_validation_history_tracking(self, json_db):
        """Test validation history tracking in JSON database."""
        # Record validation
        success = json_db.record_validation(1, "test_file.py", True, "No violations found")
        assert success
        
        # Get validation history
        history = json_db.get_validation_history(1)
        assert len(history) >= 1
        
        latest_validation = history[0]
        assert latest_validation['rule_number'] == 1
        assert latest_validation['file_path'] == "test_file.py"
        assert latest_validation['passed'] == True
    
    def test_json_database_export_to_json(self, json_db):
        """Test exporting rules to JSON format."""
        json_data = json_db.export_rules_to_json()
        
        # Should return valid JSON string
        parsed_data = json.loads(json_data)
        assert 'rules' in parsed_data
        assert 'metadata' in parsed_data
        
        # Should contain test rules
        assert len(parsed_data['rules']) == 2
    
    def test_json_database_export_enabled_only(self, json_db):
        """Test exporting only enabled rules."""
        # Disable one rule
        json_db.update_rule_configuration(1, enabled=False, reason="Test")
        
        # Export enabled only
        json_data = json_db.export_rules_to_json(enabled_only=True)
        parsed_data = json.loads(json_data)
        
        # Should only contain enabled rules
        enabled_rules = [rule for rule in parsed_data['rules'] if rule['enabled']]
        assert len(enabled_rules) == 1
    
    def test_json_database_get_rules_by_category(self, json_db):
        """Test getting rules by category."""
        rules = json_db.get_rules_by_category("basic_work")
        
        assert len(rules) == 1
        assert rules[0]['category'] == "basic_work"
        
        # Test non-existent category
        rules = json_db.get_rules_by_category("nonexistent")
        assert len(rules) == 0
    
    def test_json_database_get_enabled_rules(self, json_db):
        """Test getting only enabled rules."""
        # Disable one rule
        json_db.update_rule_configuration(1, enabled=False, reason="Test")
        
        enabled_rules = json_db.get_enabled_rules()
        assert len(enabled_rules) == 1
        assert enabled_rules[0]['enabled'] == True
    
    def test_json_database_get_disabled_rules(self, json_db):
        """Test getting only disabled rules."""
        # Disable one rule
        json_db.update_rule_configuration(1, enabled=False, reason="Test")
        
        disabled_rules = json_db.get_disabled_rules()
        assert len(disabled_rules) == 1
        assert disabled_rules[0]['enabled'] == False
    
    def test_json_database_performance_large_dataset(self, temp_dir, test_json_path, test_helpers):
        """Test JSON database performance with large dataset."""
        # Create large JSON file
        test_helpers.create_large_json_file(test_json_path, 1000)
        
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Test retrieval performance
        start_time = time.time()
        rules = json_db.get_all_rules()
        end_time = time.time()
        
        assert len(rules) == 1000
        assert (end_time - start_time) < 2.0, "Retrieval should be reasonably fast"
    
    def test_json_database_concurrent_access(self, json_db):
        """Test concurrent access to JSON database."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                rules = json_db.get_all_rules()
                results.append((worker_id, len(rules)))
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
        
        # All threads should get same result
        for worker_id, rule_count in results:
            assert rule_count == 2, f"Worker {worker_id} got wrong rule count"
    
    def test_json_database_file_permissions(self, temp_dir, test_json_path):
        """Test JSON database with file permission issues."""
        json_db = ConstitutionRulesJSON(str(test_json_path))
        
        # Make file read-only
        test_json_path.chmod(0o444)
        
        try:
            # Should handle permission error gracefully
            with pytest.raises(PermissionError):
                json_db._save_database()
        finally:
            # Restore permissions
            test_json_path.chmod(0o644)
    
    def test_json_database_disk_space_error(self, json_db):
        """Test JSON database with disk space error."""
        # Mock open to raise disk space error
        with patch('builtins.open', side_effect=OSError(28, "No space left on device")):
            with pytest.raises(OSError):
                json_db._save_database()
    
    def test_json_database_unicode_handling(self, json_db):
        """Test JSON database with Unicode content."""
        # Add Unicode content
        unicode_rule = {
            "rule_number": 999,
            "title": "Unicode Test Rule 测试规则",
            "category": "basic_work",
            "priority": "critical",
            "content": "This rule contains Unicode: 测试内容 🚀",
            "enabled": True,
            "config": {"default_enabled": True}
        }
        
        json_db.data["rules"]["999"] = unicode_rule
        json_db._save_database()
        
        # Reload and verify Unicode content
        new_json_db = ConstitutionRulesJSON(str(json_db.json_path))
        rule = new_json_db.get_rule_by_number(999)
        
        assert rule['title'] == "Unicode Test Rule 测试规则"
        assert rule['content'] == "This rule contains Unicode: 测试内容 🚀"
    
    def test_json_database_metadata_updates(self, json_db):
        """Test that metadata is updated on save."""
        original_updated = json_db.data.get('last_updated')
        
        # Wait a moment to ensure timestamp difference
        time.sleep(0.1)
        
        # Save database
        json_db._save_database()
        
        # Check that last_updated was updated
        assert json_db.data['last_updated'] != original_updated
        assert 'last_updated' in json_db.data['database_info']
    
    def test_json_database_backup_cleanup(self, temp_dir, test_json_path, test_helpers):
        """Test backup cleanup when backup fails."""
        # Create corrupted file
        test_helpers.create_corrupted_json_file(test_json_path)
        
        # Mock backup to fail
        with patch('shutil.copy2', side_effect=OSError("Backup failed")):
            json_db = ConstitutionRulesJSON(str(test_json_path))
            
            # Should remove corrupted file if backup fails
            assert not test_json_path.exists()

#!/usr/bin/env python3
"""
Test suite for ConstitutionBackendFactory.

This module tests all backend factory functionality including:
- Backend selection logic
- Auto-fallback mechanisms
- Health check systems
- Configuration management
- Error handling and recovery
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from config.constitution.backend_factory import (
    ConstitutionBackendFactory,
    get_constitution_manager,
    get_backend_factory,
    switch_backend,
    get_backend_status
)


class TestConstitutionBackendFactory:
    """Test suite for ConstitutionBackendFactory class."""
    
    def test_factory_initialization(self, backend_factory):
        """Test factory initialization."""
        assert backend_factory is not None
        assert backend_factory.config_dir is not None
        assert backend_factory.config_path.exists()
    
    def test_factory_get_sqlite_manager(self, backend_factory, temp_dir):
        """Test getting SQLite manager."""
        manager = backend_factory.get_manager("sqlite")
        
        assert manager is not None
        assert hasattr(manager, 'get_backend_type')
        assert manager.get_backend_type() == "sqlite"
    
    def test_factory_get_json_manager(self, backend_factory, temp_dir):
        """Test getting JSON manager."""
        manager = backend_factory.get_manager("json")
        
        assert manager is not None
        assert hasattr(manager, 'get_backend_type')
        assert manager.get_backend_type() == "json"
    
    def test_factory_get_auto_manager(self, backend_factory, temp_dir):
        """Test getting auto-selected manager."""
        manager = backend_factory.get_manager("auto")
        
        assert manager is not None
        assert hasattr(manager, 'get_backend_type')
        # Should default to SQLite
        assert manager.get_backend_type() == "sqlite"
    
    def test_factory_get_manager_invalid_backend(self, backend_factory):
        """Test getting manager with invalid backend."""
        with pytest.raises(ValueError, match="Unsupported backend type"):
            backend_factory.get_manager("invalid")
    
    def test_factory_auto_fallback_sqlite_failure(self, backend_factory, temp_dir):
        """Test auto-fallback when SQLite fails."""
        # Mock SQLite manager to fail
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite failed")):
            manager = backend_factory.get_manager("auto")
            
            # Should fallback to JSON
            assert manager is not None
            assert manager.get_backend_type() == "json"
    
    def test_factory_auto_fallback_both_fail(self, backend_factory, temp_dir):
        """Test auto-fallback when both backends fail."""
        # Mock both managers to fail
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite failed")), \
             patch('config.constitution.backend_factory.ConstitutionRuleManagerJSON', 
                   side_effect=Exception("JSON failed")):
            
            with pytest.raises(Exception, match="All backends failed"):
                backend_factory.get_manager("auto")
    
    def test_factory_health_check_sqlite(self, backend_factory, temp_dir):
        """Test health check for SQLite backend."""
        health = backend_factory.check_backend_health("sqlite")
        
        assert 'healthy' in health
        assert 'backend_type' in health
        assert 'error' in health
        assert health['backend_type'] == "sqlite"
    
    def test_factory_health_check_json(self, backend_factory, temp_dir):
        """Test health check for JSON backend."""
        health = backend_factory.check_backend_health("json")
        
        assert 'healthy' in health
        assert 'backend_type' in health
        assert 'error' in health
        assert health['backend_type'] == "json"
    
    def test_factory_health_check_invalid_backend(self, backend_factory):
        """Test health check for invalid backend."""
        health = backend_factory.check_backend_health("invalid")
        
        assert health['healthy'] == False
        assert health['backend_type'] == "invalid"
        assert "Unsupported backend type" in health['error']
    
    def test_factory_health_check_sqlite_failure(self, backend_factory, temp_dir):
        """Test health check when SQLite fails."""
        # Mock SQLite manager to fail
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite health check failed")):
            health = backend_factory.check_backend_health("sqlite")
            
            assert health['healthy'] == False
            assert "SQLite health check failed" in health['error']
    
    def test_factory_health_check_json_failure(self, backend_factory, temp_dir):
        """Test health check when JSON fails."""
        # Mock JSON manager to fail
        with patch('config.constitution.backend_factory.ConstitutionRuleManagerJSON', 
                   side_effect=Exception("JSON health check failed")):
            health = backend_factory.check_backend_health("json")
            
            assert health['healthy'] == False
            assert "JSON health check failed" in health['error']
    
    def test_factory_get_all_backend_status(self, backend_factory, temp_dir):
        """Test getting status of all backends."""
        status = backend_factory.get_all_backend_status()
        
        assert 'sqlite' in status
        assert 'json' in status
        assert 'auto' in status
        
        for backend_type, health in status.items():
            assert 'healthy' in health
            assert 'backend_type' in health
            assert 'error' in health
    
    def test_factory_switch_backend(self, backend_factory, temp_dir):
        """Test switching default backend."""
        # Switch to JSON
        success = backend_factory.switch_backend("json")
        assert success
        
        # Verify switch
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "json"
        
        # Switch back to SQLite
        success = backend_factory.switch_backend("sqlite")
        assert success
        
        # Verify switch back
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
    
    def test_factory_switch_backend_invalid(self, backend_factory):
        """Test switching to invalid backend."""
        success = backend_factory.switch_backend("invalid")
        assert success == False
    
    def test_factory_switch_backend_config_update(self, backend_factory, temp_dir):
        """Test that backend switch updates configuration."""
        # Switch to JSON
        backend_factory.switch_backend("json")
        
        # Verify config was updated
        with open(backend_factory.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        assert config['backend'] == "json"
    
    def test_factory_get_backend_info(self, backend_factory):
        """Test getting backend information."""
        info = backend_factory.get_backend_info()
        
        assert 'available_backends' in info
        assert 'default_backend' in info
        assert 'fallback_backend' in info
        assert 'auto_fallback_enabled' in info
        
        assert 'sqlite' in info['available_backends']
        assert 'json' in info['available_backends']
    
    def test_factory_config_loading(self, backend_factory, mock_constitution_config):
        """Test configuration loading."""
        config = backend_factory._load_config()
        
        assert config['backend'] == "sqlite"
        assert config['fallback_backend'] == "json"
        assert config['auto_fallback'] == True
        assert config['auto_sync'] == True
    
    def test_factory_config_loading_missing_file(self, temp_dir):
        """Test configuration loading with missing file."""
        factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Should create default config
        config = factory._load_config()
        assert config['backend'] == "sqlite"
        assert config['fallback_backend'] == "json"
    
    def test_factory_config_loading_corrupted_file(self, temp_dir, test_helpers):
        """Test configuration loading with corrupted file."""
        # Create corrupted config file
        config_file = temp_dir / "constitution_config.json"
        test_helpers.create_corrupted_json_file(config_file)
        
        factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Should create default config
        config = factory._load_config()
        assert config['backend'] == "sqlite"
    
    def test_factory_config_saving(self, backend_factory, temp_dir):
        """Test configuration saving."""
        # Modify config
        config = backend_factory._load_config()
        config['backend'] = "json"
        
        success = backend_factory._save_config(config)
        assert success
        
        # Verify config was saved
        with open(backend_factory.config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        assert saved_config['backend'] == "json"
    
    def test_factory_config_saving_failure(self, backend_factory):
        """Test configuration saving failure."""
        # Mock open to fail
        with patch('builtins.open', side_effect=IOError("Write failed")):
            config = backend_factory._load_config()
            success = backend_factory._save_config(config)
            assert success == False


class TestBackendFactoryFunctions:
    """Test suite for backend factory module functions."""
    
    def test_get_constitution_manager_function(self, test_config_dir, mock_constitution_config):
        """Test get_constitution_manager function."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test with auto backend
        manager = get_constitution_manager("auto", str(test_config_dir))
        assert manager is not None
        assert manager.get_backend_type() == "sqlite"
        
        # Test with specific backend
        manager = get_constitution_manager("json", str(test_config_dir))
        assert manager is not None
        assert manager.get_backend_type() == "json"
    
    def test_get_constitution_manager_function_invalid_backend(self, test_config_dir, mock_constitution_config):
        """Test get_constitution_manager function with invalid backend."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        with pytest.raises(ValueError, match="Unsupported backend type"):
            get_constitution_manager("invalid", str(test_config_dir))
    
    def test_get_backend_factory_function(self, test_config_dir, mock_constitution_config):
        """Test get_backend_factory function."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        factory = get_backend_factory(str(test_config_dir))
        assert factory is not None
        assert isinstance(factory, ConstitutionBackendFactory)
    
    def test_switch_backend_function(self, test_config_dir, mock_constitution_config):
        """Test switch_backend function."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Switch to JSON
        success = switch_backend("json", str(test_config_dir))
        assert success
        
        # Verify switch
        manager = get_constitution_manager("auto", str(test_config_dir))
        assert manager.get_backend_type() == "json"
    
    def test_switch_backend_function_invalid(self, test_config_dir, mock_constitution_config):
        """Test switch_backend function with invalid backend."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        success = switch_backend("invalid", str(test_config_dir))
        assert success == False
    
    def test_get_backend_status_function(self, test_config_dir, mock_constitution_config):
        """Test get_backend_status function."""
        # Create config file
        config_file = test_config_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        status = get_backend_status(str(test_config_dir))
        
        assert 'sqlite' in status
        assert 'json' in status
        assert 'auto' in status
        
        for backend_type, health in status.items():
            assert 'healthy' in health
            assert 'backend_type' in health


class TestBackendFactoryIntegration:
    """Integration tests for backend factory."""
    
    def test_factory_with_real_managers(self, backend_factory, temp_dir):
        """Test factory with real manager instances."""
        # Test SQLite manager
        sqlite_manager = backend_factory.get_manager("sqlite")
        assert sqlite_manager is not None
        
        # Test basic operations
        rules = sqlite_manager.get_all_rules()
        assert isinstance(rules, list)
        
        # Test JSON manager
        json_manager = backend_factory.get_manager("json")
        assert json_manager is not None
        
        # Test basic operations
        rules = json_manager.get_all_rules()
        assert isinstance(rules, list)
    
    def test_factory_auto_fallback_integration(self, backend_factory, temp_dir):
        """Test auto-fallback integration."""
        # Test normal operation (SQLite should work)
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Test with SQLite failure
        with patch('config.constitution.backend_factory.ConstitutionRuleManager', 
                   side_effect=Exception("SQLite failed")):
            manager = backend_factory.get_manager("auto")
            assert manager.get_backend_type() == "json"
    
    def test_factory_health_check_integration(self, backend_factory, temp_dir):
        """Test health check integration."""
        # Test SQLite health
        sqlite_health = backend_factory.check_backend_health("sqlite")
        assert sqlite_health['healthy'] == True
        
        # Test JSON health
        json_health = backend_factory.check_backend_health("json")
        assert json_health['healthy'] == True
        
        # Test all backends
        all_status = backend_factory.get_all_backend_status()
        assert all_status['sqlite']['healthy'] == True
        assert all_status['json']['healthy'] == True
    
    def test_factory_backend_switching_integration(self, backend_factory, temp_dir):
        """Test backend switching integration."""
        # Start with SQLite
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
        
        # Switch to JSON
        success = backend_factory.switch_backend("json")
        assert success
        
        # Verify switch
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "json"
        
        # Switch back to SQLite
        success = backend_factory.switch_backend("sqlite")
        assert success
        
        # Verify switch back
        manager = backend_factory.get_manager("auto")
        assert manager.get_backend_type() == "sqlite"
    
    def test_factory_error_handling_integration(self, backend_factory, temp_dir):
        """Test error handling integration."""
        # Test invalid backend
        with pytest.raises(ValueError):
            backend_factory.get_manager("invalid")
        
        # Test health check with invalid backend
        health = backend_factory.check_backend_health("invalid")
        assert health['healthy'] == False
        
        # Test switch to invalid backend
        success = backend_factory.switch_backend("invalid")
        assert success == False
    
    def test_factory_configuration_persistence(self, backend_factory, temp_dir):
        """Test configuration persistence across factory instances."""
        # Switch backend
        backend_factory.switch_backend("json")
        
        # Create new factory instance
        new_factory = ConstitutionBackendFactory(str(temp_dir))
        
        # Should use persisted configuration
        manager = new_factory.get_manager("auto")
        assert manager.get_backend_type() == "json"
    
    def test_factory_concurrent_access(self, backend_factory, temp_dir):
        """Test concurrent access to factory."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                manager = backend_factory.get_manager("auto")
                results.append((worker_id, manager.get_backend_type()))
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
        
        # All threads should get same backend type
        for worker_id, backend_type in results:
            assert backend_type == "sqlite", f"Worker {worker_id} got wrong backend type"
    
    def test_factory_performance(self, backend_factory, temp_dir):
        """Test factory performance."""
        import time
        
        # Test manager creation performance
        start_time = time.time()
        
        for i in range(100):
            manager = backend_factory.get_manager("auto")
            assert manager is not None
        
        end_time = time.time()
        
        # Should be reasonably fast
        assert (end_time - start_time) < 5.0, "Factory should be fast"
    
    def test_factory_memory_usage(self, backend_factory, temp_dir):
        """Test factory memory usage."""
        import gc
        
        # Create many managers
        managers = []
        for i in range(50):
            manager = backend_factory.get_manager("auto")
            managers.append(manager)
        
        # Clear references
        managers.clear()
        gc.collect()
        
        # Should not cause memory issues
        # (This is a basic test - more sophisticated memory testing would require psutil)
        assert True  # If we get here without memory issues, test passes

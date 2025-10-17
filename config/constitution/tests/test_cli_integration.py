#!/usr/bin/env python3
"""
Test suite for CLI integration with constitution database system.

This module tests all CLI functionality including:
- Unicode encoding fixes
- Backend management commands
- Error handling improvements
- Safe printing functions
- Command line argument parsing
"""

import pytest
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import io
import contextlib

# Add the project root to the path
import sys
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from enhanced_cli import (
    safe_print,
    sanitize_unicode,
    main,
    ConstitutionCLI
)


class TestCLIUnicodeHandling:
    """Test suite for CLI Unicode handling."""
    
    def test_safe_print_unicode_success(self):
        """Test safe_print with Unicode characters."""
        # Test with Unicode characters
        unicode_text = "Test with Unicode: 测试内容 🚀"
        
        # Capture output
        with io.StringIO() as captured_output:
            safe_print(unicode_text, file=captured_output)
            output = captured_output.getvalue()
        
        assert "Test with Unicode: 测试内容 🚀" in output
    
    def test_safe_print_unicode_fallback(self):
        """Test safe_print with Unicode fallback."""
        # Mock UnicodeEncodeError
        with patch('builtins.print', side_effect=UnicodeEncodeError('ascii', 'test', 0, 1, 'error')):
            # Should not raise exception
            safe_print("Test with Unicode: 测试内容 🚀")
    
    def test_sanitize_unicode(self):
        """Test Unicode sanitization."""
        # Test various Unicode characters
        test_cases = [
            ("Test–with–en–dash", "Test-with-en-dash"),
            ("Test—with—em—dash", "Test--with--em--dash"),
            ("Test'with'quotes", "Test'with'quotes"),
            ("Test"with"quotes", "Test\"with\"quotes"),
            ("Test…with…ellipsis", "Test...with...ellipsis"),
            ("Test→with→arrow", "Test->with->arrow"),
            ("Test✓with✓check", "Test[OK]with[OK]check"),
            ("Test✗with✗cross", "Test[X]with[X]cross"),
            ("Test with non-breaking space", "Test with non-breaking space"),
        ]
        
        for input_text, expected_output in test_cases:
            result = sanitize_unicode(input_text)
            assert result == expected_output, f"Failed for input: {input_text}"
    
    def test_sanitize_unicode_empty_string(self):
        """Test sanitize_unicode with empty string."""
        result = sanitize_unicode("")
        assert result == ""
    
    def test_sanitize_unicode_none(self):
        """Test sanitize_unicode with None."""
        result = sanitize_unicode(None)
        assert result is None


class TestCLIBackendManagement:
    """Test suite for CLI backend management."""
    
    def test_cli_backend_status_command(self, temp_dir, mock_constitution_config):
        """Test CLI backend status command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the constitution manager
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_backend_type.return_value = "sqlite"
            mock_manager.health_check.return_value = {
                'healthy': True,
                'database_exists': True,
                'database_readable': True,
                'database_writable': True,
                'data_valid': True
            }
            mock_get_manager.return_value = mock_manager
            
            # Test backend status
            result = cli._show_backend_status()
            assert result is not None
    
    def test_cli_switch_backend_command(self, temp_dir, mock_constitution_config):
        """Test CLI switch backend command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the backend factory
        with patch('enhanced_cli.ConstitutionCLI._get_backend_factory') as mock_get_factory:
            mock_factory = MagicMock()
            mock_factory.switch_backend.return_value = True
            mock_get_factory.return_value = mock_factory
            
            # Test switch backend
            result = cli._switch_backend("json")
            assert result is not None
    
    def test_cli_sync_backends_command(self, temp_dir, mock_constitution_config):
        """Test CLI sync backends command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the sync manager
        with patch('enhanced_cli.ConstitutionCLI._get_sync_manager') as mock_get_sync:
            mock_sync = MagicMock()
            mock_sync.sync_bidirectional.return_value = {
                'success': True,
                'sqlite_to_json': {'success': True, 'rules_synced': 5},
                'json_to_sqlite': {'success': True, 'rules_synced': 3}
            }
            mock_get_sync.return_value = mock_sync
            
            # Test sync backends
            result = cli._sync_backends()
            assert result is not None
    
    def test_cli_migrate_backends_command(self, temp_dir, mock_constitution_config):
        """Test CLI migrate backends command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the migration manager
        with patch('enhanced_cli.ConstitutionCLI._get_migration_manager') as mock_get_migration:
            mock_migration = MagicMock()
            mock_migration.migrate_sqlite_to_json.return_value = {
                'success': True,
                'rules_migrated': 149
            }
            mock_get_migration.return_value = mock_migration
            
            # Test migrate backends
            result = cli._migrate_backends("sqlite-to-json")
            assert result is not None
    
    def test_cli_verify_sync_command(self, temp_dir, mock_constitution_config):
        """Test CLI verify sync command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the sync manager
        with patch('enhanced_cli.ConstitutionCLI._get_sync_manager') as mock_get_sync:
            mock_sync = MagicMock()
            mock_sync.verify_sync.return_value = {
                'in_sync': True,
                'differences': [],
                'sqlite_rules': 149,
                'json_rules': 149
            }
            mock_get_sync.return_value = mock_sync
            
            # Test verify sync
            result = cli._verify_sync()
            assert result is not None
    
    def test_cli_repair_sync_command(self, temp_dir, mock_constitution_config):
        """Test CLI repair sync command."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test CLI command
        cli = ConstitutionCLI()
        
        # Mock the migration manager
        with patch('enhanced_cli.ConstitutionCLI._get_migration_manager') as mock_get_migration:
            mock_migration = MagicMock()
            mock_migration.repair_sync.return_value = {
                'success': True,
                'repairs_performed': 3
            }
            mock_get_migration.return_value = mock_migration
            
            # Test repair sync
            result = cli._repair_sync()
            assert result is not None


class TestCLIErrorHandling:
    """Test suite for CLI error handling."""
    
    def test_cli_handle_constitution_commands_error(self, temp_dir):
        """Test CLI error handling in constitution commands."""
        cli = ConstitutionCLI()
        
        # Mock constitution manager to fail
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager', 
                   side_effect=Exception("Constitution manager failed")):
            
            # Should handle error gracefully
            result = cli._handle_constitution_commands(["list-rules"])
            assert result is not None
    
    def test_cli_handle_backend_commands_error(self, temp_dir):
        """Test CLI error handling in backend commands."""
        cli = ConstitutionCLI()
        
        # Mock backend factory to fail
        with patch('enhanced_cli.ConstitutionCLI._get_backend_factory', 
                   side_effect=Exception("Backend factory failed")):
            
            # Should handle error gracefully
            result = cli._handle_backend_commands(["backend-status"])
            assert result is not None
    
    def test_cli_list_rules_error(self, temp_dir):
        """Test CLI list rules error handling."""
        cli = ConstitutionCLI()
        
        # Mock constitution manager to fail
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_all_rules.side_effect = Exception("Database error")
            mock_get_manager.return_value = mock_manager
            
            # Should handle error gracefully
            result = cli._list_rules()
            assert result is not None
    
    def test_cli_export_rules_error(self, temp_dir):
        """Test CLI export rules error handling."""
        cli = ConstitutionCLI()
        
        # Mock constitution manager to fail
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.export_rules_to_json.side_effect = Exception("Export error")
            mock_get_manager.return_value = mock_manager
            
            # Should handle error gracefully
            result = cli._export_rules("test_export.json")
            assert result is not None
    
    def test_cli_search_rules_error(self, temp_dir):
        """Test CLI search rules error handling."""
        cli = ConstitutionCLI()
        
        # Mock constitution manager to fail
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.search_rules.side_effect = Exception("Search error")
            mock_get_manager.return_value = mock_manager
            
            # Should handle error gracefully
            result = cli._search_rules("test")
            assert result is not None


class TestCLIArgumentParsing:
    """Test suite for CLI argument parsing."""
    
    def test_cli_parse_arguments_basic(self):
        """Test basic CLI argument parsing."""
        cli = ConstitutionCLI()
        
        # Test basic arguments
        args = cli._parse_arguments(["--rule-stats"])
        assert args.rule_stats == True
    
    def test_cli_parse_arguments_backend(self):
        """Test CLI argument parsing with backend."""
        cli = ConstitutionCLI()
        
        # Test backend argument
        args = cli._parse_arguments(["--backend", "json"])
        assert args.backend == "json"
    
    def test_cli_parse_arguments_switch_backend(self):
        """Test CLI argument parsing with switch backend."""
        cli = ConstitutionCLI()
        
        # Test switch backend argument
        args = cli._parse_arguments(["--switch-backend", "json"])
        assert args.switch_backend == "json"
    
    def test_cli_parse_arguments_sync_backends(self):
        """Test CLI argument parsing with sync backends."""
        cli = ConstitutionCLI()
        
        # Test sync backends argument
        args = cli._parse_arguments(["--sync-backends"])
        assert args.sync_backends == True
    
    def test_cli_parse_arguments_migrate(self):
        """Test CLI argument parsing with migrate."""
        cli = ConstitutionCLI()
        
        # Test migrate argument
        args = cli._parse_arguments(["--migrate", "sqlite-to-json"])
        assert args.migrate == "sqlite-to-json"
    
    def test_cli_parse_arguments_verify_sync(self):
        """Test CLI argument parsing with verify sync."""
        cli = ConstitutionCLI()
        
        # Test verify sync argument
        args = cli._parse_arguments(["--verify-sync"])
        assert args.verify_sync == True
    
    def test_cli_parse_arguments_backend_status(self):
        """Test CLI argument parsing with backend status."""
        cli = ConstitutionCLI()
        
        # Test backend status argument
        args = cli._parse_arguments(["--backend-status"])
        assert args.backend_status == True
    
    def test_cli_parse_arguments_repair_sync(self):
        """Test CLI argument parsing with repair sync."""
        cli = ConstitutionCLI()
        
        # Test repair sync argument
        args = cli._parse_arguments(["--repair-sync"])
        assert args.repair_sync == True
    
    def test_cli_parse_arguments_invalid(self):
        """Test CLI argument parsing with invalid arguments."""
        cli = ConstitutionCLI()
        
        # Test invalid arguments
        with pytest.raises(SystemExit):
            cli._parse_arguments(["--invalid-argument"])


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def test_cli_main_function(self, temp_dir, mock_constitution_config):
        """Test CLI main function."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Mock all dependencies
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager, \
             patch('enhanced_cli.ConstitutionCLI._get_backend_factory') as mock_get_factory, \
             patch('enhanced_cli.ConstitutionCLI._get_sync_manager') as mock_get_sync, \
             patch('enhanced_cli.ConstitutionCLI._get_migration_manager') as mock_get_migration:
            
            # Mock managers
            mock_manager = MagicMock()
            mock_manager.get_all_rules.return_value = []
            mock_manager.get_rule_statistics.return_value = {
                'total_rules': 149,
                'enabled_rules': 149,
                'disabled_rules': 0
            }
            mock_get_manager.return_value = mock_manager
            
            mock_factory = MagicMock()
            mock_factory.switch_backend.return_value = True
            mock_get_factory.return_value = mock_factory
            
            mock_sync = MagicMock()
            mock_sync.sync_bidirectional.return_value = {'success': True}
            mock_get_sync.return_value = mock_sync
            
            mock_migration = MagicMock()
            mock_migration.migrate_sqlite_to_json.return_value = {'success': True}
            mock_get_migration.return_value = mock_migration
            
            # Test main function
            result = main(["--rule-stats"])
            assert result == 0
    
    def test_cli_subprocess_execution(self, temp_dir, mock_constitution_config):
        """Test CLI subprocess execution."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        # Test subprocess execution
        try:
            result = subprocess.run([
                sys.executable, "enhanced_cli.py", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0
            assert "usage:" in result.stdout.lower()
        except subprocess.TimeoutExpired:
            pytest.skip("Subprocess execution timed out")
        except FileNotFoundError:
            pytest.skip("enhanced_cli.py not found")
    
    def test_cli_unicode_output(self, temp_dir, mock_constitution_config):
        """Test CLI Unicode output handling."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        cli = ConstitutionCLI()
        
        # Mock constitution manager with Unicode content
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_all_rules.return_value = [
                {
                    'rule_number': 1,
                    'title': 'Unicode Test Rule 测试规则',
                    'content': 'This rule contains Unicode: 测试内容 🚀',
                    'enabled': True
                }
            ]
            mock_get_manager.return_value = mock_manager
            
            # Test Unicode output
            result = cli._list_rules()
            assert result is not None
    
    def test_cli_file_export_unicode(self, temp_dir, mock_constitution_config):
        """Test CLI file export with Unicode content."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        cli = ConstitutionCLI()
        
        # Mock constitution manager with Unicode content
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.export_rules_to_json.return_value = json.dumps({
                'rules': [
                    {
                        'rule_number': 1,
                        'title': 'Unicode Test Rule 测试规则',
                        'content': 'This rule contains Unicode: 测试内容 🚀'
                    }
                ]
            }, ensure_ascii=False)
            mock_get_manager.return_value = mock_manager
            
            # Test Unicode file export
            export_file = temp_dir / "unicode_export.json"
            result = cli._export_rules(str(export_file))
            assert result is not None
            assert export_file.exists()
    
    def test_cli_performance(self, temp_dir, mock_constitution_config):
        """Test CLI performance."""
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        cli = ConstitutionCLI()
        
        # Mock constitution manager
        with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_all_rules.return_value = [
                {
                    'rule_number': i,
                    'title': f'Rule {i}',
                    'content': f'Content {i}',
                    'enabled': True
                }
                for i in range(1000)
            ]
            mock_get_manager.return_value = mock_manager
            
            # Test performance
            import time
            start_time = time.time()
            result = cli._list_rules()
            end_time = time.time()
            
            assert result is not None
            assert (end_time - start_time) < 5.0, "CLI should be reasonably fast"
    
    def test_cli_concurrent_execution(self, temp_dir, mock_constitution_config):
        """Test CLI concurrent execution."""
        import threading
        import time
        
        # Create config file
        config_file = temp_dir / "constitution_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mock_constitution_config, f, indent=2)
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                cli = ConstitutionCLI()
                
                with patch('enhanced_cli.ConstitutionCLI._get_constitution_manager') as mock_get_manager:
                    mock_manager = MagicMock()
                    mock_manager.get_rule_statistics.return_value = {
                        'total_rules': 149,
                        'enabled_rules': 149,
                        'disabled_rules': 0
                    }
                    mock_get_manager.return_value = mock_manager
                    
                    result = cli._show_rule_statistics()
                    results.append((worker_id, result is not None))
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

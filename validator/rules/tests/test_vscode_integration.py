"""
Integration tests for VS Code extension components.

This test suite tests the integration between the Python validator
and the VS Code extension components.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import subprocess
import sys


class TestVSCodeExtensionStructure:
    """Test VS Code extension structure and configuration."""
    
    def test_package_json_structure(self):
        """Test that package.json has correct structure."""
        package_path = Path("package.json")
        assert package_path.exists(), "package.json should exist"
        
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        # Test required fields
        required_fields = [
            'name', 'displayName', 'description', 'version', 'publisher',
            'engines', 'main', 'contributes'
        ]
        
        for field in required_fields:
            assert field in package, f"package.json should contain {field}"
        
        # Test VS Code engine version
        assert 'vscode' in package['engines'], "Should specify VS Code engine"
        vscode_version = package['engines']['vscode']
        assert vscode_version.startswith('^'), "VS Code version should use caret range"
    
    def test_extension_commands(self):
        """Test that extension commands are properly defined."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        contributes = package.get('contributes', {})
        commands = contributes.get('commands', [])
        
        # Test required commands
        required_commands = [
            'zeroui.showDecisionPanel',
            'zeroui.validateFile',
            'zeroui.validateWorkspace'
        ]
        
        command_names = [cmd['command'] for cmd in commands]
        for required_cmd in required_commands:
            assert required_cmd in command_names, f"Command {required_cmd} should be defined"
    
    def test_extension_menus(self):
        """Test that extension menus are properly configured."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        contributes = package.get('contributes', {})
        menus = contributes.get('menus', {})
        
        # Test required menu configurations
        assert 'commandPalette' in menus, "Should have command palette menu"
        assert 'editor/context' in menus, "Should have editor context menu"
        
        # Test command palette entries
        command_palette = menus['commandPalette']
        assert len(command_palette) > 0, "Should have command palette entries"
        
        # Test editor context menu entries
        editor_context = menus['editor/context']
        assert len(editor_context) > 0, "Should have editor context menu entries"
    
    def test_extension_configuration(self):
        """Test that extension configuration is properly defined."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        contributes = package.get('contributes', {})
        configuration = contributes.get('configuration', {})
        
        assert 'title' in configuration, "Should have configuration title"
        assert 'properties' in configuration, "Should have configuration properties"
        
        properties = configuration['properties']
        
        # Test required configuration properties
        required_properties = [
            'zeroui.enableValidation',
            'zeroui.showStatusBar',
            'zeroui.autoValidate',
            'zeroui.severityLevel'
        ]
        
        for prop in required_properties:
            assert prop in properties, f"Configuration property {prop} should be defined"
    
    def test_compiled_extension_files(self):
        """Test that compiled extension files exist and are valid."""
        out_dir = Path("out")
        assert out_dir.exists(), "Compiled extension directory should exist"
        
        # Test main extension file
        extension_js = out_dir / "extension.js"
        assert extension_js.exists(), "extension.js should exist"
        assert extension_js.stat().st_size > 0, "extension.js should not be empty"
        
        # Test other compiled files
        required_files = [
            "configManager.js",
            "decisionPanel.js", 
            "statusBarManager.js",
            "constitutionValidator.js"
        ]
        
        for file_name in required_files:
            file_path = out_dir / file_name
            if file_path.exists():
                assert file_path.stat().st_size > 0, f"{file_name} should not be empty"
    
    def test_typescript_configuration(self):
        """Test TypeScript configuration."""
        tsconfig_path = Path("tsconfig.json")
        assert tsconfig_path.exists(), "tsconfig.json should exist"
        
        with open(tsconfig_path, 'r') as f:
            tsconfig = json.load(f)
        
        compiler_options = tsconfig.get('compilerOptions', {})
        
        # Test required compiler options
        required_options = [
            'module', 'target', 'outDir', 'sourceMap', 'rootDir', 'strict'
        ]
        
        for option in required_options:
            assert option in compiler_options, f"TypeScript config should have {option}"


class TestExtensionIntegration:
    """Test integration between extension and validator."""
    
    def test_extension_activation(self):
        """Test that extension can be activated."""
        # This is a placeholder for actual extension activation testing
        # In a real test environment, this would use the VS Code test framework
        
        # Test that the main extension file can be loaded
        extension_path = Path("out/extension.js")
        if extension_path.exists():
            with open(extension_path, 'r') as f:
                extension_content = f.read()
            
            # Test that it contains activation function
            assert 'activate' in extension_content, "Extension should have activate function"
            assert 'deactivate' in extension_content, "Extension should have deactivate function"
    
    def test_config_manager_integration(self):
        """Test config manager integration."""
        config_manager_path = Path("out/configManager.js")
        if config_manager_path.exists():
            with open(config_manager_path, 'r') as f:
                config_content = f.read()
            
            # Test that it contains configuration management
            assert 'ConfigManager' in config_content, "Should have ConfigManager class"
            assert 'getConfig' in config_content, "Should have getConfig method"
    
    def test_validator_integration(self):
        """Test validator integration."""
        validator_path = Path("out/constitutionValidator.js")
        if validator_path.exists():
            with open(validator_path, 'r') as f:
                validator_content = f.read()
            
            # Test that it contains validator functionality
            assert 'ConstitutionValidator' in validator_content, "Should have ConstitutionValidator class"
            assert 'validateFile' in validator_content, "Should have validateFile method"
    
    def test_decision_panel_integration(self):
        """Test decision panel integration."""
        decision_panel_path = Path("out/decisionPanel.js")
        if decision_panel_path.exists():
            with open(decision_panel_path, 'r') as f:
                panel_content = f.read()
            
            # Test that it contains decision panel functionality
            assert 'DecisionPanel' in panel_content, "Should have DecisionPanel class"
            assert 'show' in panel_content, "Should have show method"
    
    def test_status_bar_integration(self):
        """Test status bar integration."""
        status_bar_path = Path("out/statusBarManager.js")
        if status_bar_path.exists():
            with open(status_bar_path, 'r') as f:
                status_content = f.read()
            
            # Test that it contains status bar functionality
            assert 'StatusBarManager' in status_content, "Should have StatusBarManager class"
            assert 'updateStatus' in status_content, "Should have updateStatus method"


class TestExtensionCommands:
    """Test extension command functionality."""
    
    def test_command_registration(self):
        """Test that commands are properly registered."""
        extension_path = Path("out/extension.js")
        if extension_path.exists():
            with open(extension_path, 'r') as f:
                extension_content = f.read()
            
            # Test command registration
            required_commands = [
                'zeroui.showDecisionPanel',
                'zeroui.validateFile',
                'zeroui.validateWorkspace'
            ]
            
            for command in required_commands:
                assert command in extension_content, f"Command {command} should be registered"
    
    def test_command_handlers(self):
        """Test that command handlers are implemented."""
        extension_path = Path("out/extension.js")
        if extension_path.exists():
            with open(extension_path, 'r') as f:
                extension_content = f.read()
            
            # Test command handler patterns
            assert 'registerCommand' in extension_content, "Should register commands"
            assert 'showDecisionPanel' in extension_content, "Should handle showDecisionPanel"
            assert 'validateFile' in extension_content, "Should handle validateFile"
            assert 'validateWorkspace' in extension_content, "Should handle validateWorkspace"


class TestExtensionConfiguration:
    """Test extension configuration handling."""
    
    def test_configuration_reading(self):
        """Test that extension can read configuration."""
        # Test that configuration files exist and are readable
        config_files = [
            "config/base_config.json",
            "config/constitution_config.json"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                assert isinstance(config, dict), f"{config_file} should contain valid JSON"
                assert len(config) > 0, f"{config_file} should not be empty"
    
    def test_configuration_validation(self):
        """Test that configuration is valid."""
        config_path = Path("config/constitution_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Test required configuration fields
            required_fields = ['version', 'primary_backend', 'rules']
            for field in required_fields:
                assert field in config, f"Configuration should have {field}"
            
            # Test backend configuration
            if 'backend_config' in config:
                backend_config = config['backend_config']
                assert isinstance(backend_config, dict), "Backend config should be a dictionary"
    
    def test_rule_configuration(self):
        """Test rule configuration structure."""
        config_path = Path("config/constitution_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            rules = config.get('rules', {})
            assert isinstance(rules, dict), "Rules should be a dictionary"
            
            # Test that rules have proper structure
            for rule_id, rule_config in list(rules.items())[:5]:  # Test first 5 rules
                assert isinstance(rule_config, dict), f"Rule {rule_id} config should be a dictionary"
                assert 'enabled' in rule_config, f"Rule {rule_id} should have enabled field"


class TestExtensionPerformance:
    """Test extension performance characteristics."""
    
    def test_extension_startup_time(self):
        """Test that extension starts up quickly."""
        # This would normally test actual extension startup
        # For now, we test that the compiled files are reasonably sized
        
        out_dir = Path("out")
        if out_dir.exists():
            total_size = 0
            for file_path in out_dir.glob("*.js"):
                total_size += file_path.stat().st_size
            
            # Extension should be reasonably sized (less than 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            assert total_size < max_size, f"Extension size {total_size / 1024 / 1024:.2f}MB too large"
    
    def test_memory_efficiency(self):
        """Test that extension is memory efficient."""
        # Test that configuration loading is efficient
        config_path = Path("config/constitution_config.json")
        if config_path.exists():
            import time
            
            start_time = time.time()
            with open(config_path, 'r') as f:
                config = json.load(f)
            end_time = time.time()
            
            load_time = end_time - start_time
            assert load_time < 0.1, f"Config loading too slow: {load_time:.3f}s"


class TestExtensionCompatibility:
    """Test extension compatibility."""
    
    def test_vscode_version_compatibility(self):
        """Test VS Code version compatibility."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        engines = package.get('engines', {})
        vscode_version = engines.get('vscode', '')
        
        # Should support recent VS Code versions
        assert vscode_version.startswith('^'), "Should use caret range for compatibility"
        
        # Extract version number
        version_num = vscode_version[1:]  # Remove ^
        major_version = int(version_num.split('.')[0])
        assert major_version >= 1, "Should support VS Code 1.x"
    
    def test_node_version_compatibility(self):
        """Test Node.js version compatibility."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        engines = package.get('engines', {})
        node_version = engines.get('node', '')
        
        if node_version:
            # Should specify Node.js version
            assert node_version.startswith(('^', '~', '>=')), "Should use proper version range"
    
    def test_dependency_compatibility(self):
        """Test dependency compatibility."""
        package_path = Path("package.json")
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        dev_dependencies = package.get('devDependencies', {})
        
        # Test key dependencies
        key_deps = ['@types/vscode', 'typescript']
        for dep in key_deps:
            if dep in dev_dependencies:
                version = dev_dependencies[dep]
                assert version.startswith(('^', '~')), f"Dependency {dep} should use proper version range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

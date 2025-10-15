#!/usr/bin/env python3
"""
Integration test suite for ZeroUI2.0 Constitution validator.

Tests the integration between different components of the validation system.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from validator.core import ConstitutionValidator
from validator.models import Violation, ValidationResult, Severity
from validator.analyzer import CodeAnalyzer
from validator.reporter import ReportGenerator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

class TestValidatorIntegration:
    """Integration tests for the validator system."""
    
    @pytest.fixture
    def validator(self):
        """Get a validator instance."""
        return ConstitutionValidator()
    
    @pytest.fixture
    def analyzer(self):
        """Get a code analyzer instance."""
        return CodeAnalyzer()
    
    @pytest.fixture
    def reporter(self):
        """Get a report generator instance."""
        return ReportGenerator()
    
    @pytest.fixture
    def factory(self):
        """Get the dynamic test factory."""
        return DynamicTestFactory()
    
    def test_end_to_end_validation(self, validator):
        """Test complete end-to-end validation workflow."""
        # Create test file with various violations
        test_content = '''
#!/usr/bin/env python3
"""
Test file with various rule violations.
"""

# Rule L003: Hardcoded credentials
password = "secret123"
api_key = "sk-1234567890abcdef"

# Rule L001: Incomplete implementation
def incomplete_function():
    # TODO: Implement this
    pass

# Rule L008: Performance issue - nested loops
def slow_function():
    for i in range(1000):
        for j in range(1000):
            result = i * j

# Rule L015: Missing docstring
def undocumented_function():
    return "test"

# Rule L019: Mixed concerns - business logic in UI
class UserInterface:
    def display_user(self):
        # This should be in a service layer
        user = self.database.get_user()
        return user

# Rule L067: Time waste - blocking operation
def blocking_operation():
    import time
    time.sleep(1)  # This blocks execution
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Validate the file
            result = validator.validate_file(test_file)
            
            # Verify result structure
            assert isinstance(result, ValidationResult)
            assert result.file_path == test_file
            assert result.total_violations > 0
            assert result.compliance_score < 100
            assert result.processing_time > 0
            
            # Verify violations
            assert len(result.violations) > 0
            for violation in result.violations:
                assert isinstance(violation, Violation)
                assert violation.rule_number
                assert violation.rule_name
                assert violation.severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]
                assert violation.message
                assert violation.line_number > 0
                assert violation.code_snippet
            
            # Verify severity counts
            assert result.violations_by_severity[Severity.ERROR] >= 0
            assert result.violations_by_severity[Severity.WARNING] >= 0
            assert result.violations_by_severity[Severity.INFO] >= 0
            
        finally:
            Path(test_file).unlink()
    
    def test_directory_validation(self, validator):
        """Test validation of entire directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple test files
            files = [
                ("file1.py", "password = 'secret'  # L003 violation"),
                ("file2.py", "def incomplete(): pass  # L001 violation"),
                ("file3.py", "def good_function(): return 'ok'  # No violations"),
            ]
            
            for filename, content in files:
                (temp_path / filename).write_text(content)
            
            # Validate directory
            results = validator.validate_directory(str(temp_path))
            
            # Verify results
            assert len(results) == 3
            assert all(isinstance(result, ValidationResult) for result in results.values())
            
            # Check that violations were found in files with violations
            file1_result = results[str(temp_path / "file1.py")]
            file2_result = results[str(temp_path / "file2.py")]
            file3_result = results[str(temp_path / "file3.py")]
            
            assert file1_result.total_violations > 0
            assert file2_result.total_violations > 0
            assert file3_result.total_violations == 0
    
    def test_report_generation(self, validator, reporter):
        """Test report generation in all formats."""
        # Create test file
        test_content = '''
password = "secret"  # L003 violation
def incomplete(): pass  # L001 violation
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Validate file
            result = validator.validate_file(test_file)
            results = {test_file: result}
            
            # Test all report formats
            formats = ["console", "json", "html", "markdown"]
            
            for format_type in formats:
                report = reporter.generate_report(results, format_type)
                assert isinstance(report, str)
                assert len(report) > 0
                
                # Format-specific validations
                if format_type == "json":
                    json_data = json.loads(report)
                    assert "timestamp" in json_data
                    assert "total_files" in json_data
                    assert "summary" in json_data
                    assert "files" in json_data
                
                elif format_type == "html":
                    assert "<html" in report.lower()
                    assert "<body" in report.lower()
                    assert "ZEROUI" in report
                
                elif format_type == "markdown":
                    assert "# ZEROUI" in report
                    assert "## Summary" in report
                
                elif format_type == "console":
                    assert "ZEROUI 2.0 CONSTITUTION VALIDATION REPORT" in report
                    assert "SUMMARY:" in report
        
        finally:
            Path(test_file).unlink()
    
    def test_analyzer_integration(self, analyzer):
        """Test code analyzer integration."""
        test_content = '''
def complex_function():
    for i in range(10):
        for j in range(10):
            if i > 5:
                for k in range(10):
                    result = i * j * k
    return result

def risky_function():
    file = open("test.txt", "r")
    data = file.read()
    return data
'''
        
        import ast
        tree = ast.parse(test_content)
        
        # Test function complexity analysis
        functions = analyzer.analyze_function_complexity(tree)
        assert len(functions) == 2
        
        complex_func = next(f for f in functions if f.name == "complex_function")
        assert complex_func.complexity > 1  # Should have high complexity
        assert complex_func.nested_depth > 0
        
        # Test nested loop detection
        nested_loops = analyzer.detect_nested_loops(tree)
        assert len(nested_loops) > 0
        
        # Test risky operations detection
        risky_ops = analyzer.detect_risky_operations(tree)
        assert len(risky_ops) > 0
        
        # Test security issues detection
        security_issues = analyzer.detect_security_issues(tree)
        assert len(security_issues) > 0
    
    def test_configuration_loading(self, validator):
        """Test configuration loading and rule management."""
        # Test that configuration is loaded
        assert validator.config is not None
        assert "categories" in validator.config
        assert "validation_patterns" in validator.config
        
        # Test rule configuration manager
        rule_status = validator.get_rule_configuration_status()
        assert isinstance(rule_status, dict)
        
        # Test rule enablement check
        is_enabled = validator.is_rule_enabled("rule_003")
        assert isinstance(is_enabled, bool)
    
    def test_factory_integration(self, factory):
        """Test dynamic test factory integration."""
        # Test rule loading
        all_rules = factory.get_all_rules()
        assert len(all_rules) > 0
        
        # Test test case generation
        test_cases = factory.create_test_cases()
        assert len(test_cases) > 0
        
        # Test specific rule test case generation
        rule_003_cases = factory.create_test_cases(lambda x: x.get("id") == "L003")
        assert len(rule_003_cases) > 0
        
        for test_case in rule_003_cases:
            assert test_case.rule_id == "L003"
            assert test_case.category in ["security", "privacy_security"]
    
    def test_error_handling(self, validator):
        """Test error handling in various scenarios."""
        # Test non-existent file
        with pytest.raises(IOError):
            validator.validate_file("non_existent_file.py")
        
        # Test invalid Python syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("invalid python syntax !!!")
            invalid_file = f.name
        
        try:
            result = validator.validate_file(invalid_file)
            # Should handle syntax errors gracefully
            assert result.total_violations > 0
            assert result.compliance_score == 0.0
        finally:
            Path(invalid_file).unlink()
        
        # Test empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            empty_file = f.name
        
        try:
            result = validator.validate_file(empty_file)
            assert result.total_violations == 0
            assert result.compliance_score == 100.0
        finally:
            Path(empty_file).unlink()
    
    def test_performance_requirements(self, validator):
        """Test that performance requirements are met."""
        import time
        
        # Create a reasonably sized test file
        test_content = '''
# Performance test file
import os
import sys
import json

class TestClass:
    def __init__(self):
        self.value = "test"
    
    def method1(self):
        return self.value
    
    def method2(self):
        return self.value * 2

def function1():
    return "test"

def function2():
    return "test" * 2

# Some violations for testing
password = "secret"
def incomplete():
    pass
''' * 10  # Repeat content to make file larger
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Measure validation time
            start_time = time.time()
            result = validator.validate_file(test_file)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Performance requirement: < 2 seconds per file
            assert processing_time < 2.0, f"Validation too slow: {processing_time:.3f}s"
            
            # Verify result is still valid
            assert result.processing_time > 0
            assert result.compliance_score >= 0
        
        finally:
            Path(test_file).unlink()

"""
Tests for Architecture Validator (Rules 19, 21, 23, 24, 28, 30)

Tests architecture patterns and system design validation.
"""

import unittest
import ast
from validator.rules.architecture import ArchitectureValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestArchitectureValidator(unittest.TestCase):
    """Test suite for architecture rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ArchitectureValidator()
        self.test_file_path = "test.py"
    
    # Rule 19: Separation of concerns
    def test_rule_019_separation_valid(self):
        """Test Rule 19: Valid separation of concerns."""
        content = '''
# Service layer - business logic
class UserService:
    def get_user(self, user_id):
        return self.repository.find(user_id)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_separation_of_concerns(tree, "services/user_service.py")
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_019_business_logic_in_ui_violation(self):
        """Test Rule 19: Business logic in UI file."""
        content = '''
# UI file with business logic - BAD
def render_user_view(user_id):
    # Business logic in UI layer
    user = database.query("SELECT * FROM users WHERE id=?", user_id)
    total = calculate_user_balance(user)
    return f"<div>{user.name}: ${total}</div>"
'''
        tree = ast.parse(content)
        violations = self.validator.validate_separation_of_concerns(tree, "ui/user_view.py")
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_19")
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_019_data_access_in_ui_violation(self):
        """Test Rule 19: Data access in UI file."""
        content = '''
def show_users():
    users = sql.execute("SELECT * FROM users")
    return render_template("users.html", users=users)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_separation_of_concerns(tree, "frontend/views.py")
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_19")
    
    # Rule 21: Hybrid system design
    def test_rule_021_extension_display_only_valid(self):
        """Test Rule 21: Valid - IDE extension only displays."""
        content = '''
# IDE Extension - display only
def show_diagnostic(data):
    formatted = format_display(data)
    ide.show_message(formatted)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_hybrid_system_design(tree, "extension/display.py")
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_021_extension_processing_violation(self):
        """Test Rule 21: IDE extension processing data."""
        content = '''
# IDE Extension with data processing - BAD
def analyze_code(file_path):
    ast_tree = parse_file(file_path)
    results = analyze_complexity(ast_tree)  # Processing in extension
    compute_metrics(results)
    return results
'''
        tree = ast.parse(content)
        violations = self.validator.validate_hybrid_system_design(tree, "ide/extension.py")
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_21")
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_021_agent_local_processing_valid(self):
        """Test Rule 21: Valid - agent processes locally."""
        content = '''
# Edge Agent - local processing
def process_locally(data):
    analyzed = analyze(data)
    result = compute_locally(analyzed)
    return result
'''
        tree = ast.parse(content)
        violations = self.validator.validate_hybrid_system_design(tree, "agent/processor.py")
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_021_agent_uploading_violation(self):
        """Test Rule 21: Agent sending data to cloud."""
        content = '''
# Edge Agent uploading data - WARNING
def process_data(data):
    result = analyze(data)
    upload_to_cloud(result)  # Should process locally
    send_results(result)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_hybrid_system_design(tree, "edge/agent.py")
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_21")
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 23: Process data locally
    def test_rule_023_local_processing_valid(self):
        """Test Rule 23: Valid local data processing."""
        content = '''
def analyze_code():
    patterns = extract_patterns_locally(code)
    send_anonymous_patterns(patterns)  # Only patterns, not code
'''
        tree = ast.parse(content)
        violations = self.validator.validate_local_data_processing(tree, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_023_sending_source_code_violation(self):
        """Test Rule 23: Sending source code externally."""
        content = '''
def backup_code():
    source_code = read_all_files()
    api.post("https://cloud.example.com/backup", data=source_code)  # BAD
'''
        tree = ast.parse(content)
        violations = self.validator.validate_local_data_processing(tree, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_23")
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_023_sending_sensitive_data_violation(self):
        """Test Rule 23: Sending sensitive data."""
        content = '''
def sync_data():
    private_data = load_private_info()
    aws.upload(private_data)  # Sending sensitive data
'''
        tree = ast.parse(content)
        violations = self.validator.validate_data_flow(tree, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_23")
    
    # Rule 24: Zero configuration
    def test_rule_024_default_values_valid(self):
        """Test Rule 24: Valid - default configuration values."""
        content = '''
class Service:
    def __init__(self, timeout=30, retries=3):
        self.timeout = timeout
        self.retries = retries
'''
        tree = ast.parse(content)
        violations = self.validator.validate_zero_configuration(tree, content, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_024_required_config_violation(self):
        """Test Rule 24: Required configuration before use."""
        content = '''
class Service:
    def __init__(self, api_key, endpoint, timeout, retries):
        # All required, no defaults
        self.api_key = api_key
        self.endpoint = endpoint
'''
        tree = ast.parse(content)
        violations = self.validator.validate_zero_configuration(tree, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_24")
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    def test_rule_024_required_config_file_violation(self):
        """Test Rule 24: Required config file."""
        content = '''
# Configuration required before use
config = load_config("config.yaml")  # Must have config file
if not config:
    raise Exception("Configuration required")
'''
        violations = self.validator.validate_zero_configuration(None, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_24")
    
    # Rule 28: Work without internet
    def test_rule_028_offline_fallback_valid(self):
        """Test Rule 28: Valid offline fallback."""
        content = '''
import requests

def fetch_data():
    try:
        return requests.get(url, timeout=5)
    except Exception:
        return load_from_cache()  # Offline fallback
'''
        tree = ast.parse(content)
        violations = self.validator.validate_offline_capability(tree, content, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_028_no_offline_support_violation(self):
        """Test Rule 28: No offline capability."""
        content = '''
import requests

def fetch_data():
    return requests.get(url)  # No offline fallback
'''
        tree = ast.parse(content)
        violations = self.validator.validate_offline_capability(tree, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_28")
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    def test_rule_028_caching_valid(self):
        """Test Rule 28: Valid - local caching."""
        content = '''
import requests
import sqlite3

cache = sqlite3.connect("cache.db")
data = cache.get_or_fetch(url)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_offline_capability(tree, content, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_028_network_without_cache_violation(self):
        """Test Rule 28: Network operations without caching."""
        content = '''
import requests

response = requests.get("https://api.example.com/data")
data = response.json()
'''
        tree = ast.parse(content)
        violations = self.validator.validate_offline_capability(tree, content, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_28")
        self.assertEqual(violations[0].severity, Severity.INFO)
    
    # Rule 30: Module consistency
    def test_rule_030_consistent_error_handling_valid(self):
        """Test Rule 30: Valid consistent error handling."""
        content = '''
def process():
    try:
        risky_operation()
    except Exception as e:
        handle_error(e)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_module_consistency(tree, self.test_file_path)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_030_inconsistent_error_handling_violation(self):
        """Test Rule 30: Inconsistent error handling."""
        content = '''
def process():
    file = open("data.txt")
    requests.get(url)
    subprocess.run(["ls"])
    # Risky operations without error handling
'''
        tree = ast.parse(content)
        violations = self.validator.validate_module_consistency(tree, self.test_file_path)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, "rule_30")
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Integration test
    def test_validate_all_rules_comprehensive(self):
        """Test validate_all() method with multiple violations."""
        content = '''
# UI file with mixed concerns
def render_user(user_id):
    # Business logic in UI - R19
    user = database.query("SELECT * FROM users WHERE id=?", user_id)
    
    # Sending data to cloud - R23
    api.post("https://cloud.example.com", user)
    
    # Network without cache - R28
    external_data = requests.get("https://api.example.com")
    
    return render(user)
'''
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, "ui/user_view.py")
        
        # Should have violations from multiple rules
        rule_ids = set(v.rule_id for v in violations)
        self.assertGreater(len(rule_ids), 1)
        self.assertIn("rule_19", rule_ids)


if __name__ == '__main__':
    unittest.main()


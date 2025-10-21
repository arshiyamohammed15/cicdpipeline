"""
Tests for Exception Handling Validator (Rules 150-181)

Tests exception handling standards and practices validation.
"""

import unittest
import ast
from validator.rules.exception_handling import ExceptionHandlingValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestExceptionHandlingValidator(unittest.TestCase):
    """Test suite for exception handling rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ExceptionHandlingValidator()
        self.test_file_path = "test.py"
    
    # Rule 150: Validate inputs early
    def test_rule_150_input_validation_valid(self):
        """Test Rule 150: Valid early input validation."""
        content = '''
def process_data(data, size):
    """Process data with validation."""
    if data is None:
        raise ValueError("Data cannot be None")
    if size <= 0:
        raise ValueError("Size must be positive")
    
    return data[:size]
'''
        tree = ast.parse(content)
        violations = self.validator._validate_prevent_first(tree, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_150_no_validation_violation(self):
        """Test Rule 150: Function without input validation."""
        content = '''
def process_data(data, size):
    """Process data without validation."""
    return data[:size]
'''
        tree = ast.parse(content)
        violations = self.validator._validate_prevent_first(tree, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R150')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 151: Canonical error codes
    def test_rule_151_canonical_codes_valid(self):
        """Test Rule 151: Valid canonical error codes."""
        content = '''
error_code = "VALIDATION_ERROR"
raise CustomError("TIMEOUT", "Operation timed out")
'''
        violations = self.validator._validate_error_codes(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_151_non_canonical_code_violation(self):
        """Test Rule 151: Non-canonical error code."""
        content = '''
error_code = "CUSTOM_ERROR_123"
raise CustomError("BAD_REQUEST_ERROR")
'''
        violations = self.validator._validate_error_codes(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R151')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 152: Wrap and chain errors
    def test_rule_152_wrap_error_valid(self):
        """Test Rule 152: Valid error wrapping."""
        content = '''
try:
    low_level_operation()
except Exception as e:
    raise ApplicationError("Failed to process", cause=e)
'''
        tree = ast.parse(content)
        violations = self.validator._validate_wrap_chain(tree, self.test_file_path, content)
        
        # Bare raise or proper wrapping should not violate
        self.assertEqual(len(violations), 0)
    
    def test_rule_152_unwrapped_error_violation(self):
        """Test Rule 152: Unwrapped error."""
        content = '''
try:
    low_level_operation()
except Exception as e:
    raise e
'''
        tree = ast.parse(content)
        violations = self.validator._validate_wrap_chain(tree, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R152')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 154: Friendly & detailed
    def test_rule_154_technical_error_message_violation(self):
        """Test Rule 154: Technical error text should be flagged."""
        content = '''
raise Exception("Traceback: Error at line 10")
'''
        violations = self.validator._validate_friendly_detailed(None, self.test_file_path, content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R154')
        self.assertEqual(violations[0].severity, Severity.INFO)
    
    def test_rule_154_user_friendly_message_valid(self):
        """Test Rule 154: User-friendly message should not be flagged."""
        content = '''
user_message = "We couldn't complete that. Please retry or contact support."
'''
        violations = self.validator._validate_friendly_detailed(None, self.test_file_path, content)
        self.assertEqual(len(violations), 0)
    
    # Rule 156: Add context on wrapping
    def test_rule_156_wrapping_without_context_violation(self):
        """Test Rule 156: Wrapping without context keywords."""
        content = '''
raise ProcessingError("Failed to process")
'''
        violations = self.validator._validate_add_context(None, self.test_file_path, content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R156')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    def test_rule_156_wrapping_with_context_valid(self):
        """Test Rule 156: Wrapping with context keywords is valid."""
        content = '''
raise ProcessingError("operation=upload id=123 step=write context=user")
'''
        violations = self.validator._validate_add_context(None, self.test_file_path, content)
        self.assertEqual(len(violations), 0)
    
    # Rule 165: HTTP/Exit code mapping
    def test_rule_165_nonstandard_status_violation(self):
        """Test Rule 165: Non-standard HTTP status should be flagged."""
        content = '''
response.status = 299
'''
        violations = self.validator._validate_http_exit_mapping(None, self.test_file_path, content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R165')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    def test_rule_165_standard_status_valid(self):
        """Test Rule 165: Standard HTTP statuses are accepted."""
        content = '''
status_code = 404
return 200
'''
        violations = self.validator._validate_http_exit_mapping(None, self.test_file_path, content)
        self.assertEqual(len(violations), 0)
    
    # Rule 166: Message catalog
    def test_rule_166_hardcoded_error_message_violation(self):
        """Test Rule 166: Hardcoded error strings flagged."""
        content = '''
logger.error("Invalid user input")
'''
        violations = self.validator._validate_message_catalog(None, self.test_file_path, content)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R166')
        self.assertEqual(violations[0].severity, Severity.INFO)
    
    def test_rule_166_catalog_message_valid(self):
        """Test Rule 166: Simulated message catalog usage is valid."""
        content = '''
messages = {"VALIDATION_ERROR": "Please check your input"}
logger.error(messages["VALIDATION_ERROR"])
'''
        violations = self.validator._validate_message_catalog(None, self.test_file_path, content)
        self.assertEqual(len(violations), 0)
    
    # Rule 153: Central error handler
    def test_rule_153_central_handler_valid(self):
        """Test Rule 153: Valid central error handler."""
        content = '''
def process_request(request):
    """Process with single error handler."""
    try:
        validate(request)
        execute(request)
        return response
    except Exception as e:
        return handle_error(e)
'''
        tree = ast.parse(content)
        violations = self.validator._validate_central_handler(tree, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_153_multiple_handlers_violation(self):
        """Test Rule 153: Multiple try blocks."""
        content = '''
def process_request(request):
    """Process with multiple error handlers."""
    try:
        validate(request)
    except Exception as e:
        log(e)
    
    try:
        execute(request)
    except Exception as e:
        log(e)
'''
        tree = ast.parse(content)
        violations = self.validator._validate_central_handler(tree, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R153')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 155: No silent catches
    def test_rule_155_silent_catch_violation(self):
        """Test Rule 155: Silent exception catch."""
        content = '''
try:
    risky_operation()
except Exception:
    pass
'''
        tree = ast.parse(content)
        violations = self.validator._validate_no_silent_catches(tree, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R155')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_155_logged_catch_valid(self):
        """Test Rule 155: Valid - exception with logging."""
        content = '''
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise
'''
        tree = ast.parse(content)
        violations = self.validator._validate_no_silent_catches(tree, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 157: Cleanup always
    def test_rule_157_cleanup_with_context_valid(self):
        """Test Rule 157: Valid cleanup with context manager."""
        content = '''
with open("file.txt", "r") as f:
    data = f.read()
    process(data)
'''
        violations = self.validator._validate_cleanup_always(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_157_no_cleanup_violation(self):
        """Test Rule 157: Resource without cleanup."""
        content = '''
f = open("file.txt", "r")
data = f.read()
process(data)
'''
        violations = self.validator._validate_cleanup_always(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R157')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 161: Timeouts
    def test_rule_161_timeout_valid(self):
        """Test Rule 161: Valid timeout."""
        content = '''
import requests
response = requests.get("https://api.example.com", timeout=30)
'''
        violations = self.validator._validate_timeouts(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_161_no_timeout_violation(self):
        """Test Rule 161: I/O without timeout."""
        content = '''
import requests
response = requests.get("https://api.example.com")
data = response.json()
'''
        violations = self.validator._validate_timeouts(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R161')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 162: Retries with backoff
    def test_rule_162_retry_with_backoff_valid(self):
        """Test Rule 162: Valid retry with backoff."""
        content = '''
import time
for attempt in range(max_retries):
    try:
        result = call_api()
        break
    except Exception:
        wait = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
        time.sleep(wait)
'''
        violations = self.validator._validate_retries_backoff(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_162_retry_without_backoff_violation(self):
        """Test Rule 162: Retry without backoff."""
        content = '''
for attempt in range(max_retries):
    try:
        result = call_api()
        break
    except Exception:
        continue
'''
        violations = self.validator._validate_retries_backoff(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R162')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 163: No retry for non-retriable errors
    def test_rule_163_retry_validation_error_violation(self):
        """Test Rule 163: Retrying validation errors."""
        content = '''
for retry in range(3):
    try:
        validate_input(data)  # Validation errors should not be retried
    except ValidationError:
        continue
'''
        violations = self.validator._validate_no_retry_nonretriables(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R163')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_163_retry_timeout_valid(self):
        """Test Rule 163: Valid retry for timeout."""
        content = '''
for retry in range(3):
    try:
        result = call_api()
    except TimeoutError:
        continue  # Timeouts are retriable
'''
        violations = self.validator._validate_no_retry_nonretriables(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 164: Idempotency for writes
    def test_rule_164_idempotent_write_valid(self):
        """Test Rule 164: Valid idempotent write."""
        content = '''
def upsert_user(user_id, data):
    """Idempotent upsert operation."""
    db.merge(user_id, data)  # Idempotent operation
'''
        violations = self.validator._validate_idempotency(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_164_non_idempotent_write_violation(self):
        """Test Rule 164: Non-idempotent write."""
        content = '''
def create_user(data):
    """Non-idempotent insert."""
    db.insert(data)
'''
        violations = self.validator._validate_idempotency(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R164')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 168: Structured logs
    def test_rule_168_structured_logging_valid(self):
        """Test Rule 168: Valid structured logging."""
        content = '''
import json
import logging
logger.info(json.dumps({"event": "user_login", "user_id": 123}))
'''
        violations = self.validator._validate_structured_logs(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_168_unstructured_logging_violation(self):
        """Test Rule 168: Unstructured logging."""
        content = '''
import logging
logger.info("User logged in")
logger.error("Something went wrong")
'''
        violations = self.validator._validate_structured_logs(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R168')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 169: Correlation IDs
    def test_rule_169_correlation_id_valid(self):
        """Test Rule 169: Valid correlation ID propagation."""
        content = '''
import requests
trace_id = generate_trace_id()
response = requests.get(url, headers={"X-Trace-ID": trace_id})
'''
        violations = self.validator._validate_correlation(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_169_no_correlation_violation(self):
        """Test Rule 169: No correlation ID."""
        content = '''
import requests
response = requests.get("https://api.example.com")
'''
        violations = self.validator._validate_correlation(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R169')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 170: Privacy in logs
    def test_rule_170_secrets_in_logs_violation(self):
        """Test Rule 170: Logging secrets."""
        content = '''
logger.info(f"User password: {password}")
logger.debug(f"API token: {token}")
'''
        violations = self.validator._validate_privacy_secrets(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R170')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_170_redacted_secrets_valid(self):
        """Test Rule 170: Valid - redacted secrets."""
        content = '''
logger.info(f"User password: {redact(password)}")
logger.debug(f"API token: {'***' if token else None}")
'''
        violations = self.validator._validate_privacy_secrets(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 174: Safe defaults
    def test_rule_174_hardcoded_timeout_violation(self):
        """Test Rule 174: Hardcoded timeout."""
        content = '''
def call_api():
    timeout = 30  # Hardcoded
    response = requests.get(url, timeout=timeout)
'''
        violations = self.validator._validate_safe_defaults(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R174')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    def test_rule_174_configurable_timeout_valid(self):
        """Test Rule 174: Valid - configurable timeout."""
        content = '''
def call_api():
    timeout = config.get("api_timeout", default=30)
    response = requests.get(url, timeout=timeout)
'''
        violations = self.validator._validate_safe_defaults(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 175: AI transparency
    def test_rule_175_ai_with_transparency_valid(self):
        """Test Rule 175: Valid AI with transparency."""
        content = '''
import ai
result = model.predict(data)
result["confidence"] = 0.95
result["reasoning"] = "Based on patterns X, Y, Z"
result["model_version"] = "v1.2.3"
'''
        violations = self.validator._validate_ai_transparency(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_175_ai_without_transparency_violation(self):
        """Test Rule 175: AI without transparency."""
        content = '''
import ai
result = model.predict(data)
return result
'''
        violations = self.validator._validate_ai_transparency(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R175')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 176: AI sandbox
    def test_rule_176_ai_direct_exec_violation(self):
        """Test Rule 176: AI executing code directly."""
        content = '''
import ai
code = model.generate_code(prompt)
exec(code)  # Dangerous!
'''
        violations = self.validator._validate_ai_sandbox(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R176')
        self.assertEqual(violations[0].severity, Severity.ERROR)
    
    def test_rule_176_ai_sandbox_valid(self):
        """Test Rule 176: Valid - AI in sandbox."""
        content = '''
import ai
code = model.generate_code(prompt)
sandbox = create_sandbox()
result = sandbox.run(code)
'''
        violations = self.validator._validate_ai_sandbox(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    # Rule 178: AI confidence thresholds
    def test_rule_178_ai_thresholds_valid(self):
        """Test Rule 178: Valid AI confidence thresholds."""
        content = '''
confidence = model.predict_confidence(data)
if confidence > 90:
    apply_automatically()
elif confidence > 70:
    suggest_to_user()
else:
    request_approval()
'''
        violations = self.validator._validate_ai_thresholds(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_178_ai_no_thresholds_violation(self):
        """Test Rule 178: AI without thresholds."""
        content = '''
confidence = model.predict_confidence(data)
if confidence > 50:
    apply()
'''
        violations = self.validator._validate_ai_thresholds(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R178')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 179: Graceful degradation
    def test_rule_179_graceful_degradation_valid(self):
        """Test Rule 179: Valid graceful degradation."""
        content = '''
try:
    data = fetch_from_service()
except DependencyError:
    data = fallback_data()  # Graceful degradation
'''
        violations = self.validator._validate_graceful_degradation(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_179_no_degradation_violation(self):
        """Test Rule 179: No graceful degradation."""
        content = '''
dependency = load_dependency()
if not dependency:
    raise Exception("Dependency failed")
'''
        violations = self.validator._validate_graceful_degradation(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R179')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Rule 180: State recovery
    def test_rule_180_state_recovery_valid(self):
        """Test Rule 180: Valid state recovery."""
        content = '''
def process():
    checkpoint = save_checkpoint()
    try:
        risky_operation()
    except Exception:
        restore_from_checkpoint(checkpoint)
        rollback_state()
'''
        violations = self.validator._validate_state_recovery(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_180_no_recovery_violation(self):
        """Test Rule 180: No state recovery."""
        content = '''
def process():
    risky_operation()
    # Crash here - no recovery
'''
        violations = self.validator._validate_state_recovery(None, self.test_file_path, content)
        
        # Should warn if crash/failure mentioned without recovery
        content_with_failure = '''
def process():
    # System may crash here
    risky_operation()
'''
        violations = self.validator._validate_state_recovery(None, self.test_file_path, content_with_failure)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R180')
    
    # Rule 181: Feature flags
    def test_rule_181_feature_flag_valid(self):
        """Test Rule 181: Valid feature flag."""
        content = '''
if feature_flag_enabled("new_risky_feature"):
    experimental_function()
else:
    stable_function()
'''
        violations = self.validator._validate_feature_flags(None, self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_181_risky_without_flag_violation(self):
        """Test Rule 181: Risky change without feature flag."""
        content = '''
# This is an experimental risky feature
def new_experimental_logic():
    pass
'''
        violations = self.validator._validate_feature_flags(None, self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'R181')
        self.assertEqual(violations[0].severity, Severity.WARNING)
    
    # Integration test
    def test_validate_all_rules_comprehensive(self):
        """Test validate() method with multiple violations."""
        content = '''
def process_data(data):  # R150: No validation
    try:
        result = call_api()  # R161: No timeout
    except Exception:
        pass  # R155: Silent catch
    
    f = open("file.txt")  # R157: No cleanup
    return result
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        # Should have violations from multiple rules
        rule_ids = set(v.rule_id for v in violations)
        self.assertGreater(len(rule_ids), 1)


if __name__ == '__main__':
    unittest.main()


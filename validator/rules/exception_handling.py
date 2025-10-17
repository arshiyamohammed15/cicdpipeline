"""
Exception Handling Constitution Validator

Validates compliance with the ZeroUI 2.0 Exception Handling Constitution.
Covers error prevention, canonical codes, wrapping, central handling, timeouts, retries, and recovery.
"""

import re
import ast
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class ExceptionHandlingValidator:
    """Validates exception handling standards and practices."""
    
    def __init__(self):
        self.rules = {
            'R150': self._validate_prevent_first,
            'R151': self._validate_error_codes,
            'R152': self._validate_wrap_chain,
            'R153': self._validate_central_handler,
            'R154': self._validate_friendly_detailed,
            'R155': self._validate_no_silent_catches,
            'R156': self._validate_add_context,
            'R157': self._validate_cleanup_always,
            'R158': self._validate_recovery_patterns,
            'R160': self._validate_onboarding,
            'R161': self._validate_timeouts,
            'R162': self._validate_retries_backoff,
            'R163': self._validate_no_retry_nonretriables,
            'R164': self._validate_idempotency,
            'R165': self._validate_http_exit_mapping,
            'R166': self._validate_message_catalog,
            'R167': self._validate_ui_behavior,
            'R168': self._validate_structured_logs,
            'R169': self._validate_correlation,
            'R170': self._validate_privacy_secrets,
            'R171': self._validate_failure_paths,
            'R172': self._validate_contracts_docs,
            'R173': self._validate_consistency,
            'R174': self._validate_safe_defaults,
            'R175': self._validate_ai_transparency,
            'R176': self._validate_ai_sandbox,
            'R177': self._validate_ai_learning,
            'R178': self._validate_ai_thresholds,
            'R179': self._validate_graceful_degradation,
            'R180': self._validate_state_recovery,
            'R181': self._validate_feature_flags
        }
        
        # Canonical error codes with severity levels
        self.canonical_codes = {
            'VALIDATION_ERROR': 'LOW',
            'AUTH_FORBIDDEN': 'LOW', 
            'RESOURCE_NOT_FOUND': 'LOW',
            'CANCELLED': 'LOW',
            'RATE_LIMITED': 'MEDIUM',
            'CONFLICT': 'MEDIUM',
            'INVARIANT_VIOLATION': 'MEDIUM',
            'DEPENDENCY_FAILED': 'HIGH',
            'INTERNAL_ERROR': 'HIGH',
            'TIMEOUT': 'HIGH'
        }
        
        # Retriable error codes
        self.retriable_codes = {
            'DEPENDENCY_FAILED', 'TIMEOUT', 'RATE_LIMITED'
        }
        
        # Non-retriable error codes
        self.non_retriable_codes = {
            'VALIDATION_ERROR', 'AUTH_FORBIDDEN', 'RESOURCE_NOT_FOUND'
        }
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate exception handling compliance for a file."""
        violations = []
        
        try:
            # Parse file content based on extension
            if file_path.endswith('.py'):
                tree = ast.parse(content)
                for rule_id, rule_func in self.rules.items():
                    try:
                        rule_violations = rule_func(tree, file_path, content)
                        violations.extend(rule_violations)
                    except Exception as e:
                        violations.append(Violation(
                            rule_id=rule_id,
                            file_path=file_path,
                            line_number=1,
                            message=f"Error validating {rule_id}: {str(e)}",
                            severity=Severity.ERROR
                        ))
            else:
                # For non-Python files, check text patterns
                for rule_id, rule_func in self.rules.items():
                    try:
                        rule_violations = rule_func(None, file_path, content)
                        violations.extend(rule_violations)
                    except Exception as e:
                        violations.append(Violation(
                            rule_id=rule_id,
                            file_path=file_path,
                            line_number=1,
                            message=f"Error validating {rule_id}: {str(e)}",
                            severity=Severity.ERROR
                        ))
        
        except Exception as e:
            violations.append(Violation(
                rule_id="R150",
                file_path=file_path,
                line_number=1,
                message=f"Failed to parse file for exception handling validation: {str(e)}",
                severity=Severity.ERROR
            ))
        
        return violations
    
    def _validate_prevent_first(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R150: Validate inputs early (required, type, range, size). Prevention beats cure."""
        violations = []
        
        if tree is None:
            return violations
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for input validation at function start
                has_validation = False
                for stmt in node.body[:3]:  # Check first 3 statements
                    if isinstance(stmt, (ast.If, ast.Assert)):
                        has_validation = True
                        break
                
                if not has_validation and len(node.args.args) > 0:
                    violations.append(Violation(
                        rule_id="R150",
                        file_path=file_path,
                        line_number=node.lineno,
                        message="Function should validate inputs early (required, type, range, size)",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_error_codes(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R151: Adopt ~10–12 canonical codes with severity levels."""
        violations = []
        
        # Check for hardcoded error codes that aren't canonical
        error_code_pattern = r'["\']([A-Z_]+_ERROR|ERROR_[A-Z_]+)["\']'
        matches = re.findall(error_code_pattern, content)
        
        for match in matches:
            if match not in self.canonical_codes:
                violations.append(Violation(
                    rule_id="R151",
                    file_path=file_path,
                    line_number=1,
                    message=f"Non-canonical error code '{match}' should use canonical codes: {list(self.canonical_codes.keys())}",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_wrap_chain(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R152: Wrap low-level errors with friendly message and keep original as cause."""
        violations = []
        
        # Check for bare raise statements that don't wrap errors
        if tree is None:
            return violations
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if node.exc is None:
                    # Bare raise - this is OK
                    continue
                elif isinstance(node.exc, ast.Name):
                    # Raising a variable - check if it's wrapped
                    violations.append(Violation(
                        rule_id="R152",
                        file_path=file_path,
                        line_number=node.lineno,
                        message="Raised exception should be wrapped with context and friendly message",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_central_handler(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R153: Have one handler per surface (API endpoint, CLI entry, IDE command)."""
        violations = []
        
        # Check for multiple exception handlers in the same function
        if tree is None:
            return violations
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                try_blocks = [n for n in ast.walk(node) if isinstance(n, ast.Try)]
                if len(try_blocks) > 1:
                    violations.append(Violation(
                        rule_id="R153",
                        file_path=file_path,
                        line_number=node.lineno,
                        message="Function should use central error handler instead of multiple try blocks",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_friendly_detailed(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R154: Users see short, calm guidance. Logs contain context and cause chain."""
        violations = []
        
        # Check for technical error messages that should be user-friendly
        technical_patterns = [
            r'Exception\s*:', r'Error\s*:', r'Failed\s*:', r'Traceback',
            r'stack\s*trace', r'line\s*\d+', r'File\s*".*"'
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(Violation(
                    rule_id="R154",
                    file_path=file_path,
                    line_number=1,
                    message="Error messages should be user-friendly, not technical",
                    severity=Severity.INFO
                ))
                break
        
        return violations
    
    def _validate_no_silent_catches(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R155: Never swallow errors. If you catch it, either fix, retry, or wrap & bubble."""
        violations = []
        
        if tree is None:
            return violations
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check if except block is empty or only has pass
                if (len(node.body) == 0 or 
                    (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))):
                    violations.append(Violation(
                        rule_id="R155",
                        file_path=file_path,
                        line_number=node.lineno,
                        message="Silent catch detected - should fix, retry, or wrap & bubble error",
                        severity=Severity.ERROR
                    ))
        
        return violations
    
    def _validate_add_context(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R156: Always include where/what (operation name, ids, step) when wrapping."""
        violations = []
        
        # Check for error wrapping without context
        context_patterns = [
            r'raise.*Error\(.*\)', r'raise.*Exception\(.*\)'
        ]
        
        for pattern in context_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                error_msg = match.group(0)
                if not any(keyword in error_msg.lower() for keyword in ['operation', 'id', 'step', 'context']):
                    violations.append(Violation(
                        rule_id="R156",
                        file_path=file_path,
                        line_number=1,
                        message="Error wrapping should include context (operation name, ids, step)",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_cleanup_always(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R157: Close files, sockets, timers; release locks. Use 'always-run' cleanup paths."""
        violations = []
        
        # Check for resource usage without cleanup
        resource_patterns = [
            r'open\(', r'\.connect\(', r'\.acquire\(', r'threading\.Lock\(\)'
        ]
        
        for pattern in resource_patterns:
            if re.search(pattern, content):
                # Check for corresponding cleanup
                cleanup_patterns = [
                    r'\.close\(\)', r'\.disconnect\(\)', r'\.release\(\)', r'with\s+'
                ]
                has_cleanup = any(re.search(cp, content) for cp in cleanup_patterns)
                
                if not has_cleanup:
                    violations.append(Violation(
                        rule_id="R157",
                        file_path=file_path,
                        line_number=1,
                        message="Resource usage detected without cleanup - use 'with' statements or finally blocks",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_recovery_patterns(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R158: Define clear recovery actions for each error type."""
        violations = []
        
        # Check for error handling without recovery guidance
        error_handling_pattern = r'except.*:'
        if re.search(error_handling_pattern, content):
            recovery_keywords = ['retry', 'fallback', 'recovery', 'guidance', 'contact support']
            has_recovery = any(keyword in content.lower() for keyword in recovery_keywords)
            
            if not has_recovery:
                violations.append(Violation(
                    rule_id="R158",
                    file_path=file_path,
                    line_number=1,
                    message="Error handling should include recovery guidance",
                    severity=Severity.INFO
                ))
        
        return violations
    
    def _validate_onboarding(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R160: Provide 'First Error Handling Task' template and examples."""
        violations = []
        
        # This is more of a documentation/process rule
        # Check for error handling examples or templates
        example_patterns = [
            r'# Example', r'# Template', r'# TODO.*error', r'# FIXME.*error'
        ]
        
        has_examples = any(re.search(pattern, content, re.IGNORECASE) for pattern in example_patterns)
        
        if not has_examples and 'error' in content.lower():
            violations.append(Violation(
                rule_id="R160",
                file_path=file_path,
                line_number=1,
                message="Error handling code should include examples or templates for onboarding",
                severity=Severity.INFO
            ))
        
        return violations
    
    def _validate_timeouts(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R161: All I/O (network, file, DB, subprocess) must have a timeout."""
        violations = []
        
        # Check for I/O operations without timeouts
        io_patterns = [
            r'requests\.get\(', r'requests\.post\(', r'urllib\.', r'subprocess\.',
            r'socket\.', r'\.read\(', r'\.write\(', r'\.execute\('
        ]
        
        for pattern in io_patterns:
            if re.search(pattern, content):
                # Check for timeout parameter
                if 'timeout' not in content.lower():
                    violations.append(Violation(
                        rule_id="R161",
                        file_path=file_path,
                        line_number=1,
                        message="I/O operations should include timeout parameter",
                        severity=Severity.WARNING
                    ))
                break
        
        return violations
    
    def _validate_retries_backoff(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R162: Retry only idempotent operations. Max 2–3 tries. Use exponential backoff + jitter."""
        violations = []
        
        # Check for retry logic
        retry_patterns = [
            r'for.*in.*range\(.*retry', r'while.*retry', r'\.retry\('
        ]
        
        has_retry = any(re.search(pattern, content, re.IGNORECASE) for pattern in retry_patterns)
        
        if has_retry:
            # Check for exponential backoff
            if 'backoff' not in content.lower() and 'jitter' not in content.lower():
                violations.append(Violation(
                    rule_id="R162",
                    file_path=file_path,
                    line_number=1,
                    message="Retry logic should use exponential backoff with jitter",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_no_retry_nonretriables(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R163: No retries for validation errors, 401/403, 404, or business rule failures."""
        violations = []
        
        # Check for retrying non-retriable errors
        non_retriable_patterns = [
            r'retry.*validation', r'retry.*401', r'retry.*403', r'retry.*404'
        ]
        
        for pattern in non_retriable_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(Violation(
                    rule_id="R163",
                    file_path=file_path,
                    line_number=1,
                    message="Should not retry validation errors, 401/403, 404, or business rule failures",
                    severity=Severity.ERROR
                ))
        
        return violations
    
    def _validate_idempotency(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R164: Design writes so they are safe to retry."""
        violations = []
        
        # Check for write operations without idempotency
        write_patterns = [
            r'\.insert\(', r'\.update\(', r'\.delete\(', r'\.save\('
        ]
        
        has_writes = any(re.search(pattern, content) for pattern in write_patterns)
        
        if has_writes:
            idempotency_keywords = ['idempotent', 'idempotency', 'upsert', 'merge']
            has_idempotency = any(keyword in content.lower() for keyword in idempotency_keywords)
            
            if not has_idempotency:
                violations.append(Violation(
                    rule_id="R164",
                    file_path=file_path,
                    line_number=1,
                    message="Write operations should be designed for idempotency",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_http_exit_mapping(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R165: Map canonical codes to standard outcomes (400/401/403/404/409/422/429/5xx)."""
        violations = []
        
        # Check for proper HTTP status code mapping
        status_patterns = [
            r'status_code\s*=\s*(\d+)', r'return.*(\d+)', r'\.status\s*=\s*(\d+)'
        ]
        
        for pattern in status_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                status_code = int(match.group(1))
                if status_code not in [200, 201, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504]:
                    violations.append(Violation(
                        rule_id="R165",
                        file_path=file_path,
                        line_number=1,
                        message=f"HTTP status code {status_code} should follow standard mapping",
                        severity=Severity.WARNING
                    ))
        
        return violations
    
    def _validate_message_catalog(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R166: Keep a single catalog that maps each code → one friendly, human sentence."""
        violations = []
        
        # Check for hardcoded error messages
        hardcoded_patterns = [
            r'["\'].*error.*["\']', r'["\'].*failed.*["\']', r'["\'].*invalid.*["\']'
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(Violation(
                    rule_id="R166",
                    file_path=file_path,
                    line_number=1,
                    message="Error messages should come from a centralized message catalog",
                    severity=Severity.INFO
                ))
                break
        
        return violations
    
    def _validate_ui_behavior(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R167: Keep UI responsive. Show short, actionable options: Retry / Cancel / Open Logs."""
        violations = []
        
        # This is more relevant for UI code
        if any(keyword in file_path.lower() for keyword in ['ui', 'gui', 'frontend', 'component']):
            ui_patterns = [
                r'loading.*\.\.\.', r'please.*wait', r'processing.*\.\.\.'
            ]
            
            for pattern in ui_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id="R167",
                        file_path=file_path,
                        line_number=1,
                        message="UI should show actionable options (Retry/Cancel/Open Logs) instead of generic loading",
                        severity=Severity.INFO
                    ))
                    break
        
        return violations
    
    def _validate_structured_logs(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R168: One JSON object per line with required fields."""
        violations = []
        
        # Check for structured logging
        log_patterns = [
            r'logger\.', r'logging\.', r'print\('
        ]
        
        has_logging = any(re.search(pattern, content) for pattern in log_patterns)
        
        if has_logging:
            # Check for JSON structure
            if 'json' not in content.lower() and 'structured' not in content.lower():
                violations.append(Violation(
                    rule_id="R168",
                    file_path=file_path,
                    line_number=1,
                    message="Logging should use structured JSON format",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_correlation(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R169: Propagate trace/request ids across calls."""
        violations = []
        
        # Check for correlation ID usage
        correlation_patterns = [
            r'trace.*id', r'request.*id', r'correlation.*id', r'correlationId'
        ]
        
        has_correlation = any(re.search(pattern, content, re.IGNORECASE) for pattern in correlation_patterns)
        
        if not has_correlation and ('http' in content.lower() or 'api' in content.lower()):
            violations.append(Violation(
                rule_id="R169",
                file_path=file_path,
                line_number=1,
                message="HTTP/API calls should propagate trace/request IDs",
                severity=Severity.WARNING
            ))
        
        return violations
    
    def _validate_privacy_secrets(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R170: Never log secrets or PII. Redact tokens, passwords, cookies."""
        violations = []
        
        # Check for potential secret/PII logging
        secret_patterns = [
            r'password', r'token', r'secret', r'key', r'cookie', r'authorization'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Check for redaction
                redaction_keywords = ['redact', 'mask', 'hide', '***', '****']
                has_redaction = any(keyword in content.lower() for keyword in redaction_keywords)
                
                if not has_redaction:
                    violations.append(Violation(
                        rule_id="R170",
                        file_path=file_path,
                        line_number=1,
                        message="Secrets/PII should be redacted in logs",
                        severity=Severity.ERROR
                    ))
                break
        
        return violations
    
    def _validate_failure_paths(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R171: Write tests for happy path, timeouts, 5xx errors, 4xx errors, cleanup."""
        violations = []
        
        # Check for test files
        if 'test' in file_path.lower():
            test_patterns = [
                r'test.*timeout', r'test.*5\d\d', r'test.*4\d\d', r'test.*cleanup'
            ]
            
            has_failure_tests = any(re.search(pattern, content, re.IGNORECASE) for pattern in test_patterns)
            
            if not has_failure_tests and 'error' in content.lower():
                violations.append(Violation(
                    rule_id="R171",
                    file_path=file_path,
                    line_number=1,
                    message="Tests should cover failure paths (timeouts, 5xx, 4xx, cleanup)",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_contracts_docs(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R172: Document the error envelope, code list, HTTP mapping, and examples."""
        violations = []
        
        # Check for API/contract files
        if any(keyword in file_path.lower() for keyword in ['api', 'contract', 'openapi', 'schema']):
            doc_patterns = [
                r'error.*envelope', r'error.*code', r'http.*mapping', r'example'
            ]
            
            has_docs = any(re.search(pattern, content, re.IGNORECASE) for pattern in doc_patterns)
            
            if not has_docs:
                violations.append(Violation(
                    rule_id="R172",
                    file_path=file_path,
                    line_number=1,
                    message="API contracts should document error envelope, codes, HTTP mapping, and examples",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_consistency(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R173: Prefer consistent handling over one-off fixes."""
        violations = []
        
        # Check for consistent error handling patterns
        error_patterns = [
            r'except.*:', r'raise.*Error', r'logger\.error'
        ]
        
        error_count = sum(1 for pattern in error_patterns if re.search(pattern, content))
        
        if error_count > 0:
            # Check for consistent patterns
            consistent_patterns = [
                r'handle_error', r'central.*handler', r'error.*handler'
            ]
            
            has_consistent = any(re.search(pattern, content, re.IGNORECASE) for pattern in consistent_patterns)
            
            if not has_consistent:
                violations.append(Violation(
                    rule_id="R173",
                    file_path=file_path,
                    line_number=1,
                    message="Error handling should use consistent patterns instead of one-off fixes",
                    severity=Severity.INFO
                ))
        
        return violations
    
    def _validate_safe_defaults(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R174: Default timeouts, retry caps, and user messages must be safe and configurable."""
        violations = []
        
        # Check for hardcoded values that should be configurable
        hardcoded_patterns = [
            r'timeout\s*=\s*\d+', r'retry.*=\s*\d+', r'max.*=\s*\d+'
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, content):
                violations.append(Violation(
                    rule_id="R174",
                    file_path=file_path,
                    line_number=1,
                    message="Timeouts, retry caps, and limits should be configurable, not hardcoded",
                    severity=Severity.WARNING
                ))
                break
        
        return violations
    
    def _validate_ai_transparency(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R175: AI decisions should include confidence level, reasoning, and version."""
        violations = []
        
        # Check for AI-related code
        ai_patterns = [
            r'ai\.', r'llm\.', r'model\.', r'gpt', r'claude', r'ollama'
        ]
        
        has_ai = any(re.search(pattern, content, re.IGNORECASE) for pattern in ai_patterns)
        
        if has_ai:
            transparency_keywords = ['confidence', 'reasoning', 'version', 'explanation']
            has_transparency = any(keyword in content.lower() for keyword in transparency_keywords)
            
            if not has_transparency:
                violations.append(Violation(
                    rule_id="R175",
                    file_path=file_path,
                    line_number=1,
                    message="AI decisions should include confidence level, reasoning, and version",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_ai_sandbox(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R176: AI should only work in a special 'playground' away from real computers."""
        violations = []
        
        # Check for AI code execution
        execution_patterns = [
            r'exec\(', r'eval\(', r'\.run\(', r'\.execute\('
        ]
        
        has_ai_execution = any(re.search(pattern, content) for pattern in execution_patterns)
        
        if has_ai_execution and any(keyword in content.lower() for keyword in ['ai', 'llm', 'model']):
            violations.append(Violation(
                rule_id="R176",
                file_path=file_path,
                line_number=1,
                message="AI should not execute code directly - use sandbox/playground",
                severity=Severity.ERROR
            ))
        
        return violations
    
    def _validate_ai_learning(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R177: When AI gets something wrong, it should remember and get smarter."""
        violations = []
        
        # Check for AI feedback mechanisms
        if any(keyword in content.lower() for keyword in ['ai', 'llm', 'model']):
            learning_keywords = ['feedback', 'learn', 'improve', 'mistake', 'error']
            has_learning = any(keyword in content.lower() for keyword in learning_keywords)
            
            if not has_learning:
                violations.append(Violation(
                    rule_id="R177",
                    file_path=file_path,
                    line_number=1,
                    message="AI systems should include learning from mistakes",
                    severity=Severity.INFO
                ))
        
        return violations
    
    def _validate_ai_thresholds(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R178: High confidence (>90%): Apply automatically. Medium (70-90%): Suggest. Low (<70%): Ask approval."""
        violations = []
        
        # Check for AI confidence handling
        confidence_patterns = [
            r'confidence', r'threshold', r'%\s*>\s*\d+', r'%\s*<\s*\d+'
        ]
        
        has_confidence = any(re.search(pattern, content, re.IGNORECASE) for pattern in confidence_patterns)
        
        if has_confidence:
            threshold_keywords = ['90', '70', 'automatic', 'suggest', 'approval']
            has_thresholds = any(keyword in content for keyword in threshold_keywords)
            
            if not has_thresholds:
                violations.append(Violation(
                    rule_id="R178",
                    file_path=file_path,
                    line_number=1,
                    message="AI confidence should have thresholds: >90% automatic, 70-90% suggest, <70% ask approval",
                    severity=Severity.WARNING
                ))
        
        return violations
    
    def _validate_graceful_degradation(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R179: When dependencies fail, provide reduced functionality rather than complete failure."""
        violations = []
        
        # Check for graceful degradation patterns
        degradation_keywords = ['fallback', 'degraded', 'reduced', 'partial', 'offline']
        has_degradation = any(keyword in content.lower() for keyword in degradation_keywords)
        
        if not has_degradation and 'dependency' in content.lower():
            violations.append(Violation(
                rule_id="R179",
                file_path=file_path,
                line_number=1,
                message="Dependency failures should provide graceful degradation, not complete failure",
                severity=Severity.WARNING
            ))
        
        return violations
    
    def _validate_state_recovery(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R180: After crashes or failures, systems should recover to known good states."""
        violations = []
        
        # Check for state recovery mechanisms
        recovery_keywords = ['checkpoint', 'recovery', 'restore', 'rollback', 'state']
        has_recovery = any(keyword in content.lower() for keyword in recovery_keywords)
        
        if not has_recovery and ('crash' in content.lower() or 'failure' in content.lower()):
            violations.append(Violation(
                rule_id="R180",
                file_path=file_path,
                line_number=1,
                message="Systems should have state recovery mechanisms for crashes/failures",
                severity=Severity.WARNING
            ))
        
        return violations
    
    def _validate_feature_flags(self, tree: ast.AST, file_path: str, content: str) -> List[Violation]:
        """R181: Use feature flags for risky changes with automatic rollback on error detection."""
        violations = []
        
        # Check for feature flag usage
        flag_patterns = [
            r'feature.*flag', r'feature_flag', r'flag.*enabled', r'experimental'
        ]
        
        has_flags = any(re.search(pattern, content, re.IGNORECASE) for pattern in flag_patterns)
        
        if not has_flags and ('risky' in content.lower() or 'experimental' in content.lower()):
            violations.append(Violation(
                rule_id="R181",
                file_path=file_path,
                line_number=1,
                message="Risky changes should use feature flags with automatic rollback",
                severity=Severity.WARNING
            ))
        
        return violations

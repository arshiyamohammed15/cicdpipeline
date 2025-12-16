"""
Post-Generation Validator for Constitution Rules

This module validates generated code after AI code generation occurs,
ensuring ALL Constitution rules are enforced on the actual code output.

Validates code structure, patterns, and compliance that cannot be detected
from prompt text analysis alone.
"""

import ast
import re
import tempfile
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from validator.models import Violation, Severity
from validator.core import ConstitutionValidator
from validator.utils.rule_validator import RuleNumberValidator


class PostGenerationValidator:
    """
    Validates generated code against all constitution rules using AST analysis.

    This validator parses generated code and checks for structural violations
    that pre-implementation hooks cannot detect from prompt text alone.
    """

    def __init__(self):
        """Initialize the post-generation validator."""
        self.code_validator = ConstitutionValidator()
        self.rule_validator = RuleNumberValidator()

        # Load rules dynamically from JSON files
        self._load_rule_references()

    def _load_rule_references(self):
        """
        Load rule references dynamically from JSON files by searching for rules by title/keywords.

        This prevents hardcoding rule numbers and adapts to changes in constitution files.
        """
        constitution_dir = Path("docs/constitution")
        if not constitution_dir.exists():
            raise FileNotFoundError(f"Constitution directory not found: {constitution_dir}")

        json_files = list(constitution_dir.glob("*.json"))
        all_rules = []

        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('constitution_rules', [])
                all_rules.extend(rules)

        # Look up rules by title keywords dynamically
        self.rule_file_header = self._find_rule_by_keywords(all_rules, ['File Headers', 'Comprehensive', 'Header'])
        self.rule_async_await = self._find_rule_by_keywords(all_rules, ['async', 'await', 'Advanced Programming'])
        self.rule_decorators = self._find_rule_by_keywords(all_rules, ['decorator', 'Advanced Programming'])
        self.rule_structured_logs = self._find_rule_by_keywords(all_rules, ['Structured Logs', 'JSON format'])
        self.rule_service_identification = self._find_rule_by_keywords(all_rules, ['Service Identification', 'service metadata'])
        self.rule_log_level_enum = self._find_rule_by_keywords(all_rules, ['Log Level', 'Enumeration', 'TRACE', 'DEBUG'])
        self.rule_error_envelope = self._find_rule_by_keywords(all_rules, ['Error Envelope', 'error', 'code', 'message'])
        self.rule_trace_context = self._find_rule_by_keywords(all_rules, ['Trace Context', 'W3C', 'traceId', 'spanId'])
        self.rule_monotonic_time = self._find_rule_by_keywords(all_rules, ['Monotonic', 'Time'])

    def _find_rule_by_keywords(self, rules: List[Dict], keywords: List[str]) -> Optional[Dict]:
        """
        Find a rule by searching for keywords in title or description.

        Args:
            rules: List of all rules
            keywords: List of keywords to search for

        Returns:
            Rule dictionary if found, None otherwise
        """
        for rule in rules:
            title = rule.get('title', '').lower()
            description = rule.get('description', '').lower()

            # Check if any keyword matches
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in description:
                    return rule

        return None

    def validate_generated_code(
        self,
        code: str,
        file_type: str = "python",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate generated code against all constitution rules.

        Args:
            code: Generated code string to validate
            file_type: Type of file (python, typescript, etc.)
            file_path: Optional file path for context

        Returns:
            Validation result with violations and recommendations
        """
        if file_type not in ["python", "py"]:
            # TypeScript validation would require different parser
            return {
                'valid': True,
                'violations': [],
                'message': f'Post-generation validation not yet implemented for {file_type}'
            }

        # Create temporary file for validation
        temp_file = None
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name

            # Validate using existing ConstitutionValidator
            validation_result = self.code_validator.validate_file(temp_file)

            # Extract violations
            violations = validation_result.violations

            # Check for specific structural violations
            structural_violations = self._check_structural_violations(code, temp_file)
            violations.extend(structural_violations)

            # Format violations
            formatted_violations = self._format_violations(violations)

            return {
                'valid': len(violations) == 0,
                'violations': formatted_violations,
                'total_violations': len(violations),
                'violations_by_severity': self._count_by_severity(violations),
                'compliance_score': validation_result.compliance_score,
                'message': f'Validated {len(violations)} violations in generated code'
            }

        except SyntaxError as e:
            # Handle syntax errors
            violation = Violation(
                rule_id="SYNTAX_ERROR",
                rule_name="Syntax Error in Generated Code",
                severity=Severity.ERROR,
                message=f"Generated code has syntax error: {e.msg}",
                file_path=file_path or "generated_code",
                line_number=e.lineno or 0,
                code_snippet=code.split('\n')[e.lineno - 1] if e.lineno else "",
                fix_suggestion="Fix syntax errors in generated code"
            )
            return {
                'valid': False,
                'violations': [self._format_violation(violation)],
                'total_violations': 1,
                'violations_by_severity': {'ERROR': 1},
                'compliance_score': 0.0,
                'message': 'Generated code has syntax errors'
            }
        except Exception as e:
            return {
                'valid': False,
                'violations': [],
                'total_violations': 0,
                'violations_by_severity': {},
                'compliance_score': 0.0,
                'error': str(e),
                'message': f'Error validating generated code: {e}'
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Failed to remove temporary file {temp_file}: {e}", exc_info=True)

    def _check_structural_violations(
        self,
        code: str,
        file_path: str
    ) -> List[Violation]:
        """
        Check for structural violations that require code analysis.

        Args:
            code: Generated code string
            file_path: Path to code file

        Returns:
            List of violations found
        """
        violations = []

        try:
            tree = ast.parse(code, filename=file_path)
        except SyntaxError:
            # Syntax errors handled separately
            return violations

        # Check for file header
        header_violation = self._check_file_header(code)
        if header_violation:
            violations.append(header_violation)

        # Check for async/await usage
        async_violations = self._check_async_await(tree, code, file_path)
        violations.extend(async_violations)

        # Check for decorator usage
        decorator_violations = self._check_decorators(tree, code, file_path)
        violations.extend(decorator_violations)

        # Check for logging format
        logging_violations = self._check_logging_format(code, file_path)
        violations.extend(logging_violations)

        # Check for error envelope structure
        error_envelope_violations = self._check_error_envelope(code, file_path)
        violations.extend(error_envelope_violations)

        # Check for W3C trace context
        trace_context_violations = self._check_trace_context(code, file_path)
        violations.extend(trace_context_violations)

        # Check for type hints (Rule compliance)
        type_hint_violations = self._check_type_hints(tree, file_path)
        violations.extend(type_hint_violations)

        return violations

    def _check_file_header(self, code: str) -> Optional[Violation]:
        """
        Check if file has comprehensive header.

        Args:
            code: Generated code string

        Returns:
            Violation if header missing, None otherwise
        """
        # If rule not found, skip this check
        if not self.rule_file_header:
            return None

        lines = code.split('\n')
        if len(lines) < 10:
            return None

        # Check first 20 lines for header structure
        header_section = '\n'.join(lines[:20]).lower()

        # Required sections: What, Why, Reads/Writes, Contracts, Risks
        required_sections = ['what', 'why']
        found_sections = []

        for section in required_sections:
            if section in header_section:
                found_sections.append(section)

        # Check if header looks comprehensive (has docstring with multiple lines)
        has_docstring = False
        if lines[0].strip().startswith('"""') or lines[0].strip().startswith("'''"):
            # Check if docstring spans multiple lines
            docstring_end = 1
            for i, line in enumerate(lines[1:], 1):
                if '"""' in line or "'''" in line:
                    docstring_end = i + 1
                    break
            if docstring_end > 5:  # Multi-line docstring
                has_docstring = True

        # If no comprehensive header found
        if not has_docstring or len(found_sections) < len(required_sections):
            rule_id = self.rule_file_header.get('rule_id', 'UNKNOWN')
            rule_number = self.rule_file_header.get('rule_number', 0)
            rule_name = self.rule_file_header.get('title', 'File Headers')
            return Violation(
                rule_id=rule_id,
                rule_name=rule_name,
                rule_number=rule_number,
                severity=Severity.ERROR,
                message="Generated code missing comprehensive file header with What/Why/Reads-Writes/Contracts/Risks sections",
                file_path="generated_code",
                line_number=1,
                code_snippet=lines[0] if lines else "",
                fix_suggestion="Add comprehensive file header with What, Why, Reads/Writes, Contracts, and Risks sections"
            )

        return None

    def _check_async_await(self, tree: ast.AST, code: str, file_path: str) -> List[Violation]:
        """
        Check for async/await usage.

        Args:
            tree: AST tree
            code: Generated code string
            file_path: File path

        Returns:
            List of violations
        """
        violations = []

        # If rule not found, skip this check
        if not self.rule_async_await:
            return violations

        rule_id = self.rule_async_await.get('rule_id', 'UNKNOWN')
        rule_number = self.rule_async_await.get('rule_number', 0)
        rule_name = self.rule_async_await.get('title', 'NO Advanced Programming Concepts')

        # Get code lines for context checking
        code_lines = code.split('\n')

        for node in ast.walk(tree):
            # Check for async function definitions
            if isinstance(node, ast.AsyncFunctionDef):
                # Check if it's framework-required (middleware, ASGI)
                # Get function context from code
                func_start = max(0, node.lineno - 1)
                func_end = min(len(code_lines), node.lineno + 10)
                func_context = '\n'.join(code_lines[func_start:func_end]).lower()

                is_framework_required = (
                    'middleware' in func_context or
                    'dispatch' in node.name.lower() or
                    'asgi' in func_context or
                    'basehttpmiddleware' in func_context
                )

                if not is_framework_required:
                    violations.append(Violation(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        rule_number=rule_number,
                        severity=Severity.ERROR,
                        message=f"Generated code uses async/await in {node.name}. Use sync functions unless framework-required.",
                        file_path=file_path,
                        line_number=node.lineno,
                        code_snippet=f"async def {node.name}",
                        fix_suggestion="Convert to sync function unless framework-required (e.g., ASGI middleware)"
                    ))

            # Check for await expressions
            if isinstance(node, ast.Await):
                # Check context - might be in framework-required async function
                parent = self._get_parent_function(node, tree)
                if parent and isinstance(parent, ast.AsyncFunctionDef):
                    func_start = max(0, parent.lineno - 1)
                    func_end = min(len(code_lines), parent.lineno + 10)
                    parent_context = '\n'.join(code_lines[func_start:func_end]).lower()

                    is_framework_required = (
                        'middleware' in parent_context or
                        'dispatch' in parent.name.lower() or
                        'basehttpmiddleware' in parent_context
                    )

                    if not is_framework_required:
                        violations.append(Violation(
                            rule_id=rule_id,
                            rule_name=rule_name,
                            rule_number=rule_number,
                            severity=Severity.ERROR,
                            message=f"Generated code uses await expression",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet="await ...",
                            fix_suggestion="Remove await or convert to sync function unless framework-required"
                        ))

        return violations

    def _check_decorators(self, tree: ast.AST, code: str, file_path: str) -> List[Violation]:
        """
        Check for decorator usage.

        Args:
            tree: AST tree
            code: Generated code string
            file_path: File path

        Returns:
            List of violations
        """
        violations = []

        # If rule not found, skip this check
        if not self.rule_decorators:
            return violations

        rule_id = self.rule_decorators.get('rule_id', 'UNKNOWN')
        rule_number = self.rule_decorators.get('rule_number', 0)
        rule_name = self.rule_decorators.get('title', 'NO Advanced Programming Concepts')

        # Get code lines for context checking
        code_lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.decorator_list:
                    for decorator in node.decorator_list:
                        # Get decorator line from code
                        decorator_line = ""
                        if hasattr(decorator, 'lineno') and decorator.lineno <= len(code_lines):
                            decorator_line = code_lines[decorator.lineno - 1].strip()

                        # Check if it's framework-required (FastAPI routes)
                        is_framework_required = (
                            '@router.' in decorator_line or
                            '@app.' in decorator_line or
                            'router.post' in decorator_line or
                            'router.get' in decorator_line or
                            'router.put' in decorator_line or
                            'router.delete' in decorator_line
                        )

                        if not is_framework_required:
                            violations.append(Violation(
                                rule_id=rule_id,
                                rule_name=rule_name,
                                rule_number=rule_number,
                                severity=Severity.ERROR,
                                message=f"Generated code uses decorator {decorator_line}. Use only framework-required decorators.",
                                file_path=file_path,
                                line_number=decorator.lineno if hasattr(decorator, 'lineno') else node.lineno,
                                code_snippet=decorator_line,
                                fix_suggestion="Remove decorator unless framework-required (e.g., FastAPI route decorators)"
                            ))

        return violations

    def _check_logging_format(self, code: str, file_path: str) -> List[Violation]:
        """
        Check logging format.

        Args:
            code: Generated code string
            file_path: File path

        Returns:
            List of violations
        """
        violations = []
        lines = code.split('\n')

        # Check for logger calls
        has_logging = False
        has_structured_logging = False
        has_service_metadata = False
        has_log_level_enum = False

        for i, line in enumerate(lines, 1):
            if 'logger.' in line.lower() or 'logging.' in line.lower():
                has_logging = True

                # Check for JSON format
                if 'json.dumps' in line or 'json.dump' in line:
                    has_structured_logging = True

                # Check for service metadata
                if any(field in line for field in ['service', 'version', 'env', 'host']):
                    has_service_metadata = True

                # Check for log level enumeration
                log_levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
                if any(level in line.upper() for level in log_levels):
                    has_log_level_enum = True

        if has_logging:
            if not has_structured_logging and self.rule_structured_logs:
                rule = self.rule_structured_logs
                violations.append(Violation(
                    rule_id=rule.get('rule_id', 'UNKNOWN'),
                    rule_name=rule.get('title', 'Structured Logs'),
                    rule_number=rule.get('rule_number', 0),
                    severity=Severity.ERROR,
                    message="Generated code has logging but not in JSON format",
                    file_path=file_path,
                    line_number=1,
                    code_snippet="logger.info(...)",
                    fix_suggestion="Use json.dumps() for structured JSON logging with timestamp, level, service, operation, error.code, trace/request ids, duration, attempt, retryable, severity, cause"
                ))

            if not has_service_metadata and self.rule_service_identification:
                rule = self.rule_service_identification
                violations.append(Violation(
                    rule_id=rule.get('rule_id', 'UNKNOWN'),
                    rule_name=rule.get('title', 'Require Service Identification'),
                    rule_number=rule.get('rule_number', 0),
                    severity=Severity.ERROR,
                    message="Generated code has logging but missing service metadata (service, version, env, host)",
                    file_path=file_path,
                    line_number=1,
                    code_snippet="logger.info(...)",
                    fix_suggestion="Include service, version, env, host in all log entries"
                ))

            if not has_log_level_enum and self.rule_log_level_enum:
                rule = self.rule_log_level_enum
                violations.append(Violation(
                    rule_id=rule.get('rule_id', 'UNKNOWN'),
                    rule_name=rule.get('title', 'Enforce Log Level Enumeration'),
                    rule_number=rule.get('rule_number', 0),
                    severity=Severity.ERROR,
                    message="Generated code has logging but missing standardized log levels (TRACE|DEBUG|INFO|WARN|ERROR|FATAL)",
                    file_path=file_path,
                    line_number=1,
                    code_snippet="logger.info(...)",
                    fix_suggestion="Use standardized log levels: TRACE|DEBUG|INFO|WARN|ERROR|FATAL"
                ))

        return violations

    def _check_error_envelope(self, code: str, file_path: str) -> List[Violation]:
        """
        Check error envelope structure.

        Args:
            code: Generated code string
            file_path: File path

        Returns:
            List of violations
        """
        violations = []

        # If rule not found, skip this check
        if not self.rule_error_envelope:
            return violations

        # Check for HTTPException usage
        if 'HTTPException' in code:
            # Check if error envelope structure is used
            has_error_envelope = (
                '"error"' in code and
                '"code"' in code and
                '"message"' in code
            )

            if not has_error_envelope:
                rule = self.rule_error_envelope
                violations.append(Violation(
                    rule_id=rule.get('rule_id', 'UNKNOWN'),
                    rule_name=rule.get('title', 'Error Envelope'),
                    rule_number=rule.get('rule_number', 0),
                    severity=Severity.ERROR,
                    message="Generated code uses HTTPException but not error envelope structure",
                    file_path=file_path,
                    line_number=1,
                    code_snippet="HTTPException(...)",
                    fix_suggestion="Use error envelope structure: {'error': {'code': '...', 'message': '...', 'details': ...}}"
                ))

        return violations

    def _check_trace_context(self, code: str, file_path: str) -> List[Violation]:
        """
        Check W3C trace context.

        Args:
            code: Generated code string
            file_path: File path

        Returns:
            List of violations
        """
        violations = []

        # If rule not found, skip this check
        if not self.rule_trace_context:
            return violations

        # Check if code has request logging but missing trace context
        has_request_logging = 'request.start' in code.lower() or 'request.end' in code.lower()
        has_trace_context = (
            'traceid' in code.lower() or
            'trace_id' in code.lower() or
            'spanid' in code.lower() or
            'span_id' in code.lower() or
            'parentspanid' in code.lower() or
            'parent_span_id' in code.lower()
        )

        if has_request_logging and not has_trace_context:
            rule = self.rule_trace_context
            violations.append(Violation(
                rule_id=rule.get('rule_id', 'UNKNOWN'),
                rule_name=rule.get('title', 'Enforce Distributed Tracing Context'),
                rule_number=rule.get('rule_number', 0),
                severity=Severity.ERROR,
                message="Generated code has request logging but missing W3C trace context (traceId, spanId, parentSpanId)",
                file_path=file_path,
                line_number=1,
                code_snippet="request.start",
                fix_suggestion="Include traceId, spanId, parentSpanId in request logging per W3C trace context"
            ))

        return violations

    def _check_type_hints(self, tree: ast.AST, file_path: str) -> List[Violation]:
        """
        Check for type hints on functions.

        Args:
            tree: AST tree
            file_path: File path

        Returns:
            List of violations
        """
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has return type hint
                if node.returns is None:
                    # Skip if it's __init__ or private method
                    if not node.name.startswith('_'):
                        violations.append(Violation(
                            rule_id="TYPE_HINT_MISSING",
                            rule_name="Missing Type Hints",
                            severity=Severity.WARNING,
                            message=f"Function {node.name} missing return type hint",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}",
                            fix_suggestion="Add return type hint to function"
                        ))

        return violations

    def _get_parent_function(self, node: ast.AST, tree: ast.AST) -> Optional[ast.FunctionDef]:
        """
        Get parent function of a node.

        Args:
            node: AST node
            tree: AST tree

        Returns:
            Parent function node or None
        """
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if child == node:
                        return parent
        return None

    def _format_violations(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """
        Format violations for response.

        Args:
            violations: List of violations

        Returns:
            Formatted violations
        """
        return [self._format_violation(v) for v in violations]

    def _format_violation(self, violation: Violation) -> Dict[str, Any]:
        """
        Format single violation.

        Args:
            violation: Violation object

        Returns:
            Formatted violation dict
        """
        return {
            'rule_id': violation.rule_id,
            'rule_number': getattr(violation, 'rule_number', 0),
            'severity': violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
            'message': violation.message,
            'file_path': violation.file_path,
            'line_number': getattr(violation, 'line_number', 0),
            'code_snippet': getattr(violation, 'code_snippet', ''),
            'fix_suggestion': getattr(violation, 'fix_suggestion', '')
        }

    def _count_by_severity(self, violations: List[Violation]) -> Dict[str, int]:
        """
        Count violations by severity.

        Args:
            violations: List of violations

        Returns:
            Count by severity
        """
        counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0}
        for v in violations:
            severity_str = v.severity.value if hasattr(v.severity, 'value') else str(v.severity)
            if severity_str in counts:
                counts[severity_str] += 1
        return counts

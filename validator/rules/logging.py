"""
Logging Constitution Validator

Validates compliance with the ZeroUI 2.0 Logging Constitution.
Covers structured logging, trace context, and log management.
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Violation, Severity


class LoggingValidator:
    """Validates logging standards and practices."""
    
    def __init__(self):
        self.rules = {
            'R043': self._validate_structured_logging,
            'R044': self._validate_log_levels,
            'R063': self._validate_log_format,
            'R064': self._validate_log_context,
            'R065': self._validate_log_correlation,
            'R066': self._validate_log_retention,
            'R067': self._validate_log_rotation,
            'R068': self._validate_log_monitoring,
            'R069': self._validate_log_alerting,
            'R070': self._validate_log_analysis,
            'R071': self._validate_log_security,
            'R072': self._validate_log_performance,
            'R073': self._validate_log_testing,
            'R074': self._validate_log_documentation,
            'R075': self._validate_log_compliance
        }
        
        # Valid log levels
        self.valid_log_levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
        
        # Required log fields
        self.required_fields = [
            'timestamp', 'level', 'message', 'service', 'version', 'env', 'host'
        ]
        
        # Trace context fields
        self.trace_fields = ['traceId', 'spanId', 'parentSpanId']
    
    def validate(self, file_path: str, content: str) -> List[Violation]:
        """Validate logging compliance for a file."""
        violations = []
        
        # Check for structured logging
        violations.extend(self._validate_structured_logging(content, file_path))
        
        # Check for log levels
        violations.extend(self._validate_log_levels(content, file_path))
        
        # Check for log format
        violations.extend(self._validate_log_format(content, file_path))
        
        # Check for log context
        violations.extend(self._validate_log_context(content, file_path))
        
        # Check for log correlation
        violations.extend(self._validate_log_correlation(content, file_path))
        
        # Check for log security
        violations.extend(self._validate_log_security(content, file_path))
        
        # Check for log performance
        violations.extend(self._validate_log_performance(content, file_path))
        
        # Check for log testing
        violations.extend(self._validate_log_testing(content, file_path))
        
        # Check for log documentation
        violations.extend(self._validate_log_documentation(content, file_path))
        
        # Check for log compliance
        violations.extend(self._validate_log_compliance(content, file_path))
        
        return violations
    
    def _validate_structured_logging(self, content: str, file_path: str) -> List[Violation]:
        """Validate structured logging implementation."""
        violations = []
        
        # Check for logging statements
        if 'log' in content.lower() or 'logger' in content.lower():
            # Check for JSON structure
            if 'json' not in content.lower() and 'structured' not in content.lower():
                violations.append(Violation(
                        rule_id='R043',
                        rule_name='Logs are structured JSON with required fields and schema version',
                        severity=Severity.ERROR,
                        message='Logs are structured JSON with required fields and schema version',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
                
                    ))
            
            # Check for required fields
            missing_fields = []
            for field in self.required_fields:
                if field not in content.lower():
                    missing_fields.append(field)
            
            if missing_fields:
                violations.append(Violation(
                    rule_id='R043',
                    rule_name=f'Missing required log fields: {", ".join(missing_fields)}',
                    severity=Severity.ERROR,
                    message=f'Missing required log fields: {", ".join(missing_fields)}',
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="",
                    category='logging'
                ))
        
        return violations
    
    def _validate_log_levels(self, content: str, file_path: str) -> List[Violation]:
        """Validate log level usage."""
        violations = []
        
        # Check for invalid log levels
        log_level_pattern = r'\.(trace|debug|info|warn|error|fatal)\s*\('
        for match in re.finditer(log_level_pattern, content, re.IGNORECASE):
            log_level = match.group(1).upper()
            if log_level not in self.valid_log_levels:
                violations.append(Violation(
                        rule_id='R044',
                        rule_name=f'Invalid log level "{log_level}" - use TRACE|DEBUG|INFO|WARN|ERROR|FATAL',
                        severity=Severity.WARNING,
                        message=f'Invalid log level "{log_level}" - use TRACE|DEBUG|INFO|WARN|ERROR|FATAL',
                        file_path=file_path,
                        line_number=content[:match.start()].count('\n') + 1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
                
                    ))
        
        return violations
    
    def _validate_log_format(self, content: str, file_path: str) -> List[Violation]:
        """Validate log format (JSONL)."""
        violations = []
        
        # Check for JSONL format
        if 'log' in content.lower():
            # Look for log statements that should be JSONL
            log_patterns = [
                r'logger\.(info|debug|warn|error|fatal)\s*\(',
                r'log\.(info|debug|warn|error|fatal)\s*\(',
                r'print\s*\('
            ]
            
            for pattern in log_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    # Check if the log statement is properly formatted
                    log_start = match.start()
                    log_end = content.find(')', log_start)
                    if log_end != -1:
                        log_content = content[log_start:log_end]
                        if not self._is_jsonl_format(log_content):
                            violations.append(Violation(
                        rule_id='R063',
                        rule_name='ONE JSON object per line (JSONL) with ISO-8601 UTC timestamps',
                        severity=Severity.ERROR,
                        message='ONE JSON object per line (JSONL) with ISO-8601 UTC timestamps',
                        file_path=file_path,
                        line_number=content[:log_start].count('\n') + 1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
                            
                    ))
        
        return violations
    
    def _validate_log_context(self, content: str, file_path: str) -> List[Violation]:
        """Validate log context and timestamps."""
        violations = []
        
        # Check for monotonic time
        if 'log' in content.lower() and 'monotonic_hw_time_ms' not in content.lower():
            violations.append(Violation(
                        rule_id='R064',
                        rule_name='Include monotonic_hw_time_ms for ordering; UTF-8 encoding only',
                        severity=Severity.ERROR,
                        message='Include monotonic_hw_time_ms for ordering; UTF-8 encoding only',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        # Check for ISO-8601 timestamps
        if 'timestamp' in content.lower() and 'iso' not in content.lower():
            violations.append(Violation(
                        rule_id='R064',
                        rule_name='Use ISO-8601 UTC timestamps',
                        severity=Severity.WARNING,
                        message='Use ISO-8601 UTC timestamps',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        return violations
    
    def _validate_log_correlation(self, content: str, file_path: str) -> List[Violation]:
        """Validate log correlation and trace context."""
        violations = []
        
        # Check for trace context fields
        if 'log' in content.lower():
            missing_trace_fields = []
            for field in self.trace_fields:
                if field not in content.lower():
                    missing_trace_fields.append(field)
            
            if missing_trace_fields:
                violations.append(Violation(
                    rule_id='R065',
                    file_path=file_path,
                    line_number=1,
                    message=f'Include traceId, spanId, parentSpanId (W3C trace context) - missing: {", ".join(missing_trace_fields)}',
                    severity=Severity.ERROR,
                    category='logging'
                ))
        
        return violations
    
    def _validate_log_retention(self, content: str, file_path: str) -> List[Violation]:
        """Validate log retention policies."""
        violations = []
        
        # Check for retention configuration
        if 'log' in content.lower() and 'retention' not in content.lower():
            violations.append(Violation(
                        rule_id='R066',
                        rule_name='App logs ≥ 14 days locally; receipts ≥ 90 days',
                        severity=Severity.WARNING,
                        message='App logs ≥ 14 days locally; receipts ≥ 90 days',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        return violations
    
    def _validate_log_rotation(self, content: str, file_path: str) -> List[Violation]:
        """Validate log rotation policies."""
        violations = []
        
        # Check for rotation configuration
        if 'log' in content.lower() and 'rotation' not in content.lower():
            violations.append(Violation(
                        rule_id='R067',
                        rule_name='Rotate at 100MB; keep last 10 files locally',
                        severity=Severity.WARNING,
                        message='Rotate at 100MB; keep last 10 files locally',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        return violations
    
    def _validate_log_monitoring(self, content: str, file_path: str) -> List[Violation]:
        """Validate log monitoring fields."""
        violations = []
        
        # Check for monitoring fields
        if 'log' in content.lower():
            monitoring_fields = ['service', 'version', 'env', 'host']
            missing_fields = []
            
            for field in monitoring_fields:
                if field not in content.lower():
                    missing_fields.append(field)
            
            if missing_fields:
                violations.append(Violation(
                    rule_id='R068',
                    file_path=file_path,
                    line_number=1,
                    message=f'Include service, version, env, host in all logs - missing: {", ".join(missing_fields)}',
                    severity=Severity.ERROR,
                    category='logging'
                ))
        
        return violations
    
    def _validate_log_alerting(self, content: str, file_path: str) -> List[Violation]:
        """Validate log alerting and event names."""
        violations = []
        
        # Check for stable event names
        if 'log' in content.lower():
            stable_events = ['request.start', 'request.end', 'db.query', 'external.call']
            has_stable_events = any(event in content.lower() for event in stable_events)
            
            if not has_stable_events:
                violations.append(Violation(
                    rule_id='R069',
                    file_path=file_path,
                    line_number=1,
                    message='Use stable event names: request.start/end, db.query, external.call',
                    severity=Severity.ERROR,
                    category='logging'
                ))
        
        return violations
    
    def _validate_log_analysis(self, content: str, file_path: str) -> List[Violation]:
        """Validate log analysis and workflow correlation."""
        violations = []
        
        # Check for workflow correlation fields
        if 'log' in content.lower():
            analysis_fields = ['event_id', 'caused_by', 'links']
            missing_fields = []
            
            for field in analysis_fields:
                if field not in content.lower():
                    missing_fields.append(field)
            
            if missing_fields:
                violations.append(Violation(
                    rule_id='R070',
                    file_path=file_path,
                    line_number=1,
                    message=f'Include event_id, caused_by, links[] for workflow correlation - missing: {", ".join(missing_fields)}',
                    severity=Severity.WARNING,
                    category='logging'
                ))
        
        return violations
    
    def _validate_log_security(self, content: str, file_path: str) -> List[Violation]:
        """Validate log security and PII protection."""
        violations = []
        
        # Check for PII in logs
        pii_patterns = [
            r'(?i)(password|secret|key|token|pii)\s*[:=]\s*["\'][^"\']+["\']',
            r'(?i)(password|secret|key|token|pii)\s*[:=]\s*[^\\s]+',
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in pii_patterns:
                if re.search(pattern, line):
                    violations.append(Violation(
                        rule_id='R071',
                        file_path=file_path,
                        line_number=line_num,
                        message='Never log secrets/PII; redact tokens, passwords, keys',
                        severity=Severity.ERROR,
                        category='logging'
                    ))
        
        return violations
    
    def _validate_log_performance(self, content: str, file_path: str) -> List[Violation]:
        """Validate log performance and sampling."""
        violations = []
        
        # Check for performance considerations
        if 'log' in content.lower():
            if 'sampling' not in content.lower() and 'performance' not in content.lower():
                violations.append(Violation(
                        rule_id='R072',
                        rule_name='Logging overhead < 5% CPU; sampling for chatty events',
                        severity=Severity.WARNING,
                        message='Logging overhead < 5% CPU; sampling for chatty events',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
                
                    ))
        
        return violations
    
    def _validate_log_testing(self, content: str, file_path: str) -> List[Violation]:
        """Validate log testing."""
        violations = []
        
        # Check for log testing
        if 'log' in content.lower() and 'test' not in content.lower():
            violations.append(Violation(
                        rule_id='R073',
                        rule_name='Test log generation and validation in unit tests',
                        severity=Severity.WARNING,
                        message='Test log generation and validation in unit tests',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        return violations
    
    def _validate_log_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Validate log documentation."""
        violations = []
        
        # Check for log documentation
        if 'log' in content.lower() and 'schema' not in content.lower():
            violations.append(Violation(
                        rule_id='R074',
                        rule_name='Document logging schema and field meanings',
                        severity=Severity.WARNING,
                        message='Document logging schema and field meanings',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
            
                    ))
        
        return violations
    
    def _validate_log_compliance(self, content: str, file_path: str) -> List[Violation]:
        """Validate log compliance."""
        violations = []
        
        # Check for compliance indicators
        if 'log' in content.lower():
            compliance_keywords = ['compliance', 'audit', 'standard', 'requirement']
            has_compliance = any(keyword in content.lower() for keyword in compliance_keywords)
            
            if not has_compliance:
                violations.append(Violation(
                        rule_id='R075',
                        rule_name='Ensure logs meet compliance requirements and audit standards',
                        severity=Severity.WARNING,
                        message='Ensure logs meet compliance requirements and audit standards',
                        file_path=file_path,
                        line_number=1,
                        column_number=0,
                        code_snippet="",
                        category='logging'
                
                    ))
        
        return violations
    
    def _is_jsonl_format(self, log_content: str) -> bool:
        """Check if log content is in JSONL format."""
        # Simple check for JSON-like structure
        if '{' in log_content and '}' in log_content:
            # Try to parse as JSON
            try:
                # Extract JSON part from log statement
                json_start = log_content.find('{')
                json_end = log_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_part = log_content[json_start:json_end]
                    json.loads(json_part)
                    return True
            except json.JSONDecodeError:
                pass
        
        return False

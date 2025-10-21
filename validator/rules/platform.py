"""
Platform rule validator.

This module implements validation for platform rules:
- Rule 42: Use All Platform Features
- Rule 43: Process Data Quickly
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class PlatformValidator:
    """
    Validates platform integration and performance rules.
    
    This class focuses on detecting platform feature usage and
    data processing performance patterns.
    """
    
    def __init__(self):
        """Initialize the platform validator."""
        self.platform_features = [
            'logging', 'logger', 'log', 'monitor', 'telemetry', 'metrics',
            'config', 'configuration', 'settings', 'alert', 'notification',
            'backup', 'deploy', 'deployment', 'api', 'health', 'status'
        ]
        self.performance_patterns = [
            'stream', 'batch', 'async', 'await', 'thread', 'process',
            'cache', 'memoize', 'lazy', 'defer', 'queue', 'buffer'
        ]
        self.blocking_operations = [
            'time.sleep', 'input', 'raw_input', 'getpass', 'subprocess.call',
            'os.system', 'requests.get', 'urllib.request.urlopen'
        ]
        
    def validate_platform_features(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for platform feature usage (Rule 42).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of platform feature violations
        """
        violations = []
        
        # Check for logging usage
        has_logging = any(pattern in content.lower() for pattern in ['logging', 'logger', 'log'])
        if not has_logging:
            violations.append(Violation(
                rule_id="rule_42",
                rule_number=42,
                rule_name="Use All Platform Features",
                severity=Severity.WARNING,
                message="No logging detected - use platform logging features",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Logging",
                fix_suggestion="Add proper logging for monitoring and debugging"
            ))
        
        # Check for monitoring/telemetry
        has_monitoring = any(pattern in content.lower() for pattern in ['monitor', 'telemetry', 'metrics', 'stats'])
        if not has_monitoring:
            violations.append(Violation(
                rule_id="rule_42",
                rule_number=42,
                rule_name="Use All Platform Features",
                severity=Severity.INFO,
                message="No monitoring/telemetry detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Monitoring",
                fix_suggestion="Add monitoring and telemetry for system health"
            ))
        
        # Check for configuration management
        has_config = any(pattern in content.lower() for pattern in ['config', 'configuration', 'settings'])
        if not has_config:
            violations.append(Violation(
                rule_id="rule_42",
                rule_number=42,
                rule_name="Use All Platform Features",
                severity=Severity.INFO,
                message="No configuration management detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Configuration",
                fix_suggestion="Use platform configuration management features"
            ))
        
        # Check for error tracking
        has_error_tracking = any(pattern in content.lower() for pattern in ['error', 'exception', 'traceback', 'stack'])
        if not has_error_tracking:
            violations.append(Violation(
                rule_id="rule_42",
                rule_number=42,
                rule_name="Use All Platform Features",
                severity=Severity.WARNING,
                message="No error tracking detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Error tracking",
                fix_suggestion="Add proper error tracking and reporting"
            ))
        
        # Check for health/status reporting
        has_health = any(pattern in content.lower() for pattern in ['health', 'status', 'ping', 'heartbeat'])
        if not has_health:
            violations.append(Violation(
                rule_id="rule_42",
                rule_number=42,
                rule_name="Use All Platform Features",
                severity=Severity.INFO,
                message="No health/status reporting detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Health monitoring",
                fix_suggestion="Add health and status reporting endpoints"
            ))
        
        return violations
    
    def validate_data_processing_speed(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for data processing performance (Rule 43).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of performance violations
        """
        violations = []
        
        # Check for blocking operations
        blocking_operations_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                for blocking_op in self.blocking_operations:
                    if blocking_op in func_name:
                        blocking_operations_found.append(func_name)
        
        if blocking_operations_found:
            violations.append(Violation(
                rule_id="rule_43",
                rule_number=43,
                rule_name="Process Data Quickly",
                severity=Severity.WARNING,
                message=f"Blocking operations detected: {blocking_operations_found}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(blocking_operations_found),
                fix_suggestion="Use non-blocking alternatives for better performance"
            ))
        
        # Check for inefficient data processing patterns
        inefficient_patterns = []
        
        # Check for nested loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        inefficient_patterns.append("nested loops")
                        break
        
        # Check for large data processing without streaming
        has_large_data = any(pattern in content.lower() for pattern in ['load_all', 'read_all', 'fetch_all'])
        has_streaming = any(pattern in content.lower() for pattern in ['stream', 'iterator', 'yield', 'generator'])
        
        if has_large_data and not has_streaming:
            inefficient_patterns.append("large data without streaming")
        
        if inefficient_patterns:
            violations.append(Violation(
                rule_id="rule_43",
                rule_number=43,
                rule_name="Process Data Quickly",
                severity=Severity.WARNING,
                message=f"Inefficient data processing patterns: {inefficient_patterns}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(inefficient_patterns),
                fix_suggestion="Use streaming and batch processing for large datasets"
            ))
        
        # Check for missing performance optimizations
        has_optimizations = any(pattern in content.lower() for pattern in self.performance_patterns)
        if not has_optimizations:
            violations.append(Violation(
                rule_id="rule_43",
                rule_number=43,
                rule_name="Process Data Quickly",
                severity=Severity.INFO,
                message="No performance optimization patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Performance optimization",
                fix_suggestion="Add caching, streaming, or async processing for better performance"
            ))
        
        # Check for data quality validation during processing
        has_quality_checks = any(pattern in content.lower() for pattern in ['validate', 'check', 'verify', 'sanitize'])
        if not has_quality_checks:
            violations.append(Violation(
                rule_id="rule_43",
                rule_number=43,
                rule_name="Process Data Quickly",
                severity=Severity.INFO,
                message="No data quality checks during processing",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Data quality",
                fix_suggestion="Add data quality validation during processing"
            ))
        
        return violations
    
    def validate_context_aware_help(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for context-aware assistance (Rule 44).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of context-aware help violations
        """
        violations = []
        
        # Check for context-aware assistance patterns
        context_patterns = ['context', 'situation', 'when', 'if', 'based_on', 'depending']
        has_context = any(pattern in content.lower() for pattern in context_patterns)
        
        if not has_context:
            violations.append(Violation(
                rule_id="rule_44",
                rule_number=44,
                rule_name="Help Without Interrupting",
                severity=Severity.INFO,
                message="No context-aware assistance patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Context awareness",
                fix_suggestion="Add context-aware help that appears when needed"
            ))
        
        # Check for progressive help patterns
        progressive_patterns = ['progressive', 'gradual', 'step', 'level', 'tier', 'advanced']
        has_progressive = any(pattern in content.lower() for pattern in progressive_patterns)
        
        if not has_progressive:
            violations.append(Violation(
                rule_id="rule_44",
                rule_number=44,
                rule_name="Help Without Interrupting",
                severity=Severity.INFO,
                message="No progressive help patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Progressive help",
                fix_suggestion="Add progressive help that matches task complexity"
            ))
        
        # Check for non-intrusive patterns
        intrusive_patterns = ['popup', 'modal', 'blocking', 'interrupt', 'stop', 'halt']
        has_intrusive = any(pattern in content.lower() for pattern in intrusive_patterns)
        
        if has_intrusive:
            violations.append(Violation(
                rule_id="rule_44",
                rule_number=44,
                rule_name="Help Without Interrupting",
                severity=Severity.WARNING,
                message="Intrusive help patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Intrusive help",
                fix_suggestion="Use non-intrusive help that doesn't interrupt workflow"
            ))
        
        return violations
    
    def validate_emergency_handling(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for emergency handling patterns (Rule 45).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of emergency handling violations
        """
        violations = []
        
        # Check for clear emergency actions
        emergency_patterns = ['emergency', 'urgent', 'critical', 'stop', 'abort', 'cancel', 'rollback']
        has_emergency = any(pattern in content.lower() for pattern in emergency_patterns)
        
        if not has_emergency:
            violations.append(Violation(
                rule_id="rule_45",
                rule_number=45,
                rule_name="Handle Emergencies Well",
                severity=Severity.WARNING,
                message="No emergency handling patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Emergency handling",
                fix_suggestion="Add clear emergency actions and recovery options"
            ))
        
        # Check for one-click emergency solutions
        one_click_emergency = ['one_click', 'single_click', 'instant', 'immediate', 'quick']
        has_one_click_emergency = any(pattern in content.lower() for pattern in one_click_emergency)
        
        if not has_one_click_emergency:
            violations.append(Violation(
                rule_id="rule_45",
                rule_number=45,
                rule_name="Handle Emergencies Well",
                severity=Severity.INFO,
                message="No one-click emergency solutions detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="One-click emergency",
                fix_suggestion="Add one-click solutions for emergency situations"
            ))
        
        # Check for recovery options
        recovery_patterns = ['recover', 'restore', 'undo', 'backup', 'rollback', 'revert']
        has_recovery = any(pattern in content.lower() for pattern in recovery_patterns)
        
        if not has_recovery:
            violations.append(Violation(
                rule_id="rule_45",
                rule_number=45,
                rule_name="Handle Emergencies Well",
                severity=Severity.WARNING,
                message="No recovery options detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Recovery options",
                fix_suggestion="Add multiple recovery options for emergency situations"
            ))
        
        # Check for progress updates
        progress_patterns = ['progress', 'status', 'update', 'percent', 'complete', 'done']
        has_progress = any(pattern in content.lower() for pattern in progress_patterns)
        
        if not has_progress:
            violations.append(Violation(
                rule_id="rule_45",
                rule_number=45,
                rule_name="Handle Emergencies Well",
                severity=Severity.INFO,
                message="No progress update patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Progress updates",
                fix_suggestion="Add clear progress updates during emergency handling"
            ))
        
        return violations
    
    def validate_scalability(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for scalability patterns (Rule 51).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of scalability violations
        """
        violations = []
        
        # Check for scalability patterns
        scalability_patterns = ['scale', 'scalable', 'elastic', 'distributed', 'cluster', 'load_balance']
        has_scalability = any(pattern in content.lower() for pattern in scalability_patterns)
        
        if not has_scalability:
            violations.append(Violation(
                rule_id="rule_51",
                rule_number=51,
                rule_name="Scale from Small to Huge",
                severity=Severity.INFO,
                message="No scalability patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Scalability",
                fix_suggestion="Add scalability patterns for growth from small to huge"
            ))
        
        # Check for hard-coded limits
        hardcoded_limits = ['100', '1000', '10000', 'limit', 'max_', 'maximum']
        has_hardcoded_limits = any(pattern in content for pattern in hardcoded_limits)
        
        if has_hardcoded_limits:
            violations.append(Violation(
                rule_id="rule_51",
                rule_number=51,
                rule_name="Scale from Small to Huge",
                severity=Severity.WARNING,
                message="Hard-coded limits detected - may not scale",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Hard-coded limits",
                fix_suggestion="Use configurable limits instead of hard-coded values"
            ))
        
        # Check for performance under load
        performance_patterns = ['performance', 'optimize', 'efficient', 'fast', 'quick', 'speed']
        has_performance = any(pattern in content.lower() for pattern in performance_patterns)
        
        if not has_performance:
            violations.append(Violation(
                rule_id="rule_51",
                rule_number=51,
                rule_name="Scale from Small to Huge",
                severity=Severity.INFO,
                message="No performance optimization patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Performance",
                fix_suggestion="Add performance optimization for scaling"
            ))
        
        # Check for configuration patterns
        config_patterns = ['config', 'configuration', 'settings', 'parameter', 'option']
        has_config = any(pattern in content.lower() for pattern in config_patterns)
        
        if not has_config:
            violations.append(Violation(
                rule_id="rule_51",
                rule_number=51,
                rule_name="Scale from Small to Huge",
                severity=Severity.INFO,
                message="No configuration patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Configuration",
                fix_suggestion="Add configuration options for different scales"
            ))
        
        return violations
    
    def validate_developer_happiness(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for developer happiness patterns (Rule 46).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of developer happiness violations
        """
        violations = []
        
        # Check for developer experience patterns
        dev_experience_patterns = ['developer', 'dev', 'programmer', 'engineer', 'happiness', 'satisfaction']
        has_dev_experience = any(pattern in content.lower() for pattern in dev_experience_patterns)
        
        if not has_dev_experience:
            violations.append(Violation(
                rule_id="rule_46",
                rule_number=46,
                rule_name="Make Developers Happier",
                severity=Severity.INFO,
                message="No developer experience patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Developer experience",
                fix_suggestion="Add features that improve developer experience and happiness"
            ))
        
        # Check for productivity patterns
        productivity_patterns = ['productivity', 'efficiency', 'speed', 'fast', 'quick', 'streamline']
        has_productivity = any(pattern in content.lower() for pattern in productivity_patterns)
        
        if not has_productivity:
            violations.append(Violation(
                rule_id="rule_46",
                rule_number=46,
                rule_name="Make Developers Happier",
                severity=Severity.INFO,
                message="No productivity patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Productivity",
                fix_suggestion="Add productivity features to make developers happier"
            ))
        
        # Check for tooling patterns
        tooling_patterns = ['tool', 'tooling', 'utility', 'helper', 'assistant', 'automation']
        has_tooling = any(pattern in content.lower() for pattern in tooling_patterns)
        
        if not has_tooling:
            violations.append(Violation(
                rule_id="rule_46",
                rule_number=46,
                rule_name="Make Developers Happier",
                severity=Severity.INFO,
                message="No tooling patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Tooling",
                fix_suggestion="Add helpful tools and utilities for developers"
            ))
        
        # Check for feedback patterns
        feedback_patterns = ['feedback', 'rating', 'review', 'satisfaction', 'happiness', 'joy']
        has_feedback = any(pattern in content.lower() for pattern in feedback_patterns)
        
        if not has_feedback:
            violations.append(Violation(
                rule_id="rule_46",
                rule_number=46,
                rule_name="Make Developers Happier",
                severity=Severity.INFO,
                message="No feedback patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Feedback",
                fix_suggestion="Add feedback mechanisms to measure developer happiness"
            ))
        
        return violations
    
    def validate_problem_prevention_tracking(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for problem prevention tracking patterns (Rule 47).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of problem prevention tracking violations
        """
        violations = []
        
        # Check for problem prevention patterns
        prevention_patterns = ['prevent', 'prevention', 'avoid', 'stop', 'block', 'intercept']
        has_prevention = any(pattern in content.lower() for pattern in prevention_patterns)
        
        if not has_prevention:
            violations.append(Violation(
                rule_id="rule_47",
                rule_number=47,
                rule_name="Track Problems You Prevent",
                severity=Severity.INFO,
                message="No problem prevention patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Problem prevention",
                fix_suggestion="Add problem prevention mechanisms and tracking"
            ))
        
        # Check for tracking patterns
        tracking_patterns = ['track', 'tracking', 'monitor', 'log', 'record', 'count']
        has_tracking = any(pattern in content.lower() for pattern in tracking_patterns)
        
        if not has_tracking:
            violations.append(Violation(
                rule_id="rule_47",
                rule_number=47,
                rule_name="Track Problems You Prevent",
                severity=Severity.INFO,
                message="No tracking patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Tracking",
                fix_suggestion="Add tracking mechanisms for prevented problems"
            ))
        
        # Check for metrics patterns
        metrics_patterns = ['metric', 'measure', 'statistic', 'counter', 'gauge', 'indicator']
        has_metrics = any(pattern in content.lower() for pattern in metrics_patterns)
        
        if not has_metrics:
            violations.append(Violation(
                rule_id="rule_47",
                rule_number=47,
                rule_name="Track Problems You Prevent",
                severity=Severity.INFO,
                message="No metrics patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Metrics",
                fix_suggestion="Add metrics to measure prevented problems"
            ))
        
        # Check for reporting patterns
        reporting_patterns = ['report', 'reporting', 'dashboard', 'summary', 'analytics']
        has_reporting = any(pattern in content.lower() for pattern in reporting_patterns)
        
        if not has_reporting:
            violations.append(Violation(
                rule_id="rule_47",
                rule_number=47,
                rule_name="Track Problems You Prevent",
                severity=Severity.INFO,
                message="No reporting patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Reporting",
                fix_suggestion="Add reporting for prevented problems"
            ))
        
        return violations
    
    def validate_compliance_workflow(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for compliance workflow patterns (Rule 48).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of compliance workflow violations
        """
        violations = []
        
        # Check for compliance patterns
        compliance_patterns = ['compliance', 'regulation', 'policy', 'standard', 'requirement', 'audit']
        has_compliance = any(pattern in content.lower() for pattern in compliance_patterns)
        
        if not has_compliance:
            violations.append(Violation(
                rule_id="rule_48",
                rule_number=48,
                rule_name="Build Compliance into Workflow",
                severity=Severity.INFO,
                message="No compliance patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Compliance",
                fix_suggestion="Add compliance checking and validation"
            ))
        
        # Check for workflow patterns
        workflow_patterns = ['workflow', 'process', 'pipeline', 'step', 'stage', 'phase']
        has_workflow = any(pattern in content.lower() for pattern in workflow_patterns)
        
        if not has_workflow:
            violations.append(Violation(
                rule_id="rule_48",
                rule_number=48,
                rule_name="Build Compliance into Workflow",
                severity=Severity.INFO,
                message="No workflow patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Workflow",
                fix_suggestion="Add workflow automation for compliance"
            ))
        
        # Check for automation patterns
        automation_patterns = ['automate', 'automatic', 'auto', 'trigger', 'event', 'hook']
        has_automation = any(pattern in content.lower() for pattern in automation_patterns)
        
        if not has_automation:
            violations.append(Violation(
                rule_id="rule_48",
                rule_number=48,
                rule_name="Build Compliance into Workflow",
                severity=Severity.INFO,
                message="No automation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Automation",
                fix_suggestion="Add automation for compliance workflows"
            ))
        
        # Check for validation patterns
        validation_patterns = ['validate', 'validation', 'check', 'verify', 'confirm', 'approve']
        has_validation = any(pattern in content.lower() for pattern in validation_patterns)
        
        if not has_validation:
            violations.append(Violation(
                rule_id="rule_48",
                rule_number=48,
                rule_name="Build Compliance into Workflow",
                severity=Severity.INFO,
                message="No validation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Validation",
                fix_suggestion="Add validation steps to compliance workflows"
            ))
        
        return violations
    
    def validate_security_usability(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for security usability patterns (Rule 49).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of security usability violations
        """
        violations = []
        
        # Check for security patterns
        security_patterns = ['security', 'secure', 'auth', 'authentication', 'authorization', 'encrypt']
        has_security = any(pattern in content.lower() for pattern in security_patterns)
        
        if has_security:
            # Check for usability patterns
            usability_patterns = ['usability', 'user_friendly', 'easy', 'simple', 'intuitive', 'convenient']
            has_usability = any(pattern in content.lower() for pattern in usability_patterns)
            
            if not has_usability:
                violations.append(Violation(
                rule_id="rule_49",
                rule_number=49,
                    rule_name="Security Should Help, Not Block",
                    severity=Severity.WARNING,
                    message="Security features detected without usability considerations",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Security usability",
                    fix_suggestion="Make security features user-friendly and helpful"
                ))
            
            # Check for blocking patterns
            blocking_patterns = ['block', 'prevent', 'deny', 'reject', 'stop', 'halt']
            has_blocking = any(pattern in content.lower() for pattern in blocking_patterns)
            
            if has_blocking:
                violations.append(Violation(
                rule_id="rule_49",
                rule_number=49,
                    rule_name="Security Should Help, Not Block",
                    severity=Severity.WARNING,
                    message="Blocking security patterns detected - should be helpful instead",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Blocking security",
                    fix_suggestion="Replace blocking security with helpful guidance"
                ))
            
            # Check for helpful patterns
            helpful_patterns = ['help', 'assist', 'guide', 'suggest', 'recommend', 'support']
            has_helpful = any(pattern in content.lower() for pattern in helpful_patterns)
            
            if not has_helpful:
                violations.append(Violation(
                rule_id="rule_49",
                rule_number=49,
                    rule_name="Security Should Help, Not Block",
                    severity=Severity.INFO,
                    message="No helpful security patterns detected",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Helpful security",
                    fix_suggestion="Add helpful security features that guide users"
                ))
            
            # Check for transparency patterns
            transparency_patterns = ['transparent', 'clear', 'explain', 'reason', 'why', 'because']
            has_transparency = any(pattern in content.lower() for pattern in transparency_patterns)
            
            if not has_transparency:
                violations.append(Violation(
                rule_id="rule_49",
                rule_number=49,
                    rule_name="Security Should Help, Not Block",
                    severity=Severity.INFO,
                    message="No security transparency patterns detected",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Security transparency",
                    fix_suggestion="Add transparent security explanations"
                ))
        
        return violations
    
    def _get_function_name(self, func_node) -> str:
        """Get function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)

    def validate_gradual_adoption(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for gradual adoption patterns (Rule 50).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 50
        """
        violations = []
        
        # Check for gradual adoption patterns
        adoption_patterns = ['gradual', 'progressive', 'step_by_step', 'incremental', 'modular', 'independent']
        has_adoption = any(pattern in content.lower() for pattern in adoption_patterns)
        
        # Check for module independence
        independence_patterns = ['standalone', 'independent', 'modular', 'self_contained', 'isolated']
        has_independence = any(pattern in content.lower() for pattern in independence_patterns)
        
        # Check for clear value demonstration
        value_patterns = ['value', 'benefit', 'roi', 'improvement', 'efficiency', 'productivity']
        has_value = any(pattern in content.lower() for pattern in value_patterns)
        
        if not has_adoption:
            violations.append(Violation(
                rule_id="rule_50",
                rule_number=50,
                rule_name="Support Gradual Adoption",
                severity=Severity.INFO,
                message="No gradual adoption patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Gradual adoption",
                fix_suggestion="Add gradual adoption mechanisms for teams to start with 3-5 most useful modules"
            ))
        
        if not has_independence:
            violations.append(Violation(
                rule_id="rule_50",
                rule_number=50,
                rule_name="Support Gradual Adoption",
                severity=Severity.INFO,
                message="No module independence patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Module independence",
                fix_suggestion="Ensure each module works well on its own"
            ))
        
        if not has_value:
            violations.append(Violation(
                rule_id="rule_50",
                rule_number=50,
                rule_name="Support Gradual Adoption",
                severity=Severity.INFO,
                message="No clear value demonstration patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Value demonstration",
                fix_suggestion="Show clear paths to add more modules and provide value at every step"
            ))
        
        return violations
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all platform validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all platform violations
        """
        violations = []
        
        violations.extend(self.validate_platform_features(tree, content, file_path))
        violations.extend(self.validate_data_processing_speed(tree, content, file_path))
        violations.extend(self.validate_context_aware_help(tree, content, file_path))
        violations.extend(self.validate_emergency_handling(tree, content, file_path))
        violations.extend(self.validate_scalability(tree, content, file_path))
        violations.extend(self.validate_developer_happiness(tree, content, file_path))
        violations.extend(self.validate_problem_prevention_tracking(tree, content, file_path))
        violations.extend(self.validate_compliance_workflow(tree, content, file_path))
        violations.extend(self.validate_security_usability(tree, content, file_path))
        violations.extend(self.validate_gradual_adoption(tree, content, file_path))
        
        return violations

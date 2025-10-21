"""
Teamwork rule validator.

This module implements validation for teamwork rules:
- Rule 58: Catch Issues Early
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class TeamworkValidator:
    """
    Validates teamwork and collaboration rules.
    
    This class focuses on detecting early warning patterns and
    validation mechanisms for team collaboration.
    """
    
    def __init__(self):
        """Initialize the teamwork validator."""
        self.early_warning_patterns = [
            'validate', 'check', 'verify', 'ensure', 'assert', 'precondition',
            'guard', 'filter', 'sanitize', 'normalize'
        ]
        self.fail_fast_patterns = [
            'raise', 'return', 'exit', 'abort', 'fail', 'error'
        ]
        
    def validate_early_issue_detection(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for early issue detection patterns (Rule 58).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of early detection violations
        """
        violations = []
        
        # Check for early validation patterns
        has_early_validation = any(pattern in content.lower() for pattern in self.early_warning_patterns)
        if not has_early_validation:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.WARNING,
                message="No early validation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Early validation",
                fix_suggestion="Add early validation to catch issues before they become problems"
            ))
        
        # Check for input validation at function boundaries
        functions_without_validation = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_input_validation = False
                has_parameters = len(node.args.args) > 0
                
                if has_parameters:
                    # Look for validation in the first few lines of the function
                    for child in node.body[:3]:  # Check first 3 statements
                        if isinstance(child, ast.If):
                            if self._is_validation_condition(child):
                                has_input_validation = True
                                break
                        elif isinstance(child, ast.Assert):
                            has_input_validation = True
                            break
                        elif isinstance(child, ast.Raise):
                            has_input_validation = True
                            break
                
                if has_parameters and not has_input_validation:
                    functions_without_validation.append(node.name)
        
        if functions_without_validation:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.WARNING,
                message=f"Functions without early input validation: {functions_without_validation}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(functions_without_validation),
                fix_suggestion="Add input validation at function boundaries"
            ))
        
        # Check for fail-fast patterns
        has_fail_fast = any(pattern in content.lower() for pattern in self.fail_fast_patterns)
        if not has_fail_fast:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.INFO,
                message="No fail-fast patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Fail-fast",
                fix_suggestion="Add fail-fast patterns to stop processing on invalid inputs"
            ))
        
        # Check for missing precondition checks
        has_preconditions = any(pattern in content.lower() for pattern in ['precondition', 'prerequisite', 'require'])
        if not has_preconditions:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.INFO,
                message="No explicit precondition checks detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Preconditions",
                fix_suggestion="Add explicit precondition checks for early issue detection"
            ))
        
        # Check for warning patterns
        has_warnings = any(pattern in content.lower() for pattern in ['warn', 'warning', 'alert', 'notice'])
        if not has_warnings:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.INFO,
                message="No warning patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Warnings",
                fix_suggestion="Add warning mechanisms for potential issues"
            ))
        
        # Check for boundary condition validation
        has_boundary_checks = any(pattern in content.lower() for pattern in ['boundary', 'limit', 'range', 'min', 'max'])
        if not has_boundary_checks:
            violations.append(Violation(
                rule_id="rule_58",
                rule_number=58,
                rule_name="Catch Issues Early",
                severity=Severity.INFO,
                message="No boundary condition validation detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Boundary checks",
                fix_suggestion="Add boundary condition validation to catch edge cases early"
            ))
        
        return violations
    
    def validate_real_team_work(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for real team work patterns (Rule 52).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of team work violations
        """
        violations = []
        
        # Check for collaboration features
        collaboration_patterns = ['collaborate', 'team', 'share', 'together', 'joint', 'collective']
        has_collaboration = any(pattern in content.lower() for pattern in collaboration_patterns)
        
        if not has_collaboration:
            violations.append(Violation(
                rule_id="rule_52",
                rule_number=52,
                rule_name="Build for Real Team Work",
                severity=Severity.INFO,
                message="No collaboration features detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Collaboration",
                fix_suggestion="Add features that support real team collaboration"
            ))
        
        # Check for knowledge sharing
        knowledge_patterns = ['knowledge', 'share', 'document', 'wiki', 'guide', 'tutorial']
        has_knowledge_sharing = any(pattern in content.lower() for pattern in knowledge_patterns)
        
        if not has_knowledge_sharing:
            violations.append(Violation(
                rule_id="rule_52",
                rule_number=52,
                rule_name="Build for Real Team Work",
                severity=Severity.INFO,
                message="No knowledge sharing patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Knowledge sharing",
                fix_suggestion="Add knowledge sharing and documentation features"
            ))
        
        # Check for team friction points
        friction_patterns = ['conflict', 'disagree', 'argument', 'friction', 'tension', 'problem']
        has_friction = any(pattern in content.lower() for pattern in friction_patterns)
        
        if has_friction:
            violations.append(Violation(
                rule_id="rule_52",
                rule_number=52,
                rule_name="Build for Real Team Work",
                severity=Severity.WARNING,
                message="Team friction points detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Team friction",
                fix_suggestion="Address team friction points and improve collaboration"
            ))
        
        # Check for communication patterns
        communication_patterns = ['communicate', 'message', 'chat', 'discuss', 'talk', 'meeting']
        has_communication = any(pattern in content.lower() for pattern in communication_patterns)
        
        if not has_communication:
            violations.append(Violation(
                rule_id="rule_52",
                rule_number=52,
                rule_name="Build for Real Team Work",
                severity=Severity.INFO,
                message="No communication patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Communication",
                fix_suggestion="Add communication features for team coordination"
            ))
        
        return violations
    
    def validate_reduce_frustration(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for frustration reduction patterns (Rule 54).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of frustration reduction violations
        """
        violations = []
        
        # Check for automation of repetitive tasks
        automation_patterns = ['automate', 'automatic', 'batch', 'bulk', 'repeat', 'loop']
        has_automation = any(pattern in content.lower() for pattern in automation_patterns)
        
        if not has_automation:
            violations.append(Violation(
                rule_id="rule_54",
                rule_number=54,
                rule_name="Reduce Frustration Daily",
                severity=Severity.INFO,
                message="No automation of repetitive tasks detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Automation",
                fix_suggestion="Automate repetitive tasks to reduce daily frustration"
            ))
        
        # Check for smooth workflows
        workflow_patterns = ['workflow', 'process', 'streamline', 'smooth', 'seamless', 'flow']
        has_workflow = any(pattern in content.lower() for pattern in workflow_patterns)
        
        if not has_workflow:
            violations.append(Violation(
                rule_id="rule_54",
                rule_number=54,
                rule_name="Reduce Frustration Daily",
                severity=Severity.INFO,
                message="No smooth workflow patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Workflow",
                fix_suggestion="Add smooth workflows to reduce friction"
            ))
        
        # Check for friction points
        friction_patterns = ['friction', 'slow', 'delay', 'wait', 'block', 'stuck']
        has_friction = any(pattern in content.lower() for pattern in friction_patterns)
        
        if has_friction:
            violations.append(Violation(
                rule_id="rule_54",
                rule_number=54,
                rule_name="Reduce Frustration Daily",
                severity=Severity.WARNING,
                message="Friction points detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Friction",
                fix_suggestion="Remove friction points and streamline processes"
            ))
        
        # Check for quick wins
        quick_win_patterns = ['quick', 'fast', 'instant', 'immediate', 'easy', 'simple']
        has_quick_wins = any(pattern in content.lower() for pattern in quick_win_patterns)
        
        if not has_quick_wins:
            violations.append(Violation(
                rule_id="rule_54",
                rule_number=54,
                rule_name="Reduce Frustration Daily",
                severity=Severity.INFO,
                message="No quick win patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Quick wins",
                fix_suggestion="Add quick wins to reduce daily frustration"
            ))
        
        return violations
    
    def validate_automate_wisely(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for wise automation patterns (Rule 60).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of automation violations
        """
        violations = []
        
        # Check for proper automation patterns
        automation_patterns = ['automate', 'automatic', 'batch', 'bulk', 'repeat', 'loop']
        has_automation = any(pattern in content.lower() for pattern in automation_patterns)
        
        if not has_automation:
            violations.append(Violation(
                rule_id="rule_60",
                rule_number=60,
                rule_name="Automate Wisely",
                severity=Severity.INFO,
                message="No automation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Automation",
                fix_suggestion="Add automation for repetitive and boring tasks"
            ))
        
        # Check for human oversight
        oversight_patterns = ['human', 'manual', 'review', 'approve', 'check', 'verify']
        has_oversight = any(pattern in content.lower() for pattern in oversight_patterns)
        
        if not has_oversight:
            violations.append(Violation(
                rule_id="rule_60",
                rule_number=60,
                rule_name="Automate Wisely",
                severity=Severity.INFO,
                message="No human oversight patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Human oversight",
                fix_suggestion="Add human oversight for automated processes"
            ))
        
        # Check for over-automation
        over_automation_patterns = ['fully_automatic', 'no_human', 'completely_auto', 'zero_touch']
        has_over_automation = any(pattern in content.lower() for pattern in over_automation_patterns)
        
        if has_over_automation:
            violations.append(Violation(
                rule_id="rule_60",
                rule_number=60,
                rule_name="Automate Wisely",
                severity=Severity.WARNING,
                message="Over-automation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Over-automation",
                fix_suggestion="Ensure automation has appropriate human oversight"
            ))
        
        # Check for automation boundaries
        boundary_patterns = ['boundary', 'limit', 'threshold', 'max', 'min', 'range']
        has_boundaries = any(pattern in content.lower() for pattern in boundary_patterns)
        
        if not has_boundaries:
            violations.append(Violation(
                rule_id="rule_60",
                rule_number=60,
                rule_name="Automate Wisely",
                severity=Severity.INFO,
                message="No automation boundaries detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Automation boundaries",
                fix_suggestion="Define clear boundaries for automation"
            ))
        
        return violations
    
    def validate_knowledge_silos_prevention(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for knowledge silos prevention patterns (Rule 53).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of knowledge silos prevention violations
        """
        violations = []
        
        # Check for knowledge sharing patterns
        knowledge_patterns = ['knowledge', 'share', 'document', 'wiki', 'guide', 'tutorial', 'documentation']
        has_knowledge_sharing = any(pattern in content.lower() for pattern in knowledge_patterns)
        
        if not has_knowledge_sharing:
            violations.append(Violation(
                rule_id="rule_53",
                rule_number=53,
                rule_name="Prevent Knowledge Silos",
                severity=Severity.INFO,
                message="No knowledge sharing patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Knowledge sharing",
                fix_suggestion="Add knowledge sharing mechanisms to prevent silos"
            ))
        
        # Check for collaboration patterns
        collaboration_patterns = ['collaborate', 'team', 'together', 'joint', 'collective', 'shared']
        has_collaboration = any(pattern in content.lower() for pattern in collaboration_patterns)
        
        if not has_collaboration:
            violations.append(Violation(
                rule_id="rule_53",
                rule_number=53,
                rule_name="Prevent Knowledge Silos",
                severity=Severity.INFO,
                message="No collaboration patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Collaboration",
                fix_suggestion="Add collaboration features to prevent knowledge silos"
            ))
        
        # Check for communication patterns
        communication_patterns = ['communicate', 'message', 'chat', 'discuss', 'talk', 'meeting']
        has_communication = any(pattern in content.lower() for pattern in communication_patterns)
        
        if not has_communication:
            violations.append(Violation(
                rule_id="rule_53",
                rule_number=53,
                rule_name="Prevent Knowledge Silos",
                severity=Severity.INFO,
                message="No communication patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Communication",
                fix_suggestion="Add communication features to prevent knowledge silos"
            ))
        
        # Check for transparency patterns
        transparency_patterns = ['transparent', 'visible', 'open', 'public', 'accessible', 'available']
        has_transparency = any(pattern in content.lower() for pattern in transparency_patterns)
        
        if not has_transparency:
            violations.append(Violation(
                rule_id="rule_53",
                rule_number=53,
                rule_name="Prevent Knowledge Silos",
                severity=Severity.INFO,
                message="No transparency patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Transparency",
                fix_suggestion="Add transparency to prevent knowledge silos"
            ))
        
        return violations
    
    def validate_confidence_building(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for confidence building patterns (Rule 55).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of confidence building violations
        """
        violations = []
        
        # Check for confidence patterns
        confidence_patterns = ['confidence', 'trust', 'reliable', 'secure', 'safe', 'stable']
        has_confidence = any(pattern in content.lower() for pattern in confidence_patterns)
        
        if not has_confidence:
            violations.append(Violation(
                rule_id="rule_55",
                rule_number=55,
                rule_name="Build Confidence, Not Fear",
                severity=Severity.INFO,
                message="No confidence building patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Confidence building",
                fix_suggestion="Add confidence building features instead of fear-based ones"
            ))
        
        # Check for fear patterns (should be avoided)
        fear_patterns = ['fear', 'scare', 'warn', 'danger', 'risk', 'threat', 'alarm']
        has_fear = any(pattern in content.lower() for pattern in fear_patterns)
        
        if has_fear:
            violations.append(Violation(
                rule_id="rule_55",
                rule_number=55,
                rule_name="Build Confidence, Not Fear",
                severity=Severity.WARNING,
                message="Fear-based patterns detected - should build confidence instead",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Fear patterns",
                fix_suggestion="Replace fear-based messaging with confidence building"
            ))
        
        # Check for positive reinforcement patterns
        positive_patterns = ['success', 'achievement', 'accomplish', 'complete', 'win', 'victory']
        has_positive = any(pattern in content.lower() for pattern in positive_patterns)
        
        if not has_positive:
            violations.append(Violation(
                rule_id="rule_55",
                rule_number=55,
                rule_name="Build Confidence, Not Fear",
                severity=Severity.INFO,
                message="No positive reinforcement patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Positive reinforcement",
                fix_suggestion="Add positive reinforcement to build confidence"
            ))
        
        # Check for support patterns
        support_patterns = ['support', 'help', 'assist', 'guide', 'encourage', 'motivate']
        has_support = any(pattern in content.lower() for pattern in support_patterns)
        
        if not has_support:
            violations.append(Violation(
                rule_id="rule_55",
                rule_number=55,
                rule_name="Build Confidence, Not Fear",
                severity=Severity.INFO,
                message="No support patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Support",
                fix_suggestion="Add support features to build confidence"
            ))
        
        return violations
    
    def validate_learning_adaptation(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for learning and adaptation patterns (Rule 56).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of learning adaptation violations
        """
        violations = []
        
        # Check for learning patterns
        learning_patterns = ['learn', 'learning', 'adapt', 'adaptation', 'evolve', 'improve']
        has_learning = any(pattern in content.lower() for pattern in learning_patterns)
        
        if not has_learning:
            violations.append(Violation(
                rule_id="rule_56",
                rule_number=56,
                rule_name="Learn and Adapt Constantly",
                severity=Severity.INFO,
                message="No learning patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Learning",
                fix_suggestion="Add learning mechanisms for constant adaptation"
            ))
        
        # Check for feedback patterns
        feedback_patterns = ['feedback', 'response', 'reaction', 'result', 'outcome', 'consequence']
        has_feedback = any(pattern in content.lower() for pattern in feedback_patterns)
        
        if not has_feedback:
            violations.append(Violation(
                rule_id="rule_56",
                rule_number=56,
                rule_name="Learn and Adapt Constantly",
                severity=Severity.INFO,
                message="No feedback patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Feedback",
                fix_suggestion="Add feedback mechanisms for learning and adaptation"
            ))
        
        # Check for iteration patterns
        iteration_patterns = ['iterate', 'iteration', 'cycle', 'loop', 'repeat', 'refine']
        has_iteration = any(pattern in content.lower() for pattern in iteration_patterns)
        
        if not has_iteration:
            violations.append(Violation(
                rule_id="rule_56",
                rule_number=56,
                rule_name="Learn and Adapt Constantly",
                severity=Severity.INFO,
                message="No iteration patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Iteration",
                fix_suggestion="Add iteration mechanisms for continuous improvement"
            ))
        
        # Check for change patterns
        change_patterns = ['change', 'modify', 'update', 'adjust', 'transform', 'evolve']
        has_change = any(pattern in content.lower() for pattern in change_patterns)
        
        if not has_change:
            violations.append(Violation(
                rule_id="rule_56",
                rule_number=56,
                rule_name="Learn and Adapt Constantly",
                severity=Severity.INFO,
                message="No change patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Change",
                fix_suggestion="Add change mechanisms for constant adaptation"
            ))
        
        return violations
    
    def validate_measurement(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for measurement patterns (Rule 57).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of measurement violations
        """
        violations = []
        
        # Check for measurement patterns
        measurement_patterns = ['measure', 'metric', 'kpi', 'indicator', 'gauge', 'counter']
        has_measurement = any(pattern in content.lower() for pattern in measurement_patterns)
        
        if not has_measurement:
            violations.append(Violation(
                rule_id="rule_57",
                rule_number=57,
                rule_name="Measure What Matters",
                severity=Severity.INFO,
                message="No measurement patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Measurement",
                fix_suggestion="Add measurement mechanisms for what matters"
            ))
        
        # Check for analytics patterns
        analytics_patterns = ['analytics', 'analysis', 'statistics', 'data', 'insight', 'trend']
        has_analytics = any(pattern in content.lower() for pattern in analytics_patterns)
        
        if not has_analytics:
            violations.append(Violation(
                rule_id="rule_57",
                rule_number=57,
                rule_name="Measure What Matters",
                severity=Severity.INFO,
                message="No analytics patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Analytics",
                fix_suggestion="Add analytics to measure what matters"
            ))
        
        # Check for reporting patterns
        reporting_patterns = ['report', 'reporting', 'dashboard', 'summary', 'visualization']
        has_reporting = any(pattern in content.lower() for pattern in reporting_patterns)
        
        if not has_reporting:
            violations.append(Violation(
                rule_id="rule_57",
                rule_number=57,
                rule_name="Measure What Matters",
                severity=Severity.INFO,
                message="No reporting patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Reporting",
                fix_suggestion="Add reporting for measured data"
            ))
        
        # Check for goal patterns
        goal_patterns = ['goal', 'target', 'objective', 'milestone', 'benchmark', 'standard']
        has_goals = any(pattern in content.lower() for pattern in goal_patterns)
        
        if not has_goals:
            violations.append(Violation(
                rule_id="rule_57",
                rule_number=57,
                rule_name="Measure What Matters",
                severity=Severity.INFO,
                message="No goal patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Goals",
                fix_suggestion="Add goal setting and tracking for meaningful measurement"
            ))
        
        return violations
    
    def _is_validation_condition(self, if_node: ast.If) -> bool:
        """Check if an if statement contains validation logic."""
        validation_keywords = [
            'isinstance', 'len', 'isdigit', 'isalpha', 'strip', 'lower', 'upper',
            'isnull', 'isempty', 'valid', 'check', 'verify', 'assert', 'raise',
            'none', 'empty', 'null', 'invalid', 'error'
        ]
        
        for node in ast.walk(if_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in validation_keywords):
                    return True
            elif isinstance(node, ast.Compare):
                # Check for comparison with None, empty strings, etc.
                for op in node.ops:
                    if isinstance(op, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)):
                        return True
        return False
    
    def _get_function_name(self, func_node) -> str:
        """Get function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return f"{self._get_function_name(func_node.value)}.{func_node.attr}"
        else:
            return str(func_node)

    def validate_learn_from_experts(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for learning from experts patterns (Rule 61).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 61
        """
        violations = []
        
        # Check for expert pattern recognition
        expert_patterns = ['expert', 'best_practice', 'pattern', 'template', 'standard', 'guideline']
        has_expert_patterns = any(pattern in content.lower() for pattern in expert_patterns)
        
        if not has_expert_patterns:
            violations.append(Violation(
                rule_id="rule_61",
                rule_number=61,
                rule_name="Learn from Experts",
                severity=Severity.INFO,
                message="No expert pattern recognition detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Expert patterns",
                fix_suggestion="Watch how the best developers work and copy their successful patterns"
            ))
        
        return violations

    def validate_right_information_timing(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for right information at right time patterns (Rule 62).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 62
        """
        violations = []
        
        # Check for contextual information display
        timing_patterns = ['context', 'relevant', 'timely', 'progressive', 'on_demand', 'just_in_time']
        has_timing = any(pattern in content.lower() for pattern in timing_patterns)
        
        if not has_timing:
            violations.append(Violation(
                rule_id="rule_62",
                rule_number=62,
                rule_name="Show the Right Information at the Right Time",
                severity=Severity.INFO,
                message="No contextual information timing patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Information timing",
                fix_suggestion="Don't overwhelm people with too much information - show what's important right now"
            ))
        
        return violations

    def validate_dependencies_visible(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for dependency visibility patterns (Rule 63).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 63
        """
        violations = []
        
        # Check for dependency visualization
        dependency_patterns = ['dependency', 'depends_on', 'requires', 'import', 'reference', 'connection']
        has_dependencies = any(pattern in content.lower() for pattern in dependency_patterns)
        
        if not has_dependencies:
            violations.append(Violation(
                rule_id="rule_63",
                rule_number=63,
                rule_name="Make Dependencies Visible",
                severity=Severity.INFO,
                message="No dependency visibility patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Dependency visibility",
                fix_suggestion="Show how different pieces connect and depend on each other"
            ))
        
        return violations

    def validate_predictability_consistency(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for predictability and consistency patterns (Rule 64).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 64
        """
        violations = []
        
        # Check for consistency patterns
        consistency_patterns = ['consistent', 'predictable', 'reliable', 'stable', 'uniform', 'standard']
        has_consistency = any(pattern in content.lower() for pattern in consistency_patterns)
        
        if not has_consistency:
            violations.append(Violation(
                rule_id="rule_64",
                rule_number=64,
                rule_name="Be Predictable and Consistent",
                severity=Severity.INFO,
                message="No predictability and consistency patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Predictability",
                fix_suggestion="Work the same way every time and don't surprise people with unexpected behavior"
            ))
        
        return violations

    def validate_work_preservation(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for work preservation patterns (Rule 65).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 65
        """
        violations = []
        
        # Check for auto-save patterns
        preservation_patterns = ['auto_save', 'backup', 'recovery', 'persist', 'save', 'restore']
        has_preservation = any(pattern in content.lower() for pattern in preservation_patterns)
        
        if not has_preservation:
            violations.append(Violation(
                rule_id="rule_65",
                rule_number=65,
                rule_name="Never Lose People's Work",
                severity=Severity.INFO,
                message="No work preservation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Work preservation",
                fix_suggestion="Save work automatically and frequently, provide clear recovery options"
            ))
        
        return violations

    def validate_beauty_pleasantness(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for beauty and pleasantness patterns (Rule 66).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 66
        """
        violations = []
        
        # Check for design quality patterns
        design_patterns = ['beautiful', 'pleasant', 'attractive', 'clean', 'smooth', 'satisfying']
        has_design = any(pattern in content.lower() for pattern in design_patterns)
        
        if not has_design:
            violations.append(Violation(
                rule_id="rule_66",
                rule_number=66,
                rule_name="Make it Beautiful and Pleasant",
                severity=Severity.INFO,
                message="No design quality patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Design quality",
                fix_suggestion="Use clean, attractive designs and make interactions smooth and satisfying"
            ))
        
        return violations

    def validate_encourage_better_practices(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for encouraging better practices patterns (Rule 70).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 70
        """
        violations = []
        
        # Check for improvement encouragement patterns
        improvement_patterns = ['improve', 'better', 'enhance', 'optimize', 'suggest', 'recommend']
        has_improvement = any(pattern in content.lower() for pattern in improvement_patterns)
        
        if not has_improvement:
            violations.append(Violation(
                rule_id="rule_70",
                rule_number=70,
                rule_name="Encourage Better Ways of Working",
                severity=Severity.INFO,
                message="No improvement encouragement patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Better practices",
                fix_suggestion="Suggest improvements to processes and help teams adopt better practices"
            ))
        
        return violations

    def validate_skill_level_adaptation(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for skill level adaptation patterns (Rule 71).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 71
        """
        violations = []
        
        # Check for skill level adaptation patterns
        skill_patterns = ['beginner', 'expert', 'skill_level', 'adaptive', 'progressive', 'scalable']
        has_skill_adaptation = any(pattern in content.lower() for pattern in skill_patterns)
        
        if not has_skill_adaptation:
            violations.append(Violation(
                rule_id="rule_71",
                rule_number=71,
                rule_name="Adapt to Different Skill Levels",
                severity=Severity.INFO,
                message="No skill level adaptation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Skill adaptation",
                fix_suggestion="Help beginners learn quickly and support experts with advanced features"
            ))
        
        return violations

    def validate_helpfulness_balance(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for helpfulness balance patterns (Rule 72).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 72
        """
        violations = []
        
        # Check for helpful but not annoying patterns
        helpful_patterns = ['helpful', 'assist', 'guide', 'support', 'contextual', 'relevant']
        has_helpful = any(pattern in content.lower() for pattern in helpful_patterns)
        
        if not has_helpful:
            violations.append(Violation(
                rule_id="rule_72",
                rule_number=72,
                rule_name="Be Helpful, Not Annoying",
                severity=Severity.INFO,
                message="No helpfulness balance patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Helpfulness balance",
                fix_suggestion="Offer help when it's actually needed and know when to be quiet"
            ))
        
        return violations

    def validate_clear_value_demonstration(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for clear value demonstration patterns (Rule 74).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 74
        """
        violations = []
        
        # Check for value demonstration patterns
        value_patterns = ['value', 'benefit', 'roi', 'savings', 'efficiency', 'productivity']
        has_value = any(pattern in content.lower() for pattern in value_patterns)
        
        if not has_value:
            violations.append(Violation(
                rule_id="rule_74",
                rule_number=74,
                rule_name="Demonstrate Clear Value",
                severity=Severity.INFO,
                message="No clear value demonstration patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Value demonstration",
                fix_suggestion="Show how the product saves time and money with obvious and measurable benefits"
            ))
        
        return violations

    def validate_customer_growth(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for customer growth patterns (Rule 75).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 75
        """
        violations = []
        
        # Check for growth and scalability patterns
        growth_patterns = ['grow', 'scale', 'expand', 'adapt', 'flexible', 'versatile']
        has_growth = any(pattern in content.lower() for pattern in growth_patterns)
        
        if not has_growth:
            violations.append(Violation(
                rule_id="rule_75",
                rule_number=75,
                rule_name="Grow with the Customer",
                severity=Severity.INFO,
                message="No customer growth patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Customer growth",
                fix_suggestion="Work well for small teams and huge organizations, adapt to different needs"
            ))
        
        return violations

    def validate_magic_moments(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for magic moments patterns (Rule 76).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 76
        """
        violations = []
        
        # Check for delightful experience patterns
        magic_patterns = ['magic', 'delight', 'surprise', 'effortless', 'seamless', 'wow']
        has_magic = any(pattern in content.lower() for pattern in magic_patterns)
        
        if not has_magic:
            violations.append(Violation(
                rule_id="rule_76",
                rule_number=76,
                rule_name="Create Magic Moments",
                severity=Severity.INFO,
                message="No magic moments patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Magic moments",
                fix_suggestion="Occasionally surprise and delight users, make some tasks feel effortless"
            ))
        
        return violations

    def validate_friction_removal(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for friction removal patterns (Rule 77).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of violations for Rule 77
        """
        violations = []
        
        # Check for friction removal patterns
        friction_patterns = ['friction', 'smooth', 'seamless', 'effortless', 'streamline', 'eliminate']
        has_friction_removal = any(pattern in content.lower() for pattern in friction_patterns)
        
        if not has_friction_removal:
            violations.append(Violation(
                rule_id="rule_77",
                rule_number=77,
                rule_name="Remove Friction Everywhere",
                severity=Severity.INFO,
                message="No friction removal patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Friction removal",
                fix_suggestion="Remove friction everywhere and make interactions as smooth as possible"
            ))
        
        return violations
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all teamwork validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all teamwork violations
        """
        violations = []
        
        violations.extend(self.validate_early_issue_detection(tree, content, file_path))
        violations.extend(self.validate_real_team_work(tree, content, file_path))
        violations.extend(self.validate_reduce_frustration(tree, content, file_path))
        violations.extend(self.validate_automate_wisely(tree, content, file_path))
        violations.extend(self.validate_knowledge_silos_prevention(tree, content, file_path))
        violations.extend(self.validate_confidence_building(tree, content, file_path))
        violations.extend(self.validate_learning_adaptation(tree, content, file_path))
        violations.extend(self.validate_measurement(tree, content, file_path))
        violations.extend(self.validate_learn_from_experts(tree, content, file_path))
        violations.extend(self.validate_right_information_timing(tree, content, file_path))
        violations.extend(self.validate_dependencies_visible(tree, content, file_path))
        violations.extend(self.validate_predictability_consistency(tree, content, file_path))
        violations.extend(self.validate_work_preservation(tree, content, file_path))
        violations.extend(self.validate_beauty_pleasantness(tree, content, file_path))
        violations.extend(self.validate_encourage_better_practices(tree, content, file_path))
        violations.extend(self.validate_skill_level_adaptation(tree, content, file_path))
        violations.extend(self.validate_helpfulness_balance(tree, content, file_path))
        violations.extend(self.validate_clear_value_demonstration(tree, content, file_path))
        violations.extend(self.validate_customer_growth(tree, content, file_path))
        violations.extend(self.validate_magic_moments(tree, content, file_path))
        violations.extend(self.validate_friction_removal(tree, content, file_path))
        
        return violations

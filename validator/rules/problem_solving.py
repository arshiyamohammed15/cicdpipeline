"""
Problem-solving rule validator.

This module implements validation for problem-solving rules:
- Solve Real Developer Problems
- Prevent Problems Before They Happen
- Detection Engine - Be Accurate
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from..models import Violation, Severity


class ProblemSolvingValidator:
    """
    Validates problem-solving approach rules.
    
    This class focuses on detecting over-engineering, proactive prevention,
    and accuracy/confidence validation.
    """
    
    def __init__(self):
        """Initialize the problem-solving validator."""
        self.over_engineering_patterns = [
            'abstract', 'interface', 'factory', 'builder', 'singleton',
            'observer', 'strategy', 'adapter', 'decorator', 'facade'
        ]
        self.complexity_indicators = [
            'recursive', 'dynamic', 'reflection', 'metaclass', 'decorator',
            'generator', 'coroutine', 'async', 'await'
        ]
        
    def validate_real_problems(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for real problem solving.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of problem-solving violations
        """
        violations = []
        
        # Check for over-engineering patterns
        over_engineering_detected = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name.lower()
                for pattern in self.over_engineering_patterns:
                    if pattern in class_name:
                        over_engineering_detected.append((node.name, pattern))
        
        if over_engineering_detected:
            violations.append(Violation(
                rule_name="Solve Real Developer Problems",
                severity=Severity.WARNING,
                message=f"Potential over-engineering detected: {[f[0] for f in over_engineering_detected]}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Design patterns",
                fix_suggestion="Ensure design patterns solve real problems, not theoretical ones"
            ))
        
        # Check for unnecessary complexity
        complex_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count complexity indicators
                complexity_score = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                        complexity_score += 1
                    elif isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id.lower() in self.complexity_indicators:
                                complexity_score += 2
                
                # Flag functions with high complexity
                if complexity_score > 8:
                    complex_functions.append((node.name, complexity_score))
        
        if complex_functions:
            violations.append(Violation(
                rule_name="Solve Real Developer Problems",
                severity=Severity.WARNING,
                message=f"High complexity functions detected: {[f[0] for f in complex_functions]}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Complex functions",
                fix_suggestion="Simplify complex functions to solve real problems more directly"
            ))
        
        # Check for practical utility
        utility_indicators = ['main', 'run', 'execute', 'process', 'handle', 'validate']
        has_utility = any(indicator in content.lower() for indicator in utility_indicators)
        
        if not has_utility:
            violations.append(Violation(
                rule_name="Solve Real Developer Problems",
                severity=Severity.INFO,
                message="No clear utility functions detected - ensure code solves practical problems",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Utility functions",
                fix_suggestion="Add clear utility functions that solve real developer problems"
            ))
        
        return violations
    
    def validate_proactive_prevention(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for proactive problem prevention.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of prevention violations
        """
        violations = []
        
        # Check for proactive validation patterns
        validation_patterns = ['validate', 'check', 'verify', 'ensure', 'assert']
        has_validation = any(pattern in content.lower() for pattern in validation_patterns)
        
        if not has_validation:
            violations.append(Violation(
                rule_name="Prevent Problems Before They Happen",
                severity=Severity.WARNING,
                message="No proactive validation detected - add precondition checks",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Validation",
                fix_suggestion="Add proactive validation to prevent problems before they occur"
            ))
        
        # Check for missing precondition checks
        functions_without_validation = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_preconditions = False
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        # Check if it's a validation condition
                        if self._is_validation_condition(child):
                            has_preconditions = True
                            break
                
                if not has_preconditions and len(node.args.args) > 0:
                    functions_without_validation.append(node.name)
        
        if functions_without_validation:
            violations.append(Violation(
                rule_name="Prevent Problems Before They Happen",
                severity=Severity.WARNING,
                message=f"Functions without precondition checks: {functions_without_validation}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(functions_without_validation),
                fix_suggestion="Add precondition checks to prevent invalid inputs"
            ))
        
        # Check for defensive programming patterns
        defensive_patterns = ['try:', 'except:', 'finally:', 'if not', 'assert', 'raise']
        has_defensive = any(pattern in content for pattern in defensive_patterns)
        
        if not has_defensive:
            violations.append(Violation(
                rule_name="Prevent Problems Before They Happen",
                severity=Severity.INFO,
                message="No defensive programming patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Defensive programming",
                fix_suggestion="Add defensive programming patterns to prevent failures"
            ))
        
        return violations
    
    def validate_accuracy_confidence(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for accuracy and confidence reporting.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of accuracy violations
        """
        violations = []
        
        # Check for confidence level reporting
        confidence_patterns = ['confidence', 'accuracy', 'probability', 'certainty', 'uncertainty']
        has_confidence = any(pattern in content.lower() for pattern in confidence_patterns)
        
        if not has_confidence:
            violations.append(Violation(
                rule_name="Detection Engine - Be Accurate",
                severity=Severity.INFO,
                message="No confidence level reporting detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Confidence reporting",
                fix_suggestion="Add confidence levels to detection results"
            ))
        
        # Check for accuracy metrics
        accuracy_patterns = ['precision', 'recall', 'f1', 'accuracy', 'error_rate', 'false_positive', 'false_negative']
        has_accuracy_metrics = any(pattern in content.lower() for pattern in accuracy_patterns)
        
        if not has_accuracy_metrics:
            violations.append(Violation(
                rule_name="Detection Engine - Be Accurate",
                severity=Severity.INFO,
                message="No accuracy metrics detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Accuracy metrics",
                fix_suggestion="Add accuracy metrics to measure detection performance"
            ))
        
        # Check for uncertainty handling
        uncertainty_patterns = ['maybe', 'possibly', 'likely', 'unlikely', 'uncertain', 'unknown']
        has_uncertainty = any(pattern in content.lower() for pattern in uncertainty_patterns)
        
        if not has_uncertainty:
            violations.append(Violation(
                rule_name="Detection Engine - Be Accurate",
                severity=Severity.INFO,
                message="No uncertainty handling detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Uncertainty handling",
                fix_suggestion="Add uncertainty handling for ambiguous cases"
            ))
        
        # Check for learning from corrections
        learning_patterns = ['learn', 'feedback', 'correction', 'improve', 'update', 'adapt']
        has_learning = any(pattern in content.lower() for pattern in learning_patterns)
        
        if not has_learning:
            violations.append(Violation(
                rule_name="Detection Engine - Be Accurate",
                severity=Severity.INFO,
                message="No learning from corrections detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Learning mechanism",
                fix_suggestion="Add mechanism to learn from corrections and improve accuracy"
            ))
        
        return violations
    
    def validate_help_people_work_better(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for Mirror/Mentor/Multiplier patterns.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of work improvement violations
        """
        violations = []
        
        # Check for Mirror patterns (show current state)
        mirror_patterns = ['status', 'current', 'state', 'show', 'display', 'view', 'monitor']
        has_mirror = any(pattern in content.lower() for pattern in mirror_patterns)
        
        if not has_mirror:
            violations.append(Violation(
                rule_name="Help People Work Better",
                severity=Severity.INFO,
                message="No Mirror patterns detected - show people what they're doing now",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Mirror patterns",
                fix_suggestion="Add status displays and current state visibility"
            ))
        
        # Check for Mentor patterns (guide improvements)
        mentor_patterns = ['suggest', 'recommend', 'guide', 'help', 'improve', 'better', 'tip', 'advice']
        has_mentor = any(pattern in content.lower() for pattern in mentor_patterns)
        
        if not has_mentor:
            violations.append(Violation(
                rule_name="Help People Work Better",
                severity=Severity.INFO,
                message="No Mentor patterns detected - guide people to better ways",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Mentor patterns",
                fix_suggestion="Add suggestions and guidance for improvements"
            ))
        
        # Check for Multiplier patterns (amplify good practices)
        multiplier_patterns = ['amplify', 'boost', 'enhance', 'multiply', 'scale', 'expand', 'accelerate']
        has_multiplier = any(pattern in content.lower() for pattern in multiplier_patterns)
        
        if not has_multiplier:
            violations.append(Violation(
                rule_name="Help People Work Better",
                severity=Severity.INFO,
                message="No Multiplier patterns detected - help people do more of what works",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Multiplier patterns",
                fix_suggestion="Add features that amplify successful practices"
            ))
        
        return violations
    
    def validate_cognitive_load(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for cognitive load and complexity.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of cognitive load violations
        """
        violations = []
        
        # Check for one-click solutions
        one_click_patterns = ['one_click', 'single_click', 'instant', 'automatic', 'auto', 'quick']
        has_one_click = any(pattern in content.lower() for pattern in one_click_patterns)
        
        if not has_one_click:
            violations.append(Violation(
                rule_name="Don't Make People Think Too Hard",
                severity=Severity.INFO,
                message="No one-click solutions detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="One-click solutions",
                fix_suggestion="Add one-click solutions for common tasks"
            ))
        
        # Check for cognitive load indicators
        cognitive_load_patterns = ['complex', 'difficult', 'confusing', 'complicated', 'hard', 'challenging']
        has_cognitive_load = any(pattern in content.lower() for pattern in cognitive_load_patterns)
        
        if has_cognitive_load:
            violations.append(Violation(
                rule_name="Don't Make People Think Too Hard",
                severity=Severity.WARNING,
                message="High cognitive load patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Cognitive load",
                fix_suggestion="Simplify complex features and reduce cognitive load"
            ))
        
        # Check for automation of boring tasks
        automation_patterns = ['automate', 'automatic', 'batch', 'bulk', 'mass', 'repeat']
        has_automation = any(pattern in content.lower() for pattern in automation_patterns)
        
        if not has_automation:
            violations.append(Violation(
                rule_name="Don't Make People Think Too Hard",
                severity=Severity.INFO,
                message="No automation patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Automation",
                fix_suggestion="Automate boring and repetitive tasks"
            ))
        
        # Check for teaching as you go
        teaching_patterns = ['explain', 'teach', 'learn', 'tutorial', 'guide', 'help', 'documentation']
        has_teaching = any(pattern in content.lower() for pattern in teaching_patterns)
        
        if not has_teaching:
            violations.append(Violation(
                rule_name="Don't Make People Think Too Hard",
                severity=Severity.INFO,
                message="No teaching patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Teaching",
                fix_suggestion="Add teaching and learning features as you go"
            ))
        
        return violations
    
    def validate_behavior_change_engine(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for MMM Engine - Change Behavior patterns.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of behavior change violations
        """
        violations = []
        
        # Check for behavior change patterns
        behavior_patterns = ['behavior', 'change', 'modify', 'adapt', 'adjust', 'transform']
        has_behavior_change = any(pattern in content.lower() for pattern in behavior_patterns)
        
        if not has_behavior_change:
            violations.append(Violation(
                rule_name="MMM Engine - Change Behavior",
                severity=Severity.INFO,
                message="No behavior change patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Behavior change",
                fix_suggestion="Add behavior modification capabilities"
            ))
        
        # Check for Mirror patterns (show current state)
        mirror_patterns = ['mirror', 'reflect', 'show', 'display', 'current_state', 'status']
        has_mirror = any(pattern in content.lower() for pattern in mirror_patterns)
        
        if not has_mirror:
            violations.append(Violation(
                rule_name="MMM Engine - Change Behavior",
                severity=Severity.INFO,
                message="No Mirror patterns detected - show current behavior state",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Mirror patterns",
                fix_suggestion="Add Mirror patterns to show current behavior state"
            ))
        
        # Check for Mentor patterns (guide behavior changes)
        mentor_patterns = ['mentor', 'guide', 'suggest', 'recommend', 'advise', 'coach']
        has_mentor = any(pattern in content.lower() for pattern in mentor_patterns)
        
        if not has_mentor:
            violations.append(Violation(
                rule_name="MMM Engine - Change Behavior",
                severity=Severity.INFO,
                message="No Mentor patterns detected - guide behavior changes",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Mentor patterns",
                fix_suggestion="Add Mentor patterns to guide behavior changes"
            ))
        
        # Check for Multiplier patterns (amplify good behaviors)
        multiplier_patterns = ['multiply', 'amplify', 'boost', 'enhance', 'scale', 'expand']
        has_multiplier = any(pattern in content.lower() for pattern in multiplier_patterns)
        
        if not has_multiplier:
            violations.append(Violation(
                rule_name="MMM Engine - Change Behavior",
                severity=Severity.INFO,
                message="No Multiplier patterns detected - amplify good behaviors",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Multiplier patterns",
                fix_suggestion="Add Multiplier patterns to amplify good behaviors"
            ))
        
        return violations
    
    def validate_success_dashboards(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for Success Dashboards - Show Business Value patterns.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of success dashboard violations
        """
        violations = []
        
        # Check for dashboard patterns
        dashboard_patterns = ['dashboard', 'metrics', 'kpi', 'analytics', 'report', 'chart']
        has_dashboard = any(pattern in content.lower() for pattern in dashboard_patterns)
        
        if not has_dashboard:
            violations.append(Violation(
                rule_name="Success Dashboards - Show Business Value",
                severity=Severity.INFO,
                message="No dashboard patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Dashboards",
                fix_suggestion="Add dashboards to show business value and success metrics"
            ))
        
        # Check for business value patterns
        business_value_patterns = ['business_value', 'roi', 'revenue', 'profit', 'cost', 'efficiency']
        has_business_value = any(pattern in content.lower() for pattern in business_value_patterns)
        
        if not has_business_value:
            violations.append(Violation(
                rule_name="Success Dashboards - Show Business Value",
                severity=Severity.INFO,
                message="No business value patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Business value",
                fix_suggestion="Add business value metrics and tracking"
            ))
        
        # Check for success metrics
        success_patterns = ['success', 'achievement', 'goal', 'target', 'milestone', 'progress']
        has_success_metrics = any(pattern in content.lower() for pattern in success_patterns)
        
        if not has_success_metrics:
            violations.append(Violation(
                rule_name="Success Dashboards - Show Business Value",
                severity=Severity.INFO,
                message="No success metrics detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Success metrics",
                fix_suggestion="Add success metrics and goal tracking"
            ))
        
        # Check for visualization patterns
        visualization_patterns = ['visualize', 'chart', 'graph', 'plot', 'display', 'show']
        has_visualization = any(pattern in content.lower() for pattern in visualization_patterns)
        
        if not has_visualization:
            violations.append(Violation(
                rule_name="Success Dashboards - Show Business Value",
                severity=Severity.INFO,
                message="No visualization patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Visualization",
                fix_suggestion="Add data visualization for better insights"
            ))
        
        # Check for real-time patterns
        realtime_patterns = ['realtime', 'real_time', 'live', 'streaming', 'instant', 'current']
        has_realtime = any(pattern in content.lower() for pattern in realtime_patterns)
        
        if not has_realtime:
            violations.append(Violation(
                rule_name="Success Dashboards - Show Business Value",
                severity=Severity.INFO,
                message="No real-time patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Real-time",
                fix_suggestion="Add real-time updates for dashboards"
            ))
        
        return violations
    
    def _is_validation_condition(self, if_node: ast.If) -> bool:
        """Check if an if statement contains validation logic."""
        validation_keywords = [
            'isinstance', 'len', 'isdigit', 'isalpha', 'strip', 'lower', 'upper',
            'isnull', 'isempty', 'valid', 'check', 'verify', 'assert', 'raise'
        ]
        
        for node in ast.walk(if_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func).lower()
                if any(keyword in func_name for keyword in validation_keywords):
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
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all problem-solving validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all problem-solving violations
        """
        violations = []
        
        violations.extend(self.validate_real_problems(tree, content, file_path))
        violations.extend(self.validate_proactive_prevention(tree, content, file_path))
        violations.extend(self.validate_accuracy_confidence(tree, content, file_path))
        violations.extend(self.validate_help_people_work_better(tree, content, file_path))
        violations.extend(self.validate_cognitive_load(tree, content, file_path))
        violations.extend(self.validate_behavior_change_engine(tree, content, file_path))
        violations.extend(self.validate_success_dashboards(tree, content, file_path))
        
        return violations

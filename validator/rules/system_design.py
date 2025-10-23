"""
System design rule validator.

This module implements validation for advanced system design rules:
- Rule 22: Make All 18 Modules Look the Same
- Rule 25: Show Information Gradually
- Rule 29: Register Modules the Same Way
- Rule 30: Make All Modules Feel Like One Product
"""

import ast
import re
from typing import List, Dict, Any, Tuple
from ..models import Violation, Severity


class SystemDesignValidator:
    """
    Validates advanced system design rules.
    
    This class focuses on detecting consistency issues, progressive disclosure,
    and unified product experience violations.
    """
    
    def __init__(self):
        """Initialize the system design validator."""
        self.standard_methods = ['__init__', 'setup', 'configure', 'initialize', 'start', 'stop', 'cleanup']
        self.standard_error_types = ['ValueError', 'TypeError', 'RuntimeError', 'ConfigurationError']
        self.standard_return_patterns = ['bool', 'dict', 'list', 'str', 'int', 'None']
        
    def validate_consistent_modules(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for consistent module patterns (Rule 22).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of consistency violations
        """
        violations = []
        
        # Check for inconsistent class naming patterns
        class_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
        
        # Check for inconsistent naming conventions
        naming_patterns = {
            'PascalCase': 0,
            'snake_case': 0,
            'camelCase': 0,
            'UPPER_CASE': 0
        }
        
        for class_name in class_names:
            if re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                naming_patterns['PascalCase'] += 1
            elif re.match(r'^[a-z][a-z0-9_]*$', class_name):
                naming_patterns['snake_case'] += 1
            elif re.match(r'^[a-z][a-zA-Z0-9]*$', class_name):
                naming_patterns['camelCase'] += 1
            elif re.match(r'^[A-Z][A-Z0-9_]*$', class_name):
                naming_patterns['UPPER_CASE'] += 1
        
        # If multiple naming patterns are used, flag inconsistency
        used_patterns = sum(1 for count in naming_patterns.values() if count > 0)
        if used_patterns > 1:
            violations.append(Violation(
                rule_id="rule_22",
                rule_number=22,
                rule_name="Make All 18 Modules Look the Same",
                severity=Severity.WARNING,
                message="Inconsistent naming conventions detected across classes",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Multiple naming patterns",
                fix_suggestion="Use consistent naming convention across all modules"
            ))
        
        # Check for inconsistent error handling
        error_handling_patterns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Name):
                    error_handling_patterns.append(node.exc.id)
        
        # Check if standard error types are used consistently
        non_standard_errors = [error for error in error_handling_patterns 
                              if error not in self.standard_error_types]
        
        if non_standard_errors:
            violations.append(Violation(
                rule_id="rule_22",
                rule_number=22,
                rule_name="Make All 18 Modules Look the Same",
                severity=Severity.INFO,
                message=f"Non-standard error types detected: {non_standard_errors}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(non_standard_errors),
                fix_suggestion="Use standard error types for consistency"
            ))
        
        return violations
    
    def validate_progressive_disclosure(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for progressive disclosure patterns (Rule 25).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of progressive disclosure violations
        """
        violations = []
        
        # Check for functions with too many parameters (information overload)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                
                # Flag functions with more than 5 parameters
                if param_count > 5:
                    violations.append(Violation(
                rule_id="rule_25",
                rule_number=25,
                        rule_name="Show Information Gradually",
                        severity=Severity.WARNING,
                        message=f"Function '{node.name}' has {param_count} parameters - consider progressive disclosure",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Use configuration objects or builder pattern for complex functions"
                    ))
                
                # Check for missing default values (should show basic info first)
                required_params = param_count - len(node.args.defaults)
                if required_params > 3:
                    violations.append(Violation(
                rule_id="rule_25",
                rule_number=25,
                        rule_name="Show Information Gradually",
                        severity=Severity.INFO,
                        message=f"Function '{node.name}' requires {required_params} parameters - consider defaults",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Provide default values for optional parameters"
                    ))
        
        # Check for missing abstraction layers
        complex_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count complexity indicators
                complexity_score = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                        complexity_score += 1
                
                if complexity_score > 5:
                    complex_functions.append((node.name, complexity_score))
        
        if complex_functions:
            violations.append(Violation(
                rule_id="rule_25",
                rule_number=25,
                rule_name="Show Information Gradually",
                severity=Severity.WARNING,
                message=f"Complex functions detected without abstraction layers: {[f[0] for f in complex_functions]}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="High complexity",
                fix_suggestion="Break complex functions into smaller, focused functions"
            ))
        
        return violations
    
    def validate_consistent_registration(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for consistent module registration (Rule 29).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of registration consistency violations
        """
        violations = []
        
        # Check for classes without standard lifecycle methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_methods = [child.name for child in node.body if isinstance(child, ast.FunctionDef)]
                
                # Check for missing standard initialization
                if '__init__' not in class_methods and len(class_methods) > 0:
                    violations.append(Violation(
                rule_id="rule_29",
                rule_number=29,
                        rule_name="Register Modules the Same Way",
                        severity=Severity.WARNING,
                        message=f"Class '{node.name}' missing standard __init__ method",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=node.name,
                        fix_suggestion="Add standard __init__ method for consistent initialization"
                    ))
                
                # Check for inconsistent setup patterns
                setup_methods = [method for method in class_methods 
                               if any(keyword in method.lower() for keyword in ['setup', 'configure', 'init'])]
                
                if len(setup_methods) > 1:
                    violations.append(Violation(
                rule_id="rule_29",
                rule_number=29,
                        rule_name="Register Modules the Same Way",
                        severity=Severity.INFO,
                        message=f"Class '{node.name}' has multiple setup methods: {setup_methods}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=str(setup_methods),
                        fix_suggestion="Use single, consistent setup method"
                    ))
        
        # Check for inconsistent module-level initialization
        module_init_patterns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.targets[0], ast.Name):
                    if 'init' in node.targets[0].id.lower() or 'config' in node.targets[0].id.lower():
                        module_init_patterns.append(node.targets[0].id)
        
        if len(module_init_patterns) > 3:
            violations.append(Violation(
                rule_id="rule_29",
                rule_number=29,
                rule_name="Register Modules the Same Way",
                severity=Severity.INFO,
                message=f"Multiple initialization patterns detected: {module_init_patterns}",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet=str(module_init_patterns),
                fix_suggestion="Use consistent module initialization pattern"
            ))
        
        return violations
    
    def validate_unified_product(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for unified product experience (Rule 30).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of unified product violations
        """
        violations = []
        
        # Check for inconsistent command/function naming
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        # Check for inconsistent naming patterns in functions
        command_patterns = {
            'get_': 0,
            'set_': 0,
            'create_': 0,
            'delete_': 0,
            'update_': 0,
            'process_': 0,
            'handle_': 0
        }
        
        for func_name in function_names:
            for pattern in command_patterns:
                if func_name.startswith(pattern):
                    command_patterns[pattern] += 1
        
        # Check for missing standard command patterns
        used_patterns = sum(1 for count in command_patterns.values() if count > 0)
        if used_patterns > 0 and used_patterns < 3:
            violations.append(Violation(
                rule_id="rule_30",
                rule_number=30,
                rule_name="Make All Modules Feel Like One Product",
                severity=Severity.INFO,
                message="Limited command pattern usage - consider standard CRUD operations",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Command patterns",
                fix_suggestion="Use consistent command naming patterns across modules"
            ))
        
        # Check for inconsistent error message formats
        error_messages = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call):
                    if isinstance(node.exc.args[0], ast.Constant):
                        error_messages.append(node.exc.args[0].value)
        
        # Check for inconsistent error message formats
        if error_messages:
            formats = {
                'sentence_case': 0,
                'title_case': 0,
                'lower_case': 0,
                'no_period': 0
            }
            
            for msg in error_messages:
                if isinstance(msg, str):
                    if msg.endswith('.'):
                        formats['sentence_case'] += 1
                    elif msg.istitle():
                        formats['title_case'] += 1
                    elif msg.islower():
                        formats['lower_case'] += 1
                    else:
                        formats['no_period'] += 1
            
            used_formats = sum(1 for count in formats.values() if count > 0)
            if used_formats > 1:
                violations.append(Violation(
                rule_id="rule_30",
                rule_number=30,
                    rule_name="Make All Modules Feel Like One Product",
                    severity=Severity.INFO,
                    message="Inconsistent error message formats detected",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Error messages",
                    fix_suggestion="Use consistent error message format across all modules"
                ))
        
        return violations
    
    def validate_feature_organization(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for clear feature organization (Rule 26).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of feature organization violations
        """
        violations = []
        
        # Check for proper module organization
        module_structure = {
            'imports': 0,
            'classes': 0,
            'functions': 0,
            'constants': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_structure['imports'] += 1
            elif isinstance(node, ast.ClassDef):
                module_structure['classes'] += 1
            elif isinstance(node, ast.FunctionDef):
                module_structure['functions'] += 1
            elif isinstance(node, ast.Assign):
                # Check if it's a constant (uppercase)
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        module_structure['constants'] += 1
        
        # Check for missing organization patterns
        if module_structure['imports'] == 0:
            violations.append(Violation(
                rule_id="rule_26",
                rule_number=26,
                rule_name="Organize Features Clearly",
                severity=Severity.INFO,
                message="No imports detected - ensure proper module organization",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Module organization",
                fix_suggestion="Organize imports, classes, and functions in clear sections"
            ))
        
        # Check for feature hierarchy
        class_names = []
        function_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        # Check for consistent naming hierarchy
        if len(class_names) > 1:
            # Check if classes follow a naming pattern
            patterns = {
                'Manager': 0,
                'Service': 0,
                'Handler': 0,
                'Controller': 0,
                'Model': 0,
                'View': 0
            }
            
            for class_name in class_names:
                for pattern in patterns:
                    if pattern in class_name:
                        patterns[pattern] += 1
            
            used_patterns = sum(1 for count in patterns.values() if count > 0)
            if used_patterns == 0:
                violations.append(Violation(
                rule_id="rule_26",
                rule_number=26,
                    rule_name="Organize Features Clearly",
                    severity=Severity.INFO,
                    message="No clear feature hierarchy detected in class names",
                    file_path=file_path,
                    line_number=1,
                    column_number=0,
                    code_snippet="Class hierarchy",
                    fix_suggestion="Use consistent naming patterns to organize features clearly"
                ))
        
        return violations
    
    def validate_quick_adoption(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for quick adoption patterns (Rule 31).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of adoption pattern violations
        """
        violations = []
        
        # Check for quick-start patterns
        quick_start_patterns = ['main', 'run', 'start', 'init', 'quick', 'simple', 'basic']
        has_quick_start = any(pattern in content.lower() for pattern in quick_start_patterns)
        
        if not has_quick_start:
            violations.append(Violation(
                rule_id="rule_31",
                rule_number=31,
                rule_name="Design for Quick Adoption",
                severity=Severity.INFO,
                message="No quick-start patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Quick start",
                fix_suggestion="Add quick-start functions for immediate value"
            ))
        
        # Check for onboarding mechanisms
        onboarding_patterns = ['example', 'demo', 'tutorial', 'guide', 'help', 'documentation']
        has_onboarding = any(pattern in content.lower() for pattern in onboarding_patterns)
        
        if not has_onboarding:
            violations.append(Violation(
                rule_id="rule_31",
                rule_number=31,
                rule_name="Design for Quick Adoption",
                severity=Severity.INFO,
                message="No onboarding mechanisms detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Onboarding",
                fix_suggestion="Add examples, demos, or guides for quick adoption"
            ))
        
        # Check for adoption barriers
        barrier_patterns = ['complex', 'difficult', 'hard', 'complicated', 'advanced', 'expert']
        has_barriers = any(pattern in content.lower() for pattern in barrier_patterns)
        
        if has_barriers:
            violations.append(Violation(
                rule_id="rule_31",
                rule_number=31,
                rule_name="Design for Quick Adoption",
                severity=Severity.WARNING,
                message="Potential adoption barriers detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Adoption barriers",
                fix_suggestion="Simplify complex features for easier adoption"
            ))
        
        # Check for immediate value patterns
        value_patterns = ['result', 'output', 'return', 'success', 'complete', 'done']
        has_immediate_value = any(pattern in content.lower() for pattern in value_patterns)
        
        if not has_immediate_value:
            violations.append(Violation(
                rule_id="rule_31",
                rule_number=31,
                rule_name="Design for Quick Adoption",
                severity=Severity.INFO,
                message="No immediate value patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Immediate value",
                fix_suggestion="Ensure users get value in first 30 seconds of use"
            ))
        
        return violations
    
    def validate_user_experience_testing(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Check for user experience testing patterns (Rule 32).
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of UX testing violations
        """
        violations = []
        
        # Check for UX testing patterns
        ux_testing_patterns = ['test', 'testing', 'user_test', 'usability', 'ux_test', 'user_experience']
        has_ux_testing = any(pattern in content.lower() for pattern in ux_testing_patterns)
        
        if not has_ux_testing:
            violations.append(Violation(
                rule_id="rule_32",
                rule_number=32,
                rule_name="Test User Experience",
                severity=Severity.INFO,
                message="No user experience testing patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="UX testing",
                fix_suggestion="Add user experience testing to validate usability"
            ))
        
        # Check for usability metrics
        usability_patterns = ['usability', 'accessibility', 'user_friendly', 'intuitive', 'easy_to_use']
        has_usability = any(pattern in content.lower() for pattern in usability_patterns)
        
        if not has_usability:
            violations.append(Violation(
                rule_id="rule_32",
                rule_number=32,
                rule_name="Test User Experience",
                severity=Severity.INFO,
                message="No usability patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="Usability",
                fix_suggestion="Add usability testing and metrics"
            ))
        
        # Check for user feedback patterns
        feedback_patterns = ['feedback', 'user_feedback', 'survey', 'rating', 'review', 'comment']
        has_feedback = any(pattern in content.lower() for pattern in feedback_patterns)
        
        if not has_feedback:
            violations.append(Violation(
                rule_id="rule_32",
                rule_number=32,
                rule_name="Test User Experience",
                severity=Severity.INFO,
                message="No user feedback patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="User feedback",
                fix_suggestion="Add user feedback collection mechanisms"
            ))
        
        # Check for A/B testing patterns
        ab_testing_patterns = ['ab_test', 'a_b_test', 'experiment', 'variant', 'control', 'treatment']
        has_ab_testing = any(pattern in content.lower() for pattern in ab_testing_patterns)
        
        if not has_ab_testing:
            violations.append(Violation(
                rule_id="rule_32",
                rule_number=32,
                rule_name="Test User Experience",
                severity=Severity.INFO,
                message="No A/B testing patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="A/B testing",
                fix_suggestion="Add A/B testing for user experience validation"
            ))
        
        # Check for user journey patterns
        journey_patterns = ['user_journey', 'user_flow', 'workflow', 'process', 'steps', 'path']
        has_journey = any(pattern in content.lower() for pattern in journey_patterns)
        
        if not has_journey:
            violations.append(Violation(
                rule_id="rule_32",
                rule_number=32,
                rule_name="Test User Experience",
                severity=Severity.INFO,
                message="No user journey patterns detected",
                file_path=file_path,
                line_number=1,
                column_number=0,
                code_snippet="User journey",
                fix_suggestion="Add user journey testing and optimization"
            ))
        
        return violations
    
    def validate_all(self, tree: ast.AST, content: str, file_path: str) -> List[Violation]:
        """
        Run all system design validations.
        
        Args:
            tree: AST tree of the code
            content: File content
            file_path: Path to the file
            
        Returns:
            List of all system design violations
        """
        violations = []
        
        violations.extend(self.validate_consistent_modules(tree, content, file_path))
        violations.extend(self.validate_progressive_disclosure(tree, content, file_path))
        violations.extend(self.validate_consistent_registration(tree, content, file_path))
        violations.extend(self.validate_unified_product(tree, content, file_path))
        violations.extend(self.validate_feature_organization(tree, content, file_path))
        violations.extend(self.validate_quick_adoption(tree, content, file_path))
        violations.extend(self.validate_user_experience_testing(tree, content, file_path))
        
        return violations

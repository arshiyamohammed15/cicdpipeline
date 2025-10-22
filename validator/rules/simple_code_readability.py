"""
Simple Code Readability Validator (Rules 253-280)

Validates that code is simple and readable for anyone, even an 8th grader.
Enforces human-understandable code patterns and bans advanced concepts.
"""

import re
import ast
from typing import List, Dict, Any
from validator.models import Violation, Severity


class SimpleCodeReadabilityValidator:
    """Validator for simple code readability rules (253-280)."""
    
    def __init__(self):
        """Initialize the validator."""
        self.rules = {
            'R253': self._validate_plain_english_names,
            'R254': self._validate_self_documenting_code,
            'R255': self._validate_one_concept_per_function,
            'R256': self._validate_comment_why_not_what,
            'R257': self._validate_avoid_mental_gymnastics,
            'R258': self._validate_real_world_analogies,
            'R259': self._validate_progressive_complexity,
            'R260': self._validate_visual_layout,
            'R261': self._validate_helpful_error_messages,
            'R262': self._validate_consistent_naming,
            'R263': self._validate_avoid_abbreviations,
            'R264': self._validate_business_language,
            'R265': self._validate_show_work,
            'R266': self._validate_fail_gracefully,
            'R267': self._validate_code_as_documentation,
            'R268': self._validate_test_names,
            'R269': self._validate_constants_explain,
            'R270': self._validate_no_advanced_concepts,
            'R271': self._validate_no_complex_data_structures,
            'R272': self._validate_no_advanced_string_manipulation,
            'R273': self._validate_no_complex_error_handling,
            'R274': self._validate_no_advanced_control_flow,
            'R275': self._validate_no_advanced_functions,
            'R276': self._validate_no_advanced_array_operations,
            'R277': self._validate_no_advanced_logic,
            'R278': self._validate_no_advanced_language_features,
            'R279': self._validate_no_advanced_libraries,
            'R280': self._validate_enforce_simple_level
        }
    
    def validate(self, content: str, file_path: str) -> List[Violation]:
        """Validate content against all simple code readability rules."""
        violations = []
        
        for rule_id, rule_func in self.rules.items():
            try:
                rule_violations = rule_func(content, file_path)
                violations.extend(rule_violations)
            except Exception as e:
                # Add error violation for rule failure
                violations.append(Violation(
                    rule_id=rule_id,
                    severity=Severity.ERROR,
                    message=f"Rule validation failed: {str(e)}",
                    file_path=file_path,
                    line_number=1
                ))
        
        return violations
    
    def _validate_plain_english_names(self, content: str, file_path: str) -> List[Violation]:
        """Rule 253: Plain English variable names."""
        violations = []
        
        # Common abbreviations to flag
        abbreviations = [
            r'\busr\b|usr_', r'\bctx\b|ctx_', r'\bmgr\b|mgr_', r'\bcalc\b|calc_', r'\bcfg\b|cfg_',
            r'\bconn\b|conn_', r'\bpool\b|pool_', r'\bproc\b|proc_', r'\btemp\b|temp_', r'\bvar\b|var_'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for abbrev_pattern in abbreviations:
                match = re.search(abbrev_pattern, line, re.IGNORECASE)
                if match:
                    violations.append(Violation(
                        rule_id='R253',
                        severity=Severity.ERROR,
                        message=f"Variable name contains abbreviation. Use full words instead of '{match.group()}'",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_self_documenting_code(self, content: str, file_path: str) -> List[Violation]:
        """Rule 254: Self-documenting code."""
        violations = []
        
        # Patterns for cryptic code
        cryptic_patterns = [
            (r'\b[a-z]\b.*=.*[a-z]\b', "Single letter variables"),
            (r'\bcalc\b', "Cryptic function name 'calc'"),
            (r'\bproc\b', "Cryptic function name 'proc'"),
            (r'if\s+[a-z]\s*[><=]', "Cryptic variable in condition")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in cryptic_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R254',
                        severity=Severity.ERROR,
                        message=f"Code is not self-documenting: {message}",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_one_concept_per_function(self, content: str, file_path: str) -> List[Violation]:
        """Rule 255: One concept per function."""
        violations = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check function length
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                    if func_lines > 20:
                        violations.append(Violation(
                            rule_id='R255',
                            severity=Severity.ERROR,
                            message=f"Function '{node.name}' has {func_lines} lines. Maximum allowed is 20 lines.",
                            file_path=file_path,
                            line_number=node.lineno
                        ))
                    
                    # Check for multiple concepts (simplified heuristic)
                    if len(node.body) > 5:  # More than 5 statements suggests multiple concepts
                        violations.append(Violation(
                            rule_id='R255',
                            severity=Severity.ERROR,
                            message=f"Function '{node.name}' appears to do multiple things. Break into smaller functions.",
                            file_path=file_path,
                            line_number=node.lineno
                        ))
        except SyntaxError:
            pass  # Skip parsing errors
        
        return violations
    
    def _validate_comment_why_not_what(self, content: str, file_path: str) -> List[Violation]:
        """Rule 256: Explain the 'why', not just the 'what'."""
        violations = []
        
        # Comments that only explain what
        what_only_patterns = [
            r'#\s*Increment\s+counter',
            r'#\s*Loop\s+through\s+array',
            r'#\s*Set\s+variable',
            r'#\s*Return\s+value'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in what_only_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R256',
                        severity=Severity.ERROR,
                        message="Comment only explains 'what'. Explain 'why' instead.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_avoid_mental_gymnastics(self, content: str, file_path: str) -> List[Violation]:
        """Rule 257: Avoid mental gymnastics."""
        violations = []
        
        # Nested ternary patterns
        nested_ternary = r'\?.*\?.*\?'
        complex_oneliner = r'return.*\?.*\?'
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if re.search(nested_ternary, line):
                violations.append(Violation(
                    rule_id='R257',
                    severity=Severity.ERROR,
                    message="Nested ternary operators detected. Use clear if-else statements instead.",
                    file_path=file_path,
                    line_number=line_num
                ))
            
            if re.search(complex_oneliner, line):
                violations.append(Violation(
                    rule_id='R257',
                    severity=Severity.ERROR,
                    message="Complex one-liner detected. Break into simple steps.",
                    file_path=file_path,
                    line_number=line_num
                ))
        
        return violations
    
    def _validate_real_world_analogies(self, content: str, file_path: str) -> List[Violation]:
        """Rule 258: Use real-world analogies."""
        violations = []
        
        # Technical jargon without analogies
        technical_jargon = [
            r'database\s+connection\s+pooling',
            r'api\s+rate\s+limiting',
            r'object\s+instantiation',
            r'memory\s+allocation'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for jargon in technical_jargon:
                if re.search(jargon, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R258',
                        severity=Severity.ERROR,
                        message="Technical jargon detected. Use real-world analogies to explain concepts.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_progressive_complexity(self, content: str, file_path: str) -> List[Violation]:
        """Rule 259: Progressive complexity."""
        violations = []
        
        # Look for very long functions (monolithic)
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                    if func_lines > 50:  # Very long function
                        violations.append(Violation(
                            rule_id='R259',
                            severity=Severity.ERROR,
                            message=f"Function '{node.name}' is too complex ({func_lines} lines). Break into smaller functions.",
                            file_path=file_path,
                            line_number=node.lineno
                        ))
        except SyntaxError:
            pass
        
        return violations
    
    def _validate_visual_layout(self, content: str, file_path: str) -> List[Violation]:
        """Rule 260: Visual code layout."""
        violations = []
        
        lines = content.split('\n')
        consecutive_code_lines = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Count consecutive non-empty, non-comment lines
            if stripped and not stripped.startswith('#'):
                consecutive_code_lines += 1
            else:
                consecutive_code_lines = 0
            
            # Flag if too many consecutive lines without whitespace
            if consecutive_code_lines > 10:
                violations.append(Violation(
                    rule_id='R260',
                    severity=Severity.ERROR,
                    message="Too many consecutive lines without whitespace. Add blank lines to group related code.",
                    file_path=file_path,
                    line_number=line_num
                ))
        
        return violations
    
    def _validate_helpful_error_messages(self, content: str, file_path: str) -> List[Violation]:
        """Rule 261: Error messages that help."""
        violations = []
        
        # Cryptic error messages
        cryptic_errors = [
            r'Error\s+\d+',
            r'Invalid\s+format',
            r'Null\s+pointer\s+exception',
            r'Validation\s+failed'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in cryptic_errors:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R261',
                        severity=Severity.ERROR,
                        message="Cryptic error message detected. Provide helpful guidance to users.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_consistent_naming(self, content: str, file_path: str) -> List[Violation]:
        """Rule 262: Consistent naming patterns."""
        violations = []
        
        # Mixed terms for same concept
        mixed_terms = [
            (r'\buser\b', r'\busr\b', "user/usr"),
            (r'\buser\b', r'\bcustomer\b', "user/customer"),
            (r'\bget\b', r'\bfetch\b', "get/fetch"),
            (r'\bget\b', r'\bretrieve\b', "get/retrieve")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for term1, term2, description in mixed_terms:
                if re.search(term1, line, re.IGNORECASE) and re.search(term2, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R262',
                        severity=Severity.ERROR,
                        message=f"Inconsistent naming: mixing {description}. Use the same term throughout.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_avoid_abbreviations(self, content: str, file_path: str) -> List[Violation]:
        """Rule 263: Avoid abbreviations."""
        violations = []
        
        # Common abbreviations to avoid (excluding allowed ones)
        banned_abbreviations = [
            r'\bcalc\b', r'\bmgr\b', r'\bctx\b', r'\bproc\b', r'\btemp\b',
            r'\bvar\b', r'\bconn\b', r'\bpool\b'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for abbrev in banned_abbreviations:
                if re.search(abbrev, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R263',
                        severity=Severity.ERROR,
                        message=f"Abbreviation detected: '{re.search(abbrev, line, re.IGNORECASE).group()}'. Use full words instead.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_business_language(self, content: str, file_path: str) -> List[Violation]:
        """Rule 264: Business language over technical language."""
        violations = []
        
        # Technical language patterns
        technical_patterns = [
            r'execute\s+database\s+transaction',
            r'initialize\s+object\s+instance',
            r'instantiate\s+class',
            r'allocate\s+memory'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in technical_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R264',
                        severity=Severity.ERROR,
                        message="Technical language detected. Use business language that users understand.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_show_work(self, content: str, file_path: str) -> List[Violation]:
        """Rule 265: Show your work."""
        violations = []
        
        # Complex expressions without intermediate steps
        complex_expressions = [
            r'return\s+\([^)]*\)\s*\+\s*\([^)]*\)\s*-\s*\([^)]*\)',
            r'return\s+[^=]*\*[^=]*\*[^=]*\*[^=]*',
            r'return\s+[^=]*\+[^=]*\+[^=]*\+[^=]*'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in complex_expressions:
                if re.search(pattern, line):
                    violations.append(Violation(
                        rule_id='R265',
                        severity=Severity.ERROR,
                        message="Complex expression detected. Break into steps with intermediate variables.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_fail_gracefully(self, content: str, file_path: str) -> List[Violation]:
        """Rule 266: Fail gracefully with helpful messages."""
        violations = []
        
        # Cryptic error messages
        cryptic_errors = [
            r'Validation\s+failed',
            r'Error\s+occurred',
            r'Invalid\s+input',
            r'Operation\s+failed'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in cryptic_errors:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R266',
                        severity=Severity.ERROR,
                        message="Cryptic error message detected. Provide specific guidance on what to do.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_code_as_documentation(self, content: str, file_path: str) -> List[Violation]:
        """Rule 267: Code as documentation."""
        violations = []
        
        # Excessive comments explaining what code does
        what_comments = [
            r'#\s*Multiply\s+.*\s+by\s+.*\s+to\s+get',
            r'#\s*Add\s+.*\s+and\s+.*\s+to\s+get',
            r'#\s*Return\s+the\s+result',
            r'#\s*Set\s+.*\s+to\s+.*'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in what_comments:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R267',
                        severity=Severity.ERROR,
                        message="Comment explains 'what' code does. Code should be self-documenting.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_test_names(self, content: str, file_path: str) -> List[Violation]:
        """Rule 268: Test names that tell a story."""
        violations = []
        
        # Generic test names
        generic_test_names = [
            r'def\s+test_user\(\)',
            r'def\s+test_error\(\)',
            r'def\s+test_function\(\)',
            r'def\s+test_data\(\)'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in generic_test_names:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R268',
                        severity=Severity.ERROR,
                        message="Generic test name detected. Use descriptive names that tell a story.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_constants_explain(self, content: str, file_path: str) -> List[Violation]:
        """Rule 269: Constants that explain themselves."""
        violations = []
        
        # Magic numbers without explanation
        magic_numbers = [
            r'if\s+.*\s*>\s*18\b',
            r'timeout\s*=\s*5000\b',
            r'max_size\s*=\s*1048576\b',
            r'default_timeout\s*=\s*30\b'
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in magic_numbers:
                if re.search(pattern, line):
                    violations.append(Violation(
                        rule_id='R269',
                        severity=Severity.ERROR,
                        message="Magic number detected. Use named constants that explain themselves.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_concepts(self, content: str, file_path: str) -> List[Violation]:
        """Rule 270: NO advanced programming concepts."""
        violations = []
        
        # Advanced concepts to ban
        advanced_concepts = [
            (r'lambda\s+', "Lambda functions"),
            (r'@\w+', "Decorators"),
            (r'async\s+def', "Async functions"),
            (r'await\s+', "Await expressions"),
            (r'yield\s+', "Yield expressions"),
            (r'generator\s+', "Generators")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, concept in advanced_concepts:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R270',
                        severity=Severity.ERROR,
                        message=f"Advanced concept detected: {concept}. Use simple programming concepts only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_complex_data_structures(self, content: str, file_path: str) -> List[Violation]:
        """Rule 271: NO complex data structures."""
        violations = []
        
        # Complex data structure patterns
        complex_patterns = [
            (r'\{[^}]*\{[^}]*\{', "Nested dictionaries"),
            (r'\[[^\]]*\{[^}]*\}[^\]]*\]', "Array of objects"),
            (r'hashmap|hash_map', "Hash maps"),
            (r'linked_list|linkedlist', "Linked lists")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, structure in complex_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R271',
                        severity=Severity.ERROR,
                        message=f"Complex data structure detected: {structure}. Use simple arrays and objects only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_string_manipulation(self, content: str, file_path: str) -> List[Violation]:
        """Rule 272: NO advanced string manipulation."""
        violations = []
        
        # Advanced string operations
        advanced_string_ops = [
            (r'import\s+re', "Regular expressions"),
            (r're\.', "Regular expression usage"),
            (r'f["\']', "F-strings/template literals"),
            (r'\.format\(', "String formatting"),
            (r'base64|encoding|decoding', "Encoding/decoding")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, operation in advanced_string_ops:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R272',
                        severity=Severity.ERROR,
                        message=f"Advanced string operation detected: {operation}. Use simple string operations only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_complex_error_handling(self, content: str, file_path: str) -> List[Violation]:
        """Rule 273: NO complex error handling."""
        violations = []
        
        # Complex error handling patterns
        complex_error_patterns = [
            (r'try\s*:', "Try-catch blocks"),
            (r'except\s+', "Exception handling"),
            (r'raise\s+', "Raising exceptions"),
            (r'class\s+\w+Exception', "Custom exceptions"),
            (r'finally\s*:', "Finally blocks")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, handling in complex_error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R273',
                        severity=Severity.ERROR,
                        message=f"Complex error handling detected: {handling}. Use simple if-else checks only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_control_flow(self, content: str, file_path: str) -> List[Violation]:
        """Rule 274: NO advanced control flow."""
        violations = []
        
        # Advanced control flow patterns
        advanced_control_flow = [
            (r'switch\s*\(|case\s+', "Switch statements"),
            (r'goto\s+', "Goto statements"),
            (r'break\s*;|continue\s*;', "Break/continue statements"),
            (r'def\s+\w+\([^)]*\):\s*.*\n\s*return\s+\w+\([^)]*\)', "Recursion")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, flow in advanced_control_flow:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R274',
                        severity=Severity.ERROR,
                        message=f"Advanced control flow detected: {flow}. Use simple if-else and basic loops only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_functions(self, content: str, file_path: str) -> List[Violation]:
        """Rule 275: NO advanced functions."""
        violations = []
        
        # Advanced function patterns
        advanced_functions = [
            (r'def\s+\w+\([^)]*=\s*[^,)]+', "Default parameters"),
            (r'\*\w+|\*\*\w+', "Variable arguments"),
            (r'def\s+\w+\([^)]*\):\s*.*\n\s*return\s+\w+\(', "Higher-order functions")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, function_type in advanced_functions:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R275',
                        severity=Severity.ERROR,
                        message=f"Advanced function detected: {function_type}. Use simple functions with basic parameters only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_array_operations(self, content: str, file_path: str) -> List[Violation]:
        """Rule 276: NO advanced array operations."""
        violations = []
        
        # Advanced array operations
        advanced_array_ops = [
            (r'\.map\s*\(', "Map function"),
            (r'\.filter\s*\(', "Filter function"),
            (r'\.reduce\s*\(', "Reduce function"),
            (r'\[.*for.*in.*\]', "List comprehensions"),
            (r'\.forEach\s*\(', "ForEach function")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, operation in advanced_array_ops:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R276',
                        severity=Severity.ERROR,
                        message=f"Advanced array operation detected: {operation}. Use simple for loops only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_logic(self, content: str, file_path: str) -> List[Violation]:
        """Rule 277: NO advanced logic."""
        violations = []
        
        # Advanced logic patterns
        advanced_logic = [
            (r'[&|^~]', "Bitwise operations"),
            (r'\([^)]*and[^)]*\)\s*or\s*\([^)]*and[^)]*\)', "Complex boolean algebra"),
            (r'not\s+.*and\s+.*or\s+', "Complex boolean logic")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, logic_type in advanced_logic:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R277',
                        severity=Severity.ERROR,
                        message=f"Advanced logic detected: {logic_type}. Use simple true/false checks only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_language_features(self, content: str, file_path: str) -> List[Violation]:
        """Rule 278: NO advanced language features."""
        violations = []
        
        # Advanced language features
        advanced_features = [
            (r'from\s+typing\s+import', "Type hints/generics"),
            (r'class\s+\w+\(metaclass=', "Metaclasses"),
            (r'__\w+__', "Magic methods"),
            (r'property\s*\(', "Property decorators")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, feature in advanced_features:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R278',
                        severity=Severity.ERROR,
                        message=f"Advanced language feature detected: {feature}. Use basic language syntax only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_no_advanced_libraries(self, content: str, file_path: str) -> List[Violation]:
        """Rule 279: NO advanced libraries."""
        violations = []
        
        # Advanced libraries to ban
        advanced_libraries = [
            (r'import\s+pandas', "Pandas library"),
            (r'import\s+numpy', "NumPy library"),
            (r'import\s+requests', "Requests library"),
            (r'from\s+django', "Django framework"),
            (r'from\s+flask', "Flask framework"),
            (r'import\s+fastapi', "FastAPI framework")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, library in advanced_libraries:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R279',
                        severity=Severity.ERROR,
                        message=f"Advanced library detected: {library}. Use basic language built-ins only.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations
    
    def _validate_enforce_simple_level(self, content: str, file_path: str) -> List[Violation]:
        """Rule 280: ENFORCE simple level."""
        violations = []
        
        # Check for complex code that 8th grader can't understand
        complex_patterns = [
            (r'\([^)]*\)\s*\+\s*\([^)]*\)\s*-\s*\([^)]*\)\s*/\s*\([^)]*\)', "Complex mathematical expressions"),
            (r'\([^)]*and[^)]*\)\s*or\s*\([^)]*and[^)]*\)\s*and\s*\([^)]*or[^)]*\)', "Complex boolean logic"),
            (r'entity_aggregation|instantiation|allocation', "Technical jargon without explanation")
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, issue in complex_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id='R280',
                        severity=Severity.ERROR,
                        message=f"Complex code detected: {issue}. Code must be understandable by an 8th grader.",
                        file_path=file_path,
                        line_number=line_num
                    ))
        
        return violations

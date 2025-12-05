#!/usr/bin/env python3
"""
Comprehensive fix for all remaining test errors.
Fixes each error type systematically.
"""
from pathlib import Path
import re
import ast

def fix_sys_imports(file_path: Path) -> bool:
    """Add missing sys imports."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Check if file uses sys but doesn't import it
        if 'sys.modules' in content or 'sys.path' in content:
            if 'import sys' not in content and 'from sys import' not in content:
                # Add import at the top after docstring
                lines = content.split('\n')
                new_lines = []
                added_import = False
                in_docstring = False
                
                for i, line in enumerate(lines):
                    if not added_import:
                        # Check if we're past docstring
                        if line.strip().startswith('"""') or line.strip().startswith("'''"):
                            in_docstring = not in_docstring
                            new_lines.append(line)
                            continue
                        elif in_docstring:
                            new_lines.append(line)
                            continue
                        elif line.strip() and not line.strip().startswith('#'):
                            # Add import before first non-comment line
                            if 'from __future__' in line:
                                new_lines.append(line)
                                new_lines.append('import sys')
                                added_import = True
                            else:
                                new_lines.append('import sys')
                                new_lines.append(line)
                                added_import = True
                            continue
                    
                    new_lines.append(line)
                
                if added_import:
                    content = '\n'.join(new_lines)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing sys imports in {file_path}: {e}")
        return False

def fix_syntax_errors(file_path: Path) -> bool:
    """Fix syntax errors by validating and fixing Python syntax."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Try to parse the file to find syntax errors
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError as e:
            # Fix common syntax error patterns
            lines = content.split('\n')
            error_line = e.lineno - 1 if e.lineno else 0
            
            # Fix common patterns
            # Pattern 1: Missing closing parenthesis/bracket
            if error_line < len(lines):
                line = lines[error_line]
                # Count parentheses
                open_parens = line.count('(') - line.count(')')
                open_brackets = line.count('[') - line.count(']')
                open_braces = line.count('{') - line.count('}')
                
                # Pattern 2: Broken string literals
                if "'" in line or '"' in line:
                    # Try to fix unclosed strings
                    if line.count("'") % 2 != 0:
                        lines[error_line] = line + "'"
                    elif line.count('"') % 2 != 0:
                        lines[error_line] = line + '"'
            
            # Pattern 3: Remove broken backslash continuations
            content = '\n'.join(lines)
            content = re.sub(r'\\napp = create_app\(\)', '', content)
            content = re.sub(r'create_app\\napp = create_app', 'app', content)
            
            # Pattern 4: Fix broken imports
            content = re.sub(
                r'from\s+health_reliability_monitoring\.main import create_app\s+app = create_app\(\)',
                'from health_reliability_monitoring.main import app',
                content,
                flags=re.MULTILINE
            )
            
            # Try parsing again
            try:
                ast.parse(content)
                file_path.write_text(content, encoding='utf-8')
                return True
            except SyntaxError:
                pass  # Couldn't auto-fix
        
        return False
    except Exception as e:
        print(f"Error fixing syntax in {file_path}: {e}")
        return False

def fix_indentation_errors(file_path: Path) -> bool:
    """Fix indentation errors."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        lines = content.split('\n')
        new_lines = []
        indent_stack = [0]  # Track indentation levels
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                new_lines.append('')
                continue
            
            # Calculate expected indentation
            current_indent = len(line) - len(stripped)
            
            # Check for dedent keywords
            if stripped.startswith(('else:', 'elif ', 'except', 'finally:', 'elif:')):
                if len(indent_stack) > 1:
                    indent_stack.pop()
            
            # Get expected indent from stack
            expected_indent = indent_stack[-1]
            
            # Fix if indentation is wrong
            if current_indent != expected_indent and current_indent % 4 != expected_indent % 4:
                # Try to fix by aligning to expected
                new_lines.append(' ' * expected_indent + stripped)
            else:
                new_lines.append(line)
            
            # Update indent stack for next line
            if stripped.endswith(':'):
                indent_stack.append(expected_indent + 4)
            elif stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'with ')):
                if not stripped.endswith(':'):
                    indent_stack.append(expected_indent + 4)
        
        content = '\n'.join(new_lines)
        
        # Validate with AST
        try:
            ast.parse(content)
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True
        except SyntaxError:
            pass  # Indentation fix didn't work
        
        return False
    except Exception as e:
        print(f"Error fixing indentation in {file_path}: {e}")
        return False

def fix_relative_imports(file_path: Path) -> bool:
    """Convert relative imports to absolute imports."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Determine module from path
        parts = file_path.parts
        module_map = None
        
        if 'budgeting_rate_limiting_cost_observability' in parts:
            module_map = 'budgeting_rate_limiting_cost_observability'
        elif 'health_reliability_monitoring' in parts:
            module_map = 'health_reliability_monitoring'
        elif 'evidence_receipt_indexing_service' in parts:
            module_map = 'evidence_receipt_indexing_service'
        elif 'integration_adapters' in parts:
            module_map = 'integration_adapters'
        elif 'detection_engine_core' in parts:
            module_map = 'detection_engine_core'
        elif 'signal_ingestion_normalization' in parts:
            module_map = 'signal_ingestion_normalization'
        elif 'user_behaviour_intelligence' in parts:
            module_map = 'user_behaviour_intelligence'
        elif 'identity_access_management' in parts:
            module_map = 'identity_access_management'
        elif 'key_management_service' in parts:
            module_map = 'key_management_service'
        elif 'mmm_engine' in parts:
            module_map = 'mmm_engine'
        
        if module_map:
            # Convert relative imports
            patterns = [
                (r'from\s+\.\.database\s+import', f'from {module_map}.database import'),
                (r'from\s+\.\.services\s+import', f'from {module_map}.services import'),
                (r'from\s+\.\.dependencies\s+import', f'from {module_map}.dependencies import'),
                (r'from\s+\.\.models\s+import', f'from {module_map}.models import'),
                (r'from\s+\.\.routes\s+import', f'from {module_map}.routes import'),
                (r'from\s+\.\.main\s+import', f'from {module_map}.main import'),
                (r'from\s+\.\.config\s+import', f'from {module_map}.config import'),
                (r'from\s+\.database\s+import', f'from {module_map}.database import'),
                (r'from\s+\.services\s+import', f'from {module_map}.services import'),
                (r'from\s+\.models\s+import', f'from {module_map}.models import'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing relative imports in {file_path}: {e}")
        return False

def fix_budgeting_database_imports(file_path: Path) -> bool:
    """Fix budgeting database import paths."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        content = re.sub(
            r'tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database',
            'budgeting_rate_limiting_cost_observability.database',
            content
        )
        content = re.sub(
            r'from\s+tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database',
            'from budgeting_rate_limiting_cost_observability.database',
            content
        )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing budgeting imports in {file_path}: {e}")
        return False

def fix_other_errors(file_path: Path) -> bool:
    """Fix other common errors."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix key-management-service imports
        content = re.sub(
            r'from\s+key-management-service',
            'from key_management_service',
            content
        )
        
        # Fix incorrect paths
        content = re.sub(
            r'tests/cloud_services/src/cloud_services',
            'src/cloud_services',
            content
        )
        
        # Fix health_reliability_monitoring router import
        if 'from health_reliability_monitoring.routes import router' in content:
            # Check if routes.py has router
            routes_path = Path('src/cloud_services/shared-services/health-reliability-monitoring/routes.py')
            if routes_path.exists():
                routes_content = routes_path.read_text(encoding='utf-8')
                if 'router = ' not in routes_content and 'router = APIRouter' not in routes_content:
                    # Router doesn't exist, remove the import
                    content = re.sub(
                        r'from\s+health_reliability_monitoring\.routes\s+import\s+router[,\s]*',
                        '',
                        content
                    )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing other issues in {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    tests_dir = Path('tests')
    fixed = 0
    
    # Get all Python test files
    test_files = list(tests_dir.rglob('*.py'))
    print(f"Processing {len(test_files)} test files...")
    
    for test_file in test_files:
        file_fixed = False
        
        # Apply all fixes
        if fix_sys_imports(test_file):
            file_fixed = True
        if fix_relative_imports(test_file):
            file_fixed = True
        if fix_budgeting_database_imports(test_file):
            file_fixed = True
        if fix_other_errors(test_file):
            file_fixed = True
        if fix_syntax_errors(test_file):
            file_fixed = True
        if fix_indentation_errors(test_file):
            file_fixed = True
        
        if file_fixed:
            fixed += 1
            if fixed % 20 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()


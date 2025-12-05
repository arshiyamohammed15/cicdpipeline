#!/usr/bin/env python3
"""
Fix indentation errors in test files.
"""
from pathlib import Path
import re
import ast

def fix_indentation_error(file_path: Path) -> tuple[bool, str]:
    """Fix indentation errors in a file."""
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
            
            # Calculate current indentation
            current_indent = len(line) - len(stripped)
            
            # Check for dedent keywords
            if stripped.startswith(('else:', 'elif ', 'except', 'finally:', 'elif:')):
                if len(indent_stack) > 1:
                    indent_stack.pop()
            
            # Get expected indent from stack
            expected_indent = indent_stack[-1]
            
            # Fix indentation if wrong
            # Check if it's a multiple of 4 and close to expected
            if current_indent != expected_indent:
                # Try to align to expected if close
                if abs(current_indent - expected_indent) <= 4:
                    new_lines.append(' ' * expected_indent + stripped)
                else:
                    # Keep original but try to fix obvious issues
                    # If indentation is way off, align to nearest 4-space boundary
                    aligned_indent = (current_indent // 4) * 4
                    if abs(aligned_indent - expected_indent) <= 4:
                        new_lines.append(' ' * expected_indent + stripped)
                    else:
                        new_lines.append(line)  # Keep original
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
                return True, "Fixed"
            return False, "No indentation errors"
        except (SyntaxError, IndentationError) as e:
            # Try a different approach - fix based on error location
            if hasattr(e, 'lineno') and e.lineno:
                error_line_idx = e.lineno - 1
                if error_line_idx < len(new_lines):
                    error_line = new_lines[error_line_idx]
                    # Try to fix by aligning to previous line's indentation
                    if error_line_idx > 0:
                        prev_line = new_lines[error_line_idx - 1]
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        if prev_line.strip().endswith(':'):
                            # Should be indented more
                            new_lines[error_line_idx] = ' ' * (prev_indent + 4) + error_line.lstrip()
                        else:
                            # Should match previous
                            new_lines[error_line_idx] = ' ' * prev_indent + error_line.lstrip()
                    
                    content = '\n'.join(new_lines)
                    try:
                        ast.parse(content)
                        if content != original:
                            file_path.write_text(content, encoding='utf-8')
                            return True, "Fixed"
                    except:
                        pass
            
            return False, f"Could not fix: {str(e)}"
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def main():
    """Main entry point."""
    error_files = [
        'tests/test_configuration_policy_management_service.py',
        'tests/test_constitution_comprehensive_runner.py',
        'tests/test_constitution_rule_semantics.py',
        'tests/test_contracts_schema_registry_api.py',
        'tests/test_deterministic_enforcement.py',
        'tests/test_enforcement_flow.py',
        'tests/test_iam_routes.py',
        'tests/test_ollama_ai_service.py',
        'tests/test_post_generation_validator.py',
        'tests/test_pre_implementation_artifacts.py',
    ]
    
    print(f"Fixing indentation errors in {len(error_files)} files...")
    
    fixed_count = 0
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        fixed, message = fix_indentation_error(file_path)
        if fixed:
            fixed_count += 1
            print(f"  Fixed: {file_path_str}")
        else:
            print(f"  Could not fix: {file_path_str} - {message}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()


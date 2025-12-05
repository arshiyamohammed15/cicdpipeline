#!/usr/bin/env python3
"""
Fix syntax errors by compiling each file and fixing the specific error.
"""
from pathlib import Path
import re
import ast
import py_compile
import subprocess

def find_syntax_error_files():
    """Find all files with syntax errors by trying to compile them."""
    tests_dir = Path('tests')
    error_files = []
    
    for test_file in tests_dir.rglob('*.py'):
        try:
            py_compile.compile(str(test_file), doraise=True)
        except py_compile.PyCompileError as e:
            error_files.append((test_file, str(e)))
        except SyntaxError as e:
            error_files.append((test_file, f"SyntaxError: {e.msg} at line {e.lineno}"))
    
    return error_files

def fix_file_syntax(file_path: Path, error_msg: str) -> tuple[bool, str]:
    """Fix syntax error in a file based on error message."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix 1: PowerShell backticks
        if '`n' in content:
            content = content.replace('`n', '\n')
        if '`t' in content:
            content = content.replace('`t', '\t')
        
        # Fix 2: Broken imports
        content = re.sub(r'import\s+(\w+)`nimport', r'import \1\nimport', content)
        content = re.sub(r'import\s+(\w+)\s*`n\s*import', r'import \1\nimport', content)
        
        # Fix 3: Try to parse and fix based on AST error
        try:
            ast.parse(content)
            # If parsing succeeds, write the fixed content
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True, "Fixed"
            return False, "No syntax errors"
        except SyntaxError as e:
            # Try to fix based on error location
            lines = content.split('\n')
            error_line_idx = e.lineno - 1 if e.lineno else 0
            
            if error_line_idx < len(lines):
                error_line = lines[error_line_idx]
                
                # Fix empty blocks
                if re.match(r'^\s+(if|for|while|try|except|with|elif|else)\s+.*:\s*$', error_line):
                    indent = len(error_line) - len(error_line.lstrip())
                    # Check if next line is empty or dedented
                    next_idx = error_line_idx + 1
                    while next_idx < len(lines) and not lines[next_idx].strip():
                        next_idx += 1
                    
                    if next_idx >= len(lines) or len(lines[next_idx]) - len(lines[next_idx].lstrip()) <= indent:
                        # Empty block - add pass
                        lines.insert(error_line_idx + 1, ' ' * (indent + 4) + 'pass')
                        content = '\n'.join(lines)
                
                # Fix unclosed parentheses (basic)
                if 'unexpected EOF' in str(e) or 'invalid syntax' in str(e):
                    # Count parentheses
                    open_parens = content.count('(') - content.count(')')
                    open_brackets = content.count('[') - content.count(']')
                    open_braces = content.count('{') - content.count('}')
                    
                    # Don't auto-fix as it's risky
                    pass
            
            # Try parsing again
            try:
                ast.parse(content)
                if content != original:
                    file_path.write_text(content, encoding='utf-8')
                    return True, "Fixed"
            except SyntaxError:
                pass
        
        return False, f"Could not auto-fix: {error_msg}"
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def main():
    """Main entry point."""
    print("Finding files with syntax errors...")
    error_files = find_syntax_error_files()
    print(f"Found {len(error_files)} files with syntax errors")
    
    fixed_count = 0
    failed_files = []
    
    for file_path, error_msg in error_files:
        fixed, message = fix_file_syntax(file_path, error_msg)
        if fixed:
            fixed_count += 1
            print(f"  Fixed: {file_path}")
        else:
            failed_files.append((file_path, message))
            if len(failed_files) <= 5:
                print(f"  Could not fix: {file_path} - {message}")
    
    print(f"\nFixed {fixed_count} files")
    
    if failed_files:
        print(f"\n{len(failed_files)} files still have syntax errors")
        print("These require manual review:")
        for file_path, error in failed_files[:10]:
            print(f"  {file_path}: {error}")
    
    # Verify
    remaining = len(find_syntax_error_files())
    print(f"\nRemaining syntax errors: {remaining}")

if __name__ == '__main__':
    main()


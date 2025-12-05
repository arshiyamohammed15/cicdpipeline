#!/usr/bin/env python3
"""
Fix all remaining syntax/indentation errors systematically.
"""
from pathlib import Path
import re
import ast

def fix_file(file_path: Path) -> tuple[bool, str]:
    """Fix syntax/indentation errors in a file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix 1: PowerShell backticks
        content = content.replace('`n', '\n')
        content = content.replace('`t', '\t')
        
        # Fix 2: Common indentation patterns
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:
                new_lines.append('')
                continue
            
            # Fix common indentation issues
            # Pattern: Comment followed by incorrectly indented code
            if i > 0 and lines[i-1].strip().startswith('#'):
                prev_line = lines[i-1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                current_indent = len(line) - len(stripped)
                
                # If current line is indented more than comment but shouldn't be
                if current_indent > prev_indent + 4 and not stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with', 'elif', 'else')):
                    # Check if it's a continuation of comment block
                    if prev_indent > 0:
                        # Align to comment's indentation level
                        new_lines.append(' ' * prev_indent + stripped)
                        continue
            
            # Fix: Lines that are indented too much after comments
            if i > 0:
                prev_line = lines[i-1]
                if prev_line.strip().startswith('#') and not prev_line.strip().endswith(':'):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    current_indent = len(line) - len(stripped)
                    
                    # If indented way more than comment, likely wrong
                    if current_indent > prev_indent + 8:
                        # Try to align to comment level or comment + 4
                        if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with')):
                            new_lines.append(' ' * (prev_indent + 4) + stripped)
                            continue
                        elif not stripped.startswith('#'):
                            new_lines.append(' ' * prev_indent + stripped)
                            continue
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        # Fix 3: Empty blocks
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for empty control structures
            block_match = re.match(r'^(\s+)(if|for|while|try|except|with|elif|else)\s+.*:\s*$', line)
            if block_match:
                indent = block_match.group(1)
                indent_len = len(indent)
                
                # Find next non-empty line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                if j >= len(lines):
                    new_lines.append(line)
                    new_lines.append(indent + '    pass')
                    break
                elif j < len(lines):
                    next_line = lines[j]
                    if next_line.strip().startswith('#'):
                        new_lines.append(line)
                        i += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent <= indent_len:
                        new_lines.append(line)
                        new_lines.append(indent + '    pass')
                        i = j - 1
                        i += 1
                        continue
            
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        # Validate
        try:
            ast.parse(content)
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True, "Fixed"
            return False, "No errors"
        except SyntaxError as e:
            # Try to fix based on error location
            if hasattr(e, 'lineno') and e.lineno:
                error_line_idx = e.lineno - 1
                if error_line_idx < len(new_lines) and error_line_idx > 0:
                    error_line = new_lines[error_line_idx]
                    prev_line = new_lines[error_line_idx - 1]
                    
                    # Fix unexpected indent
                    if 'unexpected indent' in str(e):
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        # Align to previous line
                        if prev_line.strip().endswith(':'):
                            new_lines[error_line_idx] = ' ' * (prev_indent + 4) + error_line.lstrip()
                        else:
                            new_lines[error_line_idx] = ' ' * prev_indent + error_line.lstrip()
                        
                        content = '\n'.join(new_lines)
                        try:
                            ast.parse(content)
                            if content != original:
                                file_path.write_text(content, encoding='utf-8')
                                return True, "Fixed"
                        except:
                            pass
            
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"
        except IndentationError as e:
            return False, f"IndentationError: {str(e)}"
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def main():
    """Main entry point."""
    error_files = [
        'tests/test_constitution_comprehensive_runner.py',
        'tests/test_constitution_rule_semantics.py',
        'tests/test_contracts_schema_registry_api.py',
        'tests/test_deterministic_enforcement.py',
        'tests/test_enforcement_flow.py',
        'tests/test_ollama_ai_service.py',
        'tests/test_post_generation_validator.py',
        'tests/test_pre_implementation_artifacts.py',
    ]
    
    # Also get from file
    syntax_file = Path('syntax_error_files.txt')
    if syntax_file.exists():
        with open(syntax_file) as f:
            additional_files = [line.strip() for line in f if line.strip()]
            error_files.extend(additional_files)
    
    error_files = list(set(error_files))  # Remove duplicates
    
    print(f"Fixing {len(error_files)} files...")
    
    fixed_count = 0
    failed_files = []
    
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        fixed, message = fix_file(file_path)
        if fixed:
            fixed_count += 1
            print(f"  ✓ Fixed: {file_path_str}")
        else:
            if "No errors" not in message:
                failed_files.append((file_path_str, message))
                if len(failed_files) <= 5:
                    print(f"  ✗ Could not fix: {file_path_str} - {message}")
    
    print(f"\nFixed {fixed_count} files")
    
    if failed_files:
        print(f"\n{len(failed_files)} files still have errors")
    
    return fixed_count, len(failed_files)

if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Fix syntax errors in mmm_engine and product service test files.
"""
from pathlib import Path
import re
import ast
import py_compile

def fix_file_syntax(file_path: Path) -> tuple[bool, str]:
    """Fix syntax errors in a file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix 1: PowerShell backticks
        content = content.replace('`n', '\n')
        content = content.replace('`t', '\t')
        
        # Fix 2: Common syntax issues
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            
            # Fix: Comment followed by incorrectly indented code
            if i > 0 and lines[i-1].strip().startswith('#'):
                prev_line = lines[i-1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                current_indent = len(line) - len(stripped)
                
                # If indented way too much after comment, fix it
                if current_indent > prev_indent + 8 and not stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with', 'elif', 'else')):
                    if stripped.startswith('#'):
                        new_lines.append(' ' * prev_indent + stripped)
                        continue
                    elif not stripped.startswith(('import ', 'from ')):
                        new_lines.append(' ' * prev_indent + stripped)
                        continue
            
            # Fix: Lines with excessive indentation after comments
            if i > 0:
                prev_line = lines[i-1]
                if prev_line.strip().startswith('#') and not prev_line.strip().endswith(':'):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    current_indent = len(line) - len(stripped)
                    
                    if current_indent > prev_indent + 8:
                        if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try', 'except', 'with')):
                            new_lines.append(' ' * (prev_indent + 4) + stripped)
                            continue
                        elif not stripped.startswith('#') and not stripped.startswith(('import ', 'from ')):
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
            
            block_match = re.match(r'^(\s+)(if|for|while|try|except|with|elif|else)\s+.*:\s*$', line)
            if block_match:
                indent = block_match.group(1)
                indent_len = len(indent)
                
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
            # Try to fix based on error
            if hasattr(e, 'lineno') and e.lineno:
                error_line_idx = e.lineno - 1
                if error_line_idx < len(new_lines) and error_line_idx > 0:
                    error_line = new_lines[error_line_idx]
                    prev_line = new_lines[error_line_idx - 1]
                    
                    if 'unexpected indent' in str(e):
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
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
    # Get all mmm_engine and product service files with errors
    error_files = [
        'tests/cloud_services/product_services/mmm_engine/integration/test_real_clients.py',
        'tests/cloud_services/product_services/mmm_engine/performance/test_latency_slo.py',
        'tests/cloud_services/product_services/mmm_engine/resilience/test_degraded_modes.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_actor_preferences.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_circuit_breaker_thread_safety.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_decide_endpoint.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_delivery.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_dual_channel.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_experiments.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_fatigue_and_priority.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_metrics.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_outcomes.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_playbook_crud.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_tenant_policy.py',
        'tests/cloud_services/product_services/mmm_engine/unit/test_throughput.py',
    ]
    
    # Also get from syntax_error_files.txt
    syntax_file = Path('syntax_error_files.txt')
    if syntax_file.exists():
        with open(syntax_file) as f:
            additional = [line.strip() for line in f if line.strip() and ('mmm_engine' in line or 'product_services' in line or 'detection_engine' in line or 'signal_ingestion' in line or 'user_behaviour' in line)]
            error_files.extend(additional)
    
    error_files = list(set(error_files))  # Remove duplicates
    
    print(f"Fixing {len(error_files)} files...")
    
    fixed_count = 0
    failed_files = []
    
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        fixed, message = fix_file_syntax(file_path)
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


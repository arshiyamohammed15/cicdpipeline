#!/usr/bin/env python3
"""
Fix all syntax errors in test files systematically.
"""
from pathlib import Path
import re
import ast
import subprocess

def get_syntax_error_files():
    """Get all files with syntax errors."""
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '--co'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    error_files = {}
    current_file = None
    
    for line in result.stderr.split('\n'):
        if 'ERROR collecting tests/' in line:
            match = re.search(r'tests/[^\s]+', line)
            if match:
                current_file = match.group(0)
                error_files[current_file] = []
        elif current_file and 'SyntaxError' in line:
            error_files[current_file].append(line.strip())
    
    return error_files

def fix_file_syntax(file_path: Path) -> tuple[bool, str]:
    """Fix syntax errors in a file. Returns (fixed, error_message)."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix 1: PowerShell backtick newlines
        if '`n' in content:
            content = content.replace('`n', '\n')
        
        # Fix 2: Broken string literals - unclosed quotes
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            # Check for unclosed single quotes
            single_quotes = line.count("'") - line.count("\\'")
            if single_quotes % 2 != 0 and not line.strip().startswith('#'):
                # Try to fix by adding closing quote at end
                if not line.rstrip().endswith("'") and not line.rstrip().endswith("\\'"):
                    line = line.rstrip() + "'"
            
            # Check for unclosed double quotes
            double_quotes = line.count('"') - line.count('\\"')
            if double_quotes % 2 != 0 and not line.strip().startswith('#'):
                # Try to fix by adding closing quote at end
                if not line.rstrip().endswith('"') and not line.rstrip().endswith('\\"'):
                    line = line.rstrip() + '"'
            
            new_lines.append(line)
        content = '\n'.join(new_lines)
        
        # Fix 3: Empty if/for/while/try blocks
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for empty control structures
            if_match = re.match(r'^(\s+)(if|for|while|try|except|with)\s+.*:\s*$', line)
            if if_match:
                indent = if_match.group(1)
                # Check next non-empty line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                if j >= len(lines):
                    # End of file, add pass
                    new_lines.append(line)
                    new_lines.append(indent + '    pass')
                    i = j
                    continue
                elif j < len(lines):
                    next_line = lines[j]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    current_indent = len(indent)
                    
                    if next_indent <= current_indent and not next_line.strip().startswith('#'):
                        # Empty block, add pass
                        new_lines.append(line)
                        new_lines.append(indent + '    pass')
                        i = j - 1
                        i += 1
                        continue
            
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        # Fix 4: Missing closing parentheses/brackets/braces
        # Count parentheses
        open_parens = content.count('(') - content.count(')')
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')
        
        # Try to fix by adding closing characters at end of file
        # But be careful - only if it's clearly missing
        if open_parens > 0 and open_parens <= 3:
            # Might be missing closing parens, but don't auto-fix as it's risky
            pass
        
        # Fix 5: Broken backslash continuations
        content = re.sub(r'\\napp = create_app\(\)', '', content)
        content = re.sub(r'create_app\\napp', 'app', content)
        content = re.sub(r'\\napp', '', content)
        
        # Fix 6: Fix import statements with backticks
        content = re.sub(r'import\s+(\w+)`nimport', r'import \1\nimport', content)
        
        # Validate syntax
        try:
            ast.parse(content)
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True, "Fixed"
            return False, "No syntax errors"
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main entry point."""
    print("Collecting syntax error files...")
    error_files = get_syntax_error_files()
    print(f"Found {len(error_files)} files with syntax errors")
    
    fixed_count = 0
    failed_files = []
    
    for file_path_str in error_files.keys():
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        fixed, message = fix_file_syntax(file_path)
        if fixed:
            fixed_count += 1
            if fixed_count % 5 == 0:
                print(f"Fixed {fixed_count} files...")
        else:
            if "Syntax error" in message:
                failed_files.append((file_path_str, message))
    
    print(f"\nFixed {fixed_count} files total")
    
    if failed_files:
        print(f"\n{failed_files} files still have syntax errors:")
        for file_path, error in failed_files[:10]:
            print(f"  {file_path}: {error}")
    
    # Verify
    remaining = len(get_syntax_error_files())
    print(f"\nRemaining syntax errors: {remaining}")

if __name__ == '__main__':
    main()


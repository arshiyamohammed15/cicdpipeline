#!/usr/bin/env python3
"""
Direct fix for all syntax errors by parsing pytest output.
"""
from pathlib import Path
import re
import ast
import subprocess

def get_syntax_error_files_detailed():
    """Get files with syntax errors from pytest output."""
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '--co'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    error_files = {}
    current_file = None
    
    lines = result.stderr.split('\n')
    for i, line in enumerate(lines):
        # Find ERROR collecting line
        if 'ERROR collecting' in line and 'tests/' in line:
            match = re.search(r'tests/[^\s]+', line)
            if match:
                current_file = match.group(0)
                error_files[current_file] = {'errors': [], 'context': []}
        
        # Find SyntaxError lines
        if current_file and 'SyntaxError' in line:
            error_files[current_file]['errors'].append(line.strip())
            # Get context (previous and next lines)
            if i > 0:
                error_files[current_file]['context'].append(lines[i-1].strip())
            error_files[current_file]['context'].append(line.strip())
            if i < len(lines) - 1:
                error_files[current_file]['context'].append(lines[i+1].strip())
    
    return error_files

def fix_syntax_error_in_file(file_path: Path) -> tuple[bool, str]:
    """Fix syntax errors in a specific file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix 1: PowerShell backticks
        content = content.replace('`n', '\n')
        content = content.replace('`t', '\t')
        content = content.replace('`r', '\r')
        
        # Fix 2: Broken import statements
        content = re.sub(r'import\s+(\w+)`nimport', r'import \1\nimport', content)
        content = re.sub(r'import\s+(\w+)\s*`n\s*import', r'import \1\nimport', content)
        
        # Fix 3: Empty control structures
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for empty if/for/while/try blocks
            block_match = re.match(r'^(\s+)(if|for|while|try|except|with|elif|else)\s+.*:\s*$', line)
            if block_match:
                indent = block_match.group(1)
                indent_len = len(indent)
                
                # Find next non-empty line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                if j >= len(lines):
                    # End of file - add pass
                    new_lines.append(line)
                    new_lines.append(indent + '    pass')
                    break
                elif j < len(lines):
                    next_line = lines[j]
                    # Skip comments
                    if next_line.strip().startswith('#'):
                        new_lines.append(line)
                        i += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # If next line is at same or less indentation, block is empty
                    if next_indent <= indent_len:
                        new_lines.append(line)
                        new_lines.append(indent + '    pass')
                        i = j - 1
                        i += 1
                        continue
            
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        # Fix 4: Broken string literals - be very careful
        # Only fix obvious cases
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            # Check for unclosed single quotes (but not in comments)
            if not line.strip().startswith('#'):
                # Count unescaped quotes
                single_quotes = 0
                double_quotes = 0
                escaped = False
                
                for char in line:
                    if escaped:
                        escaped = False
                        continue
                    if char == '\\':
                        escaped = True
                        continue
                    if char == "'":
                        single_quotes += 1
                    elif char == '"':
                        double_quotes += 1
                
                # Only fix if clearly unclosed (odd count and doesn't end with quote)
                if single_quotes % 2 == 1 and not line.rstrip().endswith("'") and not line.rstrip().endswith("\\'"):
                    # Very risky - skip for now
                    pass
                if double_quotes % 2 == 1 and not line.rstrip().endswith('"') and not line.rstrip().endswith('\\"'):
                    # Very risky - skip for now
                    pass
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        # Fix 5: Remove broken backslash patterns
        content = re.sub(r'\\napp\s*=\s*create_app\(\)', '', content)
        content = re.sub(r'create_app\\napp', 'app', content)
        
        # Validate syntax
        try:
            ast.parse(content)
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                return True, "Fixed"
            return False, "No changes needed"
        except SyntaxError as e:
            # Try to get more info
            error_msg = f"Line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f" - {e.text.strip()}"
            return False, error_msg
    
    except Exception as e:
        return False, f"Exception: {str(e)}"

def main():
    """Main entry point."""
    print("Collecting syntax error files...")
    error_files = get_syntax_error_files_detailed()
    print(f"Found {len(error_files)} files with syntax errors")
    
    fixed_count = 0
    failed_files = []
    
    for file_path_str in error_files.keys():
        file_path = Path(file_path_str)
        if not file_path.exists():
            # Try alternative path
            file_path = Path('tests') / file_path_str.replace('tests/', '')
        
        if not file_path.exists():
            print(f"  File not found: {file_path_str}")
            continue
        
        fixed, message = fix_syntax_error_in_file(file_path)
        if fixed:
            fixed_count += 1
            print(f"  Fixed: {file_path_str}")
        else:
            if "No changes" not in message:
                failed_files.append((file_path_str, message))
    
    print(f"\nFixed {fixed_count} files")
    
    if failed_files:
        print(f"\n{len(failed_files)} files still have issues:")
        for file_path, error in failed_files[:10]:
            print(f"  {file_path}: {error}")
    
    # Verify
    remaining = len(get_syntax_error_files_detailed())
    print(f"\nRemaining syntax errors: {remaining}")

if __name__ == '__main__':
    main()


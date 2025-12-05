#!/usr/bin/env python3
"""
Fix all remaining 78 test errors systematically.
"""
from pathlib import Path
import re
import ast
import subprocess

def get_all_error_files():
    """Get all files with errors."""
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '--co'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    error_files = set()
    for line in result.stderr.split('\n'):
        if 'ERROR collecting tests/' in line:
            match = re.search(r'tests/[^\s]+', line)
            if match:
                error_files.add(match.group(0))
    
    return sorted(error_files)

def fix_file_syntax(file_path: Path) -> bool:
    """Fix syntax errors in a file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Try to parse
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError as e:
            lines = content.split('\n')
            error_line_idx = e.lineno - 1 if e.lineno else 0
            
            # Common fixes
            # Fix 1: Empty if/for/while blocks
            if error_line_idx < len(lines):
                line = lines[error_line_idx]
                if re.match(r'^\s+(if|for|while|try|except|with)\s+.*:\s*$', line):
                    # Check if next line is empty or dedented
                    next_idx = error_line_idx + 1
                    while next_idx < len(lines) and not lines[next_idx].strip():
                        next_idx += 1
                    if next_idx >= len(lines) or len(lines[next_idx]) - len(lines[next_idx].lstrip()) <= len(line) - len(line.lstrip()):
                        # Empty block, add pass
                        indent = len(line) - len(line.lstrip())
                        lines.insert(error_line_idx + 1, ' ' * (indent + 4) + 'pass')
                        content = '\n'.join(lines)
            
            # Fix 2: Broken string literals
            if "'" in content or '"' in content:
                # Try to fix unclosed strings (basic heuristic)
                pass  # Too risky to auto-fix
            
            # Fix 3: Remove broken backslash patterns
            content = re.sub(r'\\napp = create_app\(\)', '', content)
            content = re.sub(r'create_app\\napp', 'app', content)
            
            # Try parsing again
            try:
                ast.parse(content)
                file_path.write_text(content, encoding='utf-8')
                return True
            except SyntaxError:
                pass
        
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def fix_file_imports(file_path: Path) -> bool:
    """Fix import errors."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix relative imports
        parts = file_path.parts
        module_map = None
        
        if 'budgeting_rate_limiting_cost_observability' in parts:
            module_map = 'budgeting_rate_limiting_cost_observability'
        elif 'health_reliability_monitoring' in parts:
            module_map = 'health_reliability_monitoring'
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
            patterns = [
                (r'from\s+\.\.database\s+import', f'from {module_map}.database import'),
                (r'from\s+\.\.services\s+import', f'from {module_map}.services import'),
                (r'from\s+\.\.models\s+import', f'from {module_map}.models import'),
                (r'from\s+\.\.routes\s+import', f'from {module_map}.routes import'),
                (r'from\s+\.\.main\s+import', f'from {module_map}.main import'),
                (r'from\s+\.database\s+import', f'from {module_map}.database import'),
                (r'from\s+\.services\s+import', f'from {module_map}.services import'),
                (r'from\s+\.models\s+import', f'from {module_map}.models import'),
            ]
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
        
        # Fix budgeting database imports
        content = re.sub(
            r'tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database',
            'budgeting_rate_limiting_cost_observability.database',
            content
        )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    print("Getting error files...")
    error_files = get_all_error_files()
    print(f"Found {len(error_files)} files with errors")
    
    fixed = 0
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        if fix_file_syntax(file_path):
            fixed += 1
        if fix_file_imports(file_path):
            fixed += 1
        
        if fixed % 10 == 0:
            print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")
    
    # Verify
    remaining = len(get_all_error_files())
    print(f"Remaining errors: {remaining}")

if __name__ == '__main__':
    main()


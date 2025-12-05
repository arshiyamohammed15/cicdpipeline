#!/usr/bin/env python3
"""
Comprehensive fix for all 67 remaining test errors.
Categorizes and fixes each error type systematically.
"""
from pathlib import Path
import re
import subprocess

def get_error_files():
    """Get all files with errors from pytest collection."""
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '--co'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    errors = {}
    current_file = None
    
    for line in result.stderr.split('\n'):
        if 'ERROR collecting' in line and 'tests/' in line:
            # Extract file path
            match = re.search(r'tests/[^\s]+', line)
            if match:
                current_file = match.group(0)
                errors[current_file] = []
        elif current_file and ('SyntaxError' in line or 'ImportError' in line or 
                              'ModuleNotFoundError' in line or 'IndentationError' in line or
                              'FileNotFoundError' in line):
            errors[current_file].append(line.strip())
    
    return errors

def fix_syntax_errors(file_path: Path) -> bool:
    """Fix syntax errors in a file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix common syntax error patterns
        # Remove broken backslash continuations
        content = re.sub(r'\\napp = create_app\(\)', '', content)
        content = re.sub(r'create_app\\napp = create_app', 'app', content)
        
        # Fix broken string literals
        content = re.sub(r"'\)\s*$", "')", content, flags=re.MULTILINE)
        
        # Fix broken imports
        content = re.sub(r'from\s+health_reliability_monitoring\.main import create_app\s+app = create_app\(\)',
                        'from health_reliability_monitoring.main import app', content)
        
        # Remove empty if blocks that cause syntax errors
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for empty if/for/while blocks
            if re.match(r'^\s+(if|for|while|try|except|with)\s+.*:\s*$', line):
                # Check if next non-empty line is at same or less indentation
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not next_line.strip().startswith('#'):
                        indent_level = len(line) - len(line.lstrip())
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent_level:
                            # Empty block, add pass
                            new_lines.append(line)
                            new_lines.append(' ' * (indent_level + 4) + 'pass')
                            i = j - 1
                            i += 1
                            continue
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing syntax in {file_path}: {e}")
        return False

def fix_relative_imports(file_path: Path) -> bool:
    """Convert relative imports to absolute imports."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Determine module from path
        parts = file_path.parts
        module_map = None
        
        # Map test path to Python package
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
        
        if module_map:
            # Convert relative imports
            content = re.sub(
                r'from\s+\.\.database\s+import',
                f'from {module_map}.database import',
                content
            )
            content = re.sub(
                r'from\s+\.\.services\s+import',
                f'from {module_map}.services import',
                content
            )
            content = re.sub(
                r'from\s+\.\.dependencies\s+import',
                f'from {module_map}.dependencies import',
                content
            )
            content = re.sub(
                r'from\s+\.\.models\s+import',
                f'from {module_map}.models import',
                content
            )
            content = re.sub(
                r'from\s+\.\.routes\s+import',
                f'from {module_map}.routes import',
                content
            )
            content = re.sub(
                r'from\s+\.\.main\s+import',
                f'from {module_map}.main import',
                content
            )
            content = re.sub(
                r'from\s+\.\.config\s+import',
                f'from {module_map}.config import',
                content
            )
            content = re.sub(
                r'from\s+\.database\s+import',
                f'from {module_map}.database import',
                content
            )
            content = re.sub(
                r'from\s+\.services\s+import',
                f'from {module_map}.services import',
                content
            )
            content = re.sub(
                r'from\s+\.models\s+import',
                f'from {module_map}.models import',
                content
            )
        
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
        
        # Fix incorrect import paths
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

def fix_indentation_errors(file_path: Path) -> bool:
    """Fix indentation errors."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for if statement with no body
            if_match = re.match(r'^(\s+)if\s+.*:\s*$', line)
            if if_match:
                indent = if_match.group(1)
                # Check next non-empty line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                if j >= len(lines) or len(lines[j]) - len(lines[j].lstrip()) <= len(indent):
                    # Empty block, add pass
                    new_lines.append(line)
                    new_lines.append(indent + '    pass')
                    i = j - 1
                    i += 1
                    continue
            
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing indentation in {file_path}: {e}")
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
        content = re.sub(
            r'import\s+key-management-service',
            'import key_management_service',
            content
        )
        
        # Fix incorrect paths
        content = re.sub(
            r'tests/cloud_services/src/cloud_services',
            'src/cloud_services',
            content
        )
        content = re.sub(
            r'tests.*src.*cloud_services.*product-services.*signal-ingestion-normalization.*models\.py',
            '',
            content
        )
        content = re.sub(
            r'tests.*src.*cloud_services.*shared-services.*ollama-ai-agent.*models\.py',
            '',
            content
        )
        
        # Fix health_reliability_monitoring router import
        content = re.sub(
            r'from\s+health_reliability_monitoring\.routes\s+import\s+router',
            'from health_reliability_monitoring.routes import router',
            content
        )
        
        # Fix aiosqlite import (should be installed or mocked)
        if 'aiosqlite' in content and 'import aiosqlite' in content:
            # Check if it's actually needed or can be mocked
            pass  # Will be handled by dependency installation
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing other issues in {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    print("Collecting error information...")
    errors = get_error_files()
    
    print(f"\nFound {len(errors)} files with errors")
    
    tests_dir = Path('tests')
    fixed = 0
    
    # Fix all files
    for file_path_str, error_list in errors.items():
        file_path = Path(file_path_str)
        if not file_path.exists():
            # Try to find the actual file
            file_path = tests_dir / file_path_str.replace('tests/', '')
        
        if not file_path.exists():
            continue
        
        file_fixed = False
        
        # Apply all fixes
        if fix_syntax_errors(file_path):
            file_fixed = True
        if fix_relative_imports(file_path):
            file_fixed = True
        if fix_budgeting_database_imports(file_path):
            file_fixed = True
        if fix_indentation_errors(file_path):
            file_fixed = True
        if fix_other_errors(file_path):
            file_fixed = True
        
        if file_fixed:
            fixed += 1
            if fixed % 10 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")
    
    # Verify
    print("\nVerifying fixes...")
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '--co', '-q'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    error_count = len([l for l in result.stderr.split('\n') if 'ERROR collecting' in l])
    print(f"Remaining errors: {error_count}")

if __name__ == '__main__':
    main()

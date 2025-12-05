#!/usr/bin/env python3
"""
Final comprehensive fix for all remaining test errors.
"""
from pathlib import Path
import re

def fix_file(file_path: Path) -> bool:
    """Fix all issues in a test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix syntax errors from cleanup
        # Remove broken create_app patterns
        content = re.sub(r'from health_reliability_monitoring\.main import create_app\\napp = create_app\(\)', 
                        'from health_reliability_monitoring.main import app', content)
        content = re.sub(r'create_app\\napp = create_app\(\)', 'app', content)
        content = re.sub(r'\\napp = create_app\(\)', '', content)
        
        # Fix budgeting database imports
        content = re.sub(
            r'tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database',
            'budgeting_rate_limiting_cost_observability.database',
            content
        )
        
        # Fix relative imports - convert to absolute
        if 'from .. import' in content or 'from . import' in content:
            # Determine module from path
            parts = file_path.parts
            module_mappings = {
                'budgeting_rate_limiting_cost_observability': 'budgeting_rate_limiting_cost_observability',
                'health_reliability_monitoring': 'health_reliability_monitoring',
                'evidence_receipt_indexing_service': 'evidence_receipt_indexing_service',
            }
            
            for test_name, python_pkg in module_mappings.items():
                if test_name in parts:
                    content = re.sub(
                        r'from \.\.database import',
                        f'from {python_pkg}.database import',
                        content
                    )
                    content = re.sub(
                        r'from \.\.services import',
                        f'from {python_pkg}.services import',
                        content
                    )
                    content = re.sub(
                        r'from \.\.dependencies import',
                        f'from {python_pkg}.dependencies import',
                        content
                    )
                    content = re.sub(
                        r'from \.\.models import',
                        f'from {python_pkg}.models import',
                        content
                    )
                    break
        
        # Fix signal ingestion normalization paths
        if 'signal_ingestion_normalization' in str(file_path):
            content = re.sub(
                r'tests.*src.*cloud_services.*product.*services.*signal-ingestion-normalization',
                'src/cloud_services/product-services/signal-ingestion-normalization',
                content
            )
            content = re.sub(
                r'tests.*cloud_services.*product_services.*models\.py',
                '',
                content
            )
        
        # Fix ollama-ai-agent paths
        if 'ollama_ai_agent' in str(file_path):
            content = re.sub(
                r'tests.*src.*cloud_services.*shared-services.*ollama-ai-agent',
                'src/cloud_services/shared-services/ollama-ai-agent',
                content
            )
        
        # Fix key-management-service imports
        content = re.sub(
            r'from key-management-service',
            'from key_management_service',
            content
        )
        content = re.sub(
            r'import key-management-service',
            'import key_management_service',
            content
        )
        
        # Fix indentation errors - remove empty if blocks
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for empty if block
            if re.match(r'^\s+if\s+.*:\s*$', line):
                # Check if next line is empty or comment
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if not next_line.strip() or next_line.strip().startswith('):
                        # Skip the if statement
                        i += 1
                        continue
            new_lines.append(line)
            i += 1
        content = '\n'.join(new_lines)
        
        # Clean up multiple blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    tests_dir = Path('tests_dir = Path('tests')
    fixed = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if fix_file(test_file):
            fixed += 1
            if fixed % 20 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()


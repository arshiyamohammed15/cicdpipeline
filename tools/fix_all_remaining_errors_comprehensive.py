#!/usr/bin/env python3
"""
Comprehensive fix for all remaining test errors.
"""
from pathlib import Path
import re

def fix_file(file_path: Path) -> bool:
    """Fix all issues in a test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix path issues: shared_services -> shared-services (but only in paths, not imports)
        # Only fix in path strings, not import statements
        content = re.sub(
            r'(["\'/])shared_services(["\']|/)',
            r'\1shared-services\2',
            content
        )
        content = re.sub(
            r'(["\'/])client_services(["\']|/)',
            r'\1client-services\2',
            content
        )
        content = re.sub(
            r'(["\'/])product_services(["\']|/)',
            r'\1product-services\2',
            content
        )
        
        # Fix detection_engine_core imports
        if 'detection_engine_core' in str(file_path):
            content = re.sub(
                r'from integration_adapters\.models import',
                'from detection_engine_core.models import',
                content
            )
            content = re.sub(
                r'sys\.path\.insert\(0.*?\)',
                '# Module setup handled by root conftest.py',
                content,
                flags=re.DOTALL
            )
        
        # Fix health_reliability_monitoring app import
        if 'health_reliability_monitoring' in str(file_path):
            content = re.sub(
                r'from health_reliability_monitoring\.main import app',
                'from health_reliability_monitoring.main import create_app\napp = create_app()',
                content
            )
        
        # Fix budgeting database imports
        content = re.sub(
            r'tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database',
            'budgeting_rate_limiting_cost_observability.database',
            content
        )
        
        # Fix signal ingestion normalization PACKAGE_ROOT
        if 'signal_ingestion_normalization' in str(file_path):
            # Remove PACKAGE_ROOT calculation and use direct imports
            content = re.sub(
                r'PACKAGE_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[4\] / "src" / "cloud_services" / "product_services" / "signal-ingestion-normalization".*?spec_models\.loader\.exec_module\(models_module\)',
                '# Module setup handled by root conftest.py\nfrom signal_ingestion_normalization import models as models_module',
                content,
                flags=re.DOTALL
            )
        
        # Fix root test files - cloud-services -> cloud_services
        if file_path.parent.name == 'tests' and file_path.name.startswith('test_'):
            content = re.sub(
                r'src[\\/]cloud-services',
                'src/cloud_services',
                content
            )
        
        # Fix relative imports that should be absolute
        if 'from .. import' in content or 'from . import' in content:
            # Determine module from path
            parts = file_path.parts
            if 'shared_services' in parts or 'shared-services' in parts:
                idx = parts.index('shared_services') if 'shared_services' in parts else parts.index('shared-services')
                if idx + 1 < len(parts):
                    module_test_name = parts[idx + 1].replace('_', '-')
                    # Map to Python package name
                    module_mappings = {
                        'budgeting-rate-limiting-cost-observability': 'budgeting_rate_limiting_cost_observability',
                        'health-reliability-monitoring': 'health_reliability_monitoring',
                        'evidence-receipt-indexing-service': 'evidence_receipt_indexing_service',
                    }
                    python_pkg = module_mappings.get(module_test_name, module_test_name.replace('-', '_'))
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
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    tests_dir = Path('tests')
    fixed = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if fix_file(test_file):
            fixed += 1
            if fixed % 20 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Comprehensive fix for ALL test import issues - addresses root cause.

Root Cause: Hyphenated directory names cannot be imported as Python packages.
Solution: Standardize all imports to use Python package names, not directory names.
"""
from pathlib import Path
import re

# Mapping: hyphenated directory -> Python package name
MODULE_MAPPINGS = {
    "identity-access-management": "identity_access_management",
    "key-management-service": "key_management_service",
    "alerting-notification-service": "alerting_notification_service",
    "budgeting-rate-limiting-cost-observability": "budgeting_rate_limiting_cost_observability",
    "configuration-policy-management": "configuration_policy_management",
    "contracts-schema-registry": "contracts_schema_registry",
    "data-governance-privacy": "data_governance_privacy",
    "deployment-infrastructure": "deployment_infrastructure",
    "evidence-receipt-indexing-service": "evidence_receipt_indexing_service",
    "health-reliability-monitoring": "health_reliability_monitoring",
    "ollama-ai-agent": "ollama_ai_agent",
    "integration-adapters": "integration_adapters",
    "detection-engine-core": "detection_engine_core",
    "signal-ingestion-normalization": "signal_ingestion_normalization",
    "user-behaviour-intelligence": "user_behaviour_intelligence",
}

def fix_imports_in_file(file_path: Path) -> bool:
    """Fix all imports in a test file to use Python package names."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix hyphenated module imports
        for hyphenated, python_name in MODULE_MAPPINGS.items():
            # Fix imports like "from identity-access-management.main import"
            content = re.sub(
                rf'from {re.escape(hyphenated)}\.',
                f'from {python_name}.',
                content
            )
            # Fix imports like "from key-management-service.main import app app"
            content = re.sub(
                rf'from {re.escape(hyphenated)}\.main import app app',
                f'from {python_name}.main import app',
                content
            )
        
        # Fix relative imports that should be absolute
        # "from ..database import" -> "from {module}.database import"
        if 'cloud_services' in str(file_path):
            # Extract module name from path
            parts = file_path.parts
            if 'shared_services' in parts:
                idx = parts.index('shared_services')
                if idx + 1 < len(parts):
                    module_test_name = parts[idx + 1]
                    # Find corresponding Python package name
                    for hyp, py_name in MODULE_MAPPINGS.items():
                        if module_test_name.replace('_', '-') == hyp or module_test_name == py_name:
                            content = re.sub(
                                r'from \.\.database import',
                                f'from {py_name}.database import',
                                content
                            )
                            content = re.sub(
                                r'from \.\.services import',
                                f'from {py_name}.services import',
                                content
                            )
                            content = re.sub(
                                r'from \.\.dependencies import',
                                f'from {py_name}.dependencies import',
                                content
                            )
                            content = re.sub(
                                r'from \.\.models import',
                                f'from {py_name}.models import',
                                content
                            )
                            break
        
        # Fix "from main import" -> "from {module}.main import"
        if 'detection_engine_core' in str(file_path):
            content = re.sub(r'^from main import', 'from detection_engine_core.main import', content, flags=re.MULTILINE)
            content = re.sub(r'^from routes import', 'from detection_engine_core.routes import', content, flags=re.MULTILINE)
            content = re.sub(r'^from services import', 'from detection_engine_core.services import', content, flags=re.MULTILINE)
            content = re.sub(r'^from models import', 'from detection_engine_core.models import', content, flags=re.MULTILINE)
        
        # Fix integration_adapters imports that reference wrong modules
        if 'detection_engine_core' in str(file_path):
            content = re.sub(
                r'from integration_adapters\.models import',
                'from detection_engine_core.models import',
                content
            )
        
        # Fix root test files - use Python package names
        if file_path.parent.name == 'tests' and file_path.name.startswith('test_'):
            # Fix paths in root test files
            content = re.sub(
                r'src[\\/]cloud-services',
                'src/cloud_services',
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
        if fix_imports_in_file(test_file):
            fixed += 1
            if fixed % 20 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()


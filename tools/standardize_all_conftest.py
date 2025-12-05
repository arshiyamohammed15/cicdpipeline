#!/usr/bin/env python3
"""
Standardize all conftest.py files to use root conftest.py setup.

Root Cause Fix: All module-specific conftest files should rely on root conftest.py
for package setup, not duplicate the logic.
"""
from pathlib import Path
import re

CONFTEST_TEMPLATE = '''"""
Test fixtures for {module_display_name}.

Uses standardized module setup from root conftest.py
"""
import pytest
from pathlib import Path
import sys

# Root conftest should have set up {python_pkg_name} package
# But ensure module path is in sys.path
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "{category_path}" / "{module_dir_name}"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# Import will work because root conftest.py sets up the package structure
# Tests can use: from {python_pkg_name}.main import app
'''

MODULE_MAPPINGS = {
    "identity-access-management": ("identity_access_management", "shared-services", "Identity Access Management"),
    "key-management-service": ("key_management_service", "shared-services", "Key Management Service"),
    "alerting-notification-service": ("alerting_notification_service", "shared-services", "Alerting Notification Service"),
    "budgeting-rate-limiting-cost-observability": ("budgeting_rate_limiting_cost_observability", "shared-services", "Budgeting Rate Limiting Cost Observability"),
    "configuration-policy-management": ("configuration_policy_management", "shared-services", "Configuration Policy Management"),
    "contracts-schema-registry": ("contracts_schema_registry", "shared-services", "Contracts Schema Registry"),
    "data-governance-privacy": ("data_governance_privacy", "shared-services", "Data Governance Privacy"),
    "deployment-infrastructure": ("deployment_infrastructure", "shared-services", "Deployment Infrastructure"),
    "evidence-receipt-indexing-service": ("evidence_receipt_indexing_service", "shared-services", "Evidence Receipt Indexing Service"),
    "health-reliability-monitoring": ("health_reliability_monitoring", "shared-services", "Health Reliability Monitoring"),
    "ollama-ai-agent": ("ollama_ai_agent", "shared-services", "Ollama AI Agent"),
    "integration-adapters": ("integration_adapters", "client-services", "Integration Adapters"),
    "detection-engine-core": ("detection_engine_core", "product-services", "Detection Engine Core"),
    "signal-ingestion-normalization": ("signal_ingestion_normalization", "product-services", "Signal Ingestion Normalization"),
    "user-behaviour-intelligence": ("user_behaviour_intelligence", "product-services", "User Behaviour Intelligence"),
    "mmm_engine": ("mmm_engine", "product-services", "MMM Engine"),
}

def standardize_conftest(conftest_path: Path):
    """Standardize a conftest.py file."""
    # Determine module from path
    parts = conftest_path.parts
    if 'shared_services' in parts:
        idx = parts.index('shared_services')
        category = "shared-services"
    elif 'client_services' in parts:
        idx = parts.index('client_services')
        category = "client-services"
    elif 'product_services' in parts:
        idx = parts.index('product_services')
        category = "product-services"
    else:
        return False
    
    if idx + 1 < len(parts):
        module_test_name = parts[idx + 1]
        # Find matching module
        for module_dir, (python_pkg, cat, display) in MODULE_MAPPINGS.items():
            if module_test_name.replace('_', '-') == module_dir or module_test_name == python_pkg:
                if cat == category:
                    content = CONFTEST_TEMPLATE.format(
                        module_display_name=display,
                        python_pkg_name=python_pkg,
                        category_path=category.replace("-", "_"),
                        module_dir_name=module_dir
                    )
                    conftest_path.write_text(content, encoding='utf-8')
                    return True
    return False

def main():
    """Main entry point."""
    tests_dir = Path('tests')
    fixed = 0
    
    for conftest_file in tests_dir.rglob('conftest.py'):
        if conftest_file.name == 'conftest.py' and conftest_file.parent.name != 'tests':
            if standardize_conftest(conftest_file):
                fixed += 1
                print(f"Standardized: {conftest_file}")
    
    print(f"\nStandardized {fixed} conftest files")

if __name__ == '__main__':
    main()


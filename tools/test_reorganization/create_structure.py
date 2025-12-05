#!/usr/bin/env python3
"""
Create standardized test directory structure for ZeroUI 2.0.

Creates the complete test organization structure following the reorganization strategy.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Module mappings: hyphenated names -> underscore names
MODULE_MAPPINGS = {
    # Client Services
    "integration-adapters": "integration_adapters",
    "compliance-security-challenges": "compliance_security_challenges",
    "cross-cutting-concerns": "cross_cutting_concerns",
    "feature-development-blind-spots": "feature_development_blind_spots",
    "knowledge-silo-prevention": "knowledge_silo_prevention",
    "legacy-systems-safety": "legacy_systems_safety",
    "merge-conflicts-delays": "merge_conflicts_delays",
    "monitoring-observability-gaps": "monitoring_observability_gaps",
    "release-failures-rollbacks": "release_failures_rollbacks",
    "technical-debt-accumulation": "technical_debt_accumulation",
    
    # Product Services
    "detection-engine-core": "detection_engine_core",
    "knowledge-integrity-discovery": "knowledge_integrity_discovery",
    "mmm_engine": "mmm_engine",
    "signal-ingestion-normalization": "signal_ingestion_normalization",
    "user_behaviour_intelligence": "user_behaviour_intelligence",
    
    # Shared Services
    "alerting-notification-service": "alerting_notification_service",
    "budgeting-rate-limiting-cost-observability": "budgeting_rate_limiting_cost_observability",
    "configuration-policy-management": "configuration_policy_management",
    "contracts-schema-registry": "contracts_schema_registry",
    "data-governance-privacy": "data_governance_privacy",
    "deployment-infrastructure": "deployment_infrastructure",
    "evidence-receipt-indexing-service": "evidence_receipt_indexing_service",
    "health-reliability-monitoring": "health_reliability_monitoring",
    "identity-access-management": "identity_access_management",
    "key-management-service": "key_management_service",
    "ollama-ai-agent": "ollama_ai_agent",
}

# Test categories for each module
TEST_CATEGORIES = [
    "unit",
    "integration",
    "security",
    "performance",
    "resilience",  # Optional, not all modules need this
]

# Client Services modules
CLIENT_SERVICES_MODULES = [
    "integration_adapters",
    "compliance_security_challenges",
    "cross_cutting_concerns",
    "feature_development_blind_spots",
    "knowledge_silo_prevention",
    "legacy_systems_safety",
    "merge_conflicts_delays",
    "monitoring_observability_gaps",
    "release_failures_rollbacks",
    "technical_debt_accumulation",
]

# Product Services modules
PRODUCT_SERVICES_MODULES = [
    "detection_engine_core",
    "knowledge_integrity_discovery",
    "mmm_engine",
    "signal_ingestion_normalization",
    "user_behaviour_intelligence",
]

# Shared Services modules
SHARED_SERVICES_MODULES = [
    "alerting_notification_service",
    "budgeting_rate_limiting_cost_observability",
    "configuration_policy_management",
    "contracts_schema_registry",
    "data_governance_privacy",
    "deployment_infrastructure",
    "evidence_receipt_indexing_service",
    "health_reliability_monitoring",
    "identity_access_management",
    "key_management_service",
    "ollama_ai_agent",
]


def create_directory_structure():
    """Create the complete test directory structure."""
    tests_root = PROJECT_ROOT / "tests"
    
    # Create root structure
    (tests_root / "cloud_services").mkdir(parents=True, exist_ok=True)
    (tests_root / "cloud_services" / "__init__.py").touch()
    (tests_root / "cloud_services" / "conftest.py").touch()
    
    # Create category directories
    for category in ["client_services", "product_services", "shared_services"]:
        category_dir = tests_root / "cloud_services" / category
        category_dir.mkdir(parents=True, exist_ok=True)
        (category_dir / "__init__.py").touch()
    
    # Create module directories
    modules_to_create = {
        "client_services": CLIENT_SERVICES_MODULES,
        "product_services": PRODUCT_SERVICES_MODULES,
        "shared_services": SHARED_SERVICES_MODULES,
    }
    
    for category, modules in modules_to_create.items():
        for module_name in modules:
            module_dir = tests_root / "cloud_services" / category / module_name
            module_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py
            (module_dir / "__init__.py").touch()
            
            # Create conftest.py template
            conftest_content = f'''"""
Test fixtures for {module_name.replace('_', ' ').title()}.

Module-specific fixtures and test utilities.
"""
import pytest
from pathlib import Path
import sys

# Add module to path for imports
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "{category.replace('_', '-')}" / "{module_name.replace('_', '-')}"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

'''
            (module_dir / "conftest.py").write_text(conftest_content)
            
            # Create test category directories
            for test_category in TEST_CATEGORIES:
                category_test_dir = module_dir / test_category
                category_test_dir.mkdir(parents=True, exist_ok=True)
                (category_test_dir / "__init__.py").touch()
            
            # Create README.md template
            readme_content = f'''# {module_name.replace('_', ' ').title()} Tests

## Test Organization

This directory contains all tests for the {module_name.replace('_', ' ').title()} module.

### Structure

- `unit/` - Unit tests for services, repositories, models
- `integration/` - Integration tests for API endpoints and workflows
- `security/` - Security tests (authentication, authorization, tenant isolation)
- `performance/` - Performance tests (latency, throughput)
- `resilience/` - Resilience tests (circuit breakers, degradation modes)

### Running Tests

```bash
# Run all tests for this module
pytest tests/cloud_services/{category}/{module_name}/

# Run specific test category
pytest tests/cloud_services/{category}/{module_name}/unit/
pytest tests/cloud_services/{category}/{module_name}/security/

# Run with markers
pytest -m unit tests/cloud_services/{category}/{module_name}/
pytest -m security tests/cloud_services/{category}/{module_name}/
```

### Test Framework

Tests can also be run using the test registry framework:

```bash
python tools/test_registry/test_runner.py --module {module_name.replace('_', '-')}
```
'''
            (module_dir / "README.md").write_text(readme_content)
    
    print(f"Created test directory structure in {tests_root}")
    print(f"Created {len(CLIENT_SERVICES_MODULES)} client service module directories")
    print(f"Created {len(PRODUCT_SERVICES_MODULES)} product service module directories")
    print(f"Created {len(SHARED_SERVICES_MODULES)} shared service module directories")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create standardized test directory structure")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating it",
    )
    args = parser.parse_args()
    
    if args.dry_run:
        print("Dry run mode - would create:")
        print(f"  - tests/cloud_services/")
        print(f"  - {len(CLIENT_SERVICES_MODULES)} client service modules")
        print(f"  - {len(PRODUCT_SERVICES_MODULES)} product service modules")
        print(f"  - {len(SHARED_SERVICES_MODULES)} shared service modules")
    else:
        create_directory_structure()
        print("Test directory structure created successfully")


if __name__ == "__main__":
    main()


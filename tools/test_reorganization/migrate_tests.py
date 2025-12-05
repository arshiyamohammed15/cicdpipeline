#!/usr/bin/env python3
"""
Migrate existing tests to new standardized structure.

Moves tests from scattered locations to centralized test directory structure.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Module name mappings (hyphenated -> underscored)
MODULE_MAPPINGS = {
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
    "detection-engine-core": "detection_engine_core",
    "knowledge-integrity-discovery": "knowledge_integrity_discovery",
    "mmm_engine": "mmm_engine",
    "signal-ingestion-normalization": "signal_ingestion_normalization",
    "user_behaviour_intelligence": "user_behaviour_intelligence",
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

# Category mappings
CATEGORY_MAPPINGS = {
    "client-services": "client_services",
    "product_services": "product_services",
    "shared-services": "shared_services",
}


def normalize_module_name(name: str) -> str:
    """Normalize module name (hyphenated -> underscored)."""
    return MODULE_MAPPINGS.get(name, name.replace("-", "_"))


def determine_test_category(test_file: Path) -> str:
    """Determine test category from file path or name."""
    path_str = str(test_file).lower()
    file_name = test_file.name.lower()
    
    # Check for specific test category directories in path (more specific first)
    # Check parent directory name first (most reliable)
    parent_dir = test_file.parent.name.lower()
    if parent_dir in ["unit", "integration", "security", "performance", "resilience"]:
        return parent_dir
    
    # Then check file name patterns
    if "test_security" in file_name or "security" in file_name:
        return "security"
    elif "test_performance" in file_name or "performance" in file_name:
        return "performance"
    elif "test_resilience" in file_name or "resilience" in file_name:
        return "resilience"
    elif "test_integration" in file_name:
        return "integration"
    elif "test_unit" in file_name:
        return "unit"
    
    # Then check path (checking for directory names, not substrings)
    path_parts = [p.lower() for p in test_file.parts]
    if "unit" in path_parts:
        return "unit"
    elif "integration" in path_parts:
        return "integration"
    elif "security" in path_parts:
        return "security"
    elif "performance" in path_parts:
        return "performance"
    elif "resilience" in path_parts:
        return "resilience"
    
    # Default to unit if unclear
    return "unit"


def find_module_from_path(test_file: Path) -> Tuple[str, str]:
    """Find module and category from test file path."""
    parts = test_file.parts
    
    # Check if in src/cloud_services structure
    if "cloud_services" in parts or "cloud-services" in parts:
        try:
            idx = parts.index("cloud_services") if "cloud_services" in parts else parts.index("cloud-services")
            if idx + 1 < len(parts):
                category = parts[idx + 1]
                category = CATEGORY_MAPPINGS.get(category, category.replace("-", "_"))
                if idx + 2 < len(parts):
                    module = parts[idx + 2]
                    module = normalize_module_name(module)
                    return category, module
        except (ValueError, IndexError):
            pass
    
    # Check if in tests/ structure with module name
    if "tests" in parts:
        try:
            idx = parts.index("tests")
            # Check for known module patterns
            for part in parts[idx + 1:]:
                if part in MODULE_MAPPINGS.values() or part.replace("-", "_") in MODULE_MAPPINGS.values():
                    # Try to determine category
                    if "sin" in part or "mmm" in part or "detection" in part or "user_behaviour" in part:
                        return "product_services", normalize_module_name(part)
                    elif "iam" in part or "kms" in part or "alerting" in part or "data_governance" in part:
                        return "shared_services", normalize_module_name(part)
                    else:
                        return "client_services", normalize_module_name(part)
        except (ValueError, IndexError):
            pass
    
    return None, None


def migrate_test_file(test_file: Path, dry_run: bool = False) -> bool:
    """Migrate a single test file to new structure."""
    category, module = find_module_from_path(test_file)
    
    if not category or not module:
        print(f"Warning: Could not determine module for {test_file}")
        return False
    
    test_category = determine_test_category(test_file)
    target_dir = (
        PROJECT_ROOT
        / "tests"
        / "cloud_services"
        / category
        / module
        / test_category
    )
    
    if not target_dir.exists():
        print(f"Warning: Target directory does not exist: {target_dir}")
        return False
    
    target_file = target_dir / test_file.name
    
    if target_file.exists():
        print(f"Warning: Target file already exists: {target_file}")
        return False
    
    if dry_run:
        print(f"Would move: {test_file} -> {target_file}")
        return True
    
    try:
        # Copy file
        shutil.copy2(test_file, target_file)
        print(f"Moved: {test_file.name} -> {target_file}")
        return True
    except Exception as e:
        print(f"Error moving {test_file}: {e}")
        return False


def migrate_tests_from_manifest(dry_run: bool = False):
    """Migrate tests using test manifest."""
    manifest_path = PROJECT_ROOT / "artifacts" / "test_manifest.json"
    
    if not manifest_path.exists():
        print(f"Error: Manifest not found: {manifest_path}")
        print("Run: python tools/test_registry/generate_manifest.py")
        return
    
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for test_file_info in manifest["test_files"]:
        test_path = PROJECT_ROOT / test_file_info["path"]
        
        if not test_path.exists():
            skipped += 1
            continue
        
        # Skip if already in new structure
        if "tests/cloud_services" in str(test_path):
            skipped += 1
            continue
        
        if migrate_test_file(test_path, dry_run):
            migrated += 1
        else:
            errors += 1
    
    print(f"\nMigration Summary:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate tests to new structure")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without migrating",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Migrate specific file",
    )
    args = parser.parse_args()
    
    if args.file:
        migrate_test_file(args.file, args.dry_run)
    else:
        migrate_tests_from_manifest(args.dry_run)


if __name__ == "__main__":
    main()


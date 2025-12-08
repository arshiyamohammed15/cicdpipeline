"""
Root-level pytest configuration.

Provides standardized module path resolution for all tests.
Handles hyphenated directory names by creating proper Python package structures.
"""
import sys
import importlib.util
import os
import types
from pathlib import Path

# Project root - conftest.py is in tests/, so go up one level
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_ROOT = PROJECT_ROOT / "src" / "cloud_services"

# Module name mappings: hyphenated directory -> Python package name
MODULE_MAPPINGS = {
    # Shared services
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
    # Client services
    "integration-adapters": "integration_adapters",
    # Product services
    "detection-engine-core": "detection_engine_core",
    "signal-ingestion-normalization": "signal_ingestion_normalization",
    "user-behaviour-intelligence": "user_behaviour_intelligence",
    "mmm_engine": "mmm_engine",
}

def setup_module_package(module_dir_name: str, category: str = "shared-services") -> None:
    """
    Set up Python package structure for a hyphenated module directory.

    Args:
        module_dir_name: Directory name (e.g., "integration-adapters")
        category: Service category ("shared-services", "client-services", "product-services")
    """
    python_pkg_name = MODULE_MAPPINGS.get(module_dir_name, module_dir_name.replace("-", "_"))
    # Category directories use hyphens, not underscores!
    module_path = SRC_ROOT / category / module_dir_name

    if not module_path.exists():
        return

    # Create root package
    if python_pkg_name not in sys.modules:
        pkg = types.ModuleType(python_pkg_name)
        pkg.__path__ = [str(module_path)]
        sys.modules[python_pkg_name] = pkg

    # Add module path to sys.path if not already there
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

    # Create subpackages for common directories
    common_subdirs = ["services", "database", "adapters", "reliability", "observability", "routes", "models", "integrations"]
    for subdir in common_subdirs:
        subdir_path = module_path / subdir
        if subdir_path.exists() and subdir_path.is_dir():
            subpkg_name = f"{python_pkg_name}.{subdir}"
            if subpkg_name not in sys.modules:
                subpkg = types.ModuleType(subpkg_name)
                subpkg.__path__ = [str(subdir_path)]
                sys.modules[subpkg_name] = subpkg

                # For nested subdirectories (e.g., adapters/github)
                if subdir == "adapters" and (subdir_path / "github").exists():
                    github_pkg_name = f"{python_pkg_name}.adapters.github"
                    if github_pkg_name not in sys.modules:
                        github_pkg = types.ModuleType(github_pkg_name)
                        github_pkg.__path__ = [str(subdir_path / "github")]
                        sys.modules[github_pkg_name] = github_pkg

    # Load key modules if they exist
    # Note: We don't eagerly load modules here as they may have dependencies
    # that aren't available during collection. Tests should import directly.
    # The package structure is set up above, which is sufficient for imports.

# Set up all modules at root level
# This runs when conftest.py is imported by pytest
# Only execute if SRC_ROOT exists (prevents errors during direct import testing)
if SRC_ROOT.exists():
    module_filter = os.getenv("ZEROUI_TEST_MODULE_FILTER")
    # Optional optimization: when ZEROUI_TEST_MODULE_FILTER is set (used by the runner),
    # only initialize the matching module; when unset, the full default setup runs.
    for category in ["shared-services", "client-services", "product-services"]:
        # Category directories use hyphens, not underscores!
        category_path = SRC_ROOT / category
        if category_path.exists():
            for item in category_path.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    if module_filter:
                        mapped_name = MODULE_MAPPINGS.get(item.name, item.name.replace("-", "_"))
                        if module_filter not in (item.name, mapped_name):
                            continue
                    try:
                        setup_module_package(item.name, category)
                    except Exception as e:
                        # Log but don't fail - some modules may have issues
                        import warnings
                        warnings.warn(f"Failed to set up {item.name}: {e}", UserWarning)


def pytest_configure(config):
    # Register custom markers used in performance suites.
    config.addinivalue_line("markers", "iam_performance: identity performance tests")
    config.addinivalue_line("markers", "iam_security: identity security tests")
    config.addinivalue_line("markers", "kms_performance: key management service performance tests")
    config.addinivalue_line("markers", "kms_security: key management service security tests")
    config.addinivalue_line("markers", "resilience: resilience scenarios")
    config.addinivalue_line("markers", "llm_gateway_security: llm gateway security tests")

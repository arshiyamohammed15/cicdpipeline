"""
Root-level pytest configuration.

Provides standardized module path resolution for all tests.
Handles hyphenated directory names by creating proper Python package structures.
"""
import sys
import importlib.util
import importlib.machinery
import os
import types
import warnings
from pathlib import Path
import pytest
import asyncio

from tools.test_registry.path_normalizer import setup_path_normalization, pin_repo_config
from data_governance_privacy.services import DataGovernanceService

# Project root - conftest.py is in tests/, so go up one level
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
setup_path_normalization(PROJECT_ROOT)

import importlib

# Standardize the health_reliability_monitoring models module across workers so
# SafeToActResponse class identity remains stable even when different suites are
# collected together.
try:
    hrm_models = importlib.import_module("health_reliability_monitoring.models")
    sys.modules.setdefault(
        "cloud_services.shared_services.health_reliability_monitoring.models",
        hrm_models,
    )
except Exception:
    hrm_models = None

_TRACKED_EVENT_LOOPS: list[asyncio.AbstractEventLoop] = []
_ORIGINAL_NEW_EVENT_LOOP = asyncio.new_event_loop
_ORIGINAL_GET_EVENT_LOOP = asyncio.get_event_loop


def _track_loop(loop: asyncio.AbstractEventLoop) -> None:
    if loop not in _TRACKED_EVENT_LOOPS:
        _TRACKED_EVENT_LOOPS.append(loop)


def _tracked_new_event_loop() -> asyncio.AbstractEventLoop:
    loop = _ORIGINAL_NEW_EVENT_LOOP()
    _track_loop(loop)
    return loop


def _tracked_get_event_loop() -> asyncio.AbstractEventLoop:
    loop = _ORIGINAL_GET_EVENT_LOOP()
    _track_loop(loop)
    return loop


asyncio.new_event_loop = _tracked_new_event_loop  # type: ignore[assignment]
asyncio.get_event_loop = _tracked_get_event_loop  # type: ignore[assignment]

# Suppress expected setup warnings for optional modules that are not present in this harness.
warnings.filterwarnings(
    "ignore",
    message=r"Failed to set up (clients|models|services|health-reliability-monitoring): .*",
    category=UserWarning,
)
# Suppress noisy deprecations from third-party clients used by TestClient/httpx.
warnings.filterwarnings(
    "ignore",
    message=r"The 'app' shortcut is now deprecated",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Use 'content=<.*>' to upload raw bytes/text content.",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Unclosed <MemoryObject.*",
    category=ResourceWarning,
)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings(
    "ignore",
    message=r".*app' shortcut is now deprecated.*",
    category=DeprecationWarning,
)
warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", DeprecationWarning)

TESTS_ROOT = PROJECT_ROOT / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.append(str(TESTS_ROOT))

SRC_ROOT_DIR = PROJECT_ROOT / "src"
if str(SRC_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT_DIR))

import importlib

# Force the real cloud_services package from src to avoid test-package shadowing.
try:
    cloud_services_pkg = importlib.import_module("cloud_services")
    sys.modules["cloud_services"] = cloud_services_pkg
except Exception:
    cloud_services_pkg = None

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

    # Create root package using the real __init__.py when present.
    if python_pkg_name not in sys.modules:
        init_file = module_path / "__init__.py"
        if init_file.exists():
            spec = importlib.util.spec_from_file_location(
                python_pkg_name,
                init_file,
                submodule_search_locations=[str(module_path)],
            )
            if spec is not None:
                pkg = importlib.util.module_from_spec(spec)
                if spec.loader is not None:
                    spec.loader.exec_module(pkg)  # type: ignore[call-arg]
                sys.modules[python_pkg_name] = pkg
        else:
            pkg = types.ModuleType(python_pkg_name)
            pkg.__path__ = [str(module_path)]
            pkg.__spec__ = importlib.machinery.ModuleSpec(
                name=python_pkg_name,
                loader=None,
                is_package=True,
            )
            pkg.__spec__.submodule_search_locations = pkg.__path__
            sys.modules[python_pkg_name] = pkg
    else:
        pkg = sys.modules[python_pkg_name]

    # Special-case package shim for health_reliability_monitoring.security to allow nested test modules.
    if module_dir_name == "health-reliability-monitoring":
        sec_file = module_path / "security.py"
        if sec_file.exists():
            sec_tests = PROJECT_ROOT / "tests" / "cloud_services" / "shared_services" / "health_reliability_monitoring" / "security"
            sec_search = [str(sec_tests)] if sec_tests.exists() else [str(sec_file.parent)]
            sec_spec = importlib.util.spec_from_file_location(
                "cloud_services.shared_services.health_reliability_monitoring.security",
                sec_file,
                submodule_search_locations=sec_search,
            )
            if sec_spec is not None:
                sec_module = importlib.util.module_from_spec(sec_spec)
                sec_module.__path__ = sec_search
                sys.modules["cloud_services.shared_services.health_reliability_monitoring.security"] = sec_module
                if sec_spec.loader is not None:
                    sec_spec.loader.exec_module(sec_module)  # type: ignore[call-arg]

    if module_dir_name == "detection-engine-core":
        try:
            import detection_engine_core.routes as de_routes
            sys.modules["routes"] = de_routes
        except Exception:
            pass

    # Extend module search path with matching tests package if present.
    tests_pkg = PROJECT_ROOT / "tests" / "cloud_services" / category.replace("-", "_") / python_pkg_name
    if tests_pkg.exists():
        path_list = list(getattr(pkg, "__path__", []))
        tests_path_str = str(tests_pkg)
        if tests_path_str not in path_list:
            pkg.__path__ = path_list + [tests_path_str]

    # Add module path to sys.path if not already there
    if str(module_path) not in sys.path:
        sys.path.append(str(module_path))

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
    # Register namespaced alias (cloud_services.<category>.<pkg>) to ease imports.
    category_pkg = category.replace("-", "_")
    namespaced = f"cloud_services.{category_pkg}.{python_pkg_name}"
    if "cloud_services" in sys.modules:
        ns_module = sys.modules[namespaced] = sys.modules[python_pkg_name]
        if getattr(ns_module, "__spec__", None) is None:
            ns_module.__spec__ = importlib.machinery.ModuleSpec(
                name=namespaced,
                loader=None,
                is_package=True,
            )
            ns_module.__spec__.submodule_search_locations = getattr(ns_module, "__path__", [])

# Set up all modules at root level
# This runs when conftest.py is imported by pytest
# Only execute if SRC_ROOT exists (prevents errors during direct import testing)
if SRC_ROOT.exists():
    module_filter = os.getenv("ZEROUI_TEST_MODULE_FILTER")
    # Optional optimization: when ZEROUI_TEST_MODULE_FILTER is set (used by the runner),
    # only initialize the matching module; when unset, the full default setup runs.
    for category_path in SRC_ROOT.iterdir():
        if not category_path.is_dir() or category_path.name.startswith("_"):
            continue
        category = category_path.name
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

    # Ensure the repository-level config package remains authoritative.
    pin_repo_config(PROJECT_ROOT)

    # Extend mmm_engine package search path to include test package for collection.
    mmm_tests = PROJECT_ROOT / "tests" / "mmm_engine"
    try:
        mmm_pkg = importlib.import_module("mmm_engine")
    except Exception:
        mmm_pkg = None
    if mmm_pkg and mmm_tests.exists():
        # Keep source/product_services paths first but include legacy tests/mmm_engine namespace for collection.
        existing = list(getattr(mmm_pkg, "__path__", []))
        mmm_test_path = str(mmm_tests)
        if mmm_test_path not in existing:
            mmm_pkg.__path__ = existing + [mmm_test_path]
        else:
            mmm_pkg.__path__ = existing

    # Extend cloud_services product_services/client_services packages to include test paths.
    product_tests = PROJECT_ROOT / "tests" / "cloud_services" / "product_services"
    client_tests = PROJECT_ROOT / "tests" / "cloud_services" / "client_services"
    try:
        product_pkg = importlib.import_module("cloud_services.product_services")
        p_paths = list(getattr(product_pkg, "__path__", []))
        if product_tests.exists():
            test_p = str(product_tests)
            if test_p not in p_paths:
                product_pkg.__path__ = p_paths + [test_p]
    except Exception:
        pass

    try:
        client_pkg = importlib.import_module("cloud_services.client_services")
        c_paths = list(getattr(client_pkg, "__path__", []))
        if client_tests.exists():
            test_c = str(client_tests)
            if test_c not in c_paths:
                client_pkg.__path__ = c_paths + [test_c]
    except Exception:
        pass

    shared_tests = PROJECT_ROOT / "tests" / "cloud_services" / "shared_services"
    try:
        shared_pkg = importlib.import_module("cloud_services.shared_services")
        s_paths = list(getattr(shared_pkg, "__path__", []))
        src_shared = SRC_ROOT / "shared-services"
        if src_shared.exists():
            src_shared_str = str(src_shared)
            if src_shared_str not in s_paths:
                s_paths.append(src_shared_str)
        if shared_tests.exists():
            test_s = str(shared_tests)
            if test_s not in s_paths:
                shared_pkg.__path__ = s_paths + [test_s]
            else:
                shared_pkg.__path__ = s_paths
    except Exception:
        pass

    # Force-load LLM Gateway package to avoid resolution conflicts with third-party 'routes' module.
    try:
        llm_pkg_path = SRC_ROOT / "llm_gateway"
        llm_init = llm_pkg_path / "__init__.py"
        routes_init = llm_pkg_path / "routes" / "__init__.py"
        if llm_init.exists():
            llm_spec = importlib.util.spec_from_file_location(
                "cloud_services.llm_gateway",
                llm_init,
                submodule_search_locations=[str(llm_pkg_path)],
            )
            if llm_spec is not None:
                llm_module = importlib.util.module_from_spec(llm_spec)
                llm_module.__path__ = [str(llm_pkg_path)]
                sys.modules["cloud_services.llm_gateway"] = llm_module
                if llm_spec.loader is not None:
                    llm_spec.loader.exec_module(llm_module)  # type: ignore[call-arg]
        sys.modules.pop("routes", None)
        if routes_init.exists():
            routes_spec = importlib.util.spec_from_file_location(
                "cloud_services.llm_gateway.routes",
                routes_init,
                submodule_search_locations=[str(routes_init.parent)],
            )
        if routes_spec is not None:
            routes_module = importlib.util.module_from_spec(routes_spec)
            routes_module.__path__ = [str(routes_init.parent)]
            sys.modules["cloud_services.llm_gateway.routes"] = routes_module
            if routes_spec.loader is not None:
                routes_spec.loader.exec_module(routes_module)  # type: ignore[call-arg]
    except Exception:
        pass

    # Explicitly register BRLCO performance package to avoid collection import failures.
    try:
        brlco_perf_init = PROJECT_ROOT / "tests" / "cloud_services" / "shared_services" / "budgeting_rate_limiting_cost_observability" / "performance" / "__init__.py"
        if brlco_perf_init.exists():
            perf_spec = importlib.util.spec_from_file_location(
                "cloud_services.shared_services.budgeting_rate_limiting_cost_observability.performance",
                brlco_perf_init,
                submodule_search_locations=[str(brlco_perf_init.parent)],
            )
            if perf_spec is not None:
                perf_module = importlib.util.module_from_spec(perf_spec)
                perf_module.__path__ = [str(brlco_perf_init.parent)]
                sys.modules["cloud_services.shared_services.budgeting_rate_limiting_cost_observability.performance"] = perf_module
                if perf_spec.loader is not None:
                    perf_spec.loader.exec_module(perf_module)  # type: ignore[call-arg]
        # Pre-register common subpackages to avoid collection import errors.
        brlco_root = PROJECT_ROOT / "tests" / "cloud_services" / "shared_services" / "budgeting_rate_limiting_cost_observability"
        for subpkg in ["unit", "integration", "security", "resilience", "load", "features"]:
            sub_init = brlco_root / subpkg / "__init__.py"
            if not sub_init.exists():
                continue
            fqmn = f"cloud_services.shared_services.budgeting_rate_limiting_cost_observability.{subpkg}"
            spec_sub = importlib.util.spec_from_file_location(
                fqmn,
                sub_init,
                submodule_search_locations=[str(sub_init.parent)],
            )
            if spec_sub is None:
                continue
            sub_module = importlib.util.module_from_spec(spec_sub)
            sub_module.__path__ = [str(sub_init.parent)]
            sys.modules[fqmn] = sub_module
            if spec_sub.loader is not None:
                spec_sub.loader.exec_module(sub_module)  # type: ignore[call-arg]
    except Exception:
        pass


def pytest_configure(config):
    # Register custom markers used in performance suites.
    config.addinivalue_line("markers", "iam_performance: identity performance tests")
    config.addinivalue_line("markers", "iam_security: identity security tests")
    config.addinivalue_line("markers", "kms_performance: key management service performance tests")
    config.addinivalue_line("markers", "kms_security: key management service security tests")
    config.addinivalue_line("markers", "resilience: resilience scenarios")
    config.addinivalue_line("markers", "llm_gateway_security: llm gateway security tests")


def pytest_sessionfinish(session, exitstatus):  # type: ignore[override]
    for loop in list(_TRACKED_EVENT_LOOPS):
        if loop.is_running() or loop.is_closed():
            continue
        loop.close()
    asyncio.set_event_loop(None)


def pytest_ignore_collect(collection_path: Path, config):  # type: ignore[override]
    # Avoid duplicate MMM Engine tests under two hierarchies; prefer cloud_services path.
    path_str = str(collection_path)
    if "tests\\mmm_engine\\" in path_str or "tests/mmm_engine/" in path_str:
        return True


# Shared performance runner fixture for performance suites.
from tests.shared_harness import PerfRunner
from tests.shared_harness import TenantFactory, BudgetFixtureFactory


@pytest.fixture
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        if not loop.is_closed():
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        asyncio.set_event_loop(None)


@pytest.fixture
def perf_runner() -> PerfRunner:
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = PerfRunner(loop=loop)
    try:
        yield runner
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


@pytest.fixture
def tenant_factory() -> TenantFactory:
    return TenantFactory()


@pytest.fixture
def budget_factory() -> BudgetFixtureFactory:
    return BudgetFixtureFactory()


@pytest.fixture
def governance_service() -> DataGovernanceService:
    return DataGovernanceService()

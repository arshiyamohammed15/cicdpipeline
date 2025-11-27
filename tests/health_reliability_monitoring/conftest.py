"""Shared pytest configuration for all health reliability monitoring tests."""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
import pytest

# Setup module imports - create health_reliability_monitoring package from health-reliability-monitoring directory
# conftest.py is at: tests/health_reliability_monitoring/conftest.py
# parents[0] = tests/health_reliability_monitoring (directory), parents[1] = tests, parents[2] = repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Create health_reliability_monitoring module structure from health-reliability-monitoring directory
MODULE_DIR = SRC_DIR / "cloud_services" / "shared-services" / "health-reliability-monitoring"

def _setup_health_reliability_monitoring_module():
    """Set up the health_reliability_monitoring module structure."""
    if "health_reliability_monitoring" in sys.modules and "health_reliability_monitoring.main" in sys.modules:
        return  # Already set up
    
    # CRITICAL: Ensure both repo root and src/ are in sys.path BEFORE loading any modules
    # Repo root is needed for config package (config/constitution/path_utils.py)
    # This must happen before config.py tries to import from config.constitution.path_utils
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    
    # Create parent package with __path__ so Python recognizes it as a package
    parent_pkg = type(sys)('health_reliability_monitoring')
    parent_pkg.__path__ = [str(MODULE_DIR)]
    sys.modules['health_reliability_monitoring'] = parent_pkg
    
    # Create subpackages first with __path__ so Python recognizes them as packages
    for subpkg in ["database", "routes", "services"]:
        pkg_name = f"health_reliability_monitoring.{subpkg}"
        if pkg_name not in sys.modules:
            pkg = type(sys)(pkg_name)
            pkg.__path__ = [str(MODULE_DIR / subpkg)]
            sys.modules[pkg_name] = pkg
    
    # Load modules in proper dependency order
    # Base modules first
    base_modules = [
        ("config", "config.py"),
        ("models", "models.py"),
        ("dependencies", "dependencies.py"),
    ]
    
    for module_name, filename in base_modules:
        module_path = MODULE_DIR / filename
        if module_path.exists():
            full_name = f"health_reliability_monitoring.{module_name}"
            spec = importlib.util.spec_from_file_location(full_name, module_path)
            module = importlib.util.module_from_spec(spec)
            # Set __file__ and __package__ for proper relative imports
            module.__file__ = str(module_path.resolve())
            module.__package__ = "health_reliability_monitoring"
            # Set __path__ for package discovery
            if not hasattr(module, '__path__'):
                module.__path__ = [str(MODULE_DIR)]
            sys.modules[full_name] = module
            try:
                # Ensure both repo root and src/ are in path before executing module (critical for config.py imports)
                if str(REPO_ROOT) not in sys.path:
                    sys.path.insert(0, str(REPO_ROOT))
                if str(SRC_DIR) not in sys.path:
                    sys.path.insert(0, str(SRC_DIR))
                spec.loader.exec_module(module)
            except Exception as e:
                # Config module is critical - if it fails, the whole setup fails
                if module_name == "config":
                    import traceback
                    error_msg = f"CRITICAL: Failed to load {full_name}: {e}\n"
                    error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
                    raise ImportError(error_msg) from e
                # Other modules may have optional dependencies
                import warnings
                warnings.warn(f"Failed to load {full_name}: {e}", UserWarning)
    
    # Load database models
    db_models_path = MODULE_DIR / "database" / "models.py"
    if db_models_path.exists():
        spec_db = importlib.util.spec_from_file_location("health_reliability_monitoring.database.models", db_models_path)
        db_module = importlib.util.module_from_spec(spec_db)
        db_module.__file__ = str(db_models_path)
        db_module.__package__ = "health_reliability_monitoring.database"
        sys.modules["health_reliability_monitoring.database.models"] = db_module
        try:
            spec_db.loader.exec_module(db_module)
        except Exception:
            pass
    
    # Load service container (depends on config, models, database.models, dependencies)
    container_path = MODULE_DIR / "service_container.py"
    if container_path.exists():
        spec_container = importlib.util.spec_from_file_location("health_reliability_monitoring.service_container", container_path)
        container_module = importlib.util.module_from_spec(spec_container)
        container_module.__file__ = str(container_path.resolve())
        container_module.__package__ = "health_reliability_monitoring"
        sys.modules["health_reliability_monitoring.service_container"] = container_module
        try:
            # Ensure paths are set
            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))
            spec_container.loader.exec_module(container_module)
        except Exception as e:
            import traceback
            error_msg = f"CRITICAL: Failed to load health_reliability_monitoring.service_container: {e}\n"
            error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
            raise ImportError(error_msg) from e
    
    # Load security (depends on dependencies and service_container)
    security_path = MODULE_DIR / "security.py"
    if security_path.exists():
        spec_security = importlib.util.spec_from_file_location("health_reliability_monitoring.security", security_path)
        security_module = importlib.util.module_from_spec(spec_security)
        security_module.__file__ = str(security_path.resolve())
        security_module.__package__ = "health_reliability_monitoring"
        sys.modules["health_reliability_monitoring.security"] = security_module
        try:
            # Ensure paths are set
            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))
            spec_security.loader.exec_module(security_module)
            # Verify key functions exist
            if not hasattr(security_module, 'ensure_scope'):
                import warnings
                warnings.warn("security module loaded but 'ensure_scope' not found", UserWarning)
        except Exception as e:
            import traceback
            error_msg = f"CRITICAL: Failed to load health_reliability_monitoring.security: {e}\n"
            error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
            raise ImportError(error_msg) from e
    
    # Load individual route modules FIRST (before routes.__init__ which imports from them)
    # These modules depend on models, security, service_container, etc. which should already be loaded
    route_modules = [
        ("routes.registry", "routes/registry.py"),
        ("routes.safe_to_act", "routes/safe_to_act.py"),
        ("routes.health", "routes/health.py"),
    ]
    for module_name, filename in route_modules:
        module_path = MODULE_DIR / filename
        if module_path.exists():
            full_name = f"health_reliability_monitoring.{module_name}"
            spec = importlib.util.spec_from_file_location(full_name, module_path)
            module = importlib.util.module_from_spec(spec)
            module.__file__ = str(module_path.resolve())
            module.__package__ = "health_reliability_monitoring.routes"
            sys.modules[full_name] = module
            try:
                # Ensure paths are set
                if str(REPO_ROOT) not in sys.path:
                    sys.path.insert(0, str(REPO_ROOT))
                if str(SRC_DIR) not in sys.path:
                    sys.path.insert(0, str(SRC_DIR))
                spec.loader.exec_module(module)
                # Verify router attribute exists
                if not hasattr(module, 'router'):
                    import warnings
                    warnings.warn(f"Route module {full_name} loaded but 'router' attribute not found", UserWarning)
            except Exception as e:
                import traceback
                error_msg = f"CRITICAL: Failed to load route module {full_name}: {e}\n"
                error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
                raise ImportError(error_msg) from e
    
    # Load routes package __init__ AFTER individual route modules (it imports from them)
    routes_init_path = MODULE_DIR / "routes" / "__init__.py"
    if routes_init_path.exists():
        spec_routes_init = importlib.util.spec_from_file_location("health_reliability_monitoring.routes", routes_init_path)
        routes_init_module = importlib.util.module_from_spec(spec_routes_init)
        routes_init_module.__file__ = str(routes_init_path.resolve())
        routes_init_module.__package__ = "health_reliability_monitoring.routes"
        sys.modules["health_reliability_monitoring.routes"] = routes_init_module
        try:
            # Ensure paths are set
            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))
            spec_routes_init.loader.exec_module(routes_init_module)
        except Exception as e:
            import traceback
            error_msg = f"CRITICAL: Failed to load health_reliability_monitoring.routes: {e}\n"
            error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
            raise ImportError(error_msg) from e
    
    # Load services package __init__ if it exists
    services_init_path = MODULE_DIR / "services" / "__init__.py"
    if services_init_path.exists():
        spec_services_init = importlib.util.spec_from_file_location("health_reliability_monitoring.services", services_init_path)
        services_init_module = importlib.util.module_from_spec(spec_services_init)
        services_init_module.__file__ = str(services_init_path)
        services_init_module.__package__ = "health_reliability_monitoring.services"
        sys.modules["health_reliability_monitoring.services"] = services_init_module
        try:
            spec_services_init.loader.exec_module(services_init_module)
        except Exception:
            pass
    
    # Load service modules
    service_modules = [
        ("services.registry_service", "services/registry_service.py"),
        ("services.safe_to_act_service", "services/safe_to_act_service.py"),
        ("services.rollup_service", "services/rollup_service.py"),
        ("services.telemetry_ingestion_service", "services/telemetry_ingestion_service.py"),
    ]
    for module_name, filename in service_modules:
        module_path = MODULE_DIR / filename
        if module_path.exists():
            full_name = f"health_reliability_monitoring.{module_name}"
            spec = importlib.util.spec_from_file_location(full_name, module_path)
            module = importlib.util.module_from_spec(spec)
            module.__file__ = str(module_path)
            module.__package__ = "health_reliability_monitoring.services"
            sys.modules[full_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                pass
    
    # Finally load main - this must be last as it imports from all above modules
    main_path = MODULE_DIR / "main.py"
    if main_path.exists():
        spec_main = importlib.util.spec_from_file_location("health_reliability_monitoring.main", main_path)
        main_module = importlib.util.module_from_spec(spec_main)
        main_module.__file__ = str(main_path)
        main_module.__package__ = "health_reliability_monitoring"
        # Set __path__ for package discovery
        if not hasattr(main_module, '__path__'):
            main_module.__path__ = [str(MODULE_DIR)]
        sys.modules["health_reliability_monitoring.main"] = main_module
        try:
            # Ensure both repo root and src/ are in path before executing main module
            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))
            spec_main.loader.exec_module(main_module)
            # Verify app was created
            if not hasattr(main_module, 'app'):
                raise ImportError("health_reliability_monitoring.main module loaded but 'app' attribute not found")
        except Exception as e:
            # Main module is critical - raise if it fails
            import traceback
            error_msg = f"CRITICAL: Failed to load health_reliability_monitoring.main: {e}\n"
            error_msg += "".join(traceback.format_exception(type(e), e, e.__traceback__))
            raise ImportError(error_msg) from e

# Set up module on import
_setup_health_reliability_monitoring_module()

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Ensure module is set up before test collection."""
    _setup_health_reliability_monitoring_module()

@pytest.fixture(scope="session", autouse=True)
def ensure_module_setup():
    """Ensure module is set up before any tests run."""
    _setup_health_reliability_monitoring_module()
    yield


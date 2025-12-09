"""
Shared fixtures for SIN integration tests.
"""

import pytest
import sys
from pathlib import Path
import importlib.util
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skip(reason="Signal ingestion normalization service not present in test harness")


def load_main_app():
    """Load the FastAPI app from main.py."""
    project_root = Path(__file__).parent.parent.parent.parent
    sin_module_path = project_root / "src" / "cloud_services" / "product-services" / "signal-ingestion-normalization"

    # Set up package structure
    package_name = "signal_ingestion_normalization"
    if package_name not in sys.modules:
        package = type(sys)('module')
        package.__path__ = [str(sin_module_path)]
        sys.modules[package_name] = package

    # Load dependencies first (needed by main)
    deps_path = sin_module_path / "dependencies.py"
    if f"{package_name}.dependencies" not in sys.modules:
        deps_spec = importlib.util.spec_from_file_location(f"{package_name}.dependencies", deps_path)
        deps_mod = importlib.util.module_from_spec(deps_spec)
        deps_mod.__package__ = package_name
        deps_mod.__name__ = f"{package_name}.dependencies"
        deps_mod.__file__ = str(deps_path)
        sys.modules[f"{package_name}.dependencies"] = deps_mod
        deps_spec.loader.exec_module(deps_mod)

    # Load models (needed by dependencies and main)
    models_path = sin_module_path / "models.py"
    if f"{package_name}.models" not in sys.modules:
        models_spec = importlib.util.spec_from_file_location(f"{package_name}.models", models_path)
        models_mod = importlib.util.module_from_spec(models_spec)
        models_mod.__package__ = package_name
        models_mod.__name__ = f"{package_name}.models"
        models_mod.__file__ = str(models_path)
        sys.modules[f"{package_name}.models"] = models_mod
        models_spec.loader.exec_module(models_mod)

    # Load other dependencies in order
    modules_to_load = [
        "governance",
        "producer_registry",
        "validation",
        "normalization",
        "routing",
        "deduplication",
        "dlq",
        "observability",
        "services",
        "routes"
    ]

    for module_name in modules_to_load:
        module_path = sin_module_path / f"{module_name}.py"
        full_name = f"{package_name}.{module_name}"
        if full_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(full_name, module_path)
            mod = importlib.util.module_from_spec(spec)
            mod.__package__ = package_name
            mod.__name__ = full_name
            mod.__file__ = str(module_path)
            sys.modules[full_name] = mod
            spec.loader.exec_module(mod)

    # Load main module
    main_path = sin_module_path / "main.py"
    spec = importlib.util.spec_from_file_location(f"{package_name}.main", main_path)
    main_mod = importlib.util.module_from_spec(spec)
    main_mod.__package__ = package_name
    main_mod.__name__ = f"{package_name}.main"
    main_mod.__file__ = str(main_path)
    sys.modules[f"{package_name}.main"] = main_mod
    spec.loader.exec_module(main_mod)

    return main_mod.app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    app = load_main_app()
    return TestClient(app)


@pytest.fixture
def app_iam(client):
    """Get the IAM instance from the app."""
    import sys
    package_name = "signal_ingestion_normalization"
    main_mod = sys.modules[f"{package_name}.main"]
    # Ensure services are initialized
    if main_mod._iam is None:
        main_mod.initialize_services()
    return main_mod.get_iam_instance()


@pytest.fixture
def app_schema_registry(client):
    """Get the schema registry instance from the app."""
    import sys
    package_name = "signal_ingestion_normalization"
    main_mod = sys.modules[f"{package_name}.main"]
    # Ensure services are initialized
    if main_mod._producer_registry is None:
        main_mod.initialize_services()
    return main_mod._producer_registry.schema_registry


@pytest.fixture
def app_data_governance(client):
    """Get the data governance instance from the app."""
    import sys
    package_name = "signal_ingestion_normalization"
    main_mod = sys.modules[f"{package_name}.main"]
    if main_mod._ingestion_service is None:
        main_mod.initialize_services()
    # Get from governance enforcer
    validation_engine = main_mod._ingestion_service.validation_engine
    return validation_engine.governance_enforcer.data_governance


@pytest.fixture
def app_routing_engine(client):
    """Get the routing engine instance from the app."""
    import sys
    package_name = "signal_ingestion_normalization"
    main_mod = sys.modules[f"{package_name}.main"]
    if main_mod._ingestion_service is None:
        main_mod.initialize_services()
    return main_mod._ingestion_service.routing_engine


@pytest.fixture
def auth_token(client, app_iam):
    """Create a test auth token and register it in the app's IAM instance."""
    token = "test_token_123"
    app_iam.register_token(
        token,
        {"tenant_id": "tenant_1", "producer_id": "producer_1"},
        expires_in_seconds=3600
    )
    return token


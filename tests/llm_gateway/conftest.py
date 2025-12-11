from __future__ import annotations
"""Pytest fixtures and import wiring for the LLM Gateway tests."""


import importlib.machinery
import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLOUD_SERVICES_ROOT = PROJECT_ROOT / "src" / "cloud_services"
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def ensure_cloud_services_package() -> None:
    if "cloud_services" not in sys.modules:
        pkg = types.ModuleType("cloud_services")
        spec = importlib.machinery.ModuleSpec(
            name="cloud_services",
            loader=None,
            is_package=True,
        )
        spec.submodule_search_locations = [str(CLOUD_SERVICES_ROOT)]
        pkg.__spec__ = spec
        pkg.__path__ = spec.submodule_search_locations
        sys.modules["cloud_services"] = pkg

    llm_gateway_pkg = CLOUD_SERVICES_ROOT / "llm_gateway"
    if "cloud_services.llm_gateway" not in sys.modules and llm_gateway_pkg.exists():
        init_py = llm_gateway_pkg / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            "cloud_services.llm_gateway",
            init_py,
            submodule_search_locations=[str(llm_gateway_pkg)],
        )
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            module.__path__ = [str(llm_gateway_pkg)]
            sys.modules["cloud_services.llm_gateway"] = module
            if spec.loader is not None:
                spec.loader.exec_module(module)  # type: ignore[call-arg]

    routes_pkg = llm_gateway_pkg / "routes"
    routes_init = routes_pkg / "__init__.py"
    if routes_pkg.exists() and routes_init.exists():
        # Avoid conflicts with any third-party 'routes' module on sys.path.
        sys.modules.pop("routes", None)
        spec_routes = importlib.util.spec_from_file_location(
            "cloud_services.llm_gateway.routes",
            routes_init,
            submodule_search_locations=[str(routes_pkg)],
        )
        if spec_routes is not None:
            routes_module = importlib.util.module_from_spec(spec_routes)
            sys.modules["cloud_services.llm_gateway.routes"] = routes_module
            if spec_routes.loader is not None:
                spec_routes.loader.exec_module(routes_module)  # type: ignore[call-arg]


ensure_cloud_services_package()

# Import after package setup
from cloud_services.llm_gateway.services import (  # type: ignore  # pylint: disable=import-error
    build_service_with_real_clients,
)
from tests.llm_gateway.service_health import (  # type: ignore
    check_all_services_healthy,
    get_service_urls,
    require_services,
)


@pytest.fixture(scope="session")
def real_services_available() -> bool:
    """
    Check if real backend services are available.

    Set USE_REAL_SERVICES=true to enable real service integration tests.
    """
    use_real = os.getenv("USE_REAL_SERVICES", "false").lower() == "true"
    if not use_real:
        return False

    health_status = check_all_services_healthy()
    all_healthy = all(health_status.values())
    return all_healthy


@pytest.fixture
def real_service_urls() -> dict[str, str]:
    """Get service URLs from environment variables."""
    return get_service_urls()


@pytest.fixture
def llm_gateway_service_real(real_services_available: bool, real_service_urls: dict[str, str]):
    """
    Build LLM Gateway service with real HTTP clients.

    Only available when USE_REAL_SERVICES=true and all services are healthy.
    """
    if not real_services_available:
        # Fall back to in-process defaults to keep tests runnable without external services.
        from cloud_services.llm_gateway.services import build_default_service

        return build_default_service()

    return build_service_with_real_clients(
        iam_url=real_service_urls["iam"],
        policy_url=real_service_urls["policy"],
        data_governance_url=real_service_urls["data_governance"],
        budget_url=real_service_urls["budget"],
        eris_url=real_service_urls["eris"],
        alerting_url=real_service_urls["alerting"],
    )


@pytest.fixture
def llm_gateway_service_mocked():
    """
    Build LLM Gateway service with mocked clients for unit tests.

    This is the default fixture for unit tests.
    """
    from cloud_services.llm_gateway.services import build_default_service  # type: ignore  # pylint: disable=import-error

    return build_default_service()

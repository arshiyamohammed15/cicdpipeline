"""Pytest fixtures and import wiring for the LLM Gateway tests."""

from __future__ import annotations

import importlib.machinery
import os
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLOUD_SERVICES_ROOT = PROJECT_ROOT / "src" / "cloud-services"


def ensure_cloud_services_package() -> None:
    if "cloud_services" in sys.modules:
        return

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
    if not all_healthy:
        unhealthy = [name for name, healthy in health_status.items() if not healthy]
        pytest.skip(
            f"Real services not available. Unhealthy services: {', '.join(unhealthy)}. "
            f"Set USE_REAL_SERVICES=false to use mocked services."
        )
    return True


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
        pytest.skip("Real services not enabled or unavailable")

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


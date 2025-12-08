from __future__ import annotations
"""
Health check utilities for real backend services.

Validates that required services are available before running integration tests
with real HTTP clients.
"""


import os
from typing import Dict, Optional

import httpx


def check_service_health(base_url: str, health_endpoint: str = "/health", timeout: float = 2.0) -> bool:
    """
    Check if a service is healthy by calling its health endpoint.

    Args:
        base_url: Service base URL
        health_endpoint: Health check endpoint path
        timeout: Request timeout in seconds

    Returns:
        True if service is healthy (returns 200), False otherwise
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{base_url}{health_endpoint}")
            return response.status_code == 200
    except (httpx.RequestError, httpx.TimeoutException):
        return False


def get_service_urls() -> Dict[str, Optional[str]]:
    """
    Get service URLs from environment variables with defaults.

    Returns:
        Dictionary mapping service names to URLs
    """
    return {
        "iam": os.getenv("IAM_SERVICE_URL", "http://localhost:8001/iam/v1"),
        "policy": os.getenv("POLICY_SERVICE_URL", "http://localhost:8003"),
        "data_governance": os.getenv(
            "DATA_GOVERNANCE_SERVICE_URL", "http://localhost:8002/privacy/v1"
        ),
        "budget": os.getenv("BUDGET_SERVICE_URL", "http://localhost:8035"),
        "eris": os.getenv("ERIS_SERVICE_URL", "http://localhost:8007"),
        "alerting": os.getenv("ALERTING_SERVICE_URL", "http://localhost:8004/v1"),
    }


def check_all_services_healthy() -> Dict[str, bool]:
    """
    Check health of all required backend services.

    Returns:
        Dictionary mapping service names to health status (True/False)
    """
    urls = get_service_urls()
    health_status: Dict[str, bool] = {}

    # IAM health endpoint
    health_status["iam"] = check_service_health(urls["iam"], "/health")

    # Policy health endpoint
    health_status["policy"] = check_service_health(urls["policy"], "/health")

    # Data Governance health endpoint
    health_status["data_governance"] = check_service_health(
        urls["data_governance"], "/health"
    )

    # Budget health endpoint
    health_status["budget"] = check_service_health(urls["budget"], "/health")

    # ERIS health endpoint
    health_status["eris"] = check_service_health(urls["eris"], "/health")

    # Alerting health endpoint (may not have /health, try /alerts as fallback)
    alerting_healthy = check_service_health(urls["alerting"], "/health")
    # Try alternative endpoint
    alerting_healthy = check_service_health(urls["alerting"], "/alerts")
    health_status["alerting"] = alerting_healthy

    return health_status


def require_services(*service_names: str) -> bool:
    """
    Check if specified services are healthy.

    Args:
        *service_names: Names of services to check (iam, policy, data_governance, budget, eris, alerting)

    Returns:
        True if all specified services are healthy, False otherwise
    """
    health_status = check_all_services_healthy()
    for name in service_names:
        if not health_status.get(name, False):
            return False
    return True


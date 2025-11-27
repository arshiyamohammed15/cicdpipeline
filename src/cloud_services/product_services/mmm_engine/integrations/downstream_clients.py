"""
HTTP clients for delivering MMM actions to downstream channels.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from ..observability.metrics import record_delivery_attempt

logger = logging.getLogger(__name__)

DELIVERY_METRICS = {
    "total_attempts": 0,
    "successful_deliveries": 0,
    "failed_deliveries": 0,
}


class BaseDeliveryClient:
    """Shared HTTP helper for downstream delivery."""

    def __init__(
        self,
        base_url: Optional[str],
        default_path: str,
        channel_name: str,
        timeout_seconds: float = 2.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.5,
    ):
        self.base_url = base_url
        self.default_path = default_path
        self.channel_name = channel_name
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

    def _post(self, payload: Dict[str, Any], path: Optional[str] = None) -> bool:
        if not self.base_url:
            logger.debug("Delivery client %s disabled (no base URL)", self.__class__.__name__)
            return False
        url = urljoin(self.base_url, path or self.default_path)
        attempt = 0
        success = False
        while attempt < self.max_retries and not success:
            attempt += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                success = True
                record_delivery_attempt(self.channel_name, True)
            except Exception as exc:  # pragma: no cover - network failures
                logger.warning(
                    "%s delivery attempt %s/%s to %s failed: %s",
                    self.__class__.__name__,
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds)
                record_delivery_attempt(self.channel_name, False)
        DELIVERY_METRICS["total_attempts"] += attempt
        if success:
            DELIVERY_METRICS["successful_deliveries"] += 1
            logger.debug("%s delivered payload to %s", self.__class__.__name__, url)
        else:
            DELIVERY_METRICS["failed_deliveries"] += 1
        return success


class EdgeAgentClient(BaseDeliveryClient):
    """Sends IDE-surface actions to the Edge Agent / ZeroUI extension."""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or os.getenv("EDGE_AGENT_BASE_URL"), "/api/v1/mmm/actions", channel_name="ide")

    def send_action(self, payload: Dict[str, Any]) -> bool:
        return self._post(payload)


class CIWorkflowClient(BaseDeliveryClient):
    """Publishes Mentor/Multiplier actions to CI/PR orchestration services."""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or os.getenv("CI_WORKFLOW_BASE_URL"), "/api/v1/mmm/actions", channel_name="ci")

    def send_action(self, payload: Dict[str, Any]) -> bool:
        return self._post(payload)


class AlertingClient(BaseDeliveryClient):
    """Routes actions to the Alerting & Notification Service (EPC-4)."""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or os.getenv("ALERTING_BASE_URL"), "/api/v1/notifications/mmm", channel_name="alert")

    def send_action(self, payload: Dict[str, Any]) -> bool:
        return self._post(payload)



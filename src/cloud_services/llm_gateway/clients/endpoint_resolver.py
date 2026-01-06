"""
LLM Endpoint Resolver - Resolves Ollama endpoint URLs based on plane and topology mode.

Per AGENTS.md and docs/architecture/dev/llm_topology.md:
- LLM endpoints MUST be resolved via LLM_TOPOLOGY_* environment variables
- No hardcoded Ollama URLs in code
- Endpoint resolution based on LLM_TOPOLOGY_MODE and plane context
- LOCAL_SINGLE_PLANE: Forward tenant/product/shared to IDE endpoint
- PER_PLANE: Use plane-specific endpoints
"""

from __future__ import annotations

import os
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Plane(str, Enum):
    """Deployment plane identifier."""

    IDE = "ide"
    TENANT = "tenant"
    PRODUCT = "product"
    SHARED = "shared"


class TopologyMode(str, Enum):
    """LLM topology mode."""

    LOCAL_SINGLE_PLANE = "LOCAL_SINGLE_PLANE"
    PER_PLANE = "PER_PLANE"


class LLMEndpointResolver:
    """
    Resolves LLM endpoint URLs based on plane context and topology mode.

    Per AGENTS.md directive: "LLM endpoints MUST be resolved via LLM_TOPOLOGY_*
    environment variables; no hardcoded Ollama URLs in code."

    Resolution logic:
    1. Read LLM_TOPOLOGY_MODE from environment
    2. If LOCAL_SINGLE_PLANE and plane is in LLM_FORWARD_TO_IDE_PLANES:
       - Use IDE_LLM_BASE_URL
    3. Otherwise (PER_PLANE or plane not in forward list):
       - Use {PLANE}_LLM_BASE_URL for the current plane
    """

    def __init__(self) -> None:
        """Initialize endpoint resolver."""
        self._topology_mode: Optional[TopologyMode] = None
        self._forward_to_ide_planes: list[str] = []
        self._cached_endpoints: dict[str, str] = {}

    def _get_topology_mode(self) -> TopologyMode:
        """Get topology mode from environment."""
        if self._topology_mode is None:
            mode_str = os.getenv("LLM_TOPOLOGY_MODE", "PER_PLANE").upper()
            try:
                self._topology_mode = TopologyMode(mode_str)
            except ValueError:
                logger.warning(
                    f"Invalid LLM_TOPOLOGY_MODE: {mode_str}. Defaulting to PER_PLANE"
                )
                self._topology_mode = TopologyMode.PER_PLANE
        return self._topology_mode

    def _get_forward_to_ide_planes(self) -> list[str]:
        """Get list of planes that forward to IDE endpoint in LOCAL_SINGLE_PLANE mode."""
        if not self._forward_to_ide_planes:
            forward_str = os.getenv("LLM_FORWARD_TO_IDE_PLANES", "tenant,product,shared")
            self._forward_to_ide_planes = [
                plane.strip().lower() for plane in forward_str.split(",")
            ]
        return self._forward_to_ide_planes

    def _get_ide_endpoint(self) -> str:
        """Get IDE plane endpoint URL."""
        if "ide" not in self._cached_endpoints:
            endpoint = os.getenv("IDE_LLM_BASE_URL", "http://localhost:11434")
            self._cached_endpoints["ide"] = endpoint
        return self._cached_endpoints["ide"]

    def _get_plane_endpoint(self, plane: Plane) -> str:
        """Get plane-specific endpoint URL."""
        plane_key = plane.value.lower()
        if plane_key not in self._cached_endpoints:
            env_var = f"{plane.value.upper()}_LLM_BASE_URL"
            endpoint = os.getenv(env_var)
            if not endpoint:
                logger.warning(
                    f"{env_var} not set. Defaulting to IDE endpoint for {plane.value} plane"
                )
                endpoint = self._get_ide_endpoint()
            self._cached_endpoints[plane_key] = endpoint
        return self._cached_endpoints[plane_key]

    def resolve_endpoint(self, plane: Plane) -> str:
        """
        Resolve LLM endpoint URL for the given plane.

        Args:
            plane: Deployment plane (ide/tenant/product/shared)

        Returns:
            Base URL for the LLM endpoint (e.g., "http://localhost:11434")

        Raises:
            ValueError: If endpoint cannot be resolved
        """
        topology_mode = self._get_topology_mode()

        # IDE plane always uses its own endpoint
        if plane == Plane.IDE:
            return self._get_ide_endpoint()

        # LOCAL_SINGLE_PLANE mode: forward tenant/product/shared to IDE endpoint
        if topology_mode == TopologyMode.LOCAL_SINGLE_PLANE:
            forward_planes = self._get_forward_to_ide_planes()
            if plane.value.lower() in forward_planes:
                logger.debug(
                    f"LOCAL_SINGLE_PLANE mode: forwarding {plane.value} to IDE endpoint"
                )
                return self._get_ide_endpoint()

        # PER_PLANE mode or plane not in forward list: use plane-specific endpoint
        return self._get_plane_endpoint(plane)

    def get_topology_mode(self) -> TopologyMode:
        """Get current topology mode."""
        return self._get_topology_mode()

    def reset_cache(self) -> None:
        """Reset cached endpoints (useful for testing)."""
        self._cached_endpoints.clear()
        self._topology_mode = None
        self._forward_to_ide_planes = []


# Global singleton instance
_endpoint_resolver: Optional[LLMEndpointResolver] = None


def get_endpoint_resolver() -> LLMEndpointResolver:
    """Get global endpoint resolver instance."""
    global _endpoint_resolver
    if _endpoint_resolver is None:
        _endpoint_resolver = LLMEndpointResolver()
    return _endpoint_resolver


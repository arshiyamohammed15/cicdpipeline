"""Component metadata and dependency clients."""
from __future__ import annotations

from typing import Awaitable, Callable, Dict, List, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

from ..config import get_settings

settings = get_settings()


class ComponentMetadataClient:
    async def get_component(self, component_id: str) -> Dict[str, str]:
        return {
            "component_id": component_id,
            "service_name": component_id,
            "owner_group": "default",
            "slo_snapshot_url": f"https://health.local/{component_id}/slo",
        }

    async def get_dependencies(self, component_id: str) -> List[str]:
        return []


RequestCallable = Callable[[str, str, str], Awaitable[List[str]]]


class DependencyGraphClient:
    def __init__(self, base_url: Optional[str] = None, requester: Optional[RequestCallable] = None):
        self.base_url = base_url or settings.dependency.graph_service_url
        self._requester = requester

    async def shared_dependencies(self, component_a: str, component_b: str) -> List[str]:
        if self.base_url:
            if self._requester:
                return await self._requester(self.base_url, component_a, component_b)
            return await self._fetch_shared_from_service(component_a, component_b)
        return []

    async def _fetch_shared_from_service(self, component_a: str, component_b: str) -> List[str]:  # pragma: no cover
        if httpx is None or not self.base_url:  # pragma: no cover
            return []
        try:  # pragma: no cover
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/v1/dependencies/shared",
                    params={"component_a": component_a, "component_b": component_b},
                )
                response.raise_for_status()
                payload = response.json()
                return payload.get("shared", [])
        except httpx.HTTPError:
            return []


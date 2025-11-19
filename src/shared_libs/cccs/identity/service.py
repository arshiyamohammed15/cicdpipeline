"""Identity & Actor Provenance (IAPS) implementation."""

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from ..adapters.epc1_adapter import EPC1AdapterConfig, EPC1IdentityAdapter
from ..exceptions import ActorUnavailableError
from ..types import ActorBlock, ActorContext


@dataclass(frozen=True)
class IdentityConfig:
    """Configuration for identity normalization."""

    epc1_base_url: str
    epc1_timeout_seconds: float = 5.0
    epc1_api_version: str = "v1"
    fallback_enabled: bool = False


class IdentityService:
    """
    Resolves actors via EPC-1 while honouring the zero-synchronous-network requirement.

    The request path reads from a cache only; EPC-1 calls are queued into the WAL and replayed
    by the background drain once connectivity returns.
    """

    def __init__(self, config: IdentityConfig, wal: Optional[Any] = None):
        self._config = config
        adapter_config = EPC1AdapterConfig(
            base_url=config.epc1_base_url,
            timeout_seconds=config.epc1_timeout_seconds,
            api_version=config.epc1_api_version,
        )
        self._adapter = EPC1IdentityAdapter(adapter_config)
        self._wal = wal
        self._actor_cache: Dict[str, ActorBlock] = {}

    async def _resolve_actor_async(self, context: ActorContext) -> ActorBlock:
        """Async actor resolution via EPC-1 (used by WAL drain)."""
        context_copy = copy.deepcopy(context)
        return await self._adapter.resolve_actor(context_copy)

    def resolve_actor(self, context: ActorContext, use_cache: bool = True) -> ActorBlock:
        """Returns a cached actor block or queues a refresh."""
        context_copy = copy.deepcopy(context)
        self._validate_context(context_copy)

        cache_key = self._cache_key(context_copy)
        if cache_key in self._actor_cache:
            cached = self._actor_cache[cache_key]
            if cached.session_id != context_copy.session_id:
                self._queue_epc1_call(context_copy, "update_session")
            return cached

        if use_cache:
            self._queue_epc1_call(context_copy, "resolve_actor")
            raise ActorUnavailableError("Actor not cached; EPC-1 refresh queued")

        return self._resolve_online(context_copy)

    def _resolve_online(self, context: ActorContext) -> ActorBlock:
        """Performs an EPC-1 call outside of the request path."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            actor = loop.run_until_complete(self._resolve_actor_async(context))
        except ActorUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ActorUnavailableError(f"Identity resolution failed: {exc}") from exc
        self._actor_cache[self._cache_key(context)] = actor
        return actor

    def _queue_epc1_call(self, context: ActorContext, action: str) -> None:
        if not self._wal:
            return
        self._wal.append(
            {
                "type": "epc1_call",
                "action": action,
                "context": {
                    "tenant_id": context.tenant_id,
                    "user_id": context.user_id,
                    "device_id": context.device_id,
                    "session_id": context.session_id,
                    "actor_type": context.actor_type,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            entry_type="epc1_call",
        )

    def process_wal_entry(self, payload: dict) -> None:
        """Handles queued EPC-1 calls when the WAL drain runs."""
        context_data = payload.get("context") or {}
        try:
            context = ActorContext(
                tenant_id=context_data["tenant_id"],
                device_id=context_data["device_id"],
                session_id=context_data["session_id"],
                user_id=context_data["user_id"],
                actor_type=context_data.get("actor_type", "unknown"),
                runtime_clock=datetime.now(timezone.utc),
                extras={},
            )
        except KeyError:
            return

        try:
            self._resolve_online(context)
        except Exception as exc:  # noqa: BLE001
            if self._config.fallback_enabled:
                return
            raise ActorUnavailableError(f"EPC-1 refresh failed: {exc}") from exc

    def _cache_key(self, context: ActorContext) -> str:
        return f"{context.tenant_id}:{context.user_id}:{context.device_id}"

    def _validate_context(self, context: ActorContext) -> None:
        missing: Sequence[str] = [
            field
            for field, value in {
                "tenant_id": context.tenant_id,
                "device_id": context.device_id,
                "session_id": context.session_id,
                "user_id": context.user_id,
            }.items()
            if not value
        ]
        if missing:
            raise ActorUnavailableError(f"Missing actor context fields: {missing}")

    async def health_check(self) -> bool:
        return await self._adapter.health_check()

    async def close(self) -> None:
        await self._adapter.close()

"""
MCP server registry models and persistence helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

DEFAULT_REGISTRY_FILENAME = "mcp_server_registry.json"

MCP_UNPINNED_SERVER = "MCP_UNPINNED_SERVER"
MCP_PIN_MISMATCH = "MCP_PIN_MISMATCH"

ReceiptEmitter = Callable[[dict[str, Optional[str]]], None]


def default_registry_path() -> Path:
    """Return the default registry file path under the repo config directory."""
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "config" / DEFAULT_REGISTRY_FILENAME


def _is_non_empty(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


@dataclass(frozen=True)
class MCPServerEntry:
    """Registry entry describing a single MCP server."""

    server_id: str
    display_name: str
    endpoint: str
    enabled: bool
    pinned_version: Optional[str] = None
    pinned_digest: Optional[str] = None
    capabilities: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not _is_non_empty(self.server_id):
            errors.append("server_id is required.")
        if not _is_non_empty(self.display_name):
            errors.append("display_name is required.")
        if not _is_non_empty(self.endpoint):
            errors.append("endpoint is required.")

        if self.pinned_version is not None and not _is_non_empty(self.pinned_version):
            errors.append("pinned_version must be non-empty when provided.")
        if self.pinned_digest is not None and not _is_non_empty(self.pinned_digest):
            errors.append("pinned_digest must be non-empty when provided.")

        if self.enabled and not (
            _is_non_empty(self.pinned_version) or _is_non_empty(self.pinned_digest)
        ):
            errors.append("enabled servers must set pinned_version or pinned_digest.")

        for capability in self.capabilities:
            if not _is_non_empty(capability):
                errors.append("capabilities entries must be non-empty strings.")
                break

        return errors

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MCPServerEntry":
        server_id = data.get("server_id")
        display_name = data.get("display_name")
        endpoint = data.get("endpoint")
        enabled = data.get("enabled")

        if not isinstance(server_id, str):
            raise ValueError("server_id must be a string")
        if not isinstance(display_name, str):
            raise ValueError("display_name must be a string")
        if not isinstance(endpoint, str):
            raise ValueError("endpoint must be a string")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")

        pinned_version = data.get("pinned_version")
        pinned_digest = data.get("pinned_digest")
        if pinned_version is not None and not isinstance(pinned_version, str):
            raise ValueError("pinned_version must be a string when provided")
        if pinned_digest is not None and not isinstance(pinned_digest, str):
            raise ValueError("pinned_digest must be a string when provided")

        capabilities = data.get("capabilities") or []
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) for item in capabilities
        ):
            raise ValueError("capabilities must be a list of strings when provided")

        return cls(
            server_id=server_id,
            display_name=display_name,
            endpoint=endpoint,
            enabled=enabled,
            pinned_version=pinned_version,
            pinned_digest=pinned_digest,
            capabilities=tuple(capabilities),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "server_id": self.server_id,
            "display_name": self.display_name,
            "endpoint": self.endpoint,
            "enabled": self.enabled,
        }
        if self.pinned_version is not None:
            payload["pinned_version"] = self.pinned_version
        if self.pinned_digest is not None:
            payload["pinned_digest"] = self.pinned_digest
        if self.capabilities:
            payload["capabilities"] = list(self.capabilities)
        return payload


@dataclass(frozen=True)
class MCPServerRegistry:
    """Registry container for MCP servers."""

    servers: tuple[MCPServerEntry, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        for index, entry in enumerate(self.servers):
            prefix = entry.server_id or f"index {index}"
            for message in entry.validate():
                errors.append(f"{prefix}: {message}")
        return errors

    def get(self, server_id: str) -> Optional[MCPServerEntry]:
        for entry in self.servers:
            if entry.server_id == server_id:
                return entry
        return None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MCPServerRegistry":
        raw_servers = data.get("servers", [])
        if not isinstance(raw_servers, list):
            raise ValueError("servers must be a list")

        servers = [MCPServerEntry.from_dict(item) for item in raw_servers]
        return cls(servers=tuple(servers))

    def to_dict(self) -> dict[str, Any]:
        return {"servers": [entry.to_dict() for entry in self.servers]}


def load_registry(path: Optional[Path | str] = None) -> MCPServerRegistry:
    """Load an MCP server registry from disk."""
    registry_path = Path(path) if path is not None else default_registry_path()
    with open(registry_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError("Registry data must be a JSON object")
    if "servers" in data:
        registry_data = data
    else:
        registry_section = data.get("mcp_registry")
        if isinstance(registry_section, Mapping):
            registry_data = registry_section
        else:
            raise ValueError("Registry data must include servers or mcp_registry")
    return MCPServerRegistry.from_dict(registry_data)


def save_registry(registry: MCPServerRegistry, path: Optional[Path | str] = None) -> None:
    """Persist an MCP server registry to disk."""
    registry_path = Path(path) if path is not None else default_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as handle:
        json.dump(registry.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")


@dataclass(frozen=True)
class MCPServerIdentity:
    """Optional server identity information for pin verification."""

    version: Optional[str] = None
    digest: Optional[str] = None


@dataclass(frozen=True)
class MCPVerificationError:
    """Structured MCP verification error."""

    reason_code: str
    message: str
    server_id: str
    pinned_version: Optional[str]
    pinned_digest: Optional[str]

    def receipt_metadata(self) -> dict[str, Optional[str]]:
        policy_ref = self.pinned_version or self.pinned_digest or self.server_id
        return {
            "event_type": "mcp_verification",
            "decision": "deny",
            "server_id": self.server_id,
            "pinned_version": self.pinned_version,
            "pinned_digest": self.pinned_digest,
            "reason_code": self.reason_code,
            "policy_ref": policy_ref,
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        }


@dataclass(frozen=True)
class MCPVerificationResult:
    """Result of MCP server verification."""

    allowed: bool
    error: Optional[MCPVerificationError] = None


@dataclass(frozen=True)
class MCPClientHandle:
    """Approved MCP server connection descriptor (no network calls)."""

    server_id: str
    display_name: str
    endpoint: str
    pinned_version: Optional[str]
    pinned_digest: Optional[str]
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class MCPConnectionResult:
    """Result of a connection attempt through the MCP factory."""

    handle: Optional[MCPClientHandle]
    error: Optional[MCPVerificationError]


class MCPVerifier:
    """Verifier that enforces pinning and identity checks for MCP servers."""

    def __init__(self, receipt_emitter: Optional[ReceiptEmitter] = None) -> None:
        self._receipt_emitter = receipt_emitter

    def verify(
        self,
        entry: MCPServerEntry,
        identity: Optional[MCPServerIdentity] = None,
    ) -> MCPVerificationResult:
        if not entry.enabled:
            return self._deny(
                entry,
                MCP_UNPINNED_SERVER,
                "Server is disabled.",
            )

        if not (entry.pinned_version or entry.pinned_digest):
            return self._deny(
                entry,
                MCP_UNPINNED_SERVER,
                "Pinned version or digest is required for enabled servers.",
            )

        if identity is not None:
            if entry.pinned_version and identity.version:
                if identity.version != entry.pinned_version:
                    return self._deny(
                        entry,
                        MCP_PIN_MISMATCH,
                        "Pinned version does not match server identity.",
                    )
            if entry.pinned_digest and identity.digest:
                if identity.digest != entry.pinned_digest:
                    return self._deny(
                        entry,
                        MCP_PIN_MISMATCH,
                        "Pinned digest does not match server identity.",
                    )

        return MCPVerificationResult(allowed=True)

    def emit_receipt(self, error: MCPVerificationError) -> None:
        if self._receipt_emitter is not None:
            self._receipt_emitter(error.receipt_metadata())

    def _deny(
        self,
        entry: MCPServerEntry,
        reason_code: str,
        message: str,
    ) -> MCPVerificationResult:
        error = MCPVerificationError(
            reason_code=reason_code,
            message=message,
            server_id=entry.server_id,
            pinned_version=entry.pinned_version,
            pinned_digest=entry.pinned_digest,
        )
        self.emit_receipt(error)
        return MCPVerificationResult(allowed=False, error=error)


class MCPClientFactory:
    """Factory that enforces MCP verification at a single choke-point."""

    def __init__(
        self,
        registry: MCPServerRegistry,
        verifier: Optional[MCPVerifier] = None,
    ) -> None:
        self._registry = registry
        self._verifier = verifier or MCPVerifier()

    def create_client(
        self,
        server_id: str,
        identity: Optional[MCPServerIdentity] = None,
    ) -> MCPConnectionResult:
        entry = self._registry.get(server_id)
        if entry is None:
            error = MCPVerificationError(
                reason_code=MCP_UNPINNED_SERVER,
                message="Server not registered.",
                server_id=server_id,
                pinned_version=None,
                pinned_digest=None,
            )
            self._verifier.emit_receipt(error)
            return MCPConnectionResult(handle=None, error=error)

        verification = self._verifier.verify(entry, identity)
        if not verification.allowed:
            return MCPConnectionResult(handle=None, error=verification.error)

        handle = MCPClientHandle(
            server_id=entry.server_id,
            display_name=entry.display_name,
            endpoint=entry.endpoint,
            pinned_version=entry.pinned_version,
            pinned_digest=entry.pinned_digest,
            capabilities=entry.capabilities,
        )
        return MCPConnectionResult(handle=handle, error=None)


__all__ = [
    "DEFAULT_REGISTRY_FILENAME",
    "MCP_PIN_MISMATCH",
    "MCP_UNPINNED_SERVER",
    "MCPClientFactory",
    "MCPClientHandle",
    "MCPConnectionResult",
    "MCPServerIdentity",
    "MCPServerEntry",
    "MCPServerRegistry",
    "MCPVerificationError",
    "MCPVerificationResult",
    "MCPVerifier",
    "default_registry_path",
    "load_registry",
    "save_registry",
]

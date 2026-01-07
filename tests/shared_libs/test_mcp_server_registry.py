from __future__ import annotations
import pytest

from src.shared_libs.mcp_server_registry import (
    MCPServerEntry,
    MCPServerRegistry,
    load_registry,
    save_registry,
)


@pytest.mark.unit
def test_registry_save_and_load_round_trip(tmp_path) -> None:
    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.local",
                display_name="Local MCP",
                endpoint="http://localhost:9000",
                enabled=True,
                pinned_version="1.0.0",
                capabilities=("tools", "resources"),
            ),
        )
    )
    path = tmp_path / "mcp_registry.json"

    save_registry(registry, path)
    loaded = load_registry(path)

    assert loaded == registry


@pytest.mark.unit
def test_registry_parses_from_dict() -> None:
    registry = MCPServerRegistry.from_dict(
        {
            "servers": [
                {
                    "server_id": "mcp.example",
                    "display_name": "Example MCP",
                    "endpoint": "https://mcp.example/api",
                    "enabled": False,
                    "capabilities": ["tools"],
                }
            ]
        }
    )

    assert registry.servers[0].server_id == "mcp.example"
    assert registry.servers[0].enabled is False
    assert registry.servers[0].capabilities == ("tools",)


@pytest.mark.unit
def test_enabled_server_requires_pin() -> None:
    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.unpinned",
                display_name="Unpinned MCP",
                endpoint="https://mcp.unpinned",
                enabled=True,
            ),
        )
    )

    errors = registry.validate()

    assert any("pinned_version or pinned_digest" in error for error in errors)

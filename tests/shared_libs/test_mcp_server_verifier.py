from __future__ import annotations

from src.shared_libs.mcp_server_registry import (
    MCPClientFactory,
    MCP_PIN_MISMATCH,
    MCPServerEntry,
    MCPServerIdentity,
    MCPServerRegistry,
    MCP_UNPINNED_SERVER,
    MCPVerifier,
)
from tests.shared_harness import assert_enforcement_receipt_fields


def test_unpinned_enabled_server_is_blocked_and_receipted() -> None:
    receipts: list[dict[str, object]] = []
    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.unpinned",
                display_name="Unpinned MCP",
                endpoint="http://localhost:9000",
                enabled=True,
            ),
        )
    )
    verifier = MCPVerifier(receipt_emitter=receipts.append)
    factory = MCPClientFactory(registry, verifier)

    result = factory.create_client("mcp.unpinned")

    assert result.handle is None
    assert result.error is not None
    assert result.error.reason_code == MCP_UNPINNED_SERVER
    assert receipts
    assert receipts[0]["server_id"] == "mcp.unpinned"
    assert receipts[0]["reason_code"] == MCP_UNPINNED_SERVER
    assert_enforcement_receipt_fields(receipts[0])


def test_pinned_server_passes_identity_match() -> None:
    receipts: list[dict[str, object]] = []
    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.pinned",
                display_name="Pinned MCP",
                endpoint="https://mcp.example/api",
                enabled=True,
                pinned_version="1.0.0",
            ),
        )
    )
    verifier = MCPVerifier(receipt_emitter=receipts.append)
    factory = MCPClientFactory(registry, verifier)

    result = factory.create_client(
        "mcp.pinned",
        identity=MCPServerIdentity(version="1.0.0"),
    )

    assert result.error is None
    assert result.handle is not None
    assert result.handle.server_id == "mcp.pinned"
    assert receipts == []


def test_pin_mismatch_is_blocked_and_receipted() -> None:
    receipts: list[dict[str, object]] = []
    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.mismatch",
                display_name="Mismatch MCP",
                endpoint="https://mcp.example/api",
                enabled=True,
                pinned_version="1.0.0",
            ),
        )
    )
    verifier = MCPVerifier(receipt_emitter=receipts.append)
    factory = MCPClientFactory(registry, verifier)

    result = factory.create_client(
        "mcp.mismatch",
        identity=MCPServerIdentity(version="2.0.0"),
    )

    assert result.handle is None
    assert result.error is not None
    assert result.error.reason_code == MCP_PIN_MISMATCH
    assert receipts
    assert receipts[0]["server_id"] == "mcp.mismatch"
    assert receipts[0]["reason_code"] == MCP_PIN_MISMATCH
    assert_enforcement_receipt_fields(receipts[0])

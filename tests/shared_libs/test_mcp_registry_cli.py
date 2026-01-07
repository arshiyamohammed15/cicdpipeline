from __future__ import annotations
import pytest

import io
import json

from shared_libs.mcp_server_registry import load_registry, save_registry, MCPServerEntry, MCPServerRegistry
import tools.mcp_registry_cli as cli


def _read_receipts(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.unit
def test_mcp_add_writes_registry_and_receipt(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    receipt_path = tmp_path / "receipts.jsonl"

    out = io.StringIO()
    err = io.StringIO()
    code = cli.handle_mcp_add(
        registry_path=registry_path,
        receipt_path=receipt_path,
        server_id="mcp.local",
        endpoint="http://localhost:9000",
        pinned_version="1.0.0",
        pinned_digest=None,
        display_name=None,
        enabled=True,
        capabilities=["tools"],
        output=out,
        error_output=err,
    )

    assert code == 0
    registry = load_registry(registry_path)
    entry = registry.get("mcp.local")
    assert entry is not None
    assert entry.enabled is True
    assert entry.pinned_version == "1.0.0"

    receipts = _read_receipts(receipt_path)
    assert receipts[0]["operation"] == "mcp.add"
    assert receipts[0]["server_id"] == "mcp.local"
    assert receipts[0]["pinned_version"] == "1.0.0"
    assert receipts[0]["outcome"] == "success"


@pytest.mark.unit
def test_mcp_add_unpinned_enabled_fails_and_receipted(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    receipt_path = tmp_path / "receipts.jsonl"

    out = io.StringIO()
    err = io.StringIO()
    code = cli.handle_mcp_add(
        registry_path=registry_path,
        receipt_path=receipt_path,
        server_id="mcp.unpinned",
        endpoint="http://localhost:9001",
        pinned_version=None,
        pinned_digest=None,
        display_name=None,
        enabled=True,
        capabilities=[],
        output=out,
        error_output=err,
    )

    assert code == 1
    receipts = _read_receipts(receipt_path)
    assert receipts[0]["operation"] == "mcp.add"
    assert receipts[0]["server_id"] == "mcp.unpinned"
    assert receipts[0]["outcome"] == "failure"


@pytest.mark.unit
def test_mcp_disable_updates_registry_and_receipt(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    receipt_path = tmp_path / "receipts.jsonl"

    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.disable",
                display_name="Disable MCP",
                endpoint="http://localhost:9002",
                enabled=True,
                pinned_version="1.0.0",
            ),
        )
    )
    save_registry(registry, registry_path)

    out = io.StringIO()
    err = io.StringIO()
    code = cli.handle_mcp_disable(
        registry_path=registry_path,
        receipt_path=receipt_path,
        server_id="mcp.disable",
        output=out,
        error_output=err,
    )

    assert code == 0
    updated = load_registry(registry_path).get("mcp.disable")
    assert updated is not None
    assert updated.enabled is False

    receipts = _read_receipts(receipt_path)
    assert receipts[0]["operation"] == "mcp.disable"
    assert receipts[0]["server_id"] == "mcp.disable"
    assert receipts[0]["outcome"] == "success"


@pytest.mark.unit
def test_mcp_list_emits_receipt(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    receipt_path = tmp_path / "receipts.jsonl"

    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.listed",
                display_name="Listed MCP",
                endpoint="http://localhost:9003",
                enabled=False,
                pinned_version=None,
            ),
        )
    )
    save_registry(registry, registry_path)

    out = io.StringIO()
    code = cli.handle_mcp_list(
        registry_path=registry_path,
        receipt_path=receipt_path,
        output=out,
    )

    assert code == 0
    receipts = _read_receipts(receipt_path)
    assert receipts[0]["operation"] == "mcp.list"
    assert receipts[0]["server_id"] == "*"

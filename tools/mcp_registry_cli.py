#!/usr/bin/env python3
"""
CLI for MCP server registry management.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import IO, Iterable, Optional

# Ensure project root is importable when running as a script.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from shared_libs.mcp_server_registry import (
    MCPServerEntry,
    MCPServerRegistry,
    default_registry_path,
    load_registry,
    save_registry,
)


DEFAULT_RECEIPT_FILENAME = "mcp_registry_receipts.jsonl"


def default_receipt_path() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "artifacts" / DEFAULT_RECEIPT_FILENAME


def _write_receipt(
    *,
    operation: str,
    server_id: str,
    pinned_version: Optional[str],
    pinned_digest: Optional[str],
    outcome: str,
    receipt_path: Path,
) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "operation": operation,
        "server_id": server_id,
        "pinned_version": pinned_version,
        "pinned_digest": pinned_digest,
        "outcome": outcome,
    }
    with receipt_path.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")


def _load_or_empty(path: Path) -> MCPServerRegistry:
    if path.exists():
        return load_registry(path)
    return MCPServerRegistry()


def _sorted_entries(entries: Iterable[MCPServerEntry]) -> list[MCPServerEntry]:
    return sorted(entries, key=lambda entry: entry.server_id)


def handle_mcp_list(
    *,
    registry_path: Path,
    receipt_path: Path,
    output: IO[str],
) -> int:
    registry = _load_or_empty(registry_path)
    servers = _sorted_entries(registry.servers)

    payload = {"servers": [entry.to_dict() for entry in servers]}
    output.write(json.dumps(payload, indent=2, sort_keys=True))
    output.write("\n")

    _write_receipt(
        operation="mcp.list",
        server_id="*",
        pinned_version=None,
        pinned_digest=None,
        outcome="success",
        receipt_path=receipt_path,
    )
    return 0


def handle_mcp_add(
    *,
    registry_path: Path,
    receipt_path: Path,
    server_id: str,
    endpoint: str,
    pinned_version: Optional[str],
    pinned_digest: Optional[str],
    display_name: Optional[str],
    enabled: bool,
    capabilities: Iterable[str],
    output: IO[str],
    error_output: IO[str],
) -> int:
    if enabled and not (pinned_version or pinned_digest):
        error_output.write("Pinned version or digest required for enabled servers.\n")
        _write_receipt(
            operation="mcp.add",
            server_id=server_id,
            pinned_version=pinned_version,
            pinned_digest=pinned_digest,
            outcome="failure",
            receipt_path=receipt_path,
        )
        return 1

    registry = _load_or_empty(registry_path)
    if registry.get(server_id) is not None:
        error_output.write(f"Server already registered: {server_id}\n")
        _write_receipt(
            operation="mcp.add",
            server_id=server_id,
            pinned_version=pinned_version,
            pinned_digest=pinned_digest,
            outcome="failure",
            receipt_path=receipt_path,
        )
        return 1

    entry = MCPServerEntry(
        server_id=server_id,
        display_name=display_name or server_id,
        endpoint=endpoint,
        enabled=enabled,
        pinned_version=pinned_version,
        pinned_digest=pinned_digest,
        capabilities=tuple(capabilities),
    )

    errors = entry.validate()
    if errors:
        error_output.write("\n".join(errors) + "\n")
        _write_receipt(
            operation="mcp.add",
            server_id=server_id,
            pinned_version=pinned_version,
            pinned_digest=pinned_digest,
            outcome="failure",
            receipt_path=receipt_path,
        )
        return 1

    servers = list(registry.servers)
    servers.append(entry)
    save_registry(MCPServerRegistry(servers=tuple(servers)), registry_path)

    _write_receipt(
        operation="mcp.add",
        server_id=server_id,
        pinned_version=pinned_version,
        pinned_digest=pinned_digest,
        outcome="success",
        receipt_path=receipt_path,
    )
    output.write(f"Added MCP server '{server_id}'.\n")
    return 0


def handle_mcp_disable(
    *,
    registry_path: Path,
    receipt_path: Path,
    server_id: str,
    output: IO[str],
    error_output: IO[str],
) -> int:
    registry = _load_or_empty(registry_path)
    entry = registry.get(server_id)
    if entry is None:
        error_output.write(f"Server not found: {server_id}\n")
        _write_receipt(
            operation="mcp.disable",
            server_id=server_id,
            pinned_version=None,
            pinned_digest=None,
            outcome="failure",
            receipt_path=receipt_path,
        )
        return 1

    updated_servers = []
    for current in registry.servers:
        if current.server_id == server_id:
            updated_servers.append(
                MCPServerEntry(
                    server_id=current.server_id,
                    display_name=current.display_name,
                    endpoint=current.endpoint,
                    enabled=False,
                    pinned_version=current.pinned_version,
                    pinned_digest=current.pinned_digest,
                    capabilities=current.capabilities,
                )
            )
        else:
            updated_servers.append(current)

    save_registry(MCPServerRegistry(servers=tuple(updated_servers)), registry_path)
    _write_receipt(
        operation="mcp.disable",
        server_id=server_id,
        pinned_version=entry.pinned_version,
        pinned_digest=entry.pinned_digest,
        outcome="success",
        receipt_path=receipt_path,
    )
    output.write(f"Disabled MCP server '{server_id}'.\n")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage the MCP server registry.",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mcp_parser = subparsers.add_parser("mcp", help="MCP registry commands")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)

    list_parser = mcp_subparsers.add_parser("list", help="List MCP servers")
    list_parser.add_argument(
        "--registry",
        type=Path,
        default=default_registry_path(),
        help="Path to MCP registry JSON file",
    )
    list_parser.add_argument(
        "--receipt-path",
        type=Path,
        default=default_receipt_path(),
        help="Path to append receipt JSONL entries",
    )

    add_parser = mcp_subparsers.add_parser("add", help="Add MCP server")
    add_parser.add_argument("--server-id", required=True, help="Stable MCP server identifier")
    add_parser.add_argument("--endpoint", required=True, help="Server endpoint URL or transport")
    add_parser.add_argument("--display-name", help="Human-readable display name")
    add_parser.add_argument("--pinned-version", help="Pinned server version")
    add_parser.add_argument("--pinned-digest", help="Pinned server digest")
    add_parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability identifier (repeatable)",
    )
    add_parser.add_argument(
        "--disabled",
        action="store_true",
        help="Register the server as disabled",
    )
    add_parser.add_argument(
        "--registry",
        type=Path,
        default=default_registry_path(),
        help="Path to MCP registry JSON file",
    )
    add_parser.add_argument(
        "--receipt-path",
        type=Path,
        default=default_receipt_path(),
        help="Path to append receipt JSONL entries",
    )

    disable_parser = mcp_subparsers.add_parser("disable", help="Disable MCP server")
    disable_parser.add_argument("--server-id", required=True, help="Stable MCP server identifier")
    disable_parser.add_argument(
        "--registry",
        type=Path,
        default=default_registry_path(),
        help="Path to MCP registry JSON file",
    )
    disable_parser.add_argument(
        "--receipt-path",
        type=Path,
        default=default_receipt_path(),
        help="Path to append receipt JSONL entries",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "mcp":
        parser.error("Unsupported command")
        return 2

    if args.mcp_command == "list":
        return handle_mcp_list(
            registry_path=args.registry,
            receipt_path=args.receipt_path,
            output=sys.stdout,
        )
    if args.mcp_command == "add":
        return handle_mcp_add(
            registry_path=args.registry,
            receipt_path=args.receipt_path,
            server_id=args.server_id,
            endpoint=args.endpoint,
            pinned_version=args.pinned_version,
            pinned_digest=args.pinned_digest,
            display_name=args.display_name,
            enabled=not args.disabled,
            capabilities=args.capability,
            output=sys.stdout,
            error_output=sys.stderr,
        )
    if args.mcp_command == "disable":
        return handle_mcp_disable(
            registry_path=args.registry,
            receipt_path=args.receipt_path,
            server_id=args.server_id,
            output=sys.stdout,
            error_output=sys.stderr,
        )

    parser.error("Unsupported MCP command")
    return 2


if __name__ == "__main__":
    sys.exit(main())

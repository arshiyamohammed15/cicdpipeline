"""
Python bridge for Edge Agent (TypeScript) to call CCCS runtime.

This module provides a Python HTTP server that Edge Agent can call via HTTP/gRPC,
or a JSON-RPC interface that can be used via subprocess/stdin-stdout.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..runtime import CCCSRuntime, CCCSConfig
from ..types import ActorContext
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CCCSEdgeAgentBridge:
    """
    Bridge interface for Edge Agent to use CCCS runtime.
    
    Provides JSON-RPC style interface that can be called via:
    - HTTP/gRPC (when running as a service)
    - Subprocess/stdin-stdout (when embedded)
    - Python FFI (when using PyNode or similar)
    """

    def __init__(self, runtime: CCCSRuntime):
        self._runtime = runtime

    def execute_flow_json(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute CCCS flow from JSON request.
        
        Request format:
        {
            "module_id": "m01",
            "inputs": {...},
            "action_id": "action-1",
            "cost": 1.0,
            "config_key": "config-key",
            "payload": {...},
            "redaction_hint": "hint",
            "actor_context": {
                "tenant_id": "t1",
                "device_id": "d1",
                "session_id": "s1",
                "user_id": "u1",
                "actor_type": "machine",
                "runtime_clock": "2025-01-27T00:00:00Z"
            }
        }
        
        Returns:
            {
                "actor": {...},
                "config": {...},
                "policy": {...},
                "budget": {...},
                "receipt": {...},
                "redaction": {...}
            }
        """
        try:
            # Parse actor context
            actor_ctx_data = request["actor_context"]
            actor_context = ActorContext(
                tenant_id=actor_ctx_data["tenant_id"],
                device_id=actor_ctx_data["device_id"],
                session_id=actor_ctx_data["session_id"],
                user_id=actor_ctx_data["user_id"],
                actor_type=actor_ctx_data["actor_type"],
                runtime_clock=datetime.fromisoformat(actor_ctx_data["runtime_clock"].replace("Z", "+00:00")),
                extras=actor_ctx_data.get("extras", {}),
            )

            # Execute flow
            result = self._runtime.execute_flow(
                module_id=request["module_id"],
                inputs=request["inputs"],
                action_id=request["action_id"],
                cost=request["cost"],
                config_key=request["config_key"],
                payload=request["payload"],
                redaction_hint=request["redaction_hint"],
                actor_context=actor_context,
            )

            # Convert result to JSON-serializable format
            return {
                "actor": {
                    "actor_id": result["actor"].actor_id,
                    "actor_type": result["actor"].actor_type,
                    "session_id": result["actor"].session_id,
                    "provenance_signature": result["actor"].provenance_signature,
                    "salt_version": result["actor"].salt_version,
                    "monotonic_counter": result["actor"].monotonic_counter,
                },
                "config": {
                    "value": result["config"].value,
                    "source_layers": list(result["config"].source_layers),
                    "config_snapshot_hash": result["config"].config_snapshot_hash,
                },
                "policy": {
                    "decision": result["policy"].decision,
                    "rationale": result["policy"].rationale,
                    "policy_version_ids": list(result["policy"].policy_version_ids),
                    "policy_snapshot_hash": result["policy"].policy_snapshot_hash,
                },
                "budget": {
                    "allowed": result["budget"].allowed,
                    "reason": result["budget"].reason,
                    "remaining": result["budget"].remaining,
                },
                "receipt": {
                    "receipt_id": result["receipt"].receipt_id,
                    "courier_batch_id": result["receipt"].courier_batch_id,
                    "fsync_offset": result["receipt"].fsync_offset,
                },
                "redaction": result["redaction"],
            }
        except Exception as e:
            logger.error(f"CCCS flow execution failed: {e}", exc_info=True)
            error_dict = self._runtime.normalize_error(e)
            return {"error": error_dict}

    def normalize_error_json(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize error from JSON data."""
        # Create a simple exception from error data
        error = Exception(error_data.get("message", "Unknown error"))
        return self._runtime.normalize_error(error)

    def drain_courier_json(self) -> Dict[str, Any]:
        """Drain courier and return sequence numbers."""
        sequences = self._runtime.drain_courier()
        return {"sequences": sequences}


def create_edge_agent_bridge(config: CCCSConfig, wal_path: Optional[Path] = None) -> CCCSEdgeAgentBridge:
    """Factory function to create Edge Agent bridge with runtime."""
    runtime = CCCSRuntime(config, wal_path=wal_path)
    return CCCSEdgeAgentBridge(runtime)


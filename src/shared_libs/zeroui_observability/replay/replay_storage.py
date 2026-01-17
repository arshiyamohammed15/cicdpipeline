"""
Replay Bundle Storage for ZeroUI Observability Layer.

Stores replay bundles in Evidence Plane per folder-business-rules.md.
Integrates with PM-7 (ERIS) for evidence storage.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .replay_bundle_builder import ReplayBundle

logger = logging.getLogger(__name__)


class ReplayStorage:
    """
    Stores replay bundles in Evidence Plane.

    Per folder-business-rules.md:
    - Tenant Plane: tenant/{tenant-id}/{region}/evidence/data/replay-bundles/dt={yyyy}-{mm}-{dd}/
    - Format: JSONL files (one bundle per line)
    - Append-only, WORM semantics
    """

    def __init__(
        self,
        zu_root: Optional[str] = None,
        pm7_client: Optional[Any] = None,  # PM-7 ERIS client
    ):
        """
        Initialize replay storage.

        Args:
            zu_root: ZU_ROOT path (defaults to env var)
            pm7_client: PM-7 ERIS client for evidence storage
        """
        self._zu_root = Path(zu_root or os.getenv("ZU_ROOT", ""))
        self._pm7_client = pm7_client

        if not self._zu_root:
            logger.warning("ZU_ROOT not set, replay storage may not work correctly")

    def store(
        self,
        bundle: ReplayBundle,
        bundle_payload: Dict[str, Any],
        tenant_id: str,
        region: Optional[str] = None,
    ) -> str:
        """
        Store replay bundle in Evidence Plane.

        Args:
            bundle: ReplayBundle instance
            bundle_payload: Bundle payload dictionary
            tenant_id: Tenant ID
            region: Optional region identifier

        Returns:
            Storage path where bundle was stored

        Raises:
            ValueError: If tenant_id is missing or storage fails
        """
        if not tenant_id:
            raise ValueError("tenant_id is required")

        # Build storage path per folder-business-rules.md
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        region_part = f"{region}/" if region else ""
        storage_path = (
            self._zu_root
            / "tenant"
            / tenant_id
            / region_part
            / "evidence"
            / "data"
            / "replay-bundles"
            / f"dt={date_str}"
            / f"{bundle.replay_id}.jsonl"
        )

        # Create parent directories
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Build JSONL entry
        jsonl_entry = {
            "replay_id": bundle.replay_id,
            "trigger_event_id": bundle.trigger_event_id,
            "included_event_ids": bundle.included_event_ids,
            "checksum": bundle.checksum,
            "storage_ref": str(storage_path),
            "trace_id": bundle.trace_id,
            "run_id": bundle.run_id,
            "created_at": bundle.created_at.isoformat() if bundle.created_at else None,
            "payload": bundle_payload,
        }

        # Write to JSONL file (append-only)
        try:
            with open(storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(jsonl_entry, sort_keys=True) + "\n")
            logger.info(f"Stored replay bundle {bundle.replay_id} at {storage_path}")
        except IOError as e:
            logger.error(f"Failed to store replay bundle {bundle.replay_id}: {e}")
            raise

        # If PM-7 client available, also store via ERIS API
        if self._pm7_client:
            try:
                self._store_via_pm7(bundle, bundle_payload, tenant_id)
            except Exception as e:
                logger.warning(f"Failed to store replay bundle via PM-7: {e}")
                # Continue - file storage succeeded

        return str(storage_path)

    def _store_via_pm7(
        self,
        bundle: ReplayBundle,
        bundle_payload: Dict[str, Any],
        tenant_id: str,
    ) -> None:
        """
        Store replay bundle via PM-7 ERIS API.

        Args:
            bundle: ReplayBundle instance
            bundle_payload: Bundle payload dictionary
            tenant_id: Tenant ID
        """
        if not self._pm7_client:
            return

        # Build receipt-like structure for PM-7
        receipt_data = {
            "receipt_id": bundle.replay_id,
            "gate_id": "replay_bundle_builder",
            "schema_version": "1.0.0",
            "policy_version_ids": ["POL-OBS-15"],
            "snapshot_hash": bundle.checksum,
            "timestamp_utc": bundle.created_at.isoformat() if bundle.created_at else datetime.now(timezone.utc).isoformat(),
            "timestamp_monotonic_ms": int(bundle.created_at.timestamp() * 1000) if bundle.created_at else int(datetime.now(timezone.utc).timestamp() * 1000),
            "evaluation_point": "post_incident",
            "inputs": {
                "trace_id": bundle.trace_id,
                "run_id": bundle.run_id,
                "trigger_event_id": bundle.trigger_event_id,
            },
            "decision_status": "pass",
            "decision_rationale": f"Replay bundle created for trace {bundle.trace_id}",
            "result": bundle_payload,
            "actor_repo_id": tenant_id,
            "actor_type": "system",
            "evidence_handles": {
                "replay_bundle": bundle.replay_id,
                "storage_ref": bundle.storage_ref,
            },
            "degraded": False,
        }

        # Call PM-7 API (if available)
        try:
            # PM-7 API would be: POST /v1/evidence/receipts
            # For now, log that we would call it
            logger.debug(f"Would store replay bundle via PM-7: {bundle.replay_id}")
        except Exception as e:
            logger.error(f"PM-7 storage failed: {e}")
            raise

    def retrieve(self, replay_id: str, tenant_id: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve replay bundle by replay_id.

        Args:
            replay_id: Replay bundle ID
            tenant_id: Tenant ID
            region: Optional region identifier

        Returns:
            Bundle dictionary or None if not found
        """
        # Search for bundle in storage
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        region_part = f"{region}/" if region else ""
        storage_dir = (
            self._zu_root
            / "tenant"
            / tenant_id
            / region_part
            / "evidence"
            / "data"
            / "replay-bundles"
            / f"dt={date_str}"
        )

        bundle_file = storage_dir / f"{replay_id}.jsonl"

        if not bundle_file.exists():
            # Try to find in other date directories
            replay_bundles_dir = storage_dir.parent
            if replay_bundles_dir.exists():
                for dt_dir in replay_bundles_dir.iterdir():
                    if dt_dir.is_dir() and dt_dir.name.startswith("dt="):
                        candidate_file = dt_dir / f"{replay_id}.jsonl"
                        if candidate_file.exists():
                            bundle_file = candidate_file
                            break

        if not bundle_file.exists():
            logger.warning(f"Replay bundle not found: {replay_id}")
            return None

        try:
            # Read last line (append-only, so last line is latest)
            with open(bundle_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        return json.loads(last_line)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve replay bundle {replay_id}: {e}")
            return None

        return None

"""Receipt generation, signing, and offline courier batching."""

from __future__ import annotations

import asyncio
import copy
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..adapters.epc11_adapter import EPC11AdapterConfig, EPC11SigningAdapter
from ..adapters.pm7_adapter import PM7AdapterConfig, PM7ReceiptAdapter
from ..exceptions import ReceiptSchemaError
from ..types import JSONDict, ReceiptRecord, TraceContext
from .wal import WALQueue


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ReceiptConfig:
    gate_id: str
    storage_path: Path
    epc11_base_url: str
    epc11_key_id: str
    epc11_timeout_seconds: float = 5.0
    epc11_api_version: str = "v1"
    pm7_base_url: str = ""
    pm7_timeout_seconds: float = 5.0
    pm7_api_version: str = "v1"


Hook = Callable[[Dict[str, Any]], None]


class OfflineCourier:
    """Batches receipts for asynchronous delivery with monotonic ids."""

    def __init__(self, wal: WALQueue):
        self._wal = wal

    def enqueue(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._wal.append(
            {"type": "receipt", "payload": receipt, "batch_id": str(uuid.uuid4())}
        )
        return {"courier_batch_id": entry.payload["batch_id"], "sequence": entry.sequence}

    def drain(
        self, 
        sink: Callable[[Dict[str, Any]], None], 
        receipt_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[int]:
        """Drain WAL entries to sink with optional receipt emitter for dead_letter receipts."""
        drained = self._wal.drain(
            lambda payload: sink(payload["payload"]),
            receipt_emitter=receipt_emitter
        )
        return [entry.sequence for entry in drained]


class ReceiptService:
    """Composes canonical receipts and writes them to a WAL-backed store."""

    _ALLOWED_DECISIONS = {"pass", "warn", "soft_block", "hard_block"}

    REQUIRED_FIELDS = {
        "receipt_id",
        "gate_id",
        "policy_version_ids",
        "snapshot_hash",
        "timestamp_utc",
        "timestamp_monotonic_ms",
        "inputs",
        "decision",
        "result",
        "actor",
        "degraded",
        "signature",
    }

    def __init__(
        self,
        config: ReceiptConfig,
        courier: OfflineCourier,
        time_fn: Callable[[], datetime] = _utc_now,
    ):
        self._config = config
        self._courier = courier
        self._time_fn = time_fn
        self._before_sign: list[Hook] = []
        self._before_flush: list[Hook] = []
        config.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._fsync_offset = 0
        epc11_config = EPC11AdapterConfig(
            base_url=config.epc11_base_url,
            timeout_seconds=config.epc11_timeout_seconds,
            api_version=config.epc11_api_version,
            key_id=config.epc11_key_id,
        )
        self._signing_adapter = EPC11SigningAdapter(epc11_config)

        self._pm7_adapter: Optional[PM7ReceiptAdapter] = None
        if config.pm7_base_url:
            pm7_config = PM7AdapterConfig(
                base_url=config.pm7_base_url,
                timeout_seconds=config.pm7_timeout_seconds,
                api_version=config.pm7_api_version,
            )
            self._pm7_adapter = PM7ReceiptAdapter(pm7_config)

    def register_before_sign(self, hook: Hook) -> None:
        self._before_sign.append(hook)

    def register_before_flush(self, hook: Hook) -> None:
        self._before_flush.append(hook)

    async def _sign_async(self, payload: Dict[str, Any]) -> str:
        return await self._signing_adapter.sign_receipt(payload, self._config.epc11_key_id)

    def _sign(self, payload: Dict[str, Any]) -> str:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._sign_async(payload))

    def _validate(self, receipt: Dict[str, Any]) -> None:
        missing = self.REQUIRED_FIELDS - receipt.keys()
        if missing:
            raise ReceiptSchemaError(f"Missing receipt fields: {missing}")
        decision_status = receipt.get("decision", {}).get("status")
        if decision_status not in self._ALLOWED_DECISIONS:
            raise ReceiptSchemaError("Invalid decision.status")

    def write_receipt(
        self,
        inputs: JSONDict,
        result: JSONDict,
        actor: JSONDict,
        policy_metadata: JSONDict,
        trace: Optional[TraceContext],
        annotations: Optional[JSONDict] = None,
        degraded: bool = False,
    ) -> ReceiptRecord:
        receipt_id = str(uuid.uuid4())
        timestamp = self._time_fn()
        timestamp_monotonic_ms = int(timestamp.timestamp() * 1000)

        inputs_copy = copy.deepcopy(inputs)
        result_copy = copy.deepcopy(result)
        actor_copy = copy.deepcopy(actor)

        receipt = {
            "receipt_id": receipt_id,
            "gate_id": self._config.gate_id,
            "policy_version_ids": policy_metadata.get("policy_version_ids", []),
            "snapshot_hash": policy_metadata.get("policy_snapshot_hash"),
            "timestamp_utc": timestamp.isoformat(),
            "timestamp_monotonic_ms": timestamp_monotonic_ms,
            "inputs": inputs_copy,
            "decision": {
                "status": result_copy.get("status"),
                "rationale": result_copy.get("rationale"),
                "badges": copy.deepcopy(result_copy.get("badges", [])),
            },
            "result": result_copy,
            "actor": actor_copy,
            "degraded": degraded,
            "annotations": copy.deepcopy(annotations or {}),
        }
        if trace:
            receipt["trace"] = {
                "trace_id": trace.trace_id,
                "span_id": trace.span_id,
                "parent_span_id": trace.parent_span_id,
                "name": trace.name,
            }

        for hook in self._before_sign:
            hook(receipt)

        receipt["signature"] = self._sign(receipt)
        self._validate(receipt)

        for hook in self._before_flush:
            hook(receipt)

        with self._config.storage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._fsync_offset += 1

        courier_meta = self._courier.enqueue(copy.deepcopy(receipt))

        if self._pm7_adapter:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._pm7_adapter.index_receipt(copy.deepcopy(receipt)))
            except Exception:
                # Non-fatal; will retry when courier drains
                self._courier._wal.mark(courier_meta["sequence"], "pending_sync")  # noqa: SLF001

        return ReceiptRecord(
            receipt_id=receipt_id,
            courier_batch_id=courier_meta["courier_batch_id"],
            fsync_offset=self._fsync_offset,
        )

    async def health_check(self) -> bool:
        """Check EPC-11 health."""
        return await self._signing_adapter.health_check()

    async def pm7_health_check(self) -> bool:
        """Check PM-7 health when configured."""
        if not self._pm7_adapter:
            return True
        return await self._pm7_adapter.health_check()

    def has_pm7(self) -> bool:
        """Return True if PM-7 adapter configured."""
        return self._pm7_adapter is not None

    async def close(self) -> None:
        """Close adapters."""
        await self._signing_adapter.close()
        if self._pm7_adapter:
            await self._pm7_adapter.close()

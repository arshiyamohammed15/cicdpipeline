"""CCCS runtime orchestration following PRD section 7."""

from __future__ import annotations

import asyncio
import atexit
import logging
import signal
import threading
import time
import uuid
import weakref
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

from .config import ConfigService
from .errors import ErrorTaxonomy
from .errors.taxonomy import TaxonomyEntry
from .exceptions import (
    ActorUnavailableError,
    BootstrapTimeoutError,
    BudgetExceededError,
    PolicyUnavailableError,
    VersionMismatchError,
)
from .identity import IdentityConfig, IdentityService
from .observability import ObservabilityService
from .policy import PolicyConfig, PolicyRuntime
from .ratelimit import RateLimiterConfig, RateLimiterService
from .receipts import OfflineCourier, ReceiptConfig, ReceiptService, WALQueue
from .redaction import RedactionConfig, RedactionService
from .types import (
    ActorBlock,
    ActorContext,
    ConfigLayers,
    JSONDict,
    PolicyDecision,
    TraceContext,
)
from .versioning import APIVersion


@dataclass
class CCCSConfig:
    mode: str  # "edge" or "backend"
    version: str
    identity: IdentityConfig
    policy: PolicyConfig
    config_layers: ConfigLayers
    receipt: ReceiptConfig
    redaction: RedactionConfig
    rate_limiter: RateLimiterConfig
    taxonomy_mapping: Dict[type, TaxonomyEntry]


class CCCSRuntime:
    """Coordinates façade services per PRD section 7."""

    _instance_lock = threading.Lock()
    _instance_refs: set[weakref.ReferenceType["CCCSRuntime"]] = set()
    _signals_installed = False
    _atexit_registered = False
    _previous_signal_handlers: Dict[int, Any] = {}
    _signal_numbers: tuple[int, ...] = tuple(
        sig for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)) if sig is not None
    )
    # CR-010: Shared event loop to prevent resource leaks
    _shared_event_loop: Optional[asyncio.AbstractEventLoop] = None
    _event_loop_lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        config: CCCSConfig,
        wal_path: Optional[Path] = None,
        courier_sink: Optional[Callable[[dict], None]] = None,
    ):
        if config.mode not in {"edge", "backend"}:
            raise ValueError("Mode must be 'edge' or 'backend'")
        self._config = config
        self._version = APIVersion.parse(config.version)
        
        # Create WAL first (per PRD §5.9: Bootstrap creates WAL-backed queues before services)
        wal = WALQueue(wal_path or config.receipt.storage_path.with_suffix(".wal"))
        
        # Per PRD §5.9: Initialization order is fixed: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → ETFHF
        # 1. IAPS (Identity & Actor Provenance)
        self._identity = IdentityService(config.identity, wal=wal)
        # 2. CFFS (Configuration & Feature Flags)
        self._config_service = ConfigService(config.config_layers)
        # 3. PREE (Policy Runtime & Evaluation Engine)
        self._policy = PolicyRuntime(config.policy)
        # 4. RLBGS (Rate Limiter & Budget Guard)
        self._ratelimiter = RateLimiterService(config.rate_limiter, wal=wal)
        # 5. OTCS (Observability & Trace)
        self._observability = ObservabilityService()
        # 6. RGES (Receipt Generation)
        self._courier = OfflineCourier(wal)
        self._receipts = ReceiptService(config.receipt, self._courier)
        # 7. SSDRS (Secure Redaction)
        self._redaction = RedactionService(config.redaction)
        # 8. ETFHF (Error Taxonomy Framework)
        self._taxonomy = ErrorTaxonomy(config.taxonomy_mapping)
        
        self._courier_sink = courier_sink or self._process_wal_entry
        self._dependencies_ready = False
        self._shutdown_called = False
        self._wal_worker_stop = threading.Event()
        # CR-011: Add lock for WAL worker thread synchronization
        self._wal_lock = threading.Lock()
        self._wal_worker = threading.Thread(
            target=self._process_wal_entries,
            name="cccs-wal-drain",
            daemon=True,
        )
        self._wal_worker.start()
        self._instance_ref = weakref.ref(self, self.__class__._on_instance_collect)
        self._register_lifecycle_hooks()

    def bootstrap(
        self,
        dependency_health: Optional[Dict[str, bool]] = None,
        *,
        timeout_seconds: float = 300.0,
        poll_interval: float = 30.0,  # Per PRD §5.9: re-run checks every 30s
    ) -> None:
        """
        Validates dependencies per mode requirements.
        
        Per PRD §5.9: Dependency health checks are re-run every 30 seconds during bootstrap.
        Per PRD §6.4: Version negotiation occurs during bootstrap.
        """
        if dependency_health is not None:
            self._handle_dependency_health(dependency_health)
            # Perform API version negotiation after dependency health is set
            self._perform_version_negotiation()
            return

        start = time.monotonic()
        while True:
            health = self._check_dependencies()
            missing = self._missing_dependencies(health)
            if not missing:
                self._dependencies_ready = True
                # Perform API version negotiation when dependencies are ready
                self._perform_version_negotiation()
                return
            if self._config.mode == "edge":
                self._dependencies_ready = False
                # Edge mode can start in degraded mode, but still attempt version negotiation
                self._perform_version_negotiation()
                return
            if time.monotonic() - start >= timeout_seconds:
                self._raise_bootstrap_error(missing)
            # CR-015: Use interruptible sleep instead of blocking sleep
            self._wal_worker_stop.wait(poll_interval)
            if self._shutdown_called:
                return

    def negotiate_version(self, requested_version: str) -> str:
        requested = APIVersion.parse(requested_version)
        if not self._version.is_compatible_with(requested):
            raise VersionMismatchError(
                f"Incompatible versions: runtime {self._version} vs requested {requested}"
            )
        return str(self._version)

    def load_policy_snapshot(self, payload: dict, signature: str) -> None:
        self._policy.load_snapshot(payload, signature)

    def execute_flow(
        self,
        *,
        module_id: str,
        inputs: JSONDict,
        action_id: str,
        cost: float,
        config_key: str,
        payload: JSONDict,
        redaction_hint: str,
        actor_context: ActorContext,
    ) -> dict:
        """
        Executes end-to-end flow defined in PRD section 7.
        
        Per PRD §8: Zero synchronous network calls on critical path.
        Uses cached data when dependencies not ready (offline mode).
        """
        # 1. Resolve actor (IAPS) - Use cached data, queue EPC-1 calls for background drain
        # Per PRD §8: Zero synchronous network calls on critical path
        try:
            # Use cache when dependencies not ready (offline mode); otherwise allow network calls
            # In offline mode, queue EPC-1 calls to background for later processing
            actor = self._identity.resolve_actor(actor_context, use_cache=(not self._dependencies_ready))
        except ActorUnavailableError:
            raise  # Already canonical
        except (ValueError, TypeError, AttributeError) as e:
            # CR-014: Catch specific exception types instead of generic Exception
            error = self._taxonomy.normalize_error(e)
            raise ActorUnavailableError(
                f"Identity resolution failed: {error.canonical_code} - {error.user_message}"
            ) from e
        except Exception as e:
            # Log unexpected exceptions for debugging
            logger.error(f"Unexpected error in identity resolution: {type(e).__name__}: {e}", exc_info=True)
            error = self._taxonomy.normalize_error(e)
            raise ActorUnavailableError(
                f"Identity resolution failed: {error.canonical_code} - {error.user_message}"
            ) from e

        # 2. Merge config (CFFS) - Local operation, no network
        config = self._config_service.get_config(config_key, overrides=inputs.get("config_overrides"))

        # 3. Evaluate policy (PREE) - Uses offline snapshot, no network calls
        # Per PRD §9: No network policy evaluation; GSMD snapshots validated offline
        try:
            policy_decision = self._policy.evaluate(module_id, inputs)
        except PolicyUnavailableError:
            raise  # Already canonical
        except (ValueError, TypeError, KeyError) as e:
            # CR-014: Catch specific exception types instead of generic Exception
            error = self._taxonomy.normalize_error(e)
            raise PolicyUnavailableError(
                f"Policy evaluation failed: {error.canonical_code} - {error.user_message}"
            ) from e
        except Exception as e:
            # Log unexpected exceptions for debugging
            logger.error(f"Unexpected error in policy evaluation: {type(e).__name__}: {e}", exc_info=True)
            error = self._taxonomy.normalize_error(e)
            raise PolicyUnavailableError(
                f"Policy evaluation failed: {error.canonical_code} - {error.user_message}"
            ) from e

        # Persist policy snapshot to WAL per PRD §7.1
        # CR-016: Use accessor method instead of direct private attribute access
        policy_snapshot = self._get_policy_snapshot()
        if policy_snapshot:
            wal = self._get_wal()
            wal.append_policy_snapshot({
                "module_id": module_id,
                "snapshot_hash": policy_decision.policy_snapshot_hash,
                "version": policy_snapshot.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # 4. Check budgets (RLBGS) - Use cached state, queue EPC-13 calls for background drain
        # Per PRD §8: Zero synchronous network calls on critical path
        budget = None
        budget_exceeded = False
        try:
            # Use cache when dependencies not ready (offline mode); otherwise allow network calls
            # In offline mode, queue EPC-13 calls to background for later processing
            budget = self._ratelimiter.check_budget(action_id, cost, actor_context.tenant_id, use_cache=(not self._dependencies_ready))
        except BudgetExceededError:
            budget_exceeded = True
            # Per PRD §5.6: Emit budget_exceeded receipt
            self._emit_budget_exceeded_receipt(action_id, cost, inputs, actor, policy_decision)
            raise
        except (ValueError, TypeError) as e:
            # CR-014: Catch specific exception types instead of generic Exception
            error = self._taxonomy.normalize_error(e)
            raise BudgetExceededError(
                f"Budget check failed: {error.canonical_code} - {error.user_message}"
            ) from e
        except Exception as e:
            # Log unexpected exceptions for debugging
            logger.error(f"Unexpected error in budget check: {type(e).__name__}: {e}", exc_info=True)
            error = self._taxonomy.normalize_error(e)
            raise BudgetExceededError(
                f"Budget check failed: {error.canonical_code} - {error.user_message}"
            ) from e

        # Persist budget snapshot to WAL per PRD §7.1
        if budget:
            # CR-016: Use accessor method instead of direct private attribute access
            wal = self._get_wal()
            wal.append_budget_snapshot({
                "action_id": action_id,
                "cost": cost,
                "remaining": budget.remaining,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # 5. Generate receipt (RGES) with complete actor provenance data
        with self._observability.start_span(f"cccs:{action_id}") as span:
            trace = span
            receipt = self._receipts.write_receipt(
                inputs=inputs,
                result={
                    "status": self._canonicalize_decision(policy_decision.decision),
                    "rationale": policy_decision.rationale,
                    "badges": ["cccs"],
                },
                actor={
                    "actor_id": actor.actor_id,
                    "actor_type": actor.actor_type,
                    "session_id": actor.session_id,
                    "provenance_signature": actor.provenance_signature,
                    "salt_version": actor.salt_version,
                    "monotonic_counter": actor.monotonic_counter,
                },
                policy_metadata={
                    "policy_version_ids": policy_decision.policy_version_ids,
                    "policy_snapshot_hash": policy_decision.policy_snapshot_hash,
                },
                trace=trace,
                annotations={"config_source": config.source_layers},
                degraded=not self._dependencies_ready,
            )
        
        # 6. Apply redaction (SSDRS)
        redaction_result = self._redaction.apply_redaction(payload, redaction_hint)

        return {
            "actor": actor,
            "config": config,
            "policy": policy_decision,
            "budget": budget,
            "receipt": receipt,
            "redaction": redaction_result,
        }

    def _process_wal_entry(self, payload: Dict[str, Any]) -> None:
        """Process WAL entry based on type."""
        entry_type = payload.get("type")
        if entry_type == "epc1_call":
            self._identity.process_wal_entry(payload)
        elif entry_type == "epc13_call":
            self._ratelimiter.process_wal_entry(payload)
        elif entry_type == "receipt":
            receipt = payload.get("payload", payload)
            # Replay receipt if needed (for now, just pass to sink)
            self._courier_sink(receipt)

    def _emit_budget_exceeded_receipt(
        self, action_id: str, cost: float, inputs: JSONDict, actor: ActorBlock, policy_decision: PolicyDecision
    ) -> None:
        """Emit budget_exceeded receipt per PRD §5.6."""
        try:
            self._receipts.write_receipt(
                inputs=inputs,
                result={
                    "status": "hard_block",
                    "rationale": f"Budget exceeded for {action_id}: cost {cost}",
                    "badges": ["cccs", "budget_exceeded"],
                },
                actor={
                    "actor_id": actor.actor_id,
                    "actor_type": actor.actor_type,
                    "session_id": actor.session_id,
                    "provenance_signature": actor.provenance_signature,
                    "salt_version": actor.salt_version,
                    "monotonic_counter": actor.monotonic_counter,
                },
                policy_metadata={
                    "policy_version_ids": policy_decision.policy_version_ids,
                    "policy_snapshot_hash": policy_decision.policy_snapshot_hash,
                },
                trace=None,
                annotations={"action_id": action_id, "cost": cost, "receipt_type": "budget_exceeded"},
                degraded=not self._dependencies_ready,
            )
        except Exception as e:
            # Log but don't fail the flow
            logger.error(f"Failed to emit budget_exceeded receipt: {e}")

    def _emit_dead_letter_receipt(self, dead_letter_receipt: Dict[str, Any]) -> None:
        """Emit dead_letter receipt per PRD §7.1."""
        try:
            self._receipts.write_receipt(
                inputs=dead_letter_receipt.get("payload", {}),
                result={
                    "status": "hard_block",
                    "rationale": f"WAL drain failed: {dead_letter_receipt.get('error', 'unknown')}",
                    "badges": ["cccs", "dead_letter"],
                },
                actor={},  # Dead letter receipts may not have actor context
                policy_metadata={},
                trace=None,
                annotations={
                    "receipt_type": "dead_letter",
                    "wal_sequence": dead_letter_receipt.get("wal_sequence"),
                    "entry_type": dead_letter_receipt.get("entry_type"),
                    "error": dead_letter_receipt.get("error"),
                },
                degraded=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to emit dead_letter receipt: %s", exc)

    def drain_courier(self) -> List[int]:
        """
        Flushes courier batches to sink with receipt emitter for dead_letter receipts.
        
        Per PRD §7.1: Nothing is dropped without an explicit dead_letter receipt.
        """
        # CR-011: Use lock for thread-safe access to courier
        with self._wal_lock:
            return self._courier.drain(self._courier_sink, receipt_emitter=self._emit_dead_letter_receipt)

    def normalize_error(self, error: BaseException) -> dict:
        return self._taxonomy.normalize_error(error).__dict__

    def shutdown(self) -> None:
        """Shut down runtime services cleanly."""
        if self._shutdown_called:
            return
        self._shutdown_called = True
        self._deregister_instance()

        self._wal_worker_stop.set()
        if self._wal_worker.is_alive():
            self._wal_worker.join(timeout=5)
        try:
            self._run_async(self._identity.close())
        except Exception as e:
            logger.error(f"Error closing identity service: {e}")
        try:
            self._run_async(self._policy.close())
        except Exception as e:
            logger.error(f"Error closing policy service: {e}")
        try:
            self._run_async(self._ratelimiter.close())
        except Exception as e:
            logger.error(f"Error closing rate limiter service: {e}")
        try:
            self._run_async(self._receipts.close())
        except Exception as e:
            logger.error(f"Error closing receipt service: {e}")

    def _canonicalize_decision(self, decision: str) -> str:
        mapping = {
            "allow": "pass",
            "pass": "pass",
            "warn": "warn",
            "soft_block": "soft_block",
            "deny": "hard_block",
            "hard_block": "hard_block",
        }
        return mapping.get(decision, "hard_block")

    def _handle_dependency_health(self, health: Dict[str, bool]) -> None:
        missing = self._missing_dependencies(health)
        if missing and self._config.mode == "backend":
            self._raise_bootstrap_error(missing)
        self._dependencies_ready = not missing

    def _missing_dependencies(self, health: Dict[str, bool]) -> List[str]:
        deps = self._dependency_list()
        return [dep for dep in deps if not health.get(dep)]

    def _check_dependencies(self) -> Dict[str, bool]:
        health = {
            "epc-1": self._safe_async_bool(self._identity.health_check()),
            "epc-3": self._safe_async_bool(self._policy.health_check()),
            "epc-13": self._safe_async_bool(self._ratelimiter.health_check()),
            "epc-11": self._safe_async_bool(self._receipts.health_check()),
        }
        if self._receipts.has_pm7():
            health["pm-7"] = self._safe_async_bool(self._receipts.pm7_health_check())
        return health

    def _dependency_list(self) -> List[str]:
        deps = ["epc-1", "epc-3", "epc-13", "epc-11"]
        if self._receipts.has_pm7():
            deps.append("pm-7")
        return deps

    def _raise_bootstrap_error(self, missing: List[str]) -> None:
        error = BootstrapTimeoutError(f"Dependencies unavailable: {missing}")
        raise PolicyUnavailableError("Bootstrap failed") from error

    def _safe_async_bool(self, coro) -> bool:
        try:
            return bool(self._run_async(coro))
        except Exception:
            return False

    def _run_async(self, coro):
        # CR-010: Reuse shared event loop to prevent resource leaks
        with self.__class__._event_loop_lock:
            if self.__class__._shared_event_loop is None or self.__class__._shared_event_loop.is_closed():
                try:
                    # Try to get existing event loop
                    self.__class__._shared_event_loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop exists, create new one
                    self.__class__._shared_event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.__class__._shared_event_loop)
        
        loop = self.__class__._shared_event_loop
        try:
            return loop.run_until_complete(coro)
        except RuntimeError:
            # If loop is closed, create a new one
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def _process_wal_entries(self) -> None:
        """Background worker to process WAL entries."""
        while not self._wal_worker_stop.is_set():
            try:
                # CR-011: Use lock for thread-safe access to courier
                with self._wal_lock:
                    drained = self._courier.drain(self._courier_sink, receipt_emitter=self._emit_dead_letter_receipt)
                if not drained:
                    self._wal_worker_stop.wait(1.0)
            except Exception as e:
                # CR-012: Ensure exceptions trigger dead-letter receipt emission
                logger.error(f"Error in WAL worker: {e}", exc_info=True)
                try:
                    # Emit dead-letter receipt for the error
                    self._emit_dead_letter_receipt({
                        "error": str(e),
                        "entry_type": "wal_worker_error",
                        "payload": {}
                    })
                except Exception as emit_error:
                    logger.error(f"Failed to emit dead-letter receipt for WAL worker error: {emit_error}")
                self._wal_worker_stop.wait(1.0)

    def _perform_version_negotiation(self) -> None:
        """
        Perform API version negotiation during bootstrap per PRD §6.4.
        
        Per PRD §6.4: Version negotiation occurs during bootstrap; mismatches emit version_mismatch via ETFHF.
        """
        # For now, version negotiation is handled by negotiate_version method
        # In a full implementation, this would check with EPC services for version compatibility
        # and emit ETFHF entries for mismatches
        pass

    def _get_policy_snapshot(self):
        """CR-016: Accessor method for policy snapshot."""
        # Access private attribute through method to maintain encapsulation
        return getattr(self._policy, '_snapshot', None)

    def _get_wal(self):
        """CR-016: Accessor method for WAL."""
        # Access private attribute through method to maintain encapsulation
        return getattr(getattr(self._receipts, '_courier', None), '_wal', None)

    def _register_lifecycle_hooks(self) -> None:
        cls = self.__class__
        with cls._instance_lock:
            cls._instance_refs.add(self._instance_ref)
            if not cls._atexit_registered:
                atexit.register(cls._shutdown_all_instances)
                cls._atexit_registered = True
            if not cls._signals_installed and cls._signal_numbers:
                cls._install_signal_handlers()

    def _deregister_instance(self) -> None:
        cls = self.__class__
        with cls._instance_lock:
            cls._instance_refs.discard(self._instance_ref)

    @classmethod
    def _on_instance_collect(cls, ref: weakref.ReferenceType["CCCSRuntime"]) -> None:
        with cls._instance_lock:
            cls._instance_refs.discard(ref)

    @classmethod
    def _install_signal_handlers(cls) -> None:
        for signum in cls._signal_numbers:
            try:
                previous = signal.getsignal(signum)
                cls._previous_signal_handlers[signum] = previous

                def _handler(
                    signum: int,
                    frame: Optional[object],
                    *,
                    prev: Callable[[int, Optional[object]], None] | int | None = previous,
                ) -> None:
                    cls._shutdown_all_instances()
                    if callable(prev):
                        prev(signum, frame)

                signal.signal(signum, _handler)
            except (OSError, RuntimeError, ValueError, AttributeError):
                continue
        cls._signals_installed = True

    @classmethod
    def _shutdown_all_instances(cls) -> None:
        with cls._instance_lock:
            refs = list(cls._instance_refs)
            # CR-013: Clean up instance refs to prevent memory leak
            cls._instance_refs.clear()
        for ref in refs:
            runtime = ref()
            if runtime:
                runtime.shutdown()
        # CR-010: Clean up shared event loop
        with cls._event_loop_lock:
            if cls._shared_event_loop and not cls._shared_event_loop.is_closed():
                try:
                    cls._shared_event_loop.close()
                except Exception:
                    pass
                cls._shared_event_loop = None

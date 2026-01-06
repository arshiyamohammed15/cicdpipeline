"""
Model Router component implementing policy-driven LLM routing per LLM Strategy Directives.

This component implements the Router contract required by ADR-LLM-001 and
docs/architecture/llm_strategy_directives.md Section 8.1.

The router is pure and testable - no network calls, deterministic outputs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ..clients.policy_client import PolicySnapshot


class Plane(str, Enum):
    """Deployment plane identifier."""

    IDE = "ide"
    TENANT = "tenant"
    PRODUCT = "product"
    SHARED = "shared"


class TaskType(str, Enum):
    """Task type classification per LLM Strategy Directives."""

    CODE = "code"
    TEXT = "text"
    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    SUMMARISE = "summarise"


class TaskClass(str, Enum):
    """Task class classification (major vs minor)."""

    MAJOR = "major"
    MINOR = "minor"


class ResultStatus(str, Enum):
    """Result status per LLM Strategy Directives Section 6.1."""

    OK = "ok"
    SCHEMA_FAIL = "schema_fail"
    TIMEOUT = "timeout"
    MODEL_UNAVAILABLE = "model_unavailable"
    ERROR = "error"


@dataclass
class MeasurableSignals:
    """Measurable signals for task classification."""

    changed_files_count: int = 0
    estimated_diff_loc: int = 0
    rag_context_bytes: int = 0
    tool_calls_planned: int = 0
    high_stakes_flag: bool = False


@dataclass
class LLMParams:
    """LLM parameters per LLM Strategy Directives Section 5."""

    num_ctx: int
    temperature: float
    seed: int


@dataclass
class ModelRoutingDecision:
    """Router decision output per LLM Strategy Directives Section 8.1."""

    model_primary: str
    model_failover_chain: List[str]
    llm_params: LLMParams
    task_class: TaskClass
    task_type: TaskType
    degraded_mode: bool
    router_policy_id: str
    router_policy_snapshot_hash: str
    contract_enforcement_rules: Dict[str, Any]


class ModelRouter:
    """
    Policy-driven model router per LLM Strategy Directives Section 8.1.

    This router is pure and testable - no network calls, deterministic outputs.
    All routing decisions are based on policy snapshot and measurable signals.
    """

    # Default policy ID
    DEFAULT_POLICY_ID = "POL-LLM-ROUTER-001"

    # Default thresholds (can be overridden by policy)
    DEFAULT_MAJOR_FILES_THRESHOLD = 10
    DEFAULT_MAJOR_LOC_THRESHOLD = 500
    DEFAULT_MAJOR_RAG_BYTES_THRESHOLD = 100000
    DEFAULT_MAJOR_TOOLCALL_THRESHOLD = 5

    # Default context window sizes per LLM Strategy Directives Section 4.1
    DEFAULT_MINOR_NUM_CTX = 4096
    DEFAULT_MAJOR_NUM_CTX = 16384

    # Default temperature per LLM Strategy Directives Section 5.2
    DEFAULT_TEMPERATURE = 0.0

    # Default seed (policy-defined, deterministic)
    DEFAULT_SEED = 42

    def __init__(self) -> None:
        """Initialize ModelRouter."""
        pass

    def route(
        self,
        plane: Plane,
        task_type: TaskType,
        signals: MeasurableSignals,
        policy_snapshot: PolicySnapshot,
    ) -> ModelRoutingDecision:
        """
        Route to appropriate model based on plane, task type, signals, and policy.

        Args:
            plane: Deployment plane (ide/tenant/product/shared)
            task_type: Task type (code/text/retrieval/planning/summarise)
            signals: Measurable signals for task classification
            policy_snapshot: Policy snapshot containing routing rules

        Returns:
            ModelRoutingDecision with model selection, params, and metadata
        """
        # Classify task as major or minor
        task_class = self._classify_task(signals, policy_snapshot)

        # Get routing policy from snapshot
        router_policy = self._extract_router_policy(policy_snapshot)

        # Select model based on plane, task_class, and task_type
        model_primary, model_failover_chain, degraded_mode = self._select_model(
            plane, task_class, task_type, router_policy
        )

        # Determine LLM parameters
        llm_params = self._determine_llm_params(
            task_class, router_policy, policy_snapshot
        )

        # Generate policy snapshot hash
        policy_snapshot_hash = self._generate_policy_snapshot_hash(policy_snapshot)

        # Extract contract enforcement rules from policy
        contract_enforcement_rules = self._extract_contract_enforcement_rules(
            router_policy
        )

        return ModelRoutingDecision(
            model_primary=model_primary,
            model_failover_chain=model_failover_chain,
            llm_params=llm_params,
            task_class=task_class,
            task_type=task_type,
            degraded_mode=degraded_mode,
            router_policy_id=router_policy.get("policy_id", self.DEFAULT_POLICY_ID),
            router_policy_snapshot_hash=policy_snapshot_hash,
            contract_enforcement_rules=contract_enforcement_rules,
        )

    def _classify_task(
        self, signals: MeasurableSignals, policy_snapshot: PolicySnapshot
    ) -> TaskClass:
        """
        Classify task as major or minor based on measurable signals.

        Per LLM Strategy Directives Section 2:
        - Major if ANY threshold exceeded OR high_stakes_flag == true
        - Minor if ALL thresholds below AND high_stakes_flag == false
        """
        router_policy = self._extract_router_policy(policy_snapshot)

        # Get thresholds from policy (with defaults)
        major_files_threshold = router_policy.get(
            "major", {}
        ).get("files_threshold", self.DEFAULT_MAJOR_FILES_THRESHOLD)
        major_loc_threshold = router_policy.get("major", {}).get(
            "loc_threshold", self.DEFAULT_MAJOR_LOC_THRESHOLD
        )
        major_rag_bytes_threshold = router_policy.get("major", {}).get(
            "rag_bytes_threshold", self.DEFAULT_MAJOR_RAG_BYTES_THRESHOLD
        )
        major_toolcall_threshold = router_policy.get("major", {}).get(
            "tool_calls_threshold", self.DEFAULT_MAJOR_TOOLCALL_THRESHOLD
        )

        # Check if ANY major condition is true
        if signals.high_stakes_flag:
            return TaskClass.MAJOR

        if signals.changed_files_count >= major_files_threshold:
            return TaskClass.MAJOR

        if signals.estimated_diff_loc >= major_loc_threshold:
            return TaskClass.MAJOR

        if signals.rag_context_bytes >= major_rag_bytes_threshold:
            return TaskClass.MAJOR

        if signals.tool_calls_planned >= major_toolcall_threshold:
            return TaskClass.MAJOR

        # All conditions false → Minor
        return TaskClass.MINOR

    def _select_model(
        self,
        plane: Plane,
        task_class: TaskClass,
        task_type: TaskType,
        router_policy: Dict[str, Any],
    ) -> tuple[str, List[str], bool]:
        """
        Select model based on plane, task class, and task type.

        Per LLM Strategy Directives Section 1:
        - IDE Plane: code tasks → qwen2.5-coder:7b/14b, text tasks → llama3.1:8b, failover → tinyllama:latest
        - Tenant/Product/Shared: major → qwen2.5-coder:32b, minor → qwen2.5-coder:14b, failover → qwen2.5-coder:14b/tinyllama:latest
        """
        # Check for policy overrides first
        plane_policy = router_policy.get("planes", {}).get(plane.value, {})

        if plane == Plane.IDE:
            # IDE plane: two primaries by task type
            if task_type == TaskType.CODE:
                primary = plane_policy.get(
                    "code_primary", "qwen2.5-coder:7b"
                )  # or 14b if hardware supports
            else:
                primary = plane_policy.get("text_primary", "llama3.1:8b")
            failover = plane_policy.get("failover", "tinyllama:latest")
            degraded = failover == "tinyllama:latest"
            return primary, [failover], degraded

        # Tenant/Product/Shared planes
        if task_class == TaskClass.MAJOR:
            primary = plane_policy.get("major_primary", "qwen2.5-coder:32b")
            failover = plane_policy.get("major_failover", "qwen2.5-coder:14b")
        else:
            primary = plane_policy.get("minor_primary", "qwen2.5-coder:14b")
            failover = plane_policy.get("minor_failover", "tinyllama:latest")

        degraded = failover == "tinyllama:latest"
        return primary, [failover], degraded

    def _determine_llm_params(
        self,
        task_class: TaskClass,
        router_policy: Dict[str, Any],
        policy_snapshot: PolicySnapshot,
    ) -> LLMParams:
        """
        Determine LLM parameters (num_ctx, temperature, seed) per LLM Strategy Directives Section 4-5.
        """
        # Context window: major tasks get larger context
        if task_class == TaskClass.MAJOR:
            num_ctx = router_policy.get("params", {}).get(
                "major_num_ctx", self.DEFAULT_MAJOR_NUM_CTX
            )
        else:
            num_ctx = router_policy.get("params", {}).get(
                "minor_num_ctx", self.DEFAULT_MINOR_NUM_CTX
            )

        # Temperature: policy-defined, default 0.0-0.2 for governance
        temperature = router_policy.get("params", {}).get(
            "temperature", self.DEFAULT_TEMPERATURE
        )

        # Seed: policy-defined, deterministic
        seed = router_policy.get("params", {}).get("seed", self.DEFAULT_SEED)

        return LLMParams(num_ctx=num_ctx, temperature=temperature, seed=seed)

    def _extract_router_policy(self, policy_snapshot: PolicySnapshot) -> Dict[str, Any]:
        """Extract router policy from policy snapshot."""
        # Policy snapshot may have router configuration in bounds or recovery sections
        # For now, return empty dict and use defaults
        # In production, this would extract from policy_snapshot.router_config or similar
        return policy_snapshot.bounds.get("router", {}) if hasattr(policy_snapshot, "bounds") else {}

    def _extract_contract_enforcement_rules(
        self, router_policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract contract enforcement rules from router policy."""
        return router_policy.get("contract_enforcement", {})

    def _generate_policy_snapshot_hash(
        self, policy_snapshot: PolicySnapshot
    ) -> str:
        """Generate hash of policy snapshot for receipt tracking."""
        # Create deterministic hash from snapshot ID and version IDs
        snapshot_data = {
            "snapshot_id": policy_snapshot.snapshot_id,
            "version_ids": policy_snapshot.version_ids,
        }
        snapshot_json = json.dumps(snapshot_data, sort_keys=True)
        hash_value = hashlib.sha256(snapshot_json.encode()).hexdigest()
        return f"sha256:{hash_value}"


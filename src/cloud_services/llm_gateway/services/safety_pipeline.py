"""
Safety pipeline that executes input/output checks and returns risk metadata.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Tuple

from ..models import (
    Decision,
    LLMRequest,
    RiskClass,
    RiskFlag,
    SafetyAction,
    SafetyAssessment,
    SafetyCheck,
    SafetyCheckStatus,
    Severity,
)


PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?previous instructions", re.I),
    re.compile(r"dump (the )?admin password", re.I),
]

PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"(api|access|auth)[_-]?token", re.I),
]


class SafetyPipelineResult:
    """Aggregates checks, risk flags, and actions for a request."""

    def __init__(self) -> None:
        self.input_checks: List[SafetyCheck] = []
        self.output_checks: List[SafetyCheck] = []
        self.risk_flags: List[RiskFlag] = []
        # (SafetyAction, target_risk_class or other reason)
        self.actions: List[Tuple[SafetyAction, str]] = []

    def add_flag(
        self,
        risk_class: RiskClass,
        severity: Severity,
        actions: List[SafetyAction],
    ) -> None:
        self.risk_flags.append(
            RiskFlag(risk_class=risk_class, severity=severity, actions=actions)
        )
        for action in actions:
            self.actions.append((action, risk_class.value))

    def to_assessment(self, request_id: str) -> SafetyAssessment:
        return SafetyAssessment(
            assessment_id=f"assess-{request_id}",
            request_id=request_id,
            input_checks=self.input_checks or [self._noop_check("input")],
            output_checks=self.output_checks or [self._noop_check("output")],
            risk_classes=self.risk_flags,
            actions_taken=[
                {"action": action.value, "reason": reason} for action, reason in self.actions
            ],
            metrics={"processing_latency_ms": 5},
            generated_at=datetime.now(tz=timezone.utc),
        )

    @staticmethod
    def _noop_check(stage: str) -> SafetyCheck:
        return SafetyCheck(
            name=f"{stage}_baseline",
            status=SafetyCheckStatus.PASSED,
            score=0.0,
            details="No checks executed",
        )


class SafetyPipeline:
    """
    Executes deterministic safeguards aligned with the PRD.

    This implementation keeps detectors pluggable but currently uses
    deterministic heuristics with classifier_version identifiers that
    correspond to §14.5 (e.g. r1_promptshield_v1, pii_guard_v1, r3_guard_v1).
    """

    def run_input_checks(self, request: LLMRequest) -> SafetyPipelineResult:
        result = SafetyPipelineResult()

        self._check_prompt_injection(request, result)
        self._check_pii_hints(request, result)
        self._check_tool_safety(request, result)

        if not result.input_checks:
            result.input_checks.append(
                SafetyCheck(
                    name="prompt_clean",
                    status=SafetyCheckStatus.PASSED,
                    score=0.0,
                    details="No input risks detected",
                )
            )

        return result

    # ------------------------------------------------------------------
    # Individual detector implementations
    # ------------------------------------------------------------------

    def _check_prompt_injection(
        self, request: LLMRequest, result: SafetyPipelineResult
    ) -> None:
        """R1 – Prompt injection / jailbreak (heuristic detector)."""
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(request.user_prompt):
                result.input_checks.append(
                    SafetyCheck(
                        name="prompt_injection",
                        status=SafetyCheckStatus.FAILED,
                        score=0.9,
                        details="Prompt injection heuristic matched",
                        classifier_version="r1_promptshield_v1",
                    )
                )
                result.add_flag(
                    RiskClass.R1,
                    Severity.WARN,
                    actions=[SafetyAction.BLOCK, SafetyAction.ALERTED],
                )
                break

    def _check_pii_hints(
        self, request: LLMRequest, result: SafetyPipelineResult
    ) -> None:
        """R2 – PII / secrets (heuristic pre-filter before EPC-2)."""
        for pattern in PII_PATTERNS:
            if pattern.search(request.user_prompt):
                result.input_checks.append(
                    SafetyCheck(
                        name="pii_scan",
                        status=SafetyCheckStatus.FAILED,
                        score=0.8,
                        details="Possible PII or secret detected in input",
                        classifier_version="pii_guard_v1",
                    )
                )
                result.add_flag(
                    RiskClass.R2,
                    Severity.WARN,
                    actions=[SafetyAction.REDACT],
                )
                break

    def _check_tool_safety(
        self, request: LLMRequest, result: SafetyPipelineResult
    ) -> None:
        """
        R4 – Tool/action safety (minimal implementation).

        Uses:
        - request.proposed_tool_calls: logical tool identifiers
        - request.budget.tool_allowlist: allowed tools per policy
        - Actor capabilities are validated earlier by IAM client; here we
          focus on policy/tool matrix enforcement.
        """
        proposed = request.proposed_tool_calls or []
        allowlist = request.budget.tool_allowlist or []
        if not proposed:
            return

        blocked_tools: List[str] = []
        for tool in proposed:
            if tool not in allowlist:
                blocked_tools.append(tool)

        if blocked_tools:
            details = f"Blocked tools per policy: {', '.join(sorted(blocked_tools))}"
            result.input_checks.append(
                SafetyCheck(
                    name="tool_safety_matrix",
                    status=SafetyCheckStatus.FAILED,
                    score=0.9,
                    details=details,
                    classifier_version="r4_toolmatrix_v1",
                )
            )
            result.add_flag(
                RiskClass.R4,
                Severity.WARN,
                actions=[SafetyAction.BLOCK],
            )

    def run_output_checks(
        self, response_text: str, result: SafetyPipelineResult
    ) -> SafetyPipelineResult:
        if "hate" in response_text.lower():
            result.output_checks.append(
                SafetyCheck(
                    name="toxicity_check",
                    status=SafetyCheckStatus.FAILED,
                    score=0.95,
                    details="Toxic language detected",
                    classifier_version="r3_guard_v1",
                )
            )
            result.add_flag(
                RiskClass.R3,
                Severity.CRITICAL,
                actions=[SafetyAction.BLOCK, SafetyAction.ALERTED],
            )
        else:
            result.output_checks.append(
                SafetyCheck(
                    name="toxicity_check",
                    status=SafetyCheckStatus.PASSED,
                    score=0.0,
                    classifier_version="r3_guard_v1",
                )
            )

        return result

    def final_decision(self, result: SafetyPipelineResult) -> Decision:
        for flag in result.risk_flags:
            if flag.severity is Severity.CRITICAL:
                return Decision.BLOCKED
        for action, _ in result.actions:
            if action is SafetyAction.BLOCK:
                return Decision.BLOCKED
        if any(action is SafetyAction.REDACT for action, _ in result.actions):
            return Decision.TRANSFORMED
        return Decision.ALLOWED


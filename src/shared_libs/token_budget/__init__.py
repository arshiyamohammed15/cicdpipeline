"""
Deterministic token budget checks for request sizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

DecisionType = Literal["ALLOW", "DENY"]

TOK_BUDGET_INPUT_EXCEEDED = "TOK_BUDGET_INPUT_EXCEEDED"
TOK_BUDGET_OUTPUT_EXCEEDED = "TOK_BUDGET_OUTPUT_EXCEEDED"
TOK_BUDGET_TOTAL_EXCEEDED = "TOK_BUDGET_TOTAL_EXCEEDED"
TOK_BUDGET_OK = "TOK_BUDGET_OK"


@dataclass(frozen=True)
class BudgetSpec:
    """
    Hard token limits for a request.

    max_tool_tokens_optional is included for completeness but not evaluated here.
    """

    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    max_tool_tokens_optional: Optional[int] = None


@dataclass(frozen=True)
class BudgetDecision:
    """Decision result for a token budget check."""

    decision: DecisionType
    reason_code: str
    human_message: str


def BudgetManager(
    estimated_input_tokens: int,
    requested_output_tokens: Optional[int],
    spec: BudgetSpec,
) -> BudgetDecision:
    """
    Evaluate a token budget spec against the request sizing.

    Checks input, output, then total limits. Missing output tokens are treated as 0.
    """

    normalized_output_tokens = (
        0 if requested_output_tokens is None else requested_output_tokens
    )

    if estimated_input_tokens > spec.max_input_tokens:
        return BudgetDecision(
            decision="DENY",
            reason_code=TOK_BUDGET_INPUT_EXCEEDED,
            human_message="Input token budget exceeded.",
        )

    if normalized_output_tokens > spec.max_output_tokens:
        return BudgetDecision(
            decision="DENY",
            reason_code=TOK_BUDGET_OUTPUT_EXCEEDED,
            human_message="Output token budget exceeded.",
        )

    total_tokens = estimated_input_tokens + normalized_output_tokens
    if total_tokens > spec.max_total_tokens:
        return BudgetDecision(
            decision="DENY",
            reason_code=TOK_BUDGET_TOTAL_EXCEEDED,
            human_message="Total token budget exceeded.",
        )

    return BudgetDecision(
        decision="ALLOW",
        reason_code=TOK_BUDGET_OK,
        human_message="Within token budget.",
    )


__all__ = [
    "BudgetDecision",
    "BudgetManager",
    "BudgetSpec",
    "DecisionType",
    "TOK_BUDGET_INPUT_EXCEEDED",
    "TOK_BUDGET_OUTPUT_EXCEEDED",
    "TOK_BUDGET_TOTAL_EXCEEDED",
    "TOK_BUDGET_OK",
]

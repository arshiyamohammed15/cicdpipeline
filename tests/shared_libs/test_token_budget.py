from __future__ import annotations

import pytest

from src.shared_libs.token_budget import (
    BudgetManager,
    BudgetSpec,
    TOK_BUDGET_INPUT_EXCEEDED,
    TOK_BUDGET_OK,
    TOK_BUDGET_OUTPUT_EXCEEDED,
    TOK_BUDGET_TOTAL_EXCEEDED,
)


@pytest.mark.parametrize(
    ("estimated_input_tokens", "requested_output_tokens", "spec"),
    [
        (10, 0, BudgetSpec(max_input_tokens=10, max_output_tokens=5, max_total_tokens=20)),
        (0, 5, BudgetSpec(max_input_tokens=10, max_output_tokens=5, max_total_tokens=20)),
        (60, 60, BudgetSpec(max_input_tokens=100, max_output_tokens=100, max_total_tokens=120)),
    ],
)
@pytest.mark.unit
def test_budget_manager_allows_at_limits(
    estimated_input_tokens: int,
    requested_output_tokens: int,
    spec: BudgetSpec,
) -> None:
    decision = BudgetManager(
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        spec=spec,
    )

    assert decision.decision == "ALLOW"
    assert decision.reason_code == TOK_BUDGET_OK


@pytest.mark.parametrize(
    ("estimated_input_tokens", "requested_output_tokens", "spec", "expected_reason_code"),
    [
        (
            11,
            0,
            BudgetSpec(max_input_tokens=10, max_output_tokens=50, max_total_tokens=60),
            TOK_BUDGET_INPUT_EXCEEDED,
        ),
        (
            0,
            11,
            BudgetSpec(max_input_tokens=100, max_output_tokens=10, max_total_tokens=200),
            TOK_BUDGET_OUTPUT_EXCEEDED,
        ),
        (
            60,
            61,
            BudgetSpec(max_input_tokens=100, max_output_tokens=100, max_total_tokens=120),
            TOK_BUDGET_TOTAL_EXCEEDED,
        ),
    ],
)
@pytest.mark.unit
def test_budget_manager_denies_over_limits(
    estimated_input_tokens: int,
    requested_output_tokens: int,
    spec: BudgetSpec,
    expected_reason_code: str,
) -> None:
    decision = BudgetManager(
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        spec=spec,
    )

    assert decision.decision == "DENY"
    assert decision.reason_code == expected_reason_code


@pytest.mark.unit
def test_budget_manager_missing_output_treated_as_zero_allows_at_limit() -> None:
    spec = BudgetSpec(max_input_tokens=5, max_output_tokens=0, max_total_tokens=5)

    decision = BudgetManager(
        estimated_input_tokens=5,
        requested_output_tokens=None,
        spec=spec,
    )

    assert decision.decision == "ALLOW"
    assert decision.reason_code == TOK_BUDGET_OK


@pytest.mark.unit
def test_budget_manager_missing_output_treated_as_zero_denies_when_input_exceeded() -> None:
    spec = BudgetSpec(max_input_tokens=4, max_output_tokens=0, max_total_tokens=4)

    decision = BudgetManager(
        estimated_input_tokens=5,
        requested_output_tokens=None,
        spec=spec,
    )

    assert decision.decision == "DENY"
    assert decision.reason_code == TOK_BUDGET_INPUT_EXCEEDED

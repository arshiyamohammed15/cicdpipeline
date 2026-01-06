"""
Receipt schema validation per LLM Strategy Directives Section 6.1.

Validates that receipts include all required fields as specified in
docs/architecture/llm_strategy_directives.md Section 6.1.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ReceiptValidationError(Exception):
    """Raised when receipt validation fails."""

    def __init__(self, message: str, missing_fields: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_fields = missing_fields or []


class ReceiptValidator:
    """
    Validates LLM receipts against LLM Strategy Directives Section 6.1 schema.

    Required fields per directives:
    - plane: ide | tenant | product | shared
    - task_class: major | minor
    - task_type: code | text | retrieval | planning | summarise
    - model.primary: exact model tag string
    - model.used: exact model tag string
    - model.failover_used: boolean
    - degraded_mode: boolean
    - router.policy_id: e.g. POL-LLM-ROUTER-001
    - router.policy_snapshot_hash
    - llm.params: { num_ctx, temperature, seed }
    - output.contract_id (if JSON schema enforced)
    - result.status: ok | schema_fail | timeout | model_unavailable | error
    - evidence.trace_id / receipt_id
    """

    REQUIRED_FIELDS = [
        "plane",
        "task_class",
        "task_type",
        "model",
        "degraded_mode",
        "router",
        "llm",
        "result",
        "evidence",
    ]

    REQUIRED_MODEL_FIELDS = ["primary", "used", "failover_used"]
    REQUIRED_ROUTER_FIELDS = ["policy_id", "policy_snapshot_hash"]
    REQUIRED_LLM_PARAMS = ["num_ctx", "temperature", "seed"]
    REQUIRED_RESULT_FIELDS = ["status"]
    REQUIRED_EVIDENCE_FIELDS = ["receipt_id"]

    VALID_PLANES = {"ide", "tenant", "product", "shared"}
    VALID_TASK_CLASSES = {"major", "minor"}
    VALID_TASK_TYPES = {"code", "text", "retrieval", "planning", "summarise"}
    VALID_RESULT_STATUSES = {
        "ok",
        "schema_fail",
        "timeout",
        "model_unavailable",
        "error",
    }

    @classmethod
    def validate(cls, receipt: Dict[str, Any]) -> None:
        """
        Validate receipt against LLM Strategy Directives Section 6.1 schema.

        Args:
            receipt: Receipt dictionary to validate

        Raises:
            ReceiptValidationError: If receipt is missing required fields or has invalid values
        """
        missing_fields: List[str] = []
        errors: List[str] = []

        # Check top-level required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in receipt:
                missing_fields.append(field)

        if missing_fields:
            raise ReceiptValidationError(
                f"Receipt missing required fields: {', '.join(missing_fields)}",
                missing_fields=missing_fields,
            )

        # Validate plane
        plane = receipt.get("plane")
        if plane not in cls.VALID_PLANES:
            errors.append(f"Invalid plane: {plane}. Must be one of {cls.VALID_PLANES}")

        # Validate task_class
        task_class = receipt.get("task_class")
        if task_class not in cls.VALID_TASK_CLASSES:
            errors.append(
                f"Invalid task_class: {task_class}. Must be one of {cls.VALID_TASK_CLASSES}"
            )

        # Validate task_type
        task_type = receipt.get("task_type")
        if task_type not in cls.VALID_TASK_TYPES:
            errors.append(
                f"Invalid task_type: {task_type}. Must be one of {cls.VALID_TASK_TYPES}"
            )

        # Validate model fields
        model = receipt.get("model", {})
        if not isinstance(model, dict):
            errors.append("model must be a dictionary")
        else:
            for field in cls.REQUIRED_MODEL_FIELDS:
                if field not in model:
                    errors.append(f"model.{field} is required")
            if "failover_used" in model and not isinstance(
                model["failover_used"], bool
            ):
                errors.append("model.failover_used must be a boolean")

        # Validate degraded_mode
        degraded_mode = receipt.get("degraded_mode")
        if not isinstance(degraded_mode, bool):
            errors.append("degraded_mode must be a boolean")

        # Validate router fields
        router = receipt.get("router", {})
        if not isinstance(router, dict):
            errors.append("router must be a dictionary")
        else:
            for field in cls.REQUIRED_ROUTER_FIELDS:
                if field not in router:
                    errors.append(f"router.{field} is required")

        # Validate llm.params
        llm = receipt.get("llm", {})
        if not isinstance(llm, dict):
            errors.append("llm must be a dictionary")
        else:
            params = llm.get("params", {})
            if not isinstance(params, dict):
                errors.append("llm.params must be a dictionary")
            else:
                for param in cls.REQUIRED_LLM_PARAMS:
                    if param not in params:
                        errors.append(f"llm.params.{param} is required")
                # Validate types
                if "num_ctx" in params and not isinstance(params["num_ctx"], int):
                    errors.append("llm.params.num_ctx must be an integer")
                if "temperature" in params and not isinstance(
                    params["temperature"], (int, float)
                ):
                    errors.append("llm.params.temperature must be a number")
                if "seed" in params and not isinstance(params["seed"], int):
                    errors.append("llm.params.seed must be an integer")

        # Validate result.status
        result = receipt.get("result", {})
        if not isinstance(result, dict):
            errors.append("result must be a dictionary")
        else:
            for field in cls.REQUIRED_RESULT_FIELDS:
                if field not in result:
                    errors.append(f"result.{field} is required")
            status = result.get("status")
            if status and status not in cls.VALID_RESULT_STATUSES:
                errors.append(
                    f"Invalid result.status: {status}. Must be one of {cls.VALID_RESULT_STATUSES}"
                )

        # Validate evidence fields
        evidence = receipt.get("evidence", {})
        if not isinstance(evidence, dict):
            errors.append("evidence must be a dictionary")
        else:
            if "receipt_id" not in evidence:
                errors.append("evidence.receipt_id is required")

        if errors:
            raise ReceiptValidationError(
                f"Receipt validation failed: {'; '.join(errors)}", missing_fields=[]
            )

    @classmethod
    def validate_partial(cls, receipt: Dict[str, Any]) -> List[str]:
        """
        Validate receipt and return list of missing/invalid fields (non-raising).

        Args:
            receipt: Receipt dictionary to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        try:
            cls.validate(receipt)
            return []
        except ReceiptValidationError as e:
            errors = []
            if e.missing_fields:
                errors.extend([f"Missing field: {f}" for f in e.missing_fields])
            if str(e):
                errors.append(str(e))
            return errors


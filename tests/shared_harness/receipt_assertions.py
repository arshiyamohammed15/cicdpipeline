from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


def _value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _lookup_path(payload: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, Mapping):
            return None
        if key not in current:
            return None
        current = current[key]
    return current


def _find_first(payload: Mapping[str, Any], paths: Iterable[Sequence[str]]) -> Any:
    for path in paths:
        value = _lookup_path(payload, path)
        if _value_present(value):
            return value
    return None


def assert_enforcement_receipt_fields(
    receipt: Mapping[str, Any],
    *,
    require_correlation: bool = False,
) -> None:
    event_type = _find_first(
        receipt,
        (
            ("event_type",),
            ("type",),
            ("operation_type",),
            ("gate_id",),
        ),
    )
    assert event_type is not None, "Missing event_type/type/operation_type"

    decision = _find_first(
        receipt,
        (
            ("decision",),
            ("outcome",),
            ("metadata", "decision"),
            ("metadata", "outcome"),
            ("decision", "status"),
            ("result", "decision"),
            ("result", "outcome"),
            ("result", "status"),
        ),
    )
    assert decision is not None, "Missing decision/outcome"

    reason_code = _find_first(
        receipt,
        (
            ("reason_code",),
            ("metadata", "reason_code"),
            ("decision", "reason_code"),
            ("result", "reason_code"),
        ),
    )
    assert reason_code is not None, "Missing reason_code"

    policy_ref = _find_first(
        receipt,
        (
            ("policy_snapshot_id",),
            ("policy_version_ids",),
            ("policy_snapshot_hash",),
            ("inputs", "policy_snapshot_id"),
            ("inputs", "policy_version_ids"),
            ("inputs", "policy_snapshot_hash"),
            ("policy_schema_version",),
            ("schema_version",),
            ("result", "schema_version"),
            ("metadata", "policy_schema_version"),
            ("policy_id",),
            ("metadata", "policy_id"),
            ("policy_ref",),
            ("metadata", "policy_ref"),
            ("pinned_version",),
            ("pinned_digest",),
            ("metadata", "pinned_version"),
            ("metadata", "pinned_digest"),
        ),
    )
    assert policy_ref is not None, "Missing policy reference"

    timestamp = _find_first(
        receipt,
        (
            ("timestamp_utc",),
            ("timestamp",),
            ("metadata", "timestamp_utc"),
            ("metadata", "timestamp"),
            ("result", "timestamp"),
        ),
    )
    assert timestamp is not None, "Missing timestamp"

    if require_correlation:
        correlation = _find_first(
            receipt,
            (
                ("correlation_id",),
                ("trace_id",),
                ("request_id",),
                ("stream_id",),
                ("inputs", "request_id"),
                ("metadata", "correlation_id"),
                ("metadata", "trace_id"),
                ("metadata", "stream_id"),
            ),
        )
        assert correlation is not None, "Missing correlation_id/trace_id"

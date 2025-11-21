"""IAM, approval, and key reference utilities."""

from __future__ import annotations

from typing import Iterable, Set

from .models import ApprovalDecision, ApprovalRecord, IAMContext


class PermissionDeniedError(RuntimeError):
    """Raised when IAM checks fail."""


class IAMGuard:
    """Simple IAM guard that enforces scopes or roles."""

    def __init__(self, required_scope_prefix: str = "bdr:") -> None:
        self._prefix = required_scope_prefix

    def require(self, context: IAMContext, scope: str) -> None:
        if scope in context.scopes:
            return
        prefixed_scope = f"{self._prefix}{scope}"
        if prefixed_scope in context.scopes:
            return
        if scope in context.roles or prefixed_scope in context.roles:
            return
        msg = f"Actor {context.actor} lacks required scope/role: {scope}"
        raise PermissionDeniedError(msg)


class ApprovalPolicy:
    """Defines approval requirements for sensitive operations."""

    def __init__(self, required_roles: Iterable[str], approvals_needed: int) -> None:
        self._roles = set(required_roles)
        self._approvals_needed = approvals_needed

    def evaluate(self, approvals: Iterable[ApprovalDecision]) -> ApprovalRecord:
        approval_list = list(approvals)
        approver_roles: Set[str] = {decision.approver for decision in approval_list}
        if not approver_roles <= self._roles:
            unknown = approver_roles - self._roles
            msg = f"Approvals provided by unauthorized roles: {', '.join(sorted(unknown))}"
            raise PermissionDeniedError(msg)
        return ApprovalRecord(approvals=approval_list, required_count=self._approvals_needed)


class KeyResolver:
    """Validates encryption key references against Key & Trust metadata."""

    def __init__(self, allowed_prefixes: Iterable[str]) -> None:
        self._prefixes = tuple(allowed_prefixes)

    def validate(self, key_ref: str) -> None:
        if not key_ref.startswith(self._prefixes):
            msg = f"Key reference {key_ref} is not allowed"
            raise PermissionDeniedError(msg)


import pytest

from datetime import datetime, timezone

import pytest

from bdr.models import ApprovalDecision, IAMContext
from bdr.security import (
    ApprovalPolicy,
    IAMGuard,
    KeyResolver,
    PermissionDeniedError,
)


def test_iam_guard_accepts_matching_scope():
    guard = IAMGuard()
    context = IAMContext(actor="user", roles=["reader"], scopes=["backup:run"])
    guard.require(context, "backup:run")


def test_iam_guard_rejects_missing_scope():
    guard = IAMGuard()
    context = IAMContext(actor="user", roles=["reader"], scopes=[])
    with pytest.raises(PermissionDeniedError):
        guard.require(context, "backup:run")


def test_iam_guard_accepts_prefixed_scope():
    guard = IAMGuard()
    context = IAMContext(actor="user", roles=[], scopes=["bdr:backup:run"])
    guard.require(context, "backup:run")


def test_iam_guard_accepts_role():
    guard = IAMGuard()
    context = IAMContext(actor="user", roles=["backup:run"], scopes=[])
    guard.require(context, "backup:run")


def test_key_resolver_validates_prefix():
    resolver = KeyResolver(("kid:",))
    resolver.validate("kid:abc")
    with pytest.raises(PermissionDeniedError):
        resolver.validate("arn:aws:kms:123")


def test_approval_policy_enforces_roles():
    policy = ApprovalPolicy(required_roles={"secops", "platform"}, approvals_needed=1)
    decision = ApprovalDecision(approver="secops", approved_at=datetime.now(timezone.utc))
    assert policy.evaluate([decision]).approvals[0].approver == "secops"
    with pytest.raises(PermissionDeniedError):
        policy.evaluate([ApprovalDecision(approver="other")])


import os

import jwt
import pytest

from budgeting_rate_limiting_cost_observability.dependencies import MockM21IAM


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setenv("M35_JWT_SECRET", "test-secret")
    yield


def _token(sub: str, tenant_id: str, secret: str = "test-secret"):
    return jwt.encode({"sub": sub, "tenant_id": tenant_id, "exp": 9999999999}, secret, algorithm="HS256")


def test_verify_jwt_accepts_valid_token():
    iam = MockM21IAM()
    token = _token("user-1", "tenant-1")
    ok, claims, err = iam.verify_jwt(token)
    assert ok
    assert claims["sub"] == "user-1"
    assert claims["tenant_id"] == "tenant-1"
    assert err is None


def test_verify_jwt_rejects_bad_signature():
    iam = MockM21IAM()
    token = _token("user-1", "tenant-1", secret="wrong")
    ok, claims, err = iam.verify_jwt(token)
    assert not ok
    assert claims is None
    assert err is not None


def test_verify_jwt_rejects_missing_secret(monkeypatch):
    monkeypatch.delenv("M35_JWT_SECRET", raising=False)
    iam = MockM21IAM()
    token = _token("user-1", "tenant-1")
    ok, claims, err = iam.verify_jwt(token)
    assert not ok
    assert claims is None
    assert err == "JWT secret not configured"


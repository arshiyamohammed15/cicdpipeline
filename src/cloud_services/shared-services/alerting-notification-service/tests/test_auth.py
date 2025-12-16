import asyncio
import os

import jwt
import pytest
from starlette.requests import Request

from alerting_notification_service.dependencies import get_request_context


def _build_request(headers: dict[str, str]) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setenv("ALERTING_JWT_SECRET", "test-secret")
    yield


def _token(sub: str, tenant_id: str, secret: str = "test-secret") -> str:
    return jwt.encode({"sub": sub, "tenant_id": tenant_id}, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_get_request_context_success():
    token = _token("user-1", "tenant-1")
    req = _build_request(
        {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "tenant-1",
            "X-Actor-ID": "actor-1",
            "X-Roles": "admin",
            "X-Allow-Tenants": "tenant-1",
        }
    )
    ctx = await get_request_context(req)
    assert ctx.tenant_id == "tenant-1"
    assert ctx.token_sub == "user-1"
    assert "admin" in ctx.roles


@pytest.mark.asyncio
async def test_get_request_context_rejects_missing_auth():
    req = _build_request({"X-Tenant-ID": "tenant-1"})
    with pytest.raises(Exception):
        await get_request_context(req)


@pytest.mark.asyncio
async def test_get_request_context_rejects_tenant_mismatch():
    token = _token("user-1", "other-tenant")
    req = _build_request(
        {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "tenant-1",
        }
    )
    with pytest.raises(Exception):
        await get_request_context(req)


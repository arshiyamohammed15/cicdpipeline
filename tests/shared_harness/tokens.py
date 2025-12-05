from __future__ import annotations
"""
IAM token helpers for multi-tenant security tests.
"""


import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Dict, List, Sequence
from uuid import uuid4


@dataclass(frozen=True)
class IssuedToken:
    tenant_id: str
    user_id: str
    roles: Sequence[str]
    scopes: Sequence[str]
    expires_at: datetime
    token: str

    def to_headers(self) -> Dict[str, str]:
        return {"authorization": f"Bearer {self.token}", "x-tenant-id": self.tenant_id}


class IAMTokenFactory:
    """Mint signed tokens with varying roles/scopes."""

    def __init__(self, *, secret: str | None = None, default_ttl_minutes: int = 30) -> None:
        self._secret = secret or secrets.token_hex(32)
        self._default_ttl = default_ttl_minutes

    def issue_token(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        roles: Sequence[str] | None = None,
        scopes: Sequence[str] | None = None,
        ttl_minutes: int | None = None,
    ) -> IssuedToken:
        user = user_id or f"user-{uuid4().hex[:6]}"
        role_list = list(roles or ["data_engineer"])
        scope_list = list(scopes or ["privacy:read", "privacy:write"])
        expires = datetime.now(tz=timezone.utc) + timedelta(minutes=ttl_minutes or self._default_ttl)
        payload = {
            "tenant_id": tenant_id,
            "user_id": user,
            "roles": role_list,
            "scopes": scope_list,
            "exp": int(expires.timestamp()),
            "nonce": uuid4().hex,
        }
        token = self._sign_payload(payload)
        return IssuedToken(
            tenant_id=tenant_id,
            user_id=user,
            roles=role_list,
            scopes=scope_list,
            expires_at=expires,
            token=token,
        )

    def issue_admin_token(self, tenant_id: str) -> IssuedToken:
        return self.issue_token(
            tenant_id=tenant_id,
            roles=["tenant_admin"],
            scopes=["privacy:*", "consent:*"],
        )

    def issue_cross_tenant_token(self, source_tenant: str, target_tenant: str) -> IssuedToken:
        """Used for negative tests to simulate a compromised token with forged tenant claim."""
        return self.issue_token(
            tenant_id=target_tenant,
            user_id=f"impersonator@{source_tenant}",
            roles=["compromised"],
            scopes=["privacy:read"],
        )

    def downgrade_scopes(self, token: IssuedToken, scopes: Sequence[str]) -> IssuedToken:
        return self.issue_token(
            tenant_id=token.tenant_id,
            user_id=token.user_id,
            roles=token.roles,
            scopes=scopes,
            ttl_minutes=int((token.expires_at - datetime.now(tz=timezone.utc)).total_seconds() / 60),
        )

    def _sign_payload(self, payload: Dict[str, object]) -> str:
        serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        signature = hmac.new(self._secret.encode(), serialized, sha256).hexdigest()
        return f"{serialized.decode()}.{signature}"


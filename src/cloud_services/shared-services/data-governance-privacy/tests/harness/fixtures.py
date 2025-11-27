"""
Factories for classification payloads, consent states, and retention policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Sequence
from uuid import uuid4


@dataclass
class ClassificationPayload:
    record_id: str
    tenant_id: str
    data_class: str
    confidence: float
    attributes: Dict[str, str]

    def to_request(self) -> Dict[str, object]:
        return {
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "data_class": self.data_class,
            "confidence": self.confidence,
            "attributes": self.attributes,
        }


class ClassificationPayloadFactory:
    TAXONOMY = [
        "PII",
        "SPI",
        "PHI",
        "Financial",
        "IntellectualProperty",
        "Public",
    ]

    def build(
        self,
        *,
        tenant_id: str,
        data_class: str | None = None,
        confidence: float = 0.97,
        attributes: Dict[str, str] | None = None,
    ) -> ClassificationPayload:
        clazz = data_class or "PII"
        if clazz not in self.TAXONOMY:
            raise ValueError(f"Unsupported class {clazz}")
        record_id = f"rec-{uuid4().hex}"
        attrs = attributes or {"field": "email", "value": "masked@example.com"}
        return ClassificationPayload(
            record_id=record_id,
            tenant_id=tenant_id,
            data_class=clazz,
            confidence=confidence,
            attributes=attrs,
        )


@dataclass
class ConsentRecord:
    consent_id: str
    tenant_id: str
    actor_id: str
    scopes: Sequence[str]
    granted_at: datetime
    revoked: bool = False

    def to_request(self) -> Dict[str, object]:
        return {
            "consent_id": self.consent_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "scopes": list(self.scopes),
            "granted_at": self.granted_at.isoformat(),
            "revoked": self.revoked,
        }


class ConsentStateFactory:
    def grant(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        scopes: Sequence[str] | None = None,
        granted_at: datetime | None = None,
    ) -> ConsentRecord:
        return ConsentRecord(
            consent_id=f"consent-{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            actor_id=actor_id,
            scopes=scopes or ("purpose:research",),
            granted_at=granted_at or datetime.now(tz=timezone.utc),
            revoked=False,
        )

    def revoke(self, record: ConsentRecord, *, revoked_at: datetime | None = None) -> ConsentRecord:
        record.revoked = True
        record.granted_at = revoked_at or datetime.now(tz=timezone.utc)
        return record


@dataclass
class RetentionPolicy:
    policy_id: str
    tenant_id: str
    data_class: str
    duration_days: int
    auto_renew: bool

    def to_request(self) -> Dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "tenant_id": self.tenant_id,
            "data_class": self.data_class,
            "duration_days": self.duration_days,
            "auto_renew": self.auto_renew,
        }


class RetentionPolicyFactory:
    def build(
        self,
        *,
        tenant_id: str,
        data_class: str = "PII",
        duration_days: int = 30,
        auto_renew: bool = False,
    ) -> RetentionPolicy:
        return RetentionPolicy(
            policy_id=f"ret-{uuid4().hex[:10]}",
            tenant_id=tenant_id,
            data_class=data_class,
            duration_days=duration_days,
            auto_renew=auto_renew,
        )



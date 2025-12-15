"""
Webhook service with enhanced replay protection.

What: Webhook processing with timestamp validation and nonce/signature caching
Why: Prevent webhook replay attacks per FR-4
Reads/Writes: Database (WebhookRegistration, AdapterEvent), external provider APIs
Contracts: PRD FR-4 (Webhook Ingestion)
Risks: Replay attacks, signature verification failures
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session

try:
    from ..database.models import AdapterEvent
    from ..database.repositories import AdapterEventRepository
    from ..observability.metrics import get_metrics_registry
    from ..observability.audit import get_audit_logger
except ImportError:
    import sys
    import os
    parent_dir = os.path.join(os.path.dirname(__file__), "../..")
    parent_dir = os.path.abspath(parent_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        from integration_adapters.database.models import AdapterEvent
        from integration_adapters.database.repositories import AdapterEventRepository
        from integration_adapters.observability.metrics import get_metrics_registry
        from integration_adapters.observability.audit import get_audit_logger
    except ImportError:
        from database.models import AdapterEvent
        from database.repositories import AdapterEventRepository
        from observability.metrics import get_metrics_registry
        from observability.audit import get_audit_logger

logger = logging.getLogger(__name__)


class WebhookReplayProtection:
    """
    Replay protection for webhooks using timestamp validation and signature caching.
    
    Implements:
    - Timestamp validation (reject events older than threshold)
    - Signature/nonce caching (reject duplicate signatures within time window)
    - Idempotency key tracking
    """

    def __init__(
        self,
        session: Session,
        timestamp_tolerance_seconds: int = 300,  # 5 minutes
        signature_cache_ttl_seconds: int = 3600,  # 1 hour
    ):
        """
        Initialize replay protection.
        
        Args:
            session: Database session
            timestamp_tolerance_seconds: Maximum age of events to accept (default: 5 minutes)
            signature_cache_ttl_seconds: TTL for signature cache (default: 1 hour)
        """
        self.session = session
        self.event_repo = AdapterEventRepository(session)
        self.timestamp_tolerance = timedelta(seconds=timestamp_tolerance_seconds)
        self.signature_cache_ttl = timedelta(seconds=signature_cache_ttl_seconds)
        
        # In-memory cache for signatures (would use Redis in production)
        self._signature_cache: Dict[str, datetime] = defaultdict(lambda: datetime.min)
        
        self.metrics = get_metrics_registry()
        self.audit = get_audit_logger()

    def _compute_signature_hash(
        self, payload: bytes, headers: Dict[str, str], connection_id: UUID
    ) -> str:
        """
        Compute signature hash for replay detection.
        
        Args:
            payload: Webhook payload bytes
            headers: HTTP headers
            connection_id: Connection ID
            
        Returns:
            Signature hash string
        """
        # Combine payload, signature header, and connection_id for uniqueness
        signature_header = headers.get("X-Hub-Signature-256", "") or headers.get("X-Hub-Signature", "")
        data = f"{connection_id}:{signature_header}:{payload.hex()}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def _check_timestamp(
        self, event_timestamp: Optional[datetime], headers: Dict[str, str]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if event timestamp is within acceptable range.
        
        Args:
            event_timestamp: Event timestamp from payload
            headers: HTTP headers (may contain timestamp)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to extract timestamp from headers or payload
        if event_timestamp:
            timestamp = event_timestamp
        else:
            # Try to extract from headers (provider-specific)
            timestamp_str = headers.get("X-GitHub-Delivery") or headers.get("X-Event-Time")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()

        # Check if timestamp is too old
        now = datetime.utcnow()
        age = now - timestamp if timestamp.tzinfo is None else now.replace(tzinfo=None) - timestamp.replace(tzinfo=None)
        
        if age > self.timestamp_tolerance:
            return False, f"Event timestamp too old: {age.total_seconds()}s (max: {self.timestamp_tolerance.total_seconds()}s)"
        
        # Check if timestamp is too far in the future (clock skew protection)
        if age < -timedelta(seconds=60):  # Allow 1 minute clock skew
            return False, f"Event timestamp too far in future: {abs(age.total_seconds())}s"
        
        return True, None

    def _check_signature_cache(
        self, signature_hash: str, connection_id: UUID
    ) -> tuple[bool, Optional[str]]:
        """
        Check if signature has been seen before (replay detection).
        
        Args:
            signature_hash: Computed signature hash
            connection_id: Connection ID
            
        Returns:
            Tuple of (is_new, error_message)
        """
        cache_key = f"{connection_id}:{signature_hash}"
        
        # Check in-memory cache
        if cache_key in self._signature_cache:
            cached_time = self._signature_cache[cache_key]
            if datetime.utcnow() - cached_time < self.signature_cache_ttl:
                return False, "Duplicate signature detected (replay attack)"
            else:
                # Expired entry, remove it
                del self._signature_cache[cache_key]

        # Check database for recent events with same signature
        # (In production, would query by signature hash)
        recent_events = self.event_repo.get_recent_by_connection(
            connection_id, since=datetime.utcnow() - self.signature_cache_ttl
        )
        
        # Store signature in cache
        self._signature_cache[cache_key] = datetime.utcnow()
        
        # Clean up old cache entries (simple cleanup - would use TTL in production)
        cutoff = datetime.utcnow() - self.signature_cache_ttl
        keys_to_remove = [
            k for k, v in self._signature_cache.items()
            if v < cutoff
        ]
        for key in keys_to_remove:
            del self._signature_cache[key]

        return True, None

    def validate_webhook(
        self,
        connection_id: UUID,
        payload: bytes,
        headers: Dict[str, str],
        event_timestamp: Optional[datetime] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate webhook for replay protection.
        
        Args:
            connection_id: Connection ID
            payload: Webhook payload bytes
            headers: HTTP headers
            event_timestamp: Event timestamp from payload (optional)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check timestamp
        timestamp_valid, timestamp_error = self._check_timestamp(event_timestamp, headers)
        if not timestamp_valid:
            self.metrics.increment_webhook_error("replay_protection", connection_id)
            self.audit.log_warning(
                tenant_id="",  # Would extract from connection
                operation="webhook.replay_protection.timestamp_check",
                message=timestamp_error,
                metadata={"connection_id": str(connection_id)},
            )
            return False, timestamp_error

        # Check signature cache
        signature_hash = self._compute_signature_hash(payload, headers, connection_id)
        signature_new, signature_error = self._check_signature_cache(signature_hash, connection_id)
        if not signature_new:
            self.metrics.increment_webhook_error("replay_protection", connection_id)
            self.audit.log_warning(
                tenant_id="",  # Would extract from connection
                operation="webhook.replay_protection.signature_check",
                message=signature_error,
                metadata={"connection_id": str(connection_id)},
            )
            return False, signature_error

        return True, None

    def record_webhook_event(
        self,
        connection_id: UUID,
        provider_event_type: str,
        payload: bytes,
        headers: Dict[str, str],
    ) -> AdapterEvent:
        """
        Record webhook event in database for idempotency tracking.
        
        Args:
            connection_id: Connection ID
            provider_event_type: Provider event type
            payload: Webhook payload bytes
            headers: HTTP headers
            
        Returns:
            Created AdapterEvent record
        """
        # Store event reference (not full payload to save space)
        event = AdapterEvent(
            connection_id=connection_id,
            provider_event_type=provider_event_type,
            received_at=datetime.utcnow(),
            raw_payload_ref=None,  # Would store in object storage in production
        )
        return self.event_repo.create(event)


class WebhookService:
    """
    Webhook service with enhanced replay protection.
    
    Wraps IntegrationService.process_webhook with replay protection.
    """

    def __init__(
        self,
        integration_service,  # IntegrationService instance
        session: Session,
        timestamp_tolerance_seconds: int = 300,
        signature_cache_ttl_seconds: int = 3600,
    ):
        """
        Initialize webhook service.
        
        Args:
            integration_service: IntegrationService instance
            session: Database session
            timestamp_tolerance_seconds: Timestamp tolerance for replay protection
            signature_cache_ttl_seconds: Signature cache TTL
        """
        self.integration_service = integration_service
        self.replay_protection = WebhookReplayProtection(
            session,
            timestamp_tolerance_seconds,
            signature_cache_ttl_seconds,
        )

    def process_webhook(
        self,
        provider_id: str,
        connection_token: str,
        payload: dict,
        headers: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """
        Process webhook with replay protection.
        
        Args:
            provider_id: Provider ID
            connection_token: Connection token
            payload: Webhook payload
            headers: HTTP headers
            
        Returns:
            Tuple of (success, error_message)
        """
        # Treat token as registration_id (not raw connection_id) to reduce guessability.
        try:
            registration_id = UUID(connection_token)
        except ValueError:
            return False, "Invalid connection token"

        # Convert payload to bytes for signature computation
        import json
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Extract event timestamp from payload if available
        event_timestamp = None
        if "timestamp" in payload:
            try:
                event_timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Validate replay protection
        is_valid, error = self.replay_protection.validate_webhook(
            connection_id=registration_id,
            payload=payload_bytes,
            headers=headers,
            event_timestamp=event_timestamp,
        )
        if not is_valid:
            return False, error

        # Process webhook via integration service
        success = self.integration_service.process_webhook(
            provider_id=provider_id,
            connection_token=connection_token,
            payload=payload,
            headers=headers,
        )

        if success:
            # Record event for idempotency
            event_type = payload.get("action") or payload.get("event") or "unknown"
            self.replay_protection.record_webhook_event(
                connection_id=registration_id,
                provider_event_type=event_type,
                payload=payload_bytes,
                headers=headers,
            )

        return success, None


"""
Service layer for Key Management Service (KMS).

What: Business logic for key lifecycle, cryptographic operations, trust store management per KMS spec v0.1.0
Why: Encapsulates KMS logic, provides abstraction for route handlers, implements cryptographic operations
Reads/Writes: Reads key metadata, writes receipts, audit logs via mock dependencies (PM-7, CCP-6, CCP-1)
Contracts: KMS API contract (keys, sign, verify, encrypt, decrypt endpoints), receipt schema per spec
Risks: Security vulnerabilities if keys mishandled, performance degradation under load, key compromise
"""

import base64
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from .models import (
    KeyMetadata, AccessPolicy, CryptographicOperationReceipt, KMSContext,
    EventEnvelope, KeyGeneratedPayload, KeyRotatedPayload, KeyRevokedPayload,
    SignatureCreatedPayload, SignatureVerifiedPayload, TrustAnchorUpdatedPayload
)
from .dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane, MockM21IAM  # Legacy class names: PM-7, CCP-6, CCP-1, EPC-1
from .hsm import HSMInterface, MockHSM

logger = logging.getLogger(__name__)

# Default configuration per KMS spec
DEFAULT_KEY_ROTATION_SCHEDULE = "P90D"  # 90 days
DEFAULT_ROTATION_GRACE_PERIOD = "P7D"  # 7 days
DEFAULT_MAX_USAGE_PER_DAY = 1000
ALLOWED_ALGORITHMS = ["RS256", "EdDSA", "AES-256-GCM", "CHACHA20-POLY1305"]
DUAL_AUTHORIZATION_OPERATIONS = ["key_lifecycle", "emergency_rotation"]


class KeyLifecycleManager:
    """
    Key lifecycle manager per KMS spec section 1.

    Handles: Key generation, storage, rotation, archival, revocation, destruction.
    """

    def __init__(
        self,
        hsm: HSMInterface,
        data_plane: MockM29DataPlane
    ):
        """
        Initialize key lifecycle manager.

        Args:
            hsm: HSM interface for key operations
            data_plane: M29 data plane for metadata storage
        """
        self.hsm = hsm
        self.data_plane = data_plane

    def generate_key(
        self,
        tenant_id: str,
        environment: str,
        plane: str,
        key_type: str,
        key_usage: List[str],
        key_alias: Optional[str] = None,
        access_policy: Optional[AccessPolicy] = None
    ) -> Tuple[str, str]:
        """
        Generate a new cryptographic key per KMS spec.

        Args:
            tenant_id: Tenant identifier
            environment: Environment (dev, staging, prod)
            plane: Plane (laptop, tenant, product, shared)
            key_type: Key type (RSA-2048, Ed25519, AES-256)
            key_usage: List of usage types (sign, verify, encrypt, decrypt)
            key_alias: Optional human-readable alias
            access_policy: Optional access policy

        Returns:
            Tuple of (key_id, public_key_pem)

        Raises:
            ValueError: If key generation fails
        """
        key_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Default access policy
        if not access_policy:
            access_policy = AccessPolicy(
                allowed_modules=["M21", "M27", "M29"],  # M21=EPC-1, M27=PM-7, M29=CCP-6 (code identifiers)
                requires_approval=False,
                max_usage_per_day=DEFAULT_MAX_USAGE_PER_DAY
            )

        metadata = {
            "tenant_id": tenant_id,
            "environment": environment,
            "plane": plane,
            "key_alias": key_alias
        }

        # Generate key via HSM
        public_key_pem, private_key_handle = self.hsm.generate_key(key_type, key_id, metadata)

        if not public_key_pem or not private_key_handle:
            raise ValueError("Key generation failed")

        # Store key in HSM
        self.hsm.store_key(key_id, private_key_handle, metadata)

        # Create key metadata
        key_metadata = KeyMetadata(
            tenant_id=tenant_id,
            environment=environment,
            plane=plane,
            key_id=key_id,
            key_type=key_type,
            key_usage=key_usage,
            public_key=public_key_pem,
            key_state="active",
            created_at=now,
            valid_from=now,
            valid_until=now + timedelta(days=90),  # Default 90-day validity
            rotation_count=0,
            access_policy=access_policy
        )

        # Store metadata in M29
        metadata_dict = key_metadata.model_dump(mode='json')
        self.data_plane.store_key_metadata(key_id, metadata_dict)

        logger.info(f"Generated key {key_id} for tenant {tenant_id}")
        return key_id, public_key_pem

    def retrieve_key_metadata(self, key_id: str) -> Optional[KeyMetadata]:
        """
        Retrieve key metadata.

        Args:
            key_id: Key identifier

        Returns:
            KeyMetadata or None if not found
        """
        metadata_dict = self.data_plane.get_key_metadata(key_id)
        if metadata_dict:
            return KeyMetadata(**metadata_dict)
        return None

    def rotate_key(
        self,
        key_id: str,
        tenant_id: str,
        environment: str,
        plane: str,
        event_publisher: Optional['EventPublisher'] = None
    ) -> Tuple[str, str]:
        """
        Rotate a key per KMS spec.

        Args:
            key_id: Old key identifier
            tenant_id: Tenant identifier
            environment: Environment
            plane: Plane

        Returns:
            Tuple of (new_key_id, new_public_key_pem)

        Raises:
            ValueError: If key not found or rotation fails
        """
        old_metadata = self.retrieve_key_metadata(key_id)
        if not old_metadata:
            raise ValueError(f"Key not found: {key_id}")

        # Verify tenant isolation
        if old_metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        # Generate new key
        new_key_id, new_public_key = self.generate_key(
            tenant_id=tenant_id,
            environment=environment,
            plane=plane,
            key_type=old_metadata.key_type,
            key_usage=old_metadata.key_usage,
            access_policy=old_metadata.access_policy
        )

        # Update old key state
        old_metadata.key_state = "pending_rotation"
        metadata_dict = old_metadata.model_dump(mode='json')
        self.data_plane.store_key_metadata(key_id, metadata_dict)

        # Publish key_rotated event per KMS spec
        if event_publisher:
            payload = {
                "old_key_id": key_id,
                "new_key_id": new_key_id,
                "rotation_ts": datetime.utcnow().isoformat()
            }
            event_publisher.publish_event(
                "key_rotated",
                tenant_id,
                environment,
                plane,
                payload
            )

        logger.info(f"Rotated key {key_id} to {new_key_id}")
        return new_key_id, new_public_key

    def revoke_key(
        self,
        key_id: str,
        tenant_id: str,
        revocation_reason: str,
        environment: Optional[str] = None,
        plane: Optional[str] = None,
        event_publisher: Optional['EventPublisher'] = None
    ) -> bool:
        """
        Revoke a key per KMS spec.

        Args:
            key_id: Key identifier
            tenant_id: Tenant identifier
            revocation_reason: Reason for revocation (compromised, retired, policy_violation)

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If key not found
        """
        metadata = self.retrieve_key_metadata(key_id)
        if not metadata:
            raise ValueError(f"Key not found: {key_id}")

        if metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        metadata.key_state = "destroyed"
        metadata.valid_until = datetime.utcnow()

        metadata_dict = metadata.model_dump(mode='json')
        metadata_dict['revocation_reason'] = revocation_reason
        metadata_dict['revoked_at'] = datetime.utcnow().isoformat()

        self.data_plane.store_key_metadata(key_id, metadata_dict)

        # Publish key_revoked event per KMS spec
        if event_publisher and environment and plane:
            payload = {
                "key_id": key_id,
                "revocation_reason": revocation_reason,
                "revoked_at": datetime.utcnow().isoformat()
            }
            event_publisher.publish_event(
                "key_revoked",
                tenant_id,
                environment,
                plane,
                payload
            )

        logger.info(f"Revoked key {key_id} for reason: {revocation_reason}")
        return True

    def archive_key(self, key_id: str, tenant_id: str) -> bool:
        """
        Archive a key for historical decryption.

        Args:
            key_id: Key identifier
            tenant_id: Tenant identifier

        Returns:
            True if successful, False otherwise
        """
        metadata = self.retrieve_key_metadata(key_id)
        if not metadata:
            return False

        if metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        metadata.key_state = "archived"
        metadata_dict = metadata.model_dump(mode='json')
        self.data_plane.store_key_metadata(key_id, metadata_dict)

        logger.info(f"Archived key {key_id}")
        return True


class CryptographicOperations:
    """
    Cryptographic operations service per KMS spec section 3.

    Handles: Signing, verification, encryption, decryption, key derivation, random generation.
    """

    def __init__(
        self,
        hsm: HSMInterface,
        lifecycle_manager: KeyLifecycleManager
    ):
        """
        Initialize cryptographic operations service.

        Args:
            hsm: HSM interface for cryptographic operations
            lifecycle_manager: Key lifecycle manager for key retrieval
        """
        self.hsm = hsm
        self.lifecycle_manager = lifecycle_manager

    def sign_data(
        self,
        key_id: str,
        data: bytes,
        algorithm: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Sign data per KMS spec.

        Args:
            key_id: Key identifier
            data: Data to sign
            algorithm: Optional algorithm (RS256, EdDSA), defaults based on key_type
            tenant_id: Tenant identifier for validation

        Returns:
            Tuple of (signature_bytes, algorithm_used)

        Raises:
            ValueError: If signing fails
        """
        metadata = self.lifecycle_manager.retrieve_key_metadata(key_id)
        if not metadata:
            raise ValueError(f"Key not found: {key_id}")

        if tenant_id and metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        if metadata.key_state != "active":
            raise ValueError(f"Key not active: {metadata.key_state}")

        if "sign" not in metadata.key_usage:
            raise ValueError("Key not authorized for signing")

        # Determine algorithm
        if not algorithm:
            if metadata.key_type == "RSA-2048":
                algorithm = "RS256"
            elif metadata.key_type == "Ed25519":
                algorithm = "EdDSA"
            else:
                raise ValueError(f"Cannot sign with key type: {metadata.key_type}")

        # Sign via HSM
        signature = self.hsm.sign_data(key_id, data, algorithm)
        if not signature:
            raise ValueError("Signing failed")

        return signature, algorithm

    def verify_signature(
        self,
        key_id: str,
        data: bytes,
        signature: bytes,
        algorithm: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verify signature per KMS spec.

        Args:
            key_id: Key identifier
            data: Data that was signed
            signature: Signature bytes
            algorithm: Optional algorithm (RS256, EdDSA), defaults based on key_type
            tenant_id: Tenant identifier for validation

        Returns:
            Tuple of (is_valid, algorithm_used)

        Raises:
            ValueError: If verification fails
        """
        metadata = self.lifecycle_manager.retrieve_key_metadata(key_id)
        if not metadata:
            raise ValueError(f"Key not found: {key_id}")

        if tenant_id and metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        if "verify" not in metadata.key_usage:
            raise ValueError("Key not authorized for verification")

        # Determine algorithm
        if not algorithm:
            if metadata.key_type == "RSA-2048":
                algorithm = "RS256"
            elif metadata.key_type == "Ed25519":
                algorithm = "EdDSA"
            else:
                raise ValueError(f"Cannot verify with key type: {metadata.key_type}")

        # For verification, we need the public key
        # In a real implementation, we'd verify using the public key
        # For now, we'll use a mock verification
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.backends import default_backend

            public_key_pem = metadata.public_key

            if algorithm == "RS256":
                from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode(),
                    backend=default_backend()
                )
                public_key.verify(
                    signature,
                    data,
                    padding=rsa_padding.PSS(
                        mgf=rsa_padding.MGF1(hashes.SHA256()),
                        salt_length=rsa_padding.PSS.MAX_LENGTH
                    ),
                    algorithm=hashes.SHA256()
                )
                return True, algorithm

            elif algorithm == "EdDSA":
                # Ed25519 public key verification
                public_key_bytes = base64.b64decode(public_key_pem)
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key.verify(signature, data)
                return True, algorithm

            else:
                return False, algorithm

        except Exception as exc:
            logger.error(f"Verification failed: {exc}")
            return False, algorithm

    def encrypt_data(
        self,
        key_id: str,
        plaintext: bytes,
        algorithm: Optional[str] = None,
        aad: Optional[bytes] = None,
        tenant_id: Optional[str] = None
    ) -> Tuple[bytes, bytes, str]:
        """
        Encrypt data per KMS spec.

        Args:
            key_id: Key identifier
            plaintext: Plaintext to encrypt
            algorithm: Optional algorithm (AES-256-GCM, CHACHA20-POLY1305), defaults based on key_type
            aad: Optional additional authenticated data
            tenant_id: Tenant identifier for validation

        Returns:
            Tuple of (ciphertext, iv, algorithm_used)

        Raises:
            ValueError: If encryption fails
        """
        metadata = self.lifecycle_manager.retrieve_key_metadata(key_id)
        if not metadata:
            raise ValueError(f"Key not found: {key_id}")

        if tenant_id and metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        if metadata.key_state != "active":
            raise ValueError(f"Key not active: {metadata.key_state}")

        if "encrypt" not in metadata.key_usage:
            raise ValueError("Key not authorized for encryption")

        # Determine algorithm
        if not algorithm:
            if metadata.key_type == "AES-256":
                algorithm = "AES-256-GCM"
            else:
                raise ValueError(f"Cannot encrypt with key type: {metadata.key_type}")

        # Encrypt via HSM
        result = self.hsm.encrypt_data(key_id, plaintext, algorithm, None, aad)
        if not result:
            raise ValueError("Encryption failed")

        ciphertext, iv = result
        return ciphertext, iv, algorithm

    def decrypt_data(
        self,
        key_id: str,
        ciphertext: bytes,
        iv: bytes,
        algorithm: Optional[str] = None,
        aad: Optional[bytes] = None,
        tenant_id: Optional[str] = None
    ) -> bytes:
        """
        Decrypt data per KMS spec.

        Args:
            key_id: Key identifier
            ciphertext: Ciphertext to decrypt
            iv: Initialization vector
            algorithm: Optional algorithm (AES-256-GCM, CHACHA20-POLY1305)
            aad: Optional additional authenticated data
            tenant_id: Tenant identifier for validation

        Returns:
            Plaintext bytes

        Raises:
            ValueError: If decryption fails
        """
        metadata = self.lifecycle_manager.retrieve_key_metadata(key_id)
        if not metadata:
            raise ValueError(f"Key not found: {key_id}")

        if tenant_id and metadata.tenant_id != tenant_id:
            raise ValueError("Tenant mismatch")

        if "decrypt" not in metadata.key_usage:
            raise ValueError("Key not authorized for decryption")

        # Determine algorithm if not provided
        if not algorithm:
            if metadata.key_type == "AES-256":
                algorithm = "AES-256-GCM"
            else:
                raise ValueError(f"Cannot decrypt with key type: {metadata.key_type}")

        # Decrypt via HSM
        plaintext = self.hsm.decrypt_data(key_id, ciphertext, algorithm, iv, aad)
        if not plaintext:
            raise ValueError("Decryption failed")

        return plaintext


class PolicyEnforcer:
    """
    Policy enforcer per KMS spec section 4.

    Handles: Access policy evaluation, dual-authorization, compliance monitoring, violation detection.
    """

    def __init__(self, data_plane: MockM29DataPlane):
        """
        Initialize policy enforcer.

        Args:
            data_plane: M29 data plane for usage tracking
        """
        self.data_plane = data_plane

    def evaluate_access_policy(
        self,
        key_metadata: KeyMetadata,
        module_id: str,
        operation: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate access policy for a key operation.

        Args:
            key_metadata: Key metadata
            module_id: Requesting module ID
            operation: Operation type (sign, verify, encrypt, decrypt, key_lifecycle)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check if module is allowed
        if module_id not in key_metadata.access_policy.allowed_modules:
            return False, f"Module {module_id} not allowed to use key"

        # Check usage limits
        today = datetime.utcnow().strftime("%Y-%m-%d")
        usage_count = self.data_plane.get_usage_count(key_metadata.key_id, today)

        if usage_count >= key_metadata.access_policy.max_usage_per_day:
            return False, f"Daily usage limit exceeded: {usage_count}/{key_metadata.access_policy.max_usage_per_day}"

        # Check key state
        if key_metadata.key_state != "active" and operation in ["sign", "verify", "encrypt", "decrypt"]:
            return False, f"Key not active: {key_metadata.key_state}"

        return True, None

    def check_dual_authorization(
        self,
        operation: str,
        approval_token: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check dual-authorization requirement.

        Args:
            operation: Operation type
            approval_token: Optional approval token

        Returns:
            Tuple of (is_authorized, error_message)
        """
        if operation in DUAL_AUTHORIZATION_OPERATIONS:
            if not approval_token:
                return False, "Dual authorization required for this operation"
            # In production, verify approval_token signature
            # For now, just check it exists
            if not approval_token or len(approval_token) < 10:
                return False, "Invalid approval token"
        return True, None

    def increment_usage(self, key_id: str) -> None:
        """
        Increment usage count for a key.

        Args:
            key_id: Key identifier
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.data_plane.increment_usage(key_id, today)


class EventPublisher:
    """
    Event publisher per KMS spec Event Schemas section.

    Publishes events: key_generated, key_rotated, key_revoked, signature_created, signature_verified, trust_anchor_updated.
    """

    def __init__(self):
        """Initialize event publisher."""
        self.events: List[EventEnvelope] = []

    def publish_event(
        self,
        event_type: str,
        tenant_id: str,
        environment: str,
        plane: str,
        payload: Dict[str, Any]
    ) -> str:
        """
        Publish an event with common envelope.

        Args:
            event_type: Event type
            tenant_id: Tenant identifier
            environment: Environment
            plane: Plane
            payload: Event-specific payload

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        event = EventEnvelope(
            event_id=event_id,
            event_type=event_type,
            ts=datetime.utcnow(),
            tenant_id=tenant_id,
            environment=environment,
            plane=plane,
            source_module="EPC-11",
            payload=payload
        )
        self.events.append(event)
        logger.info(f"Published event {event_type} with ID {event_id}")
        return event_id


class ReceiptGenerator:
    """
    Receipt generator per KMS spec Data Schemas section.

    Generates cryptographic operation receipts signed via M27.
    """

    def __init__(self, evidence_ledger: MockM27EvidenceLedger):
        """
        Initialize receipt generator.

        Args:
            evidence_ledger: M27 evidence ledger for receipt signing
        """
        self.evidence_ledger = evidence_ledger

    def generate_receipt(
        self,
        tenant_id: str,
        environment: str,
        plane: str,
        operation: str,
        kms_context: KMSContext,
        requesting_module: str
    ) -> CryptographicOperationReceipt:
        """
        Generate a cryptographic operation receipt.

        Args:
            tenant_id: Tenant identifier
            environment: Environment
            plane: Plane
            operation: Operation type
            kms_context: KMS operation context
            requesting_module: Requesting module ID

        Returns:
            CryptographicOperationReceipt
        """
        receipt_id = str(uuid.uuid4())
        receipt = CryptographicOperationReceipt(
            receipt_id=receipt_id,
            ts=datetime.utcnow(),
            tenant_id=tenant_id,
            environment=environment,
            plane=plane,
            module="KMS",
            operation=operation,
            kms_context=kms_context,
            requesting_module=requesting_module
        )

        # Sign receipt via M27
        receipt_dict = receipt.model_dump(mode='json', exclude={'signature'})
        signature = self.evidence_ledger.sign_receipt(receipt_dict)
        receipt.signature = signature

        # Store receipt via M27
        self.evidence_ledger.store_receipt(receipt_id, receipt_dict)

        return receipt


class KMSService:
    """
    Main KMS service orchestrator.

    Integrates all components: key lifecycle, cryptographic operations, policy enforcement, events, receipts.
    """

    def __init__(
        self,
        hsm: Optional[HSMInterface] = None,
        evidence_ledger: Optional[MockM27EvidenceLedger] = None,
        data_plane: Optional[MockM29DataPlane] = None,
        trust_plane: Optional[MockM32TrustPlane] = None,
        iam: Optional[MockM21IAM] = None
    ):
        """
        Initialize KMS service.

        Args:
            hsm: HSM interface (defaults to MockHSM)
            evidence_ledger: PM-7 (ERIS) evidence ledger (defaults to MockM27EvidenceLedger)
            data_plane: CCP-6 (Data & Memory Plane) data plane (defaults to MockM29DataPlane)
            trust_plane: CCP-1 (Identity & Trust Plane) trust plane (defaults to MockM32TrustPlane)
            iam: EPC-1 (Identity & Access Management) IAM (defaults to MockM21IAM)
        """
        self.hsm = hsm or MockHSM()
        self.evidence_ledger = evidence_ledger or MockM27EvidenceLedger()
        self.data_plane = data_plane or MockM29DataPlane()
        self.trust_plane = trust_plane or MockM32TrustPlane()
        self.iam = iam or MockM21IAM()

        self.lifecycle_manager = KeyLifecycleManager(self.hsm, self.data_plane)
        self.crypto_ops = CryptographicOperations(self.hsm, self.lifecycle_manager)
        self.policy_enforcer = PolicyEnforcer(self.data_plane)
        self.trust_store_manager = TrustStoreManager(self.trust_plane)
        self.event_publisher = EventPublisher()
        self.receipt_generator = ReceiptGenerator(self.evidence_ledger)

        self.metrics = {
            "key_generation_count": 0,
            "signing_count": 0,
            "verification_count": 0,
            "encryption_count": 0,
            "decryption_count": 0,
            "key_generation_latencies": [],
            "signing_latencies": [],
            "verification_latencies": [],
            "encryption_latencies": [],
            "decryption_latencies": [],
            "request_errors": {},  # error_code -> count
            "key_counts": {}  # (key_type, key_state) -> count
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Metrics dictionary
        """
        def avg_latency(latencies: List[float]) -> float:
            if not latencies:
                return 0.0
            return sum(latencies[-100:]) / len(latencies[-100:])

        # Update key counts from data plane
        self._update_key_counts()

        return {
            "key_generation_count": self.metrics["key_generation_count"],
            "signing_count": self.metrics["signing_count"],
            "verification_count": self.metrics["verification_count"],
            "encryption_count": self.metrics["encryption_count"],
            "decryption_count": self.metrics["decryption_count"],
            "average_key_generation_latency_ms": avg_latency(self.metrics["key_generation_latencies"]),
            "average_signing_latency_ms": avg_latency(self.metrics["signing_latencies"]),
            "average_verification_latency_ms": avg_latency(self.metrics["verification_latencies"]),
            "average_encryption_latency_ms": avg_latency(self.metrics["encryption_latencies"]),
            "average_decryption_latency_ms": avg_latency(self.metrics["decryption_latencies"]),
            "request_errors": self.metrics["request_errors"],
            "key_counts": self.metrics["key_counts"]
        }

    def _update_key_counts(self) -> None:
        """
        Update key counts by key_type and key_state from data plane.
        """
        key_counts: Dict[Tuple[str, str], int] = {}

        try:
            all_keys = self.data_plane.list_keys()
            for key_id in all_keys:
                metadata_dict = self.data_plane.get_key_metadata(key_id)
                if metadata_dict:
                    key_type = metadata_dict.get("key_type", "unknown")
                    key_state = metadata_dict.get("key_state", "unknown")
                    key = (key_type, key_state)
                    key_counts[key] = key_counts.get(key, 0) + 1
        except Exception as exc:
            logger.error(f"Error updating key counts: {exc}")

        self.metrics["key_counts"] = {f"{k[0]}_{k[1]}": v for k, v in key_counts.items()}

    def increment_error_count(self, error_code: str) -> None:
        """
        Increment error count for a specific error code.

        Args:
            error_code: Error code (e.g., "INVALID_REQUEST", "KEY_NOT_FOUND")
        """
        self.metrics["request_errors"][error_code] = self.metrics["request_errors"].get(error_code, 0) + 1


class TrustStoreManager:
    """
    Trust store manager per KMS spec section 2.

    Handles: Certificate ingestion, chain validation, revocation checking, trust distribution, enrollment.
    """

    def __init__(self, trust_plane: MockM32TrustPlane):
        """
        Initialize trust store manager.

        Args:
            trust_plane: M32 trust plane for certificate validation
        """
        self.trust_plane = trust_plane

    def ingest_certificate(
        self,
        certificate: bytes,
        anchor_type: str,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        plane: Optional[str] = None,
        event_publisher: Optional['EventPublisher'] = None
    ) -> str:
        """
        Ingest and validate a certificate.

        Args:
            certificate: Certificate bytes
            anchor_type: Anchor type (internal_ca, external_ca, root)
            tenant_id: Optional tenant identifier

        Returns:
            Trust anchor identifier

        Raises:
            ValueError: If certificate validation fails
        """
        is_valid, error, identity_info = self.trust_plane.validate_certificate(certificate)
        if not is_valid:
            raise ValueError(f"Certificate validation failed: {error}")

        anchor_id = str(uuid.uuid4())
        anchor_data = {
            "certificate": certificate,
            "type": anchor_type,
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat()
        }

        self.trust_plane.add_trust_anchor(anchor_id, anchor_data)

        # Publish trust_anchor_updated event per KMS spec
        if event_publisher and tenant_id and environment and plane:
            payload = {
                "trust_anchor_id": anchor_id,
                "anchor_type": anchor_type,
                "version": "1.0"
            }
            event_publisher.publish_event(
                "trust_anchor_updated",
                tenant_id,
                environment,
                plane,
                payload
            )

        logger.info(f"Ingested certificate as trust anchor {anchor_id}")
        return anchor_id

    def validate_chain(
        self,
        certificate: bytes,
        chain: List[bytes]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate X.509 certificate chain.

        Args:
            certificate: Certificate to validate
            chain: Certificate chain

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Mock implementation - in production would validate X.509 chain
        is_valid, error, _ = self.trust_plane.validate_certificate(certificate)
        return is_valid, error

    def check_revocation(self, certificate: bytes) -> Tuple[bool, Optional[str]]:
        """
        Check certificate revocation status.

        Args:
            certificate: Certificate to check

        Returns:
            Tuple of (is_revoked, error_message)
        """
        # Check if certificate is in revoked list
        is_valid, error, _ = self.trust_plane.validate_certificate(certificate)
        if not is_valid:
            return True, error
        return False, None

    def distribute_trust_anchor(
        self,
        anchor_id: str,
        planes: List[str]
    ) -> bool:
        """
        Distribute trust anchor to specified planes.

        Args:
            anchor_id: Trust anchor identifier
            planes: List of planes to distribute to

        Returns:
            True if successful, False otherwise
        """
        # Mock implementation - in production would distribute to planes
        logger.info(f"Distributed trust anchor {anchor_id} to planes: {planes}")
        return True

    def enroll_certificate(
        self,
        csr: bytes,
        tenant_id: str,
        environment: str
    ) -> bytes:
        """
        Enroll a certificate for a service/module.

        Args:
            csr: Certificate signing request
            tenant_id: Tenant identifier
            environment: Environment

        Returns:
            Certificate bytes

        Raises:
            ValueError: If enrollment fails
        """
        # Mock implementation - in production would sign CSR with internal CA
        certificate = b"mock-certificate-" + csr[:16]
        logger.info(f"Enrolled certificate for tenant {tenant_id} in {environment}")
        return certificate

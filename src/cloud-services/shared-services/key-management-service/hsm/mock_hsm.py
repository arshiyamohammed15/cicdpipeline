"""
Mock HSM implementation for development and testing.

What: Mock HSM implementation that stores keys in memory
Why: Enables development and testing without hardware HSM
Reads/Writes: In-memory key storage (no file I/O)
Contracts: HSMInterface contract
Risks: Keys stored in memory, not suitable for production
"""

import base64
import hashlib
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, padding
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography library not available, using mock implementations")

from .interface import HSMInterface

logger = logging.getLogger(__name__)


class MockHSM(HSMInterface):
    """
    Mock HSM implementation for development and testing.

    Stores keys in memory. NOT suitable for production.
    """

    def __init__(self):
        """Initialize mock HSM with in-memory key storage."""
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.available = True

    def generate_key(
        self,
        key_type: str,
        key_id: str,
        metadata: Dict[str, Any]
    ) -> Tuple[str, Optional[bytes]]:
        """
        Generate a cryptographic key.

        Args:
            key_type: Key type (RSA-2048, Ed25519, AES-256)
            key_id: Key identifier
            metadata: Key metadata

        Returns:
            Tuple of (public_key_pem, private_key_handle)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Mock implementation without cryptography library
            public_key_pem = f"-----BEGIN MOCK PUBLIC KEY-----\n{key_id}\n-----END MOCK PUBLIC KEY-----"
            private_key_handle = key_id.encode()
            entry = {
                "key_type": key_type,
                "private_key": private_key_handle,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
            self.keys[key_id] = entry
            return public_key_pem, private_key_handle

        try:
            private_key_obj = None

            if key_type == "RSA-2048":
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                private_key_obj = private_key
                public_key = private_key.public_key()
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode('utf-8')
                private_key_der = private_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                private_key_handle = base64.b64encode(private_key_der)

            elif key_type == "Ed25519":
                private_key = ed25519.Ed25519PrivateKey.generate()
                private_key_obj = private_key
                public_key = private_key.public_key()
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                public_key_pem = base64.b64encode(public_key_pem).decode('utf-8')
                private_key_raw = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                private_key_handle = base64.b64encode(private_key_raw)

            elif key_type == "AES-256":
                # Generate 256-bit (32-byte) key
                import os
                key_material = os.urandom(32)
                public_key_pem = base64.b64encode(key_material).decode('utf-8')
                private_key_handle = base64.b64encode(key_material)

            else:
                raise ValueError(f"Unsupported key type: {key_type}")

            entry = {
                "key_type": key_type,
                "private_key": private_key_handle,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            }
            if private_key_obj is not None:
                entry["private_key_obj"] = private_key_obj

            self.keys[key_id] = entry

            return public_key_pem, private_key_handle

        except Exception as exc:
            logger.error(f"Key generation failed: {exc}")
            return "", None

    def store_key(
        self,
        key_id: str,
        private_key_handle: bytes,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store a private key in HSM.

        Args:
            key_id: Key identifier
            private_key_handle: Private key handle
            metadata: Key metadata

        Returns:
            True if successful, False otherwise
        """
        # Preserve existing key_type if key already exists (from generate_key)
        existing_key = self.keys.get(key_id, {})
        key_type = existing_key.get("key_type")

        self.keys[key_id] = {
            "private_key": private_key_handle,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat()
        }

        # Preserve key_type and cached objects if they were set during generate_key
        if key_type:
            self.keys[key_id]["key_type"] = key_type
        cached_private_key = existing_key.get("private_key_obj")
        if cached_private_key is not None:
            self.keys[key_id]["private_key_obj"] = cached_private_key

        return True

    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """
        Retrieve a private key handle from HSM.

        Args:
            key_id: Key identifier

        Returns:
            Private key handle or None if not found
        """
        key_data = self.keys.get(key_id)
        if key_data:
            return key_data.get("private_key")
        return None

    def sign_data(
        self,
        key_id: str,
        data: bytes,
        algorithm: str
    ) -> Optional[bytes]:
        """
        Sign data using a key stored in HSM.

        Args:
            key_id: Key identifier
            data: Data to sign
            algorithm: Signing algorithm (RS256, EdDSA)

        Returns:
            Signature bytes or None if failed
        """
        key_data = self.keys.get(key_id)
        if not key_data:
            return None

        if not CRYPTOGRAPHY_AVAILABLE:
            # Mock signature
            signature = hashlib.sha256(data + key_id.encode()).digest()
            return signature

        try:
            key_type = key_data.get("key_type")
            private_key = key_data.get("private_key_obj")
            private_key_handle = key_data.get("private_key")
            if private_key is None and private_key_handle:
                if key_type == "RSA-2048":
                    private_key_der = base64.b64decode(private_key_handle)
                    private_key = serialization.load_der_private_key(
                        private_key_der,
                        password=None,
                        backend=default_backend()
                    )
                    key_data["private_key_obj"] = private_key
                elif key_type == "Ed25519":
                    private_key_raw = base64.b64decode(private_key_handle)
                    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_raw)
                    key_data["private_key_obj"] = private_key

            if private_key is None and not private_key_handle:
                return None

            if algorithm == "RS256" and key_type == "RSA-2048":
                signature = private_key.sign(
                    data,
                    padding=padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    algorithm=hashes.SHA256()
                )
                return signature

            elif algorithm == "EdDSA" and key_type == "Ed25519":
                signature = private_key.sign(data)
                return signature

            else:
                logger.error(f"Unsupported algorithm/key_type combination: {algorithm}/{key_type}")
                return None

        except Exception as exc:
            logger.error(f"Signing failed: {exc}")
            return None

    def encrypt_data(
        self,
        key_id: str,
        plaintext: bytes,
        algorithm: str,
        iv: Optional[bytes] = None,
        aad: Optional[bytes] = None
    ) -> Optional[Tuple[bytes, bytes]]:
        """
        Encrypt data using a key stored in HSM.

        Args:
            key_id: Key identifier
            plaintext: Plaintext to encrypt
            algorithm: Encryption algorithm (AES-256-GCM, CHACHA20-POLY1305)
            iv: Optional initialization vector
            aad: Optional additional authenticated data

        Returns:
            Tuple of (ciphertext, iv) or None if failed
        """
        key_data = self.keys.get(key_id)
        if not key_data:
            return None

        if not CRYPTOGRAPHY_AVAILABLE:
            # Mock encryption
            if not iv:
                import os
                iv = os.urandom(12)
            ciphertext = hashlib.sha256(plaintext + key_id.encode()).digest()
            return ciphertext, iv

        try:
            private_key_handle = key_data.get("private_key")
            if not private_key_handle:
                return None

            key_material = base64.b64decode(private_key_handle)

            if algorithm == "AES-256-GCM":
                if not iv:
                    import os
                    iv = os.urandom(12)
                aesgcm = AESGCM(key_material)
                ciphertext = aesgcm.encrypt(iv, plaintext, aad)
                return ciphertext, iv

            elif algorithm == "CHACHA20-POLY1305":
                if not iv:
                    import os
                    iv = os.urandom(12)
                chacha = ChaCha20Poly1305(key_material)
                ciphertext = chacha.encrypt(iv, plaintext, aad)
                return ciphertext, iv

            else:
                logger.error(f"Unsupported algorithm: {algorithm}")
                return None

        except Exception as exc:
            logger.error(f"Encryption failed: {exc}")
            return None

    def decrypt_data(
        self,
        key_id: str,
        ciphertext: bytes,
        algorithm: str,
        iv: bytes,
        aad: Optional[bytes] = None
    ) -> Optional[bytes]:
        """
        Decrypt data using a key stored in HSM.

        Args:
            key_id: Key identifier
            ciphertext: Ciphertext to decrypt
            algorithm: Encryption algorithm (AES-256-GCM, CHACHA20-POLY1305)
            iv: Initialization vector
            aad: Optional additional authenticated data

        Returns:
            Plaintext bytes or None if failed
        """
        key_data = self.keys.get(key_id)
        if not key_data:
            return None

        if not CRYPTOGRAPHY_AVAILABLE:
            # Mock decryption - just return mock data
            return b"mock_decrypted_data"

        try:
            private_key_handle = key_data.get("private_key")
            if not private_key_handle:
                return None

            key_material = base64.b64decode(private_key_handle)

            if algorithm == "AES-256-GCM":
                aesgcm = AESGCM(key_material)
                plaintext = aesgcm.decrypt(iv, ciphertext, aad)
                return plaintext

            elif algorithm == "CHACHA20-POLY1305":
                chacha = ChaCha20Poly1305(key_material)
                plaintext = chacha.decrypt(iv, ciphertext, aad)
                return plaintext

            else:
                logger.error(f"Unsupported algorithm: {algorithm}")
                return None

        except Exception as exc:
            logger.error(f"Decryption failed: {exc}")
            return None

    def delete_key(self, key_id: str) -> bool:
        """
        Delete a key from HSM.

        Args:
            key_id: Key identifier

        Returns:
            True if successful, False otherwise
        """
        if key_id in self.keys:
            del self.keys[key_id]
            return True
        return False

    def is_available(self) -> bool:
        """
        Check if HSM is available.

        Returns:
            True if HSM is available, False otherwise
        """
        return self.available

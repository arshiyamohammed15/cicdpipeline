"""
HSM interface abstract base class.

What: Abstract interface for HSM operations
Why: Enables multiple HSM implementations (mock, PKCS#11, TPM)
Reads/Writes: HSM operations (no file I/O)
Contracts: HSMInterface contract
Risks: Interface changes require all implementations to update
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any


class HSMInterface(ABC):
    """
    Abstract interface for Hardware Security Module operations.

    Per KMS spec: FIPS 140-3 Level 3 validated HSM support.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
            private_key_handle: Private key handle from generate_key
            metadata: Key metadata

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """
        Retrieve a private key handle from HSM.

        Args:
            key_id: Key identifier

        Returns:
            Private key handle or None if not found
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        """
        Delete a key from HSM.

        Args:
            key_id: Key identifier

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if HSM is available.

        Returns:
            True if HSM is available, False otherwise
        """
        pass

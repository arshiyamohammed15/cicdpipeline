"""
HSM abstraction layer for Key Management Service.

What: Abstract interface and implementations for Hardware Security Module operations
Why: Enables testability and supports multiple HSM backends (mock, PKCS#11, TPM)
Reads/Writes: HSM operations (key generation, storage, signing, encryption)
Contracts: HSMInterface abstract base class
Risks: HSM unavailability, key material exposure if not properly abstracted
"""

from .interface import HSMInterface
from .mock_hsm import MockHSM

__all__ = ["HSMInterface", "MockHSM"]

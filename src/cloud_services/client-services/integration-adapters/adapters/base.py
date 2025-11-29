"""
Base adapter interface (SPI) for Integration Adapters Module.

What: Abstract base class defining adapter contract per FR-14
Why: Unified interface for all provider adapters
Reads/Writes: Provider APIs via HTTP
Contracts: PRD FR-14 (Integration Adapter SDK / SPI)
Risks: Adapter implementation errors, provider API changes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from ..models import NormalisedActionCreate, NormalisedActionResponse
except ImportError:
    # Fallback for direct imports (e.g., in tests)
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from models import NormalisedActionCreate, NormalisedActionResponse


class BaseAdapter(ABC):
    """
    Abstract base class for all provider adapters.
    
    All adapters must implement this interface to be registered and used.
    """

    def __init__(self, provider_id: str, connection_id: UUID, tenant_id: str):
        """
        Initialize adapter.
        
        Args:
            provider_id: Provider identifier (e.g., "github", "jira")
            connection_id: Integration connection ID
            tenant_id: Tenant ID
        """
        self.provider_id = provider_id
        self.connection_id = connection_id
        self.tenant_id = tenant_id

    @abstractmethod
    def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from provider.
        
        Args:
            payload: Webhook payload
            headers: HTTP headers (for signature verification)
            
        Returns:
            Dict with event data ready for SignalEnvelope transformation
            
        Raises:
            ValueError: If webhook signature is invalid
            ValueError: If webhook payload is malformed
        """
        pass

    @abstractmethod
    def poll_events(
        self, cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Poll provider API for new events.
        
        Args:
            cursor: Optional cursor position from last poll
            
        Returns:
            Tuple of (events, new_cursor)
            
        Raises:
            Exception: If polling fails
        """
        pass

    @abstractmethod
    def execute_action(
        self, action: NormalisedActionCreate
    ) -> NormalisedActionResponse:
        """
        Execute outbound action on provider.
        
        Args:
            action: Normalised action to execute
            
        Returns:
            NormalisedActionResponse with execution result
            
        Raises:
            Exception: If action execution fails
        """
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """
        Verify connection to provider (test API call).
        
        Returns:
            True if connection is valid, False otherwise
            
        Raises:
            Exception: If verification fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get adapter capabilities.
        
        Returns:
            Dict with capability flags:
            - webhook_supported: bool
            - polling_supported: bool
            - outbound_actions_supported: bool
        """
        pass

    def get_provider_id(self) -> str:
        """Get provider ID."""
        return self.provider_id

    def get_connection_id(self) -> UUID:
        """Get connection ID."""
        return self.connection_id

    def get_tenant_id(self) -> str:
        """Get tenant ID."""
        return self.tenant_id


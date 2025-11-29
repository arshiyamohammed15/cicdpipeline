"""
Adapter registry for Integration Adapters Module.

What: Registry for managing and retrieving adapters by provider_id per FR-14
Why: Centralized adapter management and capability querying
Reads/Writes: Adapter instances in memory
Contracts: PRD FR-14 (Integration Adapter SDK / SPI)
Risks: Adapter registration errors, version conflicts
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type
from uuid import UUID

try:
    from ..adapters.base import BaseAdapter
except ImportError:
    # Fallback for direct imports (e.g., in tests)
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from adapters.base import BaseAdapter


class AdapterRegistry:
    """
    Registry for managing adapters.
    
    Maintains adapter classes and instances by provider_id.
    """

    def __init__(self):
        """Initialize adapter registry."""
        self._adapter_classes: Dict[str, Type[BaseAdapter]] = {}
        self._adapter_instances: Dict[str, Dict[UUID, BaseAdapter]] = {}

    def register_adapter(
        self, provider_id: str, adapter_class: Type[BaseAdapter]
    ) -> None:
        """
        Register an adapter class for a provider.
        
        Args:
            provider_id: Provider identifier
            adapter_class: Adapter class (must inherit from BaseAdapter)
            
        Raises:
            ValueError: If adapter_class is not a subclass of BaseAdapter
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise ValueError(
                f"Adapter class must inherit from BaseAdapter, got {adapter_class}"
            )
        
        self._adapter_classes[provider_id] = adapter_class
        self._adapter_instances[provider_id] = {}

    def get_adapter(
        self, provider_id: str, connection_id: UUID, tenant_id: str
    ) -> Optional[BaseAdapter]:
        """
        Get or create adapter instance.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            tenant_id: Tenant ID
            
        Returns:
            Adapter instance, or None if not registered
        """
        if provider_id not in self._adapter_classes:
            return None
        
        # Check if instance exists
        if connection_id in self._adapter_instances[provider_id]:
            return self._adapter_instances[provider_id][connection_id]
        
        # Create new instance
        adapter_class = self._adapter_classes[provider_id]
        adapter = adapter_class(provider_id, connection_id, tenant_id)
        self._adapter_instances[provider_id][connection_id] = adapter
        
        return adapter

    def get_adapter_class(self, provider_id: str) -> Optional[Type[BaseAdapter]]:
        """
        Get adapter class for provider.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            Adapter class, or None if not registered
        """
        return self._adapter_classes.get(provider_id)

    def list_providers(self) -> List[str]:
        """
        List all registered provider IDs.
        
        Returns:
            List of provider IDs
        """
        return list(self._adapter_classes.keys())

    def is_registered(self, provider_id: str) -> bool:
        """
        Check if provider is registered.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            True if registered, False otherwise
        """
        return provider_id in self._adapter_classes

    def get_capabilities(self, provider_id: str) -> Optional[Dict[str, bool]]:
        """
        Get capabilities for a provider.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            Capabilities dict, or None if not registered
        """
        adapter_class = self.get_adapter_class(provider_id)
        if not adapter_class:
            return None
        
        # Create temporary instance to get capabilities
        # Note: This requires connection_id and tenant_id, so we use dummy values
        # In practice, capabilities should be stored in the provider registry
        try:
            # Try to get capabilities from class if it's a class method
            if hasattr(adapter_class, "get_default_capabilities"):
                return adapter_class.get_default_capabilities()
        except Exception:
            pass
        
        return None

    def remove_adapter_instance(
        self, provider_id: str, connection_id: UUID
    ) -> bool:
        """
        Remove adapter instance from cache.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            
        Returns:
            True if removed, False if not found
        """
        if provider_id not in self._adapter_instances:
            return False
        
        if connection_id in self._adapter_instances[provider_id]:
            del self._adapter_instances[provider_id][connection_id]
            return True
        
        return False


# Global registry instance
_adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Get global adapter registry instance."""
    return _adapter_registry


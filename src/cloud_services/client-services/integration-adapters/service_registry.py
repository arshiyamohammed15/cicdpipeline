"""
Service registry for dependency injection.

What: Service registration and retrieval
Why: Dependency injection pattern
Reads/Writes: Service instances
Contracts: Standard service registry patterns
Risks: Service resolution errors
"""

from __future__ import annotations

from typing import Dict, Any, Optional


class ServiceRegistry:
    """Service registry for dependency injection."""

    def __init__(self):
        """Initialize service registry."""
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """
        Register a service.
        
        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service

    def get(self, name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance, or None if not found
        """
        return self._services.get(name)

    def has(self, name: str) -> bool:
        """
        Check if service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._services


# Global service registry
_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get global service registry instance."""
    return _service_registry


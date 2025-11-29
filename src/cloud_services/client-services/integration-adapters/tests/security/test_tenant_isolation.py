"""
Security test: Tenant Isolation (SEC-IA-02).

What: Ensure no cross-tenant visibility or processing
Why: Prevent data leakage between tenants
Coverage Target: All tenant-scoped operations
"""

from __future__ import annotations

import pytest
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database.models import IntegrationConnection
from database.repositories import ConnectionRepository


class TestTenantIsolation:
    """Test tenant isolation."""

    def test_connection_tenant_isolation(self, connection_repo):
        """Test that connections are isolated by tenant."""
        tenant1 = "tenant-1"
        tenant2 = "tenant-2"
        
        connection1 = IntegrationConnection(
            tenant_id=tenant1,
            provider_id="github",
            display_name="Connection 1",
            auth_ref="secret-1",
        )
        connection2 = IntegrationConnection(
            tenant_id=tenant2,
            provider_id="github",
            display_name="Connection 2",
            auth_ref="secret-2",
        )
        
        created1 = connection_repo.create(connection1)
        created2 = connection_repo.create(connection2)
        
        # Tenant 1 cannot access tenant 2's connection
        retrieved = connection_repo.get_by_id(created2.connection_id, tenant1)
        assert retrieved is None
        
        # Tenant 2 cannot access tenant 1's connection
        retrieved = connection_repo.get_by_id(created1.connection_id, tenant2)
        assert retrieved is None
        
        # Each tenant can access their own
        retrieved1 = connection_repo.get_by_id(created1.connection_id, tenant1)
        assert retrieved1 is not None
        
        retrieved2 = connection_repo.get_by_id(created2.connection_id, tenant2)
        assert retrieved2 is not None

    def test_list_connections_tenant_isolation(self, connection_repo):
        """Test that listing connections respects tenant isolation."""
        tenant1 = "tenant-1"
        tenant2 = "tenant-2"
        
        connection1 = IntegrationConnection(
            tenant_id=tenant1,
            provider_id="github",
            display_name="Connection 1",
            auth_ref="secret-1",
        )
        connection2 = IntegrationConnection(
            tenant_id=tenant2,
            provider_id="github",
            display_name="Connection 2",
            auth_ref="secret-2",
        )
        
        connection_repo.create(connection1)
        connection_repo.create(connection2)
        
        # Tenant 1 only sees their connections
        tenant1_connections = connection_repo.get_all_by_tenant(tenant1)
        assert len(tenant1_connections) == 1
        assert tenant1_connections[0].tenant_id == tenant1
        
        # Tenant 2 only sees their connections
        tenant2_connections = connection_repo.get_all_by_tenant(tenant2)
        assert len(tenant2_connections) == 1
        assert tenant2_connections[0].tenant_id == tenant2


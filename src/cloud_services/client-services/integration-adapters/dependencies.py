"""
Dependency injection for Integration Adapters Module.

What: Mock clients for shared services and dependency management
Why: Dependency injection pattern for testability
Reads/Writes: Service instances
Contracts: Standard DI patterns
Risks: Dependency resolution errors
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from .database.connection import get_db
from .integrations.kms_client import KMSClient
from .integrations.budget_client import BudgetClient
from .integrations.pm3_client import PM3Client
from .integrations.eris_client import ERISClient
from .integrations.iam_client import IAMClient
from .services.webhook_service import WebhookService
from .services.integration_service import IntegrationService


def get_integration_service(
    db: Session = Depends(get_db),
) -> IntegrationService:
    """
    Get integration service instance with dependencies.
    
    Args:
        db: Database session (from FastAPI dependency)
        
    Returns:
        IntegrationService instance
    """
    # Create default clients
    kms_client = KMSClient()
    budget_client = BudgetClient()
    pm3_client = PM3Client()
    eris_client = ERISClient()
    
    return IntegrationService(
        session=db,
        kms_client=kms_client,
        budget_client=budget_client,
        pm3_client=pm3_client,
        eris_client=eris_client,
    )


def get_iam_client() -> IAMClient:
    """Get IAM client instance."""
    return IAMClient()


def get_webhook_service(
    db: Session = Depends(get_db),
) -> WebhookService:
    """
    Get webhook service with replay protection and dependency wiring.
    
    Args:
        db: Database session
    
    Returns:
        WebhookService instance
    """
    integration_service = get_integration_service(db)
    return WebhookService(integration_service=integration_service, session=db)


"""
Test fixtures for Integration Adapters Module tests.

What: Shared test fixtures and utilities
Why: Reusable test setup across all test files
Reads/Writes: Test database, mock services
Contracts: pytest fixture patterns
Risks: Fixture conflicts, test isolation issues
"""

from __future__ import annotations

import pytest
from datetime import datetime
from typing import Generator
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database.models import Base
from database.repositories import (
    ProviderRepository,
    ConnectionRepository,
    WebhookRegistrationRepository,
    PollingCursorRepository,
    AdapterEventRepository,
    NormalisedActionRepository,
)
# Note: IntegrationService and client imports are done lazily in fixtures to avoid import errors


# Test database (SQLite in-memory)
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create test database session."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def provider_repo(db_session: Session) -> ProviderRepository:
    """Provider repository fixture."""
    return ProviderRepository(db_session)


@pytest.fixture
def connection_repo(db_session: Session) -> ConnectionRepository:
    """Connection repository fixture."""
    return ConnectionRepository(db_session)


@pytest.fixture
def webhook_repo(db_session: Session) -> WebhookRegistrationRepository:
    """Webhook registration repository fixture."""
    return WebhookRegistrationRepository(db_session)


@pytest.fixture
def polling_repo(db_session: Session) -> PollingCursorRepository:
    """Polling cursor repository fixture."""
    return PollingCursorRepository(db_session)


@pytest.fixture
def event_repo(db_session: Session) -> AdapterEventRepository:
    """Adapter event repository fixture."""
    return AdapterEventRepository(db_session)


@pytest.fixture
def action_repo(db_session: Session) -> NormalisedActionRepository:
    """Normalised action repository fixture."""
    return NormalisedActionRepository(db_session)


@pytest.fixture
def mock_kms_client(monkeypatch):
    """Mock KMS client."""
    class MockKMSClient:
        def __init__(self):
            self.secrets = {}
        
        def get_secret(self, secret_id: str, tenant_id: str) -> str:
            return self.secrets.get(secret_id, "mock-secret")
        
        def refresh_token(self, secret_id: str, tenant_id: str) -> str:
            return "refreshed-token"
    
    return MockKMSClient()


@pytest.fixture
def mock_budget_client(monkeypatch):
    """Mock budget client."""
    class MockBudgetClient:
        def check_budget(self, *args, **kwargs):
            return True, {}
        
        def check_rate_limit(self, *args, **kwargs):
            return True, {}
        
        def record_usage(self, *args, **kwargs):
            return True
    
    class MockBudgetClient:
        def check_budget(self, *args, **kwargs):
            return True, {}
        
        def check_rate_limit(self, *args, **kwargs):
            return True, {}
        
        def record_usage(self, *args, **kwargs):
            return True
    
    return MockBudgetClient()


@pytest.fixture
def mock_pm3_client(monkeypatch):
    """Mock PM-3 client."""
    class MockPM3Client:
        def ingest_signal(self, signal):
            return True
        
        def ingest_signals(self, signals):
            return len(signals)
    
    return MockPM3Client()


@pytest.fixture
def mock_eris_client(monkeypatch):
    """Mock ERIS client."""
    class MockERISClient:
        def emit_receipt(self, *args, **kwargs):
            return True
        
        def emit_receipts(self, receipts):
            return len(receipts)
    
    return MockERISClient()


@pytest.fixture
def integration_service(
    db_session: Session,
    mock_kms_client,
    mock_budget_client,
    mock_pm3_client,
    mock_eris_client,
):
    """Integration service fixture with mocked dependencies."""
    # Import here to avoid import errors at module level
    from services.integration_service import IntegrationService
    return IntegrationService(
        session=db_session,
        kms_client=mock_kms_client,
        budget_client=mock_budget_client,
        pm3_client=mock_pm3_client,
        eris_client=mock_eris_client,
    )


@pytest.fixture
def sample_tenant_id() -> str:
    """Sample tenant ID for tests."""
    return "test-tenant-123"


@pytest.fixture
def sample_connection_id() -> str:
    """Sample connection ID for tests."""
    return str(uuid4())


@pytest.fixture
def sample_provider_data():
    """Sample provider data for tests."""
    return {
        "provider_id": "github",
        "category": "SCM",
        "name": "GitHub",
        "status": "GA",
        "capabilities": {
            "webhook_supported": True,
            "polling_supported": False,
            "outbound_actions_supported": True,
        },
        "api_version": "v3",
    }


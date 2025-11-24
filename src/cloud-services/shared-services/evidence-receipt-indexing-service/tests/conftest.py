"""
Pytest configuration and fixtures for ERIS tests.
"""

import sys
import os
from pathlib import Path

# Add the module directory to Python path
module_dir = Path(__file__).parent.parent
module_dir_str = str(module_dir)
if module_dir_str not in sys.path:
    sys.path.insert(0, module_dir_str)

# Also add src directory for shared imports
src_path = Path(__file__).parent.parent.parent.parent.parent
src_path_str = str(src_path)
if src_path_str not in sys.path:
    sys.path.insert(0, src_path_str)

import pytest
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker

# Import using module name with underscores (directory has hyphens)
try:
    from evidence_receipt_indexing_service.database.models import Base, Receipt, CourierBatch, MetaReceipt, ExportJob
except ImportError:
    # Fallback: try direct import if module is in path
    import importlib.util
    spec = importlib.util.spec_from_file_location("database.models", Path(__file__).parent.parent / "database" / "models.py")
    database_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_models)
    Base = database_models.Base
    Receipt = database_models.Receipt
    CourierBatch = database_models.CourierBatch
    MetaReceipt = database_models.MetaReceipt
    ExportJob = database_models.ExportJob


@pytest.fixture
def db_session():
    """Create test database session."""
    from sqlalchemy import JSON as SQLiteJSON
    from sqlalchemy.dialects.sqlite import JSON as SQLiteJSONType
    
    # Use SQLite for testing, but need to handle PostgreSQL-specific types
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Replace PostgreSQL-specific types with SQLite-compatible types
    for table in Base.metadata.tables.values():
        for column in table.columns:
            # Replace UUID with String
            if hasattr(column.type, 'as_uuid') and column.type.as_uuid:
                column.type = String(36)
            # Replace ARRAY with JSON (SQLite stores arrays as JSON)
            elif hasattr(column.type, 'item_type'):  # ARRAY type
                column.type = SQLiteJSONType()
            # Replace JSONB with JSON
            elif str(column.type).startswith('JSONB'):
                column.type = SQLiteJSONType()
    
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_receipt():
    """Sample receipt for testing."""
    return {
        "receipt_id": "123e4567-e89b-12d3-a456-426614174000",
        "gate_id": "test-gate",
        "schema_version": "1.0.0",
        "policy_version_ids": ["policy-1"],
        "snapshot_hash": "sha256:abc123",
        "timestamp_utc": "2025-01-01T00:00:00Z",
        "timestamp_monotonic_ms": 1000,
        "evaluation_point": "pre-commit",
        "inputs": {"test": "data"},
        "decision": {
            "status": "pass",
            "rationale": "Test rationale",
            "badges": []
        },
        "actor": {
            "repo_id": "test-repo",
            "machine_fingerprint": "test-fingerprint"
        },
        "degraded": False,
        "signature": "test-signature"
    }


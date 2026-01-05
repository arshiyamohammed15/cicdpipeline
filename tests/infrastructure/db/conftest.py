"""
Pytest configuration and fixtures for database infrastructure tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def repo_root() -> Path:
    """Return repository root directory."""
    return REPO_ROOT


@pytest.fixture
def schema_pack_root(repo_root: Path) -> Path:
    """Return schema pack root directory."""
    return repo_root / "infra" / "db" / "schema_pack"


@pytest.fixture
def contract_path(schema_pack_root: Path) -> Path:
    """Return canonical schema contract path."""
    return schema_pack_root / "canonical_schema_contract.json"


@pytest.fixture
def pg_migration_path(schema_pack_root: Path) -> Path:
    """Return Postgres migration path."""
    return schema_pack_root / "migrations" / "pg" / "001_core.sql"


@pytest.fixture
def sqlite_migration_path(schema_pack_root: Path) -> Path:
    """Return SQLite migration path."""
    return schema_pack_root / "migrations" / "sqlite" / "001_core.sql"


@pytest.fixture
def bkg_schema_path(repo_root: Path) -> Path:
    """Return BKG edge JSON schema path."""
    return repo_root / "contracts" / "bkg" / "schemas" / "bkg_edge.schema.json"


@pytest.fixture
def memory_model_doc_path(repo_root: Path) -> Path:
    """Return memory model documentation path."""
    return repo_root / "docs" / "architecture" / "memory_model.md"


@pytest.fixture
def bkg_phase0_doc_path(repo_root: Path) -> Path:
    """Return BKG Phase 0 stub documentation path."""
    return repo_root / "docs" / "architecture" / "bkg_phase0_stub.md"


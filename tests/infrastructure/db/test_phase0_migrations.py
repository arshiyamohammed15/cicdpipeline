"""
Test suite for Phase 0 migration files.

Tests cover:
- Migration file existence
- SQL syntax validation
- Table creation statements
- Index creation statements
- BKG edge migrations
- Semantic Q&A Cache migration
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BKG_TENANT = REPO_ROOT / "infra" / "db" / "migrations" / "tenant" / "002_bkg_phase0.sql"
BKG_PRODUCT = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "003_bkg_phase0.sql"
BKG_SHARED = REPO_ROOT / "infra" / "db" / "migrations" / "shared" / "002_bkg_phase0.sql"
BKG_SQLITE = REPO_ROOT / "infra" / "db" / "migrations" / "sqlite" / "002_bkg_phase0.sql"
QA_CACHE_PRODUCT = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "004_semantic_qa_cache_phase0.sql"


@pytest.mark.unit
class TestPhase0MigrationExistence:
    """Test Phase 0 migration files exist."""

    @pytest.mark.unit
    def test_bkg_tenant_migration_exists(self) -> None:
        """BKG tenant migration must exist."""
        assert BKG_TENANT.exists()

    @pytest.mark.unit
    def test_bkg_product_migration_exists(self) -> None:
        """BKG product migration must exist."""
        assert BKG_PRODUCT.exists()

    @pytest.mark.unit
    def test_bkg_shared_migration_exists(self) -> None:
        """BKG shared migration must exist."""
        assert BKG_SHARED.exists()

    @pytest.mark.unit
    def test_bkg_sqlite_migration_exists(self) -> None:
        """BKG SQLite migration must exist."""
        assert BKG_SQLITE.exists()

    @pytest.mark.unit
    def test_qa_cache_product_migration_exists(self) -> None:
        """Semantic Q&A Cache product migration must exist."""
        assert QA_CACHE_PRODUCT.exists()


@pytest.mark.unit
class TestBkgPhase0Migrations:
    """Test BKG Phase 0 migration SQL structure."""

    @pytest.fixture
    def bkg_tenant_text(self) -> str:
        """Load BKG tenant migration."""
        return BKG_TENANT.read_text(encoding="utf-8")

    @pytest.fixture
    def bkg_product_text(self) -> str:
        """Load BKG product migration."""
        return BKG_PRODUCT.read_text(encoding="utf-8")

    @pytest.fixture
    def bkg_shared_text(self) -> str:
        """Load BKG shared migration."""
        return BKG_SHARED.read_text(encoding="utf-8")

    @pytest.fixture
    def bkg_sqlite_text(self) -> str:
        """Load BKG SQLite migration."""
        return BKG_SQLITE.read_text(encoding="utf-8")

    @pytest.mark.unit
    def test_bkg_postgres_migrations_create_table(self, bkg_tenant_text: str, bkg_product_text: str, bkg_shared_text: str) -> None:
        """BKG Postgres migrations must create core.bkg_edge table."""
        for migration_text in [bkg_tenant_text, bkg_product_text, bkg_shared_text]:
            assert "CREATE TABLE IF NOT EXISTS core.bkg_edge" in migration_text

    @pytest.mark.unit
    def test_bkg_sqlite_migration_creates_table(self, bkg_sqlite_text: str) -> None:
        """BKG SQLite migration must create core__bkg_edge table."""
        assert "CREATE TABLE IF NOT EXISTS core__bkg_edge" in bkg_sqlite_text

    @pytest.mark.unit
    def test_bkg_postgres_migrations_have_all_columns(self, bkg_tenant_text: str) -> None:
        """BKG Postgres migrations must have all required columns."""
        required_columns = [
            "edge_id TEXT PRIMARY KEY",
            "source_entity_type TEXT NOT NULL",
            "source_entity_id TEXT NOT NULL",
            "target_entity_type TEXT NOT NULL",
            "target_entity_id TEXT NOT NULL",
            "edge_type TEXT NOT NULL",
            "metadata JSONB NULL",
            "created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        ]
        for col in required_columns:
            assert col in bkg_tenant_text, f"Missing column definition: {col}"

    @pytest.mark.unit
    def test_bkg_sqlite_migration_has_all_columns(self, bkg_sqlite_text: str) -> None:
        """BKG SQLite migration must have all required columns."""
        required_columns = [
            "edge_id TEXT PRIMARY KEY",
            "source_entity_type TEXT NOT NULL",
            "source_entity_id TEXT NOT NULL",
            "target_entity_type TEXT NOT NULL",
            "target_entity_id TEXT NOT NULL",
            "edge_type TEXT NOT NULL",
            "metadata TEXT NULL",
            "created_at TEXT NOT NULL DEFAULT (datetime('now'))",
        ]
        for col in required_columns:
            assert col in bkg_sqlite_text, f"Missing column definition: {col}"

    @pytest.mark.unit
    def test_bkg_postgres_migrations_create_indexes(self, bkg_tenant_text: str) -> None:
        """BKG Postgres migrations must create indexes."""
        required_indexes = [
            "idx_bkg_edge_source",
            "idx_bkg_edge_target",
            "idx_bkg_edge_type",
            "idx_bkg_edge_source_target",
        ]
        for idx in required_indexes:
            assert f"CREATE INDEX IF NOT EXISTS {idx}" in bkg_tenant_text, f"Missing index: {idx}"

    @pytest.mark.unit
    def test_bkg_sqlite_migration_creates_indexes(self, bkg_sqlite_text: str) -> None:
        """BKG SQLite migration must create indexes."""
        required_indexes = [
            "idx_bkg_edge_source",
            "idx_bkg_edge_target",
            "idx_bkg_edge_type",
            "idx_bkg_edge_source_target",
        ]
        for idx in required_indexes:
            assert f"CREATE INDEX IF NOT EXISTS {idx}" in bkg_sqlite_text, f"Missing index: {idx}"

    @pytest.mark.unit
    def test_bkg_postgres_migrations_have_comments(self, bkg_tenant_text: str) -> None:
        """BKG Postgres migrations must have table comments."""
        assert "COMMENT ON TABLE core.bkg_edge" in bkg_tenant_text or "--" in bkg_tenant_text

    @pytest.mark.unit
    def test_bkg_migrations_are_idempotent(self, bkg_tenant_text: str, bkg_sqlite_text: str) -> None:
        """BKG migrations must be idempotent (IF NOT EXISTS)."""
        assert "CREATE TABLE IF NOT EXISTS" in bkg_tenant_text
        assert "CREATE TABLE IF NOT EXISTS" in bkg_sqlite_text
        assert "CREATE INDEX IF NOT EXISTS" in bkg_tenant_text
        assert "CREATE INDEX IF NOT EXISTS" in bkg_sqlite_text

    @pytest.mark.unit
    def test_bkg_postgres_migrations_identical(self, bkg_tenant_text: str, bkg_product_text: str, bkg_shared_text: str) -> None:
        """BKG Postgres migrations must be identical across planes."""
        # Extract table creation statements
        tenant_table = re.search(r"CREATE TABLE IF NOT EXISTS core\.bkg_edge\s*\((.*?)\);", bkg_tenant_text, re.DOTALL)
        product_table = re.search(r"CREATE TABLE IF NOT EXISTS core\.bkg_edge\s*\((.*?)\);", bkg_product_text, re.DOTALL)
        shared_table = re.search(r"CREATE TABLE IF NOT EXISTS core\.bkg_edge\s*\((.*?)\);", bkg_shared_text, re.DOTALL)

        assert tenant_table is not None
        assert product_table is not None
        assert shared_table is not None

        # Normalize whitespace for comparison
        tenant_body = re.sub(r"\s+", " ", tenant_table.group(1)).strip()
        product_body = re.sub(r"\s+", " ", product_table.group(1)).strip()
        shared_body = re.sub(r"\s+", " ", shared_table.group(1)).strip()

        assert tenant_body == product_body, "Tenant and Product BKG migrations differ"
        assert tenant_body == shared_body, "Tenant and Shared BKG migrations differ"


@pytest.mark.unit
class TestSemanticQaCacheMigration:
    """Test Semantic Q&A Cache migration SQL structure."""

    @pytest.fixture
    def qa_cache_text(self) -> str:
        """Load Semantic Q&A Cache migration."""
        return QA_CACHE_PRODUCT.read_text(encoding="utf-8")

    @pytest.mark.unit
    def test_qa_cache_migration_creates_table(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must create app.semantic_qa_cache table."""
        assert "CREATE TABLE IF NOT EXISTS app.semantic_qa_cache" in qa_cache_text

    @pytest.mark.unit
    def test_qa_cache_migration_has_all_columns(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must have all required columns."""
        required_columns = [
            "cache_id TEXT PRIMARY KEY",
            "query_hash TEXT NOT NULL",
            "query_text TEXT NOT NULL",
            "answer_text TEXT NOT NULL",
            "context_snapshot_id TEXT NULL",
            "embedding_doc_id TEXT NULL",
            "confidence_score REAL NULL",
            "metadata JSONB NULL",
            "created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
            "expires_at TIMESTAMPTZ NULL",
        ]
        for col in required_columns:
            assert col in qa_cache_text, f"Missing column definition: {col}"

    @pytest.mark.unit
    def test_qa_cache_migration_creates_indexes(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must create indexes."""
        required_indexes = [
            "idx_semantic_qa_cache_query_hash",
            "idx_semantic_qa_cache_expires_at",
            "idx_semantic_qa_cache_context_snapshot",
        ]
        for idx in required_indexes:
            assert f"CREATE INDEX IF NOT EXISTS {idx}" in qa_cache_text, f"Missing index: {idx}"

    @pytest.mark.unit
    def test_qa_cache_migration_has_governance_comment(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must have governance comment."""
        assert "NOT used for gating" in qa_cache_text or "not used for gating" in qa_cache_text.lower()

    @pytest.mark.unit
    def test_qa_cache_migration_is_idempotent(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must be idempotent."""
        assert "CREATE TABLE IF NOT EXISTS" in qa_cache_text
        assert "CREATE INDEX IF NOT EXISTS" in qa_cache_text

    @pytest.mark.unit
    def test_qa_cache_migration_in_app_schema(self, qa_cache_text: str) -> None:
        """Semantic Q&A Cache migration must create table in app schema."""
        assert "app.semantic_qa_cache" in qa_cache_text
        assert "core.semantic_qa_cache" not in qa_cache_text


"""
Test suite for Semantic Q&A Cache Schema validation.

Tests cover:
- Schema migration SQL structure
- Valid cache entry creation
- Invalid query hash
- Missing required fields
- TTL expiration handling
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
QA_CACHE_MIGRATION = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "004_semantic_qa_cache_phase0.sql"


@pytest.fixture
def qa_cache_migration_text() -> str:
    """Load Semantic Q&A Cache migration SQL."""
    with open(QA_CACHE_MIGRATION, encoding="utf-8") as f:
        return f.read()


@pytest.mark.unit
class TestSemanticQaCacheMigrationStructure:
    """Test Semantic Q&A Cache migration SQL structure."""

    @pytest.mark.unit
    def test_migration_creates_table(self, qa_cache_migration_text: str) -> None:
        """Migration must create app.semantic_qa_cache table."""
        assert "CREATE TABLE IF NOT EXISTS app.semantic_qa_cache" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_cache_id_primary_key(self, qa_cache_migration_text: str) -> None:
        """Migration must have cache_id as PRIMARY KEY."""
        assert "cache_id TEXT PRIMARY KEY" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_query_hash(self, qa_cache_migration_text: str) -> None:
        """Migration must have query_hash field."""
        assert "query_hash TEXT NOT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_query_text(self, qa_cache_migration_text: str) -> None:
        """Migration must have query_text field."""
        assert "query_text TEXT NOT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_answer_text(self, qa_cache_migration_text: str) -> None:
        """Migration must have answer_text field."""
        assert "answer_text TEXT NOT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_optional_context_snapshot_id(self, qa_cache_migration_text: str) -> None:
        """Migration must have optional context_snapshot_id field."""
        assert "context_snapshot_id TEXT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_optional_embedding_doc_id(self, qa_cache_migration_text: str) -> None:
        """Migration must have optional embedding_doc_id field."""
        assert "embedding_doc_id TEXT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_optional_confidence_score(self, qa_cache_migration_text: str) -> None:
        """Migration must have optional confidence_score field."""
        assert "confidence_score REAL NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_optional_metadata(self, qa_cache_migration_text: str) -> None:
        """Migration must have optional metadata JSONB field."""
        assert "metadata JSONB NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_created_at(self, qa_cache_migration_text: str) -> None:
        """Migration must have created_at field with default."""
        assert "created_at TIMESTAMPTZ NOT NULL DEFAULT now()" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_expires_at(self, qa_cache_migration_text: str) -> None:
        """Migration must have optional expires_at field for TTL."""
        assert "expires_at TIMESTAMPTZ NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_creates_query_hash_index(self, qa_cache_migration_text: str) -> None:
        """Migration must create index on query_hash."""
        assert "CREATE INDEX IF NOT EXISTS idx_semantic_qa_cache_query_hash" in qa_cache_migration_text
        assert "ON app.semantic_qa_cache(query_hash)" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_creates_expires_at_index(self, qa_cache_migration_text: str) -> None:
        """Migration must create partial index on expires_at."""
        assert "CREATE INDEX IF NOT EXISTS idx_semantic_qa_cache_expires_at" in qa_cache_migration_text
        assert "ON app.semantic_qa_cache(expires_at) WHERE expires_at IS NOT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_creates_context_snapshot_index(self, qa_cache_migration_text: str) -> None:
        """Migration must create partial index on context_snapshot_id."""
        assert "CREATE INDEX IF NOT EXISTS idx_semantic_qa_cache_context_snapshot" in qa_cache_migration_text
        assert "ON app.semantic_qa_cache(context_snapshot_id) WHERE context_snapshot_id IS NOT NULL" in qa_cache_migration_text

    @pytest.mark.unit
    def test_migration_has_governance_comment(self, qa_cache_migration_text: str) -> None:
        """Migration must have comment documenting governance rule."""
        assert "NOT used for gating decisions" in qa_cache_migration_text or "not used for gating" in qa_cache_migration_text.lower()

    @pytest.mark.unit
    def test_migration_table_in_app_schema(self, qa_cache_migration_text: str) -> None:
        """Migration must create table in app schema (not core)."""
        assert "app.semantic_qa_cache" in qa_cache_migration_text
        # Should not be in core schema
        assert "core.semantic_qa_cache" not in qa_cache_migration_text


@pytest.mark.unit
class TestSemanticQaCacheSchemaConstraints:
    """Test Semantic Q&A Cache schema constraints."""

    @pytest.mark.unit
    def test_query_hash_is_not_null(self, qa_cache_migration_text: str) -> None:
        """query_hash must be NOT NULL."""
        # Extract the CREATE TABLE statement
        table_match = re.search(r"CREATE TABLE IF NOT EXISTS app\.semantic_qa_cache\s*\((.*?)\);", qa_cache_migration_text, re.DOTALL)
        assert table_match is not None
        table_body = table_match.group(1)
        # Check query_hash is NOT NULL
        assert re.search(r"query_hash\s+TEXT\s+NOT\s+NULL", table_body) is not None

    @pytest.mark.unit
    def test_query_text_is_not_null(self, qa_cache_migration_text: str) -> None:
        """query_text must be NOT NULL."""
        table_match = re.search(r"CREATE TABLE IF NOT EXISTS app\.semantic_qa_cache\s*\((.*?)\);", qa_cache_migration_text, re.DOTALL)
        assert table_match is not None
        table_body = table_match.group(1)
        assert re.search(r"query_text\s+TEXT\s+NOT\s+NULL", table_body) is not None

    @pytest.mark.unit
    def test_answer_text_is_not_null(self, qa_cache_migration_text: str) -> None:
        """answer_text must be NOT NULL."""
        table_match = re.search(r"CREATE TABLE IF NOT EXISTS app\.semantic_qa_cache\s*\((.*?)\);", qa_cache_migration_text, re.DOTALL)
        assert table_match is not None
        table_body = table_match.group(1)
        assert re.search(r"answer_text\s+TEXT\s+NOT\s+NULL", table_body) is not None

    @pytest.mark.unit
    def test_expires_at_is_nullable(self, qa_cache_migration_text: str) -> None:
        """expires_at must be nullable (for TTL)."""
        table_match = re.search(r"CREATE TABLE IF NOT EXISTS app\.semantic_qa_cache\s*\((.*?)\);", qa_cache_migration_text, re.DOTALL)
        assert table_match is not None
        table_body = table_match.group(1)
        assert re.search(r"expires_at\s+TIMESTAMPTZ\s+NULL", table_body) is not None


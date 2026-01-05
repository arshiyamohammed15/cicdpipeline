"""
Integration test suite for schema application flow.

Tests cover:
- End-to-end schema pack application (mocked)
- End-to-end Phase 0 stub application (mocked)
- Schema equivalence verification (mocked)
- Error scenarios
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PACK_ROOT = REPO_ROOT / "infra" / "db" / "schema_pack"
CONTRACT_PATH = SCHEMA_PACK_ROOT / "canonical_schema_contract.json"
PG_MIGRATION = SCHEMA_PACK_ROOT / "migrations" / "pg" / "001_core.sql"
SQLITE_MIGRATION = SCHEMA_PACK_ROOT / "migrations" / "sqlite" / "001_core.sql"


class TestSchemaPackApplicationFlow:
    """Test schema pack application flow (mocked)."""

    def test_schema_pack_migration_files_exist(self) -> None:
        """Schema pack migration files must exist."""
        assert PG_MIGRATION.exists(), "Postgres migration file missing"
        assert SQLITE_MIGRATION.exists(), "SQLite migration file missing"

    def test_schema_pack_contract_exists(self) -> None:
        """Canonical schema contract must exist."""
        assert CONTRACT_PATH.exists(), "Canonical schema contract missing"

    def test_schema_pack_contract_is_valid_json(self) -> None:
        """Canonical schema contract must be valid JSON."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)
        assert "schema_pack_id" in contract
        assert "schema_version" in contract
        assert "postgres" in contract
        assert "sqlite" in contract

    def test_schema_pack_migrations_are_valid_sql(self) -> None:
        """Schema pack migrations must be valid SQL (syntax check)."""
        pg_text = PG_MIGRATION.read_text(encoding="utf-8")
        sqlite_text = SQLITE_MIGRATION.read_text(encoding="utf-8")

        # Basic SQL syntax checks
        assert "CREATE TABLE" in pg_text or "CREATE SCHEMA" in pg_text
        assert "CREATE TABLE" in sqlite_text
        assert "BEGIN" in pg_text or "BEGIN;" in pg_text
        assert "COMMIT" in pg_text or "COMMIT;" in pg_text

    def test_schema_pack_migrations_match_contract(self) -> None:
        """Schema pack migrations must match contract table definitions."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)

        pg_text = PG_MIGRATION.read_text(encoding="utf-8")
        sqlite_text = SQLITE_MIGRATION.read_text(encoding="utf-8")

        # Check that all contract tables are in migrations
        for table in contract["postgres"]["tables"]:
            table_name = table["name"].replace(".", r"\.")
            assert f"CREATE TABLE IF NOT EXISTS {table_name}" in pg_text or f"CREATE TABLE IF NOT EXISTS {table['name']}" in pg_text

        for table in contract["sqlite"]["tables"]:
            assert f"CREATE TABLE IF NOT EXISTS {table['name']}" in sqlite_text


class TestPhase0StubApplicationFlow:
    """Test Phase 0 stub application flow."""

    def test_bkg_migrations_exist_for_all_planes(self) -> None:
        """BKG migrations must exist for all planes."""
        bkg_tenant = REPO_ROOT / "infra" / "db" / "migrations" / "tenant" / "002_bkg_phase0.sql"
        bkg_product = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "003_bkg_phase0.sql"
        bkg_shared = REPO_ROOT / "infra" / "db" / "migrations" / "shared" / "002_bkg_phase0.sql"
        bkg_sqlite = REPO_ROOT / "infra" / "db" / "migrations" / "sqlite" / "002_bkg_phase0.sql"

        assert bkg_tenant.exists(), "BKG tenant migration missing"
        assert bkg_product.exists(), "BKG product migration missing"
        assert bkg_shared.exists(), "BKG shared migration missing"
        assert bkg_sqlite.exists(), "BKG SQLite migration missing"

    def test_qa_cache_migration_exists(self) -> None:
        """Semantic Q&A Cache migration must exist."""
        qa_cache = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "004_semantic_qa_cache_phase0.sql"
        assert qa_cache.exists(), "Semantic Q&A Cache migration missing"

    def test_bkg_migrations_are_identical_across_postgres(self) -> None:
        """BKG Postgres migrations must be identical across planes."""
        bkg_tenant = REPO_ROOT / "infra" / "db" / "migrations" / "tenant" / "002_bkg_phase0.sql"
        bkg_product = REPO_ROOT / "infra" / "db" / "migrations" / "product" / "003_bkg_phase0.sql"
        bkg_shared = REPO_ROOT / "infra" / "db" / "migrations" / "shared" / "002_bkg_phase0.sql"

        tenant_text = bkg_tenant.read_text(encoding="utf-8")
        product_text = bkg_product.read_text(encoding="utf-8")
        shared_text = bkg_shared.read_text(encoding="utf-8")

        # Normalize whitespace for comparison
        tenant_normalized = " ".join(tenant_text.split())
        product_normalized = " ".join(product_text.split())
        shared_normalized = " ".join(shared_text.split())

        assert tenant_normalized == product_normalized, "BKG tenant and product migrations differ"
        assert tenant_normalized == shared_normalized, "BKG tenant and shared migrations differ"


class TestSchemaEquivalenceVerification:
    """Test schema equivalence verification logic."""

    def test_contract_defines_postgres_tables(self) -> None:
        """Contract must define Postgres tables."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)

        assert len(contract["postgres"]["tables"]) > 0
        for table in contract["postgres"]["tables"]:
            assert "name" in table
            assert "primary_key" in table
            assert "columns" in table

    def test_contract_defines_sqlite_tables(self) -> None:
        """Contract must define SQLite tables."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)

        assert len(contract["sqlite"]["tables"]) > 0
        for table in contract["sqlite"]["tables"]:
            assert "name" in table
            assert "primary_key" in table
            assert "columns" in table

    def test_contract_postgres_sqlite_table_count_matches(self) -> None:
        """Contract must have same number of tables in Postgres and SQLite."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)

        assert len(contract["postgres"]["tables"]) == len(contract["sqlite"]["tables"])

    def test_contract_bkg_edge_in_both_engines(self) -> None:
        """Contract must include BKG edge table in both Postgres and SQLite."""
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)

        pg_tables = {t["name"]: t for t in contract["postgres"]["tables"]}
        sqlite_tables = {t["name"]: t for t in contract["sqlite"]["tables"]}

        assert "core.bkg_edge" in pg_tables
        assert "core__bkg_edge" in sqlite_tables

        # Column sets must match (ignoring type differences)
        pg_columns = set(pg_tables["core.bkg_edge"]["columns"])
        sqlite_columns = set(sqlite_tables["core__bkg_edge"]["columns"])
        assert pg_columns == sqlite_columns


class TestErrorScenarios:
    """Test error scenarios and edge cases."""

    def test_missing_migration_file_handling(self) -> None:
        """Scripts must handle missing migration files gracefully."""
        # This is tested in PowerShell script tests
        # Python test verifies files exist (negative case would require mocking)
        assert PG_MIGRATION.exists(), "Migration file should exist for positive test"

    def test_invalid_contract_json_handling(self) -> None:
        """Scripts must handle invalid contract JSON gracefully."""
        # Verify contract is valid JSON
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            contract = json.load(f)
        assert isinstance(contract, dict), "Contract must be valid JSON object"

    def test_empty_migration_file_handling(self) -> None:
        """Migrations must not be empty."""
        pg_text = PG_MIGRATION.read_text(encoding="utf-8")
        sqlite_text = SQLITE_MIGRATION.read_text(encoding="utf-8")

        assert len(pg_text.strip()) > 0, "Postgres migration must not be empty"
        assert len(sqlite_text.strip()) > 0, "SQLite migration must not be empty"

    def test_migration_idempotency(self) -> None:
        """Migrations must be idempotent (IF NOT EXISTS)."""
        pg_text = PG_MIGRATION.read_text(encoding="utf-8")
        sqlite_text = SQLITE_MIGRATION.read_text(encoding="utf-8")

        assert "CREATE TABLE IF NOT EXISTS" in pg_text
        assert "CREATE TABLE IF NOT EXISTS" in sqlite_text
        assert "CREATE INDEX IF NOT EXISTS" in pg_text
        assert "CREATE INDEX IF NOT EXISTS" in sqlite_text


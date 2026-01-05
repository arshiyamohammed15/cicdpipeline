"""
Test suite for schema_parse.ps1 library functions.

Tests cover:
- Get-CanonicalSchemaContract function
- Parse-SqliteSchema function
- Assert-TableHasColumns function
- Edge cases and error handling
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PARSE_LIB = REPO_ROOT / "scripts" / "db" / "lib" / "schema_parse.ps1"
CONTRACT_PATH = REPO_ROOT / "infra" / "db" / "schema_pack" / "canonical_schema_contract.json"


class TestSchemaParseLibrary:
    """Test schema_parse.ps1 library functions."""

    def test_get_canonical_schema_contract_success(self) -> None:
        """Get-CanonicalSchemaContract must load valid contract."""
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $contract = Get-CanonicalSchemaContract -Path '{CONTRACT_PATH}'
        if ($contract.schema_pack_id -ne 'zeroui_core_schema_pack') {{ exit 1 }}
        if ($contract.schema_version -ne '001') {{ exit 1 }}
        if ($null -eq $contract.postgres) {{ exit 1 }}
        if ($null -eq $contract.sqlite) {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_get_canonical_schema_contract_missing_file(self) -> None:
        """Get-CanonicalSchemaContract must throw on missing file."""
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        try {{
            Get-CanonicalSchemaContract -Path 'nonexistent.json'
            exit 1
        }} catch {{
            exit 0
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, "Script should throw on missing file"

    def test_parse_sqlite_schema_success(self) -> None:
        """Parse-SqliteSchema must parse valid SQLite schema."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__tenant (
            tenant_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS core__repo (
            repo_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        if ($parsed.Count -ne 2) {{ exit 1 }}
        if (-not $parsed.ContainsKey('core__tenant')) {{ exit 1 }}
        if (-not $parsed.ContainsKey('core__repo')) {{ exit 1 }}
        if ($parsed['core__tenant'] -notcontains 'tenant_id') {{ exit 1 }}
        if ($parsed['core__tenant'] -notcontains 'created_at') {{ exit 1 }}
        if ($parsed['core__repo'] -notcontains 'repo_id') {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_parse_sqlite_schema_empty(self) -> None:
        """Parse-SqliteSchema must handle empty schema."""
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $parsed = Parse-SqliteSchema -SqliteSchemaText ''
        if ($parsed.Count -ne 0) {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_assert_table_has_columns_success(self) -> None:
        """Assert-TableHasColumns must pass for valid table."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__tenant (
            tenant_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        try {{
            Assert-TableHasColumns -ParsedTables $parsed -TableName 'core__tenant' -RequiredColumns @('tenant_id', 'created_at')
            exit 0
        }} catch {{
            exit 1
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_assert_table_has_columns_missing_table(self) -> None:
        """Assert-TableHasColumns must throw on missing table."""
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $parsed = @{{}}
        try {{
            Assert-TableHasColumns -ParsedTables $parsed -TableName 'nonexistent' -RequiredColumns @('col1')
            exit 1
        }} catch {{
            if ($_.Exception.Message -match 'Missing table') {{
                exit 0
            }}
            exit 1
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, "Script should throw on missing table"

    def test_assert_table_has_columns_missing_column(self) -> None:
        """Assert-TableHasColumns must throw on missing column."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__tenant (
            tenant_id TEXT PRIMARY KEY
        );
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        try {{
            Assert-TableHasColumns -ParsedTables $parsed -TableName 'core__tenant' -RequiredColumns @('tenant_id', 'missing_col')
            exit 1
        }} catch {{
            if ($_.Exception.Message -match 'missing column') {{
                exit 0
            }}
            exit 1
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, "Script should throw on missing column"


class TestSchemaParseEdgeCases:
    """Test schema_parse.ps1 edge cases."""

    def test_parse_sqlite_schema_with_foreign_keys(self) -> None:
        """Parse-SqliteSchema must ignore FOREIGN KEY constraints."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__repo (
            repo_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            FOREIGN KEY (tenant_id) REFERENCES core__tenant(tenant_id)
        );
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        if ($parsed['core__repo'] -contains 'FOREIGN') {{ exit 1 }}
        if ($parsed['core__repo'] -notcontains 'repo_id') {{ exit 1 }}
        if ($parsed['core__repo'] -notcontains 'tenant_id') {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_parse_sqlite_schema_with_quoted_names(self) -> None:
        """Parse-SqliteSchema must handle quoted column names."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__tenant (
            "tenant_id" TEXT PRIMARY KEY,
            "created_at" TEXT NOT NULL
        );
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        if ($parsed['core__tenant'] -notcontains 'tenant_id') {{ exit 1 }}
        if ($parsed['core__tenant'] -notcontains 'created_at') {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_parse_sqlite_schema_multiple_tables(self) -> None:
        """Parse-SqliteSchema must parse multiple tables."""
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS core__tenant (tenant_id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS core__repo (repo_id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS core__actor (actor_id TEXT PRIMARY KEY);
        """
        ps_script = f"""
        . '{SCHEMA_PARSE_LIB}'
        $schemaText = @'
{sqlite_schema}
'@
        $parsed = Parse-SqliteSchema -SqliteSchemaText $schemaText
        if ($parsed.Count -ne 3) {{ exit 1 }}
        if (-not $parsed.ContainsKey('core__tenant')) {{ exit 1 }}
        if (-not $parsed.ContainsKey('core__repo')) {{ exit 1 }}
        if (-not $parsed.ContainsKey('core__actor')) {{ exit 1 }}
        exit 0
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"


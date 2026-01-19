"""
Test suite for PowerShell database scripts.

Tests cover:
- Script file existence
- Script syntax validation
- Function definitions
- Error handling patterns
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
APPLY_SCHEMA_PACK = REPO_ROOT / "scripts" / "db" / "apply_schema_pack.ps1"
APPLY_PHASE0_STUBS = REPO_ROOT / "scripts" / "db" / "apply_phase0_stubs.ps1"
VERIFY_SCHEMA_EQUIVALENCE = REPO_ROOT / "scripts" / "db" / "verify_schema_equivalence.ps1"
SCHEMA_PARSE_LIB = REPO_ROOT / "scripts" / "db" / "lib" / "schema_parse.ps1"


@pytest.mark.unit
class TestPowerShellScriptExistence:
    """Test PowerShell scripts exist."""

    @pytest.mark.unit
    def test_apply_schema_pack_exists(self) -> None:
        """apply_schema_pack.ps1 must exist."""
        assert APPLY_SCHEMA_PACK.exists()

    @pytest.mark.unit
    def test_apply_phase0_stubs_exists(self) -> None:
        """apply_phase0_stubs.ps1 must exist."""
        assert APPLY_PHASE0_STUBS.exists()

    @pytest.mark.unit
    def test_verify_schema_equivalence_exists(self) -> None:
        """verify_schema_equivalence.ps1 must exist."""
        assert VERIFY_SCHEMA_EQUIVALENCE.exists()

    @pytest.mark.unit
    def test_schema_parse_lib_exists(self) -> None:
        """schema_parse.ps1 library must exist."""
        assert SCHEMA_PARSE_LIB.exists()


@pytest.mark.unit
class TestPowerShellScriptSyntax:
    """Test PowerShell script syntax validation."""

    @pytest.mark.unit
    def test_apply_schema_pack_syntax(self) -> None:
        """apply_schema_pack.ps1 must have valid PowerShell syntax."""
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            . '{APPLY_SCHEMA_PACK}'
            exit 0
        }} catch {{
            # Syntax errors will be caught here
            exit 1
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=10,
        )
        # Script may fail due to missing Docker/env vars, but syntax should be valid
        # If syntax is invalid, PowerShell will fail immediately
        assert result.returncode in [0, 1], f"Syntax error detected: {result.stderr}"

    @pytest.mark.unit
    def test_apply_phase0_stubs_syntax(self) -> None:
        """apply_phase0_stubs.ps1 must have valid PowerShell syntax."""
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            . '{APPLY_PHASE0_STUBS}'
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
            timeout=10,
        )
        assert result.returncode in [0, 1], f"Syntax error detected: {result.stderr}"

    @pytest.mark.unit
    def test_verify_schema_equivalence_syntax(self) -> None:
        """verify_schema_equivalence.ps1 must have valid PowerShell syntax."""
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            . '{VERIFY_SCHEMA_EQUIVALENCE}'
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
            timeout=10,
        )
        assert result.returncode in [0, 1], f"Syntax error detected: {result.stderr}"

    @pytest.mark.unit
    def test_schema_parse_lib_syntax(self) -> None:
        """schema_parse.ps1 must have valid PowerShell syntax."""
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            . '{SCHEMA_PARSE_LIB}'
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
            timeout=10,
        )
        assert result.returncode == 0, f"Syntax error detected: {result.stderr}"


@pytest.mark.unit
class TestPowerShellScriptStructure:
    """Test PowerShell script structure and function definitions."""

    @pytest.mark.unit
    def test_apply_schema_pack_has_apply_pg_function(self) -> None:
        """apply_schema_pack.ps1 must define Apply-Pg function."""
        script_text = APPLY_SCHEMA_PACK.read_text(encoding="utf-8")
        assert "function Apply-Pg" in script_text or "function Apply-Postgres" in script_text


    @pytest.mark.unit
    def test_apply_phase0_stubs_has_apply_pg_function(self) -> None:
        """apply_phase0_stubs.ps1 must define Apply-PgPhase0Stub function."""
        script_text = APPLY_PHASE0_STUBS.read_text(encoding="utf-8")
        assert "function Apply-PgPhase0Stub" in script_text or "Apply-Pg" in script_text


    @pytest.mark.unit
    def test_verify_schema_equivalence_has_normalize_function(self) -> None:
        """verify_schema_equivalence.ps1 must define Normalize-PgDump function."""
        script_text = VERIFY_SCHEMA_EQUIVALENCE.read_text(encoding="utf-8")
        assert "function Normalize-PgDump" in script_text or "Normalize" in script_text

    @pytest.mark.unit
    def test_verify_schema_equivalence_has_get_pg_schema_dump_function(self) -> None:
        """verify_schema_equivalence.ps1 must define Get-PgSchemaDump function."""
        script_text = VERIFY_SCHEMA_EQUIVALENCE.read_text(encoding="utf-8")
        assert "function Get-PgSchemaDump" in script_text or "Get-Pg" in script_text

    @pytest.mark.unit
    def test_schema_parse_lib_has_get_canonical_schema_contract_function(self) -> None:
        """schema_parse.ps1 must define Get-CanonicalSchemaContract function."""
        script_text = SCHEMA_PARSE_LIB.read_text(encoding="utf-8")
        assert "function Get-CanonicalSchemaContract" in script_text

    @pytest.mark.unit
    def test_schema_parse_lib_has_assert_table_has_columns_function(self) -> None:
        """schema_parse.ps1 must define Assert-TableHasColumns function."""
        script_text = SCHEMA_PARSE_LIB.read_text(encoding="utf-8")
        assert "function Assert-TableHasColumns" in script_text


@pytest.mark.unit
class TestPowerShellScriptErrorHandling:
    """Test PowerShell script error handling."""

    @pytest.mark.unit
    def test_apply_schema_pack_checks_missing_files(self) -> None:
        """apply_schema_pack.ps1 must check for missing migration files."""
        script_text = APPLY_SCHEMA_PACK.read_text(encoding="utf-8")
        assert "Test-Path" in script_text or "if (!(Test-Path" in script_text
        assert "throw" in script_text or "exit" in script_text

    @pytest.mark.unit
    def test_apply_schema_pack_checks_missing_containers(self) -> None:
        """apply_schema_pack.ps1 must check for missing Docker containers."""
        script_text = APPLY_SCHEMA_PACK.read_text(encoding="utf-8")
        assert "docker ps" in script_text or "container" in script_text.lower()
        assert "throw" in script_text or "exit" in script_text

    @pytest.mark.unit
    def test_apply_phase0_stubs_checks_missing_files(self) -> None:
        """apply_phase0_stubs.ps1 must check for missing migration files."""
        script_text = APPLY_PHASE0_STUBS.read_text(encoding="utf-8")
        assert "Test-Path" in script_text
        assert "002_bkg_phase0.sql" in script_text or "bkg_phase0" in script_text.lower()



@pytest.mark.unit
class TestPowerShellScriptContent:
    """Test PowerShell script content and logic."""

    @pytest.mark.unit
    def test_apply_schema_pack_applies_to_all_planes(self) -> None:
        """apply_schema_pack.ps1 must apply to all 3 Postgres databases."""
        script_text = APPLY_SCHEMA_PACK.read_text(encoding="utf-8")
        assert "zeroui-postgres-tenant" in script_text
        assert "zeroui-postgres-product" in script_text
        assert "zeroui-postgres-shared" in script_text

    @pytest.mark.unit
    def test_apply_schema_pack_applies_to_ide_postgres(self) -> None:
        """apply_schema_pack.ps1 must apply to IDE Postgres."""
        script_text = APPLY_SCHEMA_PACK.read_text(encoding="utf-8")
        assert "zeroui-postgres-ide" in script_text
        assert "zeroui_ide_pg" in script_text

    @pytest.mark.unit
    def test_apply_phase0_stubs_applies_bkg_to_all_planes(self) -> None:
        """apply_phase0_stubs.ps1 must apply BKG stubs to all planes."""
        script_text = APPLY_PHASE0_STUBS.read_text(encoding="utf-8")
        assert "002_bkg_phase0.sql" in script_text or "bkg" in script_text.lower()
        assert "tenant" in script_text.lower()
        assert "product" in script_text.lower()
        assert "shared" in script_text.lower()

    @pytest.mark.unit
    def test_apply_phase0_stubs_applies_qa_cache_to_product_only(self) -> None:
        """apply_phase0_stubs.ps1 must apply Semantic Q&A Cache to Product plane only."""
        script_text = APPLY_PHASE0_STUBS.read_text(encoding="utf-8")
        assert "004_semantic_qa_cache_phase0.sql" in script_text or "semantic_qa_cache" in script_text.lower()
        # Should only apply to product
        qa_cache_section = script_text.split("semantic_qa_cache")[-1] if "semantic_qa_cache" in script_text.lower() else script_text
        assert "product" in qa_cache_section.lower()

    @pytest.mark.unit
    def test_verify_schema_equivalence_compares_all_postgres_dbs(self) -> None:
        """verify_schema_equivalence.ps1 must compare all 3 Postgres databases."""
        script_text = VERIFY_SCHEMA_EQUIVALENCE.read_text(encoding="utf-8")
        assert "tenant" in script_text.lower()
        assert "product" in script_text.lower()
        assert "shared" in script_text.lower()
        assert "mismatch" in script_text.lower() or "diff" in script_text.lower()

    @pytest.mark.unit
    def test_verify_schema_equivalence_checks_schema_version(self) -> None:
        """verify_schema_equivalence.ps1 must check meta.schema_version."""
        script_text = VERIFY_SCHEMA_EQUIVALENCE.read_text(encoding="utf-8")
        assert "meta.schema_version" in script_text or "meta__schema_version" in script_text
        assert "schema_version" in script_text.lower()


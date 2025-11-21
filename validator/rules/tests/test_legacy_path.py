"""
Legacy constitution test path shim.

Running ``pytest validator/rules/tests`` used to execute constitution suites
directly under ``validator/rules``. The canonical suites now live under the
top-level ``tests`` package, so this shim instructs callers to use the updated
command instead of failing with a missing-directory error.
"""

from pathlib import Path

LEGACY_MESSAGE = (
    'Legacy path deprecated. Run `python -m pytest tests -k "constitution" -q` instead.'
)


def _tests_root() -> Path:
    return Path(__file__).resolve().parents[3] / "tests"


def _constitution_suites() -> list[Path]:
    return sorted(_tests_root().rglob("test_*constitution*.py"))


def test_legacy_constitution_command_deprecated():
    suites = _constitution_suites()
    assert suites, (
        "Expected constitution suites under the canonical `tests/` package. "
        f"Please verify repository layout near {_tests_root()}."
    )
    for path in suites:
        assert path.is_file(), f"Constitution suite path missing: {path}"
    assert LEGACY_MESSAGE.endswith('"constitution" -q` instead.')


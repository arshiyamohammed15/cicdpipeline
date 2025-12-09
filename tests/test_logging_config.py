from __future__ import annotations

from pathlib import Path

from config.constitution.logging_config import ConstitutionLogger


def test_logger_uses_external_root(tmp_path, monkeypatch):
    log_root = tmp_path / "external-root"
    monkeypatch.setenv("ZEROU_LOG_ROOT", str(log_root))

    logger = ConstitutionLogger()

    expected = (log_root / ConstitutionLogger.LOG_SUBDIRECTORY).resolve()
    assert logger.log_dir == expected
    assert expected.exists()
    repo_root = Path(__file__).resolve().parents[1]
    assert not logger.log_dir.is_relative_to(repo_root)


def test_logger_skips_repo_paths(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    inside_repo = repo_root / "config" / "logs"
    monkeypatch.setenv("ZEROU_LOG_ROOT", str(inside_repo))

    home_dir = tmp_path / "user-profile"
    home_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    monkeypatch.setenv("HOME", str(home_dir))

    logger = ConstitutionLogger()

    assert not logger.log_dir.is_relative_to(repo_root)
    assert logger.log_dir.name == ConstitutionLogger.LOG_SUBDIRECTORY

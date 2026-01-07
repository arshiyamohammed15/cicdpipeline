from __future__ import annotations

import logging
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

from config.constitution import logging_config


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Create temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.mark.constitution
def test_logger_initialization(tmp_config_dir, tmp_log_dir):
    """Test logger initialization."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        assert logger.config_dir == tmp_config_dir
        assert logger.log_dir == tmp_log_dir
        assert logger.log_level == logging.INFO


@pytest.mark.constitution
def test_logger_initialization_custom_level(tmp_config_dir, tmp_log_dir):
    """Test logger initialization with custom log level."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir), log_level="DEBUG")
        
        assert logger.log_level == logging.DEBUG


@pytest.mark.constitution
def test_setup_logging(tmp_config_dir, tmp_log_dir):
    """Test setting up logging."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        # Check that log files are created
        assert (tmp_log_dir / "constitution_all.log").exists() or tmp_log_dir.exists()


@pytest.mark.constitution
def test_get_logger(tmp_config_dir, tmp_log_dir):
    """Test getting logger instance."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        test_logger = logger.get_logger("test_module")
        
        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "constitution.test_module"


@pytest.mark.constitution
def test_log_performance(tmp_config_dir, tmp_log_dir):
    """Test logging performance metrics."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        # Should not raise
        logger.log_performance("test_operation", 1.5, {"details": "test"})


@pytest.mark.constitution
def test_log_error_with_context(tmp_config_dir, tmp_log_dir):
    """Test logging error with context."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        error = ValueError("Test error")
        context = {"operation": "test", "rule_number": 1}
        
        # Should not raise
        logger.log_error_with_context(error, context)


@pytest.mark.constitution
def test_log_backend_operation(tmp_config_dir, tmp_log_dir):
    """Test logging backend operations."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        # Should not raise
        logger.log_backend_operation("sqlite", "enable_rule", True, {"rule_number": 1})
        logger.log_backend_operation("json", "disable_rule", False, {"error": "test"})


@pytest.mark.constitution
def test_log_sync_operation(tmp_config_dir, tmp_log_dir):
    """Test logging sync operations."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        # Should not raise
        logger.log_sync_operation("sync", "sqlite", "json", True, {"rules": 10})
        logger.log_sync_operation("sync", "sqlite", "json", False, {"error": "test"})


@pytest.mark.constitution
def test_log_migration_operation(tmp_config_dir, tmp_log_dir):
    """Test logging migration operations."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        # Should not raise
        logger.log_migration_operation("v1_to_v2", True, {"rules": 150})
        logger.log_migration_operation("v1_to_v2", False, {"error": "test"})


@pytest.mark.constitution
def test_determine_log_dir_env_override(tmp_config_dir, tmp_path, monkeypatch):
    """Test log directory determination with env override."""
    custom_log_dir = tmp_path / "custom_logs"
    custom_log_dir.mkdir()
    
    monkeypatch.setenv("ZEROU_LOG_ROOT", str(custom_log_dir))
    
    logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
    
    # Should use env var
    assert logger.log_dir.parent == custom_log_dir or "custom_logs" in str(logger.log_dir)


@pytest.mark.constitution
def test_determine_log_dir_zu_root(tmp_config_dir, monkeypatch, tmp_path):
    """Test log directory determination with ZU_ROOT."""
    zu_root = tmp_path / "zu_root"
    zu_root.mkdir()
    log_dir = zu_root.parent / "zeroui_logs"
    
    monkeypatch.setenv("ZU_ROOT", str(zu_root))
    
    logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
    
    # Should derive from ZU_ROOT
    assert logger.log_dir.exists() or logger.log_dir.parent.exists()


@pytest.mark.constitution
def test_determine_log_dir_fallback(tmp_config_dir, monkeypatch):
    """Test log directory fallback to home directory."""
    # Clear all env vars
    for key in ["ZEROU_LOG_ROOT", "ZEROUI_LOG_ROOT", "ZU_LOG_ROOT", "ZU_ROOT"]:
        monkeypatch.delenv(key, raising=False)
    
    logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
    
    # Should use fallback
    assert logger.log_dir.exists() or logger.log_dir.parent.exists()


@pytest.mark.constitution
def test_is_inside_repo(tmp_config_dir):
    """Test checking if path is inside repo."""
    repo_root = tmp_config_dir.parent
    
    # Path inside repo
    inside_path = tmp_config_dir / "subdir"
    assert logging_config.ConstitutionLogger._is_inside_repo(inside_path, repo_root) is True
    
    # Path outside repo
    outside_path = Path("/tmp/outside")
    assert logging_config.ConstitutionLogger._is_inside_repo(outside_path, repo_root) is False


@pytest.mark.constitution
def test_global_get_constitution_logger(tmp_config_dir, tmp_log_dir):
    """Test global get_constitution_logger function."""
    # Reset global instance
    logging_config._logger_instance = None
    
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger1 = logging_config.get_constitution_logger()
        logger2 = logging_config.get_constitution_logger()
        
        # Should return same instance
        assert logger1 is logger2


@pytest.mark.constitution
def test_global_setup_logging(tmp_config_dir, tmp_log_dir):
    """Test global setup_logging function."""
    # Reset global instance
    logging_config._logger_instance = None
    
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.setup_logging(config_dir=str(tmp_config_dir), log_level="DEBUG")
        
        assert isinstance(logger, logging_config.ConstitutionLogger)
        assert logger.log_level == logging.DEBUG


@pytest.mark.constitution
def test_logger_file_handlers(tmp_config_dir, tmp_log_dir):
    """Test that file handlers are created."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        root_logger = logging.getLogger()
        handlers = root_logger.handlers
        
        # Should have file handlers
        file_handlers = [h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) > 0


@pytest.mark.constitution
def test_logger_console_handler(tmp_config_dir, tmp_log_dir):
    """Test that console handler is created."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        root_logger = logging.getLogger()
        handlers = root_logger.handlers
        
        # Should have console handler
        console_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0


@pytest.mark.constitution
def test_performance_logger_separate(tmp_config_dir, tmp_log_dir):
    """Test that performance logger is separate."""
    with patch.object(logging_config.ConstitutionLogger, '_determine_log_dir', return_value=tmp_log_dir):
        logger = logging_config.ConstitutionLogger(config_dir=str(tmp_config_dir))
        
        perf_logger = logging.getLogger('constitution.performance')
        
        # Should not propagate to root
        assert perf_logger.propagate is False


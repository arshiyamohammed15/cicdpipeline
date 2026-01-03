#!/usr/bin/env python3
"""
Logging Configuration for Constitution Rules Database

This module provides centralized logging configuration for all constitution
rule management components.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class ConstitutionLogger:
    """
    Centralized logging configuration for constitution rules system.

    Features:
    - Structured logging with consistent format
    - File and console handlers
    - Log rotation for large files
    - Performance monitoring
    - Error tracking
    """

    LOG_SUBDIRECTORY = "constitution"

    def __init__(
        self,
        config_dir: str = "config",
        log_level: str = "INFO",
        log_root: Optional[str] = None,
    ):
        """
        Initialize the logging system.

        Args:
            config_dir: Configuration directory path
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_root: Optional override for the external log root (defaults to env vars or user profile)
        """
        self.config_dir = Path(config_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = self._determine_log_dir(log_root)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration."""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Close and clear existing handlers to avoid file descriptor leaks
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

        # File handler for all logs
        all_logs_file = self.log_dir / "constitution_all.log"
        file_handler = logging.handlers.RotatingFileHandler(
            all_logs_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        # Error log file
        error_log_file = self.log_dir / "constitution_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

        # Performance log file
        perf_log_file = self.log_dir / "constitution_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)

        # Create performance logger
        perf_logger = logging.getLogger('constitution.performance')
        for handler in list(perf_logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
        perf_logger.handlers.clear()
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific component.

        Args:
            name: Logger name (usually module name)

        Returns:
            Logger instance
        """
        return logging.getLogger(f'constitution.{name}')

    def log_performance(self, operation: str, duration: float, details: Optional[dict] = None):
        """
        Log performance metrics.

        Args:
            operation: Operation name
            duration: Duration in seconds
            details: Additional details
        """
        perf_logger = logging.getLogger('constitution.performance')
        message = f"PERF: {operation} took {duration:.3f}s"
        if details:
            message += f" - {details}"
        perf_logger.info(message)

    def log_error_with_context(self, error: Exception, context: dict):
        """
        Log error with additional context.

        Args:
            error: Exception instance
            context: Additional context information
        """
        logger = logging.getLogger('constitution.errors')
        logger.error(f"Error: {error} - Context: {context}", exc_info=True)

    def log_backend_operation(self, backend: str, operation: str, success: bool, details: Optional[dict] = None):
        """
        Log backend operations.

        Args:
            backend: Backend name (sqlite, json)
            operation: Operation name
            success: Whether operation succeeded
            details: Additional details
        """
        logger = logging.getLogger(f'constitution.backend.{backend}')
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation}: {status}"
        if details:
            message += f" - {details}"

        if success:
            logger.info(message)
        else:
            logger.error(message)

    def log_sync_operation(self, operation: str, source: str, target: str, success: bool, details: Optional[dict] = None):
        """
        Log synchronization operations.

        Args:
            operation: Sync operation name
            source: Source backend
            target: Target backend
            success: Whether operation succeeded
            details: Additional details
        """
        logger = logging.getLogger('constitution.sync')
        status = "SUCCESS" if success else "FAILED"
        message = f"SYNC {source}->{target}: {operation} - {status}"
        if details:
            message += f" - {details}"

        if success:
            logger.info(message)
        else:
            logger.error(message)

    def log_migration_operation(self, migration_type: str, success: bool, details: Optional[dict] = None):
        """
        Log migration operations.

        Args:
            migration_type: Type of migration
            success: Whether operation succeeded
            details: Additional details
        """
        logger = logging.getLogger('constitution.migration')
        status = "SUCCESS" if success else "FAILED"
        message = f"MIGRATION {migration_type}: {status}"
        if details:
            message += f" - {details}"

        if success:
            logger.info(message)
        else:
            logger.error(message)

    def _determine_log_dir(self, override: Optional[str]) -> Path:
        """
        Resolve a log directory that lives outside the repository tree.
        Preference order:
          1. Explicit override (argument)
          2. Env vars: ZEROU_LOG_ROOT, ZEROUI_LOG_ROOT, ZU_LOG_ROOT
          3. Derived from ZU_ROOT sibling (../zeroui_logs)
          4. User profile fallback (~/ZeroUI/zeroui_logs)
        """
        repo_root = Path(__file__).resolve().parents[2]

        candidates = [
            override,
            os.environ.get("ZEROU_LOG_ROOT"),
            os.environ.get("ZEROUI_LOG_ROOT"),
            os.environ.get("ZU_LOG_ROOT"),
        ]

        zu_root = os.environ.get("ZU_ROOT")
        if zu_root:
            parent = Path(zu_root).expanduser().resolve().parent
            candidates.append(str(parent / "zeroui_logs"))

        for candidate in candidates:
            resolved = self._prepare_candidate(candidate, repo_root)
            if resolved is not None:
                return resolved

        fallback_root = Path.home() / "ZeroUI" / "zeroui_logs"
        return (fallback_root / self.LOG_SUBDIRECTORY).expanduser().resolve()

    def _prepare_candidate(
        self, raw_path: Optional[str], repo_root: Path
    ) -> Optional[Path]:
        if not raw_path:
            return None

        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            base = Path(
                os.environ.get("ZU_ROOT", Path.home())
            ).expanduser()
            candidate = base / candidate

        candidate = (candidate / self.LOG_SUBDIRECTORY).resolve()

        if self._is_inside_repo(candidate, repo_root):
            return None

        return candidate

    @staticmethod
    def _is_inside_repo(path: Path, repo_root: Path) -> bool:
        try:
            path.relative_to(repo_root)
            return True
        except ValueError:
            return False


# Global logger instance
_logger_instance: Optional[ConstitutionLogger] = None


def get_constitution_logger(log_root: Optional[str] = None) -> ConstitutionLogger:
    """Get the global constitution logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConstitutionLogger(log_root=log_root)
    return _logger_instance


def setup_logging(
    config_dir: str = "config", log_level: str = "INFO", log_root: Optional[str] = None
):
    """Set up logging for the constitution system."""
    global _logger_instance
    _logger_instance = ConstitutionLogger(config_dir, log_level, log_root)
    return _logger_instance

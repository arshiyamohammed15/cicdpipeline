"""
LLM process manager for Ollama AI Agent service.

What: Manages Ollama process lifecycle (start/stop/status) using shared services configuration
Why: Enables automatic startup of Ollama when FastAPI starts, ensures proper process management
Reads/Writes: Reads configuration from shared/llm/ollama/config.json, manages subprocess for Ollama executable
Contracts: Subprocess management contract, configuration contract
Risks: Process startup failures, port conflicts, executable not found, process cleanup on shutdown
"""

import os
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


def _load_shared_services_config(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from shared services plane.

    Args:
        config_type: Type of configuration ('ollama' or 'tinyllama')

    Returns:
        Configuration dictionary, or empty dict if not found
    """
    try:
        # Get ZU_ROOT from environment variable (per folder-business-rules.md)
        zu_root = os.getenv("ZU_ROOT")
        
        if zu_root:
            # Use ZU_ROOT for shared services plane
            config_path = Path(zu_root) / "shared" / "llm" / config_type / "config.json"
        else:
            # Fallback: try project root (for development/testing)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent.parent
            config_path = project_root / "shared" / "llm" / config_type / "config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Replace {ZU_ROOT} placeholder if present
                zu_root = zu_root or ""
                if zu_root:
                    for key, value in config.items():
                        if isinstance(value, str) and "{ZU_ROOT}" in value:
                            config[key] = value.replace("{ZU_ROOT}", zu_root)
                return config
    except Exception as e:
        logger.warning(f"Failed to load config for {config_type}: {e}")
    
    return {}


def _get_ollama_executable_path() -> Optional[str]:
    """
    Get the Ollama executable path from configuration.

    Returns:
        Path to Ollama executable, or None if not found
    """
    config = _load_shared_services_config("ollama")
    executable_path = config.get("executable_path", "")
    
    # Replace {ZU_ROOT} placeholder if present
    zu_root = os.getenv("ZU_ROOT", "")
    if zu_root and "{ZU_ROOT}" in executable_path:
        executable_path = executable_path.replace("{ZU_ROOT}", zu_root)
    
    if executable_path and Path(executable_path).exists():
        return executable_path
    
    # Try default location
    if zu_root:
        default_path = Path(zu_root) / "shared" / "llm" / "ollama" / "bin" / "ollama.exe"
        if default_path.exists():
            return str(default_path)
    
    return None


def _is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama service is already running.

    Args:
        base_url: Base URL for Ollama API

    Returns:
        True if Ollama is running, False otherwise
    """
    try:
        config = _load_shared_services_config("ollama")
        api_endpoints = config.get("api_endpoints", {})
        tags_path = api_endpoints.get("tags", "/api/tags")
        tags_endpoint = f"{base_url}{tags_path}"
        
        response = requests.get(tags_endpoint, timeout=2)
        return response.status_code == 200
    except Exception:
        return False


class OllamaProcessManager:
    """Manages Ollama process lifecycle."""

    def __init__(self):
        """Initialize the Ollama process manager."""
        self.process: Optional[subprocess.Popen] = None
        self.config = _load_shared_services_config("ollama")
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.auto_start = self.config.get("auto_start", True)
        self.executable_path = _get_ollama_executable_path()

    def start(self) -> bool:
        """
        Start the Ollama process.

        Returns:
            True if started successfully, False otherwise
        """
        # Check if already running
        if _is_ollama_running(self.base_url):
            logger.info("Ollama service is already running")
            return True

        # Check if auto_start is enabled
        if not self.auto_start:
            logger.info("Ollama auto_start is disabled in configuration")
            return False

        # Check if executable exists
        if not self.executable_path:
            logger.error("Ollama executable not found. Check configuration.")
            return False

        if not Path(self.executable_path).exists():
            logger.error(f"Ollama executable not found at: {self.executable_path}")
            return False

        try:
            logger.info(f"Starting Ollama service from: {self.executable_path}")
            
            # Start Ollama in background
            self.process = subprocess.Popen(
                [self.executable_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Wait a bit and check if process is still running
            time.sleep(2)
            if self.process.poll() is not None:
                # Process exited immediately, likely an error
                stdout, stderr = self.process.communicate()
                logger.error(f"Ollama process exited immediately. stderr: {stderr.decode() if stderr else 'None'}")
                return False

            # Wait for service to be available
            max_attempts = 10
            for attempt in range(max_attempts):
                if _is_ollama_running(self.base_url):
                    logger.info("Ollama service started successfully")
                    return True
                time.sleep(1)

            logger.warning("Ollama process started but service not yet available")
            return True  # Process is running, may just need more time

        except Exception as e:
            logger.error(f"Failed to start Ollama service: {e}")
            return False

    def stop(self) -> None:
        """Stop the Ollama process."""
        if self.process:
            try:
                logger.info("Stopping Ollama service")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Ollama process did not terminate gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait()
                self.process = None
                logger.info("Ollama service stopped")
            except Exception as e:
                logger.error(f"Error stopping Ollama service: {e}")

    def is_running(self) -> bool:
        """
        Check if Ollama process is running.

        Returns:
            True if running, False otherwise
        """
        if self.process:
            return self.process.poll() is None
        return _is_ollama_running(self.base_url)


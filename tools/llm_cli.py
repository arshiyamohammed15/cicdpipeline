#!/usr/bin/env python3
"""
CLI tool for interacting with the LLM Service in the shared plane.

What: Command-line interface for the Ollama AI Agent service using shared services configuration
Why: Provides easy access to LLM functionality from the command line, uses shared/llm/ollama and shared/llm/tinyllama configs
Reads/Writes: Reads command-line arguments, writes HTTP requests to LLM service. Service reads from shared/llm/ollama/config.json and shared/llm/tinyllama/config.json
Contracts: LLM Service API contract (/api/v1/prompt, /api/v1/health)
Risks: Network failures, service unavailability, invalid responses
"""

import argparse
import json
import sys
import os
import subprocess
import time
import socket
from pathlib import Path
from typing import Optional, Dict, Any
import requests


class LLMCLI:
    """CLI client for the LLM Service."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the LLM CLI client.

        Args:
            base_url: Base URL for the LLM service (default: http://localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.prompt_endpoint = f"{self.base_url}/api/v1/prompt"
        self.health_endpoint = f"{self.base_url}/api/v1/health"
        self.timeout = int(os.getenv("LLM_CLI_TIMEOUT", "120"))

    def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of the LLM service.

        Returns:
            Health status response
        """
        try:
            response = requests.get(self.health_endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "error": "CONNECTION_ERROR",
                "message": f"Could not connect to LLM service at {self.base_url}",
                "suggestion": f"Start the service with: python {Path(__file__).name} --start-service"
            }
        except requests.exceptions.Timeout:
            return {
                "error": "TIMEOUT_ERROR",
                "message": "Health check request timed out",
                "suggestion": "The service may be overloaded or unavailable"
            }
        except requests.exceptions.HTTPError as e:
            return {
                "error": "HTTP_ERROR",
                "message": f"HTTP error: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {
                "error": "UNKNOWN_ERROR",
                "message": str(e)
            }

    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a prompt to the LLM service.

        Args:
            prompt: The prompt text to send
            model: Model name to use (optional)
            stream: Whether to stream the response (default: False)
            options: Additional model options (optional)

        Returns:
            Response from the LLM service
        """
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "stream": stream
        }

        if model:
            payload["model"] = model

        if options:
            payload["options"] = options

        try:
            response = requests.post(
                self.prompt_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "error": {
                    "code": "CONNECTION_ERROR",
                    "message": f"Could not connect to LLM service at {self.base_url}",
                    "details": f"Start the service with: python {Path(__file__).name} --start-service"
                }
            }
        except requests.exceptions.Timeout:
            return {
                "error": {
                    "code": "TIMEOUT_ERROR",
                    "message": "Request timed out",
                    "details": None
                }
            }
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                return error_data
            except (ValueError, json.JSONDecodeError):
                return {
                    "error": {
                        "code": "HTTP_ERROR",
                        "message": f"HTTP error: {e.response.status_code}",
                        "details": e.response.text
                    }
                }
        except Exception as e:
            return {
                "error": {
                    "code": "UNKNOWN_ERROR",
                    "message": str(e),
                    "details": None
                }
            }

    def format_response(self, response: Dict[str, Any], format_type: str = "console") -> str:
        """
        Format the response for display.

        Args:
            response: The response dictionary
            format_type: Output format (console, json)

        Returns:
            Formatted response string
        """
        if format_type == "json":
            return json.dumps(response, indent=2)

        # Console format
        if "error" in response:
            error = response["error"]
            if isinstance(error, dict):
                code = error.get("code", "UNKNOWN_ERROR")
                message = error.get("message", "Unknown error")
                details = error.get("details")
                result = f"Error: {code}\n{message}"
                if details:
                    result += f"\nDetails: {details}"
                return result
            else:
                return f"Error: {response.get('message', 'Unknown error')}"

        # Success response
        output = []
        if "success" in response:
            output.append(f"Success: {response['success']}")
        if "response" in response:
            output.append(f"\nResponse:\n{response['response']}")
        if "model" in response:
            output.append(f"\nModel: {response['model']}")
        if "timestamp" in response:
            output.append(f"Timestamp: {response['timestamp']}")
        if "metadata" in response and response["metadata"]:
            output.append(f"\nMetadata:")
            for key, value in response["metadata"].items():
                output.append(f"  {key}: {value}")

        return "\n".join(output)

    def format_health(self, health: Dict[str, Any], format_type: str = "console") -> str:
        """
        Format health check response for display.

        Args:
            health: The health response dictionary
            format_type: Output format (console, json)

        Returns:
            Formatted health status string
        """
        if format_type == "json":
            return json.dumps(health, indent=2, default=str)

        # Console format
        if "error" in health:
            error_msg = health.get("message", "Unknown error")
            suggestion = health.get("suggestion", "")
            result = f"❌ Health check failed: {error_msg}"
            if suggestion:
                result += f"\n💡 {suggestion}"
            return result

        status = health.get("status", "unknown")
        ollama_available = health.get("ollama_available", False)
        timestamp = health.get("timestamp", "")

        output = []
        output.append(f"Service Status: {status.upper()}")
        output.append(f"Ollama Available: {'✅ Yes' if ollama_available else '❌ No'}")
        if timestamp:
            output.append(f"Timestamp: {timestamp}")

        return "\n".join(output)


def start_service(port: int = 8000, host: str = "0.0.0.0") -> int:
    """
    Start the LLM service using uvicorn.

    Args:
        port: Port to run the service on (default: 8000)
        host: Host to bind to (default: 0.0.0.0)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        project_root = Path(__file__).parent.parent
        
        # Check if port is already in use
        if is_port_in_use(host, port):
            print(f"Error: Port {port} is already in use", file=sys.stderr)
            print(f"", file=sys.stderr)
            
            # Check if it's our service
            base_url = f"http://localhost:{port}"
            if check_service_running(base_url):
                print(f"💡 The LLM service appears to be already running at {base_url}", file=sys.stderr)
                print(f"   You can check its health with: python {Path(__file__).name} --health", file=sys.stderr)
                print(f"", file=sys.stderr)
            
            # Try to find an available port
            available_port = find_available_port(host, start_port=port + 1)
            if available_port:
                print(f"Options:", file=sys.stderr)
                print(f"  1. Use auto-port (recommended): python {Path(__file__).name} --start-service --auto-port", file=sys.stderr)
                print(f"  2. Use port {available_port} (available): python {Path(__file__).name} --start-service --port {available_port}", file=sys.stderr)
                print(f"  3. Stop the service running on port {port}", file=sys.stderr)
                print(f"  4. Use a different port: python {Path(__file__).name} --start-service --port <different_port>", file=sys.stderr)
            else:
                print(f"Options:", file=sys.stderr)
                print(f"  1. Use auto-port (recommended): python {Path(__file__).name} --start-service --auto-port", file=sys.stderr)
                print(f"  2. Stop the service running on port {port}", file=sys.stderr)
                print(f"  3. Use a different port: python {Path(__file__).name} --start-service --port <different_port>", file=sys.stderr)
            
            return 1
        
        print("=" * 60)
        print("STARTING LLM SERVICE (Ollama AI Agent)")
        print("=" * 60)
        print(f"Service will be available at http://localhost:{port}")
        print(f"API endpoints:")
        print(f"  - Health: http://localhost:{port}/api/v1/health")
        print(f"  - Prompt: http://localhost:{port}/api/v1/prompt")
        print("Press Ctrl+C to stop")
        print("=" * 60)

        # Paths
        service_dir = project_root / "src" / "cloud-services" / "shared-services" / "ollama-ai-agent"
        main_module_path = service_dir / "main.py"
        
        if not main_module_path.exists():
            print(f"Error: Service module not found at {main_module_path}", file=sys.stderr)
            return 1
        
        # Change to the service directory for proper relative imports
        original_cwd = os.getcwd()
        parent_dir = service_dir.parent
        
        try:
            # Set up Python path - add parent directory so relative imports work
            # The relative imports in main.py expect to be in a package
            os.chdir(parent_dir)
            
            # Add parent to path for imports
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            
            # Use importlib to load the module with proper package context
            import importlib.util
            import importlib.machinery
            
            # Create package module first (needed for relative imports)
            package_name = "ollama_ai_agent"
            init_path = service_dir / "__init__.py"
            
            # Load or create package module
            if package_name not in sys.modules:
                if init_path.exists():
                    package_loader = importlib.machinery.SourceFileLoader(
                        package_name,
                        str(init_path)
                    )
                    package_spec = importlib.util.spec_from_loader(
                        package_name,
                        package_loader,
                        origin=str(init_path)
                    )
                    if package_spec and package_spec.loader:
                        package_module = importlib.util.module_from_spec(package_spec)
                        package_module.__path__ = [str(service_dir)]
                        sys.modules[package_name] = package_module
                        package_spec.loader.exec_module(package_module)
                else:
                    # Create minimal package module
                    package_module = type(sys.modules[__name__])(package_name)
                    package_module.__path__ = [str(service_dir)]
                    package_module.__file__ = str(init_path)
                    sys.modules[package_name] = package_module
            
            # Now load main module
            loader = importlib.machinery.SourceFileLoader(
                f"{package_name}.main",
                str(main_module_path)
            )
            spec = importlib.util.spec_from_loader(
                f"{package_name}.main",
                loader,
                origin=str(main_module_path)
            )
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create spec for {main_module_path}")
            
            main_module = importlib.util.module_from_spec(spec)
            main_module.__package__ = package_name
            main_module.__file__ = str(main_module_path)
            
            # Store in sys.modules before executing
            sys.modules[f"{package_name}.main"] = main_module
            
            # Execute the module
            spec.loader.exec_module(main_module)
            
            # Get the app
            if not hasattr(main_module, 'app'):
                raise ImportError(f"Module {main_module_path} does not have an 'app' attribute")
            
            app = main_module.app
            
            # Run uvicorn
            import uvicorn
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info"
            )
            return 0
        finally:
            os.chdir(original_cwd)

    except ImportError as e:
        print(f"Error: Could not import LLM service app: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        print("Make sure you're running from the project root directory", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nShutting down LLM service...")
        return 0
    except OSError as e:
        if e.errno == 10048 or "Address already in use" in str(e) or "only one usage of each socket address" in str(e):
            print(f"Error: Port {port} is already in use", file=sys.stderr)
            print(f"", file=sys.stderr)
            print(f"Options:", file=sys.stderr)
            print(f"  1. Stop the service running on port {port}", file=sys.stderr)
            print(f"  2. Use a different port: python {Path(__file__).name} --start-service --port <different_port>", file=sys.stderr)
            
            # Check if it's our service
            base_url = f"http://localhost:{port}"
            if check_service_running(base_url):
                print(f"", file=sys.stderr)
                print(f"💡 The LLM service appears to be already running at {base_url}", file=sys.stderr)
                print(f"   You can check its health with: python {Path(__file__).name} --health", file=sys.stderr)
        else:
            print(f"Error starting service: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error starting service: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return 1


def check_service_running(base_url: str) -> bool:
    """
    Check if the service is already running.

    Args:
        base_url: Base URL of the service

    Returns:
        True if service is running, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_port_in_use(host: str, port: int) -> bool:
    """
    Check if a port is already in use.

    Args:
        host: Host to check
        port: Port to check

    Returns:
        True if port is in use, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host if host != "0.0.0.0" else "127.0.0.1", port))
            return result == 0
    except Exception:
        return False


def find_available_port(host: str, start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    """
    Find an available port starting from start_port.

    Args:
        host: Host to check
        start_port: Starting port number
        max_attempts: Maximum number of ports to check

    Returns:
        Available port number, or None if none found
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(host, port):
            return port
    return None


def main():
    """Main entry point for the LLM CLI."""
    parser = argparse.ArgumentParser(
        description="CLI tool for interacting with the LLM Service (Shared Services Plane)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --start-service
  %(prog)s --start-service --auto-port
  %(prog)s --health
  %(prog)s --prompt "What is Python?"
  %(prog)s --prompt "Explain async/await" --model "llama2"
  %(prog)s --prompt "Hello" --format json
  %(prog)s --prompt "Test" --base-url http://localhost:8000
  %(prog)s --start-service --port 8001
  %(prog)s --start-service --port 8000 --auto-port
        """
    )

    # Service configuration
    parser.add_argument(
        "--base-url",
        default=os.getenv("LLM_SERVICE_URL", "http://localhost:8000"),
        help="Base URL for the LLM service (default: http://localhost:8000 or LLM_SERVICE_URL env var)"
    )

    # Commands
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        "--health",
        action="store_true",
        help="Check the health status of the LLM service"
    )
    command_group.add_argument(
        "--prompt",
        metavar="TEXT",
        help="Send a prompt to the LLM service"
    )
    command_group.add_argument(
        "--start-service",
        action="store_true",
        help="Start the LLM service"
    )

    # Prompt options
    parser.add_argument(
        "--model",
        help="Model name to use (e.g., 'tinyllama', 'llama2')"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming response (default: False)"
    )
    parser.add_argument(
        "--options",
        help="Additional model options as JSON string (e.g., '{\"temperature\": 0.7}')"
    )

    # Output options
    parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)"
    )

    # Service start options
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the service on (default: 8000, used with --start-service)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the service to (default: 0.0.0.0, used with --start-service)"
    )
    parser.add_argument(
        "--auto-port",
        action="store_true",
        help="Automatically find and use an available port if the requested port is in use (used with --start-service)"
    )

    args = parser.parse_args()

    # Initialize CLI client
    cli = LLMCLI(base_url=args.base_url)

    # Parse options if provided
    options = None
    if args.options:
        try:
            options = json.loads(args.options)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in --options: {args.options}", file=sys.stderr)
            return 1

    # Execute command
    try:
        if args.start_service:
            # Check if service is already running
            if check_service_running(args.base_url):
                print(f"Service is already running at {args.base_url}", file=sys.stderr)
                print("Use --base-url to specify a different URL or stop the existing service", file=sys.stderr)
                return 1
            
            # Handle auto-port selection
            actual_port = args.port
            if args.auto_port and is_port_in_use(args.host, args.port):
                available_port = find_available_port(args.host, start_port=args.port)
                if available_port:
                    print(f"Port {args.port} is in use. Using available port {available_port} instead.", file=sys.stderr)
                    actual_port = available_port
                else:
                    print(f"Error: Could not find an available port starting from {args.port}", file=sys.stderr)
                    return 1
            
            return start_service(port=actual_port, host=args.host)

        elif args.health:
            health = cli.check_health()
            print(cli.format_health(health, args.format))
            # Add helpful suggestion if service is not running
            if "error" in health and "CONNECTION_ERROR" in str(health.get("error", "")):
                print(f"\n💡 Tip: Start the service with: python {Path(__file__).name} --start-service", file=sys.stderr)
            return 0 if "error" not in health else 1

        elif args.prompt:
            response = cli.send_prompt(
                prompt=args.prompt,
                model=args.model,
                stream=args.stream,
                options=options
            )
            print(cli.format_response(response, args.format))
            # Add helpful suggestion if service is not running
            if "error" in response:
                error_code = response.get("error", {}).get("code", "") if isinstance(response.get("error"), dict) else ""
                if "CONNECTION_ERROR" in str(error_code):
                    print(f"\n💡 Tip: Start the service with: python {Path(__file__).name} --start-service", file=sys.stderr)
                return 1
            return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


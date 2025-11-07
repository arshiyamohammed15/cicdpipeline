#!/usr/bin/env python3
"""
CLI tool for managing FastAPI service (start/stop/restart).

What: Command-line interface for managing the FastAPI Ollama AI Agent service
Why: Provides easy control over service lifecycle (start/stop/restart)
Reads/Writes: Reads command-line arguments, manages FastAPI process lifecycle
Contracts: FastAPI service contract, process management contract
Risks: Port conflicts, process management failures, service unavailability
"""

import argparse
import sys
import os
import subprocess
import time
import socket
import re
from pathlib import Path
from typing import Optional, Tuple


def find_process_by_port(port: int) -> Optional[int]:
    """
    Find process ID using the specified port.

    Args:
        port: Port number to check

    Returns:
        Process ID if found, None otherwise
    """
    try:
        # Use netstat to find process using the port
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse netstat output to find LISTENING on the port
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    # Extract PID (last column)
                    parts = line.strip().split()
                    if len(parts) > 0:
                        try:
                            pid = int(parts[-1])
                            return pid
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass
    
    return None


def is_port_in_use(port: int) -> bool:
    """
    Check if a port is in use.

    Args:
        port: Port number to check

    Returns:
        True if port is in use, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception:
        return False


def kill_process(pid: int) -> bool:
    """
    Kill a process by its PID.

    Args:
        pid: Process ID to kill

    Returns:
        True if successful, False otherwise
    """
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        else:  # Unix-like
            result = subprocess.run(
                ["kill", "-9", str(pid)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
    except Exception:
        return False


def stop_service(port: int = 8000) -> int:
    """
    Stop the FastAPI service running on the specified port.

    Args:
        port: Port number where FastAPI is running

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if not is_port_in_use(port):
        print(f"FastAPI service is not running on port {port}")
        return 0
    
    pid = find_process_by_port(port)
    
    if not pid:
        print(f"Could not find process using port {port}")
        return 1
    
    print(f"Stopping FastAPI service (PID: {pid})...")
    
    if kill_process(pid):
        # Wait a moment and verify
        time.sleep(1)
        if not is_port_in_use(port):
            print(f"FastAPI service stopped successfully")
            return 0
        else:
            print(f"Warning: Port {port} may still be in use")
            return 1
    else:
        print(f"Failed to stop FastAPI service (PID: {pid})")
        return 1


def start_service(port: int = 8000, host: str = "0.0.0.0") -> int:
    """
    Start the FastAPI service.

    Args:
        port: Port to run the service on
        host: Host to bind to

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Check if port is already in use
    if is_port_in_use(port):
        print(f"Error: Port {port} is already in use", file=sys.stderr)
        pid = find_process_by_port(port)
        if pid:
            print(f"  Process using port: PID {pid}", file=sys.stderr)
            print(f"  Stop it first with: python {Path(__file__).name} stop", file=sys.stderr)
        return 1
    
    print("=" * 60)
    print("STARTING FASTAPI SERVICE (Ollama AI Agent)")
    print("=" * 60)
    print(f"Service will be available at http://localhost:{port}")
    print(f"API endpoints:")
    print(f"  - Health: http://localhost:{port}/health")
    print(f"  - API: http://localhost:{port}/api/v1/*")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Service directory
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
    except ImportError as e:
        print(f"Error: Could not import FastAPI service app: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        print("Make sure you're running from the project root directory", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nShutting down FastAPI service...")
        return 0
    except OSError as e:
        if e.errno == 10048 or "Address already in use" in str(e) or "only one usage of each socket address" in str(e):
            print(f"Error: Port {port} is already in use", file=sys.stderr)
            print(f"Stop the existing service first with: python {Path(__file__).name} stop", file=sys.stderr)
        else:
            print(f"Error starting service: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error starting service: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        os.chdir(original_cwd)


def restart_service(port: int = 8000, host: str = "0.0.0.0") -> int:
    """
    Restart the FastAPI service (stop then start).

    Args:
        port: Port to run the service on
        host: Host to bind to

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("Restarting FastAPI service...")
    
    # Stop the service
    stop_result = stop_service(port)
    
    if stop_result != 0 and is_port_in_use(port):
        print("Warning: Could not stop existing service, attempting to start anyway...", file=sys.stderr)
    
    # Wait a moment for port to be released
    time.sleep(2)
    
    # Start the service
    return start_service(port, host)


def check_status(port: int = 8000) -> int:
    """
    Check the status of the FastAPI service.

    Args:
        port: Port to check

    Returns:
        Exit code (0 if running, 1 if not running)
    """
    if is_port_in_use(port):
        pid = find_process_by_port(port)
        if pid:
            print(f"FastAPI service is running on port {port} (PID: {pid})")
            return 0
        else:
            print(f"Port {port} is in use but could not identify process")
            return 1
    else:
        print(f"FastAPI service is not running on port {port}")
        return 1


def check_health(port: int = 8000) -> int:
    """
    Check the health status of the FastAPI service via health endpoint.

    Args:
        port: Port to check

    Returns:
        Exit code (0 if healthy, 1 if unhealthy or not running)
    """
    import requests
    
    url = f"http://localhost:{port}/health"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        print(f"FastAPI service health check (port {port}):")
        print(f"  Status: {health_data.get('status', 'unknown')}")
        print(f"  Ollama Available: {health_data.get('ollama_available', False)}")
        print(f"  LLM Name: {health_data.get('llm_name', 'unknown')}")
        print(f"  Model Name: {health_data.get('model_name', 'unknown')}")
        print(f"  Timestamp: {health_data.get('timestamp', 'unknown')}")
        
        if health_data.get('status') == 'healthy':
            return 0
        else:
            return 1
    except requests.exceptions.ConnectionError:
        print(f"FastAPI service is not running on port {port} (connection refused)")
        return 1
    except requests.exceptions.Timeout:
        print(f"FastAPI service health check timed out on port {port}")
        return 1
    except Exception as e:
        print(f"Error checking health: {e}")
        return 1


def check_ollama_status(ollama_port: int = 11434) -> Tuple[bool, Optional[int]]:
    """
    Check if Ollama (LLM) service is running.

    Args:
        ollama_port: Port where Ollama is running (default: 11434)

    Returns:
        Tuple of (is_running, pid) where pid is None if not found
    """
    import requests
    
    # Check if port is in use
    if not is_port_in_use(ollama_port):
        return (False, None)
    
    # Try to find process
    pid = find_process_by_port(ollama_port)
    
    # Verify it's actually Ollama by checking the API
    try:
        url = f"http://localhost:{ollama_port}/api/tags"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return (True, pid)
    except Exception:
        pass
    
    # Port is in use but might not be Ollama
    return (False, pid)


def check_ollama_windows_service() -> Tuple[bool, Optional[str]]:
    """
    Check if Ollama is running as a Windows service.

    Returns:
        Tuple of (is_service, service_name) where service_name is None if not found
    """
    if os.name != 'nt':
        return (False, None)
    
    # Try multiple possible service names
    possible_names = ["Ollama", "ollama", "OLLAMA"]
    
    for service_name in possible_names:
        try:
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Service exists, check if running
                if "RUNNING" in result.stdout:
                    return (True, service_name)
                elif "STOPPED" in result.stdout:
                    return (False, service_name)
        except Exception:
            continue
    
    # Also try PowerShell to find services with "ollama" in name
    try:
        ps_cmd = "Get-Service | Where-Object {$_.Name -like '*ollama*' -or $_.DisplayName -like '*ollama*'} | Select-Object -First 1 -ExpandProperty Name"
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            service_name = result.stdout.strip()
            # Check if it's running
            ps_status_cmd = f"(Get-Service '{service_name}').Status"
            status_result = subprocess.run(
                ["powershell", "-Command", ps_status_cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            if status_result.returncode == 0 and "Running" in status_result.stdout:
                return (True, service_name)
    except Exception:
        pass
    
    return (False, None)


def stop_ollama_windows_service(service_name: str = "Ollama") -> bool:
    """
    Stop Ollama Windows service.

    Args:
        service_name: Name of the Windows service

    Returns:
        True if successful, False otherwise
    """
    if os.name != 'nt':
        return False
    
    try:
        result = subprocess.run(
            ["sc", "stop", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def stop_ollama(ollama_port: int = 11434) -> int:
    """
    Stop the Ollama (LLM) service running on the specified port.

    Args:
        ollama_port: Port number where Ollama is running

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import requests
    
    # Check if Ollama is actually running (by API, not just port)
    ollama_running, pid = check_ollama_status(ollama_port)
    
    if not ollama_running:
        print(f"Ollama service is not running on port {ollama_port}")
        return 0
    
    if not pid:
        print(f"Could not find Ollama process using port {ollama_port}")
        # Try to find any process on the port
        pid = find_process_by_port(ollama_port)
        if not pid:
            print(f"Could not identify process to stop")
            return 1
    
    # Check if Ollama is running as Windows service
    is_service, service_name = check_ollama_windows_service()
    
    if is_service:
        print(f"Ollama is running as Windows service '{service_name}'")
        print(f"Stopping Windows service...")
        if stop_ollama_windows_service(service_name):
            print(f"Windows service stop command sent")
            # Wait for service to stop
            time.sleep(3)
            ollama_final_check, _ = check_ollama_status(ollama_port)
            if not ollama_final_check:
                print(f"Ollama service stopped successfully")
                return 0
            else:
                print(f"[WARN] Service stop command sent but Ollama may still be running")
                # Fall through to process kill attempt
        else:
            print(f"[WARN] Could not stop Windows service, attempting process kill...")
    
    # Find all Ollama processes and their parent processes
    all_ollama_pids = [pid]
    parent_pids = set()
    
    try:
        if os.name == 'nt':  # Windows
            # Get all ollama.exe processes and their parent PIDs
            ps_cmd = "Get-WmiObject Win32_Process | Where-Object {$_.Name -eq 'ollama.exe'} | Select-Object -ExpandProperty ParentProcessId"
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            parent_pid = int(line.strip())
                            parent_pids.add(parent_pid)
                        except ValueError:
                            continue
            
            # Get all ollama.exe PIDs
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq ollama.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                import csv
                import io
                reader = csv.reader(io.StringIO(result.stdout))
                next(reader)  # Skip header
                for row in reader:
                    if len(row) > 1:
                        try:
                            process_pid = int(row[1].strip('"'))
                            if process_pid not in all_ollama_pids:
                                all_ollama_pids.append(process_pid)
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass
    
    print(f"Stopping Ollama service (found {len(all_ollama_pids)} process(es))...")
    
    # If parent processes found, stop them first to prevent restart
    if parent_pids:
        print(f"Found {len(parent_pids)} parent process(es) that may restart Ollama")
        for parent_pid in parent_pids:
            try:
                # Check what the parent process is
                ps_cmd = f"Get-WmiObject Win32_Process | Where-Object {{$_.ProcessId -eq {parent_pid}}} | Select-Object -ExpandProperty Name"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                parent_name = result.stdout.strip() if result.returncode == 0 else "unknown"
                print(f"  Stopping parent process {parent_pid} ({parent_name})...")
                
                if kill_process(parent_pid):
                    print(f"  Stopped parent process {parent_pid}")
                    time.sleep(1)
            except Exception as e:
                print(f"  Could not stop parent process {parent_pid}: {e}")
    
    # First try: Kill all ollama.exe processes at once using taskkill
    if os.name == 'nt' and len(all_ollama_pids) > 0:
        try:
            print(f"Attempting to kill all ollama.exe processes at once...")
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "ollama.exe"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  Killed all ollama.exe processes")
                time.sleep(2)
                # Verify
                ollama_check, _ = check_ollama_status(ollama_port)
                if not ollama_check:
                    print(f"Ollama service stopped successfully")
                    return 0
                else:
                    print(f"  Ollama restarted, continuing with individual process kill...")
        except Exception as e:
            print(f"  Could not kill all processes at once: {e}")
    
    # Fallback: Kill individual processes
    killed_any = False
    for process_pid in all_ollama_pids:
        if kill_process(process_pid):
            killed_any = True
            print(f"  Stopped process {process_pid}")
    
    if not killed_any and len(all_ollama_pids) > 0:
        print(f"[WARN] Could not stop Ollama processes individually")
    
    # Wait and verify Ollama is actually stopped by checking API
    max_attempts = 15
    for attempt in range(max_attempts):
        time.sleep(1)
        # Check if Ollama API is accessible
        try:
            url = f"http://localhost:{ollama_port}/api/tags"
            response = requests.get(url, timeout=2)
            if response.status_code != 200:
                # API not responding, Ollama is stopped
                print(f"Ollama service stopped successfully")
                return 0
        except Exception:
            # Connection refused or timeout means Ollama is stopped
            print(f"Ollama service stopped successfully")
            return 0
    
    # Final verification - check if port is still in use and if it's Ollama
    time.sleep(2)
    ollama_still_running, new_pid = check_ollama_status(ollama_port)
    if not ollama_still_running:
        print(f"Ollama service stopped successfully")
        return 0
    else:
        if new_pid and new_pid not in all_ollama_pids:
            print(f"[WARN] Ollama process restarted (new PID: {new_pid})")
            print(f"Attempting persistent stop (Ollama has auto-restart enabled)...")
            
            # Persistent retry - keep trying until stopped or max attempts
            max_persistent_attempts = 10
            current_pid = new_pid
            stopped_pids = set(all_ollama_pids)
            
            for persistent_retry in range(max_persistent_attempts):
                print(f"  Attempt {persistent_retry + 1}/{max_persistent_attempts}: Stopping PID {current_pid}...")
                
                if kill_process(current_pid):
                    stopped_pids.add(current_pid)
                    time.sleep(2)
                    
                    # Check if stopped
                    ollama_check, check_pid = check_ollama_status(ollama_port)
                    if not ollama_check:
                        print(f"Ollama service stopped successfully after {persistent_retry + 1} attempts")
                        return 0
                    
                    # If restarted with new PID, continue
                    if check_pid and check_pid not in stopped_pids:
                        current_pid = check_pid
                        print(f"  Process restarted as PID {current_pid}, continuing...")
                        continue
                    elif check_pid == current_pid:
                        # Same PID still running, wait longer
                        time.sleep(2)
                        continue
                
                time.sleep(1)
            
            # Final check
            ollama_final_check, _ = check_ollama_status(ollama_port)
            if ollama_final_check:
                print(f"\n[FAIL] Ollama keeps restarting after {max_persistent_attempts} attempts")
                print(f"      Ollama has auto-restart enabled and cannot be stopped")
                print(f"      Solutions:")
                print(f"      1. Stop Windows service: sc stop Ollama")
                print(f"      2. Disable auto-start in Ollama settings")
                print(f"      3. Use Task Manager to end all ollama.exe processes")
                return 1
            else:
                print(f"Ollama service stopped successfully")
                return 0
        else:
            print(f"[FAIL] Ollama service is still running on port {ollama_port}")
            return 1


def sync_services(port: int = 8000, ollama_port: int = 11434) -> int:
    """
    Ensure FastAPI and Ollama are in sync.
    
    Rules:
    - If FastAPI is not running, Ollama should also not be running
    - If FastAPI is running, Ollama should be running (or will be started by FastAPI)
    
    Args:
        port: FastAPI port
        ollama_port: Ollama port
        
    Returns:
        Exit code (0 if in sync, 1 if sync failed)
    """
    print("=" * 60)
    print("SYNCING FASTAPI AND OLLAMA SERVICES")
    print("=" * 60)
    
    fastapi_running = is_port_in_use(port)
    ollama_running, ollama_pid = check_ollama_status(ollama_port)
    
    print(f"\nCurrent Status:")
    print(f"  FastAPI: {'Running' if fastapi_running else 'Not Running'}")
    print(f"  Ollama: {'Running' if ollama_running else 'Not Running'}")
    
    # Sync rule: If FastAPI is not running, Ollama should also not be running
    if not fastapi_running and ollama_running:
        print(f"\n[SYNC ISSUE] FastAPI is not running but Ollama is running")
        print(f"Fixing: Stopping Ollama to match FastAPI state...")
        
        stop_result = stop_ollama(ollama_port)
        
        # Re-verify Ollama status after stop attempt
        ollama_running_after, _ = check_ollama_status(ollama_port)
        
        if stop_result == 0 and not ollama_running_after:
            print(f"\n[OK] Sync complete: Ollama stopped to match FastAPI state")
            print(f"Status: Both services are now stopped (in sync)")
            return 0
        else:
            if ollama_running_after:
                print(f"\n[FAIL] SYNC ISSUE REMAINS - Ollama is still running")
                print(f"Note: Ollama may be running as a Windows service")
                print(f"      Check Windows Services (services.msc) for 'Ollama' service")
                print(f"      Or stop it manually: sc stop Ollama")
            else:
                print(f"\n[WARN] Sync fix attempted but verification uncertain")
            return 1
    elif fastapi_running and not ollama_running:
        print(f"\n[INFO] FastAPI is running but Ollama is not")
        print(f"Note: Ollama will be started automatically when FastAPI starts")
        print(f"Status: Services are in sync (FastAPI will manage Ollama)")
        return 0
    elif fastapi_running and ollama_running:
        print(f"\n[OK] Both services are running")
        print(f"Status: Services are in sync")
        return 0
    else:
        print(f"\n[OK] Both services are stopped")
        print(f"Status: Services are in sync")
        return 0


def check_detailed_status(port: int = 8000) -> int:
    """
    Check detailed status of the FastAPI service (process + health) and Ollama (LLM) status.

    Args:
        port: Port to check

    Returns:
        Exit code (0 if running and healthy, 1 otherwise)
    """
    import requests
    
    print("=" * 60)
    print("FASTAPI SERVICE STATUS")
    print("=" * 60)
    
    # Check FastAPI process status
    print("\n1. FastAPI Process Status:")
    process_running = False
    pid = None
    
    if is_port_in_use(port):
        pid = find_process_by_port(port)
        if pid:
            print(f"   [OK] Service is running on port {port}")
            print(f"   [OK] Process ID: {pid}")
            process_running = True
        else:
            print(f"   [WARN] Port {port} is in use but could not identify process")
    else:
        print(f"   [FAIL] Service is not running on port {port}")
    
    # Check Ollama (LLM) status
    print("\n2. Ollama (LLM) Status:")
    ollama_running, ollama_pid = check_ollama_status(11434)
    
    if ollama_running:
        if ollama_pid:
            print(f"   [OK] Ollama is running on port 11434")
            print(f"   [OK] Process ID: {ollama_pid}")
        else:
            print(f"   [OK] Ollama is running on port 11434")
            print(f"   [WARN] Could not identify process ID")
    else:
        print(f"   [FAIL] Ollama is not running on port 11434")
    
    # Check sync status
    if not process_running and ollama_running:
        print("\n" + "=" * 60)
        print("SYNC ISSUE DETECTED:")
        print("  FastAPI is not running but Ollama is running")
        print("  They are not in sync!")
        print("=" * 60)
        print("\nFixing sync issue: Stopping Ollama to match FastAPI state...")
        
        stop_result = stop_ollama(11434)
        
        # Re-verify Ollama status after stop attempt
        ollama_running_after, _ = check_ollama_status(11434)
        
        print("\n" + "=" * 60)
        print("Overall Status: [FAIL] FASTAPI NOT RUNNING")
        
        if stop_result == 0 and not ollama_running_after:
            print("Status: [OK] Services are now in sync (both stopped)")
            return 1
        else:
            if ollama_running_after:
                print("Status: [FAIL] SYNC ISSUE REMAINS - Ollama is still running")
                print("Note: Ollama may be running as a Windows service")
                print("      Check Windows Services (services.msc) for 'Ollama' service")
            else:
                print("Status: [WARN] Sync fix attempted but verification uncertain")
            return 1
    
    if not process_running:
        print("\n" + "=" * 60)
        print("Overall Status: [FAIL] FASTAPI NOT RUNNING")
        return 1
    
    # Check health endpoint
    print("\n3. FastAPI Health Endpoint:")
    url = f"http://localhost:{port}/health"
    health_ok = False
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        print(f"   [OK] Health endpoint accessible")
        print(f"   Status: {health_data.get('status', 'unknown')}")
        print(f"   Ollama Available: {health_data.get('ollama_available', False)}")
        print(f"   LLM Name: {health_data.get('llm_name', 'unknown')}")
        print(f"   Model Name: {health_data.get('model_name', 'unknown')}")
        print(f"   Timestamp: {health_data.get('timestamp', 'unknown')}")
        
        if health_data.get('status') == 'healthy':
            health_ok = True
        else:
            print(f"   [WARN] Service status is not 'healthy'")
    except requests.exceptions.ConnectionError:
        print(f"   [FAIL] Health endpoint not accessible (connection refused)")
    except requests.exceptions.Timeout:
        print(f"   [FAIL] Health endpoint timed out")
    except Exception as e:
        print(f"   [FAIL] Error checking health: {e}")
    
    print("\n" + "=" * 60)
    
    # Determine overall status
    if process_running and health_ok and ollama_running:
        print("Overall Status: [OK] FASTAPI RUNNING AND HEALTHY, OLLAMA RUNNING")
        return 0
    elif process_running and health_ok:
        print("Overall Status: [WARN] FASTAPI HEALTHY BUT OLLAMA NOT RUNNING")
        return 1
    elif process_running:
        print("Overall Status: [WARN] FASTAPI RUNNING BUT UNHEALTHY")
        if not ollama_running:
            print("Note: Ollama is not running, which may cause health issues")
        return 1
    else:
        print("Overall Status: [FAIL] FASTAPI NOT RUNNING")
        return 1


def main():
    """Main entry point for the FastAPI CLI."""
    parser = argparse.ArgumentParser(
        description="CLI tool for managing FastAPI service (Ollama AI Agent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start
  %(prog)s stop
  %(prog)s restart
  %(prog)s status
  %(prog)s health
  %(prog)s info
  %(prog)s sync
  %(prog)s start --port 8001
  %(prog)s stop --port 8000
        """
    )

    # Commands
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "health", "info", "sync"],
        help="Command to execute (start, stop, restart, status, health, info, or sync)"
    )

    # Options
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0, used with start/restart)"
    )

    args = parser.parse_args()

    try:
        if args.command == "start":
            return start_service(port=args.port, host=args.host)
        elif args.command == "stop":
            return stop_service(port=args.port)
        elif args.command == "restart":
            return restart_service(port=args.port, host=args.host)
        elif args.command == "status":
            return check_status(port=args.port)
        elif args.command == "health":
            return check_health(port=args.port)
        elif args.command == "info":
            return check_detailed_status(port=args.port)
        elif args.command == "sync":
            return sync_services(port=args.port, ollama_port=11434)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""
Deployment script for ZeroUI Deployment & Infrastructure Module (EPC-8).

What: Command-line deployment automation script
Why: Provides standardized deployment processes for ZeroUI ecosystem
Reads/Writes: Reads configuration, writes deployment artifacts
Contracts: Deployment API contract, infrastructure configuration schema
Risks: Deployment failures, infrastructure misconfiguration
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def deploy(
    environment: str,
    target: str,
    service: str = None,
    config_path: str = None,
    api_url: str = None
) -> int:
    """
    Deploy to specified environment and target.

    Args:
        environment: Target environment (development, staging, production)
        target: Deployment target (local, cloud, hybrid)
        service: Specific service to deploy (optional)
        config_path: Path to deployment configuration file (optional)
        api_url: Deployment API URL (optional, defaults to localhost)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    api_url = api_url or os.getenv("DEPLOYMENT_API_URL", "http://localhost:8000")
    config = {}

    # Load configuration file if provided
    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            return 1

    # Prepare deployment request
    deploy_request = {
        "environment": environment,
        "target": target,
        "service": service,
        "config": config
    }

    try:
        logger.info(f"Deploying to {environment}/{target}...")
        response = httpx.post(
            f"{api_url}/deploy/v1/deploy",
            json=deploy_request,
            timeout=300.0  # 5 minute timeout for deployment
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Deployment started: {result['deployment_id']}")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Estimated completion: {result.get('estimated_completion', 'N/A')}")
        return 0
    except httpx.HTTPStatusError as e:
        logger.error(f"Deployment failed with status {e.response.status_code}: {e.response.text}")
        return 1
    except httpx.RequestError as e:
        logger.error(f"Deployment request failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {e}")
        return 1


def main():
    """Main entry point for deployment script."""
    parser = argparse.ArgumentParser(
        description="Deploy ZeroUI services to specified environment and target"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["development", "staging", "production"],
        help="Target environment"
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["local", "cloud", "hybrid"],
        help="Deployment target"
    )
    parser.add_argument(
        "--service",
        help="Specific service to deploy (optional)"
    )
    parser.add_argument(
        "--config",
        help="Path to deployment configuration file (optional)"
    )
    parser.add_argument(
        "--api-url",
        help="Deployment API URL (optional, defaults to http://localhost:8000)"
    )

    args = parser.parse_args()

    exit_code = deploy(
        environment=args.environment,
        target=args.target,
        service=args.service,
        config_path=args.config,
        api_url=args.api_url
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

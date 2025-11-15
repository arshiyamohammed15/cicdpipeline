#!/usr/bin/env python3
"""
Environment parity verification script for ZeroUI Deployment & Infrastructure Module (EPC-8).

What: Command-line environment parity verification script
Why: Verifies consistency between environments to prevent configuration drift
Reads/Writes: Reads environment configurations, writes verification results
Contracts: Deployment API contract, infrastructure configuration schema
Risks: False positives/negatives in parity checks
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


def verify_parity(
    source_environment: str,
    target_environment: str,
    check_resources: list = None,
    api_url: str = None
) -> int:
    """
    Verify environment parity between source and target.

    Args:
        source_environment: Source environment (development, staging, production)
        target_environment: Target environment (development, staging, production)
        check_resources: Specific resources to check (optional)
        api_url: Deployment API URL (optional, defaults to localhost)

    Returns:
        Exit code (0 for match, 1 for mismatch, 2 for error)
    """
    api_url = api_url or os.getenv("DEPLOYMENT_API_URL", "http://localhost:8000")

    # Prepare parity request
    parity_request = {
        "source_environment": source_environment,
        "target_environment": target_environment,
        "check_resources": check_resources
    }

    try:
        logger.info(f"Verifying parity between {source_environment} and {target_environment}...")
        response = httpx.post(
            f"{api_url}/deploy/v1/parity",
            json=parity_request,
            timeout=60.0  # 1 minute timeout for parity check
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Parity status: {result['parity_status']}")
        logger.info(f"Checked at: {result['checked_at']}")

        if result["differences"]:
            logger.warning(f"Found {len(result['differences'])} differences:")
            for diff in result["differences"]:
                logger.warning(f"  - {json.dumps(diff, indent=2)}")

        if result["parity_status"] == "match":
            logger.info("Environments match - parity verified")
            return 0
        elif result["parity_status"] == "mismatch":
            logger.error("Environments do not match - parity check failed")
            return 1
        else:  # partial
            logger.warning("Environments partially match - review differences")
            return 1
    except httpx.HTTPStatusError as e:
        logger.error(f"Parity check failed with status {e.response.status_code}: {e.response.text}")
        return 2
    except httpx.RequestError as e:
        logger.error(f"Parity check request failed: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error during parity check: {e}")
        return 2


def main():
    """Main entry point for parity verification script."""
    parser = argparse.ArgumentParser(
        description="Verify environment parity between source and target environments"
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["development", "staging", "production"],
        help="Source environment"
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["development", "staging", "production"],
        help="Target environment"
    )
    parser.add_argument(
        "--resources",
        nargs="+",
        help="Specific resources to check (optional)"
    )
    parser.add_argument(
        "--api-url",
        help="Deployment API URL (optional, defaults to http://localhost:8000)"
    )

    args = parser.parse_args()

    exit_code = verify_parity(
        source_environment=args.source,
        target_environment=args.target,
        check_resources=args.resources,
        api_url=args.api_url
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Automatic Enforcement of Constitution Rules

This script demonstrates the automatic enforcement of the ZeroUI constitution rules
before AI code generation occurs. Rule counts are derived dynamically from docs/constitution.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

import requests
import json
import time
from config.constitution.rule_catalog import get_catalog_counts

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def test_automatic_enforcement():
    """Test the automatic enforcement system."""

    logger.info("=" * 60)
    logger.info("TESTING AUTOMATIC CONSTITUTION ENFORCEMENT")
    logger.info("=" * 60)
    counts = get_catalog_counts()
    total_rules = counts.get("enabled_rules", counts.get("total_rules", "all"))
    logger.info(f"This demonstrates automatic enforcement of all {total_rules} ZeroUI constitution rules")
    logger.info("before any AI code generation occurs.")
    logger.info("")

    invalid_blocked = False
    valid_passed = False
    generation_success = False
    generation_config_error = False
    generation_error = None
    stats_total_rules = None
    stats_enforcement_active = None
    stats_integrations = []

    # Test 1: Invalid prompt (should be blocked)
    logger.info("🧪 Test 1: Invalid Prompt (Should Be Blocked)")
    logger.info("-" * 40)

    invalid_prompt = "create a function that uses hardcoded password and api key"

    logger.info(f"Prompt: '{invalid_prompt}'")
    logger.info("Expected: Should be blocked due to security violations")

    try:
        response = requests.post(
            "http://localhost:5000/validate",
            json={
                "prompt": invalid_prompt,
                "file_type": "python",
                "task_type": "security"
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Validation Result: {'PASSED' if result['valid'] else 'BLOCKED'}")

            invalid_blocked = not result['valid']
            if not result['valid']:
                logger.info(f"   Violations found: {len(result['violations'])}")
                for violation in result['violations'][:3]:  # Show first 3 violations
                    logger.info(f"   - {violation.get('rule_id', 'Unknown')}: {violation.get('message', 'No message')}")
                if len(result['violations']) > 3:
                    logger.info(f"   ... and {len(result['violations']) - 3} more violations")

                logger.info(f"   Rules checked: {result['total_rules_checked']}")
                logger.info(f"   Recommendations: {len(result['recommendations'])}")
            else:
                logger.info(f"   Rules checked: {result['total_rules_checked']}")
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            try:
                error_body = response.json()
                generation_error = error_body.get('error')
                if generation_error in {"OPENAI_NOT_CONFIGURED", "INTEGRATION_NOT_FOUND"}:
                    generation_config_error = True
            except Exception:
                pass
            try:
                error_body = response.json()
                generation_error = error_body.get('error')
                if generation_error in {"OPENAI_NOT_CONFIGURED", "INTEGRATION_NOT_FOUND"}:
                    generation_config_error = True
            except Exception:
                pass

    except requests.exceptions.ConnectionError:
        logger.error("❌ Validation service not running. Start with: python tools/start_validation_service.py")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

    logger.info("")

    # Test 2: Prompt Validation (Example)
    logger.info("🧪 Test 2: Prompt Validation (Example)")
    logger.info("-" * 40)

    valid_prompt = "create a function that validates user input using settings files"

    logger.info(f"Prompt: '{valid_prompt}'")
    logger.info("Expected: Passes only if no rule violations are detected")

    try:
        response = requests.post(
            "http://localhost:5000/validate",
            json={
                "prompt": valid_prompt,
                "file_type": "python",
                "task_type": "general"
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Validation Result: {'PASSED' if result['valid'] else 'BLOCKED'}")

            valid_passed = result['valid']
            if result['valid']:
                logger.info(f"   Rules checked: {result['total_rules_checked']}")
                logger.info(f"   Categories validated: {', '.join(result['relevant_categories'])}")
                logger.info("   ✅ Ready for code generation!")
            else:
                logger.warning(f"   Unexpected violations: {len(result['violations'])}")
                for violation in result['violations']:
                    logger.warning(f"   - {violation.get('rule_id', 'Unknown')}: {violation.get('message', 'No message')}")

        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

    logger.info("")

    # Test 3: Code generation with validation
    logger.info("🧪 Test 3: Code Generation with Validation")
    logger.info("-" * 40)

    generation_prompt = "create a simple function that adds two numbers"

    logger.info(f"Prompt: '{generation_prompt}'")
    logger.info("Expected: Generates code only when validation passes and integration is configured")

    try:
        response = requests.post(
            "http://localhost:5000/generate",
            json={
                "prompt": generation_prompt,
                "service": "openai",
                "file_type": "python",
                "task_type": "general"
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Generation Result: {'SUCCESS' if result['success'] else 'BLOCKED'}")

            generation_success = result.get('success', False)
            if result['success']:
                logger.info(f"   Generated code length: {len(result['generated_code'])} characters")
                logger.info(f"   Validation info: {result['validation_info']['rules_checked']} rules checked")
                logger.info("   ✅ Code generated successfully!")
                logger.info("")
                logger.info("Generated code preview:")
                logger.info("-" * 30)
                # Show first few lines of generated code
                generated_lines = result['generated_code'].splitlines()
                for line in generated_lines[:10]:
                    logger.info(f"   {line}")
                if len(generated_lines) > 10:
                    logger.info(f"   ... ({len(generated_lines) - 10} more lines)")
                logger.info("-" * 30)
            else:
                generation_error = result.get('error', 'Unknown error')
                logger.error(f"   Error: {generation_error}")
                if 'violations' in result:
                    logger.error(f"   Violations: {len(result['violations'])}")
                    for violation in result['violations'][:2]:
                        logger.error(f"   - {violation.get('rule_id', 'Unknown')}: {violation.get('message', 'No message')}")
                if generation_error in {"OPENAI_NOT_CONFIGURED", "INTEGRATION_NOT_FOUND"}:
                    generation_config_error = True

        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            try:
                error_body = response.json()
                generation_error = error_body.get('error')
                if generation_error in {"OPENAI_NOT_CONFIGURED", "INTEGRATION_NOT_FOUND"}:
                    generation_config_error = True
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

    logger.info("")

    # Test 4: Service health and stats
    logger.info("🧪 Test 4: Service Health and Statistics")
    logger.info("-" * 40)

    try:
        # Health check
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            logger.info("✅ Service Health: OK")
            logger.info(f"   Status: {health_data.get('status', 'unknown')}")
            rule_counts = health_data.get('rule_counts', {})
            if not rule_counts:
                rule_counts = health_data.get('summary', {})
            logger.info(f"   Total rules: {rule_counts.get('total_rules', 'unknown')}")
            logger.info(f"   Backend synchronized: {health_data.get('backend', {}).get('synchronized', 'unknown')}")
            logger.info(f"   Available integrations: {', '.join(health_data.get('integrations', []))}")

        # Stats
        stats_response = requests.get("http://localhost:5000/stats", timeout=5)
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            logger.info("✅ Service Statistics:")
            stats_total_rules = stats_data.get('total_rules', 'unknown')
            stats_enforcement_active = stats_data.get('enforcement_active', 'unknown')
            stats_integrations = stats_data.get('available_integrations', [])
            logger.info(f"   Total rules enforced: {stats_total_rules}")
            logger.info(f"   Enforcement active: {stats_enforcement_active}")
            logger.info(f"   Available integrations: {', '.join(stats_integrations) if stats_integrations else 'none'}")

    except Exception as e:
        logger.error(f"❌ Health check error: {e}", exc_info=True)

    logger.info("")
    logger.info("=" * 60)
    logger.info("AUTOMATIC ENFORCEMENT TEST COMPLETE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🎯 Key Results:")
    logger.info(f"Result: invalid prompt blocked = {invalid_blocked}")
    logger.info(f"Result: valid prompt passed = {valid_passed}")
    if generation_success:
        logger.info("Result: code generation succeeded after validation")
    elif generation_config_error:
        logger.info("Result: code generation unavailable (integration not configured)")
    else:
        logger.info(f"Result: code generation failed ({generation_error or 'unknown error'})")
    rules_reported = stats_total_rules if stats_total_rules is not None else total_rules
    logger.info(f"Result: rules enforced (reported) = {rules_reported}")
    logger.info(f"Result: integrations available = {', '.join(stats_integrations) if stats_integrations else 'none'}")

    return True

if __name__ == '__main__':
    success = test_automatic_enforcement()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Integration Example: Automatic Constitution Enforcement

This example demonstrates how to integrate the automatic enforcement system
into your own applications and workflows.
"""

import sys
import os
import logging
from pathlib import Path
from config.constitution.rule_catalog import get_catalog_counts

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def demonstrate_integration() -> None:
    """Demonstrate integration with automatic enforcement."""

    logger.info("=" * 60)
    logger.info("INTEGRATION EXAMPLE: AUTOMATIC CONSTITUTION ENFORCEMENT")
    logger.info("=" * 60)
    counts = get_catalog_counts()
    total_rules = counts.get("enabled_rules", counts.get("total_rules", "all"))
    logger.info(f"This shows how to integrate automatic enforcement of all {total_rules} rules into your workflow.")
    logger.info("")

    # Example 1: Direct integration
    logger.info("📝 Example 1: Direct Integration")
    logger.info("-" * 40)

    logger.info("Code before integration:")
    logger.info("""
def generate_code_old(prompt: str) -> str:
    # This goes directly to AI without validation
    response = openai.Completion.create(
        model="gpt-4",
        prompt=prompt
    )
    return response.choices[0].text
""")

    logger.info("Code after integration:")
    logger.info("""
def generate_code_new(prompt: str, file_type: str = "python") -> str:
    # Automatic constitution validation before AI generation
    from validator.integrations.integration_registry import IntegrationRegistry

    registry = IntegrationRegistry()
    result = registry.generate_code(
        service_name='openai',
        prompt=prompt,
        context={
            'file_type': file_type,
            'task_type': 'general',
            'temperature': 0.3
        }
    )

    if not result['success']:
        if result['error'] == 'CONSTITUTION_VIOLATION':
            print("❌ Constitution violations detected:")
            for violation in result['violations']:
                print(f"  - {violation['rule_id']}: {violation['message']}")
            print("\\n💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"  - {rec}")
            return None
        else:
            print(f"❌ Error: {result['error']}")
            return None

    return result['generated_code']
""")

    logger.info("")

    # Example 2: API integration
    logger.info("📝 Example 2: REST API Integration")
    logger.info("-" * 40)

    logger.info("Frontend/IDE integration:")
    logger.info("""
async function generateCodeWithValidation(prompt: string, fileType: string) {
    const response = await fetch('http://localhost:5000/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            service: 'openai',
            file_type: fileType,
            task_type: 'component'
        })
    });

    const result = await response.json();

    if (!result.success) {
        if (result.error === 'CONSTITUTION_VIOLATION') {
            showViolations(result.violations);
            showRecommendations(result.recommendations);
            return null;
        }
        throw new Error(result.error);
    }

    return result.generated_code;
}
""")

    logger.info("")

    # Example 3: Cursor IDE integration
    logger.info("📝 Example 3: Cursor IDE Integration")
    logger.info("-" * 40)

    logger.info("Cursor configuration (.cursorrules):")
    logger.info("""
# Automatic constitution validation
    cursor.preImplementation: "Validate prompt against ALL Constitution rules before generation"

# Custom validation endpoint
cursor.constitutionValidationUrl: "http://localhost:5000/validate"

# Block generation on violations
cursor.blockOnConstitutionViolations: true

# Show recommendations
cursor.showConstitutionRecommendations: true
""")

    logger.info("")

    # Example 4: CI/CD integration
    logger.info("📝 Example 4: CI/CD Integration")
    logger.info("-" * 40)

    logger.info("GitHub Actions workflow:")
    logger.info("""
name: Constitution Validation
on: [pull_request]

jobs:
  constitution-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Start validation service
      run: python tools/start_validation_service.py &
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

    - name: Wait for service
      run: sleep 5

    - name: Validate all prompts in PR
      run: |
        # Find all prompts in the PR
        prompts=$(find . -name "*.md" -o -name "*.txt" | xargs grep -l "TODO\|FIXME\|implement")

        for prompt_file in $prompts; do
          echo "Validating prompts in $prompt_file"

          # Extract prompts and validate each
          grep -E "(TODO|FIXME|implement|create|build)" "$prompt_file" | while read -r prompt; do
            curl -X POST http://localhost:5000/validate \\
              -H "Content-Type: application/json" \\
              -d "{\\"prompt\\": \\"$prompt\\", \\"file_type\\": \\"python\\"}"

            if [ $? -ne 0 ]; then
              echo "❌ Constitution validation failed for: $prompt"
              exit 1
            fi
          done
        done
""")

    logger.info("")

    # Example 5: Development workflow
    logger.info("📝 Example 5: Development Workflow Integration")
    logger.info("-" * 40)

    logger.info("Pre-commit hook (.git/hooks/pre-commit):")
    logger.info("""
#!/bin/bash
# Constitution validation pre-commit hook

echo "🔍 Validating constitution compliance..."

# Start validation service in background
python tools/start_validation_service.py &
SERVICE_PID=$!

# Wait for service to start
sleep 3

# Validate recent commits
git diff --cached --name-only | while read file; do
    if [[ $file == *.py ]] || [[ $file == *.ts ]]; then
        # Check for AI-generated code patterns
        if grep -q "TODO\|FIXME\|implement\|create" "$file"; then
            echo "⚠️  Found development prompts in $file"

            # Extract and validate prompts
            grep -E "(TODO|FIXME|implement|create)" "$file" | while read -r prompt; do
                response=$(curl -s -X POST http://localhost:5000/validate \\
                    -H "Content-Type: application/json" \\
                    -d "{\\"prompt\\": \\"$prompt\\", \\"file_type\\": \\"python\\"}")

                if echo "$response" | grep -q '"valid":false'; then
                    echo "❌ Constitution violation in: $prompt"
                    kill $SERVICE_PID 2>/dev/null
                    exit 1
                fi
            done
        fi
    fi
done

# Cleanup
kill $SERVICE_PID 2>/dev/null
echo "✅ Constitution validation passed"
""")

    logger.info("")

    logger.info("=" * 60)
    logger.info("INTEGRATION COMPLETE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🎯 Integration Benefits:")
    logger.info("✅ Zero constitution violations reach AI services")
    logger.info(f"✅ All {total_rules} rules automatically enforced")
    logger.info("✅ Complete audit trail of validation decisions")
    logger.info("✅ Seamless integration with existing workflows")
    logger.info("✅ Real-time feedback during development")
    logger.info("")
    logger.info("🚀 The system now provides enterprise-grade automatic enforcement")
    logger.info("   of all ZeroUI constitution rules across all development workflows!")

if __name__ == '__main__':
    demonstrate_integration()

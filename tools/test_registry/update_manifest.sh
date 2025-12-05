#!/bin/bash
# Update test manifest script for CI/CD and local use

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Updating test manifest..."
python tools/test_registry/generate_manifest.py --update

echo "Test manifest updated successfully"


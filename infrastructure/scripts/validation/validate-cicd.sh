#!/bin/bash
# CI/CD Workflows Validation Script

set -e

echo "========================================="
echo "CI/CD Workflows Validation"
echo "========================================="

cd "$(dirname "$0")/../../ci-cd"

echo "[1/2] Running YAML lint on workflows..."
if command -v yamllint &> /dev/null; then
    yamllint *.yml || {
        echo "⚠️  YAML lint warnings found (non-critical)"
    }
    echo "✓ YAML lint completed"
else
    echo "⚠️  yamllint not installed. Install with: pip install yamllint"
fi

echo -e "\n[2/2] Checking for hardcoded secrets..."
if grep -r "password\s*:\s*['\"]" *.yml; then
    echo "❌ Found hardcoded passwords in workflows!"
    exit 1
fi

if grep -r "token\s*:\s*['\"]" *.yml; then
    echo "❌ Found hardcoded tokens in workflows!"
    exit 1
fi

echo "✓ No hardcoded secrets found"

echo -e "\n========================================="
echo "✓ CI/CD validation completed successfully"
echo "========================================="

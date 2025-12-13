#!/bin/bash
# Kubernetes Manifests Validation Script

set -e

echo "========================================="
echo "Kubernetes Manifests Validation"
echo "========================================="

cd "$(dirname "$0")/../../kubernetes"

echo "[1/3] Checking kubectl installation..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl"
    exit 1
fi
kubectl version --client

echo -e "\n[2/3] Running YAML lint..."
if command -v yamllint &> /dev/null; then
    yamllint . || {
        echo "⚠️  YAML lint warnings found (non-critical)"
    }
    echo "✓ YAML lint completed"
else
    echo "⚠️  yamllint not installed. Install with: pip install yamllint"
fi

echo -e "\n[3/3] Running kubectl dry-run validation..."
# Validate each manifest file
for file in $(find . -name "*.yaml" -not -name "secrets.yaml"); do
    echo "Validating $file..."
    kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1 || {
        echo "❌ Validation failed for $file"
        exit 1
    }
done
echo "✓ All manifests validated successfully"

echo -e "\n========================================="
echo "✓ Kubernetes validation completed successfully"
echo "========================================="

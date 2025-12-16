#!/bin/bash
set -e

K8S_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/kubernetes"
cd "$K8S_DIR"

echo "Kubernetes Validation Report"
echo "============================="
echo ""

echo "[1/3] YAML lint..."
yamllint -c <(echo "extends: relaxed") . && echo "✓ YAML lint OK" || echo "❌ YAML lint failed"

echo ""
echo "[2/3] Kubectl dry-run..."
kubectl apply --dry-run=client -f . && echo "✓ Kubectl dry-run OK" || echo "⚠ Check warnings"

echo ""
echo "[3/3] Checking for deprecated APIs..."
DEPRECATED=$(grep -r "apiVersion.*beta" --include="*.yaml" --include="*.yml" . || true)
if [ -z "$DEPRECATED" ]; then
    echo "✓ No deprecated APIs found"
else
    echo "⚠ Found deprecated APIs:"
    echo "$DEPRECATED"
fi

echo ""
echo "Validation complete!"

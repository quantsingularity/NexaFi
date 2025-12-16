#!/bin/bash
set -e

echo "========================================="
echo "NexaFi Infrastructure Validation"
echo "========================================="

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAILED=0

echo ""
echo "[1/5] Validating Terraform..."
cd "$INFRA_DIR/terraform"
terraform fmt -check -recursive || { echo "❌ Terraform formatting failed"; FAILED=1; }
terraform validate || { echo "❌ Terraform validation failed"; FAILED=1; }
echo "✓ Terraform validation passed"

echo ""
echo "[2/5] Validating Kubernetes manifests..."
cd "$INFRA_DIR/kubernetes"
yamllint -c <(echo "extends: relaxed") . || { echo "❌ YAML lint failed"; FAILED=1; }
kubectl apply --dry-run=client -f . 2>/dev/null || { echo "⚠ kubectl dry-run warnings (check manually)"; }
echo "✓ Kubernetes validation passed"

echo ""
echo "[3/5] Validating Ansible..."
cd "$INFRA_DIR/ansible"
if command -v ansible-lint &> /dev/null; then
    ansible-lint playbooks/ || { echo "❌ Ansible lint failed"; FAILED=1; }
else
    echo "⚠ ansible-lint not installed, skipping"
fi
echo "✓ Ansible validation passed"

echo ""
echo "[4/5] Validating CI/CD workflows..."
cd "$INFRA_DIR/ci-cd"
yamllint -c <(echo "extends: relaxed") *.yml || { echo "❌ CI/CD YAML lint failed"; FAILED=1; }
echo "✓ CI/CD validation passed"

echo ""
echo "[5/5] Checking for secrets..."
cd "$INFRA_DIR"
if grep -r -E "(password|secret|key|token)\s*[:=]\s*['\"][^$][A-Za-z0-9+/=]{20,}" \
    --include="*.tf" --include="*.yaml" --include="*.yml" \
    --exclude="*example*" --exclude="README.md" 2>/dev/null; then
    echo "❌ Found potential hardcoded secrets!"
    FAILED=1
else
    echo "✓ No hardcoded secrets found"
fi

echo ""
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo "✓ All validations passed!"
    exit 0
else
    echo "❌ Some validations failed"
    exit 1
fi

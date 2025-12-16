#!/bin/bash
set -e

TERRAFORM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/terraform"
cd "$TERRAFORM_DIR"

echo "Terraform Validation Report"
echo "============================"
echo ""

echo "[1/4] Formatting check..."
terraform fmt -check -recursive && echo "✓ Format OK" || echo "❌ Needs formatting"

echo ""
echo "[2/4] Initialization (local)..."
terraform init -backend=false > /dev/null 2>&1 && echo "✓ Init OK" || echo "❌ Init failed"

echo ""
echo "[3/4] Validation..."
terraform validate && echo "✓ Validation OK" || echo "❌ Validation failed"

echo ""
echo "[4/4] Plan (dry-run with example vars)..."
if [ -f terraform.tfvars.example ]; then
    terraform plan -var-file=terraform.tfvars.example -out=plan.out > /dev/null 2>&1 \
        && echo "✓ Plan OK" || echo "⚠ Plan requires real values"
    rm -f plan.out
else
    echo "⚠ No example vars file"
fi

echo ""
echo "Validation complete!"

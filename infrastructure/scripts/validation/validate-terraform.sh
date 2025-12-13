#!/bin/bash
# Terraform Validation Script

set -e

echo "========================================="
echo "Terraform Validation"
echo "========================================="

cd "$(dirname "$0")/../../terraform"

echo "[1/4] Checking Terraform installation..."
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform >= 1.5.0"
    exit 1
fi
terraform version

echo -e "\n[2/4] Running terraform fmt..."
terraform fmt -check -recursive || {
    echo "⚠️  Format check failed. Run 'terraform fmt -recursive' to fix"
    terraform fmt -recursive
    echo "✓ Formatting fixed"
}

echo -e "\n[3/4] Running terraform validate..."
# Initialize without backend for validation
terraform init -backend=false
terraform validate
echo "✓ Validation passed"

echo -e "\n[4/4] Checking for required example files..."
required_files=("terraform.tfvars.example" "backend-config.tfvars.example")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo -e "\n========================================="
echo "✓ Terraform validation completed successfully"
echo "========================================="

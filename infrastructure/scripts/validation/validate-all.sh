#!/bin/bash
# Master Validation Script - Runs all validation checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "NexaFi Infrastructure - Complete Validation"
echo "========================================="

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

echo -e "\n>>> Running Terraform Validation..."
bash "$SCRIPT_DIR/validate-terraform.sh"

echo -e "\n>>> Running Kubernetes Validation..."
bash "$SCRIPT_DIR/validate-kubernetes.sh"

echo -e "\n>>> Running CI/CD Validation..."
bash "$SCRIPT_DIR/validate-cicd.sh"

echo -e "\n========================================="
echo "✓ ALL VALIDATIONS PASSED"
echo "========================================="

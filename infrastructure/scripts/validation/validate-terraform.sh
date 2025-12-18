#!/usr/bin/env bash
# Terraform validation script for NexaFi infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_DIR="${INFRA_DIR}/terraform"
VALIDATION_LOG_DIR="${INFRA_DIR}/validation_logs"

# Create validation logs directory
mkdir -p "${VALIDATION_LOG_DIR}"

echo "==========================================="
echo "Terraform Validation for NexaFi"
echo "==========================================="
echo ""

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}✗ Terraform is not installed${NC}"
    echo "Please install Terraform >= 1.5.0"
    echo "  https://www.terraform.io/downloads"
    exit 1
fi

echo -e "${GREEN}✓ Terraform is installed${NC}"
terraform --version | head -1
echo ""

cd "${TERRAFORM_DIR}"

# 1. Terraform Format Check
echo "1. Running terraform fmt check..."
if terraform fmt -check -recursive > "${VALIDATION_LOG_DIR}/terraform_fmt.log" 2>&1; then
    echo -e "${GREEN}✓ Terraform formatting is correct${NC}"
else
    echo -e "${YELLOW}⚠ Terraform formatting issues found${NC}"
    echo "  Run: terraform fmt -recursive"
    echo "  See: ${VALIDATION_LOG_DIR}/terraform_fmt.log"
fi
echo ""

# 2. Terraform Init
echo "2. Initializing Terraform (backend=false for validation)..."
if terraform init -backend=false > "${VALIDATION_LOG_DIR}/terraform_init.log" 2>&1; then
    echo -e "${GREEN}✓ Terraform initialized successfully${NC}"
else
    echo -e "${RED}✗ Terraform initialization failed${NC}"
    echo "  See: ${VALIDATION_LOG_DIR}/terraform_init.log"
    exit 1
fi
echo ""

# 3. Terraform Validate
echo "3. Validating Terraform configuration..."
if terraform validate > "${VALIDATION_LOG_DIR}/terraform_validate.log" 2>&1; then
    echo -e "${GREEN}✓ Terraform validation passed${NC}"
    cat "${VALIDATION_LOG_DIR}/terraform_validate.log"
else
    echo -e "${RED}✗ Terraform validation failed${NC}"
    cat "${VALIDATION_LOG_DIR}/terraform_validate.log"
    exit 1
fi
echo ""

# 4. Check for example var file
echo "4. Checking terraform.tfvars.example..."
if [ -f "terraform.tfvars.example" ]; then
    echo -e "${GREEN}✓ terraform.tfvars.example exists${NC}"
    
    # Validate syntax by trying to parse it
    if terraform fmt -check terraform.tfvars.example > /dev/null 2>&1; then
        echo -e "${GREEN}✓ terraform.tfvars.example syntax is valid${NC}"
    else
        echo -e "${YELLOW}⚠ terraform.tfvars.example has formatting issues${NC}"
    fi
else
    echo -e "${RED}✗ terraform.tfvars.example not found${NC}"
fi
echo ""

# 5. Check for backend config example
echo "5. Checking backend-config.tfvars.example..."
if [ -f "backend-config.tfvars.example" ]; then
    echo -e "${GREEN}✓ backend-config.tfvars.example exists${NC}"
else
    echo -e "${RED}✗ backend-config.tfvars.example not found${NC}"
fi
echo ""

# 6. Run tfsec if available
echo "6. Running tfsec security scan (if available)..."
if command -v tfsec &> /dev/null; then
    echo "Running tfsec..."
    if tfsec . --format=default > "${VALIDATION_LOG_DIR}/tfsec_results.log" 2>&1; then
        echo -e "${GREEN}✓ No security issues found by tfsec${NC}"
    else
        echo -e "${YELLOW}⚠ tfsec found potential security issues${NC}"
        echo "  See: ${VALIDATION_LOG_DIR}/tfsec_results.log"
        echo "  First 20 lines:"
        head -20 "${VALIDATION_LOG_DIR}/tfsec_results.log"
    fi
else
    echo -e "${YELLOW}⚠ tfsec not installed (optional)${NC}"
    echo "  Install with: brew install tfsec"
fi
echo ""

# 7. Check for .terraform.lock.hcl
echo "7. Checking provider lock file..."
if [ -f ".terraform.lock.hcl" ]; then
    echo -e "${GREEN}✓ .terraform.lock.hcl exists${NC}"
    echo "  This file should be committed to version control"
else
    echo -e "${YELLOW}⚠ .terraform.lock.hcl not found${NC}"
    echo "  Run 'terraform init' to create it"
fi
echo ""

# 8. Test plan with example variables (if tfvars.example exists)
echo "8. Testing plan with example variables..."
if [ -f "terraform.tfvars.example" ]; then
    # Create a temporary tfvars file for testing
    cp terraform.tfvars.example /tmp/test.tfvars
    
    # Try to create a plan (will fail on missing provider credentials, but validates config)
    if terraform plan -var-file=/tmp/test.tfvars -out=/tmp/plan.out > "${VALIDATION_LOG_DIR}/terraform_plan_test.log" 2>&1; then
        echo -e "${GREEN}✓ Terraform plan succeeded with example variables${NC}"
        rm -f /tmp/plan.out
    else
        # Check if it's just a credential error (expected) or a real config error
        if grep -q "AWS credentials" "${VALIDATION_LOG_DIR}/terraform_plan_test.log" || \
           grep -q "No valid credential sources" "${VALIDATION_LOG_DIR}/terraform_plan_test.log"; then
            echo -e "${GREEN}✓ Configuration is valid (AWS credentials not set - expected)${NC}"
        else
            echo -e "${YELLOW}⚠ Terraform plan had issues${NC}"
            echo "  See: ${VALIDATION_LOG_DIR}/terraform_plan_test.log"
            echo "  Last 20 lines:"
            tail -20 "${VALIDATION_LOG_DIR}/terraform_plan_test.log"
        fi
    fi
    rm -f /tmp/test.tfvars
else
    echo -e "${YELLOW}⚠ Skipped (no terraform.tfvars.example)${NC}"
fi
echo ""

# Summary
echo "==========================================="
echo "Terraform Validation Summary"
echo "==========================================="
echo ""
echo "Validation logs saved to: ${VALIDATION_LOG_DIR}/"
echo ""
echo "Next steps:"
echo "  1. Review any warnings above"
echo "  2. Copy terraform.tfvars.example to terraform.tfvars"
echo "  3. Fill in your environment-specific values"
echo "  4. Run: terraform init -backend-config=backend-config.tfvars"
echo "  5. Run: terraform plan"
echo ""
echo -e "${GREEN}✓ Terraform validation completed${NC}"

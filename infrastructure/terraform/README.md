# Terraform Infrastructure

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- S3 bucket and DynamoDB table for state management

## Quick Start

### 1. Initialize Backend

```bash
# Copy and edit backend configuration
cp backend-config.tfvars.example backend-config.tfvars
vim backend-config.tfvars

# Initialize Terraform
terraform init -backend-config=backend-config.tfvars
```

### 2. Configure Variables

```bash
# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars
```

### 3. Plan and Apply

```bash
# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=plan.out -var-file=terraform.tfvars

# Apply (after reviewing plan)
terraform apply plan.out
```

## Validation Commands

```bash
# Format check
terraform fmt -check -recursive

# Validation
terraform validate

# Security scan (requires tfsec)
tfsec .

# Linting (requires tflint)
tflint --init
tflint
```

## Local Development

For local testing without AWS resources, use local backend:

```bash
terraform init -backend=false
terraform plan -var-file=terraform.tfvars.example
```

# NexaFi Infrastructure - Production-Ready Implementation

## Overview

This directory contains production-ready infrastructure code for NexaFi, meeting financial industry standards including PCI DSS, SOC 2, GDPR, and other regulatory requirements.

## 🏗️ Architecture

The infrastructure is built on modern cloud-native principles:

- **Security First**: Multi-layered security controls and compliance frameworks
- **High Availability**: Redundant systems across multiple availability zones
- **Scalability**: Auto-scaling capabilities for varying workloads
- **Compliance**: Built-in compliance monitoring and reporting
- **Disaster Recovery**: Automated backup and cross-region failover
- **Observability**: Comprehensive monitoring, logging, and alerting

## 📁 Directory Structure

````
infrastructure/
├── README.md                    # This file
├── .gitignore                   # Git ignore patterns
├── terraform/                   # Infrastructure as Code
│   ├── versions.tf              # Terraform and provider versions
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   ├── main.tf                  # Main infrastructure configuration
│   ├── vpc.tf                   # VPC and networking
│   ├── eks.tf                   # EKS cluster configuration
│   ├── security.tf              # Security resources
│   ├── terraform.tfvars.example # Example variables file
│   └── backend-config.tfvars.example  # Example backend config
├── kubernetes/                  # Kubernetes manifests
│   ├── namespaces.yaml          # Namespace definitions
│   ├── secrets.example.yaml     # Secrets template (DO NOT commit real secrets)
│   ├── security/                # Security policies and RBAC
│   ├── compliance/              # Compliance monitoring services
│   ├── monitoring/              # Prometheus, Grafana, AlertManager
│   ├── backup-recovery/         # Backup and disaster recovery
│   ├── infrastructure-components/  # Redis, RabbitMQ, etc.
│   ├── core-services/           # Application services
│   ├── ingress/                 # Ingress controllers
│   └── storage/                 # Persistent volumes
├── ci-cd/                       # CI/CD workflows
│   ├── cicd.yml                 # Main CI/CD pipeline
│   └── *.yml                    # Additional workflows
├── docker/                      # Container configurations
│   └── financial-services/      # Financial services Dockerfile
├── helm/                        # Helm charts
│   └── nexafi-financial-services/  # Main application chart
├── ansible/                     # Ansible automation
│   ├── playbooks/               # Ansible playbooks
│   ├── roles/                   # Ansible roles
│   └── inventory/               # Inventory examples
├── scripts/                     # Deployment and testing scripts
│   ├── deploy-all.sh            # Complete deployment
│   ├── test-infrastructure.sh   # Infrastructure testing
│   ├── validate-compliance.sh   # Compliance validation
│   ├── security-test.sh         # Security testing
│   └── deployment/              # Deployment utilities
└── docs/                        # Documentation
    └── design_document.md       # Architecture documentation

## 🚀 Quick Start

### Prerequisites

Ensure you have the following tools installed:

- **Terraform** >= 1.5.0
  ```bash
  terraform --version
````

- **kubectl** >= 1.27

  ```bash
  kubectl version --client
  ```

- **Helm** >= 3.12

  ```bash
  helm version
  ```

- **AWS CLI** >= 2.13

  ```bash
  aws --version
  ```

- **Python** >= 3.10 (for scripts)

  ```bash
  python3 --version
  ```

- **yamllint** (for YAML validation)
  ```bash
  pip install yamllint
  ```

### Initial Setup

1. **Configure AWS Credentials**

   ```bash
   aws configure
   # OR use environment variables
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_DEFAULT_REGION="us-west-2"
   ```

2. **Set Environment Variables**

   ```bash
   export ENVIRONMENT=prod  # or staging, dev
   export AWS_REGION=us-west-2
   export TF_VAR_environment=prod
   ```

3. **Create Terraform Backend Resources**  
   Before running terraform, create the S3 bucket and DynamoDB table for state management:

   ```bash
   # Create S3 bucket for terraform state
   aws s3api create-bucket \
     --bucket nexafi-terraform-state-prod \
     --region us-west-2 \
     --create-bucket-configuration LocationConstraint=us-west-2

   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket nexafi-terraform-state-prod \
     --versioning-configuration Status=Enabled

   # Create DynamoDB table for state locking
   aws dynamodb create-table \
     --table-name nexafi-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region us-west-2
   ```

4. **Configure Terraform Backend**

   ```bash
   cd terraform
   cp backend-config.tfvars.example backend-config.tfvars
   # Edit backend-config.tfvars with your values
   vi backend-config.tfvars
   ```

5. **Configure Terraform Variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your environment-specific values
   vi terraform.tfvars
   ```

### Deployment

#### Option 1: Automated Deployment (Recommended)

```bash
cd scripts
./deploy-all.sh
```

This script will:

- Validate prerequisites
- Initialize and apply Terraform
- Configure kubectl
- Deploy Kubernetes resources
- Run validation tests

#### Option 2: Manual Step-by-Step Deployment

**Step 1: Deploy Infrastructure with Terraform**

```bash
cd terraform

# Initialize Terraform with backend configuration
terraform init -backend-config=backend-config.tfvars

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan infrastructure changes
terraform plan -out=plan.out -var-file=terraform.tfvars

# Apply changes (review plan first!)
terraform apply plan.out

# Save outputs
terraform output > ../outputs.txt
```

**Step 2: Configure Kubernetes Access**

```bash
# Update kubeconfig for EKS cluster
aws eks update-kubeconfig \
  --region us-west-2 \
  --name nexafi-prod-primary

# Verify connection
kubectl cluster-info
kubectl get nodes
```

**Step 3: Deploy Kubernetes Resources**

```bash
cd ../kubernetes

# Create namespaces first
kubectl apply -f namespaces.yaml

# Deploy security policies and RBAC
kubectl apply -f security/

# Create secrets (use external secret management in production)
# Copy secrets.example.yaml to secrets.yaml and fill in values
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml with actual base64-encoded values
kubectl apply -f secrets.yaml

# Deploy infrastructure components
kubectl apply -f infrastructure-components/

# Deploy core services
kubectl apply -f core-services/

# Deploy monitoring stack
kubectl apply -f monitoring/

# Deploy ingress
kubectl apply -f ingress/

# Verify deployments
kubectl get all -n nexafi
kubectl get all -n nexafi-infra
kubectl get all -n monitoring
```

**Step 4: Validate Deployment**

```bash
cd ../scripts

# Run infrastructure tests
./test-infrastructure.sh

# Run compliance validation
./validate-compliance.sh

# Run security tests
./security-test.sh
```

## 🔒 Security & Secrets Management

### Critical Security Notes

1. **NEVER commit secrets to version control**
   - All `*.example` files are templates
   - Actual secrets should be in `.gitignore`

2. **Use External Secret Management in Production**
   - AWS Secrets Manager (recommended)
   - HashiCorp Vault
   - Kubernetes External Secrets Operator

3. **Secret Rotation**
   - Rotate secrets every 90 days
   - Use automated secret rotation where possible

### Managing Secrets

#### Development/Testing

For development, you can use the example files:

```bash
# Copy and edit secrets
cp kubernetes/secrets.example.yaml kubernetes/secrets.yaml
# Fill in base64-encoded values
echo -n "your-secret-value" | base64
```

#### Production (Recommended)

Use AWS Secrets Manager integration:

```bash
# Create secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name nexafi/prod/database-credentials \
  --secret-string '{"username":"admin","password":"strong-password"}'

# Deploy External Secrets Operator
kubectl apply -f https://raw.githubusercontent.com/external-secrets/external-secrets/main/deploy/crds/bundle.yaml
helm install external-secrets external-secrets/external-secrets -n external-secrets-system
```

## 🧪 Testing & Validation

### Terraform Validation

```bash
cd terraform

# Format check
terraform fmt -check -recursive

# Validate configuration
terraform validate

# Security scan (requires tfsec)
tfsec .

# Compliance scan (requires checkov)
checkov -d .
```

### Kubernetes Validation

```bash
cd kubernetes

# YAML lint
yamllint .

# Dry-run apply
kubectl apply --dry-run=client -f .

# Validate with kubeval (if installed)
kubeval **/*.yaml
```

### CI/CD Workflow Validation

```bash
cd ci-cd

# YAML syntax check
yamllint *.yml

# GitHub Actions workflow validation (requires act)
act -n

## 📋 Maintenance & Operations

### Regular Maintenance Tasks

1. **Security Updates**: Monthly security patch deployment
2. **Compliance Reviews**: Quarterly compliance assessments
3. **Disaster Recovery Testing**: Monthly DR drills
4. **Performance Optimization**: Quarterly performance reviews
5. **Cost Optimization**: Monthly cost analysis

### Monitoring & Alerts

- **Prometheus**: Metrics collection at `http://prometheus.nexafi.local`
- **Grafana**: Dashboards at `http://grafana.nexafi.local`
- **AlertManager**: Alert management at `http://alertmanager.nexafi.local`

### Backup & Recovery

- **Automated Backups**:
  - Financial databases: Every 4 hours, 7-year retention
  - User databases: Daily, 3-year retention
  - Cluster state: Daily
```

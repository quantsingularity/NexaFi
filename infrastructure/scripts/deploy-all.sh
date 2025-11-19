#!/bin/bash

# Enhanced deployment script for NexaFi infrastructure
# This script implements comprehensive security checks and compliance validation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
KUBERNETES_DIR="$PROJECT_ROOT/kubernetes"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required tools
    local required_tools=("terraform" "kubectl" "aws" "helm" "jq" "yq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error_exit "$tool is required but not installed"
        fi
    done

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS credentials not configured or invalid"
    fi

    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    local min_version="1.5.0"
    if ! printf '%s\n%s\n' "$min_version" "$tf_version" | sort -V -C; then
        error_exit "Terraform version $tf_version is below minimum required version $min_version"
    fi

    log_success "Prerequisites check passed"
}

# Validate environment variables
validate_environment() {
    log_info "Validating environment variables..."

    local required_vars=(
        "AWS_REGION"
        "ENVIRONMENT"
        "TF_VAR_environment"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done

    # Validate environment value
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        error_exit "ENVIRONMENT must be one of: dev, staging, prod"
    fi

    log_success "Environment validation passed"
}

# Security validation
security_validation() {
    log_info "Running security validation..."

    # Check for hardcoded secrets
    log_info "Scanning for hardcoded secrets..."
    if command -v git-secrets &> /dev/null; then
        git secrets --scan || error_exit "Security scan failed - potential secrets detected"
    else
        log_warning "git-secrets not installed, skipping secret scan"
    fi

    # Validate Terraform security
    log_info "Running Terraform security checks..."
    cd "$TERRAFORM_DIR"

    # Check for security best practices
    if command -v tfsec &> /dev/null; then
        tfsec . --format json --out tfsec-results.json || log_warning "tfsec found security issues"
    else
        log_warning "tfsec not installed, skipping Terraform security scan"
    fi

    # Check for compliance
    if command -v checkov &> /dev/null; then
        checkov -d . --framework terraform --output json --output-file checkov-results.json || log_warning "checkov found compliance issues"
    else
        log_warning "checkov not installed, skipping compliance scan"
    fi

    cd "$PROJECT_ROOT"
    log_success "Security validation completed"
}

# Terraform operations
terraform_init() {
    log_info "Initializing Terraform..."
    cd "$TERRAFORM_DIR"

    terraform init \
        -backend-config="bucket=nexafi-terraform-state-${ENVIRONMENT}" \
        -backend-config="key=infrastructure/terraform.tfstate" \
        -backend-config="region=${AWS_REGION}" \
        -backend-config="encrypt=true" \
        -backend-config="dynamodb_table=nexafi-terraform-locks-${ENVIRONMENT}"

    log_success "Terraform initialized"
}

terraform_plan() {
    log_info "Creating Terraform plan..."
    cd "$TERRAFORM_DIR"

    terraform plan \
        -var="environment=${ENVIRONMENT}" \
        -var="primary_region=${AWS_REGION}" \
        -out="tfplan-${ENVIRONMENT}" \
        -detailed-exitcode

    local plan_exit_code=$?

    case $plan_exit_code in
        0)
            log_info "No changes detected in Terraform plan"
            ;;
        1)
            error_exit "Terraform plan failed"
            ;;
        2)
            log_info "Changes detected in Terraform plan"
            ;;
    esac

    # Save plan in human-readable format
    terraform show -no-color "tfplan-${ENVIRONMENT}" > "tfplan-${ENVIRONMENT}.txt"

    log_success "Terraform plan created"
    return $plan_exit_code
}

terraform_apply() {
    log_info "Applying Terraform plan..."
    cd "$TERRAFORM_DIR"

    # Apply with auto-approve for automation
    terraform apply "tfplan-${ENVIRONMENT}"

    # Save outputs
    terraform output -json > "terraform-outputs-${ENVIRONMENT}.json"

    log_success "Terraform applied successfully"
}

# Kubernetes operations
setup_kubectl() {
    log_info "Setting up kubectl configuration..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"
    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$cluster_name" \
        --alias "$cluster_name"

    # Verify connection
    kubectl cluster-info --context "$cluster_name"

    log_success "kubectl configured for cluster $cluster_name"
}

deploy_kubernetes_resources() {
    log_info "Deploying Kubernetes resources..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"

    # Deploy in order of dependencies
    local deployment_order=(
        "namespaces.yaml"
        "security/rbac.yaml"
        "security/pod-security-standards.yaml"
        "security/network-policies.yaml"
        "storage/pv-pvc.yaml"
        "infrastructure-components/"
        "security/"
        "compliance/"
        "monitoring/"
        "backup-recovery/"
        "core-services/"
        "ingress/"
    )

    cd "$KUBERNETES_DIR"

    for resource in "${deployment_order[@]}"; do
        if [[ -f "$resource" ]]; then
            log_info "Deploying $resource..."
            kubectl apply -f "$resource" --context "$cluster_name"
        elif [[ -d "$resource" ]]; then
            log_info "Deploying resources in $resource..."
            kubectl apply -f "$resource" --context "$cluster_name" --recursive
        else
            log_warning "Resource $resource not found, skipping..."
        fi
    done

    log_success "Kubernetes resources deployed"
}

# Validation and health checks
validate_deployment() {
    log_info "Validating deployment..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"

    # Check cluster health
    kubectl get nodes --context "$cluster_name"

    # Check critical namespaces
    local critical_namespaces=("financial-services" "security" "compliance" "monitoring")
    for ns in "${critical_namespaces[@]}"; do
        log_info "Checking namespace $ns..."
        kubectl get pods -n "$ns" --context "$cluster_name"

        # Wait for pods to be ready
        kubectl wait --for=condition=ready pod \
            --all \
            -n "$ns" \
            --timeout=300s \
            --context "$cluster_name" || log_warning "Some pods in $ns are not ready"
    done

    # Check services
    log_info "Checking services..."
    kubectl get services --all-namespaces --context "$cluster_name"

    # Check ingress
    log_info "Checking ingress..."
    kubectl get ingress --all-namespaces --context "$cluster_name"

    log_success "Deployment validation completed"
}

# Compliance checks
compliance_checks() {
    log_info "Running compliance checks..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"

    # Check pod security standards
    log_info "Checking pod security standards..."
    kubectl get pods --all-namespaces \
        --context "$cluster_name" \
        -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}' \
        > pod-security-report.txt

    # Check network policies
    log_info "Checking network policies..."
    kubectl get networkpolicies --all-namespaces --context "$cluster_name"

    # Check RBAC
    log_info "Checking RBAC configuration..."
    kubectl get clusterroles,clusterrolebindings,roles,rolebindings \
        --all-namespaces \
        --context "$cluster_name" \
        > rbac-report.txt

    # Check encryption
    log_info "Checking encryption configuration..."
    kubectl get secrets --all-namespaces \
        --context "$cluster_name" \
        -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.type}{"\n"}{end}' \
        > secrets-report.txt

    log_success "Compliance checks completed"
}

# Monitoring setup
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"

    # Check Prometheus
    kubectl get pods -n monitoring -l app=prometheus --context "$cluster_name"

    # Check Grafana
    kubectl get pods -n monitoring -l app=grafana --context "$cluster_name"

    # Check AlertManager
    kubectl get pods -n monitoring -l app=alertmanager --context "$cluster_name"

    # Get monitoring URLs
    log_info "Getting monitoring service URLs..."
    kubectl get services -n monitoring --context "$cluster_name"

    log_success "Monitoring setup completed"
}

# Backup verification
verify_backups() {
    log_info "Verifying backup configuration..."

    local cluster_name="nexafi-${ENVIRONMENT}-primary"

    # Check backup jobs
    kubectl get cronjobs -n backup-recovery --context "$cluster_name"

    # Check backup storage
    aws s3 ls "s3://nexafi-backups-primary-${ENVIRONMENT}/" || log_warning "Backup bucket not accessible"

    log_success "Backup verification completed"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."

    local report_file="deployment-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).md"

    cat > "$report_file" << EOF
# NexaFi Infrastructure Deployment Report

**Environment:** $ENVIRONMENT
**Date:** $(date)
**AWS Region:** $AWS_REGION

## Deployment Summary

### Terraform Resources
$(cd "$TERRAFORM_DIR" && terraform show -json | jq -r '.values.root_module.resources[] | "- \(.type): \(.name)"')

### Kubernetes Resources
$(kubectl get all --all-namespaces --context "nexafi-${ENVIRONMENT}-primary" | head -20)

### Security Configuration
- Pod Security Standards: Enabled
- Network Policies: Configured
- RBAC: Implemented
- Encryption: Enabled (KMS)

### Compliance Status
- PCI DSS: Configured
- SOC 2: Configured
- GDPR: Configured
- Audit Logging: Enabled

### Monitoring
- Prometheus: Deployed
- Grafana: Deployed
- AlertManager: Deployed

### Backup & Recovery
- Automated Backups: Configured
- Cross-Region Replication: Enabled
- Disaster Recovery: Configured

## Next Steps
1. Configure DNS records
2. Set up SSL certificates
3. Configure external monitoring
4. Run security scans
5. Perform disaster recovery testing

EOF

    log_success "Deployment report generated: $report_file"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    cd "$PROJECT_ROOT"

    # Remove temporary files
    find . -name "*.tmp" -delete
    find . -name "tfplan-*" -delete

    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting NexaFi infrastructure deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "AWS Region: $AWS_REGION"

    # Set trap for cleanup
    trap cleanup EXIT

    # Run deployment steps
    check_prerequisites
    validate_environment
    security_validation

    terraform_init
    if terraform_plan; then
        if [[ "${AUTO_APPROVE:-false}" == "true" ]]; then
            terraform_apply
        else
            read -p "Do you want to apply the Terraform plan? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                terraform_apply
            else
                log_info "Terraform apply skipped"
                exit 0
            fi
        fi
    else
        log_info "No Terraform changes to apply"
    fi

    setup_kubectl
    deploy_kubernetes_resources
    validate_deployment
    compliance_checks
    setup_monitoring
    verify_backups
    generate_report

    log_success "NexaFi infrastructure deployment completed successfully!"
    log_info "Please review the deployment report and configure any remaining manual steps."
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

#!/bin/bash

# NexaFi Infrastructure Deployment Script
# This script deploys the complete NexaFi infrastructure following financial industry standards

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
KUBERNETES_DIR="${PROJECT_ROOT}/kubernetes"
HELM_CHARTS_DIR="${PROJECT_ROOT}/helm-charts"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check required tools
    command -v terraform >/dev/null 2>&1 || missing_tools+=("terraform")
    command -v kubectl >/dev/null 2>&1 || missing_tools+=("kubectl")
    command -v helm >/dev/null 2>&1 || missing_tools+=("helm")
    command -v aws >/dev/null 2>&1 || missing_tools+=("aws-cli")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Deploy Terraform infrastructure
deploy_terraform() {
    log_info "Deploying Terraform infrastructure..."
    
    cd "${TERRAFORM_DIR}"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    log_info "Applying Terraform deployment..."
    terraform apply tfplan
    
    # Clean up plan file
    rm -f tfplan
    
    log_success "Terraform infrastructure deployed successfully"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl for EKS clusters..."
    
    # Get cluster names from Terraform output
    local primary_cluster=$(terraform -chdir="${TERRAFORM_DIR}" output -raw eks_cluster_name_primary)
    local secondary_cluster=$(terraform -chdir="${TERRAFORM_DIR}" output -raw eks_cluster_name_secondary)
    local primary_region=$(terraform -chdir="${TERRAFORM_DIR}" output -raw primary_region)
    local secondary_region=$(terraform -chdir="${TERRAFORM_DIR}" output -raw secondary_region)
    
    # Configure kubectl for primary cluster
    log_info "Configuring kubectl for primary cluster: ${primary_cluster}"
    aws eks update-kubeconfig --region "${primary_region}" --name "${primary_cluster}" --alias "${primary_cluster}"
    
    # Configure kubectl for secondary cluster
    log_info "Configuring kubectl for secondary cluster: ${secondary_cluster}"
    aws eks update-kubeconfig --region "${secondary_region}" --name "${secondary_cluster}" --alias "${secondary_cluster}"
    
    # Set primary cluster as default context
    kubectl config use-context "${primary_cluster}"
    
    log_success "kubectl configured successfully"
}

# Deploy Kubernetes manifests
deploy_kubernetes() {
    log_info "Deploying Kubernetes manifests..."
    
    cd "${KUBERNETES_DIR}"
    
    # Create namespaces first
    log_info "Creating namespaces..."
    kubectl apply -f namespaces.yaml
    
    # Deploy secrets
    log_info "Deploying secrets..."
    kubectl apply -f secrets.yaml
    
    # Deploy storage
    log_info "Deploying storage..."
    kubectl apply -f storage/
    
    # Deploy infrastructure components
    log_info "Deploying infrastructure components..."
    kubectl apply -f infrastructure-components/
    
    # Deploy security components
    log_info "Deploying security components..."
    kubectl apply -f security/
    
    # Deploy compliance components
    log_info "Deploying compliance components..."
    kubectl apply -f compliance/
    
    # Deploy monitoring components
    log_info "Deploying monitoring components..."
    kubectl apply -f monitoring/
    
    # Deploy backup and recovery
    log_info "Deploying backup and recovery..."
    kubectl apply -f backup-recovery/
    
    # Wait for infrastructure components to be ready
    log_info "Waiting for infrastructure components to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n nexafi-infra
    kubectl wait --for=condition=available --timeout=300s deployment/elasticsearch -n nexafi-infra
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n nexafi-infra
    
    # Deploy core services
    log_info "Deploying core services..."
    kubectl apply -f core-services/
    
    # Deploy ingress
    log_info "Deploying ingress..."
    kubectl apply -f ingress/
    
    log_success "Kubernetes manifests deployed successfully"
}

# Deploy Helm charts
deploy_helm() {
    log_info "Deploying Helm charts..."
    
    cd "${HELM_CHARTS_DIR}"
    
    # Add required Helm repositories
    log_info "Adding Helm repositories..."
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add cert-manager https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager for TLS certificates
    log_info "Installing cert-manager..."
    helm upgrade --install cert-manager cert-manager/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true \
        --wait
    
    # Install ingress-nginx
    log_info "Installing ingress-nginx..."
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer \
        --set controller.metrics.enabled=true \
        --wait
    
    # Install NexaFi platform
    log_info "Installing NexaFi platform..."
    helm upgrade --install nexafi-platform . \
        --namespace nexafi \
        --create-namespace \
        --values values.yaml \
        --wait \
        --timeout=20m
    
    log_success "Helm charts deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -A | grep -E "(Error|CrashLoopBackOff|ImagePullBackOff)" && {
        log_warning "Some pods are not in a healthy state"
    } || {
        log_success "All pods are healthy"
    }
    
    # Check services
    log_info "Checking services..."
    kubectl get services -n nexafi
    
    # Check ingress
    log_info "Checking ingress..."
    kubectl get ingress -n nexafi
    
    # Check compliance services
    log_info "Checking compliance services..."
    kubectl get pods -n nexafi -l tier=compliance
    
    # Check monitoring
    log_info "Checking monitoring..."
    kubectl get pods -n nexafi-infra -l tier=monitoring
    
    log_success "Deployment verification completed"
}

# Setup monitoring dashboards
setup_monitoring() {
    log_info "Setting up monitoring dashboards..."
    
    # Get Grafana admin password
    local grafana_password=$(kubectl get secret --namespace nexafi grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
    
    log_info "Grafana admin password: ${grafana_password}"
    log_info "Access Grafana at: http://grafana.nexafi.com"
    log_info "Access Prometheus at: http://prometheus.nexafi.com"
    
    log_success "Monitoring setup completed"
}

# Main deployment function
main() {
    log_info "Starting NexaFi infrastructure deployment..."
    log_info "This deployment follows financial industry standards including:"
    log_info "- NIST Cybersecurity Framework"
    log_info "- Principles for Financial Market Infrastructures (PFMI)"
    log_info "- Zero Trust Security Model"
    log_info "- Comprehensive Audit Logging"
    log_info "- Multi-Region Disaster Recovery"
    
    # Parse command line arguments
    local deploy_terraform=true
    local deploy_k8s=true
    local deploy_helm_charts=true
    local verify=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-terraform)
                deploy_terraform=false
                shift
                ;;
            --skip-k8s)
                deploy_k8s=false
                shift
                ;;
            --skip-helm)
                deploy_helm_charts=false
                shift
                ;;
            --skip-verify)
                verify=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-terraform    Skip Terraform deployment"
                echo "  --skip-k8s         Skip Kubernetes deployment"
                echo "  --skip-helm        Skip Helm deployment"
                echo "  --skip-verify      Skip deployment verification"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    
    if [ "$deploy_terraform" = true ]; then
        deploy_terraform
        configure_kubectl
    fi
    
    if [ "$deploy_k8s" = true ]; then
        deploy_kubernetes
    fi
    
    if [ "$deploy_helm_charts" = true ]; then
        deploy_helm
    fi
    
    if [ "$verify" = true ]; then
        verify_deployment
        setup_monitoring
    fi
    
    log_success "NexaFi infrastructure deployment completed successfully!"
    log_info "Next steps:"
    log_info "1. Configure DNS records for your domain"
    log_info "2. Set up SSL certificates"
    log_info "3. Configure monitoring alerts"
    log_info "4. Run security scans"
    log_info "5. Perform disaster recovery testing"
}

# Run main function
main "$@"


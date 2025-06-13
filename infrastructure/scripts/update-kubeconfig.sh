#!/bin/bash

# NexaFi Kubeconfig Update Script
# This script helps update and manage kubeconfig for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show current context
show_current_context() {
    print_status "Current kubectl context:"
    kubectl config current-context 2>/dev/null || print_warning "No current context set"
    echo ""
    
    print_status "Available contexts:"
    kubectl config get-contexts
    echo ""
}

# Function to switch context
switch_context() {
    print_status "Available contexts:"
    kubectl config get-contexts
    echo ""
    
    read -p "Enter the context name to switch to: " context_name
    
    if kubectl config use-context "$context_name" &> /dev/null; then
        print_success "Switched to context: $context_name"
    else
        print_error "Failed to switch to context: $context_name"
        exit 1
    fi
}

# Function to add new cluster
add_cluster() {
    echo ""
    print_status "Add new cluster configuration:"
    echo "1. Minikube"
    echo "2. Google Kubernetes Engine (GKE)"
    echo "3. Amazon Elastic Kubernetes Service (EKS)"
    echo "4. Azure Kubernetes Service (AKS)"
    echo "5. DigitalOcean Kubernetes"
    echo "6. Custom cluster"
    echo ""
    
    read -p "Select cluster type (1-6): " cluster_type
    
    case $cluster_type in
        1)
            add_minikube_config
            ;;
        2)
            add_gke_config
            ;;
        3)
            add_eks_config
            ;;
        4)
            add_aks_config
            ;;
        5)
            add_do_config
            ;;
        6)
            add_custom_config
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Function to add Minikube config
add_minikube_config() {
    print_status "Setting up Minikube configuration..."
    
    if command -v minikube &> /dev/null; then
        minikube update-context
        print_success "Minikube configuration updated"
    else
        print_error "Minikube is not installed"
        exit 1
    fi
}

# Function to add GKE config
add_gke_config() {
    print_status "Setting up GKE configuration..."
    
    read -p "Enter your GCP project ID: " project_id
    read -p "Enter cluster name: " cluster_name
    read -p "Enter cluster zone/region: " cluster_zone
    
    if command -v gcloud &> /dev/null; then
        gcloud container clusters get-credentials "$cluster_name" --zone="$cluster_zone" --project="$project_id"
        print_success "GKE configuration added"
    else
        print_error "gcloud CLI is not installed"
        print_status "Install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
}

# Function to add EKS config
add_eks_config() {
    print_status "Setting up EKS configuration..."
    
    read -p "Enter cluster name: " cluster_name
    read -p "Enter AWS region: " aws_region
    
    if command -v aws &> /dev/null; then
        aws eks update-kubeconfig --name "$cluster_name" --region "$aws_region"
        print_success "EKS configuration added"
    else
        print_error "AWS CLI is not installed"
        print_status "Install it from: https://aws.amazon.com/cli/"
        exit 1
    fi
}

# Function to add AKS config
add_aks_config() {
    print_status "Setting up AKS configuration..."
    
    read -p "Enter resource group name: " resource_group
    read -p "Enter cluster name: " cluster_name
    
    if command -v az &> /dev/null; then
        az aks get-credentials --resource-group "$resource_group" --name "$cluster_name"
        print_success "AKS configuration added"
    else
        print_error "Azure CLI is not installed"
        print_status "Install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
}

# Function to add DigitalOcean config
add_do_config() {
    print_status "Setting up DigitalOcean Kubernetes configuration..."
    
    read -p "Enter cluster name: " cluster_name
    
    if command -v doctl &> /dev/null; then
        doctl kubernetes cluster kubeconfig save "$cluster_name"
        print_success "DigitalOcean Kubernetes configuration added"
    else
        print_error "doctl is not installed"
        print_status "Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/"
        exit 1
    fi
}

# Function to add custom config
add_custom_config() {
    print_status "Setting up custom cluster configuration..."
    
    read -p "Enter path to kubeconfig file: " kubeconfig_path
    
    if [ -f "$kubeconfig_path" ]; then
        export KUBECONFIG="$HOME/.kube/config:$kubeconfig_path"
        kubectl config view --flatten > "$HOME/.kube/config.tmp"
        mv "$HOME/.kube/config.tmp" "$HOME/.kube/config"
        print_success "Custom configuration merged"
    else
        print_error "Kubeconfig file not found: $kubeconfig_path"
        exit 1
    fi
}

# Function to backup current config
backup_config() {
    backup_file="$HOME/.kube/config.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$HOME/.kube/config" "$backup_file"
    print_success "Current config backed up to: $backup_file"
}

# Function to restore config
restore_config() {
    print_status "Available backup files:"
    ls -la "$HOME/.kube/config.backup."* 2>/dev/null || {
        print_warning "No backup files found"
        return
    }
    
    echo ""
    read -p "Enter the full path of the backup file to restore: " backup_file
    
    if [ -f "$backup_file" ]; then
        cp "$backup_file" "$HOME/.kube/config"
        print_success "Configuration restored from: $backup_file"
    else
        print_error "Backup file not found: $backup_file"
    fi
}

# Function to validate config
validate_config() {
    print_status "Validating kubeconfig..."
    
    if kubectl cluster-info &> /dev/null; then
        print_success "✅ Kubeconfig is valid and cluster is accessible"
        
        print_status "Cluster information:"
        kubectl cluster-info
        
        echo ""
        print_status "Node status:"
        kubectl get nodes
        
    else
        print_error "❌ Cannot connect to cluster with current configuration"
        print_status "Please check your kubeconfig and cluster status"
    fi
}

# Function to show help
show_help() {
    echo "NexaFi Kubeconfig Management Script"
    echo "=================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  show       Show current context and available contexts"
    echo "  switch     Switch to a different context"
    echo "  add        Add a new cluster configuration"
    echo "  backup     Backup current kubeconfig"
    echo "  restore    Restore kubeconfig from backup"
    echo "  validate   Validate current kubeconfig"
    echo "  help       Show this help message"
    echo ""
    echo "If no command is provided, an interactive menu will be shown."
}

# Function to show interactive menu
show_menu() {
    echo ""
    echo "🔧 NexaFi Kubeconfig Management"
    echo "=============================="
    echo ""
    echo "1. Show current context and available contexts"
    echo "2. Switch to a different context"
    echo "3. Add a new cluster configuration"
    echo "4. Backup current kubeconfig"
    echo "5. Restore kubeconfig from backup"
    echo "6. Validate current kubeconfig"
    echo "7. Exit"
    echo ""
    
    read -p "Select an option (1-7): " choice
    
    case $choice in
        1)
            show_current_context
            ;;
        2)
            switch_context
            ;;
        3)
            add_cluster
            ;;
        4)
            backup_config
            ;;
        5)
            restore_config
            ;;
        6)
            validate_config
            ;;
        7)
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Main function
main() {
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        print_status "Please install kubectl first: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    # Create .kube directory if it doesn't exist
    mkdir -p "$HOME/.kube"
    
    # Handle command line arguments
    case "${1:-}" in
        "show")
            show_current_context
            ;;
        "switch")
            switch_context
            ;;
        "add")
            add_cluster
            ;;
        "backup")
            backup_config
            ;;
        "restore")
            restore_config
            ;;
        "validate")
            validate_config
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            # Interactive mode
            while true; do
                show_menu
                echo ""
                read -p "Press Enter to continue or Ctrl+C to exit..."
            done
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"


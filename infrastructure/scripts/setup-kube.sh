#!/bin/bash

# NexaFi Kubernetes Cluster Setup Script
# This script helps set up a Kubernetes cluster for NexaFi deployment

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

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi

    print_status "Detected OS: $OS"
}

# Function to install kubectl
install_kubectl() {
    print_status "Installing kubectl..."

    case $OS in
        "debian")
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
            rm kubectl
            ;;
        "redhat")
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
            rm kubectl
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install kubectl
            else
                curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
                chmod +x kubectl
                sudo mv kubectl /usr/local/bin/
            fi
            ;;
        *)
            print_error "Unsupported OS for automatic kubectl installation"
            print_status "Please install kubectl manually: https://kubernetes.io/docs/tasks/tools/"
            exit 1
            ;;
    esac

    print_success "kubectl installed successfully"
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."

    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            sudo usermod -aG docker $USER
            ;;
        "redhat")
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;
        "macos")
            print_status "Please install Docker Desktop for Mac from: https://docs.docker.com/desktop/mac/install/"
            read -p "Press Enter after installing Docker Desktop..."
            ;;
        *)
            print_error "Unsupported OS for automatic Docker installation"
            exit 1
            ;;
    esac

    print_success "Docker installation completed"
}

# Function to install Minikube
install_minikube() {
    print_status "Installing Minikube..."

    case $OS in
        "debian"|"redhat")
            curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
            sudo install minikube-linux-amd64 /usr/local/bin/minikube
            rm minikube-linux-amd64
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install minikube
            else
                curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-darwin-amd64
                sudo install minikube-darwin-amd64 /usr/local/bin/minikube
                rm minikube-darwin-amd64
            fi
            ;;
        *)
            print_error "Unsupported OS for automatic Minikube installation"
            exit 1
            ;;
    esac

    print_success "Minikube installed successfully"
}

# Function to start Minikube cluster
start_minikube() {
    print_status "Starting Minikube cluster..."

    # Configure Minikube with appropriate resources for NexaFi
    minikube start \
        --cpus=4 \
        --memory=8192 \
        --disk-size=50g \
        --driver=docker \
        --kubernetes-version=v1.28.0

    # Enable required addons
    minikube addons enable ingress
    minikube addons enable storage-provisioner
    minikube addons enable default-storageclass
    minikube addons enable metrics-server

    print_success "Minikube cluster started with required addons"
}

# Function to setup cloud cluster (placeholder)
setup_cloud_cluster() {
    print_status "Cloud cluster setup options:"
    echo ""
    echo "1. Google Kubernetes Engine (GKE)"
    echo "2. Amazon Elastic Kubernetes Service (EKS)"
    echo "3. Azure Kubernetes Service (AKS)"
    echo "4. DigitalOcean Kubernetes"
    echo ""

    read -p "Select cloud provider (1-4): " choice

    case $choice in
        1)
            print_status "GKE Setup Instructions:"
            echo "1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install"
            echo "2. Authenticate: gcloud auth login"
            echo "3. Set project: gcloud config set project YOUR_PROJECT_ID"
            echo "4. Create cluster: gcloud container clusters create nexafi-cluster --num-nodes=3 --machine-type=e2-standard-4"
            echo "5. Get credentials: gcloud container clusters get-credentials nexafi-cluster"
            ;;
        2)
            print_status "EKS Setup Instructions:"
            echo "1. Install AWS CLI: https://aws.amazon.com/cli/"
            echo "2. Install eksctl: https://eksctl.io/introduction/#installation"
            echo "3. Create cluster: eksctl create cluster --name nexafi-cluster --nodes 3 --node-type m5.xlarge"
            echo "4. Update kubeconfig: aws eks update-kubeconfig --name nexafi-cluster"
            ;;
        3)
            print_status "AKS Setup Instructions:"
            echo "1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
            echo "2. Login: az login"
            echo "3. Create resource group: az group create --name nexafi-rg --location eastus"
            echo "4. Create cluster: az aks create --resource-group nexafi-rg --name nexafi-cluster --node-count 3 --node-vm-size Standard_D4s_v3"
            echo "5. Get credentials: az aks get-credentials --resource-group nexafi-rg --name nexafi-cluster"
            ;;
        4)
            print_status "DigitalOcean Kubernetes Setup Instructions:"
            echo "1. Install doctl: https://docs.digitalocean.com/reference/doctl/how-to/install/"
            echo "2. Authenticate: doctl auth init"
            echo "3. Create cluster: doctl kubernetes cluster create nexafi-cluster --count 3 --size s-4vcpu-8gb"
            echo "4. Get credentials: doctl kubernetes cluster kubeconfig save nexafi-cluster"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    echo ""
    print_warning "Please complete the cloud setup manually and ensure kubectl is configured"
    read -p "Press Enter when your cloud cluster is ready..."
}

# Function to verify cluster
verify_cluster() {
    print_status "Verifying cluster setup..."

    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check node status
    print_status "Cluster nodes:"
    kubectl get nodes

    # Check if ingress controller is available
    if kubectl get ingressclass nginx &> /dev/null; then
        print_success "NGINX Ingress Controller is available"
    else
        print_warning "NGINX Ingress Controller not found - will be installed during deployment"
    fi

    # Check storage class
    print_status "Available storage classes:"
    kubectl get storageclass

    print_success "Cluster verification completed"
}

# Function to show next steps
show_next_steps() {
    print_success "Kubernetes cluster setup completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Navigate to the scripts directory: cd scripts"
    echo "2. Deploy NexaFi infrastructure: ./deploy-all.sh"
    echo "3. Monitor deployment: kubectl get pods -n nexafi --watch"
    echo ""
    print_status "Useful commands:"
    echo "kubectl get pods --all-namespaces"
    echo "kubectl logs -n nexafi deployment/api-gateway"
    echo "kubectl port-forward -n nexafi svc/api-gateway-service 8080:80"
    echo ""
}

# Main setup function
main() {
    echo "🚀 NexaFi Kubernetes Cluster Setup"
    echo "=================================="
    echo ""

    detect_os

    # Check if kubectl is already installed
    if ! command -v kubectl &> /dev/null; then
        install_kubectl
    else
        print_success "kubectl is already installed"
    fi

    # Ask user for cluster type
    echo ""
    print_status "Choose cluster setup option:"
    echo "1. Local development (Minikube)"
    echo "2. Cloud cluster (GKE/EKS/AKS/DO)"
    echo "3. Existing cluster (skip setup)"
    echo ""

    read -p "Select option (1-3): " cluster_choice

    case $cluster_choice in
        1)
            # Check if Docker is installed for Minikube
            if ! command -v docker &> /dev/null; then
                install_docker
                print_warning "Please log out and log back in for Docker group changes to take effect"
                print_warning "Then run this script again"
                exit 0
            fi

            # Check if Minikube is installed
            if ! command -v minikube &> /dev/null; then
                install_minikube
            fi

            start_minikube
            ;;
        2)
            setup_cloud_cluster
            ;;
        3)
            print_status "Using existing cluster configuration"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Verify cluster setup
    verify_cluster

    # Show next steps
    show_next_steps
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo ""
        echo "This script helps set up a Kubernetes cluster for NexaFi deployment."
        echo "It can install kubectl, Docker, Minikube, and configure a local or cloud cluster."
        echo ""
        echo "Options:"
        echo "  --help     Show this help message"
        exit 0
        ;;
esac

# Run main function
main "$@"

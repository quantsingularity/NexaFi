#!/bin/bash

# NexaFi Infrastructure Cleanup Script
# This script removes all NexaFi infrastructure from a Kubernetes cluster

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

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig"
        exit 1
    fi

    print_success "kubectl is available and connected to cluster"
}

# Function to confirm deletion
confirm_deletion() {
    echo ""
    print_warning "⚠️  WARNING: This will delete ALL NexaFi infrastructure and data!"
    print_warning "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

    if [ "$confirmation" != "yes" ]; then
        print_status "Deletion cancelled."
        exit 0
    fi

    echo ""
    print_status "Proceeding with deletion..."
}

# Function to delete ingress
delete_ingress() {
    print_status "Deleting ingress configuration..."
    kubectl delete -f ../kubernetes/ingress/nginx-ingress.yaml --ignore-not-found=true
    print_success "Ingress deleted"
}

# Function to delete core services
delete_core_services() {
    print_status "Deleting core services..."

    kubectl delete -f ../kubernetes/core-services/document-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/credit-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/analytics-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/ai-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/payment-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/ledger-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/user-service.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/core-services/api-gateway.yaml --ignore-not-found=true

    print_success "Core services deleted"
}

# Function to delete infrastructure components
delete_infrastructure() {
    print_status "Deleting infrastructure components..."

    kubectl delete -f ../kubernetes/infrastructure-components/kibana.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/infrastructure-components/elasticsearch.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/infrastructure-components/rabbitmq.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/infrastructure-components/redis.yaml --ignore-not-found=true

    print_success "Infrastructure components deleted"
}

# Function to delete storage
delete_storage() {
    print_status "Deleting persistent volumes and claims..."
    kubectl delete -f ../kubernetes/storage/pv-pvc.yaml --ignore-not-found=true
    print_success "Storage deleted"
}

# Function to delete secrets
delete_secrets() {
    print_status "Deleting secrets..."
    kubectl delete -f ../kubernetes/secrets.yaml --ignore-not-found=true
    print_success "Secrets deleted"
}

# Function to delete namespaces
delete_namespaces() {
    print_status "Deleting namespaces..."
    kubectl delete -f ../kubernetes/namespaces.yaml --ignore-not-found=true

    # Wait for namespaces to be fully deleted
    print_status "Waiting for namespaces to be fully deleted..."
    kubectl wait --for=delete namespace/nexafi --timeout=300s 2>/dev/null || true
    kubectl wait --for=delete namespace/nexafi-infra --timeout=300s 2>/dev/null || true

    print_success "Namespaces deleted"
}

# Function to clean up storage directories
cleanup_storage_directories() {
    print_status "Cleaning up storage directories on nodes..."

    # Get all nodes
    nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$nodes" ]; then
        print_warning "No nodes found or cluster not accessible"
        return
    fi

    for node in $nodes; do
        print_status "Cleaning up directories on node: $node"

        # Clean up directories via a temporary pod
        kubectl run temp-storage-cleanup-$RANDOM \
            --image=busybox:1.35 \
            --restart=Never \
            --rm -i \
            --overrides='{
                "spec": {
                    "nodeSelector": {"kubernetes.io/hostname": "'$node'"},
                    "containers": [{
                        "name": "cleanup",
                        "image": "busybox:1.35",
                        "command": ["sh", "-c"],
                        "args": ["rm -rf /mnt/data/nexafi"],
                        "volumeMounts": [{
                            "name": "host-data",
                            "mountPath": "/mnt/data"
                        }]
                    }],
                    "volumes": [{
                        "name": "host-data",
                        "hostPath": {"path": "/mnt/data"}
                    }]
                }
            }' \
            --timeout=60s 2>/dev/null || print_warning "Failed to clean up directories on node $node"
    done

    print_success "Storage directories cleaned up"
}

# Function to show final status
show_final_status() {
    print_status "Final Status Check:"
    echo ""

    # Check if any nexafi resources remain
    remaining_pods=$(kubectl get pods --all-namespaces | grep nexafi | wc -l)
    remaining_services=$(kubectl get services --all-namespaces | grep nexafi | wc -l)
    remaining_pvs=$(kubectl get pv | grep nexafi | wc -l)

    if [ "$remaining_pods" -eq 0 ] && [ "$remaining_services" -eq 0 ] && [ "$remaining_pvs" -eq 0 ]; then
        print_success "✅ All NexaFi resources have been successfully removed"
    else
        print_warning "⚠️  Some resources may still remain:"
        if [ "$remaining_pods" -gt 0 ]; then
            echo "   - Pods: $remaining_pods"
            kubectl get pods --all-namespaces | grep nexafi
        fi
        if [ "$remaining_services" -gt 0 ]; then
            echo "   - Services: $remaining_services"
            kubectl get services --all-namespaces | grep nexafi
        fi
        if [ "$remaining_pvs" -gt 0 ]; then
            echo "   - Persistent Volumes: $remaining_pvs"
            kubectl get pv | grep nexafi
        fi
    fi

    echo ""
    print_status "Manual cleanup commands (if needed):"
    echo "kubectl delete namespace nexafi --force --grace-period=0"
    echo "kubectl delete namespace nexafi-infra --force --grace-period=0"
    echo "kubectl get pv | grep nexafi | awk '{print \$1}' | xargs kubectl delete pv"
    echo ""
}

# Main deletion function
main() {
    echo "🗑️  NexaFi Infrastructure Cleanup"
    echo "================================="
    echo ""

    # Check prerequisites
    check_kubectl

    # Confirm deletion
    confirm_deletion

    # Delete in reverse order
    delete_ingress
    delete_core_services
    delete_infrastructure
    delete_storage
    delete_secrets
    delete_namespaces

    # Clean up storage directories
    cleanup_storage_directories

    # Show final status
    show_final_status

    print_success "NexaFi infrastructure cleanup completed!"
}

# Handle script arguments
case "${1:-}" in
    --force)
        # Skip confirmation for automated scripts
        confirm_deletion() {
            print_warning "Force mode enabled - skipping confirmation"
        }
        ;;
    --help|-h)
        echo "Usage: $0 [--force] [--help]"
        echo ""
        echo "Options:"
        echo "  --force    Skip confirmation prompt"
        echo "  --help     Show this help message"
        echo ""
        echo "This script removes all NexaFi infrastructure from the Kubernetes cluster."
        exit 0
        ;;
esac

# Run main function
main "$@"

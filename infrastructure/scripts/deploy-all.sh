#!/bin/bash

# NexaFi Infrastructure Deployment Script
# This script deploys the complete NexaFi infrastructure to a Kubernetes cluster

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

# Function to create directories on nodes (for hostPath volumes)
create_storage_directories() {
    print_status "Creating storage directories on nodes..."
    
    # Get all nodes
    nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
    
    for node in $nodes; do
        print_status "Creating directories on node: $node"
        
        # Create directories via a temporary pod
        kubectl run temp-storage-setup-$RANDOM \
            --image=busybox:1.35 \
            --restart=Never \
            --rm -i \
            --overrides='{
                "spec": {
                    "nodeSelector": {"kubernetes.io/hostname": "'$node'"},
                    "containers": [{
                        "name": "setup",
                        "image": "busybox:1.35",
                        "command": ["sh", "-c"],
                        "args": ["mkdir -p /mnt/data/nexafi/{user-service,ledger-service,payment-service,ai-service/{data,models},analytics-service,credit-service/{data,models},document-service,redis,rabbitmq,elasticsearch} && chmod -R 755 /mnt/data/nexafi"],
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
            --timeout=60s || print_warning "Failed to create directories on node $node"
    done
    
    print_success "Storage directories created"
}

# Function to deploy namespaces
deploy_namespaces() {
    print_status "Creating namespaces..."
    kubectl apply -f ../kubernetes/namespaces.yaml
    print_success "Namespaces created"
}

# Function to deploy secrets
deploy_secrets() {
    print_status "Deploying secrets..."
    kubectl apply -f ../kubernetes/secrets.yaml
    print_success "Secrets deployed"
}

# Function to deploy storage
deploy_storage() {
    print_status "Deploying persistent volumes and claims..."
    kubectl apply -f ../kubernetes/storage/pv-pvc.yaml
    
    # Wait for PVCs to be bound
    print_status "Waiting for PVCs to be bound..."
    kubectl wait --for=condition=Bound pvc --all -n nexafi --timeout=300s
    kubectl wait --for=condition=Bound pvc --all -n nexafi-infra --timeout=300s
    
    print_success "Storage deployed and bound"
}

# Function to deploy infrastructure components
deploy_infrastructure() {
    print_status "Deploying infrastructure components..."
    
    # Deploy Redis
    print_status "Deploying Redis..."
    kubectl apply -f ../kubernetes/infrastructure-components/redis.yaml
    
    # Deploy RabbitMQ
    print_status "Deploying RabbitMQ..."
    kubectl apply -f ../kubernetes/infrastructure-components/rabbitmq.yaml
    
    # Deploy Elasticsearch
    print_status "Deploying Elasticsearch..."
    kubectl apply -f ../kubernetes/infrastructure-components/elasticsearch.yaml
    
    # Deploy Kibana
    print_status "Deploying Kibana..."
    kubectl apply -f ../kubernetes/infrastructure-components/kibana.yaml
    
    # Wait for infrastructure to be ready
    print_status "Waiting for infrastructure components to be ready..."
    kubectl wait --for=condition=available deployment/redis -n nexafi-infra --timeout=300s
    kubectl wait --for=condition=available deployment/rabbitmq -n nexafi-infra --timeout=300s
    kubectl wait --for=condition=available deployment/elasticsearch -n nexafi-infra --timeout=600s
    kubectl wait --for=condition=available deployment/kibana -n nexafi-infra --timeout=300s
    
    print_success "Infrastructure components deployed and ready"
}

# Function to deploy core services
deploy_core_services() {
    print_status "Deploying core services..."
    
    # Deploy API Gateway
    print_status "Deploying API Gateway..."
    kubectl apply -f ../kubernetes/core-services/api-gateway.yaml
    
    # Deploy User Service
    print_status "Deploying User Service..."
    kubectl apply -f ../kubernetes/core-services/user-service.yaml
    
    # Deploy Ledger Service
    print_status "Deploying Ledger Service..."
    kubectl apply -f ../kubernetes/core-services/ledger-service.yaml
    
    # Deploy Payment Service
    print_status "Deploying Payment Service..."
    kubectl apply -f ../kubernetes/core-services/payment-service.yaml
    
    # Deploy AI Service
    print_status "Deploying AI Service..."
    kubectl apply -f ../kubernetes/core-services/ai-service.yaml
    
    # Deploy Analytics Service
    print_status "Deploying Analytics Service..."
    kubectl apply -f ../kubernetes/core-services/analytics-service.yaml
    
    # Deploy Credit Service
    print_status "Deploying Credit Service..."
    kubectl apply -f ../kubernetes/core-services/credit-service.yaml
    
    # Deploy Document Service
    print_status "Deploying Document Service..."
    kubectl apply -f ../kubernetes/core-services/document-service.yaml
    
    # Wait for core services to be ready
    print_status "Waiting for core services to be ready..."
    kubectl wait --for=condition=available deployment/api-gateway -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/user-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/ledger-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/payment-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/ai-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/analytics-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/credit-service -n nexafi --timeout=300s
    kubectl wait --for=condition=available deployment/document-service -n nexafi --timeout=300s
    
    print_success "Core services deployed and ready"
}

# Function to deploy ingress
deploy_ingress() {
    print_status "Deploying ingress configuration..."
    
    # Check if nginx ingress controller is installed
    if ! kubectl get ingressclass nginx &> /dev/null; then
        print_warning "NGINX Ingress Controller not found. Installing..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
        
        # Wait for ingress controller to be ready
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
    fi
    
    kubectl apply -f ../kubernetes/ingress/nginx-ingress.yaml
    print_success "Ingress deployed"
}

# Function to display deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    
    print_status "Namespaces:"
    kubectl get namespaces | grep nexafi
    echo ""
    
    print_status "Infrastructure Components (nexafi-infra namespace):"
    kubectl get pods,svc -n nexafi-infra
    echo ""
    
    print_status "Core Services (nexafi namespace):"
    kubectl get pods,svc -n nexafi
    echo ""
    
    print_status "Persistent Volumes:"
    kubectl get pv | grep nexafi
    echo ""
    
    print_status "Ingress:"
    kubectl get ingress -n nexafi
    kubectl get ingress -n nexafi-infra
    echo ""
}

# Function to display access information
show_access_info() {
    print_success "NexaFi Infrastructure Deployed Successfully!"
    echo ""
    print_status "Access Information:"
    echo ""
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    
    if [ "$INGRESS_IP" = "pending" ] || [ -z "$INGRESS_IP" ]; then
        INGRESS_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.clusterIP}')
        print_warning "LoadBalancer IP is pending. Using ClusterIP: $INGRESS_IP"
        print_warning "You may need to set up port forwarding or configure your load balancer"
    fi
    
    echo "🌐 API Gateway: http://$INGRESS_IP (or https://api.nexafi.com if DNS is configured)"
    echo "📊 Kibana Dashboard: http://$INGRESS_IP:5601 (or https://kibana.nexafi.com if DNS is configured)"
    echo "🐰 RabbitMQ Management: http://$INGRESS_IP:15672 (or https://rabbitmq.nexafi.com if DNS is configured)"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   RabbitMQ: nexafi / nexafi123"
    echo "   Infrastructure Basic Auth: nexafi / nexafi123"
    echo ""
    
    print_status "Port Forwarding Commands (if needed):"
    echo "kubectl port-forward -n nexafi svc/api-gateway-service 8080:80"
    echo "kubectl port-forward -n nexafi-infra svc/kibana-service 5601:5601"
    echo "kubectl port-forward -n nexafi-infra svc/rabbitmq-service 15672:15672"
    echo ""
    
    print_status "Health Check Commands:"
    echo "kubectl get pods -n nexafi"
    echo "kubectl get pods -n nexafi-infra"
    echo "kubectl logs -n nexafi deployment/api-gateway"
    echo ""
}

# Main deployment function
main() {
    echo "🚀 NexaFi Infrastructure Deployment"
    echo "===================================="
    echo ""
    
    # Check prerequisites
    check_kubectl
    
    # Create storage directories
    create_storage_directories
    
    # Deploy in order
    deploy_namespaces
    deploy_secrets
    deploy_storage
    deploy_infrastructure
    
    # Wait a bit for infrastructure to stabilize
    print_status "Waiting for infrastructure to stabilize..."
    sleep 30
    
    deploy_core_services
    deploy_ingress
    
    # Show status
    show_status
    show_access_info
    
    print_success "NexaFi infrastructure deployment completed successfully!"
}

# Run main function
main "$@"


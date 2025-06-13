# NexaFi Infrastructure as Code (IaC)

## Overview
This directory contains the Infrastructure as Code (IaC) for the NexaFi project. The goal is to define and manage the entire infrastructure required for deploying and operating the NexaFi backend and frontend services using Kubernetes.

## Architecture
The infrastructure is designed to be cloud-agnostic and highly scalable, leveraging Kubernetes for container orchestration. It includes:
- **Kubernetes Cluster**: The core platform for deploying microservices.
- **Core Services**: Kubernetes manifests for all NexaFi backend microservices (API Gateway, User, Ledger, Payment, AI, Analytics, Credit, Document Services).
- **Infrastructure Components**: Kubernetes manifests for supporting services like Redis (caching), RabbitMQ (message queue), and Elasticsearch/Kibana (logging and monitoring).
- **Networking**: Ingress controllers, service meshes (optional).
- **Storage**: Persistent volumes for stateful applications.
- **Monitoring & Logging**: Centralized logging and metrics collection.
- **CI/CD Integration**: Scripts for automated deployments.

## Directory Structure
```
infra/
├── kubernetes/
│   ├── core-services/        # Kubernetes manifests for backend microservices
│   │   ├── api-gateway.yaml
│   │   ├── user-service.yaml
│   │   ├── ledger-service.yaml
│   │   ├── payment-service.yaml
│   │   ├── ai-service.yaml
│   │   ├── analytics-service.yaml
│   │   ├── credit-service.yaml
│   │   └── document-service.yaml
│   ├── infrastructure-components/ # Kubernetes manifests for supporting infrastructure
│   │   ├── redis.yaml
│   │   ├── rabbitmq.yaml
│   │   ├── elasticsearch.yaml
│   │   └── kibana.yaml
│   ├── ingress/              # Ingress controller and rules
│   │   └── nginx-ingress.yaml
│   ├── storage/              # Persistent volume claims
│   │   └── pv-pvc.yaml
│   └── namespaces.yaml       # Kubernetes namespaces
├── scripts/                  # Deployment and management scripts
│   ├── deploy-all.sh
│   ├── delete-all.sh
│   ├── setup-kube.sh
│   └── update-kubeconfig.sh
└── README.md                 # This file
```

## Technologies Used
- **Kubernetes**: Container orchestration
- **Docker**: Containerization
- **Helm (future)**: Package management for Kubernetes applications
- **kubectl**: Kubernetes command-line tool

## Deployment Workflow
1. **Setup Kubernetes Cluster**: Ensure a Kubernetes cluster is running (e.g., Minikube, GKE, EKS, AKS).
2. **Configure kubectl**: Point `kubectl` to your cluster.
3. **Deploy Infrastructure Components**: Apply manifests for Redis, RabbitMQ, Elasticsearch, Kibana.
4. **Deploy Core Services**: Apply manifests for all NexaFi microservices.
5. **Configure Ingress**: Set up ingress rules for external access.

## Getting Started
Refer to the `scripts/` directory for automated deployment and management scripts.

## Future Enhancements
- **Helm Charts**: For easier deployment and management of complex applications.
- **Service Mesh**: Implement Istio or Linkerd for advanced traffic management, security, and observability.
- **Automated Scaling**: Horizontal Pod Autoscalers (HPA) and Cluster Autoscaler.
- **Monitoring & Alerting**: Prometheus and Grafana integration.
- **Secret Management**: Vault or Kubernetes Secrets for sensitive data.
- **CI/CD Pipelines**: Integrate with Jenkins, GitLab CI, or GitHub Actions for automated deployments.



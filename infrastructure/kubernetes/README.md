# Kubernetes Manifests

## Prerequisites

- kubectl >= 1.27
- Access to Kubernetes cluster
- Helm >= 3.12 (for Helm charts)

## Directory Structure

- `namespaces.yaml` - Namespace definitions
- `secrets.example.yaml` - Secret templates (DO NOT commit real secrets)
- `security/` - RBAC, NetworkPolicies, PodSecurityStandards
- `infrastructure-components/` - Redis, RabbitMQ, Elasticsearch, etc.
- `core-services/` - Application microservices
- `monitoring/` - Prometheus, Grafana, AlertManager
- `ingress/` - Ingress controllers and rules
- `storage/` - PersistentVolumes and PersistentVolumeClaims
- `backup-recovery/` - Backup jobs and DR procedures
- `compliance/` - Compliance monitoring services

## Deployment

### Method 1: Direct kubectl apply

```bash
# Create namespaces first
kubectl apply -f namespaces.yaml

# Deploy security policies
kubectl apply -f security/

# Create secrets (DO NOT use example file in production)
kubectl apply -f secrets.yaml  # Create this from secrets.example.yaml

# Deploy infrastructure components
kubectl apply -f infrastructure-components/

# Deploy core services
kubectl apply -f core-services/

# Deploy monitoring
kubectl apply -f monitoring/

# Deploy ingress
kubectl apply -f ingress/
```

### Method 2: Using Kustomize

```bash
# Dry run
kubectl apply -k . --dry-run=client

# Apply all manifests
kubectl apply -k .
```

## Validation

```bash
# YAML lint
yamllint .

# Dry-run validation
kubectl apply --dry-run=client -f .

# Validate with kubeval (if installed)
kubeval **/*.yaml

# Check deployed resources
kubectl get all -n nexafi
kubectl get all -n nexafi-infra
kubectl get all -n monitoring
```

## Secret Management

### Development

```bash
# Copy example file
cp secrets.example.yaml secrets.yaml

# Encode secrets (base64)
echo -n "my-secret-value" | base64

# Edit secrets.yaml with encoded values
# Apply
kubectl apply -f secrets.yaml
```

### Production (Recommended)

Use external secret management:

- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes External Secrets Operator

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n nexafi

# View pod logs
kubectl logs -n nexafi <pod-name>

# Describe resource
kubectl describe pod -n nexafi <pod-name>

# Execute into pod
kubectl exec -it -n nexafi <pod-name> -- /bin/sh
```

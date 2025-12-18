#!/usr/bin/env bash
# Kubernetes validation script for NexaFi infrastructure

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
K8S_DIR="${INFRA_DIR}/kubernetes"
VALIDATION_LOG_DIR="${INFRA_DIR}/validation_logs"

mkdir -p "${VALIDATION_LOG_DIR}"

echo "==========================================="
echo "Kubernetes Validation for NexaFi"
echo "==========================================="
echo ""

cd "${K8S_DIR}"

# 1. Check yamllint
echo "1. Running yamllint..."
if command -v yamllint &> /dev/null; then
    if yamllint -d relaxed . > "${VALIDATION_LOG_DIR}/kubernetes_yamllint.log" 2>&1; then
        echo -e "${GREEN}✓ All YAML files are valid${NC}"
    else
        echo -e "${YELLOW}⚠ YAML lint warnings found${NC}"
        echo "  See: ${VALIDATION_LOG_DIR}/kubernetes_yamllint.log"
        echo "  First 20 warnings:"
        head -20 "${VALIDATION_LOG_DIR}/kubernetes_yamllint.log"
    fi
else
    echo -e "${YELLOW}⚠ yamllint not installed${NC}"
    echo "  Install with: pip install yamllint"
fi
echo ""

# 2. Check YAML syntax with Python
echo "2. Validating YAML syntax..."
YAML_FILES=$(find . -name "*.yaml" -o -name "*.yml" | grep -v ".example" | grep -v "overlays")
YAML_ERRORS=0

for file in $YAML_FILES; do
    if ! python3 -c "import yaml; yaml.safe_load_all(open('$file'))" 2>/dev/null; then
        echo -e "${RED}✗ Invalid YAML: $file${NC}"
        YAML_ERRORS=$((YAML_ERRORS + 1))
    fi
done

if [ $YAML_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All YAML files have valid syntax${NC}"
else
    echo -e "${RED}✗ Found $YAML_ERRORS YAML files with syntax errors${NC}"
fi
echo ""

# 3. Check kubectl
echo "3. Checking kubectl..."
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}✓ kubectl is installed${NC}"
    kubectl version --client 2>&1 | head -1
    
    # 4. Dry-run validation
    echo ""
    echo "4. Running kubectl dry-run validation..."
    DRY_RUN_ERRORS=0
    
    # Validate each manifest
    for file in namespaces.yaml $(find . -name "*.yaml" -not -path "*/overlays/*" -not -name "secrets.example.yaml" -not -name "*.example.yaml" | sort); do
        echo -n "  Validating $file... "
        if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            DRY_RUN_ERRORS=$((DRY_RUN_ERRORS + 1))
            kubectl apply --dry-run=client -f "$file" 2>&1 | head -5 >> "${VALIDATION_LOG_DIR}/kubectl_dryrun_errors.log"
        fi
    done
    
    if [ $DRY_RUN_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ All manifests passed kubectl dry-run${NC}"
    else
        echo -e "${RED}✗ $DRY_RUN_ERRORS manifests failed kubectl dry-run${NC}"
        echo "  See: ${VALIDATION_LOG_DIR}/kubectl_dryrun_errors.log"
    fi
else
    echo -e "${YELLOW}⚠ kubectl not installed, skipping dry-run validation${NC}"
    echo "  Install from: https://kubernetes.io/docs/tasks/tools/"
fi
echo ""

# 5. Check kustomization
echo "5. Checking kustomize configuration..."
if [ -f "kustomization.yaml" ]; then
    echo -e "${GREEN}✓ kustomization.yaml exists${NC}"
    
    if command -v kustomize &> /dev/null; then
        echo "  Building kustomize..."
        if kustomize build . > "${VALIDATION_LOG_DIR}/kustomize_build.yaml" 2>&1; then
            echo -e "${GREEN}✓ Kustomize build succeeded${NC}"
            echo "  Output saved to: ${VALIDATION_LOG_DIR}/kustomize_build.yaml"
        else
            echo -e "${RED}✗ Kustomize build failed${NC}"
            cat "${VALIDATION_LOG_DIR}/kustomize_build.yaml"
        fi
    else
        echo -e "${YELLOW}⚠ kustomize not installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ kustomization.yaml not found${NC}"
fi
echo ""

# 6. Check for secrets
echo "6. Checking secrets configuration..."
if [ -f "secrets.example.yaml" ]; then
    echo -e "${GREEN}✓ secrets.example.yaml exists${NC}"
else
    echo -e "${YELLOW}⚠ secrets.example.yaml not found${NC}"
fi

if [ -f "secrets.yaml" ]; then
    echo -e "${YELLOW}⚠ secrets.yaml exists (should not be committed)${NC}"
    echo "  Ensure secrets.yaml is in .gitignore"
fi
echo ""

# 7. Check resource definitions
echo "7. Checking resource definitions..."
MISSING_RESOURCES=0

# Check for resource requests/limits
DEPLOYMENTS=$(find . -name "*.yaml" -exec grep -l "kind: Deployment" {} \;)
for deploy in $DEPLOYMENTS; do
    if ! grep -q "resources:" "$deploy"; then
        echo -e "${YELLOW}⚠ Missing resources in: $deploy${NC}"
        MISSING_RESOURCES=$((MISSING_RESOURCES + 1))
    fi
done

if [ $MISSING_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ All deployments have resource definitions${NC}"
else
    echo -e "${YELLOW}⚠ $MISSING_RESOURCES deployments missing resource definitions${NC}"
fi
echo ""

# 8. Check for probes
echo "8. Checking liveness/readiness probes..."
MISSING_PROBES=0

for deploy in $DEPLOYMENTS; do
    if ! grep -q "livenessProbe:\|readinessProbe:" "$deploy"; then
        echo -e "${YELLOW}⚠ Missing probes in: $deploy${NC}"
        MISSING_PROBES=$((MISSING_PROBES + 1))
    fi
done

if [ $MISSING_PROBES -eq 0 ]; then
    echo -e "${GREEN}✓ All deployments have health probes${NC}"
else
    echo -e "${YELLOW}⚠ $MISSING_PROBES deployments missing health probes${NC}"
fi
echo ""

# 9. Check for deprecated APIs
echo "9. Checking for deprecated API versions..."
DEPRECATED_APIS=0

# Common deprecated APIs in Kubernetes 1.25+
if grep -r "apiVersion: policy/v1beta1" . 2>/dev/null | grep -v ".example"; then
    echo -e "${RED}✗ Found deprecated policy/v1beta1 (use policy/v1)${NC}"
    DEPRECATED_APIS=$((DEPRECATED_APIS + 1))
fi

if grep -r "apiVersion: autoscaling/v2beta" . 2>/dev/null | grep -v ".example"; then
    echo -e "${RED}✗ Found deprecated autoscaling/v2beta* (use autoscaling/v2)${NC}"
    DEPRECATED_APIS=$((DEPRECATED_APIS + 1))
fi

if [ $DEPRECATED_APIS -eq 0 ]; then
    echo -e "${GREEN}✓ No deprecated API versions found${NC}"
fi
echo ""

# Summary
echo "==========================================="
echo "Kubernetes Validation Summary"
echo "==========================================="
echo ""
echo "Validation logs saved to: ${VALIDATION_LOG_DIR}/"
echo ""
echo "Next steps:"
echo "  1. Review any warnings above"
echo "  2. Copy secrets.example.yaml to secrets.yaml"
echo "  3. Fill in base64-encoded secret values"
echo "  4. Apply to cluster: kubectl apply -f ."
echo ""
echo -e "${GREEN}✓ Kubernetes validation completed${NC}"

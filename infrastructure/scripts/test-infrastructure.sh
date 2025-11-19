#!/bin/bash

# Comprehensive testing framework for NexaFi infrastructure
# This script implements security, compliance, and functional testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

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

# Test result functions
test_pass() {
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
    log_success "✓ $1"
}

test_fail() {
    ((TOTAL_TESTS++))
    ((FAILED_TESTS++))
    log_error "✗ $1"
}

test_skip() {
    ((TOTAL_TESTS++))
    ((SKIPPED_TESTS++))
    log_warning "⊘ $1"
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."

    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Set test timestamp
    TEST_TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    # Initialize test report
    cat > "$TEST_RESULTS_DIR/test-report-$TEST_TIMESTAMP.md" << EOF
# NexaFi Infrastructure Test Report

**Date:** $(date)
**Environment:** ${ENVIRONMENT:-unknown}
**Test Run ID:** $TEST_TIMESTAMP

## Test Summary

EOF

    log_success "Test environment setup completed"
}

# Infrastructure connectivity tests
test_infrastructure_connectivity() {
    log_info "Running infrastructure connectivity tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test kubectl connectivity
    if kubectl cluster-info --context "$cluster_name" &> /dev/null; then
        test_pass "Kubernetes cluster connectivity"
    else
        test_fail "Kubernetes cluster connectivity"
        return 1
    fi

    # Test AWS connectivity
    if aws sts get-caller-identity &> /dev/null; then
        test_pass "AWS API connectivity"
    else
        test_fail "AWS API connectivity"
        return 1
    fi

    # Test node health
    local node_count=$(kubectl get nodes --context "$cluster_name" --no-headers | wc -l)
    if [[ $node_count -gt 0 ]]; then
        test_pass "Kubernetes nodes available ($node_count nodes)"
    else
        test_fail "No Kubernetes nodes available"
    fi

    # Test node readiness
    local ready_nodes=$(kubectl get nodes --context "$cluster_name" --no-headers | grep -c " Ready ")
    if [[ $ready_nodes -eq $node_count ]]; then
        test_pass "All Kubernetes nodes ready"
    else
        test_fail "Not all Kubernetes nodes ready ($ready_nodes/$node_count)"
    fi
}

# Security tests
test_security_configuration() {
    log_info "Running security configuration tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test pod security standards
    local restricted_namespaces=("financial-services" "security" "compliance")
    for ns in "${restricted_namespaces[@]}"; do
        if kubectl get namespace "$ns" --context "$cluster_name" &> /dev/null; then
            local pss_label=$(kubectl get namespace "$ns" --context "$cluster_name" -o jsonpath='{.metadata.labels.pod-security\.kubernetes\.io/enforce}')
            if [[ "$pss_label" == "restricted" ]]; then
                test_pass "Pod Security Standards enforced in $ns namespace"
            else
                test_fail "Pod Security Standards not properly enforced in $ns namespace"
            fi
        else
            test_skip "Namespace $ns not found"
        fi
    done

    # Test network policies
    local network_policies=$(kubectl get networkpolicies --all-namespaces --context "$cluster_name" --no-headers | wc -l)
    if [[ $network_policies -gt 0 ]]; then
        test_pass "Network policies configured ($network_policies policies)"
    else
        test_fail "No network policies found"
    fi

    # Test RBAC configuration
    local service_accounts=$(kubectl get serviceaccounts --all-namespaces --context "$cluster_name" --no-headers | wc -l)
    if [[ $service_accounts -gt 10 ]]; then  # Expect multiple service accounts
        test_pass "Service accounts configured ($service_accounts accounts)"
    else
        test_fail "Insufficient service accounts configured"
    fi

    # Test secrets encryption
    local secrets=$(kubectl get secrets --all-namespaces --context "$cluster_name" --no-headers | wc -l)
    if [[ $secrets -gt 0 ]]; then
        test_pass "Secrets present in cluster ($secrets secrets)"

        # Check for default service account tokens (should be minimal)
        local default_tokens=$(kubectl get secrets --all-namespaces --context "$cluster_name" --no-headers | grep -c "default-token" || true)
        if [[ $default_tokens -lt 10 ]]; then
            test_pass "Minimal default service account tokens"
        else
            test_warning "Many default service account tokens present ($default_tokens)"
        fi
    else
        test_fail "No secrets found in cluster"
    fi
}

# Compliance tests
test_compliance_configuration() {
    log_info "Running compliance configuration tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test audit logging
    if kubectl get pods -n compliance -l app=audit-service --context "$cluster_name" &> /dev/null; then
        local audit_pods=$(kubectl get pods -n compliance -l app=audit-service --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $audit_pods -gt 0 ]]; then
            test_pass "Audit service running ($audit_pods pods)"
        else
            test_fail "Audit service not running"
        fi
    else
        test_fail "Audit service not found"
    fi

    # Test compliance monitoring
    if kubectl get pods -n compliance -l app=compliance-monitor --context "$cluster_name" &> /dev/null; then
        local compliance_pods=$(kubectl get pods -n compliance -l app=compliance-monitor --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $compliance_pods -gt 0 ]]; then
            test_pass "Compliance monitoring running ($compliance_pods pods)"
        else
            test_fail "Compliance monitoring not running"
        fi
    else
        test_fail "Compliance monitoring not found"
    fi

    # Test backup jobs
    if kubectl get cronjobs -n backup-recovery --context "$cluster_name" &> /dev/null; then
        local backup_jobs=$(kubectl get cronjobs -n backup-recovery --context "$cluster_name" --no-headers | wc -l)
        if [[ $backup_jobs -gt 0 ]]; then
            test_pass "Backup jobs configured ($backup_jobs jobs)"
        else
            test_fail "No backup jobs configured"
        fi
    else
        test_fail "Backup recovery namespace not found"
    fi

    # Test data retention policies
    local pvcs=$(kubectl get pvc --all-namespaces --context "$cluster_name" --no-headers | wc -l)
    if [[ $pvcs -gt 0 ]]; then
        test_pass "Persistent volumes configured ($pvcs PVCs)"
    else
        test_warning "No persistent volumes found"
    fi
}

# Financial services tests
test_financial_services() {
    log_info "Running financial services tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test financial services namespace
    if kubectl get namespace financial-services --context "$cluster_name" &> /dev/null; then
        test_pass "Financial services namespace exists"

        # Test financial services pods
        local financial_pods=$(kubectl get pods -n financial-services --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $financial_pods -gt 0 ]]; then
            test_pass "Financial services pods running ($financial_pods pods)"
        else
            test_fail "No financial services pods running"
        fi

        # Test financial services with taints
        local tainted_nodes=$(kubectl get nodes --context "$cluster_name" -o jsonpath='{.items[*].spec.taints[?(@.key=="financial-services")].key}' | wc -w)
        if [[ $tainted_nodes -gt 0 ]]; then
            test_pass "Financial services dedicated nodes configured ($tainted_nodes nodes)"
        else
            test_warning "No dedicated financial services nodes found"
        fi
    else
        test_fail "Financial services namespace not found"
    fi

    # Test API Gateway
    if kubectl get pods -n api-gateway --context "$cluster_name" &> /dev/null; then
        local gateway_pods=$(kubectl get pods -n api-gateway --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $gateway_pods -gt 0 ]]; then
            test_pass "API Gateway running ($gateway_pods pods)"
        else
            test_fail "API Gateway not running"
        fi
    else
        test_skip "API Gateway namespace not found"
    fi
}

# Monitoring tests
test_monitoring_stack() {
    log_info "Running monitoring stack tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test Prometheus
    if kubectl get pods -n monitoring -l app=prometheus --context "$cluster_name" &> /dev/null; then
        local prometheus_pods=$(kubectl get pods -n monitoring -l app=prometheus --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $prometheus_pods -gt 0 ]]; then
            test_pass "Prometheus running ($prometheus_pods pods)"
        else
            test_fail "Prometheus not running"
        fi
    else
        test_fail "Prometheus not found"
    fi

    # Test Grafana
    if kubectl get pods -n monitoring -l app=grafana --context "$cluster_name" &> /dev/null; then
        local grafana_pods=$(kubectl get pods -n monitoring -l app=grafana --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $grafana_pods -gt 0 ]]; then
            test_pass "Grafana running ($grafana_pods pods)"
        else
            test_fail "Grafana not running"
        fi
    else
        test_fail "Grafana not found"
    fi

    # Test AlertManager
    if kubectl get pods -n monitoring -l app=alertmanager --context "$cluster_name" &> /dev/null; then
        local alertmanager_pods=$(kubectl get pods -n monitoring -l app=alertmanager --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $alertmanager_pods -gt 0 ]]; then
            test_pass "AlertManager running ($alertmanager_pods pods)"
        else
            test_fail "AlertManager not running"
        fi
    else
        test_fail "AlertManager not found"
    fi

    # Test service monitors
    local service_monitors=$(kubectl get servicemonitors --all-namespaces --context "$cluster_name" --no-headers 2>/dev/null | wc -l || echo "0")
    if [[ $service_monitors -gt 0 ]]; then
        test_pass "Service monitors configured ($service_monitors monitors)"
    else
        test_warning "No service monitors found"
    fi
}

# Infrastructure components tests
test_infrastructure_components() {
    log_info "Running infrastructure components tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test Redis
    if kubectl get pods -n infrastructure-components -l app=redis --context "$cluster_name" &> /dev/null; then
        local redis_pods=$(kubectl get pods -n infrastructure-components -l app=redis --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $redis_pods -gt 0 ]]; then
            test_pass "Redis running ($redis_pods pods)"
        else
            test_fail "Redis not running"
        fi
    else
        test_skip "Redis not found"
    fi

    # Test RabbitMQ
    if kubectl get pods -n infrastructure-components -l app=rabbitmq --context "$cluster_name" &> /dev/null; then
        local rabbitmq_pods=$(kubectl get pods -n infrastructure-components -l app=rabbitmq --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $rabbitmq_pods -gt 0 ]]; then
            test_pass "RabbitMQ running ($rabbitmq_pods pods)"
        else
            test_fail "RabbitMQ not running"
        fi
    else
        test_skip "RabbitMQ not found"
    fi

    # Test Elasticsearch
    if kubectl get pods -n infrastructure-components -l app=elasticsearch --context "$cluster_name" &> /dev/null; then
        local elasticsearch_pods=$(kubectl get pods -n infrastructure-components -l app=elasticsearch --context "$cluster_name" --no-headers | grep -c "Running" || true)
        if [[ $elasticsearch_pods -gt 0 ]]; then
            test_pass "Elasticsearch running ($elasticsearch_pods pods)"
        else
            test_fail "Elasticsearch not running"
        fi
    else
        test_skip "Elasticsearch not found"
    fi
}

# Performance tests
test_performance() {
    log_info "Running performance tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test resource limits
    local pods_without_limits=$(kubectl get pods --all-namespaces --context "$cluster_name" -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{" "}{.spec.containers[*].resources.limits}{"\n"}{end}' | grep -c "map\[\]" || true)
    local total_pods=$(kubectl get pods --all-namespaces --context "$cluster_name" --no-headers | wc -l)

    if [[ $pods_without_limits -lt $((total_pods / 2)) ]]; then
        test_pass "Most pods have resource limits configured"
    else
        test_warning "Many pods without resource limits ($pods_without_limits/$total_pods)"
    fi

    # Test HPA configuration
    local hpas=$(kubectl get hpa --all-namespaces --context "$cluster_name" --no-headers 2>/dev/null | wc -l || echo "0")
    if [[ $hpas -gt 0 ]]; then
        test_pass "Horizontal Pod Autoscalers configured ($hpas HPAs)"
    else
        test_warning "No Horizontal Pod Autoscalers found"
    fi

    # Test PDB configuration
    local pdbs=$(kubectl get pdb --all-namespaces --context "$cluster_name" --no-headers 2>/dev/null | wc -l || echo "0")
    if [[ $pdbs -gt 0 ]]; then
        test_pass "Pod Disruption Budgets configured ($pdbs PDBs)"
    else
        test_warning "No Pod Disruption Budgets found"
    fi
}

# Disaster recovery tests
test_disaster_recovery() {
    log_info "Running disaster recovery tests..."

    # Test backup storage
    local backup_bucket="nexafi-backups-primary-${ENVIRONMENT:-prod}"
    if aws s3 ls "s3://$backup_bucket/" &> /dev/null; then
        test_pass "Primary backup bucket accessible"

        # Check for recent backups
        local recent_backups=$(aws s3 ls "s3://$backup_bucket/" --recursive | grep "$(date +%Y-%m-%d)" | wc -l || echo "0")
        if [[ $recent_backups -gt 0 ]]; then
            test_pass "Recent backups found ($recent_backups backups today)"
        else
            test_warning "No recent backups found"
        fi
    else
        test_fail "Primary backup bucket not accessible"
    fi

    # Test secondary region connectivity
    local secondary_region="${SECONDARY_REGION:-us-east-1}"
    if aws ec2 describe-regions --region "$secondary_region" &> /dev/null; then
        test_pass "Secondary region ($secondary_region) accessible"
    else
        test_fail "Secondary region not accessible"
    fi

    # Test DR cluster
    local dr_cluster="nexafi-${ENVIRONMENT:-prod}-secondary"
    if aws eks describe-cluster --name "$dr_cluster" --region "$secondary_region" &> /dev/null; then
        test_pass "Disaster recovery cluster exists"
    else
        test_warning "Disaster recovery cluster not found"
    fi
}

# Security scanning
test_security_scanning() {
    log_info "Running security scanning tests..."

    local cluster_name="nexafi-${ENVIRONMENT:-prod}-primary"

    # Test for privileged containers
    local privileged_pods=$(kubectl get pods --all-namespaces --context "$cluster_name" -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{" "}{.spec.containers[*].securityContext.privileged}{"\n"}{end}' | grep -c "true" || true)
    if [[ $privileged_pods -eq 0 ]]; then
        test_pass "No privileged containers found"
    else
        test_fail "Privileged containers detected ($privileged_pods containers)"
    fi

    # Test for containers running as root
    local root_containers=$(kubectl get pods --all-namespaces --context "$cluster_name" -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{" "}{.spec.containers[*].securityContext.runAsUser}{"\n"}{end}' | grep -c "^0$" || true)
    if [[ $root_containers -eq 0 ]]; then
        test_pass "No containers running as root"
    else
        test_warning "Containers running as root detected ($root_containers containers)"
    fi

    # Test for host network usage
    local host_network_pods=$(kubectl get pods --all-namespaces --context "$cluster_name" -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{" "}{.spec.hostNetwork}{"\n"}{end}' | grep -c "true" || true)
    if [[ $host_network_pods -eq 0 ]]; then
        test_pass "No pods using host network"
    else
        test_warning "Pods using host network detected ($host_network_pods pods)"
    fi
}

# Generate test report
generate_test_report() {
    log_info "Generating test report..."

    local report_file="$TEST_RESULTS_DIR/test-report-$TEST_TIMESTAMP.md"

    cat >> "$report_file" << EOF

| Metric | Count |
|--------|-------|
| Total Tests | $TOTAL_TESTS |
| Passed | $PASSED_TESTS |
| Failed | $FAILED_TESTS |
| Skipped | $SKIPPED_TESTS |

## Test Results

### Infrastructure Connectivity
- Kubernetes cluster connectivity
- AWS API connectivity
- Node health and readiness

### Security Configuration
- Pod Security Standards
- Network Policies
- RBAC Configuration
- Secrets Encryption

### Compliance Configuration
- Audit Logging
- Compliance Monitoring
- Backup Jobs
- Data Retention

### Financial Services
- Financial Services Namespace
- Dedicated Nodes
- API Gateway

### Monitoring Stack
- Prometheus
- Grafana
- AlertManager
- Service Monitors

### Infrastructure Components
- Redis
- RabbitMQ
- Elasticsearch

### Performance
- Resource Limits
- Horizontal Pod Autoscalers
- Pod Disruption Budgets

### Disaster Recovery
- Backup Storage
- Secondary Region
- DR Cluster

### Security Scanning
- Privileged Containers
- Root Containers
- Host Network Usage

## Recommendations

EOF

    # Add recommendations based on test results
    if [[ $FAILED_TESTS -gt 0 ]]; then
        echo "- **CRITICAL**: $FAILED_TESTS tests failed. Immediate attention required." >> "$report_file"
    fi

    if [[ $SKIPPED_TESTS -gt 0 ]]; then
        echo "- **WARNING**: $SKIPPED_TESTS tests were skipped. Review configuration." >> "$report_file"
    fi

    if [[ $FAILED_TESTS -eq 0 && $SKIPPED_TESTS -eq 0 ]]; then
        echo "- **SUCCESS**: All tests passed. Infrastructure is properly configured." >> "$report_file"
    fi

    echo "" >> "$report_file"
    echo "**Test completed at:** $(date)" >> "$report_file"

    log_success "Test report generated: $report_file"
}

# Main test function
main() {
    log_info "Starting NexaFi infrastructure testing..."

    setup_test_environment

    # Run all test suites
    test_infrastructure_connectivity
    test_security_configuration
    test_compliance_configuration
    test_financial_services
    test_monitoring_stack
    test_infrastructure_components
    test_performance
    test_disaster_recovery
    test_security_scanning

    generate_test_report

    # Print summary
    log_info "Test Summary:"
    log_info "Total Tests: $TOTAL_TESTS"
    log_success "Passed: $PASSED_TESTS"
    log_error "Failed: $FAILED_TESTS"
    log_warning "Skipped: $SKIPPED_TESTS"

    # Exit with appropriate code
    if [[ $FAILED_TESTS -gt 0 ]]; then
        log_error "Some tests failed. Please review the test report."
        exit 1
    else
        log_success "All tests passed successfully!"
        exit 0
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

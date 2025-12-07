#!/bin/bash

set -euo pipefail

# Comprehensive Testing Script for NexaFi Project
# This script runs all unit, integration, and end-to-end tests for the backend and frontends.

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ALL_TESTS_SUCCESS=true

# --- Backend Testing (Python) ---
run_backend_tests() {
    print_status "Running Backend Python Tests..."
    
    # Check for pytest
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Please install with: pip install pytest"
        ALL_TESTS_SUCCESS=false
        return
    fi

    # Run tests from the root 'tests' directory, focusing on Python tests
    if ! pytest tests/integration tests/unit/shared; then
        print_error "Backend Python tests failed."
        ALL_TESTS_SUCCESS=false
    else
        print_success "Backend Python tests passed."
    fi
}

# --- Frontend Testing (JavaScript/React) ---
run_frontend_tests() {
    print_status "Running Frontend JavaScript/React Tests..."

    # Web Frontend Tests
    if [ -d "web-frontend" ]; then
        print_status "Running Web Frontend Tests..."
        cd web-frontend
        if ! pnpm test; then
            print_error "Web Frontend tests failed."
            ALL_TESTS_SUCCESS=false
        else
            print_success "Web Frontend tests passed."
        fi
        cd ..
    else
        print_warning "web-frontend directory not found. Skipping web frontend tests."
    fi

    # Mobile Frontend Tests
    if [ -d "mobile-frontend" ]; then
        print_status "Running Mobile Frontend Tests..."
        cd mobile-frontend
        if ! pnpm test; then
            print_error "Mobile Frontend tests failed."
            ALL_TESTS_SUCCESS=false
        else
            print_success "Mobile Frontend tests passed."
        fi
        cd ..
    else
        print_warning "mobile-frontend directory not found. Skipping mobile frontend tests."
    fi
}

# --- Main Execution ---
main() {
    echo "🚀 Running Comprehensive NexaFi Test Suite"
    echo "========================================="
    echo ""

    run_backend_tests
    echo ""
    run_frontend_tests
    echo ""

    if $ALL_TESTS_SUCCESS; then
        print_success "All tests passed for the entire project!"
        exit 0
    else
        print_error "Some tests failed. Please review the output above."
        exit 1
    fi
}

main

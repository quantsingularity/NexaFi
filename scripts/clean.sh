#!/bin/bash

set -euo pipefail

# Cleanup Script for NexaFi Project
# This script removes build artifacts, node_modules, virtual environments, and logs.

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

# --- Cleanup Functions ---

# Remove Python virtual environments
clean_python() {
    print_status "Cleaning Python virtual environments (venv)..."
    find . -name "venv" -type d -prune -exec rm -rf {} +
    print_success "Python venvs cleaned."
}

# Remove Node.js dependencies and build folders
clean_frontend() {
    print_status "Cleaning Node.js dependencies (node_modules) and build artifacts..."
    
    # Remove node_modules
    find . -name "node_modules" -type d -prune -exec rm -rf {} +
    
    # Remove frontend build directories
    if [ -d "web-frontend/dist" ]; then
        rm -rf web-frontend/dist
        print_status "Removed web-frontend/dist"
    fi
    if [ -d "mobile-frontend/dist" ]; then
        rm -rf mobile-frontend/dist
        print_status "Removed mobile-frontend/dist"
    fi
    
    print_success "Frontend artifacts cleaned."
}

# Remove log and PID files
clean_logs() {
    print_status "Cleaning log and PID files..."
    if [ -d "backend/logs" ]; then
        rm -rf backend/logs
        print_status "Removed backend/logs"
    fi
    print_success "Logs and PIDs cleaned."
}

# --- Main Execution ---
main() {
    echo "🧹 Running NexaFi Cleanup Script"
    echo "==============================="
    echo ""

    clean_python
    echo ""
    clean_frontend
    echo ""
    clean_logs
    echo ""
    
    print_success "NexaFi project cleanup complete!"
}

main

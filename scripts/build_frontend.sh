#!/bin/bash

set -euo pipefail

# Frontend Build Script for NexaFi Project
# This script builds the production bundles for the web and mobile frontends.

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

# --- Build Functions ---

build_web_frontend() {
    print_status "Building Web Frontend (web-frontend)..."
    if [ -d "web-frontend" ]; then
        cd web-frontend
        if pnpm install && pnpm run build; then
            print_success "Web Frontend build successful. Output in web-frontend/dist"
            cd ..
        else
            print_error "Web Frontend build failed."
            cd ..
            return 1
        fi
    else
        print_error "web-frontend directory not found. Skipping."
        return 1
    fi
}

build_mobile_frontend() {
    print_status "Building Mobile Frontend (mobile-frontend)..."
    if [ -d "mobile-frontend" ]; then
        cd mobile-frontend
        if pnpm install && pnpm run build; then
            print_success "Mobile Frontend build successful. Output in mobile-frontend/dist"
            cd ..
        else
            print_error "Mobile Frontend build failed."
            cd ..
            return 1
        fi
    else
        print_error "mobile-frontend directory not found. Skipping."
        return 1
    fi
}

# --- Main Execution ---
main() {
    echo "🏗️ Running NexaFi Frontend Build Script"
    echo "======================================"
    echo ""

    local BUILD_SUCCESS=true

    if ! build_web_frontend; then
        BUILD_SUCCESS=false
    fi
    echo ""
    if ! build_mobile_frontend; then
        BUILD_SUCCESS=false
    fi
    echo ""

    if $BUILD_SUCCESS; then
        print_success "All frontend builds completed successfully!"
        exit 0
    else
        print_error "One or more frontend builds failed. Please check the logs."
        exit 1
    fi
}

main

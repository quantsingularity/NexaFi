#!/bin/bash

# Comprehensive Linting Script for NexaFi Project
# This script lints all relevant files in the backend, frontend, and infrastructure directories.

set -euo pipefail

# Colors for output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

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

# Global success flag
ALL_LINT_SUCCESS=true

# Lint Python files (Backend)
lint_python() {
    print_status "Linting Python files in code/backend/ with flake8 and black..."

    # Check for flake8
    if ! command -v flake8 &> /dev/null; then
        print_warning "flake8 not found. Attempting to install..."
        pip install flake8 || { print_error "Failed to install flake8. Skipping Python linting."; return; }

    fi

    # Check for black
    if ! command -v black &> /dev/null; then
        print_warning "black not found. Attempting to install..."
        pip install black || { print_error "Failed to install black. Skipping Python formatting check."; return; }

    fi

    # Run flake8
    if ! flake8 code/backend/ --exclude=venv,node_modules --max-line-length=120; then
        print_error "flake8 found issues in code/backend/"
        ALL_LINT_SUCCESS=false
    else
        print_success "flake8 passed for code/backend/"
    fi

    # Run black check (no changes)
    if ! black --check code/backend/; then
        print_error "black found formatting issues in code/backend/. Run 'black code/backend/' to fix."
        ALL_LINT_SUCCESS=false
    else
        print_success "black check passed for code/backend/"
    fi
}

# Lint JavaScript/React files (Frontend)
lint_javascript() {
    print_status "Linting JavaScript/React files in web-frontend/ and mobile-frontend/ with eslint and prettier..."

    # Check for eslint
    if ! command -v eslint &> /dev/null; then
        print_warning "eslint not found. Skipping JavaScript linting. Please ensure it's installed in your project."
        return

    fi

    # Check for prettier
    if ! command -v prettier &> /dev/null; then
        print_warning "prettier not found. Skipping JavaScript formatting check. Please ensure it's installed in your project."
        return

    fi

    # Lint desktop frontend
    if [ -d "web-frontend" ]; then
        print_status "Linting web-frontend/"
        cd web-frontend
        if ! eslint src/ --ext .js,.jsx,.ts,.tsx; then
            print_error "eslint found issues in web-frontend/"
            ALL_LINT_SUCCESS=false
        else
            print_success "eslint passed for web-frontend/"
        fi
        if ! prettier --check src/; then
            print_error "prettier found formatting issues in web-frontend/. Run 'prettier --write src/' to fix."
            ALL_LINT_SUCCESS=false
        else
            print_success "prettier check passed for web-frontend/"
        fi
        cd ..
    else
        print_warning "web-frontend/ directory not found. Skipping."
    fi

    # Lint mobile frontend
    if [ -d "mobile-frontend" ]; then
        print_status "Linting mobile-frontend/"
        cd mobile-frontend
        if ! eslint src/ --ext .js,.jsx,.ts,.tsx; then
            print_error "eslint found issues in mobile-frontend/"
            ALL_LINT_SUCCESS=false
        else
            print_success "eslint passed for mobile-frontend/"
        fi
        if ! prettier --check src/; then
            print_error "prettier found formatting issues in mobile-frontend/. Run 'prettier --write src/' to fix."
            ALL_LINT_SUCCESS=false
        else
            print_success "prettier check passed for mobile-frontend/"
        fi
        cd ..
    else
        print_warning "mobile-frontend/ directory not found. Skipping."
    fi
}

# Lint YAML files (Infrastructure)
lint_yaml() {
    print_status "Linting YAML files in infra/ with yamllint..."

    # Check for yamllint
    if ! command -v yamllint &> /dev/null; then
        print_warning "yamllint not found. Attempting to install..."
        pip install yamllint || { print_error "Failed to install yamllint. Skipping YAML linting."; return; }

    fi

    if [ -d "infra" ]; then
        if ! yamllint -f parsable infra/; then
            print_error "yamllint found issues in infra/"
            ALL_LINT_SUCCESS=false
        else
            print_success "yamllint passed for infra/"
        fi
    else
        print_warning "infra/ directory not found. Skipping."
    fi
}

# Lint Markdown files (Documentation)
lint_markdown() {
    print_status "Linting Markdown files with markdownlint-cli..."

    # Check for markdownlint-cli
    if ! command -v markdownlint &> /dev/null; then
        print_warning "markdownlint-cli not found. Skipping Markdown linting. Please ensure it's installed globally or locally."
        return

    fi

    # Find all markdown files in the project, excluding node_modules and venv
    MARKDOWN_FILES=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./venv/*" -not -path "./code/backend/*/venv/*" -not -path "./web-frontend/node_modules/*" -not -path "./mobile-frontend/node_modules/*")

    if [ -n "$MARKDOWN_FILES" ]; then
        if ! echo "$MARKDOWN_FILES" | xargs markdownlint --config .markdownlint.jsonc; then
            print_error "markdownlint-cli found issues in Markdown files."
            ALL_LINT_SUCCESS=false
        else
            print_success "markdownlint-cli passed for Markdown files."
        fi
    else
        print_warning "No Markdown files found. Skipping."
    fi
}

# Main function to run all linting
main() {
    echo "🚀 Running Comprehensive NexaFi Linting Script"
    echo "==============================================="
    echo ""

    lint_python
    echo ""
    lint_javascript
    echo ""
    lint_yaml
    echo ""
    lint_markdown
    echo ""

    if $ALL_LINT_SUCCESS; then
        print_success "All linting checks passed for the entire project!"
        exit 0
    else
        print_error "Some linting checks failed. Please review the output above."
        exit 1
    fi
}

# Run main function
main

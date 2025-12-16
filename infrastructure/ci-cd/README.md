# CI/CD Workflows

## Workflows Overview

- `cicd.yml` - Main CI/CD pipeline
- `backend_ci.yml` - Backend service CI
- `frontend_ci.yml` - Frontend CI
- `ml_ci_cd.yml` - ML/AI model pipeline
- `security.yml` - Security scanning
- `release.yml` - Release automation
- `docs.yml` - Documentation deployment

## GitHub Actions Secrets Required

### AWS Credentials

- `AWS_ACCESS_KEY_ID` - AWS access key for deployments
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - Default: us-west-2

### Docker Registry

- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token

### Kubernetes

- `KUBE_CONFIG` - Base64 encoded kubeconfig file

### Application Secrets

- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - JWT signing secret
- `API_KEY` - External API keys
- `GRAFANA_API_KEY` - For Grafana annotations

## Local Testing

### Using act (GitHub Actions locally)

```bash
# Install act
# macOS: brew install act
# Linux: see https://github.com/nektos/act

# List workflows
act -l

# Run specific workflow
act -j test

# Run with secrets
act -j test --secret-file .secrets
```

## Validation

```bash
# YAML syntax
yamllint *.yml

# GitHub Actions syntax (using act)
act -n  # dry run

# Check for secrets
grep -r "password\|token\|key" *.yml | grep -v "secrets\."
```

## Adding New Workflows

1. Create `.yml` file in this directory
2. Use existing workflows as templates
3. Always use `${{ secrets.SECRET_NAME }}` for sensitive data
4. Add validation steps (lint, test, security scan)
5. Test locally with `act` before committing

## Workflow Best Practices

1. Use secret scanning to prevent credential leaks
2. Add linting/validation as first steps
3. Use matrix builds for multiple versions/platforms
4. Cache dependencies to speed up builds
5. Use `continue-on-error` sparingly
6. Add proper error handling and notifications

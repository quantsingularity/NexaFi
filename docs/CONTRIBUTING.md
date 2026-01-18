# Contributing to NexaFi

Thank you for your interest in contributing to NexaFi! This guide will help you get started.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and professional
- Follow open source best practices
- Report security issues responsibly
- Help maintain a welcoming community

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/quantsingularity/NexaFi.git
cd NexaFi
```

### 2. Set Up Development Environment

```bash
# Install dependencies
pip install -r backend/requirements.txt
npm install

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

---

## Development Workflow

### Branch Naming

| Type              | Example                        |
| ----------------- | ------------------------------ |
| **Feature**       | `feature/add-credit-scoring`   |
| **Bug Fix**       | `fix/payment-processing-error` |
| **Documentation** | `docs/update-api-reference`    |
| **Performance**   | `perf/optimize-db-queries`     |
| **Refactor**      | `refactor/simplify-auth-logic` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples:**

```
feat(payment): add multi-currency support

Implement support for 135+ currencies with real-time FX rates

Closes #123
```

```
fix(api): resolve rate limiting bug

Rate limiter was not correctly resetting window

Fixes #456
```

---

## Code Standards

### Python

- **Style**: Follow PEP 8
- **Formatter**: Black (line length 100)
- **Linter**: autoflake, pylint
- **Type Hints**: Use type hints for all functions

**Example:**

```python
def calculate_interest(principal: float, rate: float, time: int) -> float:
    """
    Calculate simple interest.

    Args:
        principal: Principal amount
        rate: Interest rate (as decimal)
        time: Time period in years

    Returns:
        Calculated interest
    """
    return principal * rate * time
```

### JavaScript/TypeScript

- **Style**: Airbnb JavaScript Style Guide
- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Safety**: Use TypeScript

**Example:**

```typescript
interface Transaction {
  id: string;
  amount: number;
  currency: string;
}

export const processTransaction = async (
  transaction: Transaction,
): Promise<boolean> => {
  // Implementation
  return true;
};
```

### Documentation

- **API**: OpenAPI/Swagger for REST APIs
- **Code**: Docstrings for all public functions
- **README**: Update relevant READMEs

---

## Testing Requirements

### Test Coverage

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Paths**: 100%

### Test Types

| Type                  | Command                    | When        |
| --------------------- | -------------------------- | ----------- |
| **Unit Tests**        | `pytest tests/unit`        | Always      |
| **Integration Tests** | `pytest tests/integration` | API changes |
| **E2E Tests**         | `npm run test:e2e`         | UI changes  |

### Running Tests

```bash
# Backend tests
cd backend
python test_suite.py

# Frontend tests
cd web-frontend
npm test

# All tests
./scripts/test_all.sh
```

### Writing Tests

**Example unit test:**

```python
import pytest
from mymodule import calculate_interest

def test_calculate_interest():
    """Test interest calculation"""
    result = calculate_interest(1000, 0.05, 2)
    assert result == 100.0

def test_calculate_interest_zero_rate():
    """Test with zero interest rate"""
    result = calculate_interest(1000, 0, 2)
    assert result == 0.0
```

---

## Pull Request Process

### 1. Ensure Quality

- [ ] All tests pass
- [ ] Code is formatted
- [ ] Documentation is updated
- [ ] No linting errors

```bash
# Run checks
./scripts/lint_all.sh
./scripts/test_all.sh
```

### 2. Create Pull Request

- Use descriptive title
- Reference related issues
- Provide detailed description
- Add screenshots if UI changes

**PR Template:**

```markdown
## Description

Brief description of changes

## Related Issues

Closes #123

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots

(if applicable)
```

### 3. Code Review

- Address reviewer feedback
- Keep discussion professional
- Update PR as needed

### 4. Merge

- Squash commits if requested
- Ensure CI/CD passes
- Wait for maintainer approval

---

## Project Structure

```
NexaFi/
├── backend/            # Python microservices
│   ├── api-gateway/    # Entry point
│   ├── *-service/      # Individual services
│   └── shared/         # Shared libraries
├── web-frontend/       # React web app
├── mobile-frontend/    # Flutter mobile app
├── ml/                 # ML models
├── infrastructure/     # K8s, Terraform
├── tests/              # Test suites
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

---

## Updating Documentation

### When to Update Docs

- New features added
- API changes
- Configuration changes
- Breaking changes

### Documentation Files

| File                    | Update When               |
| ----------------------- | ------------------------- |
| `docs/API.md`           | API endpoints change      |
| `docs/CONFIGURATION.md` | New environment variables |
| `docs/INSTALLATION.md`  | Setup steps change        |
| `docs/EXAMPLES/`        | New features added        |

### How to Update

```bash
# Update documentation
vim docs/API.md

# Test locally
# Preview in browser or markdown viewer

# Commit changes
git add docs/
git commit -m "docs: update API reference"
```

---

## Style Guides

### Python

```bash
# Format code
black backend/ --line-length 100

# Remove unused imports
autoflake --remove-all-unused-imports --recursive --in-place backend/

# Check style
pylint backend/
```

### JavaScript/TypeScript

```bash
# Format code
prettier --write "**/*.{js,ts,jsx,tsx,json,css,md}"

# Lint code
eslint . --ext .js,.jsx,.ts,.tsx
```

---

## Community

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bugs and feature requests
- **Security**: security@nexafi.com

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

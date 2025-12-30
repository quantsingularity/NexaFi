# CLI Reference

Command-line interface reference for NexaFi scripts and utilities.

## Table of Contents

1. [Overview](#overview)
2. [Service Management Commands](#service-management-commands)
3. [Development Commands](#development-commands)
4. [Testing Commands](#testing-commands)
5. [Deployment Commands](#deployment-commands)
6. [Utility Scripts](#utility-scripts)

---

## Overview

NexaFi provides several command-line scripts for managing services, running tests, and deployment operations.

**Scripts Location:** `backend/` and `scripts/`

---

## Service Management Commands

### Start All Services

**Command:** `./start_services.sh`

**Description:** Start all backend microservices

| Argument | Description                                    | Example               |
| -------- | ---------------------------------------------- | --------------------- |
| None     | Starts all services with default configuration | `./start_services.sh` |

**Example:**

```bash
cd backend
./start_services.sh
```

**Output:**

```
Starting API Gateway on port 5000...
Starting User Service on port 5001...
Starting Ledger Service on port 5002...
Starting Payment Service on port 5003...
Starting AI Service on port 5004...
All services started successfully!
```

### Stop All Services

**Command:** `./stop_services.sh`

**Description:** Stop all running backend services

**Example:**

```bash
cd backend
./stop_services.sh
```

### Start Individual Service

**Command:** `python3 main.py`

**Description:** Start a single service

| Service         | Directory                     | Command           |
| --------------- | ----------------------------- | ----------------- |
| API Gateway     | `backend/api-gateway/src`     | `python3 main.py` |
| User Service    | `backend/user-service/src`    | `python3 main.py` |
| Auth Service    | `backend/auth-service/src`    | `python3 main.py` |
| Ledger Service  | `backend/ledger-service/src`  | `python3 main.py` |
| Payment Service | `backend/payment-service/src` | `python3 main.py` |
| AI Service      | `backend/ai-service/src`      | `python3 main.py` |

**Example:**

```bash
cd backend/api-gateway/src
python3 main.py

# Output:
#  * Running on http://0.0.0.0:5000
#  * Debug mode: off
```

---

## Development Commands

### Setup Development Environment

**Command:** `./scripts/setup.sh`

**Description:** Initialize development environment with dependencies

**Example:**

```bash
./scripts/setup.sh
```

**Flags:**

| Flag               | Description                        | Example                               |
| ------------------ | ---------------------------------- | ------------------------------------- |
| `--backend-only`   | Install only backend dependencies  | `./scripts/setup.sh --backend-only`   |
| `--frontend-only`  | Install only frontend dependencies | `./scripts/setup.sh --frontend-only`  |
| `--skip-git-hooks` | Skip pre-commit hook installation  | `./scripts/setup.sh --skip-git-hooks` |

### Build Frontend

**Command:** `./scripts/build_frontend.sh`

**Description:** Build web and mobile frontends for production

**Example:**

```bash
./scripts/build_frontend.sh
```

### Lint All Code

**Command:** `./scripts/lint_all.sh`

**Description:** Run linters on all code (Python, JavaScript, TypeScript)

**Example:**

```bash
./scripts/lint_all.sh
```

**Output:**

```
Linting backend Python code...
✓ black formatting passed
✓ autoflake passed
Linting frontend JavaScript/TypeScript...
✓ eslint passed
✓ prettier passed
All linting checks passed!
```

### Clean Build Artifacts

**Command:** `./scripts/clean.sh`

**Description:** Remove build artifacts, caches, and temporary files

**Example:**

```bash
./scripts/clean.sh
```

---

## Testing Commands

### Run All Tests

**Command:** `./scripts/test_all.sh`

**Description:** Execute complete test suite (unit, integration, e2e)

**Example:**

```bash
./scripts/test_all.sh
```

**Output:**

```
Running unit tests...
✓ 150 passed, 0 failed
Running integration tests...
✓ 45 passed, 0 failed
Running e2e tests...
✓ 20 passed, 0 failed
Total: 215 passed, 0 failed
```

### Test Backend Services

**Command:** `python test_all_services.py`

**Description:** Test all backend microservices

**Example:**

```bash
cd backend
python test_all_services.py
```

### Test Imports

**Command:** `python test_imports.py`

**Description:** Verify all Python imports work correctly

**Example:**

```bash
cd backend
python test_imports.py
```

### Run Test Suite

**Command:** `python test_suite.py`

**Description:** Comprehensive backend test suite

**Example:**

```bash
cd backend
python test_suite.py
```

**Options:**

| Flag               | Description              | Example                                       |
| ------------------ | ------------------------ | --------------------------------------------- |
| `--verbose`        | Show detailed output     | `python test_suite.py --verbose`              |
| `--coverage`       | Generate coverage report | `python test_suite.py --coverage`             |
| `--service=<name>` | Test specific service    | `python test_suite.py --service=user-service` |

---

## Deployment Commands

### Setup Infrastructure

**Command:** `./setup_infrastructure.sh`

**Description:** Initialize infrastructure components (databases, Redis, etc.)

**Example:**

```bash
cd backend
./setup_infrastructure.sh
```

**Flags:**

| Flag           | Description              | Example                                  |
| -------------- | ------------------------ | ---------------------------------------- |
| `--docker`     | Use Docker containers    | `./setup_infrastructure.sh --docker`     |
| `--kubernetes` | Deploy to Kubernetes     | `./setup_infrastructure.sh --kubernetes` |
| `--production` | Production configuration | `./setup_infrastructure.sh --production` |

### Deploy to Kubernetes

**Command:** `kubectl apply -f infrastructure/kubernetes/`

**Description:** Deploy NexaFi to Kubernetes cluster

**Example:**

```bash
kubectl apply -f infrastructure/kubernetes/
kubectl get pods -n nexafi
```

### Deploy with Helm

**Command:** `helm install nexafi infrastructure/helm/nexafi`

**Description:** Deploy using Helm charts

**Example:**

```bash
helm install nexafi infrastructure/helm/nexafi \
  --namespace nexafi \
  --create-namespace \
  --values values.yaml
```

---

## Utility Scripts

### Database Migration

**Command:** `alembic upgrade head`

**Description:** Run database migrations

**Example:**

```bash
cd backend/shared/database
alembic upgrade head
```

**Common Alembic Commands:**

| Command                         | Description             | Example                                 |
| ------------------------------- | ----------------------- | --------------------------------------- |
| `alembic upgrade head`          | Apply all migrations    | `alembic upgrade head`                  |
| `alembic downgrade -1`          | Rollback last migration | `alembic downgrade -1`                  |
| `alembic revision -m "message"` | Create new migration    | `alembic revision -m "add users table"` |
| `alembic current`               | Show current migration  | `alembic current`                       |
| `alembic history`               | Show migration history  | `alembic history`                       |

### Health Check

**Command:** `curl http://localhost:5000/health`

**Description:** Check service health status

**Example:**

```bash
# Check API Gateway
curl http://localhost:5000/health

# Check User Service
curl http://localhost:5001/api/v1/health

# Check all services
for port in 5000 5001 5002 5003 5004; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health | jq .
done
```

### View Logs

**Command:** `tail -f logs/nexafi.log`

**Description:** Monitor application logs in real-time

**Example:**

```bash
# View all logs
tail -f backend/logs/nexafi.log

# View specific service logs
tail -f backend/logs/api-gateway.log

# View audit logs
tail -f backend/logs/audit/audit_$(date +%Y-%m-%d).jsonl

# Search logs for errors
grep "ERROR" backend/logs/nexafi.log
```

### Environment Variable Check

**Command:** `printenv | grep NEXAFI`

**Description:** View NexaFi-related environment variables

**Example:**

```bash
printenv | grep NEXAFI
printenv | grep DATABASE_URL
printenv | grep SECRET_KEY
```

---

## Script Reference Table

### Backend Scripts

| Script                    | Location   | Purpose              | Example                       |
| ------------------------- | ---------- | -------------------- | ----------------------------- |
| `start_services.sh`       | `backend/` | Start all services   | `./start_services.sh`         |
| `stop_services.sh`        | `backend/` | Stop all services    | `./stop_services.sh`          |
| `test_all_services.py`    | `backend/` | Test services        | `python test_all_services.py` |
| `test_imports.py`         | `backend/` | Verify imports       | `python test_imports.py`      |
| `test_suite.py`           | `backend/` | Run test suite       | `python test_suite.py`        |
| `setup_infrastructure.sh` | `backend/` | Setup infrastructure | `./setup_infrastructure.sh`   |

### Root Scripts

| Script              | Location   | Purpose               | Example                       |
| ------------------- | ---------- | --------------------- | ----------------------------- |
| `setup.sh`          | `scripts/` | Setup dev environment | `./scripts/setup.sh`          |
| `build_frontend.sh` | `scripts/` | Build frontends       | `./scripts/build_frontend.sh` |
| `lint_all.sh`       | `scripts/` | Lint all code         | `./scripts/lint_all.sh`       |
| `test_all.sh`       | `scripts/` | Run all tests         | `./scripts/test_all.sh`       |
| `clean.sh`          | `scripts/` | Clean artifacts       | `./scripts/clean.sh`          |
| `run.sh`            | `scripts/` | Quick start           | `./scripts/run.sh`            |
| `stop.sh`           | `scripts/` | Stop services         | `./scripts/stop.sh`           |

---

## Environment Variables for CLI

| Variable              | Description           | Example                     |
| --------------------- | --------------------- | --------------------------- |
| `NEXAFI_ENV`          | Environment name      | `development`, `production` |
| `NEXAFI_LOG_LEVEL`    | Log level for scripts | `DEBUG`, `INFO`, `ERROR`    |
| `NEXAFI_BACKEND_DIR`  | Backend directory     | `./backend`                 |
| `NEXAFI_FRONTEND_DIR` | Frontend directory    | `./web-frontend`            |

---

## Best Practices

| Practice                             | Description                           |
| ------------------------------------ | ------------------------------------- |
| **Always check exit codes**          | Use `$?` to verify command success    |
| **Use absolute paths**               | Avoid relative path issues in scripts |
| **Set -e for safety**                | Exit on error in bash scripts         |
| **Log all operations**               | Keep audit trail of CLI operations    |
| **Use environment-specific configs** | Separate dev/staging/prod configs     |

---

## Troubleshooting CLI Issues

| Issue                       | Solution                           |
| --------------------------- | ---------------------------------- |
| **Permission denied**       | `chmod +x script.sh`               |
| **Command not found**       | Add script dir to PATH or use `./` |
| **Service won't start**     | Check logs: `tail -f logs/*.log`   |
| **Port already in use**     | `lsof -ti:5000 \| xargs kill -9`   |
| **Python module not found** | `pip install -r requirements.txt`  |

---

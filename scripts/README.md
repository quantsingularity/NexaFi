# NexaFi Automation Scripts

This document provides a structured and detailed overview of the operational scripts used within the NexaFi project. These scripts are designed to streamline the entire development and deployment lifecycle, covering setup, execution, maintenance, quality assurance, and cleanup. The focus is on providing **automation, consistency, and ease of use** for developers and operators managing the NexaFi platform.

## 1. Scripts Overview

The following table provides a quick reference for all executable scripts located in the `scripts/` directory and their primary function.

| Script              | Category              | Description                                                                                                                                         |
| :------------------ | :-------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| `setup.sh`          | **Setup**             | Installs all necessary system dependencies, sets up virtual environments, and installs project dependencies for a complete development environment. |
| `run.sh`            | **Execution**         | Starts the entire NexaFi application stack, including infrastructure, backend services, and the frontend development server.                        |
| `stop.sh`           | **Execution**         | Gracefully stops all running NexaFi services and infrastructure components.                                                                         |
| `build_frontend.sh` | **Build**             | Creates production-ready, optimized bundles for both the web and mobile frontends.                                                                  |
| `lint_all.sh`       | **Quality Assurance** | Runs a comprehensive, multi-language linting and formatting suite across the entire codebase.                                                       |
| `test_all.sh`       | **Quality Assurance** | Executes all unit, integration, and end-to-end tests for the backend and all frontend applications.                                                 |
| `clean.sh`          | **Maintenance**       | Removes build artifacts, temporary files, virtual environments, and dependencies to clean the workspace.                                            |

## 2. Detailed Script Documentation

### 2.1. `setup.sh` - Environment Initialization

This script is the first step for any new developer or environment. It automates the installation of all external and internal dependencies required to run NexaFi.

**Functionality:**

| Step                      | Target         | Action Performed                                                                                                                                   |
| :------------------------ | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| **System Tools**          | Host OS        | Installs essential tools like `git`, `curl`, `python3-venv`, and the **Docker** engine and Docker Compose plugin.                                  |
| **Backend Setup**         | `backend/*`    | Iterates through all backend services, creates a dedicated Python virtual environment (`venv`), and installs dependencies from `requirements.txt`. |
| **Frontend Setup**        | Global/Local   | Installs the `pnpm` package manager globally (if not present).                                                                                     |
| **Frontend Dependencies** | `web-frontend` | Installs all Node.js dependencies using `pnpm install`.                                                                                            |

**Usage Example:**

```bash
# Run this script from the project root to set up your environment
./scripts/setup.sh
```

### 2.2. `run.sh` and `stop.sh` - Application Lifecycle

These scripts manage the execution of the full NexaFi stack, which is composed of multiple interconnected services.

#### `run.sh` - Start Application

This script orchestrates the startup sequence, ensuring all components are initialized in the correct order.

**Startup Sequence:**

1.  **Infrastructure**: Executes `infrastructure/start-infrastructure.sh` (e.g., databases, message queues).
2.  **Backend Services**: Executes `backend/start_services.sh` (e.g., API gateway, microservices).
3.  **Frontend Server**: Starts the `web-frontend` development server using `pnpm run dev`.

**Usage Example:**

```bash
# Start the entire NexaFi application stack
./scripts/run.sh
```

#### `stop.sh` - Stop Application

This script attempts to gracefully shut down all running components.

**Shutdown Sequence:**

1.  **Backend Services**: Executes `backend/stop_services.sh`.
2.  **Infrastructure Services**: Executes `infrastructure/stop-infrastructure.sh`.

**Usage Example:**

```bash
# Stop all running NexaFi services
./scripts/stop.sh
```

### 2.3. `lint_all.sh` - Code Quality and Security

This script enforces code standards across the entire polyglot codebase, which is essential for maintaining a high-quality, secure financial application.

**Linting and Formatting Tools:**

| Target       | Tool         | Purpose                                                   | Fix Command Hint             |
| :----------- | :----------- | :-------------------------------------------------------- | :--------------------------- |
| **Python**   | Flake8       | Code style and complexity checks.                         | N/A                          |
| **Python**   | Black        | Uncompromising code formatting check.                     | `black <path>`               |
| **Python**   | isort        | Import sorting and organization check.                    | `isort <path>`               |
| **Python**   | Bandit       | Security vulnerability scanning.                          | N/A (Requires manual review) |
| **JS/TS**    | ESLint       | Code quality and bug prevention.                          | `eslint --fix <path>`        |
| **JS/TS**    | Prettier     | Opinionated code formatting check.                        | `prettier --write <path>`    |
| **YAML**     | yamllint     | Validates YAML syntax and style for infrastructure files. | N/A                          |
| **Markdown** | markdownlint | Enforces documentation style and consistency.             | N/A                          |

**Usage Example:**

```bash
# Run the comprehensive linting suite
./scripts/lint_all.sh
```

### 2.4. `test_all.sh` - Comprehensive Testing

This script provides a single command to execute the full test suite, ensuring that all changes maintain the integrity and functionality of the platform.

**Testing Coverage:**

| Component           | Test Type          | Tool        | Directories Tested                       |
| :------------------ | :----------------- | :---------- | :--------------------------------------- |
| **Backend**         | Unit & Integration | `pytest`    | `tests/integration`, `tests/unit/shared` |
| **Web Frontend**    | Unit & Component   | `pnpm test` | `web-frontend` directory                 |
| **Mobile Frontend** | Unit & Component   | `pnpm test` | `mobile-frontend` directory              |

**Usage Example:**

```bash
# Execute all tests across the backend and frontends
./scripts/test_all.sh
```

### 2.5. Maintenance and Build Scripts

#### `build_frontend.sh` - Production Build

This script is used to prepare the frontend assets for production deployment by creating optimized, minified bundles.

**Functionality:**

1.  **Web Frontend**: Runs `pnpm install` and `pnpm run build` in the `web-frontend` directory. Output is expected in `web-frontend/dist`.
2.  **Mobile Frontend**: Runs `pnpm install` and `pnpm run build` in the `mobile-frontend` directory. Output is expected in `mobile-frontend/dist`.

**Usage Example:**

```bash
# Build production assets for both frontends
./scripts/build_frontend.sh
```

#### `clean.sh` - Workspace Cleanup

This script helps maintain a clean workspace by removing generated files and dependencies, which is useful for fresh builds or reducing disk space usage.

**Cleanup Actions:**

| Target              | Action                                                              |
| :------------------ | :------------------------------------------------------------------ |
| **Python**          | Removes all `venv` directories found across the project.            |
| **Node.js**         | Removes all `node_modules` directories.                             |
| **Build Artifacts** | Removes `web-frontend/dist` and `mobile-frontend/dist` directories. |
| **Logs**            | Removes the `backend/logs` directory.                               |

**Usage Example:**

```bash
# Clean the project workspace
./scripts/clean.sh
```

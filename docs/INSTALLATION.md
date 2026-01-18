# Installation Guide

Complete installation guide for NexaFi across different platforms and deployment scenarios.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Installation](#quick-installation)
3. [Installation by Platform](#installation-by-platform)
4. [Docker Installation](#docker-installation)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component            | Minimum                   | Recommended              |
| -------------------- | ------------------------- | ------------------------ |
| **Operating System** | Linux, macOS, Windows 10+ | Ubuntu 20.04+, macOS 12+ |
| **RAM**              | 8 GB                      | 16 GB                    |
| **CPU**              | 2 cores                   | 4+ cores                 |
| **Disk Space**       | 20 GB                     | 50 GB                    |
| **Network**          | Broadband                 | High-speed broadband     |

### Software Prerequisites

| Software           | Version | Required For                          | Installation                           |
| ------------------ | ------- | ------------------------------------- | -------------------------------------- |
| **Python**         | 3.11+   | Backend services                      | [python.org](https://python.org)       |
| **Node.js**        | 18+     | Frontend applications                 | [nodejs.org](https://nodejs.org)       |
| **Docker**         | 20.10+  | Containerization                      | [docker.com](https://docker.com)       |
| **Docker Compose** | 2.0+    | Multi-container orchestration         | Included with Docker Desktop           |
| **Git**            | 2.30+   | Version control                       | [git-scm.com](https://git-scm.com)     |
| **kubectl**        | 1.25+   | Kubernetes deployment (optional)      | [kubernetes.io](https://kubernetes.io) |
| **Helm**           | 3.0+    | Kubernetes package manager (optional) | [helm.sh](https://helm.sh)             |

### Optional Components

| Component         | Purpose                    | Installation                          |
| ----------------- | -------------------------- | ------------------------------------- |
| **Redis**         | Caching and rate limiting  | `apt install redis-server` or Docker  |
| **PostgreSQL**    | Production database        | `apt install postgresql-14` or Docker |
| **Elasticsearch** | Log aggregation and search | Docker recommended                    |

---

## Quick Installation

**For local development (3 steps):**

```bash
# 1. Clone the repository
git clone https://github.com/quantsingularity/NexaFi.git
cd NexaFi

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Start the API Gateway
cd api-gateway/src
python3 main.py
```

**Verify installation:**

```bash
curl http://localhost:5000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": [
    "user-service",
    "ledger-service",
    "payment-service",
    "ai-service"
  ]
}
```

---

## Installation by Platform

### Ubuntu / Debian

```bash
# Update package list
sudo apt update

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Git
sudo apt install git

# Clone NexaFi
git clone https://github.com/quantsingularity/NexaFi.git
cd NexaFi

# Install backend dependencies
cd backend
pip3 install -r requirements.txt

# Install frontend dependencies
cd ../web-frontend
npm install
```

| Step                 | Command                                                    | Notes                           |
| -------------------- | ---------------------------------------------------------- | ------------------------------- |
| **Update system**    | `sudo apt update && sudo apt upgrade`                      | Recommended before installation |
| **Install Python**   | `sudo apt install python3.11 python3-pip`                  | Python 3.11+ required           |
| **Install Node.js**  | Use NodeSource repository                                  | Node 18+ required               |
| **Install Docker**   | Use official Docker script                                 | Add user to docker group        |
| **Clone repository** | `git clone https://github.com/quantsingularity/NexaFi.git` | Requires Git                    |

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install Node.js 18+
brew install node@18

# Install Docker Desktop
brew install --cask docker

# Install Git (usually pre-installed)
brew install git

# Clone NexaFi
git clone https://github.com/quantsingularity/NexaFi.git
cd NexaFi

# Install backend dependencies
cd backend
pip3 install -r requirements.txt

# Install frontend dependencies
cd ../web-frontend
npm install
```

| Step                 | Command                      | Notes                     |
| -------------------- | ---------------------------- | ------------------------- |
| **Install Homebrew** | See command above            | Package manager for macOS |
| **Install Python**   | `brew install python@3.11`   | Use Homebrew Python       |
| **Install Node**     | `brew install node@18`       | Node 18 LTS               |
| **Install Docker**   | `brew install --cask docker` | Docker Desktop for Mac    |

### Windows

```powershell
# Install using Windows Package Manager (winget)

# Install Python 3.11+
winget install Python.Python.3.11

# Install Node.js 18+
winget install OpenJS.NodeJS.LTS

# Install Docker Desktop
winget install Docker.DockerDesktop

# Install Git
winget install Git.Git

# Clone NexaFi (using Git Bash or PowerShell)
git clone https://github.com/quantsingularity/NexaFi.git
cd NexaFi

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ..\web-frontend
npm install
```

| Step                | Tool                             | Notes             |
| ------------------- | -------------------------------- | ----------------- |
| **Install Python**  | `winget` or python.org installer | Add to PATH       |
| **Install Node.js** | `winget` or nodejs.org installer | Includes npm      |
| **Install Docker**  | Docker Desktop                   | Requires WSL2     |
| **Install Git**     | Git for Windows                  | Includes Git Bash |

**Alternative: Using Chocolatey**

```powershell
choco install python nodejs docker-desktop git -y
```

---

## Docker Installation

### Using Docker Compose (Recommended)

**1. Create docker-compose configuration:**

```yaml
# docker-compose.yml
version: "3.8"

services:
  api-gateway:
    build:
      context: ./backend/api-gateway
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres

  user-service:
    build:
      context: ./backend/user-service
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/nexafi

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=nexafi
      - POSTGRES_PASSWORD=nexafi_dev
      - POSTGRES_DB=nexafi
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**2. Start all services:**

```bash
# Set environment variables
export SECRET_KEY="your-secret-key-here"

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**3. Check service health:**

```bash
# Check all containers
docker-compose ps

# Test API Gateway
curl http://localhost:5000/health
```

### Building Individual Containers

```bash
# Build API Gateway
docker build -t nexafi-api-gateway ./backend/api-gateway

# Run API Gateway
docker run -d \
  --name api-gateway \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  nexafi-api-gateway

# Check logs
docker logs -f api-gateway
```

---

## Kubernetes Deployment

### Prerequisites

| Tool               | Version | Purpose           |
| ------------------ | ------- | ----------------- |
| `kubectl`          | 1.25+   | Kubernetes CLI    |
| `helm`             | 3.0+    | Package manager   |
| Kubernetes cluster | 1.25+   | Target deployment |

### Using Helm Charts

**1. Configure values.yaml:**

```yaml
# infrastructure/helm/nexafi/values.yaml
apiGateway:
  replicaCount: 2
  image:
    repository: nexafi/api-gateway
    tag: "2.0.0"
  service:
    type: LoadBalancer
    port: 5000

database:
  enabled: true
  type: postgresql
  replicaCount: 1

redis:
  enabled: true
  replicaCount: 1
```

**2. Install using Helm:**

```bash
# Add NexaFi Helm repository (if available)
helm repo add nexafi https://charts.nexafi.com
helm repo update

# Install NexaFi
helm install nexafi nexafi/nexafi \
  --namespace nexafi \
  --create-namespace \
  --values values.yaml

# Check deployment status
kubectl get pods -n nexafi

# Get service endpoints
kubectl get services -n nexafi
```

### Manual Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployment
kubectl get deployments -n nexafi
kubectl get services -n nexafi
kubectl get pods -n nexafi

# View logs
kubectl logs -f deployment/api-gateway -n nexafi
```

---

## Verification

### Backend Services Health Check

```bash
# Check API Gateway
curl http://localhost:5000/health

# Check individual services
curl http://localhost:5001/api/v1/health  # User Service
curl http://localhost:5002/api/v1/health  # Ledger Service
curl http://localhost:5003/api/v1/health  # Payment Service
curl http://localhost:5004/api/v1/health  # AI Service
```

### Run Test Suite

```bash
# Backend tests
cd backend
python test_imports.py
python test_suite.py

# Frontend tests
cd web-frontend
npm test

# End-to-end tests
cd tests/e2e
npm test
```

### Access Web Dashboard

1. Start the web frontend:

   ```bash
   cd web-frontend
   npm run dev
   ```

2. Open browser: http://localhost:3000

3. Login with demo credentials:
   - Username: `demo@nexafi.com`
   - Password: `SecurePass123!`

---

## Troubleshooting

### Common Installation Issues

| Issue                         | Solution                                                    |
| ----------------------------- | ----------------------------------------------------------- |
| **Port already in use**       | `lsof -ti:5000 \| xargs kill -9` (Mac/Linux) or change port |
| **Python module not found**   | `pip install -r requirements.txt`                           |
| **Docker daemon not running** | Start Docker Desktop or `sudo systemctl start docker`       |
| **Permission denied**         | `sudo usermod -aG docker $USER` then logout/login           |
| **npm install fails**         | `npm cache clean --force && npm install`                    |

### Installation Validation Table

| Component   | Validation Command  | Expected Output           |
| ----------- | ------------------- | ------------------------- |
| **Python**  | `python3 --version` | `Python 3.11.x` or higher |
| **Node.js** | `node --version`    | `v18.x.x` or higher       |
| **Docker**  | `docker --version`  | `Docker version 20.10.x`  |
| **Git**     | `git --version`     | `git version 2.30.x`      |
| **pip**     | `pip3 --version`    | `pip 23.x.x`              |
| **npm**     | `npm --version`     | `9.x.x` or higher         |

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U nexafi -d nexafi -c "SELECT version();"

# Test Redis connection
redis-cli ping

# Check database logs
docker logs postgres-container
```

### Service Start Failures

```bash
# Check Python environment
which python3
python3 -c "import flask; print(flask.__version__)"

# Check required ports
netstat -tuln | grep -E ':(5000|5001|5002|5003|5004|6379|5432)'

# Check logs
tail -f backend/logs/nexafi.log
```

---

## Next Steps

After successful installation:

1. **Configure Environment**: See [CONFIGURATION.md](CONFIGURATION.md)
2. **Start Using NexaFi**: See [USAGE.md](USAGE.md)
3. **Explore Examples**: See [EXAMPLES/](EXAMPLES/)
4. **Read API Docs**: See [API.md](API.md)

---

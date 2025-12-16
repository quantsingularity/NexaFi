# NexaFi Backend - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start the API Gateway

```bash
# Navigate to API Gateway
cd api-gateway/src

# Start the server
python3 main.py
```

The API Gateway will start on `http://localhost:5000`

### Step 3: Test the Installation

```bash
# In another terminal, test the health endpoint
curl http://localhost:5000/health
```

Expected response:

```json
{
  "services": [
    "user-service",
    "ledger-service",
    "payment-service",
    "ai-service"
  ],
  "status": "healthy",
  "timestamp": "2025-12-16T...",
  "version": "2.0.0"
}
```

---

## 🎯 Quick Tests

### Test 1: Simple Server

```bash
python3 test_server.py
```

Access: http://localhost:5000/

### Test 2: API Gateway

```bash
cd api-gateway/src
python3 main.py
```

Access: http://localhost:5000/health

### Test 3: List Services

```bash
curl http://localhost:5000/api/v1/services
```

---

## 📋 Service Ports

| Service         | Port | Status   |
| --------------- | ---- | -------- |
| API Gateway     | 5000 | ✅ Ready |
| User Service    | 5001 | ✅ Ready |
| Ledger Service  | 5002 | ✅ Ready |
| Payment Service | 5003 | ✅ Ready |
| AI Service      | 5004 | ✅ Ready |
| Auth Service    | 5011 | ✅ Ready |

---

## 🔧 Starting Individual Services

### Auth Service

```bash
cd auth-service/src
python3 main.py
```

### User Service

```bash
cd user-service/src
python3 main.py
```

### Payment Service

```bash
cd payment-service/src
python3 main.py
```

---

## 🐛 Troubleshooting

### ImportError: No module named 'xxx'

```bash
# Install missing package
pip install package-name

# Or reinstall requirements
pip install -r requirements_minimal.txt
```

### Port Already in Use

```bash
# Find process using port 5000
lsof -ti:5000

# Kill the process
kill $(lsof -ti:5000)
```

### Permission Denied

```bash
# Make scripts executable
chmod +x start_backend.sh
chmod +x test_server.py
```

---

## 📦 What's Included

```
backend/
├── api-gateway/         # Main API Gateway (Port 5000)
├── auth-service/        # Authentication & OAuth2
├── user-service/        # User management
├── payment-service/     # Payment processing
├── ledger-service/      # Financial ledger
├── ai-service/          # AI/ML features
├── shared/              # Shared modules
│   ├── nexafi_logging/  # Logging utilities
│   ├── middleware/      # Auth & rate limiting
│   ├── database/        # Database manager
│   └── validators/      # Input validation
├── requirements.txt           # Full dependencies
├── requirements_minimal.txt   # Minimal dependencies
├── test_server.py            # Test server
├── start_backend.sh          # Start script
├── CHANGES_SUMMARY.md        # All fixes applied
└── QUICK_START.md            # This file
```

---

## 🌟 Features

- ✅ OAuth 2.1 & OpenID Connect
- ✅ FAPI 2.0 Security
- ✅ Multi-Factor Authentication
- ✅ Circuit Breaker Pattern
- ✅ Rate Limiting
- ✅ Audit Logging
- ✅ Fraud Detection
- ✅ Microservices Architecture

---

## 📖 Next Steps

1. **Configure Environment Variables**

   ```bash
   export SECRET_KEY="your-secret-key"
   export REDIS_HOST="localhost"
   export REDIS_PORT="6379"
   ```

2. **Start Additional Services**
   - Start services on their respective ports
   - Each service has its own `main.py`

3. **Read Full Documentation**
   - See `CHANGES_SUMMARY.md` for all fixes
   - Check `README.md` for architecture details

---

## 🔐 Default Credentials (Demo)

For testing authentication:

- **Username**: demo@nexafi.com
- **Password**: SecurePass123!

⚠️ **Change these in production!**

---

## 💡 Common Commands

```bash
# Install dependencies
pip install -r requirements_minimal.txt

# Start API Gateway
cd api-gateway/src && python3 main.py

# Test health check
curl http://localhost:5000/health

# View logs
tail -f logs/nexafi.log

# Stop all services
pkill -f "python3 main.py"
```

---

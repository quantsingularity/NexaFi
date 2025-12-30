# Troubleshooting Guide

Common issues and solutions for NexaFi platform.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Runtime Issues](#runtime-issues)
3. [API Issues](#api-issues)
4. [Database Issues](#database-issues)
5. [Performance Issues](#performance-issues)

---

## Installation Issues

### Python Dependency Errors

**Issue:** `pip install` fails with dependency conflicts

**Solution:**

```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Port Already in Use

**Issue:** `Address already in use` error

**Solution:**

```bash
# Find process using port
lsof -ti:5000

# Kill the process
kill $(lsof -ti:5000)

# Or change port in configuration
export PORT=5001
```

### Docker Issues

**Issue:** Docker daemon not running

**Solution:**

```bash
# Start Docker Desktop (Mac/Windows)
# Or on Linux:
sudo systemctl start docker

# Verify
docker ps
```

---

## Runtime Issues

### Service Won't Start

**Issue:** Service fails to start

**Symptoms:**

- Import errors
- Connection refused
- Permission denied

**Solutions:**

| Symptom                | Solution                                              |
| ---------------------- | ----------------------------------------------------- |
| **ImportError**        | `pip install -r requirements.txt`                     |
| **Connection refused** | Check if dependencies (Redis, PostgreSQL) are running |
| **Permission denied**  | `chmod +x script.sh` or run with `sudo`               |
| **Port conflict**      | Change port or kill conflicting process               |

### Authentication Failures

**Issue:** 401 Unauthorized errors

**Symptoms:**

- Login fails
- Token expired
- Invalid credentials

**Solutions:**

```bash
# Check SECRET_KEY is set
echo $SECRET_KEY

# Generate new token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'

# Check token expiry
# Tokens expire after 1 hour by default
```

### Rate Limiting

**Issue:** 429 Too Many Requests

**Solution:**

```bash
# Wait for rate limit window to reset
# Check rate limit headers:
# X-RateLimit-Reset: 1704024000

# Or disable rate limiting for development
export RATE_LIMIT_ENABLED=false
```

---

## API Issues

### 404 Not Found

**Issue:** Endpoint returns 404

**Checklist:**

- [ ] Service is running: `curl http://localhost:5000/health`
- [ ] Correct base URL: `/api/v1/...`
- [ ] Endpoint exists: Check [API.md](API.md)
- [ ] API Gateway routes to service

### 500 Internal Server Error

**Issue:** Server error

**Debug Steps:**

```bash
# Check service logs
tail -f backend/logs/nexafi.log

# Check specific service
tail -f backend/logs/api-gateway.log

# Enable debug mode (development only)
export DEBUG=true
```

### Slow API Response

**Issue:** API calls are slow

**Solutions:**

| Cause                   | Solution                          |
| ----------------------- | --------------------------------- |
| **Database query slow** | Check indexes, optimize queries   |
| **No caching**          | Enable Redis caching              |
| **Large payload**       | Use pagination, compress response |
| **Network latency**     | Check network, use CDN            |

---

## Database Issues

### Connection Failed

**Issue:** Cannot connect to database

**Solutions:**

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U nexafi -d nexafi

# Check DATABASE_URL
echo $DATABASE_URL

# Restart database
sudo systemctl restart postgresql
```

### Migration Errors

**Issue:** Database migration fails

**Solutions:**

```bash
# Check current migration state
alembic current

# Rollback last migration
alembic downgrade -1

# Re-run migration
alembic upgrade head

# Force migration (DANGEROUS)
alembic stamp head
```

### Lock Timeout

**Issue:** Database lock timeout

**Solution:**

```sql
-- Find blocking queries
SELECT pid, query, state
FROM pg_stat_activity
WHERE state = 'active';

-- Kill blocking query
SELECT pg_terminate_backend(pid);
```

---

## Performance Issues

### High Memory Usage

**Issue:** Service consuming too much memory

**Solutions:**

```bash
# Check memory usage
docker stats

# Restart service
./scripts/stop.sh
./scripts/run.sh

# Reduce workers/threads in config
export WORKERS=2
```

### CPU Spikes

**Issue:** High CPU usage

**Debugging:**

```bash
# Profile Python code
python -m cProfile -o profile.stats backend/api-gateway/src/main.py

# Analyze profile
python -m pstats profile.stats

# Check for infinite loops
# Check database N+1 queries
# Optimize ML model inference
```

### Disk Space Issues

**Issue:** Running out of disk space

**Solutions:**

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Clean logs
find backend/logs -name "*.log" -mtime +7 -delete

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
```

---

## Common Error Messages

| Error                   | Cause                    | Solution                         |
| ----------------------- | ------------------------ | -------------------------------- |
| **ModuleNotFoundError** | Missing Python package   | `pip install <package>`          |
| **EADDRINUSE**          | Port already in use      | Kill process or change port      |
| **ECONNREFUSED**        | Service not running      | Start the service                |
| **JWT expired**         | Token expired            | Get new token via login          |
| **Permission denied**   | Insufficient permissions | Check file/directory permissions |
| **Database locked**     | SQLite concurrent access | Use PostgreSQL in production     |
| **Memory error**        | Insufficient RAM         | Increase memory or optimize code |

---

## Getting Help

If you can't resolve the issue:

1. **Search GitHub Issues**: https://github.com/abrar2030/NexaFi/issues
2. **Check Logs**: `backend/logs/` directory
3. **Enable Debug Mode**: `export DEBUG=true`
4. **Create Issue**: Provide logs, steps to reproduce, environment details

**Issue Template:**

```markdown
## Description

Brief description of the issue

## Environment

- OS: Ubuntu 22.04
- Python: 3.11.0
- Node: 18.16.0
- Docker: 24.0.0

## Steps to Reproduce

1. Start service
2. Call API
3. See error

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Logs
```

Paste relevant logs here

```

## Screenshots
(if applicable)
```

---

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_transactions_date ON transactions(created_at);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Analyze tables
ANALYZE transactions;
```

### Redis Configuration

```bash
# Increase memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Enable AOF persistence
appendonly yes
```

### API Gateway

```python
# Increase timeouts
TIMEOUT = 60

# Increase worker processes
WORKERS = 4
```

---

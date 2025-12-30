# Configuration Guide

Complete configuration reference for NexaFi services, environment variables, and deployment settings.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Service Configuration](#service-configuration)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Monitoring & Logging](#monitoring--logging)
6. [Advanced Configuration](#advanced-configuration)

---

## Environment Variables

### Core Environment Variables

| Variable      | Type    | Default       | Required | Description                                         |
| ------------- | ------- | ------------- | -------- | --------------------------------------------------- |
| `SECRET_KEY`  | string  | -             | ✅       | Application secret key for JWT signing              |
| `ENVIRONMENT` | string  | `development` | ❌       | Environment: `development`, `staging`, `production` |
| `DEBUG`       | boolean | `false`       | ❌       | Enable debug mode (DO NOT use in production)        |
| `LOG_LEVEL`   | string  | `INFO`        | ❌       | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`  |
| `API_VERSION` | string  | `v1`          | ❌       | API version prefix                                  |

### Database Configuration

| Variable          | Type    | Default                    | Required | Description                           |
| ----------------- | ------- | -------------------------- | -------- | ------------------------------------- |
| `DATABASE_URL`    | string  | `sqlite:///data/nexafi.db` | ❌       | Database connection string            |
| `DB_POOL_SIZE`    | integer | `10`                       | ❌       | Database connection pool size         |
| `DB_MAX_OVERFLOW` | integer | `20`                       | ❌       | Maximum database overflow connections |
| `DB_ECHO`         | boolean | `false`                    | ❌       | Echo SQL queries (debug only)         |

**PostgreSQL Example:**

```bash
DATABASE_URL="postgresql://user:password@localhost:5432/nexafi"
```

**MySQL Example:**

```bash
DATABASE_URL="mysql://user:password@localhost:3306/nexafi"
```

### Redis Configuration

| Variable         | Type    | Default                  | Required | Description                     |
| ---------------- | ------- | ------------------------ | -------- | ------------------------------- |
| `REDIS_URL`      | string  | `redis://localhost:6379` | ❌       | Redis connection URL            |
| `REDIS_HOST`     | string  | `localhost`              | ❌       | Redis server host               |
| `REDIS_PORT`     | integer | `6379`                   | ❌       | Redis server port               |
| `REDIS_DB`       | integer | `0`                      | ❌       | Redis database number           |
| `REDIS_PASSWORD` | string  | -                        | ❌       | Redis authentication password   |
| `REDIS_SSL`      | boolean | `false`                  | ❌       | Enable SSL for Redis connection |

### Authentication Configuration

| Variable                    | Type    | Default              | Required | Description                               |
| --------------------------- | ------- | -------------------- | -------- | ----------------------------------------- |
| `JWT_SECRET_KEY`            | string  | Same as `SECRET_KEY` | ❌       | JWT signing secret                        |
| `JWT_ACCESS_TOKEN_EXPIRES`  | integer | `3600`               | ❌       | Access token lifetime (seconds)           |
| `JWT_REFRESH_TOKEN_EXPIRES` | integer | `2592000`            | ❌       | Refresh token lifetime (seconds, 30 days) |
| `JWT_ALGORITHM`             | string  | `HS256`              | ❌       | JWT signing algorithm                     |
| `PASSWORD_MIN_LENGTH`       | integer | `8`                  | ❌       | Minimum password length                   |
| `MFA_ENABLED`               | boolean | `false`              | ❌       | Enable multi-factor authentication        |
| `SESSION_TIMEOUT`           | integer | `1800`               | ❌       | Session timeout (seconds)                 |

### Payment Processing Configuration

| Variable                 | Type    | Default | Required   | Description                           |
| ------------------------ | ------- | ------- | ---------- | ------------------------------------- |
| `STRIPE_SECRET_KEY`      | string  | -       | Production | Stripe API secret key                 |
| `STRIPE_PUBLISHABLE_KEY` | string  | -       | Production | Stripe publishable key                |
| `PAYMENT_WEBHOOK_SECRET` | string  | -       | Production | Webhook signing secret                |
| `CURRENCY_DEFAULT`       | string  | `USD`   | ❌         | Default currency code                 |
| `TRANSACTION_TIMEOUT`    | integer | `300`   | ❌         | Payment transaction timeout (seconds) |

### Email/Notification Configuration

| Variable        | Type    | Default              | Required   | Description                  |
| --------------- | ------- | -------------------- | ---------- | ---------------------------- |
| `SMTP_HOST`     | string  | -                    | Production | SMTP server hostname         |
| `SMTP_PORT`     | integer | `587`                | ❌         | SMTP server port             |
| `SMTP_USERNAME` | string  | -                    | Production | SMTP authentication username |
| `SMTP_PASSWORD` | string  | -                    | Production | SMTP authentication password |
| `SMTP_USE_TLS`  | boolean | `true`               | ❌         | Enable TLS for SMTP          |
| `EMAIL_FROM`    | string  | `noreply@nexafi.com` | ❌         | Default sender email address |

### AI/ML Configuration

| Variable               | Type    | Default       | Required | Description                     |
| ---------------------- | ------- | ------------- | -------- | ------------------------------- |
| `ML_MODEL_PATH`        | string  | `./ml/models` | ❌       | Path to ML model files          |
| `ML_INFERENCE_TIMEOUT` | integer | `30`          | ❌       | ML inference timeout (seconds)  |
| `ML_BATCH_SIZE`        | integer | `32`          | ❌       | Batch size for ML predictions   |
| `OPENAI_API_KEY`       | string  | -             | Optional | OpenAI API key for LLM features |
| `ML_CACHE_ENABLED`     | boolean | `true`        | ❌       | Enable ML prediction caching    |

### Rate Limiting Configuration

| Variable                 | Type    | Default           | Required | Description                          |
| ------------------------ | ------- | ----------------- | -------- | ------------------------------------ |
| `RATE_LIMIT_ENABLED`     | boolean | `true`            | ❌       | Enable rate limiting                 |
| `RATE_LIMIT_AUTH`        | string  | `5 per 5 minutes` | ❌       | Rate limit for auth endpoints        |
| `RATE_LIMIT_API`         | string  | `1000 per minute` | ❌       | Rate limit for API endpoints         |
| `RATE_LIMIT_TRANSACTION` | string  | `100 per minute`  | ❌       | Rate limit for transaction endpoints |

---

## Service Configuration

### API Gateway Configuration

**File:** `backend/api-gateway/config.py`

```python
# API Gateway Configuration
API_GATEWAY_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "services": {
        "user-service": {
            "url": "http://localhost:5001",
            "timeout": 30,
            "retry_count": 3
        },
        "ledger-service": {
            "url": "http://localhost:5002",
            "timeout": 30,
            "retry_count": 3
        },
        "payment-service": {
            "url": "http://localhost:5003",
            "timeout": 30,
            "retry_count": 3
        },
        "ai-service": {
            "url": "http://localhost:5004",
            "timeout": 60,
            "retry_count": 2
        }
    },
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60
    }
}
```

### Service Ports

| Service                  | Port | Protocol | Public | Description         |
| ------------------------ | ---- | -------- | ------ | ------------------- |
| **API Gateway**          | 5000 | HTTP     | ✅     | Main entry point    |
| **User Service**         | 5001 | HTTP     | ❌     | User management     |
| **Ledger Service**       | 5002 | HTTP     | ❌     | Accounting ledger   |
| **Payment Service**      | 5003 | HTTP     | ❌     | Payment processing  |
| **AI Service**           | 5004 | HTTP     | ❌     | ML predictions      |
| **Compliance Service**   | 5005 | HTTP     | ❌     | AML/KYC checks      |
| **Notification Service** | 5006 | HTTP     | ❌     | Notifications       |
| **Auth Service**         | 5011 | HTTP     | ❌     | Authentication      |
| **Analytics Service**    | 5007 | HTTP     | ❌     | Business analytics  |
| **Credit Service**       | 5008 | HTTP     | ❌     | Credit scoring      |
| **Document Service**     | 5009 | HTTP     | ❌     | Document processing |
| **Open Banking Gateway** | 5010 | HTTP     | ❌     | Bank integrations   |

---

## Database Configuration

### SQLite (Development)

**Default configuration:**

```bash
DATABASE_URL="sqlite:///data/nexafi.db"
```

**Configuration file:** `backend/shared/database/config.py`

```python
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///data/nexafi.db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True
}
```

### PostgreSQL (Production)

**Connection string:**

```bash
DATABASE_URL="postgresql://nexafi_user:strong_password@localhost:5432/nexafi_production"
```

**Advanced configuration:**

```python
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10
    }
}
```

**PostgreSQL-specific settings:**

| Setting                        | Value   | Description                       |
| ------------------------------ | ------- | --------------------------------- |
| `shared_buffers`               | `256MB` | Memory for caching                |
| `effective_cache_size`         | `1GB`   | Estimated cache memory            |
| `maintenance_work_mem`         | `64MB`  | Memory for maintenance operations |
| `checkpoint_completion_target` | `0.9`   | Checkpoint completion timing      |
| `wal_buffers`                  | `16MB`  | Write-ahead log buffers           |
| `default_statistics_target`    | `100`   | Query planner statistics          |
| `max_connections`              | `100`   | Maximum database connections      |

### Database Migrations

**Using Alembic:**

```bash
# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Security Configuration

### SSL/TLS Configuration

**For production deployment:**

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name api.nexafi.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### CORS Configuration

```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-User-ID"]
```

### Security Headers

| Header                      | Value                                 | Purpose                    |
| --------------------------- | ------------------------------------- | -------------------------- |
| `X-Content-Type-Options`    | `nosniff`                             | Prevent MIME type sniffing |
| `X-Frame-Options`           | `DENY`                                | Prevent clickjacking       |
| `X-XSS-Protection`          | `1; mode=block`                       | Enable XSS protection      |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforce HTTPS              |
| `Content-Security-Policy`   | `default-src 'self'`                  | Restrict content sources   |

---

## Monitoring & Logging

### Logging Configuration

**Log levels:**

- `DEBUG`: Detailed debug information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

**Configuration:**

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/nexafi.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "nexafi": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}
```

### Audit Logging

**Environment variables:**

| Variable            | Type    | Default      | Description                  |
| ------------------- | ------- | ------------ | ---------------------------- |
| `AUDIT_LOG_ENABLED` | boolean | `true`       | Enable audit logging         |
| `AUDIT_LOG_PATH`    | string  | `logs/audit` | Audit log directory          |
| `AUDIT_LOG_FORMAT`  | string  | `json`       | Log format: `json` or `text` |

**Audit log configuration:**

```python
AUDIT_CONFIG = {
    "enabled": True,
    "log_path": "logs/audit",
    "format": "json",
    "integrity_check": True,
    "retention_days": 365
}
```

---

## Advanced Configuration

### Docker Compose Configuration

**File:** `docker-compose.yml`

```yaml
version: "3.8"

services:
  api-gateway:
    build: ./backend/api-gateway
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### Kubernetes Configuration

**Deployment manifest:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: nexafi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
        - name: api-gateway
          image: nexafi/api-gateway:2.0.0
          ports:
            - containerPort: 5000
          env:
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: nexafi-secrets
                  key: secret-key
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: nexafi-secrets
                  key: database-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Environment-Specific Configuration

**.env.development:**

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///data/nexafi_dev.db
REDIS_URL=redis://localhost:6379
SECRET_KEY=dev-secret-key-change-in-production
```

**.env.staging:**

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/nexafi_staging
REDIS_URL=redis://staging-redis:6379
SECRET_KEY=${STAGING_SECRET_KEY}
```

**.env.production:**

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db:5432/nexafi_production
REDIS_URL=redis://prod-redis:6379
SECRET_KEY=${PRODUCTION_SECRET_KEY}
SENTRY_DSN=${SENTRY_DSN}
```

---

## Configuration Best Practices

| Practice                              | Description                     | Example                               |
| ------------------------------------- | ------------------------------- | ------------------------------------- |
| **Use environment variables**         | Never hardcode secrets          | `os.getenv('SECRET_KEY')`             |
| **Separate configs by environment**   | Different settings for dev/prod | `.env.development`, `.env.production` |
| **Validate configuration on startup** | Fail fast if misconfigured      | Check required vars at startup        |
| **Use secret management**             | Store secrets securely          | HashiCorp Vault, AWS Secrets Manager  |
| **Document all variables**            | Make configuration discoverable | This document!                        |
| **Version configuration**             | Track changes to settings       | Git version control                   |

---

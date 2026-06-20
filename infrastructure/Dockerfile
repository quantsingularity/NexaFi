# NexaFi Service Dockerfile Template
# Copy this file into each service directory and adjust SERVICE_PORT and SERVICE_NAME.
# Usage: cp Dockerfile services/<service-name>/Dockerfile

ARG PYTHON_VERSION=3.11

# ─── Build stage ─────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies in isolation
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

# Metadata
LABEL org.opencontainers.image.source="https://github.com/nexafi/nexafi" \
      org.opencontainers.image.vendor="NexaFi" \
      org.opencontainers.image.licenses="Proprietary"

# Runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appgroup . .

# Ensure data/temp directories exist with correct ownership
RUN mkdir -p /app/data /app/temp /app/logs && \
    chown -R appuser:appgroup /app

USER appuser

# Override in each service's Dockerfile
ARG SERVICE_PORT=5000
ENV SERVICE_PORT=${SERVICE_PORT} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE ${SERVICE_PORT}

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f "http://localhost:${SERVICE_PORT}/api/v1/health" || exit 1

# Shell form so ${SERVICE_PORT} is expanded at runtime. Exec (JSON array) form
# does not perform environment-variable substitution, which would make gunicorn
# try to bind the literal string "0.0.0.0:${SERVICE_PORT}".
# PYTHONPATH includes /app, so the Flask app in src/main.py is "src.main:app".
CMD gunicorn \
    --bind "0.0.0.0:${SERVICE_PORT}" \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    src.main:app

# Multi-stage Dockerfile for NexaFi ML Models
# Optimized for production deployment with security and performance

# Build stage
FROM python:3.11-slim as builder

# Build arguments
ARG MODEL_NAME
ARG BUILD_DATE
ARG VCS_REF

# Set labels for metadata
LABEL org.opencontainers.image.title="NexaFi ML Model: ${MODEL_NAME}" \
      org.opencontainers.image.description="Enterprise ML model serving for financial services" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="NexaFi" \
      org.opencontainers.image.source="https://github.com/nexafi/ml-models"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY ml/requirements.txt /tmp/requirements.txt
COPY ml/requirements-prod.txt /tmp/requirements-prod.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements-prod.txt

# Production stage
FROM python:3.11-slim as production

# Build arguments
ARG MODEL_NAME
ARG BUILD_DATE
ARG VCS_REF

# Set labels
LABEL org.opencontainers.image.title="NexaFi ML Model: ${MODEL_NAME}" \
      org.opencontainers.image.description="Enterprise ML model serving for financial services" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="NexaFi"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r nexafi && useradd -r -g nexafi -u 1001 nexafi

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY ml/pipelines/model_server.py /app/
COPY ml/pipelines/mlops_pipeline.py /app/
COPY ml/shared/ /app/shared/
COPY ml/models/${MODEL_NAME}/ /app/model/

# Copy configuration files
COPY ml/config/ /app/config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models && \
    chown -R nexafi:nexafi /app

# Set environment variables
ENV MODEL_NAME=${MODEL_NAME} \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    WORKERS=4 \
    TIMEOUT=300 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Security: Run as non-root user
USER nexafi

# Expose port
EXPOSE ${PORT}

# Start command with gunicorn for production
CMD ["sh", "-c", "gunicorn --bind ${HOST}:${PORT} --workers ${WORKERS} --timeout ${TIMEOUT} --max-requests ${MAX_REQUESTS} --max-requests-jitter ${MAX_REQUESTS_JITTER} --worker-class sync --worker-connections 1000 --preload --access-logfile - --error-logfile - --log-level ${LOG_LEVEL} model_server:app"]

# Alternative development command (can be overridden)
# CMD ["python", "model_server.py"]

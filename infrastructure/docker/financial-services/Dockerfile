# Multi-stage Dockerfile for NexaFi financial services
# Optimized for security, performance, and compliance

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./
COPY yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile --production=false

# Copy source code
COPY . .

# Build application
RUN yarn build

# Remove development dependencies
RUN yarn install --frozen-lockfile --production=true && yarn cache clean

# Production stage
FROM node:18-alpine AS production

# Create non-root user
RUN addgroup -g 1001 -S nexafi && \
    adduser -S nexafi -u 1001 -G nexafi

# Install security updates and required packages
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
    dumb-init \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=nexafi:nexafi /app/dist ./dist
COPY --from=builder --chown=nexafi:nexafi /app/node_modules ./node_modules
COPY --from=builder --chown=nexafi:nexafi /app/package.json ./package.json

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R nexafi:nexafi /app

# Security hardening
RUN chmod -R 755 /app && \
    chmod -R 644 /app/dist && \
    chmod 755 /app/dist/server.js

# Switch to non-root user
USER nexafi

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["node", "dist/server.js"]

# Metadata
LABEL maintainer="NexaFi DevOps <devops@nexafi.com>"
LABEL version="1.0.0"
LABEL description="NexaFi Financial Services Application"
LABEL org.opencontainers.image.title="NexaFi Financial Services"
LABEL org.opencontainers.image.description="Secure financial services application"
LABEL org.opencontainers.image.vendor="NexaFi"
LABEL org.opencontainers.image.licenses="Proprietary"
LABEL org.opencontainers.image.source="https://github.com/nexafi/financial-services"

#!/bin/bash

# Includes new services and improved error handling

set -e

echo "Starting NexaFi Backend Services ..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_dir=$3

    echo -e "${YELLOW}Starting $service_name on port $port...${NC}"

    if ! check_port $port; then
        echo -e "${RED}Cannot start $service_name - port $port is in use${NC}"
        return 1
    fi

    # Launch inside a subshell so the working directory is NOT changed for the
    # caller. Previously this function ran a bare "cd", so after the first
    # service every later "[ -d $service_dir ]" check ran from inside that
    # service's directory and failed ("directory not found"). The PID is written
    # to a file because $! from a subshell is not visible to the parent.
    (
        cd "$service_dir" || exit 1
        export SERVICE_NAME="$service_name"
        export SERVICE_PORT="$port"
        export PORT="$port"
        # shared is one level up from the service directory.
        export PYTHONPATH="${PYTHONPATH}:$(pwd)/../shared"
        nohup python3 src/main.py > "../logs/${service_name}.log" 2>&1 &
        echo $! > "../logs/${service_name}.pid"
    )

    # Wait a moment and check if service started successfully
    sleep 2
    local pid
    pid="$(cat "logs/${service_name}.pid" 2>/dev/null)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}$service_name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}Failed to start $service_name${NC}"
        echo -e "${RED}--- last lines of logs/${service_name}.log ---${NC}"
        tail -n 15 "logs/${service_name}.log" 2>/dev/null
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/api/v1/health" >/dev/null 2>&1; then
            echo -e "${GREEN}$service_name is ready${NC}"
            return 0
        fi

        echo "Attempt $attempt/$max_attempts - waiting for $service_name..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}$service_name failed to become ready${NC}"
    echo -e "${RED}--- last lines of logs/${service_name}.log ---${NC}"
    tail -n 20 "logs/${service_name}.log" 2>/dev/null
    return 1
}

# Create logs directory
mkdir -p logs

# Start Redis (if available) for rate limiting and caching
if command -v redis-server >/dev/null 2>&1; then
    if ! pgrep redis-server >/dev/null; then
        echo -e "${YELLOW}Starting Redis server...${NC}"
        redis-server --daemonize yes --port 6379 >/dev/null 2>&1 || {
            echo -e "${YELLOW}Warning: Could not start Redis. Rate limiting and caching will use fallback methods.${NC}"
        }
    else
        echo -e "${GREEN}Redis is already running${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Redis not found. Rate limiting and caching will use fallback methods.${NC}"
fi

# Required service configuration. The services exit at startup if SECRET_KEY or
# DATABASE_URL is missing. Defaults are provided here so the stack runs without
# a .env; anything already exported in your shell takes precedence.
export SECRET_KEY="${SECRET_KEY:-nexafi-local-dev-secret-change-me}"
# DEBUG=false disables the Flask reloader. On the Windows filesystem under WSL
# (/mnt/c) the reloader's file watcher stalls, which leaves the process alive
# but never serving (the "started but failed to become ready" symptom).
export DEBUG="${DEBUG:-false}"
# Put the dev SQLite database on the fast Linux-side filesystem rather than
# /mnt/c, where SQLite locking over the 9p mount is slow and flaky. All services
# share one file so they see the same users table. Override DATABASE_URL to use
# Postgres or another location.
mkdir -p /tmp/nexafi-data
export DATABASE_URL="${DATABASE_URL:-sqlite:////tmp/nexafi-data/nexafi.db}"

# When running locally (not in Docker), the gateway must reach the other
# services on localhost. Without these, it falls back to the Docker service
# hostnames (e.g. http://user-service:5001), which do not resolve on the host
# and cause "Temporary failure in name resolution" and 503s.
export USER_SERVICE_URL="${USER_SERVICE_URL:-http://localhost:5001}"
export LEDGER_SERVICE_URL="${LEDGER_SERVICE_URL:-http://localhost:5002}"
export PAYMENT_SERVICE_URL="${PAYMENT_SERVICE_URL:-http://localhost:5003}"
export AI_SERVICE_URL="${AI_SERVICE_URL:-http://localhost:5004}"
export COMPLIANCE_SERVICE_URL="${COMPLIANCE_SERVICE_URL:-http://localhost:5005}"
export NOTIFICATION_SERVICE_URL="${NOTIFICATION_SERVICE_URL:-http://localhost:5007}"

# Array of services to start
declare -a services=(
    "user-service:5001"
    "ledger-service:5002"
    "payment-service:5003"
    "ai-service:5004"
    "compliance-service:5005"
    "notification-service:5007"
    "api-gateway:5000"  # Start gateway last
)

# Start each service
failed_services=()
for service_info in "${services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    service_dir="$service_name"

    if [ -d "$service_dir" ]; then
        if start_service "$service_name" "$port" "$service_dir"; then
            # Wait for service to be ready (except for API gateway)
            if [ "$service_name" != "api-gateway" ]; then
                if ! wait_for_service "$service_name" "$port"; then
                    failed_services+=("$service_name")
                fi
            fi
        else
            failed_services+=("$service_name")
        fi
    else
        echo -e "${YELLOW}Warning: $service_dir directory not found, skipping $service_name${NC}"
    fi
done

# Special handling for API Gateway - wait for it to be ready
if [ -d "api-gateway" ]; then
    echo "Waiting for API Gateway to be ready..."
    if wait_for_service "api-gateway" "5000"; then
        echo -e "${GREEN}API Gateway is ready and routing requests${NC}"
    else
        failed_services+=("api-gateway")
    fi
fi

# Summary
echo ""
echo "=== NexaFi Backend Startup Summary ==="

if [ ${#failed_services[@]} -eq 0 ]; then
    echo -e "${GREEN}All services started successfully!${NC}"
    echo ""
    echo "Service URLs:"
    echo "  API Gateway:         http://localhost:5000"
    echo "  User Service:        http://localhost:5001"
    echo "  Ledger Service:      http://localhost:5002"
    echo "  Payment Service:     http://localhost:5003"
    echo "  AI Service:          http://localhost:5004"
    echo "  Compliance Service:  http://localhost:5005"
    echo "  Notification Service: http://localhost:5007"
    echo ""
    echo "Health Check: curl http://localhost:5000/health"
    echo "Service List: curl http://localhost:5000/api/v1/services"
    echo ""
    echo "Logs are available in the logs/ directory"
    echo "To stop all services, run: ./stop_services.sh"
else
    echo -e "${RED}Some services failed to start:${NC}"
    for service in "${failed_services[@]}"; do
        echo -e "  ${RED}- $service${NC}"
    done
    echo ""
    echo "Check the logs in the logs/ directory for more details"
    exit 1
fi

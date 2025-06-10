#!/bin/bash

# NexaFi Backend Services Startup Script
# This script starts all microservices in the correct order

echo "🚀 Starting NexaFi Backend Services..."
echo "======================================"

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_dir="/home/ubuntu/NexaFi/backend/$service_name"
    
    echo "Starting $service_name on port $port..."
    
    if [ -d "$service_dir" ]; then
        cd "$service_dir"
        
        # Activate virtual environment and start service
        source venv/bin/activate
        
        # Start service in background
        python src/main.py > logs/${service_name}.log 2>&1 &
        
        # Store PID
        echo $! > logs/${service_name}.pid
        
        echo "✅ $service_name started (PID: $!)"
        
        # Wait a moment for service to start
        sleep 2
    else
        echo "❌ Service directory not found: $service_dir"
        exit 1
    fi
}

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    echo "Checking $service_name health..."
    
    # Wait for service to be ready
    for i in {1..10}; do
        if curl -s "http://localhost:$port/api/v1/health" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        echo "⏳ Waiting for $service_name to be ready... ($i/10)"
        sleep 3
    done
    
    echo "❌ $service_name failed to start properly"
    return 1
}

# Create logs directory
mkdir -p /home/ubuntu/NexaFi/backend/logs

# Start services in order
echo "Starting microservices..."

start_service "user-service" 5001
check_service "user-service" 5001

start_service "ledger-service" 5002
check_service "ledger-service" 5002

start_service "payment-service" 5003
check_service "payment-service" 5003

start_service "ai-service" 5004
check_service "ai-service" 5004

# Start API Gateway last
echo "Starting API Gateway..."
cd /home/ubuntu/NexaFi/backend/api-gateway
source venv/bin/activate
python src/main.py > ../logs/api-gateway.log 2>&1 &
echo $! > ../logs/api-gateway.pid

# Check API Gateway
sleep 3
if curl -s "http://localhost:5000/health" > /dev/null 2>&1; then
    echo "✅ API Gateway is healthy"
else
    echo "❌ API Gateway failed to start"
    exit 1
fi

echo ""
echo "🎉 All NexaFi Backend Services Started Successfully!"
echo "=================================================="
echo ""
echo "Service URLs:"
echo "- API Gateway:     http://localhost:5000"
echo "- User Service:    http://localhost:5001"
echo "- Ledger Service:  http://localhost:5002"
echo "- Payment Service: http://localhost:5003"
echo "- AI Service:      http://localhost:5004"
echo ""
echo "Health Check: curl http://localhost:5000/health"
echo "API Documentation: http://localhost:5000/api/v1/services"
echo ""
echo "To stop all services, run: ./stop_services.sh"
echo "To view logs: tail -f logs/[service-name].log"


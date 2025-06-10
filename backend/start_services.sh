#!/bin/bash

# Enhanced NexaFi Backend Startup Script
# This script starts all microservices with infrastructure support

echo "🚀 Starting Enhanced NexaFi Backend Services..."

# Create logs directory
mkdir -p logs

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    
    echo "🔄 Starting $service_name on port $port..."
    
    cd $service_name
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install additional dependencies if requirements have changed
    pip install -q redis pika elasticsearch flask-limiter
    
    # Update requirements
    pip freeze > requirements.txt
    
    # Start the service in background
    nohup python src/main.py > ../logs/$service_name.log 2>&1 &
    
    # Store PID
    echo $! > ../logs/$service_name.pid
    
    cd ..
    
    echo "✅ $service_name started (PID: $(cat logs/$service_name.pid))"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start within timeout"
    return 1
}

# Check if infrastructure is running
echo "🔍 Checking infrastructure services..."

if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting infrastructure..."
    cd infrastructure
    ./start-infrastructure.sh
    cd ..
    sleep 10
fi

# Start all services
echo "🚀 Starting microservices..."

# API Gateway (Port 5000)
if check_port 5000; then
    start_service "api-gateway" 5000
    wait_for_service "api-gateway" 5000
fi

# User Service (Port 5001)
if check_port 5001; then
    start_service "user-service" 5001
    wait_for_service "user-service" 5001
fi

# Ledger Service (Port 5002)
if check_port 5002; then
    start_service "ledger-service" 5002
    wait_for_service "ledger-service" 5002
fi

# Payment Service (Port 5003)
if check_port 5003; then
    start_service "payment-service" 5003
    wait_for_service "payment-service" 5003
fi

# AI Service (Port 5004)
if check_port 5004; then
    start_service "ai-service" 5004
    wait_for_service "ai-service" 5004
fi

# Analytics Service (Port 5005)
if check_port 5005; then
    start_service "analytics-service" 5005
    wait_for_service "analytics-service" 5005
fi

# Credit Service (Port 5006)
if check_port 5006; then
    start_service "credit-service" 5006
    wait_for_service "credit-service" 5006
fi

# Document Service (Port 5007)
if check_port 5007; then
    start_service "document-service" 5007
    wait_for_service "document-service" 5007
fi

echo ""
echo "🎉 Enhanced NexaFi Backend is now running!"
echo ""
echo "📊 Service Status:"
echo "   🌐 API Gateway:      http://localhost:5000"
echo "   👤 User Service:     http://localhost:5001"
echo "   📊 Ledger Service:   http://localhost:5002"
echo "   💳 Payment Service:  http://localhost:5003"
echo "   🤖 AI Service:       http://localhost:5004"
echo "   📈 Analytics Service: http://localhost:5005"
echo "   💰 Credit Service:   http://localhost:5006"
echo "   📄 Document Service: http://localhost:5007"
echo ""
echo "🔧 Infrastructure Services:"
echo "   🗄️  Redis:           localhost:6379"
echo "   🐰 RabbitMQ:         http://localhost:15672 (nexafi/nexafi123)"
echo "   🔍 Elasticsearch:    http://localhost:9200"
echo "   📊 Kibana:           http://localhost:5601"
echo ""
echo "📝 Logs are available in the logs/ directory"
echo "🛑 To stop all services, run: ./stop_services.sh"


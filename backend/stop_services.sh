#!/bin/bash

# NexaFi Backend Services Stop Script
# This script stops all running microservices

echo "🛑 Stopping NexaFi Backend Services..."
echo "====================================="

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "Stopping $service_name (PID: $pid)..."
        
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force killing $service_name..."
                kill -9 "$pid"
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name was not running"
        fi
        
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file found for $service_name"
    fi
}

# Stop all services
stop_service "api-gateway"
stop_service "ai-service"
stop_service "payment-service"
stop_service "ledger-service"
stop_service "user-service"

# Kill any remaining Python processes on our ports
echo "Cleaning up any remaining processes..."
for port in 5000 5001 5002 5003 5004; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
    fi
done

echo ""
echo "✅ All NexaFi Backend Services Stopped"


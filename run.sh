#!/bin/bash

# Run script for NexaFi

echo "Starting NexaFi application..."

# Navigate to the NexaFi directory
cd /home/ubuntu/NexaFi

# --- Start Infrastructure Services ---
echo "Starting infrastructure services..."
cd backend/infrastructure
./start-infrastructure.sh
cd ../..

# --- Start Backend Services ---
echo "Starting backend services..."
cd backend
./start_services.sh
cd ..

# --- Start Frontend Development Server ---
echo "Starting frontend development server..."
cd frontend/web
pnpm run dev

echo "NexaFi application is running!"

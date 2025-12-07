#!/bin/bash\n\nset -euo pipefail

# Run script for NexaFi

echo "Starting NexaFi application..."

# Navigate to the NexaFi directory
# The script is expected to be run from the root of the NexaFi directory, so no need to cd to a fixed path

# --- Start Infrastructure Services ---
echo "Starting infrastructure services..."
cd infrastructure
./start-infrastructure.sh || { echo "Failed to start infrastructure."; exit 1; }
cd ..

# --- Start Backend Services ---
echo "Starting backend services..."
cd backend
./start_services.sh || { echo "Failed to start backend services."; exit 1; }
cd ..

# --- Start Frontend Development Server ---
echo "Starting frontend development server..."
cd web-frontend
pnpm run dev || { echo "Failed to start frontend development server."; exit 1; }

echo "NexaFi application is running!"

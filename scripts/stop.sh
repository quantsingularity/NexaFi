#!/bin/bash

set -euo pipefail

echo "🛑 Stopping NexaFi Application..."

# --- Stop Frontend Development Server ---
# The frontend server is usually stopped by Ctrl+C in the terminal where it was started.
# If it was run in the background, we would need to find its PID.
# For simplicity, we assume the user will stop the foreground process.

# --- Stop Backend Services ---
echo "Stopping backend services..."
if [ -f "backend/stop_services.sh" ]; then
    ./backend/stop_services.sh
else
    echo "Warning: backend/stop_services.sh not found. Cannot stop backend services cleanly."
fi

# --- Stop Infrastructure Services ---
echo "Stopping infrastructure services..."
if [ -f "infrastructure/stop-infrastructure.sh" ]; then
    ./infrastructure/stop-infrastructure.sh
else
    echo "Warning: infrastructure/stop-infrastructure.sh not found. Cannot stop infrastructure services cleanly."
fi

echo "NexaFi application stopped."

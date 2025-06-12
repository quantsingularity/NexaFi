#!/bin/bash

# Setup script for NexaFi

echo "Starting NexaFi setup..."

# Navigate to the NexaFi directory
cd /home/ubuntu/NexaFi

# --- Install Docker and Docker Compose ---
echo "Installing Docker and Docker Compose..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  \"$(. /etc/os-release && echo "$VERSION_CODENAME")\" stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# --- Backend Setup ---
echo "Setting up backend dependencies..."

# Install Python dependencies for each service in a virtual environment
for service_dir in backend/*/; do
  if [ -f "${service_dir}requirements.txt" ]; then
    echo "Installing dependencies for ${service_dir}..."
    cd "${service_dir}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ../..
  fi
done

# --- Frontend Setup ---
echo "Setting up frontend dependencies..."

# Install pnpm
npm install -g pnpm

# Navigate to the frontend web directory
cd frontend/web

# Install Node.js dependencies using pnpm
pnpm install

echo "NexaFi setup complete!"



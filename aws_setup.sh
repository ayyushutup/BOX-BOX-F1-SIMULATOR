#!/bin/bash
set -e

echo "--- BOX BOX AWS EC2 SETUP ---"

# 1. Update and install basic dependencies
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "Docker already installed."
fi

# 3. Create Swap file (Critical for t3.micro/1GB RAM)
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swap file..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile lib none swap sw 0 0' | sudo tee -a /etc/etc/fstab
    echo "Swap created."
else
    echo "Swap file already exists."
fi

# 4. Firewall reminder
echo "------------------------------------------------"
echo "SETUP COMPLETE!"
echo "IMPORTANT: Ensure your AWS Security Group allows:"
echo " - Port 22 (SSH)"
echo " - Port 80 (Frontend)"
echo " - Port 443 (HTTPS - if using SSL)"
echo " - Port 8000 (Backend - if accessed directly)"
echo "------------------------------------------------"
echo "Next steps:"
echo "1. git clone <repo_url>"
echo "2. cd \"BOX BOX\""
echo "3. cp .env.example .env"
echo "4. Edit .env (set VITE_API_BASE_URL and POSTGRES_PASSWORD)"
echo "5. docker compose up --build -d"

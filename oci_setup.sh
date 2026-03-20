#!/bin/bash
set -e

echo "--- BOX BOX ORACLE CLOUD (OCI) ARM SETUP ---"

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
    echo "Docker installed."
else
    echo "Docker already installed."
fi

# 3. OCI Networking: Open Firewall (iptables)
# OCI instances often have restrictive default iptables rules.
echo "Opening firewall ports 80, 8000..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save || true

# 4. Success summary
echo "------------------------------------------------"
echo "OCI SETUP COMPLETE!"
echo "REMEMBER: You MUST also open ports 80 and 8000"
echo "in your OCI 'Security List' (Ingress Rules) via the Console."
echo "------------------------------------------------"
echo "Next steps:"
echo "1. git clone <repo_url>"
echo "2. cd \"BOX BOX\""
echo "3. cp .env.example .env"
echo "4. Edit .env (set VITE_API_BASE_URL to your OCI Public IP)"
echo "5. docker compose up --build -d"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker and Docker Compose first."
  exit 1
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
  echo "Update .env with production values, then run ./deploy.sh again."
  exit 1
fi

if ! grep -q "^POSTGRES_PASSWORD=" .env || grep -q "^POSTGRES_PASSWORD=your_secure_password" .env; then
  echo "Set a secure POSTGRES_PASSWORD in .env before deploy."
  exit 1
fi

echo "Validating compose configuration..."
docker compose config >/dev/null

echo "Building and starting services..."
docker compose up -d --build

echo "Services status:"
docker compose ps

echo "Health checks:"
curl -fsS http://localhost/health || true
curl -fsS http://localhost/api/tracks | head -c 300 || true
echo

echo "Deploy completed."

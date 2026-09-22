#!/bin/bash
set -euo pipefail

echo "=== Bootstrap ECS ==="

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root (sudo)"
    exit 1
fi

echo "[1/6] Installing Git, curl, ca-certificates..."
apt-get update -qq
apt-get install -y -qq git curl ca-certificates >/dev/null

echo "[2/6] Checking Docker..."
if command -v docker &>/dev/null; then
    echo "Docker already installed: $(docker --version)"
else
    echo "Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sh
fi

echo "[3/6] Enabling Docker..."
systemctl enable docker >/dev/null 2>&1 || true
systemctl start docker >/dev/null 2>&1 || true

echo "[4/6] Checking Docker Compose..."
if docker compose version &>/dev/null; then
    echo "Docker Compose already available: $(docker compose version)"
else
    echo "Installing Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin >/dev/null
fi

echo "[5/6] Adding current user to docker group..."
if [ -n "${SUDO_USER:-}" ]; then
    usermod -aG docker "$SUDO_USER" 2>/dev/null || true
    echo "Added $SUDO_USER to docker group"
fi

echo "[6/6] Verifying..."
docker --version
docker compose version

echo "=== Bootstrap Complete ==="

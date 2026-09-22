#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== One-Click ECS Deployment ==="

echo "[1/4] Bootstrapping ECS..."
bash "$SCRIPT_DIR/bootstrap-ecs.sh"

echo "[2/4] Creating environment..."
bash "$SCRIPT_DIR/create-env.sh"

echo "[3/4] Deploying..."
bash "$SCRIPT_DIR/deploy.sh"

echo "[4/4] Deployment complete!"
echo ""
echo "Open http://<ECS_PUBLIC_IP>:8080 in your browser."

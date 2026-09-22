#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_FILE="${PROJECT_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found. Run create-env.sh first."
    exit 1
fi

source "$ENV_FILE"

REQUIRED_VARS=(
    AIOPS_INTERNAL_TOKEN
    DEMO_ADMIN_TOKEN
    APPROVAL_SIGNING_SECRET
    HERMES_API_SERVER_KEY
)

for var in "${REQUIRED_VARS[@]}"; do
    val="${!var:-}"
    if [ -z "$val" ] || [ "$val" = "replace-me" ]; then
        echo "ERROR: $var is not set or still 'replace-me' in .env"
        exit 1
    fi
done

echo "=== Deploy Governed AI Ops Demo ==="

echo "[1/6] Rendering Hermes config..."
bash "$SCRIPT_DIR/render-hermes-config.sh" || true

echo "[2/6] Building Docker images..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" build

echo "[3/6] Starting services..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d

echo "[4/6] Waiting for health..."
sleep 5
bash "$SCRIPT_DIR/healthcheck.sh"

echo "[5/6] Running smoke tests..."
bash "$SCRIPT_DIR/smoke-test.sh" || true

echo "[6/6] Done."
echo ""
echo "Governed AI Ops Demo is READY"
echo ""
echo "UI:"
echo "  http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):${PUBLIC_PORT:-8080}"
echo ""
echo "Mode:"
if [ "${AIOPS_AGENT_MODE:-mock}" = "hermes" ]; then
    echo "  Hermes"
else
    echo "  Mock"
fi
echo ""
echo "Next:"
echo "  1. Open UI"
echo "  2. Reset Demo"
echo "  3. Inject Incident"
echo "  4. Start AI Diagnosis"

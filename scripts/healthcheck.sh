#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_DIR/.env"

PORT="${PUBLIC_PORT:-8080}"
MAX_WAIT=60
WAITED=0

echo "Checking service health..."

check_url() {
    local name=$1
    local url=$2
    local resp
    resp=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$resp" = "200" ]; then
        echo "  ✓ $name: OK ($resp)"
        return 0
    else
        echo "  ✗ $name: FAIL ($resp)"
        return 1
    fi
}

while [ $WAITED -lt $MAX_WAIT ]; do
    if check_url "aiops-ui" "http://localhost:$PORT/" && \
       check_url "aiops-api" "http://localhost:$PORT/api/demo/status" && \
       docker compose -f "$PROJECT_DIR/docker-compose.yml" ps | grep -q "demo-backend.*healthy"; then
        echo "All services healthy!"
        exit 0
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo "  Waiting... ($WAITED/${MAX_WAIT}s)"
done

echo "ERROR: Services did not become healthy in time."
docker compose -f "$PROJECT_DIR/docker-compose.yml" ps
exit 1

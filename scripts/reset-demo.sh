#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PORT="${PUBLIC_PORT:-8080}"
BASE="http://localhost:$PORT"

echo "=== Reset Demo ==="
curl -s -X POST "$BASE/api/demo/reset" | python3 -m json.tool 2>/dev/null || echo "reset failed"
echo "Demo reset complete."

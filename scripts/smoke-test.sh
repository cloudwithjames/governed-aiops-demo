#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_DIR/.env"

PORT="${PUBLIC_PORT:-8080}"
BASE="http://localhost:$PORT"

echo "=== Reset Demo ==="
curl -s -X POST "$BASE/api/demo/reset" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Check Status ==="
curl -s "$BASE/api/demo/status" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Inject Fault ==="
curl -s -X POST "$BASE/api/demo/inject" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Create Incident ==="
INCIDENT=$(curl -s -X POST "$BASE/api/incidents")
echo "$INCIDENT" | python3 -m json.tool 2>/dev/null || true
INCIDENT_ID=$(echo "$INCIDENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
echo ""

if [ -z "$INCIDENT_ID" ]; then
    echo "ERROR: Could not create incident"
    exit 1
fi

echo "=== Run Diagnosis ==="
curl -s -X POST "$BASE/api/incidents/$INCIDENT_ID/run-diagnosis" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Approve ==="
curl -s -X POST "$BASE/api/incidents/$INCIDENT_ID/approve" -d "approver=Demo%20Operator" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Get Report ==="
curl -s "$BASE/api/incidents/$INCIDENT_ID/report" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Reset ==="
curl -s -X POST "$BASE/api/demo/reset" | python3 -m json.tool 2>/dev/null || true
echo ""

echo "=== Smoke Test Complete ==="

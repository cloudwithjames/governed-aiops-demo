#!/bin/bash
set -e
BASE="http://localhost:8080"

echo "=== 0. CHECK PORTAL (healthy) ==="
curl -s -o /dev/null -w "Portal HTTP %{http_code}\n" "$BASE/portal/"
echo ""

echo "=== 1. INJECT FAULT ==="
curl -s -X POST "$BASE/api/demo/inject" | python3 -m json.tool
echo ""

echo "=== 1b. CHECK PORTAL (should be 502) ==="
curl -s -o /dev/null -w "Portal HTTP %{http_code}\n" "$BASE/portal/"
echo ""

echo "=== 2. CREATE INCIDENT ==="
INCIDENT=$(curl -s -X POST "$BASE/api/incidents")
echo "$INCIDENT" | python3 -m json.tool
IID=$(echo "$INCIDENT" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "Incident ID: $IID"
echo ""

echo "=== 3. RUN DIAGNOSIS (async) ==="
curl -s -X POST "$BASE/api/incidents/$IID/run-diagnosis" | python3 -m json.tool
echo ""

echo "=== 3b. WAIT FOR DIAGNOSIS COMPLETE ==="
for i in $(seq 1 30); do
    STATUS=$(curl -s "$BASE/api/incidents/$IID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
    echo "  Status: $STATUS ($i/30)"
    if [ "$STATUS" = "WAITING_APPROVAL" ]; then
        echo "  Diagnosis complete!"
        break
    fi
    sleep 1
done
echo ""

echo "=== 4. GET EVIDENCE ==="
curl -s "$BASE/api/incidents/$IID/evidence" | python3 -m json.tool
echo ""

echo "=== 5. GET INCIDENT ==="
curl -s "$BASE/api/incidents/$IID" | python3 -m json.tool
echo ""

echo "=== 6. APPROVE (async) ==="
curl -s -X POST "$BASE/api/incidents/$IID/approve" -d "approver=Demo%20Operator" | python3 -m json.tool
echo ""

echo "=== 6b. WAIT FOR EXECUTION COMPLETE ==="
for i in $(seq 1 30); do
    STATUS=$(curl -s "$BASE/api/incidents/$IID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
    echo "  Status: $STATUS ($i/30)"
    if [ "$STATUS" = "REPORTED" ] || [ "$STATUS" = "FAILED" ]; then
        echo "  Execution complete!"
        break
    fi
    sleep 1
done
echo ""

echo "=== 7. GET REPORT ==="
curl -s "$BASE/api/incidents/$IID/report" | python3 -m json.tool
echo ""

echo "=== 8. FINAL STATUS ==="
curl -s "$BASE/api/demo/status" | python3 -m json.tool
echo ""

echo "=== 9. CHECK PORTAL (should be 200 again) ==="
curl -s -o /dev/null -w "Portal HTTP %{http_code}\n" "$BASE/portal/"
echo ""

echo "=== 10. RESET ==="
curl -s -X POST "$BASE/api/demo/reset" | python3 -m json.tool
echo ""

echo "=== SMOKE TEST COMPLETE ==="

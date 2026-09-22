# Architecture

## Components

| Service | Tech | Port | Public |
|---------|------|------|--------|
| aiops-ui | Nginx + HTML/JS | 80 (→8080) | Yes |
| aiops-api | FastAPI + SQLite | 8000 | No |
| hermes | Hermes Agent | 8642 | No |
| ops-mcp | FastAPI MCP | 8765 | No |
| demo-gateway | FastAPI proxy | 8080 | No |
| demo-backend | FastAPI | 8080 | No |

## Flow

```
Observe → Diagnose → Plan → Human Approval → Execute → Verify → Record
```

1. **Observe**: AI calls `check_portal`, `check_backend` via MCP
2. **Diagnose**: AI calls `get_gateway_logs`, `get_gateway_config`, `get_recent_changes`
3. **Plan**: AI builds remediation plan, stops before write
4. **Approval**: Human approves in UI → server generates scoped token
5. **Execute**: MCP `apply_gateway_fix` validates token, changes gateway upstream
6. **Verify**: MCP `verify_service` checks portal/backend/gateway health
7. **Record**: Report generated with evidence, MTTR, approval audit

## Governance Layers

```
Human (approves risk)
  → Hermes (probabilistic reasoning)
    → Ops MCP (deterministic permissions)
      → Demo system (execute known operations)
        → Verification (evidence decides success)
```

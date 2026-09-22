# Security Model

## AI reasoning is not authorization

Hermes recommends; it does not self-authorize. Approval tokens are generated only by the approval API, never by Hermes.

## Deterministic write path

Only `apply_gateway_fix` performs state-changing operations. It enforces:
1. Incident exists and is in APPROVED/EXECUTING state
2. Token valid, unexpired, not reused
3. Action scope matches
4. Expected current config matches actual
5. Target URL on hard allowlist

## No generic shell

No shell/bash/ssh/sudo/docker/exec tools are exposed via MCP.

## Docker isolation

No `/var/run/docker.sock`, `/`, `/root`, or `/home` mounts into Hermes or MCP.

## Network

Only UI port 8080 is public. Hermes (8642), MCP (8765), API (8000) are Docker-internal only.

## Secrets

`.gitignore` excludes `.env`, `*.db`, `data/`, `hermes-data/`.

## Demo disclaimer

This is a reference demo, not a production security architecture. For production, map to enterprise IAM/RBAC, policy engine, real approval workflow, secret manager, audit service, sandboxed execution.

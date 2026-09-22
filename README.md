# Huawei Cloud Governed AI Ops Demo

> **Observe → Diagnose → Plan → Approve → Execute → Verify → Record**

A governed AI operations demo where AI reasons, humans approve risky decisions, and deterministic tools execute.

## What This Demo Proves

- AI observes and reasons (Hermes Agent)
- Humans approve risky decisions (Approval gate)
- Deterministic tools execute and verify (MCP server)

## Architecture

```
Customer Browser → aiops-ui (Nginx) → aiops-api (FastAPI) ↔ Hermes Agent
                                       ↕                        ↕
                                   ops-mcp (7 tools)    demo-gateway → demo-backend
                                       SQLite
```

Six Docker services on one Huawei Cloud ECS.

## Prerequisites

- Ubuntu 22.04/24.04 LTS ECS
- Docker Engine + Compose plugin
- 4 vCPU, 8GB RAM, 30GB+ disk

## Quick Start (Mock Mode)

```bash
cp .env.example .env
# Edit .env: set tokens to random values
docker compose up -d --build
```

Open `http://<ECS_IP>:8080`

## ECS Deployment

```bash
git clone <repo-url> governed-aiops-demo
cd governed-aiops-demo
sudo ./scripts/one-click-ecs.sh
```

## Hermes Mode

Set in `.env`:
```
AIOPS_AGENT_MODE=hermes
HERMES_MODEL_NAME=your-model
HERMES_MODEL_BASE_URL=https://your-endpoint/v1
HERMES_MODEL_API_KEY=your-key
```

Then:
```bash
docker compose --profile hermes up -d --build
```

## Demo Runbook

See `docs/demo-runbook.md` for the 20-30 minute demo script.

## Reset/Recovery

Click "Reset Demo" in the UI, or:
```bash
curl -X POST http://localhost:8080/api/demo/reset
```

## Security

See `docs/security.md`. Key points:
- Only UI port 8080 is public
- No shell/SSH access for Hermes
- State-changing ops require approval tokens
- No Docker socket mount

## Troubleshooting

```bash
docker compose ps
docker compose logs -f aiops-api
docker compose logs -f ops-mcp
docker compose logs -f demo-gateway
```

## Git Update

```bash
git pull --ff-only
sudo ./scripts/deploy.sh
```

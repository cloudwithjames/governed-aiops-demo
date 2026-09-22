# implementation.md
# Huawei Cloud Governed AI Ops Demo — Implementation Specification

> **Purpose**  
> This file is the implementation prompt/specification for an AI coding agent. Build a complete, Git-ready repository that deploys to **one Huawei Cloud ECS** with **Docker Compose** and supports a **20–30 minute customer demo**.
>
> Demo loop:
>
> **Observe → Diagnose → Plan → Human Approval → Execute → Verify → Record**
>
> The UI must be a **single-page bilingual Chinese/English interface**. Hermes Agent is the reasoning layer. Hermes must **not** have unrestricted SSH/root/shell access. All operational actions go through a small deterministic MCP tool server with approval checks.

---

## 0. Instructions to the AI Coding Agent

You are implementing a customer-facing technical demo, not a throwaway script.

### Deliverables

Create a complete repository containing:

1. Bilingual single-page Web UI.
2. FastAPI orchestration backend.
3. Hermes Agent integration through its OpenAI-compatible API server.
4. Custom MCP server exposing only approved AI Ops tools.
5. Fault-injectable demo gateway.
6. Healthy demo backend.
7. SQLite persistence for incident state, evidence, approvals, events and reports.
8. Dockerfiles and `docker-compose.yml`.
9. `.env.example`, configuration templates and secret handling.
10. Unit, integration and smoke tests.
11. One-click ECS bootstrap/deployment scripts.
12. README with deployment/demo instructions.
13. GitHub Actions CI for test/build validation.
14. Deterministic mock-agent mode for automated testing and emergency fallback.
15. This `implementation.md` in the repository root.

### Mandatory behavior

- Prefer the simplest reliable implementation.
- Do **not** add Kubernetes, AWX, Argo, Terraform, Prometheus, Grafana, Redis or PostgreSQL.
- Do not build a generic platform; build this exact demo well.
- Do not give Hermes arbitrary shell access to the ECS.
- Do not mount `/var/run/docker.sock`, `/`, `/root` or `/home` into Hermes/MCP.
- Do not expose Hermes, MCP, aiops-api or demo admin endpoints publicly.
- State-changing operations must fail without a valid, scoped, unexpired approval token.
- The LLM may select an approved action; deterministic code performs it.
- The UI must make **AI reasoning**, **human approval**, and **deterministic execution** visibly distinct.
- Use synthetic demo data only.
- Never commit secrets.
- Language switching must not trigger a second LLM call.
- If ambiguous, choose the smallest design consistent with this document and record the decision.

### Git behavior

If Git is available:

1. Initialize Git if needed.
2. Create `feat/governed-aiops-demo`.
3. Implement in logical commits.
4. Run tests before completion.
5. Never commit `.env`, keys, approval tokens or databases.
6. Push only if credentials are already available; otherwise print the exact push commands.

Suggested commits:

```text
chore: scaffold governed aiops demo
feat: add demo backend and fault-injectable gateway
feat: add governed ops mcp tools
feat: add incident orchestration and approval state machine
feat: integrate hermes agent
feat: add bilingual customer demo ui
test: add end-to-end and approval tests
chore: add docker compose and ecs deployment automation
docs: add demo runbook and architecture
```


---

## 1. Demo Story

### 1.1 Business scenario

A fictional **Customer Portal** is unavailable.

Visible service state:

```text
Customer Portal    CRITICAL
Gateway            CRITICAL
Backend            HEALTHY
```

The portal returns:

```text
HTTP 502 Bad Gateway
```

The backend itself remains healthy:

```text
HTTP 200 OK
```

Actual deterministic fault:

```text
Normal gateway upstream:
http://demo-backend:8080

Injected faulty upstream:
http://demo-backend:8081
```

Port `8081` intentionally has no listener.

The AI must discover this by using evidence tools.

### 1.2 Expected evidence chain

```text
E01 — Customer Portal returns HTTP 502.
E02 — Backend health endpoint returns HTTP 200.
E03 — Gateway log shows connection refused to demo-backend:8081.
E04 — Current gateway upstream configuration points to demo-backend:8081.
E05 — Recent change history shows upstream changed from 8080 to 8081.
```

Expected conclusion:

```text
Root Cause:
Gateway upstream port misconfiguration.

Expected:
demo-backend:8080

Current:
demo-backend:8081
```

The exact wording may differ, but the conclusion must cite evidence IDs.


---

## 2. Customer Message

The demo must reinforce these three lines:

```text
AI observes and reasons.
Humans approve risky decisions.
Deterministic tools execute and verify.
```

Chinese:

```text
AI 负责观察和推理。
人负责风险决策。
确定性工具负责执行与验证。
```

The interface should visibly indicate which step belongs to which layer.


---

## 3. Target Architecture

Run all components on one Huawei Cloud ECS.

```text
                     Customer Browser
                            |
                         HTTP/HTTPS
                            |
                            v
              +---------------------------+
              | aiops-ui                  |
              | Nginx + static HTML/JS    |
              |                           |
              | /api/*    -> aiops-api    |
              | /portal/* -> demo-gateway |
              +-------------+-------------+
                            |
               Docker private network
                            |
      +---------------------+----------------------+
      |                     |                      |
      v                     v                      v
+-------------+      +--------------+      +---------------+
| aiops-api   |      | Hermes Agent |      | ops-mcp       |
| FastAPI     |<---->| API :8642    |----->| approved tools|
| SQLite      |      | reasoning    | MCP  | policy checks |
+------+------+      +--------------+      +-------+-------+
       |                                            |
       | internal HTTP                              |
       v                                            v
+----------------+                           +----------------+
| demo-gateway   |-------------------------->| demo-backend   |
| fault target   |                           | healthy app    |
+----------------+                           +----------------+

Hermes model path:
Hermes -> configurable OpenAI-compatible endpoint
       -> UOL LiteLLM OR Huawei Cloud MaaS compatible endpoint
       -> GLM
```

### Public exposure

Default public mapping:

```text
ECS TCP 8080 -> aiops-ui:80
```

Do **not** publish:

```text
8642 Hermes
8765 MCP
8000 aiops-api
demo backend
demo gateway admin API
```


---

## 4. Technology Choices

### Frontend

Use:

```text
HTML5
CSS3
Vanilla JavaScript
Nginx
```

Do not use React/Vue/Angular for V1.

### Backend

Use:

```text
Python 3.12
FastAPI
Pydantic
SQLAlchemy or SQLModel
SQLite
httpx
Server-Sent Events (SSE)
```

Persist SQLite at:

```text
/data/aiops.db
```

### Hermes

Use the official Hermes Agent Docker image in persistent gateway/API mode.

Expected internal API:

```text
http://hermes:8642/v1/chat/completions
```

Use runtime configuration:

```text
HERMES_MODEL_NAME
HERMES_MODEL_BASE_URL
HERMES_MODEL_API_KEY
HERMES_API_SERVER_KEY
```

The model endpoint can be UOL LiteLLM or another OpenAI-compatible endpoint. Do not hard-code the provider.

Select a model compatible with Hermes multi-step tool-calling requirements.

### MCP

Use the current official Python MCP SDK and expose a remote HTTP/Streamable HTTP MCP endpoint:

```text
http://ops-mcp:8765/mcp
```

Do not expose a generic shell tool.


---

## 5. Repository Structure

Create this overall shape:

```text
governed-aiops-demo/
|
|-- implementation.md
|-- README.md
|-- LICENSE
|-- .gitignore
|-- .env.example
|-- docker-compose.yml
|-- Makefile
|
|-- ui/
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- index.html
|   |-- css/app.css
|   `-- js/
|       |-- app.js
|       |-- api.js
|       |-- i18n.js
|       `-- state.js
|
|-- api/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/
|       |-- __init__.py
|       |-- main.py
|       |-- config.py
|       |-- db.py
|       |-- models.py
|       |-- schemas.py
|       |-- i18n.py
|       |-- routers/
|       |   |-- demo.py
|       |   |-- incidents.py
|       |   |-- approvals.py
|       |   |-- reports.py
|       |   `-- health.py
|       |-- services/
|       |   |-- incident_service.py
|       |   |-- state_machine.py
|       |   |-- hermes_client.py
|       |   |-- approval_service.py
|       |   |-- report_service.py
|       |   `-- event_service.py
|       `-- prompts/
|           |-- system_prompt.md
|           |-- diagnose_prompt.md
|           `-- execute_prompt.md
|
|-- ops-mcp/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/
|       |-- __init__.py
|       |-- main.py
|       |-- config.py
|       |-- tools.py
|       |-- approval_client.py
|       |-- event_client.py
|       `-- gateway_client.py
|
|-- demo-backend/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app.py
|
|-- demo-gateway/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app.py
|
|-- hermes/
|   |-- config.yaml.template
|   |-- env.template
|   `-- skills/governed-aiops.md
|
|-- scripts/
|   |-- render-hermes-config.sh
|   |-- bootstrap-ecs.sh
|   |-- deploy.sh
|   |-- one-click-ecs.sh
|   |-- healthcheck.sh
|   |-- reset-demo.sh
|   |-- smoke-test.sh
|   `-- create-env.sh
|
|-- tests/
|   |-- unit/
|   |   |-- test_state_machine.py
|   |   |-- test_approval.py
|   |   `-- test_i18n.py
|   |-- integration/
|   |   |-- test_fault_injection.py
|   |   |-- test_mcp_write_guard.py
|   |   `-- test_incident_flow_mock.py
|   `-- fixtures/
|
|-- .github/workflows/ci.yml
|
`-- docs/
    |-- architecture.md
    |-- demo-runbook.md
    |-- security.md
    `-- screenshots/
```


---

## 6. Docker Compose Requirements

Six services:

```text
1. aiops-ui
2. aiops-api
3. hermes
4. ops-mcp
5. demo-gateway
6. demo-backend
```

Create network:

```text
aiops-net
```

Create volumes:

```text
aiops-data
hermes-data
```

Use health checks and dependency ordering.

Logical readiness:

```text
demo-backend
  -> demo-gateway
  -> aiops-api + ops-mcp
  -> hermes
  -> aiops-ui
```

Health endpoints:

```text
aiops-api     GET /healthz
ops-mcp       GET /healthz where transport allows
demo-gateway  GET /healthz
demo-backend  GET /healthz
```

Hermes health can use its API health endpoint or a lightweight `/v1/models` equivalent.


---

## 7. Environment Variables

Create `.env.example`:

```dotenv
PUBLIC_PORT=8080

AIOPS_AGENT_MODE=hermes
AIOPS_DB_PATH=/data/aiops.db
AIOPS_INTERNAL_TOKEN=replace-me
DEMO_ADMIN_TOKEN=replace-me
APPROVAL_SIGNING_SECRET=replace-me
APPROVAL_TTL_SECONDS=300

HERMES_API_URL=http://hermes:8642/v1
HERMES_API_SERVER_KEY=replace-me

HERMES_MODEL_NAME=your-model-name
HERMES_MODEL_BASE_URL=https://your-openai-compatible-endpoint/v1
HERMES_MODEL_API_KEY=replace-me

OPS_MCP_URL=http://ops-mcp:8765/mcp

DEMO_GATEWAY_URL=http://demo-gateway:8080
DEMO_BACKEND_URL=http://demo-backend:8080
NORMAL_BACKEND_URL=http://demo-backend:8080
FAULT_BACKEND_URL=http://demo-backend:8081

DEMO_APPROVER_NAME=Demo Operator
```

Deployment must fail fast if required values remain `replace-me`.

`create-env.sh` may generate local random secrets but must never invent a model API key.


---

## 8. Demo Backend

Implement a tiny FastAPI service.

Endpoints:

```text
GET /healthz
GET /api/status
```

Example:

```json
{
  "service": "demo-backend",
  "status": "healthy",
  "version": "1.0.0",
  "message": "Customer Portal backend is healthy"
}
```

The backend remains healthy during the main incident.


---

## 9. Demo Gateway

Implement a tiny reverse-proxy-like FastAPI service using `httpx`.

Normal upstream:

```text
http://demo-backend:8080
```

Fault upstream:

```text
http://demo-backend:8081
```

Public/demo endpoints:

```text
GET /healthz
GET /portal
GET /api/portal/status
```

When healthy, `/portal` shows a simple Customer Portal page.

When faulted, it visibly returns or renders:

```text
502 Bad Gateway
```

Internal admin endpoints require:

```text
X-Demo-Admin-Token
```

Implement:

```text
GET  /internal/config
POST /internal/config/upstream
GET  /internal/logs
GET  /internal/changes
POST /internal/reset
POST /internal/inject-fault
```

Track changes:

```json
{
  "timestamp": "...",
  "field": "backend_url",
  "old": "http://demo-backend:8080",
  "new": "http://demo-backend:8081",
  "source": "demo-fault-injection"
}
```

When the fault occurs, emit structured log data such as:

```json
{
  "level": "ERROR",
  "message": "upstream connection failed",
  "target": "demo-backend:8081",
  "error": "connection refused"
}
```


---

## 10. Incident State Machine

Allowed states:

```text
IDLE
INCIDENT_DETECTED
OBSERVING
DIAGNOSING
PLAN_READY
WAITING_APPROVAL
APPROVED
REJECTED
EXECUTING
VERIFYING
RECOVERED
FAILED
REPORTED
```

Happy path:

```text
IDLE
-> INCIDENT_DETECTED
-> OBSERVING
-> DIAGNOSING
-> PLAN_READY
-> WAITING_APPROVAL
-> APPROVED
-> EXECUTING
-> VERIFYING
-> RECOVERED
-> REPORTED
```

Reject:

```text
WAITING_APPROVAL -> REJECTED
```

Failure:

```text
EXECUTING -> FAILED
VERIFYING -> FAILED
```

Centralize transition validation and unit-test all allowed/forbidden transitions.


---

## 11. SQLite Data Model

### Incident

```text
id
title
status
created_at
updated_at
started_by
root_cause_json
plan_json
verification_json
report_json
mttr_seconds
```

### Event

```text
id
incident_id
sequence
timestamp
stage
event_type
source
message_code
message_params_json
raw_payload_json
```

Use deterministic message codes where possible:

```text
PORTAL_CHECK_STARTED
PORTAL_HTTP_502
BACKEND_HEALTHY
ROOT_CAUSE_READY
PLAN_READY
APPROVAL_GRANTED
FIX_EXECUTED
VERIFY_SUCCESS
```

### Evidence

```text
id
incident_id
evidence_code
category
source_tool
summary_en
summary_zh
raw_json
created_at
```

Evidence codes:

```text
E01, E02, E03...
```

### Approval

```text
id
incident_id
action
scope_json
token_hash
issued_at
expires_at
approved_by
status
used_at
```

Avoid storing raw approval tokens.


---

## 12. Public API

### Demo

```text
POST /api/demo/inject
POST /api/demo/reset
GET  /api/demo/status
```

`inject` must:

1. reset if necessary
2. change upstream 8080 -> 8081
3. confirm portal = 502
4. confirm backend = 200
5. publish visible state

### Incident

```text
POST /api/incidents
GET  /api/incidents/{id}
POST /api/incidents/{id}/run-diagnosis
GET  /api/incidents/{id}/events
GET  /api/incidents/{id}/stream
GET  /api/incidents/{id}/evidence
```

### Approval

```text
POST /api/incidents/{id}/approve
POST /api/incidents/{id}/reject
```

Approve request:

```json
{"approver":"Demo Operator"}
```

Prefer the server to keep the raw token and automatically resume execution after approval rather than exposing it broadly to the browser.

### Report

```text
GET /api/incidents/{id}/report
```

Return both languages in the same payload.


---

## 13. SSE Event Stream

Implement:

```text
GET /api/incidents/{id}/stream
Content-Type: text/event-stream
```

UI updates through SSE:

- state
- timeline
- evidence
- root cause
- plan
- approval
- execution
- verification
- final report

Implement reconnect behavior.


---

## 14. MCP Tool Server

This is a core control boundary.

Expose **exactly** these seven tools.

### `check_portal`

Input:

```json
{"incident_id":"INC-..."}
```

Output example:

```json
{
  "evidence_id": "E01",
  "portal_status_code": 502,
  "healthy": false,
  "latency_ms": 21
}
```

### `check_backend`

Output:

```json
{
  "evidence_id": "E02",
  "backend_status_code": 200,
  "healthy": true,
  "version": "1.0.0"
}
```

### `get_gateway_logs`

Bound recent entries only.

```json
{
  "evidence_id": "E03",
  "entries": [{
    "level":"ERROR",
    "message":"upstream connection failed",
    "target":"demo-backend:8081",
    "error":"connection refused"
  }]
}
```

### `get_gateway_config`

```json
{
  "evidence_id":"E04",
  "backend_url":"http://demo-backend:8081"
}
```

### `get_recent_changes`

```json
{
  "evidence_id":"E05",
  "changes":[{
    "field":"backend_url",
    "old":"http://demo-backend:8080",
    "new":"http://demo-backend:8081"
  }]
}
```

### `apply_gateway_fix`

Input:

```json
{
  "incident_id":"INC-...",
  "approval_token":"APP-...",
  "expected_current_backend_url":"http://demo-backend:8081",
  "target_backend_url":"http://demo-backend:8080"
}
```

Mandatory checks:

1. incident exists
2. state is approved/executing
3. token valid
4. token unexpired
5. action scope == `fix_gateway_upstream`
6. expected current config matches actual config
7. target URL is on hard allowlist
8. token not already used
9. mark token used
10. execute deterministic admin API change
11. emit event
12. return exact before/after config

Errors:

```text
APPROVAL_REQUIRED
APPROVAL_EXPIRED
SCOPE_MISMATCH
CURRENT_STATE_MISMATCH
TARGET_NOT_ALLOWED
TOKEN_ALREADY_USED
```

### `verify_service`

Perform:

```text
gateway config == healthy config
backend == HTTP 200
portal == HTTP 200
no new 502/upstream errors after remediation timestamp
```

Return structured check results and create verification evidence.

### Forbidden tools

Do not expose anything equivalent to:

```text
shell
bash
ssh
sudo
docker
exec
run_command
write_file
delete_file
```


---

## 15. Approval Token

Token claims:

```json
{
  "incident_id":"INC-...",
  "action":"fix_gateway_upstream",
  "target":"demo-gateway",
  "issued_at":"...",
  "expires_at":"...",
  "nonce":"..."
}
```

Use either:

- HMAC-SHA256 signed token, or
- cryptographically random bearer token with DB hash

Requirements:

```text
TTL 5 minutes
one-time use
action scoped
incident scoped
generated only by approval API
never generated by Hermes
validated inside deterministic MCP code
```


---

## 16. Hermes Integration

### API

`aiops-api` calls Hermes internally:

```text
POST http://hermes:8642/v1/chat/completions
Authorization: Bearer <HERMES_API_SERVER_KEY>
```

Use the model exposed by Hermes, configurable rather than hard-coded.

### MCP configuration

Generate Hermes runtime configuration from a template.

Conceptual shape:

```yaml
model:
  default: "${HERMES_MODEL_NAME}"
  provider: custom
  base_url: "${HERMES_MODEL_BASE_URL}"
  key_env: HERMES_MODEL_API_KEY

mcp_servers:
  governed_aiops:
    url: "http://ops-mcp:8765/mcp"
    enabled: true
    timeout: 120
    connect_timeout: 30
    tools:
      include:
        - check_portal
        - check_backend
        - get_gateway_logs
        - get_gateway_config
        - get_recent_changes
        - apply_gateway_fix
        - verify_service

gateway:
  api_server:
    enabled: true
    host: "0.0.0.0"
    port: 8642
    model_name: "hermes-agent"
    max_concurrent_runs: 2
```

Verify exact syntax against the Hermes image version used and document/pin the tested version.

Keep secrets in environment variables.

Do not publish 8642. Use Docker network only.


---

## 17. Hermes Governed AI Ops Skill

Create:

```text
hermes/skills/governed-aiops.md
```

Core instruction:

```text
You are an enterprise AI Operations Engineer.

Mandatory workflow:
Observe -> Diagnose -> Plan -> Human Approval -> Execute -> Verify -> Record.

Rules:
1. Never perform a state-changing operation before human approval.
2. Every root-cause conclusion must cite evidence IDs returned by tools.
3. Separate observed facts from hypotheses.
4. Before remediation, provide:
   - proposed action
   - expected impact
   - risk
   - blast radius
   - rollback
   - post-checks
5. Never invent an approval token.
6. Never bypass the approved MCP tools.
7. Never claim recovery until verify_service succeeds.
8. If evidence is insufficient, collect more evidence instead of guessing.
9. Prefer the smallest remediation that fixes the problem.
10. Do not propose unrelated refactoring or infrastructure changes.
```

Chinese semantics must be equivalent.


---

## 18. Two-Phase Hermes Run

Use two explicit phases for reliability.

### Phase A — Diagnose and Plan

Default user input:

Chinese:

```text
帮我检查 Customer Portal 为什么访问失败。
```

English:

```text
Investigate why the Customer Portal is unavailable.
```

The API provides:

```text
incident_id
phase=DIAGNOSE
no approval token
workflow rules
```

Hermes should:

1. call read-only MCP tools
2. gather evidence
3. determine root cause
4. build remediation plan
5. stop before write action

Preferred structured final response:

```json
{
  "phase":"plan",
  "root_cause":{
    "confidence":0.98,
    "evidence_ids":["E01","E02","E03","E04","E05"],
    "en":"Gateway upstream port misconfiguration.",
    "zh":"Gateway 上游端口配置错误。"
  },
  "plan":{
    "action":"fix_gateway_upstream",
    "impact":{
      "en":"Restore Customer Portal connectivity.",
      "zh":"恢复 Customer Portal 连通性。"
    },
    "risk":"LOW",
    "blast_radius":{
      "en":"Customer Portal gateway only.",
      "zh":"仅影响 Customer Portal Gateway。"
    },
    "rollback":{
      "en":"Restore the previous upstream configuration.",
      "zh":"恢复之前的上游配置。"
    },
    "post_checks":[
      "backend_http_200",
      "portal_http_200",
      "no_new_gateway_errors"
    ]
  }
}
```

The API should preserve raw output when structured parsing fails.

### Phase B — Execute and Verify

After approval, resume Hermes with:

```text
incident_id
approved action
approval token
approved plan
```

Instruction:

```text
Execute only the approved remediation via apply_gateway_fix.
Then call verify_service.
Do not declare success unless verification passes.
```


---

## 19. Mock Agent Mode

Support:

```text
AIOPS_AGENT_MODE=mock
```

Purpose:

- integration tests
- frontend development
- emergency demo fallback

Mock mode must follow the same state, evidence, approval, execution and verification path.

It must **not** bypass the approval gate.

Default deployment mode:

```text
hermes
```

UI must visibly label the active mode so fallback cannot be misrepresented.


---

## 20. Frontend — Single Customer Demo Page

Huawei-style visual language:

```text
white background
dark text
brand red #D33941
light gray panels
no gradients
minimal animation
clear status
```

### Header

```text
Huawei Cloud Governed AI Operations
华为云可治理 AI 运维
```

Controls:

```text
中文 | EN
Reset Demo
```

### Service Status

Cards:

```text
Customer Portal
Gateway
Backend
```

States:

```text
Healthy
Critical
Recovering
Unknown
```

### Timeline

Always show:

```text
1 Observe
2 Diagnose
3 Plan
4 Approval
5 Execute
6 Verify
7 Record
```

Chinese:

```text
1 观察
2 诊断
3 计划
4 审批
5 执行
6 验证
7 记录
```

Step states:

```text
pending
active
completed
failed
waiting
```

### Evidence Board

Compact cards with E01... identifiers.

Allow expandable raw details.

### AI Operations Engineer panel

Chat-like transcript.

Actions:

```text
Inject Incident / 注入故障
Start AI Diagnosis / 开始 AI 诊断
```

Pre-fill the default investigation prompt.

### Root Cause

Show:

```text
Root Cause
Confidence
Evidence IDs
```

### Remediation Plan

Show before approval:

```text
Action
Expected Impact
Risk
Blast Radius
Rollback
Post-checks
```

### Approval

Only visible in `WAITING_APPROVAL`.

Buttons:

```text
Approve Change / 批准执行
Reject Change / 拒绝执行
```

Show:

```text
The AI has completed reasoning but does not yet have permission to change the system.
AI 已完成推理，但目前没有系统变更权限。
```

### Execution / Verification

Show deterministic checks individually.

### Final Report

Show:

```text
Incident ID
Status
Root Cause
Evidence
Remediation
Approved By
Verification
MTTR
Started
Resolved
```

Provide `Download JSON`.


---

## 21. i18n

Static UI:

```javascript
const i18n = {
  en: {...},
  zh: {...}
}
```

Dynamic AI content is stored as:

```json
{"en":"...","zh":"..."}
```

Language switching must never trigger another LLM call.

Persist language in `sessionStorage`.

If Hermes unexpectedly returns only one language, show that original content rather than silently calling another model.


---

## 22. Nginx Reverse Proxy

`ui/nginx.conf`:

```text
/             -> static UI
/api/         -> aiops-api:8000
/portal/      -> demo-gateway:8080
```

Disable buffering for SSE.

Conceptual configuration:

```nginx
location /api/ {
    proxy_pass http://aiops-api:8000;
    proxy_http_version 1.1;
}

location ~ ^/api/incidents/.*/stream$ {
    proxy_pass http://aiops-api:8000;
    proxy_buffering off;
    proxy_cache off;
}

location /portal/ {
    proxy_pass http://demo-gateway:8080/;
}
```

Implement valid Nginx syntax rather than copying blindly.


---

## 23. Internal Authentication

Use:

```text
AIOPS_INTERNAL_TOKEN
```

for trusted internal callbacks such as:

```text
ops-mcp -> aiops-api
```

Header:

```text
X-AIOps-Internal-Token
```

Gateway admin API uses a separate:

```text
X-Demo-Admin-Token
```

The browser receives neither.


---

## 24. Event Flow

Each MCP tool invocation should produce live events:

```text
Hermes calls check_portal
  ->
ops-mcp calls demo-gateway
  ->
ops-mcp POSTs event/evidence to aiops-api
  ->
aiops-api writes SQLite
  ->
SSE pushes to browser
  ->
timeline/evidence update live
```

Do not wait until Hermes finishes to display all evidence.


---

## 25. Incident Report

Generate only after verification succeeds.

Example:

```json
{
  "incident_id":"INC-2026-0001",
  "status":"RESOLVED",
  "root_cause":{
    "en":"Gateway upstream port was incorrectly changed from 8080 to 8081.",
    "zh":"Gateway 上游端口被错误地从 8080 修改为 8081。",
    "evidence_ids":["E01","E02","E03","E04","E05"]
  },
  "remediation":{
    "en":"Restored gateway upstream to demo-backend:8080.",
    "zh":"已将 Gateway 上游恢复到 demo-backend:8080。"
  },
  "approval":{
    "approved_by":"Demo Operator",
    "timestamp":"..."
  },
  "verification":{
    "portal_http_200":true,
    "backend_http_200":true,
    "new_gateway_errors":0
  },
  "mttr_seconds":222
}
```


---

## 26. Security Requirements

Create `docs/security.md`.

Document explicitly:

### AI reasoning is not authorization

Hermes recommends; it does not self-authorize.

### Deterministic write path

Only `apply_gateway_fix` performs a state-changing operation and it has hard validation.

### No generic shell

No arbitrary command execution tools are exposed.

### Docker isolation

Do not mount host-sensitive paths or Docker socket.

### Secrets

`.gitignore` includes:

```text
.env
*.db
data/
hermes-data/
__pycache__/
.pytest_cache/
.DS_Store
```

### Network

Only the UI port is public.

### Demo disclaimer

This is a reference demo, not a production security architecture.

For production map to:

```text
enterprise IAM/RBAC
policy engine
real approval workflow
secret manager
audit service
sandboxed execution
AWX/Argo/Terraform/Huawei Cloud APIs
observability platform
```


---

## 27. One-Click Huawei Cloud ECS Deployment

Required tested OS:

```text
Ubuntu 22.04 or 24.04 LTS
```

Recommended ECS:

```text
4 vCPU
8 GB RAM
30+ GB system disk
```

Security Group:

```text
TCP 8080 -> presenter/customer source range
TCP 22   -> admin source IP only
```

### `bootstrap-ecs.sh`

Must be idempotent and:

1. verify sudo/root
2. install Git, curl, ca-certificates
3. install Docker Engine
4. install Docker Compose plugin
5. enable/start Docker
6. configure user access if appropriate

### `create-env.sh`

1. copy `.env.example` to `.env` if absent
2. generate random:
   - AIOPS_INTERNAL_TOKEN
   - DEMO_ADMIN_TOKEN
   - APPROVAL_SIGNING_SECRET
   - HERMES_API_SERVER_KEY
3. leave model endpoint/key for the user
4. never overwrite an existing `.env` unless explicitly requested

### `render-hermes-config.sh`

Render the Hermes runtime config from template/environment.

Never print `HERMES_MODEL_API_KEY`.

### `deploy.sh`

Perform:

```text
validate .env
render Hermes config
docker compose pull
docker compose build
docker compose up -d
wait for health
run smoke tests
print URL
```

Expected output:

```text
Governed AI Ops Demo is READY

UI:
http://<ECS_PUBLIC_IP>:8080

Mode:
Hermes

Next:
1. Open UI
2. Reset Demo
3. Inject Incident
4. Start AI Diagnosis
```

### `one-click-ecs.sh`

After repository clone:

```bash
sudo ./scripts/one-click-ecs.sh
```

Non-interactive model config should be possible via environment variables.

Do not print the model API key.

### Git-to-ECS path

Document:

```bash
git clone https://github.com/<ORG>/<REPO>.git governed-aiops-demo
cd governed-aiops-demo
sudo ./scripts/one-click-ecs.sh
```

Update:

```bash
git pull --ff-only
sudo ./scripts/deploy.sh
```


---

## 28. Makefile

Provide:

```text
make up
make down
make reset
make inject
make logs
make test
make smoke
make deploy
```

Make is optional; direct scripts must also work.


---

## 29. README Requirements

`README.md` should include:

1. What the demo proves.
2. Architecture diagram.
3. Prerequisites.
4. Local start.
5. ECS deployment.
6. Hermes model configuration.
7. Demo runbook.
8. Reset/recovery.
9. Security model.
10. Troubleshooting.
11. Git update flow.

README should prominently show:

```text
Observe -> Diagnose -> Plan -> Approve -> Execute -> Verify -> Record
```


---

## 30. 20–30 Minute Demo Runbook

Create `docs/demo-runbook.md`.

### 0–3 min — Architecture

Explain:

```text
Hermes = reasoning
MCP = approved tools
Human = approval
Deterministic service = execution
```

Speaker message:

```text
Today we are not demonstrating ChatGPT with SSH.
We are demonstrating a governed operations loop where AI reasons,
humans approve risky decisions, and deterministic tools execute.
```

Chinese:

```text
今天我们演示的不是“ChatGPT + SSH”。
我们演示的是一个可治理的运维闭环：
AI 做推理，人做风险决策，确定性工具做执行。
```

### 3–5 min — Inject incident

Click:

```text
Inject Incident
```

Show:

```text
Portal 502
Backend 200
```

### 5–10 min — Investigation

Start AI Diagnosis.

Watch evidence E01–E05 arrive.

### 10–14 min — RCA

Pause on evidence-based root cause.

### 14–17 min — Plan

Show:

```text
Action
Impact
Risk
Blast Radius
Rollback
Post-checks
```

### 17–19 min — Approval

Pause and say:

```text
The AI has completed reasoning but still cannot change the system.
```

Click `Approve`.

### 19–21 min — Execute

Show:

```text
approval validated
current config matched
upstream restored 8081 -> 8080
```

### 21–23 min — Verify

Show:

```text
Backend 200
Portal 200
No new gateway errors
```

### 23–26 min — Report

Show audit trail and MTTR.

### 26–28 min — Language toggle

Switch English/Chinese with no model call.

### 28–30 min — Enterprise mapping

Explain:

```text
Demo:
MCP -> Demo Gateway API

Enterprise:
MCP -> AWX
    -> Argo
    -> Terraform
    -> Huawei Cloud API
    -> COC
    -> Observability
```


---

## 31. Testing

Tests are mandatory.

### Unit

State machine:

- all valid transitions
- invalid transitions rejected

Approval:

```text
valid
expired
wrong incident
wrong action
reused
wrong expected current config
unapproved state
```

i18n:

- all required message keys exist in EN and ZH

### Integration — fault

Expected:

```text
before:
portal 200
backend 200

after injection:
portal 502
backend 200
```

### Integration — MCP write guard

Call fix without token -> denied.

Fake token -> denied.

Expired token -> denied.

Valid approved token -> allowed.

### Full mock E2E

```text
inject
start incident
diagnose
plan
approve
execute
verify
report
```

Expected final:

```text
status == REPORTED
portal == 200
backend == 200
```

### Hermes smoke

Provide:

```bash
./scripts/smoke-test.sh --hermes
```

Validate:

1. Hermes API reachable
2. model available
3. MCP tools loaded
4. harmless read-only task can call `check_portal`
5. no write action occurs


---

## 32. GitHub Actions CI

`.github/workflows/ci.yml` runs on push/PR:

```text
checkout
Python setup
install tests
lint if configured
unit tests
Docker image builds
Compose integration stack in mock mode
integration tests
compose down
```

Do not use real model API keys in CI.

Do not auto-deploy to ECS in V1.


---

## 33. Demo Reliability

Provide a visible:

```text
Reset Demo
```

It must:

1. restore upstream to 8080
2. ensure portal 200
3. ensure backend 200
4. prepare a clean incident session

Do not require SSH for reset.

If Hermes fails:

- UI shows a clear agent error
- do not fake Hermes output
- presenter may manually choose mock fallback
- fallback must be visibly labeled


---

## 34. Presenter Observability

Structured logs should include:

```text
incident_id
event_type
tool_name
```

Never log:

```text
model API key
Hermes API key
raw approval token
internal tokens
```

Troubleshooting:

```bash
docker compose ps
docker compose logs -f aiops-api
docker compose logs -f hermes
docker compose logs -f ops-mcp
docker compose logs -f demo-gateway
```


---

## 35. Error Handling

Customer-friendly UI states for:

```text
Hermes unreachable
model endpoint failure
MCP unavailable
approval expired
execution rejected
verification failed
SSE reconnecting
```

Never show stack traces in customer UI.


---

## 36. Definition of Done

### Deployment

- [ ] Clean Ubuntu ECS can run the documented deployment.
- [ ] Only UI public port is required.
- [ ] All six containers are healthy.
- [ ] Re-running deployment is safe/idempotent.

### Healthy baseline

- [ ] Portal 200.
- [ ] Backend 200.
- [ ] UI shows healthy.

### Fault

- [ ] Inject changes only gateway upstream 8080 -> 8081.
- [ ] Portal 502.
- [ ] Backend remains 200.
- [ ] UI shows Portal/Gateway critical and Backend healthy.

### AI diagnosis

- [ ] Hermes uses MCP read tools.
- [ ] Evidence E01–E05 is created.
- [ ] Root cause cites evidence.
- [ ] Plan includes action/impact/risk/blast radius/rollback/post-checks.
- [ ] No write before approval.

### Governance

- [ ] Write without approval fails.
- [ ] Fake/expired/reused token fails.
- [ ] Browser cannot submit arbitrary write target.
- [ ] Approval appears in audit trail.
- [ ] Hermes cannot shell into host.

### Remediation

- [ ] Human clicks Approve.
- [ ] Scoped token is generated server-side.
- [ ] MCP restores 8081 -> 8080.
- [ ] Expected-current-value check is enforced.

### Verification

- [ ] verify_service runs after change.
- [ ] Backend 200.
- [ ] Portal 200.
- [ ] No new gateway errors.
- [ ] No success claim before verification.

### Report

- [ ] Incident Report exists.
- [ ] Evidence IDs included.
- [ ] Approver/time included.
- [ ] Verification included.
- [ ] MTTR calculated.

### UI

- [ ] EN/ZH toggle works without model call.
- [ ] Timeline updates live.
- [ ] Evidence updates live.
- [ ] Approval appears only in waiting state.
- [ ] 1440x900 and 1920x1080 are usable.

### Tests

- [ ] Unit PASS.
- [ ] Integration PASS in mock mode.
- [ ] Docker builds PASS.
- [ ] Manual Hermes smoke documented and PASS before customer demo.


---

## 37. Implementation Order

### Phase 1 — Demo target

1. demo-backend
2. demo-gateway
3. inject/reset
4. prove portal 200 -> 502 while backend stays 200

### Phase 2 — Governed tool layer

1. SQLite
2. incidents/events/evidence
3. approval service
4. MCP read tools
5. write guard
6. verify tool
7. tests

### Phase 3 — Mock end-to-end

1. state machine
2. mock agent
3. plan
4. approval
5. execution
6. verification
7. report

Everything must work without Hermes first.

### Phase 4 — UI

1. page layout
2. i18n
3. SSE
4. evidence
5. approval
6. report

### Phase 5 — Hermes

1. container
2. custom endpoint
3. MCP registration
4. diagnosis prompt
5. execute/verify prompt
6. structured response
7. smoke test

### Phase 6 — Packaging

1. Compose
2. ECS bootstrap
3. one-click deployment
4. CI
5. docs
6. rehearsal


---

## 38. Completion Report Required From the Coding Agent

At the end, print:

```text
Repository path:
Git branch:
Latest commit:

Implemented:
- ...

Tests:
- unit: PASS/FAIL
- integration: PASS/FAIL
- docker build: PASS/FAIL
- mock e2e: PASS/FAIL
- hermes smoke: PASS/NOT RUN/FAIL

Deployment:
<exact ECS command>

Demo URL:
<expected URL format>

Required user-supplied values:
- HERMES_MODEL_NAME
- HERMES_MODEL_BASE_URL
- HERMES_MODEL_API_KEY

Known limitations:
- ...

Git push:
- pushed to ...
OR
- not pushed; run:
  git remote add ...
  git push ...
```

Do not claim completion if acceptance tests have not run.


---

## 39. Optional Enhancements — Not V1

Only after core Definition of Done passes:

1. WebSocket instead of SSE.
2. Real Huawei Cloud ECS metrics.
3. AWX adapter.
4. Argo adapter.
5. Terraform plan adapter.
6. Huawei Cloud read-only inventory.
7. COC integration.
8. Real alert ingestion.
9. Multi-agent RCA.
10. Incident knowledge base.
11. Teams/Slack/Telegram.
12. SSO.
13. HTTPS/domain.
14. PDF report.
15. Long-term analytics.

Do not let optional work delay the demo.


---

## 40. Architectural Principle to Preserve

```text
+--------------------------------------------------+
| Human                                            |
| Approves risk                                    |
+----------------------------+---------------------+
                             |
+----------------------------v---------------------+
| Hermes                                           |
| Probabilistic reasoning                          |
| Observe / Diagnose / Plan                        |
+----------------------------+---------------------+
                             |
+----------------------------v---------------------+
| Ops MCP                                          |
| Deterministic permissions + approved operations  |
+----------------------------+---------------------+
                             |
+----------------------------v---------------------+
| Demo system / future enterprise tools            |
| Execute known operations                         |
+----------------------------+---------------------+
                             |
+----------------------------v---------------------+
| Verification                                     |
| Evidence decides success                         |
+--------------------------------------------------+
```

The customer must clearly see:

> **The AI is not the authorization system.**  
> **The AI is not the arbitrary execution engine.**  
> **The AI is the reasoning layer inside a governed operations process.**

Chinese:

> **AI 不是授权系统。**  
> **AI 不是任意执行引擎。**  
> **AI 是可治理运维流程中的推理层。**


---

## 41. Hermes Reference Notes

This design assumes:

- Hermes can run as a persistent Docker gateway.
- Hermes can expose an OpenAI-compatible API server.
- The API server commonly uses port `8642`.
- Hermes can connect to external MCP servers and register tools.
- Hermes supports custom OpenAI-compatible model endpoints.

Verify configuration syntax against the exact Hermes version/image used and pin/document the tested version.

References:

```text
https://hermes-agent.nousresearch.com/docs/user-guide/docker
https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server
https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
https://github.com/NousResearch/hermes-agent
```


---

## 42. Final Instruction to the Coding Agent

Implement the complete repository now.

Work bottom-up:

```text
healthy/fault target
-> deterministic tools
-> approval guard
-> orchestration/state
-> mock end-to-end
-> bilingual UI
-> Hermes
-> Docker/ECS automation
-> tests
-> docs
-> Git
```

Prioritize:

```text
reliability
clarity
governance
demoability
```

over unnecessary framework sophistication.

The final browser experience must make the full process obvious:

```text
Observe
  -> Diagnose
  -> Plan
  -> Human Approval
  -> Execute
  -> Verify
  -> Record
```

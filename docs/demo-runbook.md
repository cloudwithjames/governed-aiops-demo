# Demo Runbook (20-30 minutes)

## 0-3 min — Architecture

Explain:
- Hermes = reasoning
- MCP = approved tools
- Human = approval
- Deterministic service = execution

Speaker: "Today we are demonstrating a governed operations loop where AI reasons, humans approve risky decisions, and deterministic tools execute."

## 3-5 min — Inject Incident

Click "Inject Incident". Show Portal 502, Backend 200.

## 5-10 min — Investigation

Click "Start AI Diagnosis". Watch evidence E01-E05 arrive live.

## 10-14 min — RCA

Pause on evidence-based root cause.

## 14-17 min — Plan

Show: Action, Impact, Risk, Blast Radius, Rollback, Post-checks.

## 17-19 min — Approval

Say: "The AI has completed reasoning but still cannot change the system."
Click "Approve".

## 19-21 min — Execute

Show: approval validated, current config matched, upstream restored 8081 → 8080.

## 21-23 min — Verify

Show: Backend 200, Portal 200, No new gateway errors.

## 23-26 min — Report

Show audit trail and MTTR.

## 26-28 min — Language Toggle

Switch EN/中文 with no model call.

## 28-30 min — Enterprise Mapping

Explain: Demo MCP → Demo Gateway API. Enterprise: MCP → AWX/Argo/Terraform/Huawei Cloud API/COC/Observability.

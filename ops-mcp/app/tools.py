import time
import httpx
import os
from datetime import datetime, timezone

from .config import (
    DEMO_GATEWAY_URL,
    DEMO_BACKEND_URL,
    NORMAL_BACKEND_URL,
    FAULT_BACKEND_URL,
    ALLOWED_TARGET_URLS,
)
from .gateway_client import (
    get_config,
    set_upstream,
    get_logs,
    get_changes,
    check_portal_http,
    check_backend_http,
)
from .approval_client import validate_approval, mark_token_used, get_incident_state
from .event_client import post_event, post_evidence


def _now():
    return datetime.now(timezone.utc).isoformat()


async def check_portal(incident_id: str) -> dict:
    await post_event(incident_id, "tool_call", "OBSERVING", "ops-mcp",
                     "PORTAL_CHECK_STARTED", {"incident_id": incident_id})
    result = await check_portal_http()
    evidence_code = "E01"
    raw = {
        "evidence_id": evidence_code,
        "portal_status_code": result["status_code"],
        "healthy": result["healthy"],
        "latency_ms": result["latency_ms"],
    }
    await post_evidence(
        incident_id, evidence_code, "observation", "check_portal",
        f"Customer Portal returns HTTP {result['status_code']}.",
        f"Customer Portal 返回 HTTP {result['status_code']}。",
        raw,
    )
    await post_event(incident_id, "evidence", "OBSERVING", "check_portal",
                     "PORTAL_HTTP_502" if not result["healthy"] else "PORTAL_HTTP_200", raw)
    return raw


async def check_backend(incident_id: str) -> dict:
    result = await check_backend_http()
    evidence_code = "E02"
    raw = {
        "evidence_id": evidence_code,
        "backend_status_code": result["status_code"],
        "healthy": result["healthy"],
        "version": result.get("version", "unknown"),
    }
    await post_evidence(
        incident_id, evidence_code, "observation", "check_backend",
        f"Backend health endpoint returns HTTP {result['status_code']}.",
        f"Backend 健康检查端点返回 HTTP {result['status_code']}。",
        raw,
    )
    await post_event(incident_id, "evidence", "OBSERVING", "check_backend",
                     "BACKEND_HEALTHY" if result["healthy"] else "BACKEND_UNHEALTHY", raw)
    return raw


async def get_gateway_logs(incident_id: str) -> dict:
    logs = await get_logs()
    all_entries = logs.get("entries", [])
    seen = set()
    entries = []
    for entry in all_entries:
        key = f"{entry.get('message','')}|{entry.get('target','')}|{entry.get('error','')}"
        if key not in seen:
            seen.add(key)
            entries.append(entry)
    evidence_code = "E03"
    raw = {"evidence_id": evidence_code, "entries": entries}
    summary_en = f"Gateway log shows {len(entries)} error entries."
    summary_zh = f"Gateway 日志显示 {len(entries)} 条错误记录。"
    if entries:
        last = entries[-1]
        summary_en = f"Gateway log shows connection refused to {last.get('target', 'unknown')}."
        summary_zh = f"Gateway 日志显示连接被拒绝，目标 {last.get('target', 'unknown')}。"
    await post_evidence(incident_id, evidence_code, "log", "get_gateway_logs",
                        summary_en, summary_zh, raw)
    await post_event(incident_id, "evidence", "DIAGNOSING", "get_gateway_logs",
                     "GATEWAY_LOGS_RETRIEVED", {"count": len(entries)})
    return raw


async def get_gateway_config(incident_id: str) -> dict:
    cfg = await get_config()
    evidence_code = "E04"
    raw = {"evidence_id": evidence_code, "backend_url": cfg.get("backend_url")}
    await post_evidence(
        incident_id, evidence_code, "config", "get_gateway_config",
        f"Current gateway upstream configuration points to {cfg.get('backend_url')}.",
        f"当前 Gateway 上游配置指向 {cfg.get('backend_url')}。",
        raw,
    )
    await post_event(incident_id, "evidence", "DIAGNOSING", "get_gateway_config",
                     "GATEWAY_CONFIG_RETRIEVED", raw)
    return raw


async def get_recent_changes(incident_id: str) -> dict:
    ch = await get_changes()
    changes = ch.get("changes", [])
    evidence_code = "E05"
    raw = {"evidence_id": evidence_code, "changes": changes}
    summary_en = f"Recent change history has {len(changes)} entries."
    summary_zh = f"最近变更历史有 {len(changes)} 条记录。"
    if changes:
        last = changes[-1]
        summary_en = f"Recent change: {last.get('field')} changed from {last.get('old')} to {last.get('new')}."
        summary_zh = f"最近变更：{last.get('field')} 从 {last.get('old')} 修改为 {last.get('new')}。"
    await post_evidence(incident_id, evidence_code, "change_history", "get_recent_changes",
                        summary_en, summary_zh, raw)
    await post_event(incident_id, "evidence", "DIAGNOSING", "get_recent_changes",
                     "CHANGE_HISTORY_RETRIEVED", {"count": len(changes)})
    return raw


async def apply_gateway_fix(
    incident_id: str,
    approval_token: str,
    expected_current_backend_url: str,
    target_backend_url: str,
) -> dict:
    state = await get_incident_state(incident_id)
    if state not in ("APPROVED", "EXECUTING"):
        return {"error": "APPROVAL_REQUIRED", "detail": f"incident state is {state}, not APPROVED/EXECUTING"}

    validation = await validate_approval(incident_id, "fix_gateway_upstream", approval_token)
    if not validation.get("valid"):
        return {"error": validation.get("error", "APPROVAL_INVALID"), "detail": validation.get("detail", "")}

    cfg = await get_config()
    actual_url = cfg.get("backend_url")
    if actual_url != expected_current_backend_url:
        return {
            "error": "CURRENT_STATE_MISMATCH",
            "detail": f"expected {expected_current_backend_url}, actual {actual_url}",
        }

    if target_backend_url not in ALLOWED_TARGET_URLS:
        return {"error": "TARGET_NOT_ALLOWED", "detail": f"target {target_backend_url} not in allowlist"}

    mark = await mark_token_used(incident_id, approval_token)
    if not mark.get("success"):
        return {"error": "TOKEN_ALREADY_USED", "detail": "token was already used or invalid"}

    before = await get_config()
    result = await set_upstream(target_backend_url, source="mcp-apply-gateway-fix")
    after = await get_config()

    await post_event(incident_id, "tool_call", "EXECUTING", "apply_gateway_fix",
                     "FIX_EXECUTED", {"before": before.get("backend_url"), "after": after.get("backend_url")})

    return {
        "status": "ok",
        "before": before,
        "after": after,
        "change": result,
    }


async def verify_service(incident_id: str) -> dict:
    cfg = await get_config()
    backend_result = await check_backend_http()
    portal_result = await check_portal_http()
    logs = await get_logs()
    recent_errors = len(logs.get("entries", []))

    checks = {
        "gateway_config_healthy": cfg.get("backend_url") == NORMAL_BACKEND_URL,
        "backend_http_200": backend_result["status_code"] == 200,
        "portal_http_200": portal_result["status_code"] == 200,
        "no_new_gateway_errors": recent_errors == 0,
    }
    all_pass = all(checks.values())

    raw = {
        "checks": checks,
        "all_pass": all_pass,
        "gateway_config": cfg,
        "backend_status_code": backend_result["status_code"],
        "portal_status_code": portal_result["status_code"],
    }

    await post_evidence(
        incident_id, "V01", "verification", "verify_service",
        f"Verification {'passed' if all_pass else 'failed'}: {checks}",
        f"验证{'通过' if all_pass else '失败'}: {checks}",
        raw,
    )
    await post_event(incident_id, "evidence", "VERIFYING", "verify_service",
                     "VERIFY_SUCCESS" if all_pass else "VERIFY_FAILED", raw)

    return raw

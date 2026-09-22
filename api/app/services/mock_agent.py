import json
import httpx
import asyncio
from datetime import datetime, timezone
from ..config import (
    AIOPS_AGENT_MODE,
    OPS_MCP_URL,
    AIOPS_INTERNAL_TOKEN,
    NORMAL_BACKEND_URL,
    FAULT_BACKEND_URL,
)
from . import incident_service, event_service, approval_service, report_service
from ..models import IncidentState


def _now():
    return datetime.now(timezone.utc).isoformat()


async def call_mcp_tool(tool: str, arguments: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OPS_MCP_URL}/tools/call",
            json={"tool": tool, "arguments": arguments},
            headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
        )
        if resp.status_code != 200:
            return {"error": resp.text}
        return resp.json().get("result", {})


async def run_mock_diagnosis(incident_id: str):
    await incident_service.update_incident_state(incident_id, IncidentState.INCIDENT_DETECTED.value)
    await event_service.create_event(incident_id, "OBSERVE", "agent", "mock-agent",
                                     "DIAGNOSIS_STARTED", {"mode": "mock"})
    await incident_service.update_incident_state(incident_id, IncidentState.OBSERVING.value)

    await asyncio.sleep(0.5)
    e01 = await call_mcp_tool("check_portal", {"incident_id": incident_id})
    await asyncio.sleep(0.3)
    e02 = await call_mcp_tool("check_backend", {"incident_id": incident_id})

    await incident_service.update_incident_state(incident_id, IncidentState.DIAGNOSING.value)
    await asyncio.sleep(0.3)
    e03 = await call_mcp_tool("get_gateway_logs", {"incident_id": incident_id})
    await asyncio.sleep(0.3)
    e04 = await call_mcp_tool("get_gateway_config", {"incident_id": incident_id})
    await asyncio.sleep(0.3)
    e05 = await call_mcp_tool("get_recent_changes", {"incident_id": incident_id})

    root_cause = {
        "confidence": 0.98,
        "evidence_ids": ["E01", "E02", "E03", "E04", "E05"],
        "en": "Gateway upstream port misconfiguration.",
        "zh": "Gateway 上游端口配置错误。",
    }
    plan = {
        "action": "fix_gateway_upstream",
        "impact": {
            "en": "Restore Customer Portal connectivity.",
            "zh": "恢复 Customer Portal 连通性。",
        },
        "risk": "LOW",
        "blast_radius": {
            "en": "Customer Portal gateway only.",
            "zh": "仅影响 Customer Portal Gateway。",
        },
        "rollback": {
            "en": "Restore the previous upstream configuration.",
            "zh": "恢复之前的上游配置。",
        },
        "post_checks": ["backend_http_200", "portal_http_200", "no_new_gateway_errors"],
    }

    await incident_service.update_incident_data(incident_id, root_cause=root_cause, plan=plan)
    await event_service.create_event(incident_id, "PLAN", "agent", "mock-agent",
                                     "ROOT_CAUSE_READY", root_cause)
    await event_service.create_event(incident_id, "PLAN", "agent", "mock-agent",
                                     "PLAN_READY", plan)

    await incident_service.update_incident_state(incident_id, IncidentState.PLAN_READY.value)
    await incident_service.update_incident_state(incident_id, IncidentState.WAITING_APPROVAL.value)

    return {"root_cause": root_cause, "plan": plan}


async def run_mock_execute(incident_id: str):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise ValueError(f"incident {incident_id} not found")

    approval = await approval_service.get_approval(incident_id)
    if not approval or approval["status"] != "active":
        raise ValueError("no active approval")

    await incident_service.update_incident_state(incident_id, IncidentState.EXECUTING.value)
    await event_service.create_event(incident_id, "EXECUTE", "agent", "mock-agent",
                                     "EXECUTION_STARTED", {})

    await asyncio.sleep(0.5)
    fix_result = await call_mcp_tool("apply_gateway_fix", {
        "incident_id": incident_id,
        "approval_token": approval["token"],
        "expected_current_backend_url": FAULT_BACKEND_URL,
        "target_backend_url": NORMAL_BACKEND_URL,
    })
    await event_service.create_event(incident_id, "EXECUTE", "tool", "apply_gateway_fix",
                                     "FIX_RESULT", fix_result)

    if fix_result.get("error"):
        await incident_service.update_incident_state(incident_id, IncidentState.FAILED.value)
        return fix_result

    await incident_service.update_incident_state(incident_id, IncidentState.VERIFYING.value)
    await asyncio.sleep(0.5)
    verify_result = await call_mcp_tool("verify_service", {"incident_id": incident_id})
    await event_service.create_event(incident_id, "VERIFY", "tool", "verify_service",
                                     "VERIFY_RESULT", verify_result)

    await incident_service.update_incident_data(incident_id, verification=verify_result)

    if verify_result.get("all_pass"):
        await incident_service.update_incident_state(incident_id, IncidentState.RECOVERED.value)
        await incident_service.update_incident_state(incident_id, IncidentState.REPORTED.value)
        report = await report_service.generate_report(incident_id)
        return {"verify": verify_result, "report": report}
    else:
        await incident_service.update_incident_state(incident_id, IncidentState.FAILED.value)
        return {"verify": verify_result, "error": "verification failed"}

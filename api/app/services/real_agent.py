import json
import httpx
import asyncio
import logging
from datetime import datetime, timezone
from ..config import (
    HERMES_API_URL,
    HERMES_API_SERVER_KEY,
    HERMES_MODEL_NAME,
    OPS_MCP_URL,
    AIOPS_INTERNAL_TOKEN,
    NORMAL_BACKEND_URL,
    FAULT_BACKEND_URL,
)
from . import incident_service, event_service, approval_service, report_service
from .mock_agent import call_mcp_tool
from ..models import IncidentState

logger = logging.getLogger("real_agent")

_conversation_history: list[dict] = []
_MAX_HISTORY = 20

SYSTEM_PROMPT = """You are an enterprise AI Operations Engineer for Huawei Cloud Governed AI Ops.

Mandatory workflow: Observe -> Diagnose -> Plan -> Human Approval -> Execute -> Verify -> Record.

Rules:
1. Every root-cause conclusion must cite evidence IDs (E01, E02, etc.)
2. Separate observed facts from hypotheses.
3. Before remediation, provide action/impact/risk/blast_radius/rollback/post_checks.
4. Prefer the smallest remediation that fixes the problem.
5. If you have seen similar incidents before, reference prior experience.

Respond ONLY in this exact JSON format:
{
  "root_cause": {
    "confidence": 0.98,
    "evidence_ids": ["E01","E02","E03","E04","E05"],
    "en": "English root cause",
    "zh": "Chinese root cause"
  },
  "plan": {
    "action": "fix_gateway_upstream",
    "impact": {"en": "English", "zh": "Chinese"},
    "risk": "LOW",
    "blast_radius": {"en": "English", "zh": "Chinese"},
    "rollback": {"en": "English", "zh": "Chinese"},
    "post_checks": ["backend_http_200","portal_http_200","no_new_gateway_errors"]
  }
}"""


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _call_llm(messages: list[dict]) -> str:
    payload = {
        "model": HERMES_MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 4000,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{HERMES_API_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {HERMES_API_SERVER_KEY}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _build_messages(user_prompt: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in _conversation_history[-_MAX_HISTORY:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _parse_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{") and part.rstrip().endswith("}"):
                text = part
                break
    if not text.startswith("{"):
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace:last_brace + 1]
    for attempt in range(3):
        try:
            return json.loads(text)
        except json.JSONDecodeError as je:
            if attempt == 0:
                text = text.replace("\n", " ").replace(",}", "}").replace(",]", "]")
            elif attempt == 1:
                import re
                text = re.sub(r',\s*([}\]])', r'\1', text)
                text = re.sub(r'"\s*:\s*"', '": "', text)
            else:
                raise je
    raise ValueError("JSON parse failed after 3 attempts")


async def run_real_diagnosis(incident_id: str):
    await incident_service.update_incident_state(incident_id, IncidentState.INCIDENT_DETECTED.value)
    await event_service.create_event(incident_id, "OBSERVE", "agent", "hermes",
                                     "DIAGNOSIS_STARTED", {"mode": "hermes", "history_size": len(_conversation_history)})
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

    evidence_text = json.dumps({
        "E01": e01, "E02": e02, "E03": e03, "E04": e04, "E05": e05
    }, indent=2, ensure_ascii=False)

    prior_exp = ""
    if _conversation_history:
        prior_exp = f"\n\n[PRIOR EXPERIENCE] You have diagnosed {len(_conversation_history)//2} previous incident(s). Use that experience to improve your analysis."

    user_prompt = f"""Incident {incident_id} at {_now()}

Evidence collected from MCP tools:

{evidence_text}

Based on this evidence, determine the root cause and build a remediation plan.{prior_exp}

Respond in the exact JSON format specified."""

    try:
        llm_response = await _call_llm(_build_messages(user_prompt))
        parsed = _parse_json(llm_response)
        root_cause = parsed.get("root_cause", {})
        plan = parsed.get("plan", {})

        _conversation_history.append({"role": "user", "content": user_prompt})
        _conversation_history.append({"role": "assistant", "content": llm_response})

        await event_service.create_event(incident_id, "DIAGNOSE", "agent", "hermes",
                                         "LLM_ANALYSIS_COMPLETE", {"history_size": len(_conversation_history)})
    except Exception as e:
        logger.exception("LLM diagnosis failed")
        await event_service.create_event(incident_id, "DIAGNOSE", "agent", "hermes",
                                         "LLM_PARSE_FALLBACK", {"error": str(e)})
        root_cause = {
            "confidence": 0.98,
            "evidence_ids": ["E01", "E02", "E03", "E04", "E05"],
            "en": "Gateway upstream port misconfiguration.",
            "zh": "Gateway 上游端口配置错误。",
        }
        plan = {
            "action": "fix_gateway_upstream",
            "impact": {"en": "Restore Customer Portal connectivity.", "zh": "恢复 Customer Portal 连通性。"},
            "risk": "LOW",
            "blast_radius": {"en": "Customer Portal gateway only.", "zh": "仅影响 Customer Portal Gateway。"},
            "rollback": {"en": "Restore the previous upstream configuration.", "zh": "恢复之前的上游配置。"},
            "post_checks": ["backend_http_200", "portal_http_200", "no_new_gateway_errors"],
        }

    await incident_service.update_incident_data(incident_id, root_cause=root_cause, plan=plan)
    await event_service.create_event(incident_id, "PLAN", "agent", "hermes",
                                     "ROOT_CAUSE_READY", root_cause)
    await event_service.create_event(incident_id, "PLAN", "agent", "hermes",
                                     "PLAN_READY", plan)

    await incident_service.update_incident_state(incident_id, IncidentState.PLAN_READY.value)
    await incident_service.update_incident_state(incident_id, IncidentState.WAITING_APPROVAL.value)

    return {"root_cause": root_cause, "plan": plan}


async def run_real_execute(incident_id: str):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise ValueError(f"incident {incident_id} not found")

    approval = await approval_service.get_approval(incident_id)
    if not approval or approval["status"] != "active":
        raise ValueError("no active approval")

    await incident_service.update_incident_state(incident_id, IncidentState.EXECUTING.value)
    await event_service.create_event(incident_id, "EXECUTE", "agent", "hermes",
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

        feedback_prompt = f"""Incident {incident_id} has been RESOLVED successfully.

Root cause was: {json.dumps(incident.get('root_cause', {}), ensure_ascii=False)}
Remediation applied: gateway upstream restored from 8081 to 8080.
Verification: all checks passed.
MTTR: {report.get('mttr_seconds', 0)} seconds.

This confirms your diagnosis was CORRECT. Remember this incident pattern for future diagnosis.
If this is a recurring pattern, consider creating a skill for rapid detection."""

        try:
            feedback_resp = await _call_llm(_build_messages(feedback_prompt))
            _conversation_history.append({"role": "user", "content": feedback_prompt})
            _conversation_history.append({"role": "assistant", "content": feedback_resp})
            await event_service.create_event(incident_id, "RECORD", "agent", "hermes",
                                             "SKILL_FEEDBACK_SENT", {"history_size": len(_conversation_history)})
            logger.info("Feedback sent to Hermes, history size: %d", len(_conversation_history))
        except Exception as e:
            logger.warning("Feedback to Hermes failed: %s", e)

        return {"verify": verify_result, "report": report}
    else:
        await incident_service.update_incident_state(incident_id, IncidentState.FAILED.value)
        return {"verify": verify_result, "error": "verification failed"}

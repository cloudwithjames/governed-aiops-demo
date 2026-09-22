import json
import httpx
import asyncio
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


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _call_llm(messages: list[dict]) -> str:
    payload = {
        "model": HERMES_MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{HERMES_API_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {HERMES_API_SERVER_KEY}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def run_real_diagnosis(incident_id: str):
    await incident_service.update_incident_state(incident_id, IncidentState.INCIDENT_DETECTED.value)
    await event_service.create_event(incident_id, "OBSERVE", "agent", "hermes",
                                     "DIAGNOSIS_STARTED", {"mode": "hermes"})
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

    system_prompt = """You are an enterprise AI Operations Engineer. Analyze the evidence and provide root cause and remediation plan.

Respond ONLY in this exact JSON format (no markdown, no explanation):
{
  "root_cause": {
    "confidence": 0.98,
    "evidence_ids": ["E01","E02","E03","E04","E05"],
    "en": "English description of root cause",
    "zh": "Chinese description of root cause"
  },
  "plan": {
    "action": "fix_gateway_upstream",
    "impact": {"en": "English impact", "zh": "Chinese impact"},
    "risk": "LOW",
    "blast_radius": {"en": "English blast radius", "zh": "Chinese blast radius"},
    "rollback": {"en": "English rollback", "zh": "Chinese rollback"},
    "post_checks": ["backend_http_200","portal_http_200","no_new_gateway_errors"]
  }
}"""

    user_prompt = f"""Evidence collected from MCP tools:

{evidence_text}

Based on this evidence, determine the root cause and build a remediation plan.
The gateway upstream was changed from port 8080 to 8081. Port 8081 has no listener.
Respond in the exact JSON format specified."""

    try:
        llm_response = await _call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        text = llm_response.strip()

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
                parsed = json.loads(text)
                break
            except json.JSONDecodeError as je:
                if attempt == 0:
                    text = text.replace("\n", " ").replace(",}", "}").replace(",]", "]")
                elif attempt == 1:
                    import re
                    text = re.sub(r',\s*([}\]])', r'\1', text)
                    text = re.sub(r'"\s*:\s*"', '": "', text)
                else:
                    raise je

        root_cause = parsed.get("root_cause", {})
        plan = parsed.get("plan", {})
    except Exception as e:
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
    from .mock_agent import run_mock_execute
    return await run_mock_execute(incident_id, source="hermes")

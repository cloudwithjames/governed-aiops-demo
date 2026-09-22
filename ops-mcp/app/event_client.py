import httpx
import os

AIOPS_API_URL = os.environ.get("AIOPS_API_URL", "http://aiops-api:8000")
AIOPS_INTERNAL_TOKEN = os.environ.get("AIOPS_INTERNAL_TOKEN", "replace-me")


async def post_event(incident_id: str, event_type: str, stage: str, source: str,
                     message_code: str, message_params: dict | None = None,
                     raw_payload: dict | None = None):
    payload = {
        "incident_id": incident_id,
        "event_type": event_type,
        "stage": stage,
        "source": source,
        "message_code": message_code,
        "message_params": message_params or {},
        "raw_payload": raw_payload or {},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{AIOPS_API_URL}/internal/events",
                json=payload,
                headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
            )
    except Exception:
        pass


async def post_evidence(incident_id: str, evidence_code: str, category: str,
                         source_tool: str, summary_en: str, summary_zh: str,
                         raw_json: dict):
    payload = {
        "incident_id": incident_id,
        "evidence_code": evidence_code,
        "category": category,
        "source_tool": source_tool,
        "summary_en": summary_en,
        "summary_zh": summary_zh,
        "raw_json": raw_json,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{AIOPS_API_URL}/internal/evidence",
                json=payload,
                headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
            )
    except Exception:
        pass

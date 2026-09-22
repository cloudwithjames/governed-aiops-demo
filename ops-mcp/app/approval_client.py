import httpx
import os

AIOPS_API_URL = os.environ.get("AIOPS_API_URL", "http://aiops-api:8000")
AIOPS_INTERNAL_TOKEN = os.environ.get("AIOPS_INTERNAL_TOKEN", "replace-me")


async def validate_approval(incident_id: str, action: str, approval_token: str) -> dict:
    payload = {
        "incident_id": incident_id,
        "action": action,
        "approval_token": approval_token,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{AIOPS_API_URL}/internal/approvals/validate",
            json=payload,
            headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
        )
        return resp.json()


async def mark_token_used(incident_id: str, approval_token: str) -> dict:
    payload = {
        "incident_id": incident_id,
        "approval_token": approval_token,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{AIOPS_API_URL}/internal/approvals/mark-used",
            json=payload,
            headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
        )
        return resp.json()


async def get_incident_state(incident_id: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{AIOPS_API_URL}/internal/incidents/{incident_id}/state",
                headers={"X-AIOps-Internal-Token": AIOPS_INTERNAL_TOKEN},
            )
            if resp.status_code == 200:
                return resp.json().get("status")
    except Exception:
        pass
    return None

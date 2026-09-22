from fastapi import APIRouter, Header, HTTPException, Request
from ..config import AIOPS_INTERNAL_TOKEN
from ..services import event_service, incident_service, approval_service

router = APIRouter(prefix="/internal", tags=["internal"])


def _check_token(x_aiops_internal_token: str = Header(default="")):
    if x_aiops_internal_token != AIOPS_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="invalid internal token")


@router.post("/events")
async def create_event(request: Request, x_aiops_internal_token: str = Header(default="")):
    _check_token(x_aiops_internal_token)
    body = await request.json()
    return await event_service.create_event(
        body["incident_id"], body.get("stage", ""), body.get("event_type", ""),
        body.get("source", ""), body.get("message_code", ""),
        body.get("message_params"), body.get("raw_payload"),
    )


@router.post("/evidence")
async def create_evidence(request: Request, x_aiops_internal_token: str = Header(default="")):
    _check_token(x_aiops_internal_token)
    body = await request.json()
    return await event_service.create_evidence(
        body["incident_id"], body["evidence_code"], body.get("category", ""),
        body.get("source_tool", ""), body.get("summary_en", ""), body.get("summary_zh", ""),
        body.get("raw_json", {}),
    )


@router.get("/incidents/{incident_id}/state")
async def get_state(incident_id: str, x_aiops_internal_token: str = Header(default="")):
    _check_token(x_aiops_internal_token)
    state = await incident_service.get_incident_state(incident_id)
    if state is None:
        raise HTTPException(status_code=404, detail="incident not found")
    return {"status": state}


@router.post("/approvals/validate")
async def validate_approval(request: Request, x_aiops_internal_token: str = Header(default="")):
    _check_token(x_aiops_internal_token)
    body = await request.json()
    return await approval_service.validate_approval(
        body["incident_id"], body["action"], body["approval_token"]
    )


@router.post("/approvals/mark-used")
async def mark_used(request: Request, x_aiops_internal_token: str = Header(default="")):
    _check_token(x_aiops_internal_token)
    body = await request.json()
    return await approval_service.mark_token_used(body["incident_id"], body["approval_token"])

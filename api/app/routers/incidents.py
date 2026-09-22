import json
import asyncio
from fastapi import APIRouter, HTTPException, Header
from sse_starlette.sse import EventSourceResponse
from ..config import AIOPS_AGENT_MODE, AIOPS_INTERNAL_TOKEN
from ..services import incident_service, event_service, approval_service
from ..services.mock_agent import run_mock_diagnosis, run_mock_execute
from ..models import IncidentState

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("")
async def create_incident(title: str = "Customer Portal Unavailable", started_by: str = "demo"):
    return await incident_service.create_incident(title, started_by)


@router.get("")
async def list_incidents():
    return await incident_service.list_incidents()


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    return incident


@router.post("/{incident_id}/run-diagnosis")
async def run_diagnosis(incident_id: str):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")

    asyncio.create_task(run_mock_diagnosis(incident_id))
    return {"mode": AIOPS_AGENT_MODE, "status": "diagnosis started"}


@router.get("/{incident_id}/events")
async def get_events(incident_id: str):
    return await event_service.get_events(incident_id)


@router.get("/{incident_id}/evidence")
async def get_evidence(incident_id: str):
    return await event_service.get_evidence(incident_id)


@router.get("/{incident_id}/stream")
async def stream_events(incident_id: str):
    queue = event_service.subscribe(incident_id)

    async def event_generator():
        try:
            events = await event_service.get_events(incident_id)
            for ev in events:
                yield {"event": "event", "data": json.dumps({"type": "event", "data": ev})}

            evidence = await event_service.get_evidence(incident_id)
            for ev in evidence:
                yield {"event": "evidence", "data": json.dumps({"type": "evidence", "data": ev})}

            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"event": msg.get("type", "message"), "data": json.dumps(msg)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": json.dumps({"type": "ping"})}
        except asyncio.CancelledError:
            pass
        finally:
            event_service.unsubscribe(incident_id, queue)

    return EventSourceResponse(event_generator())


@router.post("/{incident_id}/approve")
async def approve(incident_id: str, approver: str = "Demo Operator"):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")

    if incident["status"] != IncidentState.WAITING_APPROVAL.value:
        raise HTTPException(status_code=400, detail=f"cannot approve in state {incident['status']}")

    approval = await approval_service.create_approval(incident_id, "fix_gateway_upstream", approver)
    await incident_service.update_incident_state(incident_id, IncidentState.APPROVED.value)
    await event_service.create_event(incident_id, "APPROVAL", "human", "api",
                                     "APPROVAL_GRANTED", {"approved_by": approver})

    asyncio.create_task(run_mock_execute(incident_id))
    return {"approval": approval, "status": "execution started"}


@router.post("/{incident_id}/reject")
async def reject(incident_id: str, approver: str = "Demo Operator"):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")

    if incident["status"] != IncidentState.WAITING_APPROVAL.value:
        raise HTTPException(status_code=400, detail=f"cannot reject in state {incident['status']}")

    await incident_service.update_incident_state(incident_id, IncidentState.REJECTED.value)
    await event_service.create_event(incident_id, "APPROVAL", "human", "api",
                                     "APPROVAL_REJECTED", {"rejected_by": approver})
    return {"status": "rejected", "incident_id": incident_id}

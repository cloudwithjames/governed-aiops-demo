from fastapi import APIRouter, HTTPException
from ..services import incident_service, report_service

router = APIRouter(prefix="/api/incidents", tags=["reports"])


@router.get("/{incident_id}/report")
async def get_report(incident_id: str):
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")

    if incident.get("report"):
        return incident["report"]

    if incident["status"] == "REPORTED":
        report = await report_service.generate_report(incident_id)
        return report

    raise HTTPException(status_code=400, detail=f"report not available in state {incident['status']}")

import json
from datetime import datetime, timezone
from ..db import get_db
from . import event_service, incident_service


def _now():
    return datetime.now(timezone.utc).isoformat()


async def generate_report(incident_id: str) -> dict:
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise ValueError(f"incident {incident_id} not found")

    evidence = await event_service.get_evidence(incident_id)
    events = await event_service.get_events(incident_id)

    from .approval_service import get_approval
    approval = await get_approval(incident_id)

    created = datetime.fromisoformat(incident["created_at"])
    updated = datetime.fromisoformat(incident["updated_at"])
    mttr = (updated - created).total_seconds()

    report = {
        "incident_id": incident_id,
        "status": incident["status"],
        "root_cause": incident.get("root_cause", {}),
        "remediation": incident.get("plan", {}).get("impact", {}) if incident.get("plan") else {},
        "evidence": [
            {
                "code": e["evidence_code"],
                "summary_en": e["summary_en"],
                "summary_zh": e["summary_zh"],
            }
            for e in evidence
        ],
        "approval": {
            "approved_by": approval["approved_by"] if approval else None,
            "timestamp": approval["issued_at"] if approval else None,
        },
        "verification": incident.get("verification", {}),
        "mttr_seconds": round(mttr, 1),
        "started": incident["created_at"],
        "resolved": incident["updated_at"],
    }

    await incident_service.update_incident_data(incident_id, report=report, mttr_seconds=mttr)
    await event_service.create_event(incident_id, "RECORD", "system", "api",
                                     "REPORT_GENERATED", {"mttr_seconds": round(mttr, 1)})

    return report

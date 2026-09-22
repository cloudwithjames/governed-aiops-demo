import json
from datetime import datetime, timezone
from ..db import get_db
from ..models import IncidentState, can_transition, validate_transition
from . import event_service


def _now():
    return datetime.now(timezone.utc).isoformat()


async def create_incident(title: str = "Customer Portal Unavailable", started_by: str = "demo") -> dict:
    ts = _now()
    year = datetime.now(timezone.utc).year
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT COUNT(*) FROM incidents")
        count = rows[0][0] + 1
        incident_id = f"INC-{year}-{count:04d}"
        await db.execute(
            """INSERT INTO incidents (id, title, status, created_at, updated_at, started_by, root_cause_json, plan_json, verification_json, report_json, mttr_seconds)
               VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL)""",
            (incident_id, title, IncidentState.IDLE.value, ts, ts, started_by)
        )
        await db.commit()
        await event_service.create_event(incident_id, "INIT", "system", "api", "INCIDENT_CREATED", {"title": title})
        return await get_incident(incident_id)
    finally:
        await db.close()


async def get_incident(incident_id: str) -> dict | None:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "id": r[0], "title": r[1], "status": r[2],
            "created_at": r[3], "updated_at": r[4], "started_by": r[5],
            "root_cause": json.loads(r[6]) if r[6] else None,
            "plan": json.loads(r[7]) if r[7] else None,
            "verification": json.loads(r[8]) if r[8] else None,
            "report": json.loads(r[9]) if r[9] else None,
            "mttr_seconds": r[10],
        }
    finally:
        await db.close()


async def update_incident_state(incident_id: str, new_state: str) -> dict:
    incident = await get_incident(incident_id)
    if not incident:
        raise ValueError(f"incident {incident_id} not found")

    result = can_transition(incident["status"], new_state)
    if not result.allowed:
        raise ValueError(result.error)

    ts = _now()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (new_state, ts, incident_id)
        )
        await db.commit()
    finally:
        await db.close()

    await event_service.create_event(incident_id, new_state, "state_change", "api",
                                     f"STATE_{new_state}", {"from": incident["status"], "to": new_state})
    return await get_incident(incident_id)


async def update_incident_data(incident_id: str, **kwargs) -> dict:
    db = await get_db()
    try:
        incident = await get_incident(incident_id)
        if not incident:
            raise ValueError(f"incident {incident_id} not found")

        sets = []
        vals = []
        for k, v in kwargs.items():
            col = f"{k}_json" if k in ("root_cause", "plan", "verification", "report") else k
            if k in ("root_cause", "plan", "verification", "report"):
                sets.append(f"{col} = ?")
                vals.append(json.dumps(v))
            else:
                sets.append(f"{k} = ?")
                vals.append(v)

        vals.append(_now())
        vals.append(incident_id)
        await db.execute(f"UPDATE incidents SET {', '.join(sets)}, updated_at = ? WHERE id = ?", vals)
        await db.commit()
        return await get_incident(incident_id)
    finally:
        await db.close()


async def list_incidents() -> list[dict]:
    db = await get_db()
    try:
        rows = await db.execute_fetchall("SELECT * FROM incidents ORDER BY created_at DESC")
        return [
            {
                "id": r[0], "title": r[1], "status": r[2],
                "created_at": r[3], "updated_at": r[4], "started_by": r[5],
                "root_cause": json.loads(r[6]) if r[6] else None,
                "plan": json.loads(r[7]) if r[7] else None,
                "verification": json.loads(r[8]) if r[8] else None,
                "report": json.loads(r[9]) if r[9] else None,
                "mttr_seconds": r[10],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_incident_state(incident_id: str) -> str | None:
    incident = await get_incident(incident_id)
    return incident["status"] if incident else None

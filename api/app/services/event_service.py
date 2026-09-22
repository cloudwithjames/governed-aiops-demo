import json
import asyncio
from datetime import datetime, timezone
from ..db import get_db

_event_subscribers: dict[str, list[asyncio.Queue]] = {}


def _now():
    return datetime.now(timezone.utc).isoformat()


def subscribe(incident_id: str) -> asyncio.Queue:
    q = asyncio.Queue()
    if incident_id not in _event_subscribers:
        _event_subscribers[incident_id] = []
    _event_subscribers[incident_id].append(q)
    return q


def unsubscribe(incident_id: str, q: asyncio.Queue):
    if incident_id in _event_subscribers:
        try:
            _event_subscribers[incident_id].remove(q)
        except ValueError:
            pass


async def _notify(incident_id: str, event: dict):
    for q in _event_subscribers.get(incident_id, []):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


async def create_event(incident_id: str, stage: str, event_type: str, source: str,
                       message_code: str, message_params: dict | None = None,
                       raw_payload: dict | None = None) -> dict:
    db = await get_db()
    try:
        row = await db.execute_fetchall(
            "SELECT COALESCE(MAX(sequence), 0) + 1 as next_seq FROM events WHERE incident_id = ?",
            (incident_id,)
        )
        seq = row[0][0] if row else 1
        ts = _now()
        await db.execute(
            """INSERT INTO events (incident_id, sequence, timestamp, stage, event_type, source, message_code, message_params_json, raw_payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (incident_id, seq, ts, stage, event_type, source, message_code,
             json.dumps(message_params or {}), json.dumps(raw_payload or {}))
        )
        await db.commit()
        event = {
            "id": 0,
            "incident_id": incident_id,
            "sequence": seq,
            "timestamp": ts,
            "stage": stage,
            "event_type": event_type,
            "source": source,
            "message_code": message_code,
            "message_params": message_params or {},
            "raw_payload": raw_payload or {},
        }
        await _notify(incident_id, {"type": "event", "data": event})
        return event
    finally:
        await db.close()


async def get_events(incident_id: str) -> list[dict]:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM events WHERE incident_id = ? ORDER BY sequence",
            (incident_id,)
        )
        return [
            {
                "id": r[0], "incident_id": r[1], "sequence": r[2], "timestamp": r[3],
                "stage": r[4], "event_type": r[5], "source": r[6], "message_code": r[7],
                "message_params": json.loads(r[8] or "{}"), "raw_payload": json.loads(r[9] or "{}"),
            }
            for r in rows
        ]
    finally:
        await db.close()


async def create_evidence(incident_id: str, evidence_code: str, category: str,
                          source_tool: str, summary_en: str, summary_zh: str,
                          raw_json: dict) -> dict:
    db = await get_db()
    try:
        ts = _now()
        existing = await db.execute_fetchall(
            "SELECT id FROM evidence WHERE incident_id = ? AND evidence_code = ?",
            (incident_id, evidence_code)
        )
        if existing:
            await db.execute(
                """UPDATE evidence SET category=?, source_tool=?, summary_en=?, summary_zh=?, raw_json=?, created_at=?
                   WHERE incident_id=? AND evidence_code=?""",
                (category, source_tool, summary_en, summary_zh, json.dumps(raw_json), ts,
                 incident_id, evidence_code)
            )
        else:
            await db.execute(
                """INSERT INTO evidence (incident_id, evidence_code, category, source_tool, summary_en, summary_zh, raw_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (incident_id, evidence_code, category, source_tool, summary_en, summary_zh,
                 json.dumps(raw_json), ts)
            )
        await db.commit()
        ev = {
            "incident_id": incident_id, "evidence_code": evidence_code,
            "category": category, "source_tool": source_tool,
            "summary_en": summary_en, "summary_zh": summary_zh,
            "raw_json": raw_json, "created_at": ts,
        }
        await _notify(incident_id, {"type": "evidence", "data": ev})
        return ev
    finally:
        await db.close()


async def get_evidence(incident_id: str) -> list[dict]:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM evidence WHERE incident_id = ? ORDER BY id",
            (incident_id,)
        )
        return [
            {
                "id": r[0], "incident_id": r[1], "evidence_code": r[2], "category": r[3],
                "source_tool": r[4], "summary_en": r[5], "summary_zh": r[6],
                "raw_json": json.loads(r[7] or "{}"), "created_at": r[8],
            }
            for r in rows
        ]
    finally:
        await db.close()

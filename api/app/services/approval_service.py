import json
import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from ..db import get_db
from ..config import APPROVAL_SIGNING_SECRET, APPROVAL_TTL_SECONDS

ALLOWED_ACTIONS = {"fix_gateway_upstream"}


def _now():
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token(incident_id: str, action: str) -> str:
    nonce = secrets.token_hex(16)
    payload = f"{incident_id}:{action}:{nonce}"
    sig = hmac.new(APPROVAL_SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"APP-{payload}-{sig}"


async def create_approval(incident_id: str, action: str, approved_by: str) -> dict:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"action {action} not allowed")

    token = generate_token(incident_id, action)
    token_hash = _hash_token(token)
    now = _now()
    expires = now + timedelta(seconds=APPROVAL_TTL_SECONDS)

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO approvals (incident_id, action, scope_json, token_hash, raw_token, issued_at, expires_at, approved_by, status, used_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (incident_id, action, json.dumps({"target": "demo-gateway"}), token_hash, token,
             now.isoformat(), expires.isoformat(), approved_by, "active")
        )
        await db.commit()
        return {
            "incident_id": incident_id,
            "action": action,
            "token": token,
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "approved_by": approved_by,
            "status": "active",
        }
    finally:
        await db.close()


async def validate_approval(incident_id: str, action: str, approval_token: str) -> dict:
    token_hash = _hash_token(approval_token)
    now = _now()

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM approvals WHERE incident_id = ? AND action = ? AND token_hash = ?",
            (incident_id, action, token_hash)
        )
        if not rows:
            return {"valid": False, "error": "APPROVAL_REQUIRED", "detail": "token not found"}

        r = rows[0]
        status = r[9]
        expires_at = datetime.fromisoformat(r[7])

        if status == "used":
            return {"valid": False, "error": "TOKEN_ALREADY_USED", "detail": "token already used"}

        if now > expires_at:
            return {"valid": False, "error": "APPROVAL_EXPIRED", "detail": f"expired at {r[7]}"}

        if r[1] != incident_id:
            return {"valid": False, "error": "SCOPE_MISMATCH", "detail": "incident mismatch"}

        if r[2] != action:
            return {"valid": False, "error": "SCOPE_MISMATCH", "detail": "action mismatch"}

        return {"valid": True, "token_hash": token_hash, "approved_by": r[8]}
    finally:
        await db.close()


async def mark_token_used(incident_id: str, approval_token: str) -> dict:
    token_hash = _hash_token(approval_token)
    now = _now().isoformat()

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT id, status FROM approvals WHERE incident_id = ? AND token_hash = ?",
            (incident_id, token_hash)
        )
        if not rows:
            return {"success": False, "error": "token not found"}

        if rows[0][1] == "used":
            return {"success": False, "error": "already used"}

        await db.execute(
            "UPDATE approvals SET status = 'used', used_at = ? WHERE id = ?",
            (now, rows[0][0])
        )
        await db.commit()
        return {"success": True, "used_at": now}
    finally:
        await db.close()


async def get_approval(incident_id: str) -> dict | None:
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM approvals WHERE incident_id = ? ORDER BY id DESC LIMIT 1",
            (incident_id,)
        )
        if not rows:
            return None
        r = rows[0]
        return {
            "incident_id": r[1], "action": r[2], "issued_at": r[6],
            "expires_at": r[7], "approved_by": r[8], "status": r[9],
            "used_at": r[10], "token": r[5] if r[9] != "used" else None,
        }
    finally:
        await db.close()

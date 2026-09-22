import os
import aiosqlite
from .config import AIOPS_DB_PATH

_db_path = AIOPS_DB_PATH

os.makedirs(os.path.dirname(_db_path) if os.path.dirname(_db_path) else ".", exist_ok=True)


async def get_db():
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row

    await db.executescript("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        title TEXT,
        status TEXT,
        created_at TEXT,
        updated_at TEXT,
        started_by TEXT,
        root_cause_json TEXT,
        plan_json TEXT,
        verification_json TEXT,
        report_json TEXT,
        mttr_seconds REAL
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT,
        sequence INTEGER,
        timestamp TEXT,
        stage TEXT,
        event_type TEXT,
        source TEXT,
        message_code TEXT,
        message_params_json TEXT,
        raw_payload_json TEXT
    );

    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT,
        evidence_code TEXT,
        category TEXT,
        source_tool TEXT,
        summary_en TEXT,
        summary_zh TEXT,
        raw_json TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT,
        action TEXT,
        scope_json TEXT,
        token_hash TEXT,
        raw_token TEXT,
        issued_at TEXT,
        expires_at TEXT,
        approved_by TEXT,
        status TEXT,
        used_at TEXT
    );
    """)

    await db.commit()
    await db.close()

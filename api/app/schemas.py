from pydantic import BaseModel
from typing import Any


class IncidentCreate(BaseModel):
    title: str = "Customer Portal Unavailable"
    started_by: str = "demo"


class ApprovalRequest(BaseModel):
    approver: str


class IncidentResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    root_cause: dict | None = None
    plan: dict | None = None
    verification: dict | None = None
    report: dict | None = None
    mttr_seconds: float | None = None


class EventResponse(BaseModel):
    id: int
    incident_id: str
    sequence: int
    timestamp: str
    stage: str
    event_type: str
    source: str
    message_code: str
    message_params: dict = {}
    raw_payload: dict = {}


class EvidenceResponse(BaseModel):
    id: int
    incident_id: str
    evidence_code: str
    category: str
    source_tool: str
    summary_en: str
    summary_zh: str
    raw_json: dict = {}


class DemoStatus(BaseModel):
    portal_status: int
    backend_status: int
    gateway_upstream: str
    portal_healthy: bool
    backend_healthy: bool

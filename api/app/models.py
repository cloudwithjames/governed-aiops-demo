from enum import Enum
from typing import NamedTuple


class IncidentState(str, Enum):
    IDLE = "IDLE"
    INCIDENT_DETECTED = "INCIDENT_DETECTED"
    OBSERVING = "OBSERVING"
    DIAGNOSING = "DIAGNOSING"
    PLAN_READY = "PLAN_READY"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    REPORTED = "REPORTED"


VALID_TRANSITIONS: dict[IncidentState, set[IncidentState]] = {
    IncidentState.IDLE: {IncidentState.INCIDENT_DETECTED},
    IncidentState.INCIDENT_DETECTED: {IncidentState.OBSERVING, IncidentState.FAILED},
    IncidentState.OBSERVING: {IncidentState.DIAGNOSING, IncidentState.FAILED},
    IncidentState.DIAGNOSING: {IncidentState.PLAN_READY, IncidentState.FAILED},
    IncidentState.PLAN_READY: {IncidentState.WAITING_APPROVAL, IncidentState.FAILED},
    IncidentState.WAITING_APPROVAL: {IncidentState.APPROVED, IncidentState.REJECTED, IncidentState.FAILED},
    IncidentState.APPROVED: {IncidentState.EXECUTING, IncidentState.FAILED},
    IncidentState.REJECTED: {IncidentState.IDLE, IncidentState.REPORTED},
    IncidentState.EXECUTING: {IncidentState.VERIFYING, IncidentState.FAILED},
    IncidentState.VERIFYING: {IncidentState.RECOVERED, IncidentState.FAILED},
    IncidentState.RECOVERED: {IncidentState.REPORTED, IncidentState.FAILED},
    IncidentState.FAILED: {IncidentState.IDLE, IncidentState.REPORTED},
    IncidentState.REPORTED: {IncidentState.IDLE},
}


class TransitionResult(NamedTuple):
    allowed: bool
    from_state: str
    to_state: str
    error: str | None


def can_transition(from_state: str, to_state: str) -> TransitionResult:
    try:
        fs = IncidentState(from_state)
        ts = IncidentState(to_state)
    except ValueError as e:
        return TransitionResult(False, from_state, to_state, f"invalid state: {e}")

    if ts in VALID_TRANSITIONS.get(fs, set()):
        return TransitionResult(True, from_state, to_state, None)
    return TransitionResult(
        False, from_state, to_state,
        f"transition {from_state} -> {to_state} not allowed"
    )


def validate_transition(from_state: str, to_state: str) -> str:
    result = can_transition(from_state, to_state)
    if not result.allowed:
        raise ValueError(result.error)
    return to_state


HAPPY_PATH = [
    IncidentState.IDLE,
    IncidentState.INCIDENT_DETECTED,
    IncidentState.OBSERVING,
    IncidentState.DIAGNOSING,
    IncidentState.PLAN_READY,
    IncidentState.WAITING_APPROVAL,
    IncidentState.APPROVED,
    IncidentState.EXECUTING,
    IncidentState.VERIFYING,
    IncidentState.RECOVERED,
    IncidentState.REPORTED,
]

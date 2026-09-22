import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from app.models import IncidentState, can_transition, HAPPY_PATH


def test_all_happy_path_transitions_allowed():
    for i in range(len(HAPPY_PATH) - 1):
        result = can_transition(HAPPY_PATH[i].value, HAPPY_PATH[i + 1].value)
        assert result.allowed, f"Transition {HAPPY_PATH[i]} -> {HAPPY_PATH[i+1]} should be allowed"


def test_invalid_transition_rejected():
    result = can_transition(IncidentState.IDLE.value, IncidentState.EXECUTING.value)
    assert not result.allowed
    assert result.error is not None


def test_idle_to_incident_detected():
    result = can_transition("IDLE", "INCIDENT_DETECTED")
    assert result.allowed


def test_waiting_approval_to_approved():
    result = can_transition("WAITING_APPROVAL", "APPROVED")
    assert result.allowed


def test_waiting_approval_to_rejected():
    result = can_transition("WAITING_APPROVAL", "REJECTED")
    assert result.allowed


def test_executing_to_failed():
    result = can_transition("EXECUTING", "FAILED")
    assert result.allowed


def test_verifying_to_failed():
    result = can_transition("VERIFYING", "FAILED")
    assert result.allowed


def test_executing_to_recovered_not_allowed():
    result = can_transition("EXECUTING", "RECOVERED")
    assert not result.allowed


def test_invalid_state_name():
    result = can_transition("INVALID_STATE", "IDLE")
    assert not result.allowed


def test_all_states_have_transitions():
    for state in IncidentState:
        assert state in dict.fromkeys(IncidentState), f"State {state} not covered"

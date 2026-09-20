import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from pe_claw_web.schemas import (
    ActionStatus, DesignAction, DesignActionRequest, DesignActionResponse, action_dependencies,
    action_stages, validate_action_transition,
)


def test_all_actions_have_frozen_dependencies_and_stages():
    assert set(DesignAction) == {DesignAction.capacitor, DesignAction.magnetics, DesignAction.waveforms, DesignAction.efficiency_sweep}
    for action in DesignAction:
        assert action_dependencies(action) == frozenset({"design"})
        assert action_stages(action)[0] == "validate"
        assert action_stages(action)[-1] == "finalize"


def test_waveform_requires_operating_point_and_rejects_it_for_other_actions():
    with pytest.raises(ValidationError, match="operating_point"):
        DesignActionRequest(job_id="job-1", action=DesignAction.waveforms)
    with pytest.raises(ValidationError, match="only supported"):
        DesignActionRequest(job_id="job-1", action=DesignAction.capacitor, operating_point={"vin_v": 48, "load_ratio": 1})
    request = DesignActionRequest(job_id="job-1", action=DesignAction.waveforms, operating_point={"vin_v": 48, "load_ratio": 0.75})
    assert request.operating_point.vin_v == 48


def test_action_options_are_allowlisted_and_payload_is_transport_safe():
    request = DesignActionRequest(job_id="job_1", action=DesignAction.magnetics, options={"llc_search_mode": "fast"})
    assert request.model_dump()["schema_version"] == "1.0"
    with pytest.raises(ValidationError, match="Unsupported action option"):
        DesignActionRequest(job_id="job-1", action=DesignAction.magnetics, options={"module_path": "secret"})


def test_action_state_machine_rejects_terminal_rewrites():
    validate_action_transition(ActionStatus.queued, ActionStatus.running)
    validate_action_transition(ActionStatus.running, ActionStatus.succeeded)
    validate_action_transition(ActionStatus.queued, ActionStatus.failed)
    validate_action_transition(ActionStatus.succeeded, ActionStatus.expired)
    with pytest.raises(ValueError, match="Invalid action status transition"):
        validate_action_transition(ActionStatus.succeeded, ActionStatus.running)
    with pytest.raises(ValueError, match="Invalid action status transition"):
        validate_action_transition(ActionStatus.queued, ActionStatus.succeeded)


@pytest.mark.parametrize("current", list(ActionStatus))
@pytest.mark.parametrize("target", list(ActionStatus))
def test_complete_transition_matrix(current, target):
    allowed = {
        "queued": {"running", "failed", "cancelled", "expired"},
        "running": {"succeeded", "failed", "cancelled"},
        "succeeded": {"expired"},
        "failed": {"expired"},
        "cancelled": {"expired"},
        "expired": set(),
    }
    if target.value in allowed[current.value]:
        validate_action_transition(current, target)
    else:
        with pytest.raises(ValueError):
            validate_action_transition(current, target)


@pytest.mark.parametrize("field,value", [
    ("vin_v", 0), ("vin_v", -1), ("vin_v", float("inf")),
    ("load_ratio", -0.1), ("load_ratio", float("inf")),
    ("load_ratio", float("nan")),
])
def test_operating_point_rejects_invalid_numbers(field, value):
    point = {"vin_v": 48, "load_ratio": 1}
    point[field] = value
    with pytest.raises(ValidationError):
        DesignActionRequest(job_id="job-1", action="waveforms", operating_point=point)


@pytest.mark.parametrize("payload", [
    {"job_id": "../job"}, {"action": "design"}, {"schema_version": "2.0"},
    {"output_path": "somewhere"}, {"options": {"llc_search_mode": []}},
    {"options": {"llc_search_mode": True}}, {"options": {"llc_search_mode": "audit"}},
    {"options": {"enable_debug_outputs": True}},
    {"action": "capacitor", "options": {"llc_search_mode": "fast"}},
    {"action": "waveforms", "operating_point": {"vin_v": 48, "load_ratio": 1, "path": "x"}},
])
def test_invalid_action_payloads(payload):
    with pytest.raises(ValidationError):
        DesignActionRequest.model_validate({"job_id": "job-1", "action": "magnetics", **payload})


@pytest.mark.parametrize("action", list(DesignAction))
def test_request_and_response_json_roundtrip(action):
    request = DesignActionRequest(
        job_id="job-1", action=action,
        operating_point={"vin_v": 48, "load_ratio": 0} if action is DesignAction.waveforms else None,
    )
    assert DesignActionRequest.model_validate_json(request.model_dump_json()) == request
    response = DesignActionResponse(
        action_id="action-1", job_id=request.job_id, action=action,
        status="failed", progress=0, created_at=datetime.now(timezone.utc),
        error={"code": "queue_unavailable", "message": "Queue unavailable", "correlation_id": "action-1"},
    )
    assert DesignActionResponse.model_validate_json(response.model_dump_json()) == response
    with pytest.raises(ValidationError):
        DesignActionResponse.model_validate({**response.model_dump(), "error": "unstructured"})
    with pytest.raises(ValidationError):
        DesignActionResponse.model_validate({**response.model_dump(), "progress": 101})

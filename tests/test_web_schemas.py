import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pydantic import ValidationError

from pe_claw_web.schemas import (
    ArtifactManifestEntry,
    BuckDesignRequest,
    DesignJobCreate,
    DesignJobResponse,
    DesignJobStatus,
    DesignStageState,
    DesignRequest,
    TopologyDesignRequest,
)


VALID_REQUEST = {
    "vin_min": 36,
    "vin_max": 60,
    "vout": 12,
    "pout": 120,
    "fs_khz": 100,
    "ripple_current_ratio": .3,
    "ripple_voltage_ratio_percent": 1,
}


def test_buck_request():
    request = BuckDesignRequest(**VALID_REQUEST)
    assert isinstance(request, DesignRequest)
    assert request.model_dump()["topology"] == "buck_diode_rectified_unidirectional"
    assert request.model_dump()["schema_version"] == "1.0"
    DesignJobCreate(request=request)


def test_all_registered_topology_form_defaults_are_valid_web_requests():
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    validated = []
    for definition in registry.list_definitions():
        fields = registry.get_form_class(definition.topology_id).get_design_fields()
        request = TopologyDesignRequest(
            topology=definition.topology_id,
            raw_input={field.key: field.default for field in fields},
        )
        assert request.pipeline_input() == {field.key: field.default for field in fields}
        DesignJobCreate(request=request)
        validated.append(definition.topology_id)
    assert len(validated) == 19


def test_generic_topology_request_rejects_missing_extra_nested_and_invalid_choice():
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    topology = 'single_phase_full_bridge_inverter'
    fields = registry.get_form_class(topology).get_design_fields()
    raw = {field.key: field.default for field in fields}
    with pytest.raises(ValidationError):
        TopologyDesignRequest(topology=topology, raw_input={key: value for key, value in raw.items() if key != 'pout_w'})
    with pytest.raises(ValidationError):
        TopologyDesignRequest(topology=topology, raw_input={**raw, 'module_name': 'internal'})
    with pytest.raises(ValidationError):
        TopologyDesignRequest(topology=topology, raw_input={**raw, 'pout_w': {'expression': '1+1'}})
    with pytest.raises(ValidationError):
        TopologyDesignRequest(topology=topology, raw_input={**raw, 'conduction_mode': 'unsupported'})


def test_invalid_request():
    with pytest.raises(ValueError):
        BuckDesignRequest(**{**VALID_REQUEST, "vin_min": 60, "vin_max": 36})
    with pytest.raises(ValueError):
        BuckDesignRequest(**{**VALID_REQUEST, "vout": 36})
    with pytest.raises(ValueError):
        BuckDesignRequest(**{**VALID_REQUEST, "internal_path": "secret"})


def test_response_contract():
    response = DesignJobResponse(
        job_id="job-1",
        topology="buck_diode_rectified_unidirectional",
        status=DesignJobStatus.queued,
        progress=0,
        created_at=datetime.now(timezone.utc),
        stages={"validate": "running"},
        stage_details={"validate": DesignStageState(status="running", progress=0)},
    )
    assert response.schema_version == "1.0"
    assert response.stage_details["validate"].schema_version == "1.0"
    assert response.stage_details["validate"].status == "running"


def test_complete_execution_profile_and_operating_point():
    request = BuckDesignRequest(**VALID_REQUEST)
    payload = DesignJobCreate(request=request, operating_point={"vin_v": 48, "load_ratio": 1})
    assert payload.execution_profile == "complete"
    assert payload.operating_point.vin_v == 48
    with pytest.raises(ValueError):
        DesignJobCreate(request=request, execution_profile="incremental")
    with pytest.raises(ValueError):
        DesignJobCreate(request=request, operating_point={"vin_v": 100, "load_ratio": 1})
    with pytest.raises(ValueError):
        DesignJobCreate(request=request, operating_point={"vin_v": 48, "load_ratio": -1})


def test_missing_range_and_topology_errors_are_located():
    missing = dict(VALID_REQUEST)
    missing.pop("pout")
    with pytest.raises(ValidationError) as missing_error:
        BuckDesignRequest.model_validate(missing)
    assert ("pout",) in {tuple(item["loc"]) for item in missing_error.value.errors()}

    with pytest.raises(ValidationError) as range_error:
        BuckDesignRequest.model_validate({**VALID_REQUEST, "fs_khz": 0})
    assert range_error.value.errors()[0]["loc"] == ("fs_khz",)

    with pytest.raises(ValidationError) as topology_error:
        BuckDesignRequest.model_validate({**VALID_REQUEST, "topology": "boost_diode_rectified_unidirectional"})
    assert topology_error.value.errors()[0]["loc"] == ("topology",)


@pytest.mark.parametrize("forbidden_key", ["path", "module_name", "expression", "internal_object"])
def test_buck_options_reject_unpublished_inputs(forbidden_key):
    with pytest.raises(ValidationError) as error:
        BuckDesignRequest.model_validate({**VALID_REQUEST, "options": {forbidden_key: "secret"}})
    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_schema_units_and_directly_loadable_example():
    schema = BuckDesignRequest.model_json_schema()
    expected_units = {
        "vin_min": "V",
        "vin_max": "V",
        "vout": "V",
        "pout": "W",
        "fs_khz": "kHz",
        "ripple_current_ratio": "ratio",
        "ripple_voltage_ratio_percent": "%",
    }
    assert {key: schema["properties"][key]["unit"] for key in expected_units} == expected_units

    example_path = Path(__file__).resolve().parents[1] / "docs" / "web-api-v1-buck-request.json"
    request = BuckDesignRequest.model_validate_json(example_path.read_text(encoding="utf-8"))
    assert request.pipeline_input()["ambient_temp_c"] == 25.0
    assert json.loads(request.model_dump_json())["schema_version"] == "1.0"


def test_artifact_manifest_rejects_paths_and_external_urls():
    valid = {
        "id": "result-json",
        "name": "result.json",
        "media_type": "application/json",
        "size": 10,
        "sha256": "0" * 64,
        "stage": "report",
        "download_url": "/api/v1/design-jobs/job-1/artifacts/result-json",
    }
    assert ArtifactManifestEntry.model_validate(valid).schema_version == "1.0"
    with pytest.raises(ValidationError):
        ArtifactManifestEntry.model_validate({**valid, "name": "../result.json"})
    with pytest.raises(ValidationError):
        ArtifactManifestEntry.model_validate({**valid, "download_url": "https://example.test/result.json"})

from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path(__file__).resolve().parent / "fixtures" / "two_phase_interleaved_boost_pfc_step1_contract.json"


def _load_contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="ascii"))


def test_step1_contract_freezes_identity_and_fixed_two_phase_assumptions() -> None:
    contract = _load_contract()

    assert contract["contract_version"] == "two_phase_interleaved_boost_pfc_contract_v1"
    assert contract["identity"] == {
        "topology_id": "single_phase_interleaved_boost_pfc_diode_bridge",
        "display_name": "Single-Phase Interleaved Boost PFC Diode Bridge",
        "legacy_key": "SinglePhase_InterleavedBoostPFC_DiodeBridge_FirstPass",
        "category_id": "ac_dc",
        "support_status": "first-pass",
    }
    fixed = contract["fixed_topology"]
    assert fixed["phase_count"] == 2
    assert fixed["phase_shift_deg"] == 180.0
    assert fixed["current_sharing_assumption"] == "ideal_equal_phase_current"
    assert fixed["phase_current_fraction"] == {"phase_1": 0.5, "phase_2": 0.5}


def test_step1_contract_reuses_boost_pfc_inputs_without_sizing_efficiency_or_phase_controls() -> None:
    contract = _load_contract()
    user_input = contract["user_input"]
    fields = set(user_input["fields"])
    excluded = set(user_input["excluded_fields"])

    assert "sizing_efficiency_assumption" not in fields
    assert "phase_count" not in fields
    assert "phase_shift_deg" not in fields
    assert "phase_current_sharing_tolerance_percent" not in fields
    assert "phase_inductor_current_ripple_ratio" not in fields
    assert "phase_inductance_h" not in fields
    assert fields.isdisjoint(excluded)
    assert "inductor_current_ripple_ratio" in fields
    assert "input_inductance_h" in fields


def test_step1_contract_freezes_inductance_and_common_model_semantics() -> None:
    contract = _load_contract()
    inductance = contract["inductance_semantics"]
    assert inductance["input_inductance_h"]["role"] == "per_phase_series_input_inductance"
    assert inductance["input_inductance_h"]["common_bridge_side_inductor"] is False
    assert inductance["phase_boost_inductance_h"]["unit"] == "H"
    assert inductance["phase_total_series_inductance_h"]["unit"] == "H"

    candidate = contract["candidate_contract"]
    public_fields = candidate["public_fields"]
    assert public_fields["inductance_h"] == "per-phase total series inductance in H"
    assert public_fields["delta_il"] == "per-phase nominal peak-to-peak inductor ripple in A"
    assert public_fields["iout"] == "common DC output current in A"
    assert public_fields["capacitance_f"] == "common DC-link capacitance requirement in F"


def test_step1_contract_has_phase_level_waveform_stress_hardware_and_provenance() -> None:
    contract = _load_contract()

    waveform = contract["waveform_contract"]
    assert "phase_waveforms" in waveform["metadata_fields"]
    assert "aggregate_waveform_basis" in waveform["metadata_fields"]
    assert waveform["public_field_semantics"]["input_source_current_a"] == "signed aggregate AC input current"

    stress = contract["stress_contract"]
    assert stress["phase_roles"] == [
        "phase_1_main_switch",
        "phase_2_main_switch",
        "phase_1_boost_diode",
        "phase_2_boost_diode",
        "input_bridge_rectifier",
    ]
    assert stress["phase_metadata_field"] == "phase_stress"

    hardware = contract["hardware_contract"]
    assert hardware["magnetic_instances"] == [
        "phase_1_boost_inductor",
        "phase_2_boost_inductor",
    ]
    assert "run_id" in contract["report_contract"]["provenance_fields"]
    assert "input_sha256" in contract["report_contract"]["provenance_fields"]


def test_step1_contract_records_explicit_first_pass_boundaries() -> None:
    boundaries = set(_load_contract()["unsupported_boundaries"])

    assert {
        "dcm",
        "crm",
        "dynamic_current_sharing_control",
        "phase_parameter_mismatch",
        "thd_control_validation",
        "emi_filter_validation",
        "detailed_parasitic_switching_model",
    }.issubset(boundaries)

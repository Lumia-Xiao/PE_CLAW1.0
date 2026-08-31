"""AC-DC bridge-rectifier selection pipeline stage."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..engines.devices.bridge_rectifier_selector import select_bridge_rectifier
from ..libraries.semiconductors.bridge_rectifier_candidates import load_bridge_rectifier_candidates
from ..models.bridge_rectifier import BridgeRectifierSelectionRequest
from ..models.design_report import DesignReport


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEGACY_OUTPUT_BRIDGE_RECTIFIER_CSV_PATH = _REPO_ROOT / "outputs" / "ac_dc_bridge_rectifier_candidates.csv"
LEGACY_OUTPUT_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH = (
    _REPO_ROOT / "outputs" / "ac_dc_three_phase_bridge_rectifier_candidates.csv"
)
PACKAGED_BRIDGE_RECTIFIER_CSV_PATH = (
    _PACKAGE_ROOT / "libraries" / "semiconductors" / "data" / "ac_dc_bridge_rectifier_candidates.csv"
)
PACKAGED_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH = (
    _PACKAGE_ROOT / "libraries" / "semiconductors" / "data" / "ac_dc_three_phase_bridge_rectifier_candidates.csv"
)
DEFAULT_BRIDGE_RECTIFIER_CSV_PATH = PACKAGED_BRIDGE_RECTIFIER_CSV_PATH
DEFAULT_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH = PACKAGED_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH
SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND = "single_phase_bridge_rectifier"
THREE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND = "three_phase_bridge_rectifier"
SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
BRIDGE_RECTIFIER_TOPOLOGY_CONFIG = {
    "single_phase_diode_bridge_rectifier_capacitor_filter": (
        DEFAULT_BRIDGE_RECTIFIER_CSV_PATH,
        SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND,
    ),
    "single_phase_diode_bridge_rectifier_dc_inductor_filter": (
        DEFAULT_BRIDGE_RECTIFIER_CSV_PATH,
        SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND,
    ),
    "three_phase_diode_bridge_rectifier_capacitor_filter": (
        DEFAULT_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH,
        THREE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND,
    ),
    SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID: (
        DEFAULT_BRIDGE_RECTIFIER_CSV_PATH,
        SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND,
    ),
}
SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES = frozenset(BRIDGE_RECTIFIER_TOPOLOGY_CONFIG)
SUPPORTED_SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGIES = {
    topology_id
    for topology_id, (_, topology_kind) in BRIDGE_RECTIFIER_TOPOLOGY_CONFIG.items()
    if topology_kind == SINGLE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND
}


def run_bridge_rectifier_pipeline(
    report: DesignReport,
    candidate_csv_path: str | Path | None = None,
) -> DesignReport:
    """Select a normalized bridge rectifier for an AC-DC report."""

    if report.candidate is None:
        return _append_note(report, "Bridge rectifier selection skipped: design report has no topology candidate.")
    topology_config = BRIDGE_RECTIFIER_TOPOLOGY_CONFIG.get(report.spec.topology_id)
    if topology_config is None:
        return _append_note(
            report,
            f"Bridge rectifier selection skipped: unsupported topology {report.spec.topology_id}.",
        )

    default_csv_path, topology_kind = topology_config
    csv_path = _resolve_candidate_csv_path(
        default_csv_path=default_csv_path,
        topology_kind=topology_kind,
        candidate_csv_path=candidate_csv_path,
    )
    if not csv_path.exists():
        return _append_note(report, f"Bridge rectifier selection skipped: candidate CSV not found: {csv_path}.")

    try:
        load_result = load_bridge_rectifier_candidates(csv_path, topology_kind=topology_kind)
    except (OSError, ValueError) as exc:
        return _append_note(report, f"Bridge rectifier selection skipped: candidate CSV load failed: {exc}")

    request = build_bridge_rectifier_selection_request(report)
    selection = select_bridge_rectifier(load_result.candidates, request)
    notes = list(report.notes)
    notes.append(
        "Bridge rectifier selection completed: "
        f"{selection.passed_candidate_count} / {selection.candidate_count} candidates passed hard filters."
    )
    if load_result.rejected_count:
        notes.append(f"Bridge rectifier CSV loader rejected {load_result.rejected_count} malformed rows.")
    if load_result.filtered_count:
        notes.append(f"Bridge rectifier CSV loader filtered {load_result.filtered_count} rows for topology kind {topology_kind}.")
    return replace(report, bridge_rectifier=selection, notes=notes)


def _resolve_candidate_csv_path(
    *,
    default_csv_path: Path,
    topology_kind: str,
    candidate_csv_path: str | Path | None,
) -> Path:
    if candidate_csv_path is not None:
        return Path(candidate_csv_path)
    configured_path = Path(default_csv_path)
    if configured_path.exists():
        return configured_path
    packaged_path = _packaged_candidate_csv_path(topology_kind)
    if packaged_path.exists():
        return packaged_path
    return configured_path


def _packaged_candidate_csv_path(topology_kind: str) -> Path:
    if topology_kind == THREE_PHASE_BRIDGE_RECTIFIER_TOPOLOGY_KIND:
        return PACKAGED_THREE_PHASE_BRIDGE_RECTIFIER_CSV_PATH
    return PACKAGED_BRIDGE_RECTIFIER_CSV_PATH


def build_bridge_rectifier_selection_request(report: DesignReport) -> BridgeRectifierSelectionRequest:
    """Build bridge-rectifier selector inputs from an AC-DC topology report."""

    if report.candidate is None:
        raise ValueError("Cannot build bridge rectifier request without a topology candidate.")

    candidate = report.candidate
    metadata = candidate.metadata
    required_reverse_voltage_v = _bridge_required_reverse_voltage_v(report)
    recommended_reverse_voltage_v = _bridge_recommended_reverse_voltage_v(report)
    bridge_current_waveform_a = _bridge_current_waveform(report)
    bridge_current_avg_a = _bridge_current_avg(report, bridge_current_waveform_a)
    bridge_current_rms_a = _bridge_current_rms(report, bridge_current_waveform_a, bridge_current_avg_a)
    dc_bus_voltage_v = _metadata_float(metadata, "vdc_est_v", "vdc_avg_v", default=candidate.vout_target)
    request_notes = ["Request generated from AC-DC topology report for bridge-rectifier selection."]
    if _is_three_phase_bridge_topology(report.spec.topology_id):
        request_notes.append(
            "Three-phase bridge voltage hard filter uses line-line peak diode reverse stress; "
            "600 V class bridges are acceptable for a 400 VLL design when they exceed this stress."
        )
    if report.spec.topology_id == SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        request_notes.append(
            "Boost PFC bridge current uses the rectified input-source current waveform, not the boost diode current."
        )

    return BridgeRectifierSelectionRequest(
        topology_id=report.spec.topology_id,
        ac_input_rms_v=_metadata_float(metadata, "vac_rms_v", default=candidate.vin_nom),
        dc_bus_voltage_v=dc_bus_voltage_v,
        output_power_w=candidate.pout_target,
        dc_output_current_a=_metadata_float(metadata, "idc_a", default=candidate.iout),
        bridge_current_avg_a=bridge_current_avg_a,
        bridge_current_rms_a=bridge_current_rms_a,
        required_reverse_voltage_v=required_reverse_voltage_v,
        line_frequency_hz=_metadata_float(metadata, "f_line_hz", default=max(candidate.fs_hz / 2.0, 1e-9)),
        bridge_current_waveform_a=bridge_current_waveform_a,
        recommended_reverse_voltage_v=recommended_reverse_voltage_v,
        voltage_margin_basis=_bridge_voltage_margin_basis(report),
        voltage_margin_policy=_bridge_voltage_margin_policy(report),
        ambient_temp_c=_metadata_float(metadata, "ambient_temp_c", default=25.0),
        target_junction_temp_c=_metadata_float(metadata, "target_junction_temp_c", default=125.0),
        voltage_margin=1.0,
        current_margin=1.10,
        notes=tuple(request_notes),
    )


def _bridge_required_reverse_voltage_v(report: DesignReport) -> float:
    if report.candidate is None:
        raise ValueError("Cannot build bridge rectifier request without a topology candidate.")
    metadata = report.candidate.metadata
    if _is_three_phase_bridge_topology(report.spec.topology_id):
        return _metadata_float(
            metadata,
            "diode_reverse_stress_v",
            "diode_vrrm_stress_v",
            "recommended_diode_vrrm_v",
            "diode_vrrm_required_v",
            default=report.candidate.vin_nom,
        )
    return _metadata_float(
        metadata,
        "recommended_diode_vrrm_v",
        "diode_vrrm_required_v",
        "diode_reverse_stress_v",
        "diode_vrrm_stress_v",
        default=report.candidate.vin_nom,
    )


def _bridge_recommended_reverse_voltage_v(report: DesignReport) -> float | None:
    if report.candidate is None:
        return None
    if _is_three_phase_bridge_topology(report.spec.topology_id):
        return _bridge_required_reverse_voltage_v(report)
    metadata = report.candidate.metadata
    value = _metadata_float_or_none(metadata, "recommended_diode_vrrm_v", "diode_vrrm_required_v")
    if value is not None:
        return value
    return _bridge_required_reverse_voltage_v(report) * _metadata_float(metadata, "diode_voltage_margin", default=1.0)


def _bridge_voltage_margin_basis(report: DesignReport) -> str:
    if _is_three_phase_bridge_topology(report.spec.topology_id):
        return "hard_filter_uses_line_line_peak_reverse_stress"
    return "hard_filter_uses_recommended_vrrm"


def _bridge_voltage_margin_policy(report: DesignReport) -> str:
    if report.candidate is None:
        return "stress_with_margin_warning"
    policy = report.candidate.metadata.get("bridge_voltage_margin_policy")
    if isinstance(policy, str) and policy.strip():
        return policy.strip()
    return "stress_with_margin_warning"


def _is_three_phase_bridge_topology(topology_id: str) -> bool:
    return topology_id.startswith("three_phase_")


def _bridge_current_waveform(report: DesignReport) -> tuple[float, ...]:
    if (
        report.spec.topology_id == SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID
        and report.candidate is not None
    ):
        line_cycle = report.candidate.metadata.get("sizing_line_cycle")
        if isinstance(line_cycle, dict):
            values = line_cycle.get("input_current_a")
            if isinstance(values, (list, tuple)) and values:
                try:
                    half = [float(value) for value in values]
                    return tuple([*half, *[-value for value in half[1:]]])
                except (TypeError, ValueError):
                    pass
    if report.waveform is not None and report.waveform.diode_current_a:
        return tuple(float(value) for value in report.waveform.diode_current_a)
    if report.waveform is not None and report.waveform.inductor_current_a:
        return tuple(float(value) for value in report.waveform.inductor_current_a)
    metadata_waveform = _metadata_bridge_current_waveform(report)
    if metadata_waveform:
        return metadata_waveform
    return ()


def _metadata_bridge_current_waveform(report: DesignReport) -> tuple[float, ...]:
    if report.candidate is None:
        return ()
    if report.spec.topology_id == SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        values = report.candidate.metadata.get("bridge_current_waveform_a")
        if isinstance(values, (list, tuple)) and values:
            try:
                return tuple(float(value) for value in values)
            except (TypeError, ValueError):
                return ()
        line_cycle = report.candidate.metadata.get("line_cycle")
        if isinstance(line_cycle, dict):
            input_current = line_cycle.get("input_current_a")
            if isinstance(input_current, (list, tuple)) and input_current:
                try:
                    return tuple(float(value) for value in input_current)
                except (TypeError, ValueError):
                    return ()
    waveforms = report.candidate.metadata.get("six_pulse_waveform_preview_waveforms")
    if not isinstance(waveforms, dict):
        return ()
    for key in ("ia_a", "ib_a", "ic_a"):
        values = waveforms.get(key)
        if isinstance(values, (list, tuple)) and values:
            try:
                return tuple(float(value) for value in values)
            except (TypeError, ValueError):
                return ()
    return ()


def _bridge_current_avg(report: DesignReport, waveform: tuple[float, ...]) -> float:
    if waveform:
        return sum(abs(sample) for sample in waveform) / len(waveform)
    return _metadata_float(
        report.candidate.metadata,
        "idc_a",
        "il_avg_a",
        default=report.candidate.iout,
    )


def _bridge_current_rms(report: DesignReport, waveform: tuple[float, ...], fallback_a: float) -> float:
    if waveform:
        return (sum(sample * sample for sample in waveform) / len(waveform)) ** 0.5
    return _metadata_float(
        report.candidate.metadata,
        "i_bridge_rms_a",
        "bridge_current_rms_a",
        "il_rms_est_a",
        default=fallback_a,
    )


def _metadata_float(metadata: dict[str, object], *keys: str, default: float) -> float:
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return float(default)


def _metadata_float_or_none(metadata: dict[str, object], *keys: str) -> float | None:
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _append_note(report: DesignReport, note: str) -> DesignReport:
    return replace(report, notes=[*report.notes, note])

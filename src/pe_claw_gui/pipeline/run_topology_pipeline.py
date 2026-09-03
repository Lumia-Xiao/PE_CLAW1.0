"""Topology-level runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ..libraries.semiconductors.metadata import (
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
)
from ..models.common_spec import CommonSpec
from ..models.design_run_context import DesignRunContext, write_design_run_manifest
from ..models.design_report import DesignReport
from ..models.operating_point import OperatingPoint
from ..models.llc_run_context import LlcRunContext, is_llc_topology
from ..models.waveform import WaveformSet
from ..topologies.base import TopologyCandidate, TopologyPlugin, TopologyResult


@dataclass(frozen=True)
class TopologyPipelineBundle:
    """Intermediate runtime bundle produced by the topology pipeline."""

    plugin: TopologyPlugin
    spec: CommonSpec
    candidate: TopologyCandidate
    operating_point: OperatingPoint | None
    waveform: WaveformSet | None
    topology_result: TopologyResult
    report: DesignReport


def run_topology_pipeline(
    plugin: TopologyPlugin,
    raw_input: dict[str, str],
    operating_point: OperatingPoint | None = None,
    include_waveforms: bool = False,
    output_root: str | Path | None = None,
) -> TopologyPipelineBundle:
    """Run the selected topology plugin through synthesis and evaluation."""
    context = DesignRunContext.create(plugin.topology_id, raw_input, output_root=output_root)
    try:
        with context.activate():
            spec = plugin.build_spec(raw_input)
            candidate = plugin.synthesize(spec)
            # Synthesis defines the design-point hardware once; waveform generation must
            # reuse that candidate and only vary the requested operating point.
            waveform_set = plugin.generate_waveforms(candidate, operating_point) if include_waveforms else None
            stress_result = plugin.extract_stress(candidate, waveform_set=waveform_set)
            topology_result = plugin.evaluate(candidate, waveform_set=waveform_set, stress_result=stress_result)
            report = plugin.build_report(
                spec=spec,
                candidate=candidate,
                operating_point=operating_point,
                waveform_set=waveform_set,
                stress_result=stress_result,
                topology_result=topology_result,
            )
    except Exception as exc:
        context = context.transition("design", "failed", reason=f"{type(exc).__name__}: {exc}")
        write_design_run_manifest(context)
        raise
    context = context.transition("design", "succeeded")
    report = replace(
        report,
        run_context=context,
        notes=[*report.notes, "Design run context created with an isolated output directory."],
    )
    if is_llc_topology(spec.topology_id):
        llc_context = LlcRunContext.create(
            spec.topology_id,
            raw_input,
            output_root=context.output_root,
            run_id=context.run_id,
            created_at=context.created_at,
        )
        if report.device is not None and report.device.recommended_scheme_id:
            llc_context = llc_context.with_result_ids(device_design_id=report.device.recommended_scheme_id)
        report = replace(
            report,
            llc_run_context=llc_context,
            notes=[*report.notes, "LLC run context created with isolated input and output identity."],
        )
    write_design_run_manifest(context)
    return TopologyPipelineBundle(
        plugin=plugin,
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        topology_result=topology_result,
        report=report,
    )


def run_design_pipeline(spec: Any):
    """Compatibility wrapper around the new runtime topology pipeline."""
    from ..topologies.base.registry import build_default_registry

    topology_id = getattr(spec, "topology_id", None)
    if topology_id is None:
        legacy_key = getattr(spec, "archetype_key", "")
        if legacy_key == "Buck_CCM_DiodeRectified_Unidirectional":
            topology_id = "buck_diode_rectified_unidirectional"
        else:
            raise ValueError(f"Unsupported topology spec: {legacy_key!r}")

    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    if topology_id == "three_level_tzcm_fixed_frequency":
        raw_input = {
            "vin_nom": str(spec.vin_min),
            "vout_nom": str(spec.vout),
            "pout_nom": str(spec.pout),
            "fsw_khz": str(getattr(spec, "metadata", {}).get("fsw_khz", spec.fs_khz)),
            "izvs": str(getattr(spec, "metadata", {}).get("izvs", 0.0)),
            "ripple_voltage_ratio_percent": str(spec.ripple_voltage_ratio_percent),
            "vout_ripple_ratio": str(
                getattr(spec, "metadata", {}).get("vout_ripple_ratio", spec.ripple_voltage_ratio_percent / 100.0)
            ),
        }
    else:
        raw_input = {
            "vin_min": str(spec.vin_min),
            "vin_max": str(spec.vin_max),
            "vout": str(spec.vout),
            "pout": str(spec.pout),
            "fs_khz": str(spec.fs_khz),
            "ripple_current_ratio": str(spec.ripple_current_ratio),
            "ripple_voltage_ratio_percent": str(spec.ripple_voltage_ratio_percent),
        }
    for key in ("duty_clamp", "transition_band_ratio"):
        if hasattr(spec, "metadata") and key in getattr(spec, "metadata", {}):
            raw_input[key] = str(spec.metadata[key])
    for key in (SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, SEMICONDUCTOR_MANUFACTURER_INPUT_KEY):
        if hasattr(spec, "metadata") and key in getattr(spec, "metadata", {}):
            raw_input[key] = str(spec.metadata[key])
    bundle = run_topology_pipeline(plugin, raw_input=raw_input, include_waveforms=False)

    from ..models.pipeline import DesignPipelineResult

    return DesignPipelineResult.from_report(bundle.report)


def run_waveform_pipeline(candidate: Any, vin: float, load_ratio: float):
    """Compatibility wrapper around the new runtime topology pipeline."""
    from ..topologies.base.registry import build_default_registry

    topology_id = getattr(candidate, "topology_id", None)
    if topology_id is None:
        legacy_key = getattr(getattr(candidate, "archetype", None), "key", "")
        if legacy_key == "Buck_CCM_DiodeRectified_Unidirectional":
            topology_id = "buck_diode_rectified_unidirectional"
        else:
            raise ValueError(f"Unsupported topology candidate: {legacy_key!r}")

    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    if topology_id == "three_level_tzcm_fixed_frequency":
        spec_like = {
            "vin_nom": str(candidate.metadata.get("vin_nom", candidate.vin_nom)),
            "vout_nom": str(candidate.metadata.get("vout_nom", candidate.vout_target)),
            "pout_nom": str(candidate.metadata.get("pout_nom", candidate.pout_target)),
            "fsw_khz": str(candidate.metadata.get("fsw_khz", candidate.fs_hz / 1e3)),
            "izvs": str(candidate.metadata.get("izvs", abs(candidate.current_ip_minus_a or 0.0))),
            "ripple_voltage_ratio_percent": str(
                candidate.metadata.get(
                    "ripple_voltage_ratio_percent",
                    candidate.metadata.get("vout_ripple_ratio", candidate.delta_vo / max(candidate.vout_target, 1e-9)) * 100.0,
                )
            ),
            "vout_ripple_ratio": str(
                candidate.metadata.get("vout_ripple_ratio", candidate.delta_vo / max(candidate.vout_target, 1e-9))
            ),
        }
    else:
        spec_like = {
            "vin_min": str(candidate.vin_min),
            "vin_max": str(candidate.vin_max),
            "vout": str(candidate.vout_target),
            "pout": str(candidate.pout_target),
            "fs_khz": str(candidate.fs_hz / 1e3),
            "ripple_current_ratio": str(candidate.delta_il / max(candidate.iout, 1e-9)),
            "ripple_voltage_ratio_percent": str((candidate.delta_vo / max(candidate.vout_target, 1e-9)) * 100.0),
        }
    for key in ("duty_clamp", "transition_band_ratio"):
        if key in getattr(candidate, "metadata", {}):
            spec_like[key] = str(candidate.metadata[key])
    for key in (SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, SEMICONDUCTOR_MANUFACTURER_INPUT_KEY):
        if key in getattr(candidate, "metadata", {}):
            spec_like[key] = str(candidate.metadata[key])
    bundle = run_topology_pipeline(
        plugin,
        raw_input=spec_like,
        operating_point=OperatingPoint(vin_v=vin, load_ratio=load_ratio),
        include_waveforms=True,
    )

    from ..models.pipeline import WaveformPipelineResult

    return WaveformPipelineResult.from_report(bundle.report)

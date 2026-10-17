"""Stage 6 contracts for the fixed-order complete design Worker."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

from pe_claw_gui.models.device_result import DeviceSelectionResult
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepResult
from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_web.jobs.store import JobStore
from pe_claw_web.jobs.stages import COMPLETE_STAGES
from pe_claw_web.schemas import BuckDesignRequest


INPUT = {
    "vin_min": 36,
    "vin_max": 60,
    "vout": 12,
    "pout": 120,
    "fs_khz": 100,
    "ripple_current_ratio": 0.3,
    "ripple_voltage_ratio_percent": 1,
}


def _base_report(tmp_path):
    from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import build_default_inputs

    request = BuckDesignRequest(**INPUT)
    plugin = build_default_registry().get_plugin(request.topology)
    return run_topology_pipeline(
        plugin,
        raw_input=build_default_inputs(),
        include_waveforms=False,
        output_root=tmp_path / "base",
    ).report


def test_complete_adapter_has_fixed_order_and_reuses_selected_hardware(tmp_path, monkeypatch):
    import pe_claw_web.api.complete as complete

    request = BuckDesignRequest(**INPUT)
    base = _base_report(tmp_path)
    selected_device = DeviceSelectionResult(selected_devices={"switch": "fixed-switch"})
    selected_magnetic = MagneticResult(
        chosen_designs=[FixedInductorDesignCandidate(candidate_id="fixed-core", turns=10)]
    )
    capacitor_marker = object()
    calls = []

    monkeypatch.setattr(complete, "run_topology_pipeline", lambda *a, **k: SimpleNamespace(report=base))

    def devices(report, **_kwargs):
        calls.append("devices")
        return replace(report, device=selected_device)

    def capacitor(report, **_kwargs):
        assert report.device is selected_device
        calls.append("capacitor")
        return replace(report, capacitor=capacitor_marker)

    def magnetics(report, **_kwargs):
        assert report.capacitor is capacitor_marker
        calls.append("magnetics")
        return replace(report, magnetic=selected_magnetic)

    def operating_point(report, _plugin, point, **kwargs):
        assert report.device is selected_device
        assert report.capacitor is capacitor_marker
        assert report.magnetic is selected_magnetic
        assert kwargs["refresh_loss_thermal"] is False
        calls.append("operating_point")
        return replace(report, operating_point=point)

    def fixed_hardware(stage):
        def run(report, **_kwargs):
            assert report.device is selected_device
            assert report.capacitor is capacitor_marker
            assert report.magnetic is selected_magnetic
            calls.append(stage)
            return report
        return run

    def sweep(report, **_kwargs):
        assert report.device is selected_device
        assert report.capacitor is capacitor_marker
        assert report.magnetic is selected_magnetic
        calls.append("efficiency_sweep")
        return EfficiencySweepResult(status="blocked", blocked_reason="test fixture")

    monkeypatch.setattr(complete, "run_device_pipeline", devices)
    monkeypatch.setattr(complete, "run_semiconductor_geometry_pipeline", lambda report: report)
    monkeypatch.setattr(complete, "run_capacitor_pipeline", capacitor)
    monkeypatch.setattr(complete, "run_magnetic_pipeline", magnetics)
    monkeypatch.setattr(complete, "run_operating_point_refresh", operating_point)
    monkeypatch.setattr(complete, "run_loss_pipeline", fixed_hardware("loss"))
    monkeypatch.setattr(complete, "run_thermal_pipeline", fixed_hardware("thermal"))
    monkeypatch.setattr(complete, "run_geometry_pipeline", lambda report, **k: report)
    monkeypatch.setattr(complete, "run_efficiency_sweep", sweep)
    monkeypatch.setattr(complete, "result_of", lambda report, _topology: report)

    started = []
    result = complete.run_complete(
        request,
        output_root=tmp_path / "complete",
        on_stage=lambda stage, _progress: started.append(stage),
    )

    assert started == list(complete.STAGES)
    assert calls == [
        "devices",
        "capacitor",
        "magnetics",
        "operating_point",
        "loss",
        "thermal",
        "efficiency_sweep",
    ]
    assert result.device is selected_device
    assert result.capacitor is capacitor_marker
    assert result.magnetic is selected_magnetic


def test_worker_records_start_and_terminal_state_for_every_stage(tmp_path, monkeypatch):
    import pe_claw_web.workers.tasks as tasks
    from pe_claw_web.api.complete import STAGES, STAGE_PROGRESS, result_of

    repository = JobStore(f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}")
    item = repository.create(BuckDesignRequest(**INPUT))
    assert tuple(item.stages) == COMPLETE_STAGES
    assert set(item.stages.values()) == {"pending"}
    partial = result_of(_base_report(tmp_path), item.topology)
    summary = deepcopy(partial.summary)
    summary["efficiency_sweep"]["metadata"]["warnings"] = ["fixture sweep warning"]
    partial = partial.model_copy(update={"summary": summary})
    observed = []
    original_update = repository.owned_update

    def record_update(*args, **kwargs):
        if "stages_json" in kwargs:
            observed.append(deepcopy(kwargs["stages_json"]))
        return original_update(*args, **kwargs)

    def execute(_request, **kwargs):
        for stage in STAGES:
            kwargs["on_stage"](stage, STAGE_PROGRESS[stage])
            kwargs["on_checkpoint"](stage, {"completed_stage": stage}, partial)
        return partial

    monkeypatch.setattr(tasks, "store", repository)
    monkeypatch.setattr(tasks, "run_complete_buck_design", execute)
    monkeypatch.setattr(tasks, "save_result", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(repository, "owned_update", record_update)

    tasks.design_buck_task.run(item.job_id)

    status = repository.get(item.job_id)[0]
    expected = ("validate", *STAGES, "finalize")
    assert tuple(status.stages) == expected
    assert status.status == "succeeded"
    assert status.progress == 100
    for stage in expected:
        detail = status.stage_details[stage]
        assert detail.status in {"succeeded", "unavailable", "blocked"}
        assert detail.progress == 100
        assert detail.started_at is not None
        assert detail.finished_at is not None
        assert any(snapshot[stage]["status"] == "running" for snapshot in observed)
    assert status.stage_details["efficiency_sweep"].warnings == ["fixture sweep warning"]
    repository.engine.dispose()

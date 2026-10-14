"""Independent conduction references, real selection, staged routes and readback."""

from __future__ import annotations
from dataclasses import asdict, replace
import json
import math
import numpy as np
import pytest
from pe_claw_gui.engines.devices.t_type_conduction import (
    integrate_conduction_table,
    model_rejection,
    position_losses,
    evaluate_t_type_conduction_reference,
)
from pe_claw_gui.libraries.semiconductors.registry import (
    build_default_semiconductor_registry,
)
from pe_claw_gui.libraries.semiconductors.sic_module_models import ConductionTable2D
from pe_claw_gui.libraries.semiconductors.igbt_discrete_models import RohmRGIGBTDevice
from pe_claw_gui.models.device_loss import SwitchStress
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.models.t_type_engineering import LOSS_SCOPE_ID
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import (
    ROLE_POSITIONS,
    PositionConductionRequest,
    build_position_requests,
)
from pe_claw_gui.topology_capabilities import (
    supports_engineering_stage,
    has_semiconductor_selection_path,
)


@pytest.fixture(scope="module")
def library():
    return build_default_semiconductor_registry()


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    return run_full_pipeline(
        PLUGIN, {}, output_root=tmp_path_factory.mktemp("t-type-real")
    )


def test_real_two_role_selection_and_physical_count(report, tmp_path):
    assert has_semiconductor_selection_path(PLUGIN.topology_id)
    assert set(report.device.selected_devices) == set(ROLE_POSITIONS)
    selected = next(
        s
        for s in report.device.scheme_results
        if s.scheme_id == report.device.active_scheme_id
    )
    assert selected.complete and selected.feasible
    assert [s.parallel_count for s in report.device.scheme_results] == [1, 2, 3]
    n = selected.parallel_count
    assert len(report.t_type_engineering.packages) == 12 * n
    assert (
        len({p.package_instance_id for p in report.t_type_engineering.packages})
        == 12 * n
    )
    for role in selected.role_results:
        assert (
            role.topology_position_count == 6
            and role.total_physical_device_count == 6 * n
        )
        assert role.total_loss_w is None
        assert role.per_device_stress.v_block_V == (
            700 if role.role == "t_type_main_switch" else 350
        )
    assert report.t_type_engineering.loss_scope_id == LOSS_SCOPE_ID
    assert report.t_type_engineering.design_basis.cases == ((700, 1.0, 1.0),)
    assert report.t_type_engineering.design_basis.selection_policy == "nominal_design_point"
    basis = report.t_type_engineering.design_basis
    assert (
        basis.rated_output_power_w,
        basis.vac_ll_rms_v,
        basis.f_line_hz,
        basis.fsw_hz,
    ) == (10000, 400, 50, 20000)
    assert basis.design_inductance_h == report.candidate.inductance_h
    assert (basis.voltage_margin_ratio, basis.current_margin_ratio) == (0.2, 0.1)
    for target in report.semiconductor_geometry.targets:
        assert (
            sum(r.quantity for r in target.role_layouts) == 12 * target.parallel_count
        )
        assert all(
            r.layout.parallel_count == 6 * target.parallel_count
            for r in target.role_layouts
        )
        assert target.sink_volume_cm3 is None
    from pe_claw_gui.engines.hardware_overview import _resolve_semiconductor_loss_w

    assert _resolve_semiconductor_loss_w(report) is None
    assert (
        report.device.current_operating_losses == report.device.evaluated_losses == {}
    )
    assert (
        report.loss
        is report.capacitor
        is report.magnetic
        is report.thermal
        is report.geometry
        is None
    )
    assert report.run_context.stage_status["semiconductor_design"] == "succeeded"
    (tmp_path / "selection_readback.json").write_text(
        json.dumps(asdict(report.t_type_engineering), indent=2), encoding="utf-8"
    )


@pytest.mark.parametrize("n", [1, 2, 3])
def test_independent_affine_curve_integral_and_equal_sharing(library, n):
    device = next(d for d in library.list_devices("IGBT") if model_rejection(d) is None)
    table = ConductionTable2D((0.0, 100.0), (25.0, 150.0), ((1.0, 11.0), (1.0, 11.0)))
    diode_table = replace(table, values_ti=((2.0, 7.0), (2.0, 7.0)))
    payload = replace(
        device.payload,
        igbt_loss_model=replace(device.payload.igbt_loss_model, conduction=table),
        frd_loss_model=replace(device.payload.frd_loss_model, conduction=diode_table),
    )
    device = replace(device, payload=payload)
    # Independent half-cycle piecewise constants: P = sum(duty*(V0*I+R*I²)).
    request = PositionConductionRequest(
        (700.0, 1.0, 1.0),
        "a_QA",
        "t_type_midpoint_switch",
        np.array([4.0, 0.0]),
        np.array([0.0, 6.0]),
        np.array([0.5, 0.5]),
    )
    _, channel, diode = position_losses(device, (request,), n, 100.0)[0]
    assert channel == pytest.approx(0.5 * ((4 / n) + 0.1 * (4 / n) ** 2), rel=1e-12)
    assert diode == pytest.approx(0.5 * (2 * (6 / n) + 0.05 * (6 / n) ** 2), rel=1e-12)
    assert n * (channel + diode) > 0


def test_real_quadrature_refinement_and_library_scalar_lookup(report, library):
    wave = PLUGIN.generate_waveforms(
        report.candidate, OperatingPoint(vin_v=700, load_ratio=1.0, power_factor=0.8)
    )
    payload = wave.metadata["three_phase_t_type_pd_spwm_waveforms"]
    device = library.get_device(
        report.device.selected_devices["t_type_midpoint_switch"]
    )
    coarse = build_position_requests(payload, (700.0, 1.0, 0.8), 8)
    refined = build_position_requests(payload, (700.0, 1.0, 0.8), 16)
    a = position_losses(device, coarse, 1, 100.0)
    b = position_losses(device, refined, 1, 100.0)
    for (_, c, d), (_, cc, dd) in zip(a, b):
        assert c == pytest.approx(cc, rel=1e-4, abs=1e-6)
        assert d == pytest.approx(dd, rel=1e-4, abs=1e-6)
    # Library's scalar lookup independently checks the vectorized interpolation.
    table = device.payload.igbt_loss_model.conduction
    currents = np.array([1.0, 2.0, 5.0, 10.0])
    weights = np.full(4, 0.25)
    expected = sum(
        w * i * abs(table.lookup(i, 100.0)) for i, w in zip(currents, weights)
    )
    assert integrate_conduction_table(table, currents, weights, 100.0) == pytest.approx(
        expected, rel=1e-12
    )


def test_conduction_evaluation_never_calls_energy(library, monkeypatch):
    device = next(d for d in library.list_devices("IGBT") if model_rejection(d) is None)

    def forbidden(*args, **kw):
        raise AssertionError("Energy evaluation invoked")

    for name in (
        "eon_mJ",
        "eoff_mJ",
        "err_mJ",
        "igbt_switching_loss_W",
        "frd_reverse_recovery_loss_W",
    ):
        monkeypatch.setattr(RohmRGIGBTDevice, name, forbidden)
    request = PositionConductionRequest(
        (700.0, 1.0, 1.0),
        "a_QP",
        "t_type_main_switch",
        np.array([2.0, 0.0]),
        np.array([0.0, 1.0]),
        np.array([0.5, 0.5]),
    )
    stress = SwitchStress(
        request.role,
        "selection_peak_bound_no_energy",
        800.0,
        2.0,
        1.0,
        2.0,
        2.0,
        20000.0,
        0.5,
        0.5 / 20000.0,
        ambient_temp_C=25.0,
        target_junction_temp_C=100.0,
    )
    loss, reference = evaluate_t_type_conduction_reference(
        device, stress, (request,), 1, 100.0
    )
    assert (
        loss.thermal_feasible and math.isfinite(loss.p_total_W) and loss.p_total_W > 0
    )
    assert loss.p_total_W == loss.p_cond_W
    assert loss.method == LOSS_SCOPE_ID
    assert reference.position_id == "a_QP"


@pytest.mark.parametrize(
    "kind", ["frd", "module", "nonfinite", "temperature", "current"]
)
def test_missing_invalid_and_out_of_range_models_rejected(library, kind):
    device = next(d for d in library.list_devices("IGBT") if model_rejection(d) is None)
    if kind == "frd":
        assert (
            model_rejection(
                replace(device, payload=replace(device.payload, frd_loss_model=None))
            )
            == "missing_antiparallel_diode_model"
        )
    elif kind == "module":
        module = next(
            d
            for d in library.list_devices("IGBT")
            if not isinstance(d.payload, RohmRGIGBTDevice)
        )
        assert model_rejection(module) == "unsupported_package_connection_or_technology"
    elif kind == "nonfinite":
        table = replace(device.payload.igbt_loss_model.conduction, scale=float("nan"))
        payload = replace(
            device.payload,
            igbt_loss_model=replace(device.payload.igbt_loss_model, conduction=table),
        )
        assert (
            model_rejection(replace(device, payload=payload))
            == "invalid_conduction_table"
        )
    else:
        table = device.payload.igbt_loss_model.conduction
        with pytest.raises(ValueError, match="out_of_table_range"):
            integrate_conduction_table(
                table,
                np.array([1e9 if kind == "current" else 1.0]),
                np.array([1.0]),
                1e9 if kind == "temperature" else 100.0,
            )


@pytest.mark.parametrize(
    "stage", ["capacitors", "system", "thermal", "geometry", "sweep"]
)
def test_unopened_stages_protected_on_direct_calls(report, stage):
    from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
    from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
    from pe_claw_gui.pipeline.run_loss_pipeline import run_loss_pipeline
    from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline
    from pe_claw_gui.pipeline.run_geometry_pipeline import run_geometry_pipeline
    from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep

    function = {
        "magnetics": run_magnetic_pipeline,
        "capacitors": run_capacitor_pipeline,
        "system": run_loss_pipeline,
        "thermal": run_thermal_pipeline,
        "geometry": run_geometry_pipeline,
        "sweep": run_efficiency_sweep,
    }[stage]
    assert not supports_engineering_stage(PLUGIN.topology_id, stage)
    with pytest.raises(RuntimeError, match="stage is unavailable"):
        function(report)


def test_fixed_candidate_refresh_retains_selection_without_reselect(
    report, monkeypatch
):
    import pe_claw_gui.pipeline.run_t_type_device_pipeline as stage

    def forbidden(*a, **kw):
        raise AssertionError("Unexpected reselection")

    monkeypatch.setattr(stage, "run_t_type_device_pipeline", forbidden)
    current = run_operating_point_refresh(
        report, PLUGIN, OperatingPoint(vin_v=800.0, load_ratio=0.5, power_factor=0.8)
    )
    assert current.device is report.device and current.candidate is report.candidate
    assert current.t_type_engineering is report.t_type_engineering
    assert current.waveform.operating_vin_v == 800 and current.loss is None


def test_scope_readback_and_structured_contract(report):
    from pe_claw_gui.app.result_views.device_view import build_device_summary_text
    from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
    from pe_claw_gui.reports.structured_output import build_structured_report
    from scripts.report_schema_validation import validate_report

    text = build_device_summary_text(report)
    assert (
        "conduction only" in text
        and "Current/system losses and efficiency: unavailable" in text
    )
    assert all(part in text for part in report.device.selected_devices.values())
    assert any(
        "Estimated efficiency: unavailable" in s
        for s in build_system_loss_summary(report)
    )
    payload = build_structured_report(report)
    assert not validate_report(payload)
    assert payload["engineering_result"]["loss_scope_id"] == LOSS_SCOPE_ID
    assert payload["loss"]["available"] is False


@pytest.mark.parametrize(
    "inputs",
    [
        {"engineering_vdc_min_v": "900"},
        {"engineering_pf_min": "0"},
        {"engineering_target_junction_temp_c": "20"},
        {"engineering_device_type": "MOSFET"},
        {"engineering_device_implementation": "Module"},
    ],
)
def test_invalid_engineering_inputs_have_diagnostics(inputs):
    with pytest.raises(ValueError, match="engineering|temperature"):
        PLUGIN.build_spec(inputs)


def test_independent_sink_backsolve_and_frd_rating_failure(library):
    device = next(d for d in library.list_devices("IGBT") if model_rejection(d) is None)
    request = PositionConductionRequest(
        (700.0, 1.0, 1.0),
        "a_QP",
        "t_type_main_switch",
        np.array([2.0, 0.0]),
        np.array([0.0, 1.0]),
        np.array([0.5, 0.5]),
    )
    stress = SwitchStress(
        request.role,
        "selection_peak_bound_no_energy",
        800.0,
        2.0,
        1.0,
        2.0,
        2.0,
        20000.0,
        0.5,
        0.5 / 20000.0,
        ambient_temp_C=25.0,
        target_junction_temp_C=100.0,
    )
    loss, _ = evaluate_t_type_conduction_reference(device, stress, (request,), 1, 100.0)
    rth = max(
        device.payload.static.rth_jc_igbt_K_per_W,
        device.payload.static.rth_jc_frd_K_per_W,
    )
    expected = 75 / loss.p_cond_W - rth - loss.interface_rth_cs_k_per_w
    assert loss.required_sink_rth_k_per_w == pytest.approx(expected, rel=1e-12)
    invalid, _ = evaluate_t_type_conduction_reference(
        device, replace(stress, ambient_temp_C=100.0), (request,), 1, 100.0
    )
    assert not invalid.thermal_feasible
    restricted = replace(
        device,
        payload=replace(
            device.payload, static=replace(device.payload.static, ie_cont_A=0.1)
        ),
    )
    with pytest.raises(ValueError, match="antiparallel_diode_current_rating_failed"):
        evaluate_t_type_conduction_reference(restricted, stress, (request,), 1, 100.0)


def test_schema_rejects_wrong_scope_missing_role_and_nonfinite_reference(report):
    import copy
    from pe_claw_gui.reports.structured_output import build_structured_report
    from scripts.report_schema_validation import validate_report

    payload = build_structured_report(report)
    for kind, expected in (
        ("scope", "scope"),
        ("role", "required_roles"),
        ("nonfinite", "reference"),
        ("package", "packages"),
        ("malformed", "reference"),
    ):
        invalid = copy.deepcopy(payload)
        engineering = invalid["engineering_result"]
        if kind == "scope":
            engineering["loss_scope_id"] = "npc_full"
        elif kind == "role":
            engineering["selected_devices"] = engineering["selected_devices"][:1]
        elif kind == "package":
            engineering["packages"] = engineering["packages"][:-1]
        elif kind == "malformed":
            engineering["role_selection_reference"] = None
        else:
            next(iter(engineering["role_selection_reference"].values()))[
                "per_device_channel_w"
            ] = float("nan")
        assert any(expected in error for error in validate_report(invalid))


@pytest.mark.parametrize("failure", ["none", "midpoint", "thermal"])
def test_selector_failure_preserves_audit_and_blocks_publication(
    report, library, monkeypatch, failure
):
    import pe_claw_gui.pipeline.run_t_type_device_pipeline as stage

    stresses = report.device.scheme_results[0].per_device_selection_stresses
    requests = tuple(
        PositionConductionRequest(
            (700.0, 1.0, 1.0),
            p,
            role,
            np.array([2.0, 0.0]),
            np.array([0.0, 1.0]),
            np.array([0.5, 0.5]),
        )
        for role, ids in ROLE_POSITIONS.items()
        for p in ids
    )
    monkeypatch.setattr(
        stage,
        "build_device_selection_requests",
        lambda *a: ({r: [s] for r, s in stresses.items()}, requests),
    )
    if failure == "none":
        monkeypatch.setattr(type(library), "search", lambda self, **kw: [])
    monkeypatch.setattr(stage, "build_default_semiconductor_registry", lambda: library)
    original = stage.evaluate_t_type_conduction_reference

    def evaluate(device, stress, *a):
        if failure == "midpoint" and stress.role == "t_type_midpoint_switch":
            raise ValueError("controlled_midpoint_model_failure")
        loss, reference = original(device, stress, *a)
        return (
            replace(loss, thermal_feasible=False) if failure == "thermal" else loss
        ), reference

    monkeypatch.setattr(stage, "evaluate_t_type_conduction_reference", evaluate)

    def forbidden(*a, **kw):
        raise AssertionError("Energy API invoked during selection")

    for name in (
        "eon_mJ",
        "eoff_mJ",
        "err_mJ",
        "igbt_switching_loss_W",
        "frd_reverse_recovery_loss_W",
    ):
        monkeypatch.setattr(RohmRGIGBTDevice, name, forbidden)
    result = stage.run_t_type_device_pipeline(report, PLUGIN)
    assert result.device.selected_devices == {}
    assert result.device.active_scheme_id is None
    assert (
        result.t_type_engineering.selected_devices
        == result.t_type_engineering.packages
        == ()
    )
    assert result.run_context.stage_status["semiconductor_design"] == "blocked"
    assert all(not s.feasible for s in result.device.scheme_results)
    assert result.device.selection_summaries
    if failure == "midpoint":
        assert any(
            "controlled_midpoint_model_failure" in reason
            for s in result.device.scheme_results
            for t in s.candidate_traces["t_type_midpoint_switch"]
            for reason in t["rejection_reasons"]
        )


def test_independent_actual_segment_conduction_integral(report, library):
    from scipy.integrate import quad

    wave = PLUGIN.generate_waveforms(
        report.candidate, OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=1.0)
    )
    payload = wave.metadata["three_phase_t_type_pd_spwm_waveforms"]
    basis = payload["basis"]
    omega = 2 * math.pi * basis["f_line_hz"]
    grid_peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    requests = {
        r.position_id: r for r in build_position_requests(payload, (700.0, 1.0, 1.0))
    }
    for position, state, sign, role in [
        ("a_QP", 1, 1, "t_type_main_switch"),
        ("a_QA", 0, -1, "t_type_midpoint_switch"),
    ]:
        device = library.get_device(report.device.selected_devices[role])
        table_channel = device.payload.igbt_loss_model.conduction
        table_diode = device.payload.frd_loss_model.conduction
        reference = [0.0, 0.0]
        for s in payload["segments"]:
            if s["states"][0] != state:
                continue

            def instantaneous(t, diode):
                # Independent scalar solution of L di/dt = vPWM - vgrid.
                i = sign * (
                    s["start_currents_a"][0]
                    + (
                        s["phase_neutral_voltages_v"][0] * (t - s["start_time_s"])
                        + grid_peak
                        / omega
                        * (math.cos(omega * t) - math.cos(omega * s["start_time_s"]))
                    )
                    / basis["inductance_h"]
                )
                magnitude = max(-i if diode else i, 0.0)
                table = table_diode if diode else table_channel
                return magnitude * abs(table.lookup(magnitude, 100.0))

            for diode in (0, 1):
                reference[diode] += (
                    quad(
                        lambda t: instantaneous(t, diode),
                        s["start_time_s"],
                        s["end_time_s"],
                        epsabs=1e-12,
                        epsrel=1e-8,
                        limit=100,
                    )[0]
                    * basis["f_line_hz"]
                )
        _, channel, diode = position_losses(device, (requests[position],), 1, 100.0)[0]
        assert channel == pytest.approx(reference[0], rel=1e-4, abs=1e-6)
        assert diode == pytest.approx(reference[1], rel=1e-4, abs=1e-6)

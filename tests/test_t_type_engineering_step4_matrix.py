"""Complete-hardware phase matrix and explicit fixed-bank boundaries."""
from dataclasses import replace

import pytest

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_t_type_hardware_refresh import refresh_t_type_hardware
from test_t_type_engineering_step4_refresh import check_current


@pytest.fixture(scope="module", params=("lagging", "leading"))
def hardware(request, tmp_path_factory):
    source = run_full_pipeline(PLUGIN, {"power_factor":".8", "power_factor_phase":request.param},
        include_waveforms=True, output_root=tmp_path_factory.mktemp("tt4-"+request.param))
    result = run_capacitor_pipeline(run_magnetic_pipeline(source))
    check_current(result)
    assert result.t_type_engineering.current_basis["power_factor_phase"] == request.param
    return result


@pytest.mark.parametrize("bus,load,pf", [(700, 1, None), (700, .5, .9), (800, .5, .9)])
def test_complete_phase_matrix_fixed_hardware(hardware, bus, load, pf):
    actual = refresh_t_type_hardware(hardware, OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf))
    assert actual.t_type_engineering.hardware == hardware.t_type_engineering.hardware
    if bus == 800:
        assert actual.t_type_engineering.refresh_status == "unavailable"
        assert "capacitor" in str(actual.t_type_engineering.refresh_diagnostics).lower()
        assert actual.waveform is None
        recovered = refresh_t_type_hardware(actual, OperatingPoint(vin_v=700, load_ratio=1))
        check_current(recovered)
    else:
        check_current(actual)
        assert actual.t_type_engineering.current_basis["power_factor"] == (pf or .8)
        assert actual.t_type_engineering.current_basis["load_ratio"] == load


@pytest.mark.parametrize("edit", ["fsw", "vac", "pf", "load", "nan_bus"])
def test_complete_hardware_input_boundaries_and_recovery(hardware, edit):
    point = OperatingPoint(vin_v=700, load_ratio=1, power_factor=.8)
    kwargs = {"fsw":{"switching_frequency_hz":25000}, "vac":{"vout_v":410},
        "pf":{"power_factor":-1}, "load":{"load_ratio":1.1}, "nan_bus":{"vin_v":float("nan")}}[edit]
    invalid = refresh_t_type_hardware(hardware, replace(point, **kwargs))
    assert invalid.t_type_engineering.refresh_status == "unavailable"
    assert not invalid.device.current_operating_losses
    assert invalid.waveform is None and invalid.t_type_engineering.capacitors.total_loss_w is None
    recovered = refresh_t_type_hardware(invalid, point)
    check_current(recovered)
    assert recovered.t_type_engineering.hardware == hardware.t_type_engineering.hardware


def test_unequal_actual_banks_explicit_update_and_Q_over_C(hardware):
    from pe_claw_gui.engines.capacitors.selection import evaluate_capacitor_bank
    from pe_claw_gui.pipeline.run_t_type_hardware_refresh import update_t_type_selected_hardware
    e, c = hardware.t_type_engineering, hardware.t_type_engineering.capacitors
    lower = c.selected_lower
    changed = evaluate_capacitor_bank(hardware.capacitor.output_selection.request,
        lower.candidate, parallel_count=lower.parallel_count*2, series_count=lower.series_count)
    assert changed.feasible
    edited = replace(hardware, t_type_engineering=replace(e, capacitors=replace(c, selected_lower=changed)),
        capacitor=replace(hardware.capacitor, output_selection=replace(hardware.capacitor.output_selection, recommended=changed)))
    actual = update_t_type_selected_hardware(edited)
    check_current(actual)
    ac, h = actual.t_type_engineering.capacitors, actual.t_type_engineering.hardware
    assert h.hardware_id != e.hardware.hardware_id
    assert h.lower_capacitance_f == 2*e.hardware.lower_capacitance_f
    assert h.lower_esr_ohm == e.hardware.lower_esr_ohm/2
    assert actual.candidate == hardware.candidate
    for side in ("upper", "lower"):
        assert ac.voltage_ripple[side+"_capacitive_pp_v"] == pytest.approx(
            ac.port_metrics["banks"][side]["raw_q_swing_c"] / getattr(h, side+"_capacitance_f"))

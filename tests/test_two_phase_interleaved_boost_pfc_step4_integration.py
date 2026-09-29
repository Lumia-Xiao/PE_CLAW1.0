from __future__ import annotations

from importlib import import_module
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


def test_step4_registry_capability_and_legacy_routing() -> None:
    from pe_claw_gui.topologies.base.capabilities import PLUGIN_HOOKS
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    definition = registry.get_definition(TOPOLOGY_ID)
    capability = registry.get_capability(TOPOLOGY_ID)
    plugin = registry.get_plugin(TOPOLOGY_ID)

    assert definition.category_id == "ac_dc"
    assert definition.implemented is False
    assert registry.resolve_topology_id(definition.legacy_key) == TOPOLOGY_ID
    assert capability.capability_id == "ac_dc_single_phase_interleaved_boost_pfc"
    assert capability.support_status == "planned"
    assert capability.hooks == PLUGIN_HOOKS
    assert all(callable(getattr(plugin, hook)) for hook in PLUGIN_HOOKS)


def test_step4_form_matches_frozen_inputs_without_phase_controls() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry

    form_class = build_default_registry().get_form_class(TOPOLOGY_ID)
    field_keys = [field.key for field in form_class.get_design_fields()]
    assert form_class.implemented is False
    assert field_keys[:13] == [
        "vac_rms",
        "vac_rms_min",
        "vac_rms_max",
        "f_line_hz",
        "vdc_target_v",
        "pout_w",
        "fsw_hz",
        "dc_bus_ripple_percent",
        "inductor_current_ripple_ratio",
        "power_factor_target",
        "input_inductance_h",
        "ambient_temp_c",
        "target_junction_temp_c",
    ]
    assert "sizing_efficiency_assumption" not in field_keys
    assert "phase_count" not in field_keys
    assert "phase_shift_deg" not in field_keys


def test_step4_topology_local_report_does_not_attach_downstream_stages() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry

    registry = build_default_registry()
    plugin = registry.get_plugin(TOPOLOGY_ID)
    module = import_module(plugin.__module__)
    spec = plugin.build_spec(module.build_default_inputs())
    candidate = plugin.synthesize(spec)
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)
    result = plugin.evaluate(candidate, waveform, stress)
    report = plugin.build_report(
        spec,
        candidate,
        waveform_set=waveform,
        stress_result=stress,
        topology_result=result,
    )

    assert report.topology_result is not None
    assert report.topology_result.topology_id == TOPOLOGY_ID
    assert report.waveform is waveform
    assert report.stress is stress
    assert report.device is None
    assert report.bridge_rectifier is None
    assert report.magnetic is None
    assert report.loss is None
    assert report.thermal is None
    assert report.geometry is None


def test_step4_import_is_side_effect_free() -> None:
    env = {
        **__import__("os").environ,
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    code = (
        "import pathlib; "
        "before=sorted(str(p) for p in pathlib.Path('outputs').glob('**/*')) if pathlib.Path('outputs').exists() else []; "
        "import pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge as m; "
        "assert m.PLUGIN.implemented is False; "
        "after=sorted(str(p) for p in pathlib.Path('outputs').glob('**/*')) if pathlib.Path('outputs').exists() else []; "
        "assert before == after"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

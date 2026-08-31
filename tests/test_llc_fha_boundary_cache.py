from __future__ import annotations

import pytest

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
    clear_fha_boundary_frequency_cache,
    design_llc_fha,
    fha_boundary_frequency_cache_info,
    solve_operating_frequency,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
    build_transformer_design_inputs_from_fha,
    make_fha_boundary_frequency_solver,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (
    build_default_inputs,
    build_spec,
)


@pytest.fixture
def fha_design():
    return design_llc_fha(build_spec(build_default_inputs()))


def test_fha_boundary_cache_reuses_identical_result(fha_design) -> None:
    clear_fha_boundary_frequency_cache()
    first = solve_operating_frequency(fha_design, 400.0, 48.0, 4000.0)
    after_first = fha_boundary_frequency_cache_info()
    second = solve_operating_frequency(fha_design, 400.0, 48.0, 4000.0)
    after_second = fha_boundary_frequency_cache_info()

    assert second == first
    assert after_first["misses"] == 1
    assert after_first["hits"] == 0
    assert after_second["misses"] == 1
    assert after_second["hits"] == 1
    assert after_second["size"] == 1


def test_fha_boundary_cache_key_includes_solver_inputs(fha_design) -> None:
    clear_fha_boundary_frequency_cache()
    solve_operating_frequency(fha_design, 400.0, 48.0, 4000.0)
    solve_operating_frequency(fha_design, 399.0, 48.0, 4000.0)
    solve_operating_frequency(fha_design, 400.0, 48.0, 3900.0)

    info = fha_boundary_frequency_cache_info()
    assert info["misses"] == 3
    assert info["size"] == 3


def test_fha_boundary_cache_is_bounded(fha_design) -> None:
    clear_fha_boundary_frequency_cache()
    for index in range(520):
        solve_operating_frequency(fha_design, 300.0 + index, 48.0, 4000.0)

    info = fha_boundary_frequency_cache_info()
    assert info["size"] == info["maxsize"]
    assert info["misses"] == 520


def test_invalid_fha_inputs_keep_original_exception_contract(fha_design) -> None:
    clear_fha_boundary_frequency_cache()
    with pytest.raises(ValueError, match="must be positive"):
        solve_operating_frequency(fha_design, 0.0, 48.0, 4000.0)
    assert fha_boundary_frequency_cache_info()["size"] == 0


def test_coverage_solver_uses_shared_cache(fha_design) -> None:
    clear_fha_boundary_frequency_cache()
    inputs = build_transformer_design_inputs_from_fha(fha_design)
    solver = make_fha_boundary_frequency_solver(fha_design)

    first = solver(inputs, "Vin_nom/Vout_nom/Pmax", 400.0, 48.0, 4000.0)
    second = solver(inputs, "Vin_nom/Vout_nom/Pmax", 400.0, 48.0, 4000.0)
    info = fha_boundary_frequency_cache_info()

    assert second == first
    assert info["size"] == 1
    assert info["hits"] == 1

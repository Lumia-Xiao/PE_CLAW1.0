from __future__ import annotations

import math
import random
import time
from types import SimpleNamespace

from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
    LLC_PARETO_FILTER_ALGORITHM,
    _build_llc_2d_pareto_front,
    _build_llc_2d_pareto_front_reference,
)


def _candidate(identifier: str, volume: float, loss: float) -> SimpleNamespace:
    return SimpleNamespace(candidate_id=identifier, design_id=identifier, volume=volume, loss=loss)


def _optimized(items):
    return _build_llc_2d_pareto_front(
        items,
        volume_key=lambda item: item.volume,
        loss_key=lambda item: item.loss,
        identifier_key=lambda item: item.candidate_id,
    )


def _reference(items):
    return _build_llc_2d_pareto_front_reference(
        items,
        volume_key=lambda item: item.volume,
        loss_key=lambda item: item.loss,
        identifier_key=lambda item: item.candidate_id,
    )


def test_llc_pareto_filter_handles_empty_single_equal_and_dominated_cases() -> None:
    assert _optimized([]) == []
    single = [_candidate("single", 1.0, 2.0)]
    assert _optimized(single) == single
    items = [
        _candidate("equal-a", 1.0, 1.0),
        _candidate("equal-b", 1.0, 1.0),
        _candidate("dominated", 2.0, 2.0),
        _candidate("tradeoff", 2.0, 0.5),
    ]
    assert [item.candidate_id for item in _optimized(items)] == ["equal-a", "equal-b", "tradeoff"]


def test_llc_pareto_filter_matches_reference_for_special_values_and_duplicate_ids() -> None:
    items = [
        _candidate("finite-a", 1.0, 3.0),
        _candidate("finite-b", 2.0, 2.0),
        _candidate("same-id-worse", 2.0, 9.0),
        _candidate("same-id-worse", 3.0, 1.0),
        _candidate("nan-volume", math.nan, 0.0),
        _candidate("inf-loss", 0.5, math.inf),
    ]
    assert [item.candidate_id for item in _optimized(items)] == [item.candidate_id for item in _reference(items)]


def test_llc_pareto_filter_matches_reference_on_random_finite_inputs() -> None:
    rng = random.Random(20260829)
    for _ in range(20):
        items = [
            _candidate(f"candidate-{index}", rng.randrange(1, 100), rng.randrange(1, 100))
            for index in range(120)
        ]
        assert [item.candidate_id for item in _optimized(items)] == [item.candidate_id for item in _reference(items)]


def test_llc_pareto_filter_scales_better_than_reference_on_medium_input() -> None:
    items = [
        _candidate(f"candidate-{index}", float(index), float(900 - index))
        for index in range(900)
    ]
    optimized_started = time.perf_counter()
    optimized = _optimized(items)
    optimized_seconds = time.perf_counter() - optimized_started
    reference_started = time.perf_counter()
    reference = _reference(items)
    reference_seconds = time.perf_counter() - reference_started

    assert [item.candidate_id for item in optimized] == [item.candidate_id for item in reference]
    assert optimized_seconds < reference_seconds
    assert LLC_PARETO_FILTER_ALGORITHM == "finite-2d-sweep-v1"

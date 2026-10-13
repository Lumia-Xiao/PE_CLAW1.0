"""Topology-owned design envelope and direction-aware conduction requests."""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
import numpy as np
from ....models.device_loss import SwitchStress
from ....models.operating_point import OperatingPoint
from ....models.t_type_engineering import TTypeDesignBasis
from .integration import ANGLES, segment_current, current_zero_times
from .stress import stress_readback, PAYLOAD_KEY
from .topology_contract import TOPOLOGY_ID

ROLE_POSITIONS = {
    "t_type_main_switch": tuple(f"{p}_{r}" for p in "abc" for r in ("QP", "QN")),
    "t_type_midpoint_switch": tuple(f"{p}_{r}" for p in "abc" for r in ("QA", "QO")),
}


@dataclass(frozen=True)
class PositionConductionRequest:
    case: tuple[float, float, float]
    position_id: str
    role: str
    channel_a: np.ndarray
    diode_a: np.ndarray
    weights: np.ndarray


def candidate_fingerprint(candidate):
    from dataclasses import asdict

    return hashlib.sha256(
        json.dumps(asdict(candidate), sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def build_design_basis(report):
    if (
        report.candidate is None
        or report.candidate.topology_id != TOPOLOGY_ID
        or report.spec.topology_id != TOPOLOGY_ID
    ):
        raise ValueError("T-type design source identity mismatch")
    m = report.spec.metadata
    cases = tuple(
        itertools.product(
            sorted(set((m["engineering_vdc_min_v"], m["engineering_vdc_max_v"]))),
            sorted(set((m["engineering_load_min"], 0.5, m["engineering_load_max"]))),
            sorted(set((m["engineering_pf_min"], m["engineering_pf_max"]))),
        )
    )
    cases = tuple(
        c
        for c in cases
        if m["engineering_load_min"] <= c[1] <= m["engineering_load_max"]
    )
    return TTypeDesignBasis(
        TOPOLOGY_ID,
        getattr(report.run_context, "run_id", None),
        candidate_fingerprint(report.candidate),
        cases,
        m["power_factor_phase"],
        m["engineering_ambient_temp_c"],
        m["engineering_target_junction_temp_c"],
        m["engineering_target_junction_temp_c"],
        report.candidate.pout_target,
        report.candidate.vout_target,
        m["f_line_hz"],
        report.candidate.fs_hz,
        report.candidate.inductance_h,
        0.20,
        0.10,
    )


def build_position_requests(payload, case, order=8):
    """Gauss quadrature within exact ideal-L segments; no sampled switch-edge interpolation."""
    basis = payload["basis"]
    nodes, weights = np.polynomial.legendre.leggauss(order)
    segments = payload["segments"]
    start = np.array([s["start_time_s"] for s in segments])
    end = np.array([s["end_time_s"] for s in segments])
    if (
        not np.all(np.isfinite(start))
        or not np.all(end > start)
        or not np.allclose(start[1:], end[:-1], rtol=0, atol=1e-12)
    ):
        raise ValueError("Invalid T-type segment time axis")
    duration = end[-1] - start[0]
    t = (start[:, None] + end[:, None]) / 2 + (end - start)[:, None] * nodes / 2
    w = np.broadcast_to(
        (end - start)[:, None] * weights / (2 * duration), t.shape
    ).ravel()
    omega = 2 * math.pi * basis["f_line_hz"]
    peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    requests = []
    for phase_index, phase in enumerate("abc"):
        initial = np.array([s["start_currents_a"][phase_index] for s in segments])[
            :, None
        ]
        voltage = np.array(
            [s["phase_neutral_voltages_v"][phase_index] for s in segments]
        )[:, None]
        currents = (
            initial
            + (
                voltage * (t - start[:, None])
                + peak
                / omega
                * (
                    np.cos(omega * t + ANGLES[phase_index])
                    - np.cos(omega * start[:, None] + ANGLES[phase_index])
                )
            )
            / basis["inductance_h"]
        )
        states = np.array([s["states"][phase_index] for s in segments])[:, None]
        for r, state, sign in (
            ("QP", 1, 1),
            ("QN", -1, -1),
            ("QA", 0, -1),
            ("QO", 0, 1),
        ):
            local = np.where(states == state, sign * currents, 0).ravel()
            role = (
                "t_type_main_switch" if r in ("QP", "QN") else "t_type_midpoint_switch"
            )
            channel = np.maximum(local, 0)
            diode = np.maximum(-local, 0)
            for array in (channel, diode, w):
                array.setflags(write=False)
            requests.append(
                PositionConductionRequest(case, f"{phase}_{r}", role, channel, diode, w)
            )
    return tuple(requests)


def build_device_selection_requests(report, design_basis, plugin):
    if (
        plugin.topology_id != TOPOLOGY_ID
        or candidate_fingerprint(report.candidate) != design_basis.candidate_fingerprint
    ):
        raise ValueError("T-type design request source mismatch")
    requests = []
    stresses = {r: [] for r in ROLE_POSITIONS}
    for case in design_basis.cases:
        bus, load, pf = case
        wave = plugin.generate_waveforms(
            report.candidate,
            OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf),
        )
        actual = stress_readback(report.candidate, wave)
        requests.extend(build_position_requests(wave.metadata[PAYLOAD_KEY], case))
        # Conduction fractions use exact zero-crossing intervals, not dead time.
        fractions = conduction_fractions(wave.metadata[PAYLOAD_KEY])
        for role, ids in ROLE_POSITIONS.items():
            metrics = [actual["positions"][p] for p in ids]
            peak = max(max(v["channel_peak_a"], v["diode_peak_a"]) for v in metrics)
            rms = max(max(v["channel_rms_a"], v["diode_rms_a"]) for v in metrics)
            avg = max(v["channel_avg_a"] for v in metrics)
            channel_fraction = max(fractions[p][0] for p in ids)
            diode_fraction = max(fractions[p][1] for p in ids)
            stresses[role].append(
                SwitchStress(
                    role,
                    "selection_peak_bound_no_energy",
                    bus * (1 if role == "t_type_main_switch" else 0.5),
                    rms,
                    avg,
                    peak,
                    peak,
                    report.candidate.fs_hz,
                    channel_fraction,
                    channel_fraction / report.candidate.fs_hz,
                    body_diode_conduction_time_s=diode_fraction
                    / report.candidate.fs_hz,
                    ambient_temp_C=design_basis.ambient_temp_c,
                    target_junction_temp_C=design_basis.target_junction_temp_c,
                )
            )
    return stresses, tuple(requests)


def conduction_fractions(payload):
    durations = {p: [0.0, 0.0] for ids in ROLE_POSITIONS.values() for p in ids}
    period = 1 / payload["basis"]["f_line_hz"]
    for segment in payload["segments"]:
        for index, phase in enumerate("abc"):
            current, extrema = segment_current(segment, index, payload["basis"])
            splits = current_zero_times(current, extrema)
            for r, state, sign in (
                ("QP", 1, 1),
                ("QN", -1, -1),
                ("QA", 0, -1),
                ("QO", 0, 1),
            ):
                if segment["states"][index] != state:
                    continue
                for left, right in zip(splits, splits[1:]):
                    value = sign * current((left + right) / 2)
                    if value != 0:
                        durations[f"{phase}_{r}"][int(value < 0)] += (
                            right - left
                        ) / period
    return durations

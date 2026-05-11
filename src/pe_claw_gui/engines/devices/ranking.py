"""Device ranking helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ...libraries.semiconductors.power_device import PowerDevice
from ...models.device_loss import DeviceLossResult

LOSS_WEIGHT = 0.70
TJ_WEIGHT = 0.30


@dataclass(frozen=True)
class RankedDeviceCandidate:
    """One ranked device candidate with its estimated operating-point loss."""

    device: PowerDevice
    score: float
    loss_result: DeviceLossResult
    ranking_notes: list[str]


def rank_switch_candidates(
    candidates: Sequence[tuple[PowerDevice, DeviceLossResult]],
    *,
    loss_weight: float = LOSS_WEIGHT,
    tj_weight: float = TJ_WEIGHT,
) -> list[RankedDeviceCandidate]:
    """Rank surviving switch candidates by normalized weighted loss and Tj."""

    if not candidates:
        return []

    losses = [loss_result.p_total_W for _, loss_result in candidates]
    junction_temps = [loss_result.tj_est_C for _, loss_result in candidates]
    min_loss, max_loss = min(losses), max(losses)
    min_tj, max_tj = min(junction_temps), max(junction_temps)

    ranked = []
    for device, loss_result in candidates:
        normalized_loss = _normalize(loss_result.p_total_W, min_loss, max_loss)
        normalized_tj = _normalize(loss_result.tj_est_C, min_tj, max_tj)
        score = (loss_weight * normalized_loss) + (tj_weight * normalized_tj)
        ranking_notes = [
            f"score={score:.6g}",
            f"normalized_loss={normalized_loss:.6g}",
            f"normalized_tj={normalized_tj:.6g}",
            f"weights loss={loss_weight:.3g}, tj={tj_weight:.3g}",
        ]
        ranked.append(
            RankedDeviceCandidate(
                device=device,
                score=score,
                loss_result=loss_result,
                ranking_notes=ranking_notes,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (
            item.score,
            item.loss_result.p_total_W,
            item.loss_result.tj_est_C,
            item.device.static.rds_on_typ_25C_Ohm,
            -item.device.static.vdss_max_V,
            item.device.part_number,
        ),
    )


def _normalize(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    return (value - lower) / (upper - lower)

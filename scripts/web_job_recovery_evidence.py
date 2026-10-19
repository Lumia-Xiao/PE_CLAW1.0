"""Print only checkpoint and selected-hardware digests for Windows acceptance."""

from __future__ import annotations

import argparse
import json

from pe_claw_web.jobs.checkpoints import checksum, decode, encode
from pe_claw_web.jobs.store import store


SELECTION_STAGE_ORDER = ("topology", "devices", "capacitor", "magnetics")


def hardware_digest(checkpoint: dict, through_stage: str | None = None) -> str:
    report = decode(checkpoint["report"])
    boundary = through_stage or checkpoint.get("completed_stage")
    if boundary not in SELECTION_STAGE_ORDER:
        # Stages after magnetics retain all selected hardware.
        boundary = "magnetics"
    selection_index = SELECTION_STAGE_ORDER.index(boundary)
    capacitors = {}
    if selection_index >= SELECTION_STAGE_ORDER.index("capacitor") and report.capacitor is not None:
        for side in ("input_selection", "output_selection"):
            selection = getattr(report.capacitor, side)
            chosen = selection.recommended if selection is not None else None
            if chosen is not None:
                capacitors[side] = {
                    "candidate": encode(chosen.candidate),
                    "parallel_count": chosen.parallel_count,
                    "series_count": chosen.series_count,
                }
    return checksum(
        {
            "candidate": encode(report.candidate) if selection_index >= 0 else None,
            "devices": report.device.selected_devices
            if selection_index >= SELECTION_STAGE_ORDER.index("devices") and report.device
            else {},
            "capacitors": capacitors,
            "magnetic": encode(report.magnetic)
            if selection_index >= SELECTION_STAGE_ORDER.index("magnetics") and report.magnetic
            else None,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id")
    parser.add_argument("--through-stage", choices=SELECTION_STAGE_ORDER)
    args = parser.parse_args()
    checkpoint = store.get_checkpoint(args.job_id)
    if not checkpoint:
        raise SystemExit("Checkpoint is not available")
    print(
        json.dumps(
            {
                "schema_version": "1.0",
                "job_id": args.job_id,
                "completed_stage": checkpoint.get("completed_stage"),
                "checkpoint_sha256": checkpoint.get("sha256"),
                "hardware_boundary": args.through_stage or checkpoint.get("completed_stage"),
                "hardware_sha256": hardware_digest(checkpoint, args.through_stage),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

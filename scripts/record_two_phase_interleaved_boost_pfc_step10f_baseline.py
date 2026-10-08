"""Record the post-10E two-phase baseline without replacing historical evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.record_two_phase_interleaved_boost_pfc_step10a_baseline import build_baseline


def build_step10f_baseline() -> dict[str, object]:
    baseline = build_baseline()
    baseline["schema_version"] = "two_phase_interleaved_boost_pfc_step10f_baseline_v1"
    baseline["scope"]["step"] = "10F post-10E result views and unchanged 10D engineering boundary"
    return baseline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_step10f_baseline(), indent=2, sort_keys=True) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()

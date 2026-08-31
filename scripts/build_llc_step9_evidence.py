"""Build evidence for the LLC magnetic output-policy reduction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pe_claw_gui.pipeline.run_magnetic_pipeline import _llc_output_policy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text(encoding="ascii"))
    formal = _llc_output_policy(debug_outputs=False, geometry_roles=None)
    diagnostic = _llc_output_policy(debug_outputs=True, geometry_roles=None)
    case_summary = []
    for case in baseline.get("cases", []):
        transformer = case.get("transformer") or {}
        external_lr = case.get("external_lr") or {}
        case_summary.append(
            {
                "case": case.get("case"),
                "status": case.get("status"),
                "transformer_total_seconds": (transformer.get("timing") or {}).get("total_seconds"),
                "transformer_debug_output_seconds": (transformer.get("timing") or {}).get("debug_output_seconds"),
                "transformer_generated_candidate_count": (transformer.get("counts") or {}).get("generated_candidate_count"),
                "transformer_precise_evaluated_candidate_count": (transformer.get("counts") or {}).get("precise_evaluated_candidate_count"),
                "external_lr_total_seconds": (external_lr.get("timing") or {}).get("total_seconds"),
                "external_lr_debug_output_seconds": (external_lr.get("timing") or {}).get("debug_output_seconds"),
                "external_lr_generated_candidate_count": (external_lr.get("counts") or {}).get("generated_candidate_count"),
                "external_lr_precise_evaluated_candidate_count": (external_lr.get("counts") or {}).get("precise_evaluated_candidate_count"),
            }
        )

    payload = {
        "schema_version": "llc_magnetic_output_policy_step9_v1",
        "baseline_file": str(args.baseline),
        "formal_mode": formal,
        "diagnostic_mode": diagnostic,
        "repeat_run_strategy": {
            "formal_geometry_root": "outputs/resonant_inductor_design",
            "diagnostic_root": "outputs/llc_diagnostics",
            "diagnostic_outputs_are_opt_in": True,
            "stable_role_file_names": True,
        },
        "benchmark_cases": case_summary,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "llc_magnetic_output_policy.json"
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(json.dumps({"output": str(output), "case_count": len(case_summary)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

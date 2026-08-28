"""Freeze repeatable LLC magnetic-search performance evidence.

The benchmark deliberately calls the LLC magnetic helpers directly with bounded
search sizes.  This keeps baseline collection auditable and prevents evidence
generation from silently invoking the unbounded GUI-scale search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.engines.magnetics.data_backend import (  # noqa: E402
    get_production_magnetic_backend_config,
    resolve_magnetic_data_backend,
)
from pe_claw_gui.engines.magnetics.core_loss_kernel import (  # noqa: E402
    clear_scalar_triangular_loss_cache,
    scalar_triangular_loss_cache_info,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (  # noqa: E402
    clear_fha_boundary_frequency_cache,
    design_llc_fha,
    fha_boundary_frequency_cache_info,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import (  # noqa: E402
    build_default_inputs,
    build_spec,
)
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (  # noqa: E402
    build_llc_external_resonant_inductor_target,
    build_transformer_design_inputs_from_fha,
    generate_llc_external_resonant_inductor_candidates,
    generate_separated_llc_transformer_candidates,
    make_fha_boundary_frequency_solver,
)


CASES: dict[str, dict[str, int]] = {
    "transformer-small": {"core_limit": 2, "material_limit": 2, "wire_limit": 4, "max_scale_factor": 4},
    "transformer-medium": {"core_limit": 4, "material_limit": 4, "wire_limit": 8, "max_scale_factor": 8},
    "external-lr-small": {"core_limit": 2, "material_limit": 2, "wire_limit": 3},
    "external-lr-medium": {"core_limit": 4, "material_limit": 4, "wire_limit": 5},
}

EXTERNAL_LR_TRANSFORMER_SEED_LIMITS = {
    "core_limit": 4,
    "material_limit": 4,
    "wire_limit": 8,
    "max_scale_factor": 8,
}


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _representative(candidate: object | None, *, external: bool = False) -> dict[str, object] | None:
    if candidate is None:
        return None
    if external:
        return {
            "design_id": candidate.design_id,
            "core_id": candidate.core_id,
            "material_name": candidate.material_name,
            "turns": candidate.turns,
            "total_loss_w": candidate.total_loss_w,
            "estimated_volume_cm3": candidate.estimated_volume_cm3,
            "hotspot_c": candidate.hotspot_c,
        }
    return {
        "candidate_id": candidate.candidate_id,
        "core_id": candidate.core_id,
        "material_id": candidate.material_id,
        "np": candidate.np,
        "ns": candidate.ns,
        "total_loss_w": candidate.total_loss_w,
        "estimated_volume_cm3": candidate.estimated_volume_cm3,
        "hotspot_c": candidate.hotspot_c,
    }


def _run_case(case_name: str) -> dict[str, object]:
    limits = CASES[case_name]
    transformer_limits = EXTERNAL_LR_TRANSFORMER_SEED_LIMITS if case_name.startswith("external-lr") else limits
    clear_fha_boundary_frequency_cache()
    clear_scalar_triangular_loss_cache()
    spec = build_spec(build_default_inputs())
    fha_design = design_llc_fha(spec)
    transformer_inputs = build_transformer_design_inputs_from_fha(fha_design)
    backend_config = get_production_magnetic_backend_config()
    backend_bundle = resolve_magnetic_data_backend(backend_config)
    input_payload = {
        "topology_id": spec.topology_id,
        "raw_input": dict(spec.raw_input),
        "fha_design": asdict(fha_design),
        "search_limits": limits,
    }
    result: dict[str, object] = {
        "case": case_name,
        "status": "completed",
        "input_sha256": _sha256_payload(input_payload),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "backend": backend_bundle.backend,
        "backend_mode": backend_bundle.mode,
        "backend_provenance": dict(backend_bundle.provenance),
        "registered_database_counts": {
            "cores": len(backend_bundle.cores),
            "materials": len(backend_bundle.materials),
            "wires": len(backend_bundle.wires),
        },
        "search_limits": limits,
        "fha_boundary_cache": None,
        "scalar_triangular_loss_cache": None,
        "transformer": None,
        "external_lr": None,
    }
    if case_name.startswith("transformer") or case_name.startswith("external-lr"):
        transformer_result = generate_separated_llc_transformer_candidates(
            transformer_inputs,
            core_records=backend_bundle.cores,
            material_records=backend_bundle.materials,
            wire_records=backend_bundle.wires,
            max_scale_factor=transformer_limits.get("max_scale_factor", 8),
            frequency_solver=make_fha_boundary_frequency_solver(fha_design),
            core_limit=transformer_limits["core_limit"],
            material_limit=transformer_limits["material_limit"],
            wire_limit=transformer_limits["wire_limit"],
            write_debug_csv=False,
        )
        result["transformer"] = {
            "timing": transformer_result.performance_timing,
            "counts": {
                **transformer_result.performance_counts,
                "registered_core_count": transformer_result.registered_core_count,
                "registered_material_count": transformer_result.registered_material_count,
                "registered_wire_count": transformer_result.registered_wire_count,
                "rejected_by_saturation_count": transformer_result.rejected_by_saturation_count,
                "rejected_by_lm_count": transformer_result.rejected_by_lm_count,
                "rejected_by_leakage_count": transformer_result.rejected_by_leakage_count,
                "rejected_by_fill_count": transformer_result.rejected_by_fill_count,
                "rejected_by_thermal_count": transformer_result.rejected_by_thermal_count,
                "rejected_by_missing_data_count": transformer_result.rejected_by_missing_data_count,
            },
            "search_bounds": transformer_result.search_bounds,
            "representative": _representative(transformer_result.recommended_preliminary_candidate),
        }
        result["fha_boundary_cache"] = fha_boundary_frequency_cache_info()
        scalar_cache = scalar_triangular_loss_cache_info()
        result["scalar_triangular_loss_cache"] = {
            "hits": scalar_cache.hits,
            "misses": scalar_cache.misses,
            "maxsize": scalar_cache.maxsize,
            "size": scalar_cache.currsize,
            "model_version": "llc_scalar_triangular_igse_v1",
        }
        if case_name.startswith("external-lr") and transformer_result.recommended_preliminary_candidate is not None:
            external_target = build_llc_external_resonant_inductor_target(
                fha_design,
                transformer_result.recommended_preliminary_candidate,
            )
            external_result = generate_llc_external_resonant_inductor_candidates(
                external_target,
                core_records=backend_bundle.cores,
                material_records=backend_bundle.materials,
                wire_records=backend_bundle.wires,
                core_limit=limits["core_limit"],
                material_limit=limits["material_limit"],
                wire_limit=limits["wire_limit"],
                write_csv=False,
            )
            result["external_lr"] = {
                "timing": external_result.performance_timing,
                "counts": {
                    **external_result.performance_counts,
                    "rejection_counts": external_result.rejection_counts,
                },
                "search_bounds": external_result.search_bounds,
                "representative": _representative(external_result.recommended_candidate, external=True),
            }
    return result


def _worker(case_name: str, result_queue: mp.Queue) -> None:
    try:
        result_queue.put(_run_case(case_name))
    except Exception as exc:  # pragma: no cover - surfaced in the parent result.
        result_queue.put({"case": case_name, "status": "error", "error": f"{type(exc).__name__}: {exc}"})


def _run_with_timeout(case_name: str, timeout_seconds: float) -> dict[str, object]:
    context = mp.get_context("spawn")
    result_queue = context.Queue()
    process = context.Process(target=_worker, args=(case_name, result_queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5.0)
        return {
            "case": case_name,
            "status": "timeout",
            "timeout_seconds": timeout_seconds,
        }
    try:
        return result_queue.get_nowait()
    except Empty:
        return {"case": case_name, "status": "error", "error": f"worker exited with code {process.exitcode}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--case", action="append", choices=sorted(CASES), dest="cases")
    args = parser.parse_args()
    cases = args.cases or list(CASES)
    results = [_run_with_timeout(case_name, args.timeout_seconds) for case_name in cases]
    completed_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "llc_magnetic_performance_baseline_v1",
        "created_at_utc": completed_at,
        "repository": str(ROOT),
        "cases": results,
        "summary": {
            "case_count": len(results),
            "completed_count": sum(item.get("status") == "completed" for item in results),
            "timeout_count": sum(item.get("status") == "timeout" for item in results),
            "error_count": sum(item.get("status") == "error" for item in results),
        },
    }
    output_dir = args.output_dir or ROOT / "migration" / "evidence" / datetime.now().strftime("%Y%m%d") / "llc_magnetic_performance"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "llc_magnetic_performance_baseline.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii", newline="\n")
    print(json.dumps({"output": str(output_path), "summary": payload["summary"]}, sort_keys=True))
    return 0 if payload["summary"]["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

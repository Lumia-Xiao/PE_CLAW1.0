"""Post-remediation Step 19E evidence aggregation and reviewed rollout gate."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

from .core_loss_ab_rerun_manifest import REQUIRED_ROLES


STEP19E_PHYSICAL_CONTRACT = "openmagnetics-step19e-physical-consistency-v1"
STEP19E_RANKING_CONTRACT = "openmagnetics-step19e-candidate-ranking-v1"
STEP19E_GATE_CONTRACT = "openmagnetics-step19e-reviewed-rollout-gate-v1"
COMPARISON_LAYERS = (
    "historical_v1_baseline",
    "pre_remediation_v2_free_selection",
    "post_step19_remediation",
)
CURRENT_LAYER_FIELDS = (
    "selected_design_id", "core_id", "material_id", "wire_id", "turns",
    "parallel_count", "stack_count", "gap_m", "effective_magnetic_volume_m3",
    "flux_peak_to_peak_t", "flux_dc_offset_t", "flux_absolute_peak_t",
    "core_loss_w", "copper_loss_w", "total_loss_w", "total_volume_m3",
    "fill_factor", "current_density_a_per_mm2", "saturation_margin",
    "thermal_status", "model_validity",
)


def build_step19e_physical_audit(sources: Mapping[str, Any], input_hashes: Mapping[str, str]) -> dict[str, Any]:
    """Build seven passed physical records from role-specific Step 19 authority."""
    current = build_post_step19_layers(sources)
    authority = _authority_by_role(sources)
    records: list[dict[str, Any]] = []
    for role in REQUIRED_ROLES:
        selected = current[role]
        checks = authority[role]["checks"]
        if not checks or not all(item["status"] == "pass" for item in checks):
            raise ValueError(f"{role}: Step 19E physical authority did not pass.")
        _validate_selected_layer(role, selected)
        records.append({
            "role": role,
            "physical_status": "pass",
            "selection_status": "selected",
            "selected_design_id": selected["selected_design_id"],
            "authority_paths": authority[role]["paths"],
            "checks": checks,
            "warnings": authority[role].get("warnings", []),
            "blockers": [],
            "current_candidate": selected,
        })
    payload = {
        "contract_version": STEP19E_PHYSICAL_CONTRACT,
        "scope": "post_step19_remediation_seven_role_physical_consistency",
        "backend": "packaged_normalized_v2_explicit_opt_in",
        "required_roles": list(REQUIRED_ROLES),
        "input_hashes": dict(sorted(input_hashes.items())),
        "roles": records,
        "summary": {
            "role_count": len(records),
            "all_roles_audited": True,
            "all_roles_pass": True,
            "status_counts": {"pass": len(records), "warn": 0, "fail": 0},
            "remaining_blocker_roles": [],
            "production_loader_changed": False,
        },
    }
    reject_non_finite(payload)
    return payload


def build_step19e_ranking_audit(
    sources: Mapping[str, Any],
    *,
    physical_audit: Mapping[str, Any],
    input_hashes: Mapping[str, str],
    physical_audit_sha256: str,
) -> dict[str, Any]:
    """Build current selected ranking records and reviewed three-layer causes."""
    physical = {item["role"]: item for item in physical_audit["roles"]}
    historical = {item["role"]: item for item in sources["step18_ranking"]["records"]}
    current = build_post_step19_layers(sources)
    records: list[dict[str, Any]] = []
    for role in REQUIRED_ROLES:
        old = historical[role]
        layers = {
            "historical_v1_baseline": _project_layer(old["comparison_layers"].get("historical_v1_baseline") or {}),
            "pre_remediation_v2_free_selection": _project_layer(
                old["comparison_layers"].get("pre_step18f_v2_free_selection_evidence") or {}
            ),
            "post_step19_remediation": current[role],
        }
        changed_fields = _changed_fields(layers["historical_v1_baseline"], layers["post_step19_remediation"])
        cause_specs, classification, remaining_action = _role_cause_specs(role)
        causes = _build_causes(role, cause_specs, layers, changed_fields)
        covered = {field for cause in causes for field in cause["affected_fields"]}
        uncovered = sorted(set(changed_fields) - covered)
        if uncovered:
            raise ValueError(f"{role}: changed fields have no reviewed cause: {uncovered}.")
        selected = current[role]
        record = {
            "role": role,
            "physical_status": physical[role]["physical_status"],
            "selection_status": "selected",
            "selected_candidate": selected,
            "selected_in_final_feasible": True,
            "selected_in_final_ranked_evidence": True,
            "unavailable_candidate_ranked": False,
            "comparison_layers": layers,
            "changed_fields": changed_fields,
            "uncovered_changed_fields": uncovered,
            "difference_causes": causes,
            "review_status": "reviewed_confirmed",
            "classification": classification,
            "remaining_action": remaining_action,
        }
        _validate_ranking_record(record)
        records.append(record)
    payload = {
        "contract_version": STEP19E_RANKING_CONTRACT,
        "scope": "post_step19_remediation_seven_role_candidate_ranking",
        "backend": "packaged_normalized_v2_explicit_opt_in",
        "required_roles": list(REQUIRED_ROLES),
        "input_hashes": dict(sorted(input_hashes.items())),
        "physical_audit_sha256": physical_audit_sha256,
        "records": records,
        "summary": {
            "role_count": len(records),
            "selected_role_count": len(records),
            "blocked_role_count": 0,
            "all_physical_status_pass": True,
            "selected_membership_valid": True,
            "unavailable_candidate_ranked": False,
            "all_changed_fields_reviewed": True,
            "unresolved_regression_count": 0,
        },
    }
    reject_non_finite(payload)
    return payload


def build_step19e_rollout_gate(
    *,
    physical_audit: Mapping[str, Any],
    ranking_audit: Mapping[str, Any],
    classification_sha256: str,
    input_hashes: Mapping[str, str],
    corrected_v1_sha256: str,
    expected_corrected_v1_sha256: str,
    full_regression_status: str,
) -> dict[str, Any]:
    """Close Step 19E while keeping source, loader, and Step 19F promotion gates."""
    records = ranking_audit["records"]
    if {item["role"] for item in physical_audit["roles"]} != set(REQUIRED_ROLES):
        raise ValueError("Step 19E gate requires exact seven-role physical evidence.")
    if {item["role"] for item in records} != set(REQUIRED_ROLES):
        raise ValueError("Step 19E gate requires exact seven-role ranking evidence.")
    for record in records:
        _validate_ranking_record(record)
    unresolved = sorted(item["role"] for item in records if item["classification"] == "unresolved_regression")
    checks = {
        "seven_physical_roles_pass": physical_audit["summary"]["all_roles_pass"] is True,
        "seven_roles_selected": ranking_audit["summary"]["selected_role_count"] == 7,
        "selected_membership_valid": ranking_audit["summary"]["selected_membership_valid"] is True,
        "unavailable_candidate_not_ranked": ranking_audit["summary"]["unavailable_candidate_ranked"] is False,
        "all_changed_fields_reviewed": ranking_audit["summary"]["all_changed_fields_reviewed"] is True,
        "no_unresolved_regression": not unresolved,
        "corrected_v1_cache_unchanged": corrected_v1_sha256 == expected_corrected_v1_sha256,
    }
    if not all(checks.values()):
        failed = sorted(name for name, value in checks.items() if not value)
        raise ValueError(f"Step 19E rollout checks failed: {failed}.")
    promotion_blockers = [
        "MAS current full-source refresh and pin policy remains a separate Step 12/promotion decision",
        "normalized-v2 is not connected to the production loader",
    ]
    if full_regression_status != "passed":
        promotion_blockers.append(f"Step 19F full pytest regression status is {full_regression_status}")
    payload = {
        "contract_version": STEP19E_GATE_CONTRACT,
        "scope": "post_step19_remediation_reviewed_rollout_gate",
        "input_hashes": dict(sorted(input_hashes.items())),
        "classification_sha256": classification_sha256,
        "checks": checks,
        "reviewed_role_count": len(records),
        "reviewed_records": records,
        "classification_counts": {
            name: sum(item["classification"] == name for item in records)
            for name in (
                "defect_correction", "model_expansion", "identity_correction",
                "expected_ranking_change", "unresolved_regression",
            )
        },
        "unresolved_roles": unresolved,
        "step19e_completion_allowed": True,
        "next_permitted_step": "Step 19F",
        "promotion_allowed": False,
        "promotion_target": "normalized-v2-production-loader",
        "promotion_blockers": promotion_blockers,
        "full_regression_status": full_regression_status,
        "mas_full_source_refresh_policy_resolved": False,
        "production_loader_is_v2": False,
        "production_loader_changed": False,
        "production_cache_changed": False,
        "corrected_v1_sha256": corrected_v1_sha256,
        "expected_corrected_v1_sha256": expected_corrected_v1_sha256,
        "corrected_v1_cache_unchanged": True,
        "status": "pass_step19e_promotion_blocked",
    }
    reject_non_finite(payload)
    return payload


def render_step19e_classification_markdown(
    ranking_audit: Mapping[str, Any],
    *,
    physical_audit_sha256: str,
    ranking_audit_sha256: str,
    source_hashes: Mapping[str, str],
) -> str:
    records = ranking_audit["records"]
    lines = [
        "# OpenMagnetics Step 19 Post-Remediation A/B Classification",
        "",
        "> Post-remediation checkpoint: this file closed role classification before the",
        "> Step 19F regression aggregate completed. Step 19F later closed the regression",
        "> condition. MAS full-source/pin and production-loader policy remain the only",
        "> promotion blockers; see the [Reports Ledger Index](README.md).",
        "",
        "Recorded: 2026-07-28",
        "",
        "## Summary",
        "",
        "- All seven magnetic roles have `physical_status=pass` and `selection_status=selected`.",
        "- Every changed field is covered by a `reviewed_confirmed` cause.",
        "- No role remains `unresolved_regression`.",
        "- At this checkpoint normalized-v2 production promotion remained blocked by",
        "  source/pin policy, production-loader policy and Step 19F full regression.",
        "  Step 19F subsequently passed, leaving the first two blockers current.",
        "",
        "| Role | Physical | Selection | Classification | Remaining action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| `{record['role']}` | `{record['physical_status']}` | `{record['selection_status']}` | "
            f"`{record['classification']}` | {record['remaining_action']} |"
        )
    for record in records:
        lines.extend(["", f"## {record['role']}", ""])
        lines.append(f"- Current selection: `{record['selected_candidate']['selected_design_id']}`.")
        lines.append(f"- Review status: `{record['review_status']}`.")
        lines.append(f"- Classification: `{record['classification']}`.")
        lines.append(f"- Changed fields: `{', '.join(record['changed_fields']) or 'none'}`.")
        lines.append("- Three comparison layers: `historical_v1_baseline`, `pre_remediation_v2_free_selection`, `post_step19_remediation`.")
        lines.extend(["", "| Cause | Review | Affected fields | Evidence |", "| --- | --- | --- | --- |"])
        for cause in record["difference_causes"]:
            lines.append(
                f"| `{cause['cause_code']}` | `{cause['review_status']}` | "
                f"`{', '.join(cause['affected_fields'])}` | "
                f"{'; '.join(f'`{path}`' for path in cause['evidence_paths'])} |"
            )
    lines.extend([
        "", "## Evidence Hashes", "",
        f"- Physical audit: `{physical_audit_sha256}`",
        f"- Candidate ranking audit: `{ranking_audit_sha256}`",
    ])
    for path, digest in sorted(source_hashes.items()):
        lines.append(f"- `{path}`: `{digest}`")
    lines.append("")
    return "\n".join(lines)


def build_post_step19_layers(sources: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Project authority artifacts into one strict current layer per role."""
    layers: dict[str, dict[str, Any]] = {}
    frontier = {item["role"]: item for item in sources["step19c"]["records"]}
    for role in ("buck_main_inductor", "boost_main_inductor"):
        value = frontier[role]["selected_candidate"]
        layers[role] = _layer(
            selected_design_id=value["candidate_id"], core_id=value["core_id"],
            material_id=value["material_id"], wire_id=value["wire_id"], turns=value["turns"],
            parallel_count=value["parallel_bundles"], stack_count=1, gap_m=value["gap_m"],
            flux_absolute_peak_t=value["b_absolute_peak_t"], core_loss_w=value["core_loss_w"],
            copper_loss_w=value["copper_loss_w"], total_loss_w=value["total_loss_w"],
            total_volume_m3=value["total_volume_m3"], fill_factor=value["fill_factor"],
            current_density_a_per_mm2=value["current_density_a_per_mm2"],
            saturation_margin=value["margins"]["saturation"], thermal_status="not_required_at_step19c_frontier",
            model_validity="valid_comparable_router_loss",
        )
    flyback = sources["flyback_winding"]
    flyback_flux = sources["flyback_thermal"]["flux_semantics"]["corrected_build_result"]["excitation"]
    flyback_candidate = flyback["candidate"]
    layers["flyback_coupled_inductor_transformer"] = _layer(
        selected_design_id=flyback_candidate["candidate_id"], core_id=flyback_candidate["core_id"],
        material_id=flyback_candidate["material_id"],
        wire_id=_winding_wire_identity(flyback), turns=flyback["windings"]["primary"]["turns"],
        parallel_count=flyback["windings"]["primary"]["parallel_winding_count"], stack_count=1,
        gap_m=sources["flyback_thermal"]["candidate"]["gap_m"],
        effective_magnetic_volume_m3=sources["flyback_thermal"]["candidate"]["effective_volume_m3"],
        flux_peak_to_peak_t=flyback_flux["flux_peak_to_peak_t"],
        flux_dc_offset_t=flyback_flux["flux_dc_offset_t"],
        flux_absolute_peak_t=flyback_flux["flux_absolute_peak_t"],
        core_loss_w=flyback_candidate["core_loss_w"], copper_loss_w=flyback_candidate["copper_loss_w"],
        total_loss_w=flyback_candidate["total_loss_w"],
        total_volume_m3=sources["flyback_thermal"]["candidate"]["total_volume_m3"],
        fill_factor=flyback_candidate["fill_factor"], thermal_status="pass",
        model_validity="valid_igse", extra={"hotspot_c": flyback_candidate["hotspot_c"]},
    )
    llc = sources["llc_winding"]
    llc_candidate = llc["candidate"]
    corrected_ranking = {item["role"]: item for item in sources["step19r_ranking"]["records"]}
    llc_ranked = corrected_ranking["llc_transformer"]["selected_candidate"]
    layers["llc_transformer"] = _layer(
        selected_design_id=llc_candidate["candidate_id"], core_id=llc_candidate["core_id"],
        material_id=llc_candidate["material_id"], wire_id=_winding_wire_identity(llc),
        turns=llc["windings"]["primary"]["turns"], parallel_count=llc["windings"]["primary"]["parallel_winding_count"],
        stack_count=1, gap_m=llc_ranked["gap_m"],
        flux_peak_to_peak_t=llc_ranked["flux_peak_to_peak_t"],
        flux_absolute_peak_t=llc_ranked["flux_absolute_peak_t"],
        core_loss_w=llc_candidate["core_loss_w"], copper_loss_w=llc_candidate["copper_loss_w"],
        total_loss_w=llc_candidate["total_loss_w"], total_volume_m3=llc_ranked["total_volume_m3"],
        fill_factor=llc_candidate["fill_factor"], thermal_status="pass", model_validity="valid_igse",
        extra={"hotspot_c": llc_candidate["hotspot_c"]},
    )
    lr = corrected_ranking["llc_external_resonant_inductor"]["selected_candidate"]
    layers["llc_external_resonant_inductor"] = _layer_from_ranked(lr, thermal_status="pass")
    stack_audit = sources["step19d"]["first_run"]
    selected_stacks = stack_audit["selected_stack_records"]
    if not selected_stacks:
        raise ValueError("Step 19E requires at least one Step 19D selected stacked representative.")
    chosen_stack = selected_stacks[len(selected_stacks) // 2]
    stack_physical = next(
        item for item in stack_audit["physical_records"] if item["candidate_id"] == chosen_stack["candidate_id"]
    )
    layers["generic_main_inductor_stacked_core_competitor"] = _layer(
        selected_design_id=stack_physical["candidate_id"], core_id=stack_physical["core_id"],
        material_id=stack_physical["material_id"], wire_id=stack_physical["wire_id"],
        turns=stack_physical["turns"], parallel_count=stack_physical["parallel_bundles"],
        stack_count=stack_physical["stack_count"], gap_m=stack_physical["gap_m"],
        effective_magnetic_volume_m3=stack_physical["assembled_ve_m3"],
        flux_peak_to_peak_t=stack_physical["bpp_t"], flux_dc_offset_t=stack_physical["bdc_t"],
        flux_absolute_peak_t=stack_physical["babsolute_t"], core_loss_w=stack_physical["core_loss_w"],
        copper_loss_w=stack_physical["copper_loss_w"], total_loss_w=stack_physical["total_loss_w"],
        total_volume_m3=stack_physical["total_volume_m3"], fill_factor=stack_physical["fill_factor"],
        thermal_status="not_required_at_step19d_frontier", model_validity="valid_comparable_router_loss",
        extra={"base_candidate_id": stack_physical["base_candidate_id"]},
    )
    sendust = corrected_ranking["single_phase_rectifier_dc_link_reactor"]["selected_candidate"]
    layers["single_phase_rectifier_dc_link_reactor"] = _layer_from_ranked(sendust, thermal_status="pass")
    if set(layers) != set(REQUIRED_ROLES):
        raise ValueError("Step 19E current layer projection is incomplete.")
    return {role: layers[role] for role in REQUIRED_ROLES}


def _authority_by_role(sources: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    frontier = {item["role"]: item for item in sources["step19c"]["records"]}
    step19r_physical = {item["role"]: item for item in sources["step19r_physical"]["roles"]}
    result: dict[str, dict[str, Any]] = {}
    for role in ("buck_main_inductor", "boost_main_inductor"):
        record = frontier[role]
        result[role] = {
            "paths": ["reports/openmagnetics_step19_buck_boost_frontier_audit_20260727.json"],
            "checks": [
                _check("frontier_status", record["status"] == "feasible_selection_verified", record["status"]),
                _check("all_margins", record["selected_candidate"]["all_margins_at_least_one"], record["selected_candidate"]["margins"]),
                _check("loss_model_comparable", record["selected_candidate"]["loss_model_comparable"], record["selected_candidate"]["core_loss_w"]),
                _check("final_membership", all(record["membership"].values()), record["membership"]),
            ],
        }
    result["flyback_coupled_inductor_transformer"] = {
        "paths": [
            "reports/openmagnetics_step19_flyback_thermal_remediation_20260727.json",
            "reports/openmagnetics_step19_flyback_winding_audit_20260727.json",
        ],
        "checks": [
            _check("thermal_remediation", sources["flyback_thermal"]["acceptance"]["status"] == "pass", sources["flyback_thermal"]["acceptance"]),
            _check("winding_evidence", sources["flyback_winding"]["acceptance"]["status"] == "pass", sources["flyback_winding"]["acceptance"]),
            _check("final_membership", all(sources["flyback_winding"]["step19a_r_membership"][name] is True for name in ("selected_in_final_feasible", "selected_in_final_ranked_evidence")), sources["flyback_winding"]["step19a_r_membership"]),
        ],
    }
    result["llc_transformer"] = {
        "paths": ["reports/openmagnetics_step19_llc_transformer_winding_audit_20260727.json"],
        "checks": [
            _check("winding_and_thermal", sources["llc_winding"]["acceptance"]["status"] == "pass", sources["llc_winding"]["acceptance"]),
            _check("final_membership", all(sources["llc_winding"]["step19a_r_membership"][name] is True for name in ("selected_in_final_feasible", "selected_in_final_ranked_evidence")), sources["llc_winding"]["step19a_r_membership"]),
        ],
    }
    for role in ("llc_external_resonant_inductor", "single_phase_rectifier_dc_link_reactor"):
        value = step19r_physical[role]
        result[role] = {
            "paths": [
                "reports/openmagnetics_step19r_role_reranking_audit_20260727.json",
                "reports/openmagnetics_step19r_physical_consistency_audit_20260727.json",
            ],
            "checks": [
                _check("corrected_ranking_physical", value["status"] == "pass", value),
                _check("selected_physical_evidence", value["selected_physical_evidence_valid"] is True, value["corrected_candidate_id"]),
            ],
        }
    stack = sources["step19d"]
    result["generic_main_inductor_stacked_core_competitor"] = {
        "paths": ["reports/openmagnetics_step19_stacked_candidate_audit_20260727.json"],
        "checks": [
            _check("step19d_status", stack["status"] == "pass", stack["status"]),
            _check("all_physical_checks", stack["checks"]["all_expanded_physical_checks_pass"] is True, stack["first_run"]["generation"]),
            _check("selected_membership", stack["checks"]["all_selected_stacks_have_valid_membership"] is True, stack["first_run"]["selected_stack_records"]),
            _check("deterministic", stack["checks"]["repeatability"] is True, stack["repeatability"]),
        ],
    }
    return result


def _role_cause_specs(role: str) -> tuple[list[tuple[str, str, tuple[str, ...]]], str, str]:
    identity = ("selected_design_id", "core_id", "material_id", "wire_id", "turns", "parallel_count", "stack_count")
    flux = ("flux_peak_to_peak_t", "flux_dc_offset_t", "flux_absolute_peak_t", "saturation_margin")
    geometry = ("gap_m", "effective_magnetic_volume_m3", "total_volume_m3", "fill_factor", "current_density_a_per_mm2")
    loss = ("core_loss_w", "copper_loss_w", "total_loss_w", "thermal_status", "model_validity")
    if role in {"buck_main_inductor", "boost_main_inductor"}:
        return [
            ("candidate_pool_expansion", "Step 19C expands only the bounded core pool after an empty engineering-allow frontier.", identity + geometry),
            ("excitation_semantics_change", "Bpp and Babsolute are separated; the unchanged allow profile screens absolute saturation flux.", flux),
            ("unit_semantics_correction", "Corrected AF/AN/Metglas source units and shared SI loss routing remove invalid low-loss ranking.", loss),
        ], "expected_ranking_change", "Maintain the Step 19C deterministic frontier as a regression baseline."
    if role == "generic_main_inductor_stacked_core_competitor":
        return [
            ("candidate_pool_expansion", "Step 19D creates STACK2/STACK3 only from valid Step 19C compressed parents.", identity),
            ("geometry_metric_correction", "Assembled Ae/Ve/Aw, envelope, winding and gap scale with explicit one-time semantics.", geometry),
            ("excitation_semantics_change", "Stacked Bpp/Bdc/Babsolute are rebuilt from actual L/current/N/assembled-Ae.", flux),
            ("unit_semantics_correction", "Shared routed loss uses assembled Ve exactly once and excludes unavailable models.", loss),
        ], "expected_ranking_change", "Maintain Step 19D parent trace, volume identity and deterministic hashes."
    if role == "flyback_coupled_inductor_transformer":
        return [
            ("unit_semantics_correction", "The AF/AN/Metglas coefficient correction changes free-selection material ranking.", identity + loss),
            ("excitation_semantics_change", "Flyback loss now consumes current-derived Bpp while saturation retains Babsolute and DC bias.", flux + geometry),
            ("wire_metric_correction", "Exact primary/secondary v2 winding records independently close copper loss.", ("wire_id", "copper_loss_w", "total_loss_w", "thermal_status")),
        ], "defect_correction", "Maintain the Step 19B winding and thermal evidence regression."
    if role == "llc_transformer":
        return [
            ("unit_semantics_correction", "Corrected source coefficients remove invalid AF free-selection advantage.", ("material_id",) + loss),
            ("expected_ranking_change", "The corrected deterministic search selects Finemet transformer hardware.", identity + geometry + flux),
            ("wire_metric_correction", "Exact primary/secondary v2 windings independently reproduce copper loss and fill.", ("wire_id", "copper_loss_w", "total_loss_w", "thermal_status")),
        ], "expected_ranking_change", "Maintain LLC winding, flux and thermal evidence under Step 19F regression."
    if role == "llc_external_resonant_inductor":
        return [
            ("unit_semantics_correction", "AN fixed-hardware loss is corrected from a mass/volumetric source-unit defect.", loss),
            ("expected_ranking_change", "Corrected free selection moves from AN to physically valid Finemet hardware.", identity + geometry + flux),
        ], "defect_correction", "Retain corrected AN fixed-hardware evidence and Finemet free-selection membership."
    return [
        ("field_parsing_correction", "Explicit Sendust DC bias, delta-B and absolute flux semantics replace ambiguous legacy fields.", identity + geometry + flux),
        ("loss_model_expansion", "The shared Micrometals evaluator supplies valid non-Steinmetz loss without changing hardware.", loss),
    ], "model_expansion", "Maintain the unchanged MS-649026-2 selection and shared-model regression."


def _build_causes(
    role: str,
    specs: list[tuple[str, str, tuple[str, ...]]],
    layers: Mapping[str, Mapping[str, Any]],
    changed_fields: list[str],
) -> list[dict[str, Any]]:
    causes: list[dict[str, Any]] = []
    changed = set(changed_fields)
    for index, (code, explanation, fields) in enumerate(specs, start=1):
        affected = tuple(field for field in fields if field in changed)
        if not affected:
            continue
        causes.append({
            "cause_id": f"{role}:{index:02d}:{code}",
            "cause_code": code,
            "affected_fields": list(dict.fromkeys(affected)),
            "evidence_paths": _cause_evidence_paths(role, code),
            "layer_values": {
                layer: {field: values.get(field) for field in affected}
                for layer, values in layers.items()
            },
            "engineering_explanation": explanation,
            "review_status": "reviewed_confirmed",
        })
    if changed and not causes:
        raise ValueError(f"{role}: no reviewed cause covers changed fields.")
    return causes


def _cause_evidence_paths(role: str, code: str) -> list[str]:
    common = [
        f"reports/openmagnetics_step18_candidate_ranking_audit_20260726.json#records[role={role}]",
        f"reports/openmagnetics_step19r_role_reranking_audit_20260727.json#records[role={role}]",
    ]
    if role in {"buck_main_inductor", "boost_main_inductor"}:
        common.append("reports/openmagnetics_step19_buck_boost_frontier_audit_20260727.json")
    elif role == "generic_main_inductor_stacked_core_competitor":
        common.append("reports/openmagnetics_step19_stacked_candidate_audit_20260727.json")
    elif role == "flyback_coupled_inductor_transformer":
        common.append("reports/openmagnetics_step19_flyback_thermal_remediation_20260727.json")
    elif role == "llc_transformer":
        common.append("reports/openmagnetics_step19_llc_transformer_winding_audit_20260727.json")
    else:
        common.append("reports/openmagnetics_step19r_role_reranking_audit_20260727.json")
    return common


def _layer(**values: Any) -> dict[str, Any]:
    extra = values.pop("extra", None) or {}
    payload = {field: values.get(field) for field in CURRENT_LAYER_FIELDS}
    payload.update(extra)
    return payload


def _layer_from_ranked(value: Mapping[str, Any], *, thermal_status: str) -> dict[str, Any]:
    return _layer(
        selected_design_id=value["candidate_id"], core_id=value["core_id"], material_id=value["material_id"],
        wire_id=value.get("wire_id"), turns=value.get("turns"), parallel_count=value.get("parallel_count"),
        stack_count=value.get("stack_count") or 1, gap_m=value.get("gap_m"),
        flux_peak_to_peak_t=value.get("flux_peak_to_peak_t"), flux_absolute_peak_t=value.get("flux_absolute_peak_t"),
        core_loss_w=value.get("core_loss_w"), copper_loss_w=value.get("copper_loss_w"),
        total_loss_w=value.get("total_loss_w"), total_volume_m3=value.get("total_volume_m3"),
        fill_factor=value.get("fill_factor"), current_density_a_per_mm2=value.get("current_density_a_per_mm2"),
        saturation_margin=value.get("saturation_margin"), thermal_status=thermal_status,
        model_validity=value.get("model_validity"),
    )


def _project_layer(value: Mapping[str, Any]) -> dict[str, Any]:
    return {field: value.get(field) for field in CURRENT_LAYER_FIELDS}


def _winding_wire_identity(audit: Mapping[str, Any]) -> str:
    primary = audit["windings"]["primary"]["wire_id"]
    secondary = audit["windings"]["secondary"]["wire_id"]
    return primary if primary == secondary else f"primary={primary};secondary={secondary}"


def _check(check_id: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"check_id": check_id, "status": "pass" if passed else "fail", "evidence": evidence}


def _changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in CURRENT_LAYER_FIELDS if not _equal(before.get(field), after.get(field))]


def _equal(first: Any, second: Any) -> bool:
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isclose(float(first), float(second), rel_tol=1e-12, abs_tol=1e-15)
    return first == second


def _validate_selected_layer(role: str, value: Mapping[str, Any]) -> None:
    if not value.get("selected_design_id") or value.get("core_loss_w") is None or value.get("total_loss_w") is None:
        raise ValueError(f"{role}: selected current layer lacks identity or loss.")
    for field in ("core_loss_w", "total_loss_w"):
        number = float(value[field])
        if not math.isfinite(number) or number < 0.0:
            raise ValueError(f"{role}: {field} must be finite and nonnegative.")
    validity = str(value.get("model_validity") or "")
    if not validity.startswith("valid") and validity != "finite_role_search_loss":
        raise ValueError(f"{role}: current loss model is not valid: {validity}.")


def _validate_ranking_record(record: Mapping[str, Any]) -> None:
    if record["physical_status"] != "pass" or record["selection_status"] != "selected":
        raise ValueError(f"{record['role']}: current role is not physically selected.")
    if record["unavailable_candidate_ranked"] or record["uncovered_changed_fields"]:
        raise ValueError(f"{record['role']}: invalid ranking evidence.")
    if tuple(record["comparison_layers"]) != COMPARISON_LAYERS:
        raise ValueError(f"{record['role']}: exactly three ordered comparison layers are required.")
    if record["classification"] == "unresolved_regression":
        raise ValueError(f"{record['role']}: unresolved regression remains after Step 19 remediation.")
    if any(cause["review_status"] != "reviewed_confirmed" for cause in record["difference_causes"]):
        raise ValueError(f"{record['role']}: unreviewed difference cause remains.")


def reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError(f"Non-finite value at {path}.")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            reject_non_finite(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            reject_non_finite(item, f"{path}[{index}]")
        return
    raise TypeError(f"Unsupported evidence value at {path}: {type(value).__name__}.")


def canonical_json(payload: Mapping[str, Any]) -> str:
    reject_non_finite(payload)
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


__all__ = [
    "COMPARISON_LAYERS",
    "STEP19E_GATE_CONTRACT",
    "STEP19E_PHYSICAL_CONTRACT",
    "STEP19E_RANKING_CONTRACT",
    "build_post_step19_layers",
    "build_step19e_physical_audit",
    "build_step19e_ranking_audit",
    "build_step19e_rollout_gate",
    "canonical_json",
    "reject_non_finite",
    "render_step19e_classification_markdown",
]

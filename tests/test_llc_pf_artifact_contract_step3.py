from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report
from pe_claw_gui.app.result_views.inductor_pf_view import resolve_llc_pf_plot_paths
from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.pipeline.llc_pf_artifacts import (
    build_llc_pf_artifact_contract,
    llc_pf_artifact_payload,
    validate_llc_pf_artifact_contracts,
)
from pe_claw_gui.reports.structured_output import build_structured_report


TOPOLOGY = "llc_resonant_converter_diode_rectifier"


def _artifact_set(root: Path, role: str) -> list[str]:
    names = {
        "transformer": (
            "llc_transformer_pareto_front.png",
            "llc_transformer_pareto_front.csv",
            "llc_transformer_feasible_candidates.csv",
            "llc_transformer_chosen_candidates.csv",
        ),
        "external_lr": (
            "llc_external_resonant_inductor_pareto_front.png",
            "llc_external_resonant_inductor_pareto_front.csv",
            "llc_external_resonant_inductor_feasible_candidates.csv",
            "llc_external_resonant_inductor_chosen_candidates.csv",
        ),
    }[role]
    directory = root / role
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        path = directory / name
        path.write_bytes(b"artifact")
        paths.append(str(path))
    return paths


def _contracts(root: Path, *, run_id: str = "run-1"):
    return {
        role: build_llc_pf_artifact_contract(
            role=role,
            artifact_paths=_artifact_set(root, role),
            run_id=run_id,
            topology_id=TOPOLOGY,
            run_root=root,
            recommended_design_id=f"{role}-recommended",
        )
        for role in ("transformer", "external_lr")
    }


def _workspace_tmp(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.mkdir()
    return path


def test_complete_role_contracts_are_available_and_hashed(tmp_path: Path) -> None:
    root = _workspace_tmp(tmp_path, "llc-step3-contract")
    contracts = _contracts(root)
    result = validate_llc_pf_artifact_contracts(contracts, run_id="run-1", topology_id=TOPOLOGY)
    assert result["valid"] is True
    payload = llc_pf_artifact_payload(contracts)
    for role in contracts:
        assert payload[role]["status"] == "available"
        assert all(item["exists"] and item["non_empty"] and item["sha256"] for item in payload[role]["files"].values())


def test_missing_empty_and_wrong_role_artifacts_are_blocked(tmp_path: Path) -> None:
    root = _workspace_tmp(tmp_path, "llc-step3-missing")
    paths = _artifact_set(root, "transformer")
    (root / "transformer" / "llc_transformer_pareto_front.csv").write_bytes(b"")
    contract = build_llc_pf_artifact_contract(
        role="external_lr",
        artifact_paths=paths,
        run_id="run-1",
        topology_id=TOPOLOGY,
        run_root=root,
        recommended_design_id="L-recommended",
    )
    assert contract.status == "blocked"
    assert any("missing required artifact" in item for item in contract.diagnostics)

    transformer = build_llc_pf_artifact_contract(
        role="transformer",
        artifact_paths=paths,
        run_id="run-1",
        topology_id=TOPOLOGY,
        run_root=root,
        recommended_design_id="T-recommended",
    )
    assert any("artifact is empty" in item for item in transformer.diagnostics)


def test_contract_rejects_outside_run_and_identity_mismatch(tmp_path: Path) -> None:
    root = _workspace_tmp(tmp_path, "llc-step3-identity")
    outside_root = tmp_path / "llc-outside"
    outside_root.mkdir()
    outside = outside_root / "llc_transformer_pareto_front.png"
    paths = _artifact_set(root, "transformer")
    outside.write_bytes(b"artifact")
    paths[0] = str(outside)
    contract = build_llc_pf_artifact_contract(
        role="transformer",
        artifact_paths=paths,
        run_id="run-old",
        topology_id="other-topology",
        run_root=root,
        recommended_design_id="T-recommended",
    )
    assert any("outside current run root" in item for item in contract.diagnostics)
    result = validate_llc_pf_artifact_contracts(
        {"transformer": contract}, run_id="run-current", topology_id=TOPOLOGY
    )
    assert result["valid"] is False
    assert any("run mismatch" in item or "topology mismatch" in item for item in result["diagnostics"])


def test_structured_output_exposes_llc_pf_artifacts_only_for_llc(tmp_path: Path) -> None:
    root = _workspace_tmp(tmp_path, "llc-step3-structured")
    report = build_baseline_report()
    context = LlcRunContext.create(TOPOLOGY, {"fixture": "step3"}, output_root=root)
    contracts = _contracts(root, run_id=context.run_id)
    magnetic = replace(report.magnetic, llc_pf_artifact_contracts=contracts)
    payload = build_structured_report(replace(report, magnetic=magnetic, llc_run_context=context))
    pf_artifacts = payload["magnetic"]["llc"]["pf_artifacts"]
    assert set(pf_artifacts) == {"transformer", "external_lr"}
    assert pf_artifacts["transformer"]["run_id"] == context.run_id
    assert pf_artifacts["external_lr"]["topology_id"] == TOPOLOGY

    non_llc = replace(
        report,
        spec=replace(report.spec, topology_id="buck_diode_rectified_unidirectional"),
        magnetic=replace(report.magnetic, result_type="fixed_inductor"),
    )
    assert "llc" not in build_structured_report(non_llc)["magnetic"]


def test_pf_view_prefers_role_contract_paths(tmp_path: Path) -> None:
    root = _workspace_tmp(tmp_path, "llc-step3-view")
    report = build_baseline_report()
    context = LlcRunContext.create(TOPOLOGY, {"fixture": "step3"}, output_root=root)
    contracts = _contracts(root, run_id=context.run_id)
    report = replace(
        report,
        magnetic=replace(report.magnetic, llc_pf_artifact_contracts=contracts),
        llc_run_context=context,
    )
    paths = resolve_llc_pf_plot_paths(report)
    assert paths["transformer"] == Path(contracts["transformer"].pareto_png_path)
    assert paths["external_lr"] == Path(contracts["external_lr"].pareto_png_path)

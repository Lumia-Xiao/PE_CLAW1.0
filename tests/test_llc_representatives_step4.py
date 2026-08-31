from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from scripts.build_llc_magnetic_result_display_step1_baseline import build_baseline_report
from pe_claw_gui.pipeline.llc_representatives import build_llc_representative_payload
from pe_claw_gui.models.magnetic_result import LlcMagneticResultSummary, LlcMagneticStageSummary
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.app.result_views.llc_result_text import build_llc_magnetic_summary_text


ROLES = ("recommended", "min-volume", "min-loss")


def _candidate(component: str, role: str):
    if component == "transformer":
        return SimpleNamespace(
            candidate_id=f"T-{role}",
            core_id="E 80/38/32",
            material_id="SMP97",
            np=18,
            ns=18,
            gap_m=0.002,
            lm_actual_h=0.0018,
            fill_factor=0.2,
            estimated_volume_m3={"recommended": 10e-6, "min-volume": 8e-6, "min-loss": 12e-6}[role],
            total_loss_w={"recommended": 2.0, "min-volume": 3.0, "min-loss": 1.0}[role],
            core_loss_w=1.0,
            copper_loss_w=1.0,
            hotspot_c={"recommended": 40.0, "min-volume": 45.0, "min-loss": 38.0}[role],
        )
    return SimpleNamespace(
        design_id=f"L-{role}",
        core_id="E 55/28/25",
        material_name="SMP97",
        turns=11,
        gap_m=0.001,
        actual_l_h=0.001,
        fill_factor=0.2,
        estimated_volume_m3={"recommended": 10e-6, "min-volume": 8e-6, "min-loss": 12e-6}[role],
        total_loss_w={"recommended": 2.0, "min-volume": 3.0, "min-loss": 1.0}[role],
        core_loss_w=1.0,
        copper_loss_w=1.0,
        hotspot_c={"recommended": 40.0, "min-volume": 45.0, "min-loss": 38.0}[role],
        wire_name="SMP97",
        wire_parallel_count=4,
    )


def _report_with_representatives():
    report = build_baseline_report()
    transformer = SimpleNamespace(
        representative_by_role={
            role: SimpleNamespace(role=role, candidate=_candidate("transformer", role), reason=f"T {role}")
            for role in ROLES
        }
    )
    external = SimpleNamespace(
        chosen_candidates=[
            SimpleNamespace(role=role, candidate=_candidate("external_lr", role), reason=f"L {role}")
            for role in ROLES
        ]
    )
    magnetic = replace(
        report.magnetic,
        transformer_pareto_result=transformer,
        transformer_chosen_candidates=list(transformer.representative_by_role.values()),
        llc_external_resonant_inductor_search_result=external,
    )
    return replace(report, magnetic=magnetic)


def test_both_llc_roles_expose_three_representatives_and_metrics() -> None:
    payload = build_llc_representative_payload(_report_with_representatives().magnetic)
    assert set(payload) == {"transformer", "external_lr"}
    for component in payload:
        assert set(payload[component]) == set(ROLES)
        assert [payload[component][role]["design_id"] for role in ROLES] == [
            f"{'T' if component == 'transformer' else 'L'}-{role}" for role in ROLES
        ]
        assert all(payload[component][role]["status"] == "available" for role in ROLES)
        assert all(payload[component][role]["metrics"]["volume_m3"] is not None for role in ROLES)


def test_missing_representative_is_unavailable_without_recommended_fallback() -> None:
    report = _report_with_representatives()
    transformer = report.magnetic.transformer_pareto_result
    transformer.representative_by_role.pop("min-loss")
    magnetic = replace(report.magnetic, transformer_chosen_candidates=[
        item for item in report.magnetic.transformer_chosen_candidates if item.role != "min-loss"
    ])
    report = replace(report, magnetic=magnetic)
    payload = build_llc_representative_payload(report.magnetic)
    assert payload["transformer"]["recommended"]["design_id"] == "T-recommended"
    assert payload["transformer"]["min-loss"]["status"] == "unavailable"
    assert payload["transformer"]["min-loss"]["design_id"] is None
    assert "min-loss" in payload["transformer"]["min-loss"]["diagnostics"][0]


def test_structured_and_text_outputs_share_roles_and_ids() -> None:
    report = _report_with_representatives()
    report = replace(
        report,
        magnetic=replace(
            report.magnetic,
            llc_result_summary=LlcMagneticResultSummary(
                transformer=LlcMagneticStageSummary(status="available"),
                external_lr=LlcMagneticStageSummary(status="available"),
            ),
        ),
    )
    structured = build_structured_report(report)["magnetic"]["llc"]["representatives"]
    text = build_llc_magnetic_summary_text(report)
    for component, prefix in (("transformer", "T-"), ("external_lr", "L-")):
        for role in ROLES:
            design_id = structured[component][role]["design_id"]
            assert design_id is not None
            assert design_id.startswith(prefix)
            assert f"{role}: {design_id}" in text

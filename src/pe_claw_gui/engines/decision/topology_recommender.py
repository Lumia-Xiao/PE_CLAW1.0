"""Deterministic topology recommender for AI-assisted design."""

from __future__ import annotations

from ...models.ai_design_report import TopologyRecommendation
from ...models.design_intent import DesignIntent
from ...topologies.base.registry import TopologyRegistry, build_default_registry


def recommend_topologies(
    intent: DesignIntent | dict,
    registry: TopologyRegistry | None = None,
    limit: int | None = None,
) -> list[TopologyRecommendation]:
    """Return deterministic ranked topology recommendations."""

    design_intent = intent if isinstance(intent, DesignIntent) else DesignIntent.from_dict(intent)
    registry = registry or build_default_registry()
    recommendations = [
        _score_definition(design_intent, definition)
        for definition in registry.list_definitions()
        if definition.implemented
    ]
    recommendations.sort(key=lambda item: (item.rejected, -item.score, -item.confidence, item.topology_id))
    return recommendations[:limit] if limit is not None else recommendations


def _score_definition(intent: DesignIntent, definition) -> TopologyRecommendation:
    topology_id = definition.topology_id
    name = definition.display_name
    score = 0.0
    confidence = 0.35
    reasons: list[str] = []
    risks: list[str] = []
    missing: list[str] = []
    matched_priorities: list[str] = []

    priorities = set(intent.normalized_priorities())
    family = (intent.converter_family or "").strip().lower()
    if family in {"dc_dc", "dc-dc", "dcdc"} or definition.category_id == "dc_dc":
        score += 5.0
        reasons.append("Registered DC-DC topology matches converter family.")

    vin_nom = intent.vin_nom_v
    vout = intent.vout_v
    if vin_nom is None:
        missing.append("vin_nom_v")
    if vout is None:
        missing.append("vout_v")

    crosses_output = False
    if intent.vin_min_v is not None and intent.vin_max_v is not None and vout is not None:
        crosses_output = intent.vin_min_v < vout < intent.vin_max_v
        confidence += 0.15

    if vin_nom is not None and vout is not None:
        confidence += 0.2
        if vin_nom > vout:
            score += _buck_score(topology_id, reasons)
            score -= _boost_penalty(topology_id, risks)
        elif vin_nom < vout:
            score += _boost_score(topology_id, reasons)
            score -= _buck_penalty(topology_id, risks)
        else:
            score += _buck_boost_score(topology_id, reasons)
            risks.append("Nominal gain is near unity; control margin should be checked.")

    if crosses_output:
        score += _buck_boost_score(topology_id, reasons)
        if "buck_boost" not in topology_id and "four_switch" not in topology_id:
            risks.append("Input range crosses output voltage; fixed buck or boost topology may not cover all conditions.")
            score -= 5.0

    if "three_level" in topology_id:
        if max(intent.vin_nom_v or 0.0, intent.vin_max_v or 0.0) >= 300.0:
            score += 12.0
            reasons.append("Three-level topology reduces switch voltage stress for higher-voltage designs.")
        risks.append("Three-level TZCM adds control and operating-point feasibility complexity.")

    if intent.isolation_required is True:
        risks.append("Intent requires isolation; registered DC-DC candidates are treated as non-isolated in this first rule set.")
        score -= 15.0
    elif intent.isolation_required is None:
        missing.append("isolation_required")

    if intent.bidirectional is True:
        if "synchronous" in topology_id or "four_switch" in topology_id:
            score += 3.0
            reasons.append("Synchronous/four-switch implementation is a better starting point for bidirectional extension.")
        else:
            score -= 10.0
            risks.append("Topology appears unidirectional; bidirectional requirement is uncertain.")
    elif intent.bidirectional is None:
        missing.append("bidirectional")

    if intent.fsw_hz is not None and intent.fsw_hz >= 200_000.0:
        if "synchronous" in topology_id or "four_switch" in topology_id:
            score += 2.0
        else:
            risks.append("High switching frequency may increase hard-switching loss.")
            score -= 3.0
    elif intent.fsw_hz is None:
        missing.append("fsw_hz")

    score += _priority_score(topology_id, priorities, reasons, risks, matched_priorities)
    score += _power_score(intent.pout_w, topology_id, reasons, risks)

    if intent.topology_hint and intent.topology_hint.lower().replace(" ", "_") in topology_id:
        score += 20.0
        confidence += 0.15
        reasons.append("Topology hint matches this registered topology.")

    rejected = False
    rejection_reason = None
    if intent.isolation_required is True and not _looks_isolated(topology_id):
        rejected = False
        rejection_reason = None

    confidence = max(0.05, min(1.0, confidence - 0.04 * len(set(missing))))
    if not reasons:
        reasons.append("Candidate retained for comparison because registered topology metadata is available.")

    return TopologyRecommendation(
        topology_id=topology_id,
        display_name=name,
        score=round(score, 3),
        confidence=round(confidence, 3),
        reasons=_dedupe(reasons),
        risks=_dedupe(risks),
        missing_information=_dedupe(missing),
        matched_priorities=_dedupe(matched_priorities),
        rejected=rejected,
        rejection_reason=rejection_reason,
    )


def _buck_score(topology_id: str, reasons: list[str]) -> float:
    if topology_id.startswith("buck_") or "three_level" in topology_id:
        reasons.append("Nominal input voltage is above output voltage, favoring buck-like conversion.")
        return 18.0
    if "buck_boost" in topology_id or "four_switch" in topology_id:
        reasons.append("Buck-boost topology can cover step-down operation with extra flexibility.")
        return 8.0
    return 0.0


def _boost_score(topology_id: str, reasons: list[str]) -> float:
    if topology_id.startswith("boost_"):
        reasons.append("Nominal input voltage is below output voltage, favoring boost conversion.")
        return 18.0
    if "buck_boost" in topology_id or "four_switch" in topology_id:
        reasons.append("Buck-boost topology can cover step-up operation with extra flexibility.")
        return 8.0
    return 0.0


def _buck_boost_score(topology_id: str, reasons: list[str]) -> float:
    if "buck_boost" in topology_id or "four_switch" in topology_id:
        reasons.append("Input/output relation favors buck-boost range coverage.")
        return 18.0
    return 0.0


def _boost_penalty(topology_id: str, risks: list[str]) -> float:
    if topology_id.startswith("boost_"):
        risks.append("Boost topology is not a natural fit for nominal step-down conversion.")
        return 10.0
    return 0.0


def _buck_penalty(topology_id: str, risks: list[str]) -> float:
    if topology_id.startswith("buck_") or "three_level" in topology_id:
        risks.append("Buck-like topology is not a natural fit for nominal step-up conversion.")
        return 10.0
    return 0.0


def _priority_score(
    topology_id: str,
    priorities: set[str],
    reasons: list[str],
    risks: list[str],
    matched: list[str],
) -> float:
    score = 0.0
    if "efficiency" in priorities:
        matched.append("efficiency")
        if "synchronous" in topology_id or "three_level" in topology_id:
            score += 5.0
            reasons.append("Priority efficiency favors synchronous or voltage-stress-reduced candidates.")
        else:
            risks.append("Diode rectification may reduce efficiency at high current.")
    if "power_density" in priorities:
        matched.append("power_density")
        score += 2.0
        reasons.append("Power density priority retained for downstream magnetic, thermal, and geometry comparison.")
    if "low_ripple" in priorities:
        matched.append("low_ripple")
        if "three_level" in topology_id:
            score += 3.0
            reasons.append("Three-level switching can reduce voltage stress and help ripple management.")
    if "low_cost" in priorities:
        matched.append("low_cost")
        if "diode" in topology_id and "four_switch" not in topology_id:
            score += 4.0
            reasons.append("Diode-rectified topology is a simpler low-cost starting point.")
        else:
            risks.append("More switches/control may increase implementation cost.")
    if "thermal_safety" in priorities:
        matched.append("thermal_safety")
        score += 1.0
        reasons.append("Thermal safety is deferred to semiconductor, magnetic, capacitor, and thermal stages.")
    return score


def _power_score(pout_w: float | None, topology_id: str, reasons: list[str], risks: list[str]) -> float:
    if pout_w is None:
        return 0.0
    if pout_w >= 1000.0 and ("three_level" in topology_id or "four_switch" in topology_id or "synchronous" in topology_id):
        reasons.append("Higher power favors reduced conduction loss or voltage-stress-managed candidates.")
        return 3.0
    if pout_w >= 1000.0 and "diode" in topology_id:
        risks.append("High power may make diode conduction loss significant.")
        return -2.0
    return 0.0


def _looks_isolated(topology_id: str) -> bool:
    return any(token in topology_id for token in ("llc", "cllc", "dab", "psfb", "flyback", "forward"))


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped

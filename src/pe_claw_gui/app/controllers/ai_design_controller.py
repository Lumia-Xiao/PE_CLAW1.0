"""Controller for AI-assisted design execution."""

from __future__ import annotations

from collections.abc import Callable

from ...models.ai_design_report import AIDesignReport
from ...models.design_intent import DesignIntent
from ...pipeline.run_ai_design_pipeline import run_ai_design_pipeline
from ..shell.state_store import AppStateStore


class AIDesignController:
    """Build a system-level design intent and run the deterministic AI pipeline."""

    def __init__(
        self,
        state_store: AppStateStore,
        pipeline_runner: Callable[[DesignIntent], AIDesignReport] = run_ai_design_pipeline,
    ) -> None:
        self._state_store = state_store
        self._pipeline_runner = pipeline_runner

    def build_design_intent(self, form_values: dict[str, object]) -> DesignIntent:
        """Convert GUI values into a structured design intent."""

        normalized = {
            "converter_family": _optional_str(form_values.get("converter_family")),
            "topology_hint": _optional_str(form_values.get("topology_hint")),
            "vin_min_v": form_values.get("vin_min_v"),
            "vin_nom_v": form_values.get("vin_nom_v"),
            "vin_max_v": form_values.get("vin_max_v"),
            "vout_v": form_values.get("vout_v"),
            "iout_a": form_values.get("iout_a"),
            "pout_w": form_values.get("pout_w"),
            "fsw_hz": _scale_float(form_values.get("fsw_khz"), 1_000.0),
            "ripple_voltage_ratio": _scale_float(form_values.get("voltage_ripple_ratio_percent"), 0.01),
            "ripple_current_pp_a": form_values.get("current_ripple_pp_a"),
            "isolation_required": form_values.get("isolation_required"),
            "bidirectional": form_values.get("bidirectional"),
            "load_type": _optional_str(form_values.get("load_type")),
            "priorities": _parse_priorities(form_values.get("priorities")),
        }
        return DesignIntent.from_dict(normalized)

    def run_ai_design(self, form_values: dict[str, object]) -> tuple[AIDesignReport | None, str | None]:
        """Run the AI design pipeline and capture user-readable errors."""

        try:
            intent = self.build_design_intent(form_values)
            report = self._pipeline_runner(intent)
        except Exception as exc:  # pragma: no cover - defensive GUI boundary
            self._state_store.ai_design_intent = None
            self._state_store.ai_design_report = None
            return None, f"AI design failed: {exc}"

        self._state_store.ai_design_intent = intent
        self._state_store.ai_design_report = report
        return report, None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _scale_float(value: object, scale: float) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value) * scale
    except (TypeError, ValueError):
        return None


def _parse_priorities(value: object) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        items = value.split(",")
    else:
        try:
            items = list(value)  # type: ignore[arg-type]
        except TypeError:
            items = [value]
    priorities: list[str] = []
    seen: set[str] = set()
    for item in items:
        token = str(item).strip()
        if not token or token in seen:
            continue
        seen.add(token)
        priorities.append(token)
    return tuple(priorities)

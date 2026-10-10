"""Small, explicit semantic checks independent of topology production models."""

from collections.abc import Mapping, Sequence
from math import fsum, isclose, isfinite
from numbers import Real


def _fail(rule: str, field: str, expected: object, actual: object) -> None:
    raise AssertionError(f"{rule}: {field}: expected {expected!r}; actual {actual!r}")


def _number(rule: str, field: str, value: object, *, nonnegative: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        _fail(rule, field, "finite real number", value)
    numeric = float(value)
    if nonnegative and numeric < 0.0:
        _fail(rule, field, "nonnegative number", value)
    return numeric


def _close(rule: str, field: str, expected: float, actual: object,
           *, abs_tol: float, rel_tol: float) -> None:
    _number("TOLERANCE", "abs_tol", abs_tol)
    _number("TOLERANCE", "rel_tol", rel_tol)
    value = _number(rule, field, actual, nonnegative=False)
    if not isclose(value, expected, abs_tol=abs_tol, rel_tol=rel_tol):
        _fail(rule, field, {"value": expected, "abs_tol": abs_tol, "rel_tol": rel_tol}, value)


def assert_loss_balance(*, components: Mapping[str, object], required_components: Sequence[str],
                        total_loss_w: object, output_power_w: object, efficiency: object,
                        loss_abs_tol: float, loss_rel_tol: float,
                        efficiency_abs_tol: float, efficiency_rel_tol: float) -> None:
    """Validate original totals, not a pre-corrected display snapshot."""
    required = tuple(required_components)
    if not required or len(set(required)) != len(required):
        _fail("LOSS_COMPONENTS", "required_components", "nonempty unique components", required)
    values = []
    for name in required:
        if name not in components:
            _fail("LOSS_COMPONENT_MISSING", name, "required component", "absent")
        values.append(_number("LOSS_COMPONENT_VALUE", name, components[name]))
    total = _number("LOSS_TOTAL_VALUE", "total_loss_w", total_loss_w)
    output = _number("LOSS_POWER", "output_power_w", output_power_w)
    if output <= 0.0:
        _fail("LOSS_POWER", "output_power_w", "positive modeled output power", output)
    expected_total = fsum(values)
    _close("LOSS_TOTAL", "total_loss_w", expected_total, total,
           abs_tol=loss_abs_tol, rel_tol=loss_rel_tol)
    eta = _number("LOSS_EFFICIENCY_VALUE", "efficiency", efficiency)
    if eta > 1.0:
        _fail("LOSS_EFFICIENCY_VALUE", "efficiency", "ratio in [0, 1]", eta)
    _close("LOSS_EFFICIENCY", "efficiency", output / (output + expected_total), eta,
           abs_tol=efficiency_abs_tol, rel_tol=efficiency_rel_tol)


def assert_operating_basis(*, expected: Mapping[str, object], actual: Mapping[str, object],
                           required_keys: Sequence[str],
                           tolerances: Mapping[str, tuple[float, float]]) -> None:
    """Compare stated basis, using (absolute, relative) tolerances per numeric key."""
    if not required_keys:
        _fail("BASIS_KEYS", "required_keys", "nonempty keys", required_keys)
    for key in required_keys:
        if key not in expected or key not in actual:
            _fail("BASIS_MISSING", key, expected.get(key, "required expected basis"), actual.get(key, "absent"))
        reference, value = expected[key], actual[key]
        if reference is None:
            _fail("BASIS_EXPECTED", key, "explicit basis", reference)
        if isinstance(reference, Real) and not isinstance(reference, bool):
            ref = _number("BASIS_EXPECTED", key, reference, nonnegative=False)
            if key not in tolerances:
                _fail("BASIS_TOLERANCE", key, "explicit (absolute, relative) tolerance", "absent")
            abs_tol, rel_tol = tolerances[key]
            _close("BASIS_VALUE", key, ref, value, abs_tol=abs_tol, rel_tol=rel_tol)
        elif value != reference:
            _fail("BASIS_SOURCE", key, reference, value)


def assert_fixed_hardware(*, before: Mapping[str, object], after: Mapping[str, object],
                          required_roles: Sequence[str], selection_calls: Sequence[object]) -> None:
    """The caller installs monitors; snapshots cannot establish zero selection calls."""
    if not required_roles:
        _fail("HARDWARE_ROLES", "required_roles", "nonempty roles", required_roles)
    for role in required_roles:
        for label, snapshot in (("before", before), ("after", after)):
            if role not in snapshot or snapshot[role] is None or snapshot[role] == "":
                _fail("HARDWARE_MISSING", f"{label}.{role}", "selected hardware identity", snapshot.get(role))
    if before != after:
        _fail("HARDWARE_CHANGED", "hardware_ids", dict(before), dict(after))
    if selection_calls:
        _fail("HARDWARE_SELECTION", "selection_calls", "no selection during fixed-hardware refresh", selection_calls)


def assert_physical_instances(*, instances: Sequence[Mapping[str, object]],
                             expected_roles: Sequence[str], expected_count: int) -> None:
    """Equal library models are legal; roles, design IDs and physical IDs are unique."""
    if expected_count <= 0 or len(set(expected_roles)) != expected_count:
        _fail("INSTANCE_CONTRACT", "expected_roles/count", "positive count and unique roles", (expected_roles, expected_count))
    if len(instances) != expected_count:
        _fail("INSTANCE_COUNT", "instances", expected_count, len(instances))
    for field in ("role", "design_id", "physical_id"):
        values = [item.get(field) for item in instances]
        if any(not isinstance(value, str) or not value for value in values):
            _fail("INSTANCE_MISSING", field, "nonempty identity for every instance", values)
        if len(set(values)) != expected_count:
            _fail("INSTANCE_UNIQUE", field, "unique identities", values)
        if field == "role" and set(values) != set(expected_roles):
            _fail("INSTANCE_ROLES", field, tuple(expected_roles), values)

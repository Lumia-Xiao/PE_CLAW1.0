"""Volume pie chart for Hardware Overview."""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from ...engines.hardware_overview import HardwareOverviewComponentGroup


def export_hardware_volume_pie(groups: list[HardwareOverviewComponentGroup], output_dir: str | Path) -> tuple[str, list[str]]:
    """Export the recommended hardware volume pie chart."""

    output_path = Path(output_dir) / "hardware_volume_pie.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_groups = [group for group in groups if group.status != "missing" and group.volume_cm3 is not None and group.volume_cm3 > 0.0]
    warnings: list[str] = []
    missing_names = [group.display_name for group in groups if group not in valid_groups]
    if missing_names:
        warnings.append("Volume pie excludes missing or zero-volume groups: " + ", ".join(missing_names) + ".")

    figure = Figure(figsize=(5.2, 4.4), dpi=120)
    axis = figure.subplots(1, 1)
    if not valid_groups:
        axis.axis("off")
        axis.text(0.5, 0.55, "Hardware volume data unavailable", ha="center", va="center", fontsize=12.0)
        axis.text(0.5, 0.44, "Run the relevant design stages before generating the overview.", ha="center", va="center", fontsize=9.0)
        warnings.append("Volume pie placeholder generated because no positive group volumes were available.")
    else:
        volumes = [float(group.volume_cm3) for group in valid_groups]
        total_volume_cm3 = sum(volumes)
        labels = [
            f"{group.display_name}\n{volume:.3g} cm^3\n{(volume / total_volume_cm3 * 100.0):.1f}%"
            for group, volume in zip(valid_groups, volumes)
        ]
        axis.pie(volumes, labels=labels, startangle=90.0, counterclock=False)
        axis.set_title(f"Recommended Hardware Volume Breakdown, Total = {total_volume_cm3:.3g} cm^3", fontsize=10.0)
        axis.axis("equal")
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()
    return str(output_path), warnings

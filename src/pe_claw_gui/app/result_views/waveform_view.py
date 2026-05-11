"""Waveform result view."""

from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ...models.design_report import DesignReport


class WaveformView(ttk.Frame):
    """Render the waveform bundle for the active report."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.figure = Figure(figsize=(9, 7), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        self.figure.clear()
        if report is None or report.waveform is None:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Generate topology waveforms to render plots here.", ha="center", va="center")
            ax.set_axis_off()
            self.figure.tight_layout()
            self.canvas.draw_idle()
            return

        waveform = report.waveform
        time_us = [t * 1e6 for t in waveform.time_s]
        if report.spec.topology_id == "three_level_tzcm_fixed_frequency":
            from ...models.operating_point import OperatingPoint
            from ...topologies.dc_dc.three_level_tzcm_fixed_frequency.mode import build_operating_state

            operating_state = build_operating_state(
                report.candidate,
                operating_point=report.operating_point
                if report.operating_point is not None
                else OperatingPoint(vin_v=waveform.operating_vin_v, load_ratio=waveform.load_ratio),
            )
            axes = [self.figure.add_subplot(4, 1, i + 1) for i in range(4)]

            gate_offsets = [3.0, 2.0, 1.0, 0.0]
            gate_series = [
                ("S1", waveform.gate_s1, gate_offsets[0]),
                ("S2", waveform.gate_s2, gate_offsets[1]),
                ("S3", waveform.gate_s3, gate_offsets[2]),
                ("S4", waveform.gate_s4, gate_offsets[3]),
            ]
            for label, series, offset in gate_series:
                axes[0].step(time_us, [value + offset for value in series], where="post", linewidth=1.3, label=label)
            axes[0].set_yticks([offset + 0.5 for offset in gate_offsets], labels=["S1", "S2", "S3", "S4"])
            axes[0].set_ylabel("Gates")
            axes[0].grid(True, alpha=0.35)

            vox_series = waveform.vox_voltage_v or waveform.switch_node_voltage_v
            axes[1].plot(time_us, vox_series, linewidth=1.4)
            axes[1].set_ylabel("Vox [V]", fontsize=8)
            axes[1].grid(True, alpha=0.35)

            axes[2].plot(time_us, waveform.inductor_current_a, linewidth=1.4)
            axes[2].set_ylabel("i_L [A]", fontsize=8)
            axes[2].grid(True, alpha=0.35)

            ripple_series = waveform.output_ripple_v or [value - waveform.operating_vout_v for value in waveform.output_voltage_v]
            axes[3].plot(time_us, ripple_series, linewidth=1.4)
            axes[3].set_ylabel("v_C ripple [V]", fontsize=8)
            axes[3].set_xlabel("Time [us]")
            axes[3].grid(True, alpha=0.35)

            for ax in axes:
                ax.set_xlim(time_us[0], time_us[-1])

            self.figure.suptitle(
                (
                    f"{report.spec.display_name} | Vin={waveform.operating_vin_v:.3f} V | "
                    f"Vout={waveform.operating_vout_v:.3f} V | D1={operating_state.d1:.4f} | D4={operating_state.d4:.4f}"
                ),
                fontsize=11,
            )
            self.figure.tight_layout(rect=[0, 0, 1, 0.97])
            self.canvas.draw_idle()
            return

        plots = [
            ("Switch-node voltage v_sw [V]", waveform.switch_node_voltage_v),
            ("Inductor current i_L [A]", waveform.inductor_current_a),
            ("Capacitor current i_C [A]", waveform.capacitor_current_a),
            ("Approx. output voltage v_o [V]", waveform.output_voltage_v),
        ]
        axes = [self.figure.add_subplot(len(plots), 1, i + 1) for i in range(len(plots))]

        for ax, (title, series) in zip(axes, plots, strict=True):
            ax.plot(time_us, series, linewidth=1.4)
            ax.set_ylabel(title, fontsize=8)
            ax.set_xlim(time_us[0], time_us[-1])
            ax.grid(True, alpha=0.35)

        axes[-1].set_xlabel("Time [us]")
        self.figure.suptitle(
            (
                f"{report.spec.display_name} | Vin={waveform.operating_vin_v:.3f} V | "
                f"Vout~={waveform.operating_vout_v:.3f} V | Duty={waveform.duty:.4f} | "
                f"Mode={waveform.mode}"
            ),
            fontsize=11,
        )
        self.figure.tight_layout(rect=[0, 0, 1, 0.97])
        self.canvas.draw_idle()

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
        refined = waveform.metadata.get("single_phase_inverter_refined_waveforms")
        if report.spec.topology_id == "single_phase_full_bridge_inverter" and isinstance(refined, dict):
            self._render_single_phase_inverter_waveforms(report, refined)
            return
        three_phase = waveform.metadata.get("three_phase_two_level_spwm_waveforms")
        if report.spec.topology_id == "three_phase_two_level_voltage_source_inverter" and isinstance(three_phase, dict):
            self._render_three_phase_two_level_waveforms(report, three_phase)
            return
        npc = waveform.metadata.get("three_phase_npc_pd_spwm_waveforms")
        if report.spec.topology_id == "three_phase_three_level_npc_inverter" and isinstance(npc, dict):
            self._render_three_phase_npc_waveforms(report, npc)
            return
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

    def _render_single_phase_inverter_waveforms(self, report: DesignReport, data: dict[str, object]) -> None:
        time_ms = [float(value) * 1e3 for value in _series(data, "time_s")]
        if not time_ms:
            return
        axes = [self.figure.add_subplot(5, 1, index + 1) for index in range(5)]
        gates = [("S1", 3.0), ("S2", 2.0), ("S3", 1.0), ("S4", 0.0)]
        for label, offset in gates:
            axes[0].step(time_ms, [value + offset for value in _series(data, f"gate_{label.lower()}")], where="post", label=label)
        axes[0].set_title("Single-phase unipolar SPWM gate states", fontsize=9)
        axes[0].set_yticks([3.5, 2.5, 1.5, 0.5], labels=[label for label, _ in gates])
        axes[0].grid(True, alpha=0.35)
        axes[1].plot(time_ms, _series(data, "mod_a"), label="m_A")
        axes[1].plot(time_ms, _series(data, "mod_b"), label="m_B")
        axes[1].plot(time_ms, _series(data, "carrier"), linewidth=0.6, label="carrier")
        axes[1].set_title("SPWM references and carrier", fontsize=9)
        axes[1].legend(fontsize=7, ncol=3)
        axes[1].grid(True, alpha=0.35)
        axes[2].step(time_ms, _series(data, "v_ab_pwm_v"), where="post", label="v_ab PWM")
        axes[2].plot(time_ms, _series(data, "vac_fundamental_v"), label="v_ac fundamental")
        axes[2].set_title("Bridge output voltage", fontsize=9)
        axes[2].set_ylabel("Voltage [V]")
        axes[2].legend(fontsize=7)
        axes[2].grid(True, alpha=0.35)
        axes[3].plot(time_ms, _series(data, "inductor_current_a"), label="i_L")
        axes[3].plot(time_ms, _series(data, "i_ac_fundamental_a"), label="i_ac fundamental")
        axes[3].set_title("Output inductor current", fontsize=9)
        axes[3].set_ylabel("Current [A]")
        axes[3].legend(fontsize=7)
        axes[3].grid(True, alpha=0.35)
        axes[4].plot(time_ms, _series(data, "dc_link_capacitor_current_pwm_a"), label="i_Cdc")
        axes[4].plot(time_ms, _series(data, "dc_link_voltage_v"), label="v_dc")
        axes[4].set_title("DC-link capacitor current and voltage", fontsize=9)
        axes[4].set_xlabel("Time [ms]")
        axes[4].legend(fontsize=7)
        axes[4].grid(True, alpha=0.35)
        self._finish_inverter_plot(report, axes, "Vac", "single-phase first-pass preview")

    def _render_three_phase_two_level_waveforms(self, report: DesignReport, data: dict[str, object]) -> None:
        time_ms = [float(value) * 1e3 for value in _series(data, "time_s")]
        if not time_ms:
            return
        axes = [self.figure.add_subplot(4, 1, index + 1) for index in range(4)]
        for key, label in (("va_phase_v", "v_aN"), ("vb_phase_v", "v_bN"), ("vc_phase_v", "v_cN")):
            axes[0].plot(time_ms, _series(data, key), label=label)
        axes[0].set_title("Three-phase phase voltages", fontsize=9)
        axes[0].set_ylabel("Voltage [V]")
        axes[0].legend(fontsize=7, ncol=3)
        axes[0].grid(True, alpha=0.35)
        for key, label in (("ia_a", "i_a"), ("ib_a", "i_b"), ("ic_a", "i_c")):
            axes[1].plot(time_ms, _series(data, key), label=label)
        axes[1].set_title("Three-phase phase currents", fontsize=9)
        axes[1].set_ylabel("Current [A]")
        axes[1].legend(fontsize=7, ncol=3)
        axes[1].grid(True, alpha=0.35)
        for key, label in (("mod_a", "m_a"), ("mod_b", "m_b"), ("mod_c", "m_c"), ("carrier", "carrier")):
            axes[2].plot(time_ms, _series(data, key), label=label)
        axes[2].set_title("SPWM references, carrier, and upper-switch states", fontsize=9)
        axes[2].legend(fontsize=7, ncol=4)
        axes[2].grid(True, alpha=0.35)
        axes[3].plot(time_ms, _series(data, "dc_link_bus_current_pwm_a"), label="i_Cdc proxy")
        axes[3].plot(time_ms, _series(data, "dc_link_voltage_v"), label="v_dc")
        axes[3].set_title("DC-link current proxy and voltage", fontsize=9)
        axes[3].set_xlabel("Time [ms]")
        axes[3].legend(fontsize=7)
        axes[3].grid(True, alpha=0.35)
        self._finish_inverter_plot(report, axes, "VLL", "three-phase two-level SPWM first-pass preview")

    def _render_three_phase_npc_waveforms(self, report: DesignReport, data: dict[str, object]) -> None:
        time_ms = [float(value) * 1e3 for value in _series(data, "time_s")]
        if not time_ms:
            return
        axes = [self.figure.add_subplot(5, 1, index + 1) for index in range(5)]
        for key, label in (("va_phase_v", "v_aN"), ("vb_phase_v", "v_bN"), ("vc_phase_v", "v_cN")):
            axes[0].plot(time_ms, _series(data, key), label=label)
        axes[0].set_title("NPC phase voltages", fontsize=9)
        axes[0].legend(fontsize=7, ncol=3)
        axes[0].grid(True, alpha=0.35)
        for key, label in (("ia_a", "i_a"), ("ib_a", "i_b"), ("ic_a", "i_c")):
            axes[1].plot(time_ms, _series(data, key), label=label)
        axes[1].set_title("NPC phase currents", fontsize=9)
        axes[1].legend(fontsize=7, ncol=3)
        axes[1].grid(True, alpha=0.35)
        for key, label in (("va_pole_v", "v_aO"), ("vb_pole_v", "v_bO"), ("vc_pole_v", "v_cO"), ("vab_pwm_v", "v_ab PWM")):
            axes[2].step(time_ms, _series(data, key), where="post", label=label)
        axes[2].set_title("NPC pole and line-line PWM voltages", fontsize=9)
        axes[2].legend(fontsize=7, ncol=4)
        axes[2].grid(True, alpha=0.35)
        for key, label in (("mod_a", "m_a"), ("mod_b", "m_b"), ("mod_c", "m_c"), ("carrier_upper", "carrier upper"), ("carrier_lower", "carrier lower")):
            axes[3].plot(time_ms, _series(data, key), label=label)
        axes[3].set_title("PD-SPWM references and carriers", fontsize=9)
        axes[3].legend(fontsize=7, ncol=5)
        axes[3].grid(True, alpha=0.35)
        for key, label in (("dc_link_capacitor_current_pwm_a", "i_Cdc"), ("upper_dc_link_capacitor_current_pwm_a", "i_Cupper"), ("lower_dc_link_capacitor_current_pwm_a", "i_Clower"), ("neutral_point_current_a", "i_neutral")):
            axes[4].plot(time_ms, _series(data, key), label=label)
        axes[4].set_title("Split DC-link and neutral-point current proxies", fontsize=9)
        axes[4].set_xlabel("Time [ms]")
        axes[4].legend(fontsize=7, ncol=4)
        axes[4].grid(True, alpha=0.35)
        self._finish_inverter_plot(report, axes, "VLL", "three-phase three-level NPC PD-SPWM first-pass preview")

    def _finish_inverter_plot(self, report: DesignReport, axes, voltage_label: str, mode_label: str) -> None:
        waveform = report.waveform
        for axis in axes:
            axis.set_xlim(axes[0].lines[0].get_xdata()[0], axes[0].lines[0].get_xdata()[-1])
        pf = waveform.metadata.get("operating_power_factor") if waveform is not None else None
        pf_text = f" | PF={float(pf):.3f}" if pf is not None else ""
        self.figure.suptitle(
            f"{report.spec.display_name} | Vdc={waveform.operating_vin_v:.3f} V | {voltage_label}={waveform.operating_vout_v:.3f} Vrms | Load={waveform.load_ratio:.3f} pu{pf_text}",
            fontsize=11,
        )
        self.figure.text(0.5, 0.01, f"{mode_label}; dead-time, Coss, and parasitic transients are not modeled.", ha="center", va="bottom", fontsize=7)
        self.figure.tight_layout(rect=[0, 0.035, 1, 0.97])
        self.canvas.draw_idle()


def _series(data: dict[str, object], key: str) -> list[float]:
    values = data.get(key, [])
    if not isinstance(values, list):
        return []
    return [float(value) for value in values]

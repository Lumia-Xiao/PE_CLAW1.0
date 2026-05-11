<p align="center">
  <img src="docs/assets/images/pe_claw1.0_logo.png" alt="PE-Claw 1.0 Logo" width="760">
</p>

# PE-Claw 1.0

**PE-Claw 1.0** is a rule-based automated power converter design platform for staged power-electronics converter design, component selection, loss estimation, thermal evaluation, Pareto-front analysis, efficiency sweeps, and engineering visualization.

PE-Claw is built for transparent engineering automation. It turns converter requirements into an auditable design workflow rather than a black-box optimization result.

```text
User specifications
-> topology selection
-> electrical parameter synthesis
-> waveform and stress extraction
-> semiconductor selection
-> capacitor bank selection
-> magnetic/inductor design
-> loss and efficiency analysis
-> hardware overview
-> engineering report artifacts
```

## Quick Start

Run PE-Claw from the project environment where dependencies are installed:

```bash
python -m pe_claw_gui
```

If installed editable, run from the repository root or from an active environment that can import `pe_claw_gui`.

## Current GUI Workflow

1. Select a converter category and topology, or open AI Design.
2. Fill in voltage, power, ripple, frequency, thermal, and device filter settings.
3. Click `Run Design` for topology synthesis and semiconductor selection.
4. Click `Run Capacitor` for input/output capacitor selection.
5. Click `Run Magnetics` for inductor selection.
6. Click `Generate Waveforms` for selected-hardware operating-point refresh.
7. Click `Run Efficiency Sweep` for fixed-hardware efficiency and loss trends from 0.1 to 1.0 p.u. load.
8. Review Summary, Waveforms, Devices, Capacitor PF, Capacitors, Inductor PF, Inductor, Loss, Efficiency, and Hardware Overview pages.

## Main Features

- Manual topology-based DC-DC converter design workflow.
- AI Design mode for deterministic system-level design assistance.
- Topology-specific electrical synthesis, waveform generation, and stress extraction.
- Semiconductor filtering, selection, loss estimation, and first-pass thermal evaluation.
- Input/output capacitor selection with Pareto-front views and geometry artifacts.
- Magnetic/inductor candidate generation, screening, Pareto-front selection, and geometry artifacts.
- Unified semiconductor, capacitor, and magnetic loss page.
- Fixed selected-hardware efficiency sweep from 0.1 to 1.0 p.u. load.
- Integrated hardware overview with volume breakdown and 2D/3D engineering visualization.

## Design Rules

PE-Claw separates design-point selection from operating-point analysis:

- `Run Design` selects semiconductor devices at the design point.
- `Run Capacitor` selects capacitor banks at the design point.
- `Run Magnetics` selects inductor designs at the design point.
- `Generate Waveforms` refreshes waveforms and operating-point losses using selected hardware.
- `Run Efficiency Sweep` scans load from 0.1 to 1.0 p.u. using selected hardware.

The efficiency sweep is not a re-optimized design at every load point. It represents fixed selected hardware operating across the load range.

## Architecture Snapshot

PE-Claw 1.0 follows a category-first, plugin-driven architecture:

```text
python -m pe_claw_gui
-> pe_claw_gui.__main__
-> pe_claw_gui.main
-> pe_claw_gui.app.main
-> PEClawMainWindow
-> NavigationBar + Workspace
-> controllers
-> pipeline
-> result views
```

Active source areas:

```text
src/pe_claw_gui/
|-- app/             GUI shell, controllers, topology forms, result views
|-- agents/          deterministic report and AI-summary helpers
|-- engines/         devices, capacitors, magnetics, losses, thermal, geometry
|-- libraries/       semiconductor, capacitor, magnetic, heatsink, mechanical data
|-- models/          dataclasses and DesignReport handoff objects
|-- pipeline/        staged design and operating-point pipelines
|-- topologies/      topology registry and active topology plugins
|-- visualization/   geometry, plot, and hardware overview rendering
```

See `PROJECT_ARCHITECTURE.md` for the current active architecture.

## Case Study: Buck Synchronous Rectified Unidirectional Converter

The PE-Claw 1.0 release case study uses the **Buck Synchronous Rectified Unidirectional** topology.

Design target:

| Parameter | Value |
|---|---:|
| Topology ID | `buck_synchronous_rectified_unidirectional` |
| Nominal input voltage | 500 V |
| Output voltage | 300 V |
| Output power | 5 kW |
| Output current | 16.6667 A |
| Switching frequency | 50 kHz |
| Inductor current ripple | 5 A peak-to-peak |
| Output voltage ripple | 0.6 V peak-to-peak |
| Operating mode | CCM |

The case study demonstrates:

```text
Electrical synthesis
-> waveform and stress calculation
-> semiconductor filtering and selection
-> input/output capacitor Pareto-front analysis
-> magnetic/inductor Pareto-front analysis
-> loss and efficiency calculation
-> fixed-hardware efficiency sweep
-> volume and hardware overview
```

Representative release images are stored under `docs/assets/images/`.

<p align="center">
  <img src="docs/assets/images/case_buck_sync_01_design_summary.png" alt="Buck synchronous design summary" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/case_buck_sync_02_waveforms.png" alt="Buck synchronous operating waveforms" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/case_buck_sync_03_semiconductor_selection.png" alt="Semiconductor selection result" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/case_buck_sync_04_input_capacitor_pareto.png" alt="Input capacitor Pareto front" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/case_buck_sync_06_output_capacitor_pareto.png" alt="Output capacitor Pareto front" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/case_buck_sync_08_inductor_pareto.png" alt="Inductor Pareto front" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/efficiency_curve.png" alt="Fixed-hardware efficiency curve" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/loss_breakdown_stacked.png" alt="Loss breakdown stacked plot" width="820">
</p>

<p align="center">
  <img src="docs/assets/images/overview_hardware_2d.png" alt="Hardware overview 2D" width="900">
</p>

<p align="center">
  <img src="docs/assets/images/overview_hardware_3d.png" alt="Hardware overview 3D" width="900">
</p>

## Outputs and Artifacts

Typical PE-Claw outputs include:

- `DesignReport` handoff objects.
- Waveform plots and operating-point summaries.
- Semiconductor selection and loss summaries.
- Capacitor Pareto-front plots and capacitor-bank geometry.
- Inductor Pareto-front plots and magnetic geometry.
- Loss breakdown and fixed-hardware efficiency sweep plots.
- Hardware overview images.
- CSV, JSON, and report artifacts.

Common artifact folders include:

```text
outputs/capacitor_design/
outputs/magnetic_design/
outputs/efficiency_sweep/
outputs/hardware_overview/
```

## Current Limitations

PE-Claw 1.0 is an engineering automation platform and prototype design environment. Current limitations include:

- Capacitor loss uses first-pass datasheet ESR/Irms models.
- Harmonic-by-harmonic high-frequency capacitor loss is future work.
- Magnetic loss and thermal estimation are first-pass engineering estimates.
- Semiconductor heatsink sizing is proxy-based, not CFD or catalog-optimized.
- Cost, availability, reliability, and lifetime prediction are not fully integrated.
- Geometry output is engineering visualization, not manufacturable CAD or PCB layout.
- AI Design mode is deterministic and structured-input based.

## Roadmap

### PE-Claw 1.0

Rule-based automated power converter design platform:

```text
user input
-> topology plugin
-> parameter synthesis
-> component selection
-> loss / thermal / volume analysis
-> engineering visualization
```

### PE-Claw 2.0

AI-assisted design co-pilot:

- natural-language requirement parsing;
- topology advising;
- design-space pruning;
- design memory and case retrieval;
- explanation generation;
- surrogate-assisted optimization.

### PE-Claw 3.0

Autonomous power converter design agent:

- full agentic design loop;
- self-repair candidate generation;
- simulation export;
- BOM and report generation;
- multi-objective global optimization;
- interactive design explanation.

## Documentation

- `README.md`: official GitHub release README.
- `README_Test.md`: local debugging, validation, and development testing notes only.
- `PROJECT_ARCHITECTURE.md`: current active architecture.
- `DEVELOPMENT.md`: developer workflow and documentation rules.
- `report1.md`: compact chronological engineering change log.

## License


Copyright (c) 2026 [Ziheng Xiao]

All rights reserved.

This software and its associated source code, component libraries, magnetic design data, capacitor databases, device selection rules, optimization methods, documentation, and generated datasets are proprietary.

Permission is granted only to view this repository for academic evaluation and demonstration purposes.

Without prior written permission, no person or organization may copy, modify, redistribute, sublicense, commercialize, integrate, train models on, or use this software or its embedded libraries in any product, service, research platform, or commercial workflow.

For licensing inquiries, please contact: [ziheng.xiao@ntu.edu.sg]

## Contact

**Dr. Ziheng Xiao**  
Energy Research Institute @ NTU, Nanyang Technological University, Singapore  
Homepage: <https://lumia-xiao.github.io/>  
Email: ziheng.xiao@ntu.edu.sg

## Intellectual Property Notice

PE-Claw is an original power electronics design and optimization platform developed by the author.

The software architecture, embedded component libraries, semiconductor database, magnetic component database, capacitor selection database, automatic selection rules, Pareto optimization workflow, and visualization logic are protected intellectual property.

This public repository is provided only for demonstration and academic evaluation. Unauthorized copying, redistribution, commercial use, or integration into other software platforms is not permitted.

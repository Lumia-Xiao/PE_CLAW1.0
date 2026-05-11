# PE-Claw Project Architecture

## Runtime Entry Path

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

## GUI Architecture

- `NavigationBar`: category/topology/action navigation.
- `Workspace`: page and report rendering host.
- Category views: converter category and topology selection pages.
- Topology forms: topology-specific raw input collection.
- AI Design page: natural-language/structured design intent entry.
- Controllers: bridge GUI state to pipeline calls.
- Result views: render summary, waveform, device, capacitor, inductor, loss, efficiency, and hardware overview data.

## Manual Workflow

```text
topology selection
  -> raw input
  -> Run Design
  -> Run Capacitor
  -> Run Magnetics
  -> Generate Waveforms
  -> Run Efficiency Sweep
  -> render report
```

Run Design performs electrical synthesis and semiconductor selection. Run Capacitor and Run Magnetics are separate hardware-selection stages. Generate Waveforms refreshes the current operating point. Run Efficiency Sweep evaluates the already selected hardware from 0.1 p.u. to 1.0 p.u. load and does not reselect hardware.

## AI Design Workflow

```text
AIDesignPage
  -> AIDesignController
  -> DesignIntent
  -> topology_recommender
  -> run_ai_design_pipeline
  -> design_checker
  -> report_agent
  -> AIDesignView
```

## Pipeline Stages

- `run_full_pipeline`: full manual design orchestration.
- `run_topology_pipeline`: topology plugin synthesis/evaluation.
- `run_device_pipeline`: semiconductor selection.
- `run_capacitor_pipeline`: capacitor selection and artifacts.
- `run_magnetic_pipeline`: inductor selection and Pareto artifacts.
- `run_loss_pipeline`: selected-hardware loss aggregation/refresh.
- `run_efficiency_sweep_pipeline`: fixed selected-hardware load sweep with efficiency and loss-breakdown artifacts.
- `run_thermal_pipeline`: first-pass thermal estimation.
- `run_geometry_pipeline`: engineering geometry artifacts.
- `run_operating_point_refresh`: waveform and selected-hardware operating refresh.
- `run_ai_design_pipeline`: AI Design candidate flow.

## Topology Plugin Structure

Active DC-DC topology plugins live under `src/pe_claw_gui/topologies/dc_dc/`. A typical plugin contains:

- `input_schema.py`: normalize form/raw input.
- `synthesizer.py`: nominal design calculations.
- `waveform.py`: waveform generation.
- `stress.py`: semiconductor stress extraction.
- `evaluator.py`: topology-level report assembly.
- `mode.py`: mode detection when needed.
- `__init__.py`: exposes the plugin object.

Topology form binding is managed by `topologies/base/registry.py`, which maps registered plugins to form classes.

## Active Engine And Library Structure

- Semiconductor libraries and device engines: `libraries/semiconductors/`, `engines/devices/`, `pipeline/run_device_pipeline.py`.
- Capacitor libraries and engines: `libraries/capacitors/`, `engines/capacitors/`, `pipeline/run_capacitor_pipeline.py`.
- Magnetic engines: `engines/magnetics/`, `libraries/magnetics/`, `pipeline/run_magnetic_pipeline.py`.
- Losses: `engines/losses/`, device/capacitor/magnetic loss paths, `pipeline/run_loss_pipeline.py`.
- Thermal: `engines/thermal/`, `pipeline/run_thermal_pipeline.py`.
- Geometry/visualization: `engines/geometry/`, `visualization/geometry/`, `visualization/semiconductors/`.
- Hardware overview: `engines/hardware_overview.py`, `visualization/hardware_overview/`, result view integration.
- Efficiency sweep: `pipeline/run_efficiency_sweep_pipeline.py`, `models/efficiency_sweep.py`, and the Efficiency result page.

## Design-Point Vs Operating-Point Rule

Hardware selection occurs at the design point. Operating-point refresh reuses the selected semiconductor, capacitor, and magnetic hardware. Generate Waveforms does not rerun hardware selection.

Efficiency Sweep follows the same rule over a 0.1-1.0 p.u. load grid. It reuses selected semiconductor devices, selected capacitor banks when available, and selected magnetic designs when available. Missing capacitor or magnetic stages are reported as warnings, while missing semiconductor selection blocks the sweep.

## Removed Legacy Namespaces

These old namespaces were removed and should not be reintroduced:

- `topologies/boost/`
- `app/tabs/`
- `topologies/buck/`
- `waveform/`
- `losses/`
- `core/`
- `devices/`

## Future AI-Agent Direction

Future work can extend AI Design toward:

- natural-language requirement parsing;
- design memory and case retrieval;
- surrogate-assisted optimization;
- self-repair candidate loops;
- a full design chain managed through AI Design.

## Documentation Roles

- `README.md` is the release-facing GitHub README.
- `README_Test.md` / `readme_test.md` is internal local debug and validation documentation.
- `report1.md` is the compact engineering change log.

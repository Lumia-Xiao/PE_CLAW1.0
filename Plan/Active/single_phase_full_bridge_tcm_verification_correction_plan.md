# 单相全桥 TCM 核实与修正计划

## 1. 计划目标

核实并修正单相全桥逆变器 TCM 模式的以下问题：

1. GUI Generate waveform 是否显示完整的一个工频周期；
2. TCM 详细波形、逐周期开关频率和谷值电流目标是否正确生成；
3. efficiency sweep 是否使用每个负载点实际的 TCM 开关频率和开关事件电流；
4. 半导体开关损耗为何在不同负载下几乎保持固定；
5. TCM 电感、电容、半导体损耗和效率结果是否闭合；
6. 输出目录中的 manifest 是否能正确结束为完成状态。

本计划只处理：

- `single_phase_full_bridge_inverter`；
- `conduction_mode = TCM`；
- TCM 波形、开关损耗、效率扫描和相关 GUI 展示。

不扩大到 NPC、CCM 或其他拓扑，除非共享代码合同验证必须进行定向回归。

## 2. 必须保持的约束

- 不新增用户输入字段。
- 保持现有 TCM 输入字段、默认值和校验逻辑。
- 保持 TCM 负谷值电流目标的现有输入语义。
- 保持 GUI 显示一个完整工频周期，默认 `50 Hz` 时为 `0–20 ms`。
- 保持 SiC 反向恢复损耗为零。
- 开通损耗必须根据实际开关时刻电流判定：
  - 电流小于 `0 A`：软开通，`Eon = 0`；
  - 电流大于等于 `0 A`：硬开通，使用实际电流计算 `Eon`。
- 关断损耗使用实际关断时刻电流。
- TCM 开关频率必须来自 TCM 实际逐周期数据，不能使用固定设计输入频率替代。
- 不恢复已删除的 `Other loss`。
- 不修改 NPC 的生产代码、公式和输出字段。
- 所有测试临时文件写入：

```text
C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\pytest_temp\single-phase-full-bridge-tcm-stepN\
```

- 每一步完成后必须：专项测试、`git diff --check`、独立 `commit`、`push`，并核对远端 HEAD。
- `outputs/`、`pytest_temp/`、缓存和手动设计结果不加入 Git。

## 3. 当前已知现象

最近一次 TCM 输出目录：

```text
outputs/20260906_sp_fbi_b48dd62b
```

输入为：

- `Pout = 1000 W`；
- `Vac = 230 Vrms`；
- `Vdc = 400 V`；
- `f_line = 50 Hz`；
- `fsw = 20 kHz`；
- `fsw_min = 5 kHz`；
- `fsw_max = 100 kHz`；
- `tcm_valley_current_target = -1 A`；
- 器件为 Wolfspeed MOSFET。

观察到：

- 满载效率约 `97.94%`；
- 满载半导体损耗约 `19.99 W`；
- 从 `5%` 到 `100%` 负载，半导体损耗几乎保持 `19.99 W`；
- `Other loss = 0`；
- manifest 仍为 `status = running`；
- `semiconductor_design` 和 `validation` 显示 `not_started`；
- TCM 详细波形在代码中已经生成，但输出目录未明确保存独立的详细波形证据。

这些现象需要先通过代码路径和独立诊断确认，不能直接假设为计算错误。

## 4. 重点代码范围

### 4.1 TCM 波形生成

```text
src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/waveform.py
```

重点检查：

- `_generate_tcm_envelope_waveforms()`；
- `_build_tcm_detail_current_waveform()`；
- `_tcm_cycle_state()`；
- `detail_time_s`、`detail_fsw_hz`、`detail_natural_fsw_hz`；
- `cycle_start_time_s`、`cycle_fsw_hz`；
- `time_span_s` 与 `1 / f_line_hz` 的关系。

### 4.2 GUI 波形显示

```text
src/pe_claw_gui/app/result_views/waveform_view.py
```

重点检查：

- `_render_single_phase_tcm_waveforms()`；
- 详细时间轴与包络时间轴是否混用；
- 所有绘图数据与对应时间轴长度是否一致；
- 横坐标是否固定为完整工频周期。

### 4.3 效率扫描和开关损耗

```text
src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py
src/pe_claw_gui/pipeline/run_device_pipeline.py
src/pe_claw_gui/engines/devices/loss_evaluator.py
```

重点检查：

- efficiency sweep 每个负载点是否重新生成 TCM waveform；
- operating point 是否正确传递 `load_ratio`；
- TCM 详细开关频率是否进入损耗计算；
- 事件数量是否随实际 TCM 周期变化；
- 是否错误复用设计点半导体损耗；
- 是否存在固定频率、固定事件数或固定负载电流缓存；
- 总损耗是否重复计算或遗漏开关损耗。

### 4.4 输出状态和证据

```text
src/pe_claw_gui/pipeline/
outputs/
```

重点检查：

- TCM 波形是否保存到当前设计输出目录；
- manifest 阶段状态是否在完整流程结束时正确收尾；
- `status = running` 是否仅为状态更新遗漏；
- `validation = not_started` 是否符合当前流程定义，还是应生成验证结果。

## 5. 分步执行安排

### 第一步：建立 TCM 当前结果基线

**目标：** 固化最近 TCM case 的输入、波形、损耗和状态，形成后续修改的对照。

**执行内容：**

1. 读取最近 TCM 输出目录的 `design_request.json`、`manifest.json`、`efficiency_sweep.csv`、`chosen_designs.csv` 和 `hardware_overview_payload.json`；
2. 记录各负载点的输出功率、效率、总损耗、半导体损耗、电感损耗、电容损耗和 `Other loss`；
3. 直接调用插件生成默认 TCM waveform；
4. 记录：
   - `time_span_s`；
   - `1/f_line`；
   - `detail_time_s` 首尾时间；
   - 详细采样点数；
   - `detail_fsw_hz` 的最小值、最大值、平均值和唯一值数量；
   - `cycle_fsw_hz` 的最小值、最大值和周期数量；
   - 平均电流、峰值包络、谷值包络；
   - TCM 混合模式和低斜率诊断；
5. 将诊断写入：

```text
pytest_temp/single-phase-full-bridge-tcm-step1/baseline.json
```

**验收标准：**

- 能明确区分包络时间轴和详细 TCM 时间轴；
- 能确认 waveform 是否覆盖完整工频周期；
- 能确认半导体损耗是否在效率扫描中保持固定；
- 不修改生产代码。

**提交：**

```text
test: establish full-bridge TCM verification baseline
```

### 第二步：验证 TCM 波形和 GUI 时间轴合同

**目标：** 确认 Generate waveform 使用正确的 TCM 数据，并且所有曲线都能在一个工频周期内绘制。

**修改范围：**

- TCM 专项合同测试；
- 必要时仅修改 GUI 波形显示代码。

**执行内容：**

1. 验证 `WaveformSet.time_span_s == 1/f_line_hz`；
2. 验证包络时间轴从 `0` 到 `1/f_line_hz`；
3. 验证详细 TCM 时间轴从 `0` 到 `1/f_line_hz`；
4. 验证详细电流、详细频率、平均电流和包络数据分别与自己的时间轴等长；
5. 验证 GUI 绘图函数不会把详细时间轴与包络数组混用；
6. 验证默认 `50 Hz` 工频显示范围为 `0–20 ms`；
7. 验证低斜率区间、混合模式区间不会截断工频末端。

**验收标准：**

- TCM Generate waveform 不因数组长度不一致而报错；
- 每个子图的横坐标覆盖同一个完整工频周期；
- 不修改 TCM 计算结果。

**提交：**

```text
test: validate full-bridge TCM waveform display contract
```

### 第三步：核实 efficiency sweep 的 TCM operating point 传递

**目标：** 确认每个负载点都重新生成对应的 TCM 波形，而不是复用满载设计点波形或损耗。

**重点检查：**

- `run_efficiency_sweep_pipeline.py` 中的 operating point 生成；
- `plugin.generate_waveforms(candidate, operating_point=...)` 调用；
- TCM `load_ratio`、输出功率和电流幅值传递；
- waveform metadata 是否随负载变化。

**执行内容：**

1. 选取 `0.05`、`0.5`、`1.0` 三个负载点；
2. 分别生成 TCM waveform；
3. 比较 `iavg`、峰值/谷值包络、`detail_fsw_hz` 和 `cycle_fsw_hz`；
4. 确认低负载和满载的 TCM 数据确实不同；
5. 检查效率扫描是否将每个 operating point 的结果传给损耗计算；
6. 增加测试，防止 efficiency sweep 固定复用设计点 TCM 数据。

**验收标准：**

- 不同负载点的 TCM 电流和频率数据能够反映负载变化；
- 每个负载点的效率计算都基于自己的 waveform；
- 不增加用户输入。

**提交：**

```text
test: verify TCM operating-point waveform refresh
```

### 第四步：核实 TCM 开关事件和实际开关频率来源

**目标：** 确认开关损耗计算使用真实 TCM 周期，而不是固定 `fsw_hz` 或 CCM 的固定事件轴。

**执行内容：**

1. 追踪 TCM waveform metadata 到 `run_device_pipeline.py` 的开关损耗入口；
2. 确认当前 TCM 是否有逐周期开关事件列表；
3. 如果已有事件数据，检查事件数量、事件时间和事件频率统计；
4. 如果没有事件数据，设计最小的 TCM 事件记录结构，至少包括：
   - `event_time_s`；
   - `event_type`；
   - `switch_name` 或物理位置；
   - `signed_current_A`；
   - `blocking_voltage_V`；
   - `switching_period_s` 或相邻事件间隔；
   - `soft_turn_on` / `hard_turn_on`；
5. 确认 TCM 的负谷值电流是否真的在开通时刻出现；
6. 确认 SiC 或 MOSFET 器件模型对反向恢复损耗的处理符合现有合同；
7. 不在本步骤改变公共事件能量模型接口。

**验收标准：**

- 事件时间覆盖一个完整工频周期；
- 事件统计能够反映 TCM 的变频特征；
- 事件电流不是正弦峰值或设计点固定电流；
- 事件能量接口仍只读取公共字段。

**提交：**

```text
test: audit TCM switching event source
```

### 第五步：修正 TCM 逐事件开关损耗累计

**目标：** 使效率扫描中的半导体损耗随实际 TCM 工作点和开关频率变化。

**执行内容：**

1. 对每个 TCM operating point 重新获取完整工频周期事件；
2. 对每个事件使用实际开关时刻电流和实际直流电压；
3. 开通事件按实际电流极性分类：
   - `I < 0`：`Eon = 0`；
   - `I >= 0`：按实际电流计算 `Eon`；
4. 关断事件按实际电流计算 `Eoff`；
5. SiC 二极管反向恢复损耗保持为零；
6. 按事件总能量除以工频周期和物理开关位置数得到平均损耗；
7. 清除或避免复用固定设计点的 TCM 半导体开关损耗；
8. 保持导通损耗、Eoss、栅极损耗和器件数量换算逻辑不变；
9. 保持 `Other loss = 0`。

**验收标准：**

- 低负载、半载、满载的半导体损耗有可解释变化；
- TCM 开关频率变化能反映到开关损耗；
- 硬/软开通数量和事件电流范围可审计；
- 不出现重复乘以物理器件数量的问题；
- 共享 `loss_evaluator` 公共接口保持兼容。

**提交：**

```text
fix: calculate full-bridge TCM switching loss per event
```

### 第六步：核实 TCM 电感和电容损耗输入

**目标：** 确认 TCM 的高频电流数据没有错误传递到磁性件和电容损耗模型。

**执行内容：**

1. 检查电感损耗使用的是 TCM 实际电流还是仅使用包络平均值；
2. 检查峰值、谷值和 RMS 的计算时间轴是否为完整工频周期；
3. 检查电容损耗使用的 DC-link 电流时间轴是否与其数据等长；
4. 检查 TCM 高频电流 RMS proxy 与低频能量平衡电流的使用边界；
5. 保持当前电容设计输入语义，不新增输入；
6. 若发现错误，只做数据源和时间轴的最小修正。

**验收标准：**

- 电感和电容损耗不出现数量级异常；
- 损耗积分只覆盖一个工频周期；
- 电感饱和电流、实际 TCM 峰值和设计裕量可比较；
- 不改变器件和磁件选择算法的无关部分。

**提交：**

```text
fix: align TCM magnetic and capacitor loss waveforms
```

### 第七步：修正设计输出状态和 TCM 结果证据

**目标：** 让 TCM 设计输出能够明确表示完成，并保留可审计的波形和损耗结果。

**执行内容：**

1. 检查完整设计流程的阶段状态收尾；
2. 修正明确属于状态更新遗漏的 `status = running`；
3. 明确 `semiconductor_design` 和 `validation` 是否应为 `succeeded`、`not_applicable` 或其他已有合法状态；
4. 不伪造未执行的 validation 结果；
5. 在 TCM 输出目录保存最小诊断 JSON，至少包含：
   - 输入快照；
   - 工频周期；
   - 详细波形时间范围；
   - TCM 开关频率范围；
   - 硬/软开通统计；
   - 半导体、电感、电容和其他损耗；
   - warning 和失败原因。

**验收标准：**

- 输出 manifest 状态与实际阶段一致；
- 不把未执行的验证标记为成功；
- TCM 设计结果可以脱离 GUI 独立复核。

**提交：**

```text
fix: finalize full-bridge TCM output status and evidence
```

### 第八步：TCM 最终专项验收

**目标：** 完成 TCM 的最小闭环验证，不扩大到其他拓扑全量回归。

**建议验证内容：**

1. 默认 TCM 工况；
2. 低负载、半载、满载 operating point；
3. 不同 TCM 最小/最大频率边界；
4. 正常 TCM 区间和低斜率混合模式区间；
5. GUI Generate waveform 路径；
6. 事件级开关损耗；
7. 电感、电容和效率汇总；
8. `Other loss = 0`；
9. 不修改 NPC 的定向合同测试。

**验收标准：**

- TCM GUI 显示一个完整工频周期；
- 详细波形数组和时间轴长度一致；
- TCM 开关频率范围和事件数可解释；
- 半导体损耗不再无条件固定为设计点值；
- 负电流开通为软开通，`Eon = 0`；
- 非负电流开通和关断使用实际事件电流；
- SiC 反向恢复损耗为零；
- 电感和电容损耗输入时间轴正确；
- `Other loss = 0`；
- manifest 收尾状态正确；
- 所有修改完成独立 commit 和 push。

**建议测试命令：**

```powershell
python -B -m pytest -q `
  tests/test_dc_ac_single_phase_full_bridge_contract.py `
  tests/test_single_phase_full_bridge_switching_loss.py `
  tests/test_single_phase_full_bridge_periodic_current.py `
  tests/test_dc_ac_operating_refresh_gui_chain.py `
  tests/test_dc_ac_three_phase_three_level_npc_contract.py `
  --basetemp=pytest_temp/single-phase-full-bridge-tcm-step8/final-tests `
  --junitxml=pytest_temp/single-phase-full-bridge-tcm-step8/final-tests.xml

python -B -m compileall -q src tests
git diff --check
```

## 6. 计划状态表

| 步骤 | 状态 | 实现 commit | 回执 commit | 远端 push | 证据 |
|---|---|---|---|---|---|
| 1 | 已完成 | 待本次提交 | 待本次提交 | 待本次提交 | `baseline.json`; `12 passed`; `compileall`; `git diff --check` |
| 2 | 已完成 | 待本次提交 | 待本次提交 | 待本次提交 | `13 passed`; GUI TCM four-axis smoke; full line-cycle axis checks |
| 3 | 已完成 | 待本次提交 | 待本次提交 | 待本次提交 | `19 passed`; 5%/50%/100% TCM operating-point refresh checks |
| 4 | 已完成 | 待本次提交 | 待本次提交 | 待本次提交 | `19 passed`; TCM event-source audit; fixed-loss root cause recorded |
| 5 | 已完成 | `e320ce4` | 待本次提交 | 已推送 | `28 passed`; TCM 逐周期事件损耗；每周期 4 个换相事件；compileall; diff-check |
| 6 | 已完成 | `535a4d9` | 待本次提交 | 已推送 | `29 passed`; detailed TCM current period contract; compileall; diff-check |
| 7 | 进行中 | `9a41075` | 待本次提交 | 已推送 | 状态收尾问题已定位并修复；TCM 诊断 JSON 待继续完成 |
| 8 | 待执行 | - | - | - | - |

每一步完成后必须更新：

- 实际修改文件；
- 测试命令和结果；
- 输出证据路径；
- 实现 commit；
- 文档回执 commit；
- 远端 branch 和 HEAD。

### 第一步执行回执

- 读取并固化最新 TCM 输出：`outputs/20260906_sp_fbi_b48dd62b`。
- 基线文件：`pytest_temp/single-phase-full-bridge-tcm-step1/baseline.json`。
- 输入模式：TCM；`f_line = 50 Hz`；`fsw_min = 5 kHz`；`fsw_max = 100 kHz`；谷值目标 `-1 A`。
- 时间轴：`WaveformSet.time_span_s = 0.02 s`，包络轴和详细 TCM 轴均覆盖 `0–0.02 s`，即完整一个工频周期。
- 详细 TCM 波形：`4061` 个采样点、`508` 个 TCM 周期；详细开关频率范围约 `8.705–39.153 kHz`，平均约 `28.887 kHz`。
- efficiency sweep 基线：20 个负载点的半导体损耗全部为 `19.993834141874594 W`，已确认固定损耗现象，留待第 3 至第 5 步定位。
- 输出状态基线：manifest `status = running`；`semiconductor_design = not_started`；`validation = not_started`，留待第 7 步核实。
- 验证：`python -B -m pytest -q tests/test_single_phase_full_bridge_tcm_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step1/tests` -> `12 passed in 20.92s`；`python -B -m compileall -q src tests` 通过；`git diff --check` 通过。
- 本步骤未修改生产计算逻辑；只新增基线测试和诊断证据。

### 第二步执行回执

- 验证 TCM GUI 使用独立时间轴：详细电感电流和详细开关频率使用 `detail_time_s`，输出电压和 DC-link 包络使用 `time_s`。
- 验证默认 `50 Hz` 工况四个 GUI 子图均显示 `0–20 ms`，不再混用不同长度数组。
- 验证包络轴和详细轴均从 `0` 到 `1/f_line`，详细采样数量与详细时间轴长度一致，低斜率/混合模式数据未截断工频末端。
- 新增 GUI TCM 渲染 smoke 测试，未修改 TCM 计算和损耗逻辑。
- 验证：`python -B -m pytest -q tests/test_dc_ac_packaged_gui_runtime.py::test_single_phase_full_bridge_tcm_waveform_renders_with_separate_time_axes tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_single_phase_full_bridge_tcm_baseline.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step2/tests` -> `13 passed in 31.24s`；`compileall` 通过；`git diff --check` 通过。

### 第三步执行回执

- 检查 `run_efficiency_sweep_pipeline.py::_evaluate_load_point()`：每个负载点通过 `_sweep_operating_point()` 创建新的 `OperatingPoint(load_ratio=load_pu)`，并传给 `plugin.generate_waveforms(..., operating_point=...)`。
- 新增 5%、50%、100% 负载的 TCM operating-point 测试，确认 `waveform.load_ratio`、平均电流峰值和详细开关频率随负载重新计算，而不是复用固定设计点波形。
- 确认 `_sweep_operating_point()` 保留 PF，并正确传递低载、半载和满载比例。
- 本步骤未修改生产代码；半导体损耗在效率扫描中仍固定的原因留待第 4/5 步继续定位。
- 验证：`python -B -m pytest -q tests/test_single_phase_full_bridge_tcm_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_dc_ac_operating_refresh_gui_chain.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step3/tests` -> `19 passed in 34.46s`；`compileall` 通过；`git diff --check` 通过。

### 第四步执行回执

- 核实单相全桥开关损耗入口：`run_device_pipeline.py::_apply_full_bridge_event_switching_loss()` 只读取 `single_phase_inverter_refined_waveforms.switching_events`。
- TCM waveform 使用 `single_phase_inverter_tcm_envelope`，当前只提供 `detail_time_s`、`detail_inductor_current_a`、`detail_cycle_fsw_hz` 等包络/详细周期数据，没有 `switching_events`。
- 因此 TCM 进入 `_apply_full_bridge_event_switching_loss()` 时会因事件列表缺失直接返回设计点代表性开关损耗，不使用 TCM 实际逐周期频率或事件电流；这解释了效率扫描中半导体损耗固定为约 `19.993834 W` 的现象。
- 公共 `evaluate_switching_event_energy()` 已确认支持负电流软开通、非负电流硬开通、实际阻断电压和 SiC 反向恢复为零；第 4 步未修改该公共接口。
- 新增 TCM 事件源审计测试，固化当前缺口，留待第 5 步建立最小 TCM 事件记录并接入逐事件损耗。
- 验证：`python -B -m pytest -q tests/test_single_phase_full_bridge_tcm_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_dc_ac_operating_refresh_gui_chain.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step4/tests` -> `20 passed in 36.45s`；`compileall` 和 `git diff --check` 通过。
- 本步骤未修改生产代码和公共损耗公式。

### 第五步执行回执

- 在 `waveform.py` 中为每个实际重构的 TCM 周期生成逐事件记录；事件电流分别取周期谷值和峰值，阻断电压取周期起点对应的实际 DC-link 电压。
- 依据实际电流极性标记硬/软开通：负电流开通交由公共 `evaluate_switching_events()` 产生 `Eon=0`，非负电流按实际电流计算，关断按峰值电流计算；SiC 反向恢复保持为零。
- 修正事件映射：每个 TCM 周期只生成活动桥臂的 4 个物理换相事件，事件数为 `4 * detail_cycle_count`，避免将同一周期复制到 S1-S4 后重复计数；汇总继续按 `sum(Eevent)/(4*Tline)` 换算四个物理位置的平均损耗。
- 在 `run_device_pipeline.py` 中让 TCM 事件列表优先进入现有全桥公共事件损耗入口，避免回退到固定设计点代表性开关损耗；导通损耗、Eoss、栅极损耗及其他公共接口保持不变。
- 验证：`python -B -m pytest -q tests/test_single_phase_full_bridge_tcm_baseline.py tests/test_single_phase_full_bridge_switching_loss.py tests/test_dc_ac_single_phase_full_bridge_contract.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step5/tests` -> `28 passed in 77.49s`；`python -B -m compileall -q src tests` 通过；`git diff --check` 通过。
- 实现提交：`e320ce4`（`fix: calculate full-bridge TCM switching loss per event`）已推送到 `origin/codex/npc-output-run-isolation-step1`；本步骤回执提交将在本次文档更新后生成。

### 第六步执行回执

- 修正 TCM 电感磁件请求：优先从 `single_phase_inverter_tcm_envelope.detail_time_s` 和 `detail_inductor_current_a` 对完整一个工频周期进行梯形积分，得到实际详细电流 RMS 和峰值，不再优先使用候选元数据中的 20 段包络 RMS/峰值。
- 保留候选元数据作为详细波形不可用时的兼容回退，并记录 `tcm_current_stats_basis`，不改变器件或磁件选择算法的其他部分。
- 核实电容请求继续使用 TCM 详细 DC-link 电流 `tcm_dc_link_capacitor_current_detail_time_s/detail_a`；时间轴与电流数组严格等长，覆盖 `0–1/f_line`，并由公共电容选择器执行时间积分 RMS、充电量和 ESR 纹波计算。
- 增加 TCM 合同测试，验证详细电感 RMS/峰值来源、电容电流时间轴长度和完整工频周期覆盖。
- 验证：`python -B -m pytest -q tests/test_single_phase_full_bridge_tcm_baseline.py tests/test_single_phase_full_bridge_switching_loss.py tests/test_dc_ac_single_phase_full_bridge_contract.py --basetemp=pytest_temp/single-phase-full-bridge-tcm-step6/tests` -> `29 passed in 80.10s`；`python -B -m compileall -q src tests` 通过；`git diff --check` 通过。
- 实现提交：`535a4d9`（`fix: align TCM magnetic and capacitor loss waveforms`）已推送到 `origin/codex/npc-output-run-isolation-step1`；本步骤文档回执提交将在本次更新后生成。

### 第七步状态问题修复回执（阶段性）

- 原因 1：`DesignRunContext._overall_run_status()` 只在 `validation == succeeded` 时结束，因此未执行独立 validation 的单相全桥设计被永久显示为 `running`。
- 原因 2：`run_full_pipeline.py` 的单相全桥 selection-only 提前返回路径没有更新 `semiconductor_design`，并且下游未执行阶段保持 `not_started`。
- 修复：增加已有状态体系的 `not_applicable`；单相全桥在器件选择完成后标记 `semiconductor_design = succeeded`，未执行的电容、磁件、损耗、热、效率、硬件概览和验证阶段标记为 `not_applicable`；总状态仅在所有阶段进入终态后为 `succeeded`。
- 未将未执行的 validation 标记为成功，未修改 TCM 诊断 JSON部分。
- 验证：状态/TCM/NPC 定向测试 `25 passed in 65.55s`；`compileall` 和 `git diff --check` 通过。
- 状态修复实现提交：`9a41075`（`fix: close full-bridge TCM design run status`）已推送到 `origin/codex/npc-output-run-isolation-step1`；本阶段文档回执提交将在本次更新后生成。第 7 步整体仍待诊断 JSON部分完成。

## 7. 风险和控制

| 风险 | 控制措施 |
|---|---|
| TCM 频率变化没有传递到损耗 | 逐 operating point 检查 waveform metadata 和事件数据 |
| 事件损耗重复计算 | 对比旧代表性损耗和新事件损耗，确认只保留一套 |
| 半桥模块数量重复计数 | 明确物理模块数、开关位置数和并联数的换算边界 |
| 详细波形与包络时间轴混用 | 每条曲线在测试中检查时间轴长度 |
| 低斜率区域数据截断 | 检查工频末端和 `mixed_mode_clamped` 统计 |
| manifest 被错误标记完成 | 只根据实际阶段结果更新状态，不伪造 validation |
| 修改影响 NPC | 运行 NPC 定向合同测试并检查 diff 范围 |

## 8. 完成和归档规则

第 1 至第 8 步全部完成、验证、commit 和 push 后：

1. 更新本计划最终状态；
2. 更新根目录 `ChangeLog.md`；
3. 将本文件从 `Plan/Active/` 移动到 `Plan/completed/`；
4. 归档动作单独 commit 和 push；
5. 保留最终 TCM 输出目录、测试证据和远端 HEAD，供人工检查。

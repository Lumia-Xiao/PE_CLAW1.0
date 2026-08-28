# AC-DC Efficiency Sweep 修复计划

## 1. 计划目标

修复已迁移工程 `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` 中 AC-DC 拓扑无法执行 `Run Efficiency Sweep` 的问题。

目标是让以下五个 AC-DC 拓扑能够按照各自的硬件模型和损耗模型完成固定硬件效率扫描：

1. `single_phase_diode_bridge_rectifier_capacitor_filter`
2. `single_phase_diode_bridge_rectifier_dc_inductor_filter`
3. `three_phase_diode_bridge_rectifier_capacitor_filter`
4. `single_phase_boost_pfc_diode_bridge`
5. `single_phase_totem_pole_bridgeless_pfc`

效率扫描的原则是复用已经完成设计和器件选择的固定硬件，只改变负载工作点，不在每个负载点重新优化硬件。

## 2. 已确认的问题

### 2.1 桥式整流器选择流程未接入

`src/pe_claw_gui/pipeline/run_full_pipeline.py` 中的 `AC_DC_DIODE_BRIDGE_TOPOLOGIES` 当前为空集合，导致三个二极管桥整流拓扑没有执行桥式整流器选择流程。

同时，效率扫描前置检查要求 `report.bridge_rectifier.selected_candidate` 存在，因此三个普通桥式整流拓扑和 Boost PFC 会在进入负载点计算之前被阻断。

### 2.2 AC-DC 专用效率计算器未被分发

`run_efficiency_sweep_pipeline.py` 已实现以下专用函数：

- `_evaluate_single_phase_boost_pfc_load_point`
- `_evaluate_single_phase_totem_pole_pfc_load_point`
- `_evaluate_ac_dc_load_point`

但主循环当前始终调用通用的 `_evaluate_load_point`，导致 AC-DC 专用桥损耗、PFC 损耗和 DC 电感损耗模型没有真正执行。

### 2.3 现有测试覆盖不足

当前 AC-DC 测试主要验证拓扑注册、默认输入、波形和基础设计流程，没有完整验证 `run_efficiency_sweep()` 的负载点、损耗组成、硬件前置条件和 artifact 输出。

## 3. 总体执行规则

本计划分为 9 步。每一步都必须独立完成、独立验证并独立提交。

每一步严格遵循以下顺序：

1. 检查本步骤涉及的现状和依赖。
2. 修改代码或测试。
3. 执行本步骤规定的测试和运行验证。
4. 检查 `git diff`、`git status` 和变更范围。
5. 执行独立 commit。
6. 执行 `git push`。
7. 记录 commit ID、push 状态和验证结果。
8. 只有本步骤通过后，才能开始下一步。

不得将多个步骤合并为一次提交。不得删除或覆盖与本计划无关的用户已有未跟踪文件。

## 4. 分步安排

### 第一步：建立 AC-DC 效率扫描基线

**目的**

将当前失败状态固化为可重复的测试和诊断结果。

**修改范围**

- 新增 `tests/test_ac_dc_efficiency_sweep.py`。
- 必要时新增仅用于诊断的测试辅助代码，不改变生产逻辑。

**具体内容**

- 对五个 AC-DC 拓扑加载默认输入。
- 执行 `run_full_pipeline`。
- 使用小负载网格，例如 `(0.5, 1.0)`，调用 `run_efficiency_sweep`。
- 记录并断言当前基线行为，包括：
  - candidate 是否生成；
  - waveform 是否生成；
  - bridge rectifier 是否存在；
  - semiconductor 结果是否存在；
  - capacitor 结果是否存在；
  - magnetic 结果是否存在；
  - sweep 点数量；
  - warning 内容；
  - 异常类型。

**验收标准**

- 测试稳定复现当前问题。
- 测试能够区分三个普通桥式拓扑、Boost PFC 和 Totem-Pole PFC 的失败原因。
- 不修改生产代码。

**提交要求**

```text
git commit -m "test: add AC-DC efficiency sweep baseline"
git push
```

### 第二步：恢复桥式整流器选择流程

**目的**

让普通桥式整流拓扑和 Boost PFC 在 Run Design 阶段生成并保存可复用的桥式整流器候选。

**重点文件**

- `src/pe_claw_gui/pipeline/run_full_pipeline.py`
- `src/pe_claw_gui/pipeline/run_bridge_rectifier_pipeline.py`
- `src/pe_claw_gui/pipeline/options.py`
- `src/pe_claw_gui/topology_capabilities.py`
- 必要时涉及桥式整流器模型、候选库和拓扑映射文件

**具体内容**

- 将三个二极管桥整流拓扑接入桥式整流器选择集合。
- 检查 `PipelineOptions` 是否提供桥式整流器选择开关；若参考实现已有该开关，恢复到目标代码。
- 确保 `run_bridge_rectifier_pipeline()` 在设计流程中被调用。
- 确保桥式整流器选择发生在需要它的后续损耗、热和效率阶段之前。
- 检查后续阶段不会清空 `report.bridge_rectifier`。
- 检查 Boost PFC 的输入桥是否复用现有桥式整流器选择器；若当前选择器不支持 Boost PFC，则补充拓扑映射、选择请求和候选数据路径。
- 保证 Totem-Pole 不错误地要求桥式整流器。

**验收标准**

- 三个普通桥式拓扑的 `report.bridge_rectifier.selected_candidate` 非空。
- Boost PFC 的输入桥结果非空。
- 选择结果包含候选、筛选、评分和损耗数据。
- Totem-Pole 仍保持无桥拓扑语义。
- 第一步基线测试中的桥式硬件缺失问题消失。

**提交要求**

```text
git commit -m "fix: connect AC-DC bridge rectifier selection"
git push
```

### 第三步：修复效率扫描拓扑分发

**目的**

让效率扫描主循环真正调用各 AC-DC 拓扑对应的负载点 evaluator。

**重点文件**

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`

**具体内容**

将当前统一调用逻辑改为按拓扑分发：

```text
Boost PFC
    -> _evaluate_single_phase_boost_pfc_load_point

Totem-Pole PFC
    -> _evaluate_single_phase_totem_pole_pfc_load_point

普通 AC-DC 桥式整流
    -> _evaluate_ac_dc_load_point

其他拓扑
    -> _evaluate_load_point
```

检查专用 evaluator 的损耗组成：

- Boost PFC：主开关、独立 Boost 二极管、输入桥、Boost 电感、DC-link 电容。
- Totem-Pole：HF 开关、LF 开关、Boost 电感、DC-link 电容。
- 普通桥式 AC-DC：桥式整流器、DC 侧电感、输出电容。

同时检查 `other_loss_w` 的语义，避免将输入桥损耗错误地隐藏为无意义的其他损耗。

**验收标准**

- 五个拓扑均进入正确 evaluator。
- 专用 warning 和损耗字段符合拓扑类型。
- 不再所有拓扑都调用通用 `_evaluate_load_point`。
- 非 AC-DC 拓扑的现有效率扫描行为不回归。

**提交要求**

```text
git commit -m "fix: dispatch AC-DC efficiency sweep evaluators"
git push
```

### 第四步：统一效率扫描前置条件与 GUI 按钮状态

**目的**

确保后端 `_blocking_warning()`、控制器和 GUI 按钮使用一致的硬件完成条件。

**重点文件**

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`
- `src/pe_claw_gui/app/controllers/efficiency_sweep_controller.py`
- 五个 AC-DC topology form 文件

**具体内容**

普通桥式整流：

```text
candidate
bridge_rectifier.selected_candidate
```

DC 电感滤波：

```text
candidate
bridge_rectifier.selected_candidate
selected AC-DC reactor
```

Boost PFC：

```text
candidate
input bridge
main_switch
rectifier_diode
DC-link capacitor
boost inductor
```

Totem-Pole：

```text
candidate
totem_pole_hf_switch
totem_pole_lf_switch
DC-link capacitor
boost inductor
```

检查并修复：

- GUI 按钮可用条件与后端阻断条件不一致的问题。
- 只存在空的 `DeviceSelectionResult` 时被误认为已有有效器件的问题。
- 设计输入变化后按钮和旧报告状态没有刷新的问题。
- 缺少硬件时后端返回不清晰 warning 的问题。

**验收标准**

- GUI 按钮状态与后端前置条件一致。
- 按钮可用时，后端不会立即返回同一硬件缺失 warning。
- 缺少必要硬件时不会执行不完整的效率计算。
- 设计输入变化后旧 sweep 不会继续被使用。

**提交要求**

```text
git commit -m "fix: align AC-DC efficiency sweep prerequisites"
git push
```

### 第五步：修复 AC-DC 负载点波形与损耗刷新

**目的**

确保每个负载点使用固定硬件生成正确波形，并刷新所有适用的工作点损耗。

**重点文件**

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`
- `src/pe_claw_gui/pipeline/run_capacitor_pipeline.py`
- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/pipeline/run_device_pipeline.py`

**每个负载点的执行顺序**

1. 构造当前负载点 `OperatingPoint`。
2. 复用固定 candidate。
3. 生成当前负载点 waveform。
4. 重新提取 stress。
5. 刷新半导体工作点损耗。
6. 刷新磁性器件工作点损耗。
7. 刷新电容工作点损耗。
8. 计算桥式整流器损耗。
9. 汇总总损耗并计算效率。

**具体检查项**

- 不在每个负载点重新选择硬件。
- 不覆盖固定硬件的 candidate ID、器件 ID、电容料号和磁性设计 ID。
- DC 电感拓扑正确获取 `ac_dc_reactor_result.selected_candidate`。
- 三相拓扑使用正确的三相线电流、DC 输出电流和桥损耗模型。
- Boost PFC 按负载变化计算输入桥损耗。
- 负载点刷新不清空 `bridge_rectifier`、`capacitor`、`magnetic` 或 `device`。
- 波形为空时返回可诊断 warning，不使整个 sweep 崩溃。

**验收标准**

- 所有有效负载点均能生成 waveform。
- 有可用损耗组件时 `efficiency` 非空。
- 效率不出现 NaN、负值或大于 100% 的结果。
- 固定硬件 ID 在整个 sweep 中保持不变。
- 单个负载点异常不会导致结果对象完全丢失，且 warning 能定位负载点。

**提交要求**

```text
git commit -m "fix: refresh AC-DC sweep operating-point losses"
git push
```

### 第六步：修复效率结果、签名和 artifact 输出

**目的**

确保效率结果模型、缓存签名、图表和 GUI 结果页完整反映 AC-DC 损耗。

**重点文件**

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`
- `src/pe_claw_gui/models/efficiency_sweep.py`
- `src/pe_claw_gui/app/result_views/efficiency_view.py`
- 必要时涉及 loss view 和 hardware overview view

**具体内容**

检查并修复：

- `points` 是否完整。
- `peak_efficiency` 是否正确。
- `full_load_efficiency` 是否正确。
- `light_load_efficiency` 是否正确。
- `sweep_basis` 是否说明固定硬件和实际计入的损耗。
- efficiency curve 是否包含有效点。
- loss breakdown 是否包含正确损耗项。
- AC-DC 桥损耗、Boost PFC 输入桥损耗和 DC 电感损耗是否可读。

效率扫描签名至少应包含：

- topology ID；
- candidate 关键参数；
- semiconductor hardware；
- bridge rectifier candidate；
- capacitor part number；
- magnetic design ID；
- load grid；
- operating input；
- power factor（适用时）。

**验收标准**

- 更换桥式整流器、电感或电容后，旧 sweep 不会错误复用。
- efficiency curve 和 loss breakdown artifact 成功生成。
- 结果页不会把桥式整流器损耗错误地显示成普通无定义损耗。
- 缺少可选损耗时结果仍可生成，但有明确提示。

**提交要求**

```text
git commit -m "fix: complete AC-DC efficiency sweep result artifacts"
git push
```

### 第七步：补充五种 AC-DC 的回归测试

**目的**

建立覆盖设计、硬件选择、效率扫描和错误处理的长期回归保护。

**重点文件**

- `tests/test_ac_dc_efficiency_sweep.py`
- `tests/test_phase8_ac_dc_topologies.py`
- 必要时新增 GUI form 测试文件

**测试内容**

- 五种拓扑默认设计。
- 三种普通桥式拓扑的桥式整流器候选生成。
- Boost PFC 输入桥生成。
- Totem-Pole 不生成桥式整流器。
- 普通桥式 AC-DC efficiency sweep。
- DC 电感拓扑 efficiency sweep。
- Boost PFC 完整硬件前置条件。
- Totem-Pole 完整硬件前置条件。
- 缺硬件时的阻断 warning。
- 空 waveform 的处理。
- 固定硬件不被重新选择。
- efficiency artifact 生成。
- sweep signature 缓存和失效。

**最低验收标准**

五个 AC-DC 拓扑均满足：

```text
Run Design 成功
waveform 成功
必要硬件结果存在
Efficiency Sweep 不返回 0 个点
至少一个有效点的 efficiency 非空
```

**提交要求**

```text
git commit -m "test: cover AC-DC efficiency sweep regressions"
git push
```

### 第八步：执行全量回归和 GUI 链路验证

**目的**

确认修复没有破坏 DC-AC、DC-DC、GUI 和打包运行链路。

**验证范围**

- AC-DC 专项测试。
- DC-AC 现有测试。
- DC-DC 现有测试。
- 全量 `pytest`。
- GUI 集成测试。
- 包导入和启动测试。
- 输出目录和 artifact 生成测试。

**GUI 验证流程**

1. 打开 AC-DC 分类页。
2. 依次选择五个拓扑。
3. 执行 `Run Design`。
4. 检查桥式整流器、半导体、电容和磁性结果。
5. 按拓扑需要执行 `Run Capacitor` 和 `Run Magnetics`。
6. 执行 `Run Efficiency Sweep`。
7. 打开 efficiency result 页面。
8. 检查效率曲线、损耗分解、warning 和固定硬件说明。

**验收标准**

- AC-DC 五个拓扑均可完成用户可见的效率扫描流程。
- 原有 DC-AC 和 DC-DC 测试全部通过。
- 全量测试没有新增回归失败。
- GUI 不出现按钮状态、结果页或 artifact 路径异常。

**提交要求**

```text
git commit -m "test: validate AC-DC efficiency sweep end to end"
git push
```

### 第九步：整理修复报告并最终交付

**目的**

整理每一步的证据、提交记录和最终状态，形成可审计交付。

**具体内容**

- 记录修复前后的失败矩阵。
- 记录每个拓扑的硬件前置条件。
- 记录每个拓扑使用的 efficiency evaluator。
- 记录测试命令和测试结果。
- 记录生成的 artifact 文件清单。
- 记录每一步 commit ID 和 push 结果。
- 说明仍属于 first-pass 或尚未支持的功能。
- 检查目标仓库工作树，忽略计划外的用户未跟踪文件，不删除它们。
- 确认远端分支包含全部步骤的提交。

**最终交付标准**

- 五个 AC-DC 拓扑均能执行 `Run Efficiency Sweep`。
- 有效负载点可以计算效率。
- 桥式整流器和 PFC 专用损耗已经进入对应计算路径。
- GUI 前置条件、后端前置条件和结果页一致。
- 每一步都有独立 commit。
- 每一步 commit 都已 push。
- 测试结果、风险和剩余限制均有记录。

## 5. 风险与处理原则

### 5.1 桥式整流器候选数据不足

如果某个拓扑没有满足筛选条件的候选器件，应保留完整 rejection breakdown，并返回明确 warning。不得用无依据的默认器件替代选择结果。

### 5.2 磁性阶段运行时间较长

优先使用小负载网格进行步骤级验证，最终再运行默认完整负载网格。不得为了缩短测试时间而跳过固定硬件一致性检查。

### 5.3 用户已有未跟踪文件

工作区可能包含测试临时文件、输出文件、缓存目录或本地环境。只提交本计划产生的相关文件，不删除、不回滚与本任务无关的已有文件。

### 5.4 两个工作区混淆

本修复计划针对：

```text
C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0
```

不针对仍处于迁移前骨架状态的：

```text
C:\Users\Lumia\Documents\ChatGPT\PE-Claw1.0
```

## 6. 执行结果

状态：`COMPLETED - READY_FOR_USER_ACCEPTANCE`

完成日期：`2026-08-28`

目标分支：`codex/sync-gui-backend-from-2`

最终交付证据：

- `migration/evidence/20260828/step9_ac_dc_efficiency_sweep/ac_dc_efficiency_sweep_final_report.md`
- `migration/evidence/20260828/step9_ac_dc_efficiency_sweep/ac_dc_efficiency_sweep_delivery_manifest.json`

### 6.1 分步提交

| 步骤 | Commit | 提交内容 | Push |
| --- | --- | --- | --- |
| 1 | `931ca386088059900674e47ab828092067599087` | `test: add AC-DC efficiency sweep baseline` | 已推送 |
| 2 | `eb0f7526450c91436e2f6950a8472dab006660cc` | `fix: connect AC-DC bridge rectifier selection` | 已推送 |
| 3 | `bc47deb80c84e8c781c47e2294e0563a9b4dd65f` | `fix: dispatch AC-DC efficiency sweep evaluators` | 已推送 |
| 4 | `f0e9273f1d3da2fe2247b0e0b015b30f824d343f` | `fix: align AC-DC efficiency sweep prerequisites` | 已推送 |
| 5 | `5ac1bb98d059f40b030e3b036cba438887ca22c6` | `fix: refresh AC-DC sweep operating-point losses` | 已推送 |
| 6 | `ce1de2c52f727d316cbd0e0add833670dae6f2c7` | `fix: complete AC-DC efficiency sweep result artifacts` | 已推送 |
| 7 | `2728fd4284200af39ba8adc06163a86bef95ed37` | `test: cover AC-DC efficiency sweep regressions` | 已推送 |
| 8 | `309e65fc0a993d855205d329fe0b5a74209ac0b4` | `test: validate AC-DC efficiency sweep end to end` | 已推送 |
| 9 | 推送后回执更新记录 | `docs: finalize AC-DC efficiency sweep delivery` | 待本步骤 subject commit 推送后确认 |

### 6.2 最终验证

- AC-DC 专项：`27 passed`，包含五拓扑完整硬件设计与效率扫描。
- DC-AC 回归：`64 passed`。
- DC-DC/PSFB 回归：`25 passed`。
- GUI、包导入、Tk 启动与 Windows launcher：`13 passed`。
- 全量 pytest：`338 passed, 1 skipped`，无失败和错误。
- 五个拓扑均生成 `efficiency_curve.png` 和
  `loss_breakdown_stacked.png`。
- Step 1 至 Step 8 均已存在于
  `origin/codex/sync-gui-backend-from-2`。
- 未执行 merge、tag、release 或 `master` push。

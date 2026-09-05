# 单相全桥逆变器精确开关损耗改造计划

## 1. 计划目标

将 `single_phase_full_bridge_inverter` 的开关损耗计算，从当前按工频周期 20 个中点分段、使用正弦电流代表值的准静态模型，改为与三相三电平 NPC 已完成逻辑一致的最小事件级模型：

1. 在一个工频周期内，根据现有单极性 SPWM 开关时序建立统一的开关事件时间轴。
2. 根据实际桥臂电压、输出电压和电感值，连续逐段积分电感电流。
3. 通过周期稳态条件求得工频周期起始电流，不使用工频末端人工线性修正。
4. 在每个开关事件时刻读取有符号的实际电感电流和实际阻断电压。
5. 对每个开通、关断事件调用现有器件开关能量模型，并在工频周期内求和后换算为平均功率。
6. 当开通事件的实际有符号电流为负时，将其判定为体二极管/反并联二极管续流下的软开通，开通损耗为 0；当电流为非负时，按实际电流计算硬开通损耗。

本计划只处理单相全桥的开关损耗计算链路，不扩大到其他拓扑或其他损耗模型。

## 2. 已确认的当前实现

当前主要链路如下：

- `src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/waveform.py`
  - 生成低频正弦波形。
  - 在 `single_phase_inverter_refined_waveforms` 中生成单极性 SPWM 预览门极、桥输出电压和带 PWM 纹波的电感电流。
  - 当前 `_integrate_pwm_inductor_ripple_by_cycle()` 对每个开关周期单独积分，并执行局部漂移/均值处理，不能直接作为跨周期连续实际电流的事件级仿真结果。
- `src/pe_claw_gui/engines/devices/inverter_segmented_loss.py`
  - 当前将工频周期划分为 `DEFAULT_LINE_CYCLE_SEGMENT_COUNT = 20` 个中点分段。
  - `i_turn_on_A` 和 `i_turn_off_A` 使用分段正弦电流的绝对值，既不是逐开关事件电流，也不是开关时刻的实际电流。
  - 当前 ZVS 方向只用于诊断，不会将开通能量置零。
- `src/pe_claw_gui/pipeline/run_device_pipeline.py`
  - 单相全桥 `main_switch` 目前调用 `evaluate_inverter_segmented_switch_loss()`。
  - NPC `npc_outer_switch`、`npc_inner_switch` 已调用事件级损耗替换路径。
- `src/pe_claw_gui/engines/devices/loss_evaluator.py`
  - 已有 `evaluate_npc_switching_event_energy()` 和 `evaluate_npc_switching_events()`。
  - 该路径已经包含：有符号电流软开通判据、实际电流调用厂商 Eon/Eoff 模型、SiC 反向恢复损耗为 0 的行为。
- `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py`
  - 已有统一事件时间轴、连续分段电流积分、周期稳态初值求解、事件时刻电流提取和实际分裂直流母线电压提取逻辑，可作为实现参考。

## 3. 不变约束和非目标

### 3.1 必须保持

- 保持现有用户输入字段、GUI 表单、默认值、输入校验和输入语义，不新增用户输入。
- 保持单相全桥现有拓扑注册、器件角色 `main_switch`、器件选型、并联数和报告主字段兼容性。
- 保持现有器件厂商开关能量模型及其单位换算；实际事件电流作为模型输入。
- 对 SiC 器件保持反向恢复损耗为 0；不得因为移植事件路径重新引入 SiC `Qrr` 损耗。
- 保持 NPC 已完成事件级实现的结果、字段、路径和测试行为不变。
- 保持导通损耗、Eoss、栅极损耗、磁性件损耗、电容损耗、热设计和器件选型逻辑不变，除非为了替换单相全桥开关损耗必须做最小的数据传递调整。
- 测试生成文件只写入工程根目录 `pytest_temp`；运行结果仍使用独立的 `outputs/<运行目录>`，不把生成物加入 Git。

### 3.2 明确不做

- 不增加“采样点数”“死区时间”“软开关阈值”等 GUI 输入。
- 不修改单相全桥的调制策略，不把单极性 SPWM 改成双极性 SPWM。
- 不重新设计 NPC，不把单相全桥逻辑泛化到其他拓扑。
- 不把工频平均电流、正弦峰值电流或 20 段中点电流继续作为开关事件的 Eon/Eoff 输入。
- 不在工频周期末端用人工线性修正强行闭合电流；应通过周期稳态初始值解决首尾连续性。
- 不借助改变断言、放宽损耗公式或删除失败证据来使测试通过。

## 4. 统一术语和计算合同

### 4.1 开关位置

单相全桥采用现有门极命名：

| 桥臂 | 上管 | 下管 |
|---|---|---|
| A 桥臂 | `S1` | `S2` |
| B 桥臂 | `S3` | `S4` |

门极互补关系保持为 `S2 = 1 - S1`、`S4 = 1 - S3`。事件记录必须包含至少：

- `switch_name` 或等价稳定开关标识；
- `event_type`：`turn_on` 或 `turn_off`；
- `event_time_s`；
- `signed_current_A`；
- `absolute_current_A`；
- `blocking_voltage_V`；
- `event_source`；
- `current_source`；
- `blocking_voltage_source`。

### 4.2 电流和开关损耗

对每个事件使用事件时刻的有符号电感电流 `i_event`：

- `turn_on` 且 `i_event < 0`：软开通，`Eon = 0`；
- `turn_on` 且 `i_event >= 0`：硬开通，使用 `abs(i_event)`、事件阻断电压和器件温度调用 Eon 模型；
- `turn_off`：使用 `abs(i_event)`、事件阻断电压和器件温度调用 Eoff 模型；
- SiC 反向恢复：`Err = 0`；其他器件沿用现有非 SiC 行为。

一个工频周期的开关损耗为：

```text
Eline = sum(Eon_event + Eoff_event + Err_event)
Psw   = Eline / Tline
```

若同一器件位置存在并联器件，必须沿用当前 `parallel_count` 合同，将事件电流按并联数分配后再调用器件模型。报告中的 `p_sw_on_W`、`p_sw_off_W`、`p_rr_W` 和 `p_total_W` 的单位及含义保持不变。

## 5. 总体执行规则

本计划分为 7 步。每一步必须独立完成，不能把多个步骤合并为一个提交。每一步严格执行：

1. 阅读本步骤涉及的代码、测试和当前差异。
2. 先明确本步骤的修改文件和验证命令。
3. 只实施本步骤范围内的最小改动。
4. 将测试临时文件写入 `pytest_temp/<步骤目录>`，不得提交生成物。
5. 执行本步骤规定的聚焦测试和必要的静态检查。
6. 检查 `git diff --check`、`git diff`、`git status`，确认没有混入 `outputs/`、`pytest_temp/`、缓存或无关用户文件。
7. 更新本计划的步骤状态、验证结果和 Git 回执。
8. 更新根目录 `ChangeLog.md`，记录日期、目的、文件、行为、测试、分支、commit 和 push 状态。
9. 执行独立 `git commit`，再执行当前工作分支的 `git push`，并核对远端 HEAD。
10. 只有 commit 已成功推送并记录回执后，才能开始下一步。

本计划默认使用当前分支 `codex/npc-output-run-isolation-step1`，不得直接修改或推送 `master`。如果当前分支在执行时发生变化，应先记录实际分支，再按用户指定的远端分支推送。

## 6. 分步实施安排

### 第一步：建立单相全桥开关损耗基线

**目的**

把现有 20 段准静态开关损耗行为、详细 PWM 预览和报告字段固化为可重复基线，为后续逐步替换提供前后对照。

**修改范围**

- 新增单相全桥专用测试文件，例如 `tests/test_single_phase_full_bridge_switching_loss.py`。
- 必要时只增加测试辅助函数；不改生产计算逻辑。

**具体内容**

- 使用现有默认输入构建设计报告，并覆盖至少 CCM 单极性 SPWM 默认路径。
- 记录当前 `evaluate_inverter_segmented_switch_loss()` 的 20 段数量、分段电流、`p_sw_on_W`、`p_sw_off_W`、`p_rr_W`、`p_total_W` 和 ZVS 诊断字段。
- 检查当前详细波形中的 `gate_s1` 至 `gate_s4`、`v_ab_pwm_v`、`inductor_current_a` 和采样参数存在且长度一致。
- 对现有单相全桥器件损耗报告建立断言，明确当前事件级字段尚不存在或尚未接入，避免把基线误当成目标行为。
- 若测试需要写 JSON 或诊断报告，写入 `pytest_temp/single-phase-full-bridge-step1`。

**验收标准**

- 基线测试稳定通过，并且能复现当前使用 20 个工频分段代表电流的行为。
- 基线不要求新硬/软开通计数通过；它只锁定改造前事实。
- 不修改 `src/` 生产代码。

**提交要求**

```text
git commit -m "test: establish single-phase full-bridge switching-loss baseline"
git push
```

### 第二步：建立单相全桥统一开关事件时间轴

**目的**

把现有单极性 SPWM 预览中的四个门极信号转换为严格有序、可审计的开关事件列表，作为后续电流积分和损耗计算的唯一时序输入。

**重点文件**

- `src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/waveform.py`
- 单相全桥相关测试文件

**具体内容**

- 从现有 `mod_a`、`mod_b`、载波比较结果或等价现有门极生成逻辑抽取事件，不新增调制输入。
- 对 `S1`、`S2`、`S3`、`S4` 的相邻门极状态变化生成 `turn_on`/`turn_off` 事件。
- 去除工频周期首尾重复边界事件，或者采用明确的半开区间合同，避免同一物理事件被计算两次。
- 按 `(event_time_s, switch_name)` 稳定排序，记录采样时间轴、开关周期数和事件来源。
- 保证事件时间落在 `[0, Tline)`，并明确周期首尾闭合事件的归属。
- 为 CCM 默认路径建立事件时间轴；如果 TCM 当前没有可复用门极序列，应在 metadata 中明确其边界，不得伪造事件。

**验收标准**

- 默认设计能生成四个开关的事件，事件时间单调且没有重复物理事件。
- 每个开关同时包含开通和关断事件，互补门极不会产生非法同时导通状态。
- 事件数量与现有 SPWM 周期、载波比较结果一致，并能在测试中复核。
- 事件记录包含稳定来源字段，但此步骤暂不要求电流字段已经是最终实际值。

**提交要求**

```text
git commit -m "feat: add single-phase full-bridge switching event timeline"
git push
```

### 第三步：为单相全桥实现连续逐段电感电流积分

**目的**

将现有按周期独立积分并人工去漂移的 PWM 纹波预览，替换或旁路为跨整个工频周期连续的实际电感电流仿真，并通过周期稳态条件确定初始电流。

**重点文件**

- `src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/waveform.py`
- 必要时新增单相全桥内部 helper 模块，但不得复制一套与 NPC 不一致的损耗公式

**具体内容**

- 使用现有输入和候选参数构造：

  ```text
  di/dt = (v_bridge(t) - v_ac(t)) / L
  ```

- `v_bridge(t)` 使用事件时间轴对应的实际桥输出电平及实际 DC-link 电压；`v_ac(t)` 使用当前设计的正弦输出电压。
- 采用梯形积分或与 NPC 等价的确定性分段积分，电流状态跨越所有 PWM 周期连续传递。
- 移植 NPC 的周期 shooting/fixed-point 思路，求满足 `i(Tline) - i(0) = 0` 的初始电流；记录收敛状态、迭代次数、残差和是否饱和。
- 不在工频末端插入人工线性修正；若调制饱和、周期稳态无法收敛或输入边界无效，返回明确的诊断状态。
- 将实际电流数组与事件时间轴放入单相全桥 waveform metadata，保留已有 GUI 所需的低频数组和字段。
- 单相全桥的电流仿真必须继续使用当前用户输入得到的功率因数、负载比例、工频频率、开关频率、直流电压和电感，不引入新的输入字段。

**验收标准**

- 实际电流数组覆盖完整工频周期并跨周期连续。
- 周期稳态残差达到测试设定容差，或明确标记为未收敛而不静默修正。
- 电流包含 PWM 高频纹波，且不是简单的正弦峰值复制。
- 对默认输入，积分结果的平均/基波量仍与现有设计目标处于合理范围内。
- 现有波形和 GUI 合同测试继续通过。

**提交要求**

```text
git commit -m "feat: simulate continuous full-bridge inductor current"
git push
```

### 第四步：提取事件时刻实际电流和实际阻断电压

**目的**

把第三步的连续实际电流与第二步的事件时间轴连接起来，为每一个开关事件生成损耗模型需要的实际运行值。

**具体内容**

- 在事件时刻读取切换前、与 NPC 保持一致定义的事件电流；事件电流必须来自连续分段积分结果，而不是工频平均数组、正弦峰值或 20 段中点值。
- 保留有符号 `signed_current_A`，同时提供 `absolute_current_A`；开通软硬判据只能使用前者。
- 根据事件时刻的 DC-link 状态确定 `blocking_voltage_V`，不能固定为额定峰值；对于现有单相全桥桥臂，使用与该开关位置对应的实际阻断电压。
- 记录 `current_source = exact_segment_integrated_current_at_event` 或等价明确字符串，记录 `blocking_voltage_source` 和事件所在积分区间。
- 对边界事件制定一致的左/右状态规则：电流取事件前的连续值，门极状态取事件后的状态；测试必须锁定该合同。
- 增加单相全桥事件审计所需的硬开通数、软开通数、开通数、关断数、电流范围、电压范围和周期残差。

**验收标准**

- 事件电流同时出现正、负或接近零的实际样本（按默认工况和物理结果判断，不人为伪造）。
- `turn_on` 事件中，负电流事件的 `soft_turn_on` 为真；非负电流事件为硬开通候选。
- 事件阻断电压来自 DC-link 事件时刻值，且来源字段可审计。
- 事件数量、事件时间和电流数组之间可逐项对应。

**提交要求**

```text
git commit -m "feat: attach actual current and voltage to full-bridge events"
git push
```

### 第五步：接入 NPC 兼容的单事件器件损耗模型

**目的**

复用 NPC 已验证的单事件能量模型，将单相全桥事件逐项转换为 Eon、Eoff 和反向恢复能量，避免重新实现一套可能不一致的厂商模型分发。

**重点文件**

- `src/pe_claw_gui/engines/devices/loss_evaluator.py`
- 必要时 `src/pe_claw_gui/engines/devices/inverter_segmented_loss.py`
- 单相全桥事件和损耗测试

**具体内容**

- 优先抽取一个保持现有 NPC 行为不变的通用事件能量 helper；若不需要抽取，则由单相全桥直接调用现有 NPC 事件 API。
- 将单相全桥事件映射为现有 `evaluate_npc_switching_event_energy()` 可接受的字段，或扩展该 API 的拓扑中立字段名；不改变现有 NPC 字段兼容性。
- 开通事件严格执行：负实际电流 `Eon=0`，非负实际电流按 `abs(i_event)` 调用 Eon；关断事件按实际 `abs(i_event)` 调用 Eoff。
- 保持厂商 Eon/Eoff 查表、回退模型、结温输入和并联器件电流分配。
- SiC 器件的 `reverse_recovery_J` 和最终 `p_rr_W` 继续为 0；非 SiC 保持既有规则。
- 计算本工频周期所有事件总能量，再按 `Tline` 换算开关损耗平均值，填回 `DeviceLossResult` 的既有字段。
- 不改变导通损耗、Eoss、栅极损耗的计算；替换开关损耗时必须避免旧的分段开关损耗与新事件损耗叠加。

**验收标准**

- 构造正电流开通、负电流开通、正/负电流关断测试事件，分别验证 Eon/Eoff 行为。
- 低电流和高电流事件的能量不同，证明模型没有退回峰值电流。
- SiC 事件反向恢复为 0。
- 单相全桥事件总能量与报告 `p_sw_on_W`、`p_sw_off_W`、`p_rr_W` 的换算关系闭合。
- NPC 原有事件级合同测试全部通过，且结果不发生无关变化。

**提交要求**

```text
git commit -m "feat: evaluate full-bridge switching loss per event"
git push
```

### 第六步：替换单相全桥调用链并完善报告审计

**目的**

让单相全桥 `main_switch` 真正使用事件级开关损耗，同时保持其他器件损耗和 NPC 分支不变，让 GUI/结构化报告可以解释计算来源。

**重点文件**

- `src/pe_claw_gui/pipeline/run_device_pipeline.py`
- `src/pe_claw_gui/engines/devices/inverter_segmented_loss.py`
- 必要的 report/结果组装文件
- 单相全桥专项合同测试

**具体内容**

- 将单相全桥 `main_switch` 从旧 `evaluate_inverter_segmented_switch_loss()` 分支切换到新的事件级单相全桥损耗入口。
- 清理或保留旧 20 段 helper 时必须有明确用途：如果只用于兼容诊断，不能继续影响 `p_sw_on_W`、`p_sw_off_W`；如果不再被生产路径使用，保留最小兼容接口或安全移除对应调用。
- 只在单相全桥分支新增/写入事件审计 metadata，例如：
  - `event_count`、`turn_on_count`、`turn_off_count`；
  - `hard_turn_on_count`、`soft_turn_on_count`；
  - `event_current_min_A`、`event_current_max_A`；
  - `event_blocking_voltage_min_V`、`event_blocking_voltage_max_V`；
  - `line_frequency_hz`、`switching_frequency_hz`；
  - `periodic_current_residual_A`、`periodic_solver_converged`；
  - `event_current_source`、`event_voltage_source`。
- GUI 不新增输入控件；已有损耗视图继续读取既有 `DeviceLossResult` 字段，必要的解释只通过已有 notes/metadata 传递。
- 检查运行点刷新和 efficiency sweep 是否复用同一事件级 waveform/硬件链路，避免固定硬件刷新时重新退回旧 20 段模型。

**验收标准**

- 默认单相全桥设计报告的开关损耗来自事件总能量/Tline，而不是旧 20 段平均值。
- 报告中 `p_total_W` 只包含一次开关损耗；没有旧模型与新模型重复相加。
- 单相全桥运行点刷新、效率扫描和 GUI 结果读取不破坏现有字段。
- NPC、其他 DC-AC 拓扑和其他损耗类别的调用路径未被改变。

**提交要求**

```text
git commit -m "feat: route full-bridge device loss through event model"
git push
```

### 第七步：单相全桥专项验收与 NPC 回归

**目的**

在不扩大到全工程回归的前提下，完成单相全桥事件级开关损耗的闭环验收，并证明 NPC 已完成逻辑未被破坏。

**具体内容**

- 补充或完善单相全桥专项测试，覆盖：
  - 默认 CCM 单极性 SPWM 设计和波形生成；
  - 四个开关均有开通/关断事件；
  - 事件时间单调、边界无重复；
  - 事件电流来自连续实际积分；
  - 正电流开通为硬开通并计算 Eon；
  - 负电流开通为软开通且 Eon 为 0；
  - 关断使用事件实际电流；
  - 事件阻断电压与 DC-link 事件时刻值关联；
  - SiC 反向恢复为 0；
  - 工频周期能量与平均功率闭合；
  - 周期稳态残差和电流范围合理；
  - 运行点刷新保持选定开关硬件不变。
- 运行单相全桥最小设计链路和必要的固定硬件 operating-point refresh，不运行无关拓扑的完整回归。
- 运行 NPC 专项事件合同测试，至少确认事件数量、软开通判据、事件电流来源、阻断电压来源和报告功率换算仍通过。
- 执行 `python -m pytest -q` 的单相全桥/NPC 指定测试集合、`python -m compileall -q src tests` 或等价 `py_compile` 检查，以及 `git diff --check`。
- 需要性能观察时，只测单个默认单相全桥波形/损耗运行点；不得为了实时刷新而在本计划中引入新的采样输入或扩大性能重构。
- 将测试输出放入 `pytest_temp/single-phase-full-bridge-step7`，检查 `outputs` 和 `pytest_temp` 不被 Git 跟踪。

**验收标准**

- 单相全桥专项测试全部通过，且事件级开关损耗审计字段完整。
- NPC 专项测试全部通过，未出现行为回归。
- 计算中不存在以工频正弦峰值替代事件电流的生产路径。
- 没有新增用户输入，没有 `other` 损耗或其他未请求损耗被重新引入。
- 计划 1 至 7 步均有独立 commit、push 和验证回执。

**提交要求**

```text
git commit -m "test: close single-phase full-bridge switching-loss plan"
git push
```

## 7. 计划状态和证据记录

| 步骤 | 状态 | 实现 commit | ChangeLog 回执 commit | 远端 push | 验证证据 |
|---|---|---|---|---|---|
| 1 | 已完成 | `18b04258a7040737a048e72f4c9c2542316769a6` | 待本回执提交 | 已推送；远端 HEAD=`18b04258a7040737a048e72f4c9c2542316769a6` | 新增基线+既有合同 `14 passed`；`compileall` 通过；`git diff --check` 通过 |
| 2 | 待执行 | - | - | - | - |
| 3 | 待执行 | - | - | - | - |
| 4 | 待执行 | - | - | - | - |
| 5 | 待执行 | - | - | - | - |
| 6 | 待执行 | - | - | - | - |
| 7 | 待执行 | - | - | - | - |

每一步完成后，必须把该行的状态改为“已完成”，填写实际 commit、push 结果和测试证据；在远端 push 验证之前不得标记为已完成。计划完成后将本文件从 `Plan/Active` 移动到 `Plan/completed`，移动动作也必须单独记录并提交。

## 8. 风险和处理边界

- **现有 refined waveform 不是连续周期电流**：第三步必须建立独立的连续积分结果，不能直接把旧的局部去漂移数组当成事件电流。
- **事件边界落在离散采样点之间**：应使用统一时间轴和确定性插值/分段积分，不能把最近的工频中点当作事件值。
- **电流周期稳态不收敛**：保留诊断和残差，检查调制饱和、输入参数和电压限幅根因；不得人工修正首尾电流掩盖问题。
- **开通极性误判**：软硬判据必须针对 `turn_on` 的有符号事件电流，不能使用绝对值或电流平均值。
- **损耗重复叠加**：替换调用链后必须从总损耗中扣除旧开关损耗，再加上事件级开关损耗；导通、Eoss、栅极和其他现有损耗只保留一次。
- **NPC 回归**：任何通用 helper 抽取都必须先锁定 NPC 现有测试，再切换单相全桥调用，保证 NPC 的事件语义和结果不变。

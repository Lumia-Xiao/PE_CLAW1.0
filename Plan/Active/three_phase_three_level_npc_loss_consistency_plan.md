# 三相三电平 NPC 损耗一致性修复计划

## 目标

修复最近 NPC 设计中发现的以下问题：

1. Efficiency Sweep 中半导体损耗在不同负载下保持不变。
2. 器件页、损耗页和硬件概览页的损耗数据口径不一致。
3. 半导体组级损耗与内管、外管角色级损耗存在数量倍增错误。
4. 当前工况损耗没有稳定传递到效率扫描和硬件概览。
5. 开关频率审计字段为空，器件类型相关的反向恢复损耗说明不准确。
6. NPC 设计完成后 manifest 仍可能显示为 `running` 或 `not_started`。

## 范围约束

- 只修改三相三电平 NPC 拓扑相关的损耗刷新、汇总、页面显示和结果状态链路。
- 不新增任何用户输入项，继续使用现有用户输入。
- 保留现有逐开关事件、实际开关时刻电流、实际阻断电压和软开通判定模型。
- 不扩大为全拓扑回归；验证以 NPC 定向测试为主。
- 不改变器件选型规则，效率扫描只刷新当前工况损耗，不重新选型。
- 不使用历史输出作为当前设计数据来源。

## 每步共同要求

每完成一个步骤，都必须：

1. 运行该步骤对应的 NPC 定向测试或检查。
2. 检查 `outputs` 下是否生成独立的本次结果目录。
3. 检查 `pytest_temp` 下的测试临时文件是否按当前规则生成。
4. 查看 `git diff` 和 `git status`，确认没有引入无关修改。
5. 创建一个独立 commit。
6. push 当前远端分支。

---

## 第 1 步：建立损耗数据契约和回归基线

### 修改内容

1. 梳理并在相关模型、函数注释或测试中固定以下损耗口径：
   - `DeviceLossResult.p_total_W`：单个物理器件的损耗。
   - 角色总损耗：该角色所有实际物理位置的损耗。
   - 方案总损耗：active semiconductor scheme 中所有角色总损耗之和。
   - `semiconductor_loss_w`：效率扫描中整个 NPC 功率级的半导体总损耗。
2. 确认 NPC 的物理数量：
   - 外管开关位置数为 6。
   - 内管开关位置数为 6。
   - 钳位二极管位置数为 6；若当前器件模型不单独选择钳位二极管，必须明确其损耗是否为 0，而不能重复计数。
3. 增加或完善最小基线检查，记录 5%、50%、100% 负载下：
   - 实际事件电流范围。
   - `current_operating_losses` 是否存在。
   - 内管、外管角色数量和损耗。
   - 半导体总损耗、总损耗和效率。
4. 基线检查不得改变现有计算结果，只用于锁定问题和后续比较。

### 重点位置

- `src/pe_claw_gui/models/device_result.py`
- `src/pe_claw_gui/models/device_loss.py`
- `src/pe_claw_gui/pipeline/run_device_pipeline.py`
- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`

### 验收条件

- 能明确区分单器件、角色总量、方案总量三种口径。
- 基线结果可以证明当前问题确实存在。
- 不改变用户输入和器件选型。

### 执行回执（2026-09-07）

- 状态：已完成。
- 新增 `scripts/record_npc_loss_consistency_baseline.py` 和 `tests/test_npc_loss_consistency_step1.py`。
- 补充 `DeviceLossResult`、角色结果和方案结果的损耗口径注释。
- NPC 定向验证：`23 passed`；基线输出：`pytest_temp/npc-loss-consistency-step1/baseline.json`。
- 本步骤未修改损耗计算逻辑、器件选型规则或用户输入。

## 第 2 步：修复 NPC 当前工况损耗刷新

### 修改内容

1. 检查 `run_device_operating_point_refresh` 对 NPC 的执行前提：candidate、stress、waveform 和 active scheme 必须来自当前报告。
2. 当前工况存在有效波形时，必须调用现有 `build_current_operating_switch_stress_case`，并生成 NPC 内管、外管角色的当前损耗结果。
3. 当前工况刷新使用已选器件，不允许触发新的器件选型。
4. 保证当前工况结果写入：
   - `device.current_operating_losses`
   - `current_operating_summary`
   - `current_operating_point_key`
5. 如果刷新失败或角色缺失，必须保留明确的失败原因或 warning；不能清空后无提示地回退到设计点损耗。
6. 检查 `_apply_design_sink_reference` 只复用设计点散热器参数，不覆盖当前工况的电气损耗字段。

### 重点位置

- `src/pe_claw_gui/pipeline/run_device_pipeline.py:2193-2310`
- `src/pe_claw_gui/pipeline/run_device_pipeline.py:2815-2838`
- `src/pe_claw_gui/engines/devices/stress_adapter.py:961-987`
- `src/pe_claw_gui/engines/devices/stress_adapter.py:396-469`

### 验收条件

- 5%、50%、100% 负载点均能得到当前工况损耗。
- 当前工况损耗中内管和外管角色均存在。
- 当前损耗不被设计点散热参数替换为设计点电气损耗。

### 执行回执（2026-09-07）

- 状态：已完成。
- NPC 当前工况刷新现在要求匹配的当前波形、开关事件、active scheme 和全部三类已选器件。
- 缺失角色、波形或评估异常会清空当前工况损耗并记录明确 warning，不再静默回退到设计点损耗。
- NPC 定向验证：`24 passed`；未修改用户输入和器件选型规则。

## 第 3 步：禁止效率扫描静默回退到固定设计点损耗

### 修改内容

1. NPC 效率扫描每个负载点都使用该负载点刚刚刷新得到的 `current_operating_losses`。
2. 修改半导体损耗读取逻辑，使 NPC 在当前工况刷新失败时：
   - 当前点标记为损耗不可用，或
   - 输出明确 warning 并阻止该点被当成正常有效点。
3. 不允许使用 `active_scheme.total_scheme_loss_w` 作为 NPC 当前负载点的静默替代值。
4. 将当前工况的角色损耗按物理数量汇总，不能直接使用设计点方案总损耗。
5. 保留现有逐事件开关损耗计算，不重新引入峰值电流假设。

### 重点位置

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:298-390`
- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:826-841`
- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:886-960`

### 验收条件

- `semiconductor_loss_w` 不再在全部负载点完全相同。
- 事件电流增大时，导通损耗和硬开关损耗能够反映到半导体总损耗。
- 当前工况刷新失败时不会生成看似有效的固定损耗结果。

### 执行回执（2026-09-07）

- 状态：已完成。
- NPC 半导体损耗读取现在只接受当前工况且三类角色完整的 `current_operating_losses`。
- 刷新失败时负载点的半导体损耗、总损耗和效率均不可用，并明确提示没有使用设计点半导体损耗。
- NPC 定向验证：`26 passed`；其他拓扑的既有回退逻辑保持不变。

## 第 4 步：修复效率扫描结果到最终报告的传递

### 修改内容

1. 检查效率扫描过程中每个负载点的临时报告与最终 `EfficiencySweepResult` 的关系。
2. 扫描完成后，保留满载点或当前用户工况的刷新后报告快照，至少包括：
   - 当前波形。
   - 当前 stress。
   - 当前器件损耗。
   - 当前磁性损耗。
   - 当前电容损耗。
3. 效率扫描控制器生成硬件概览时，必须使用同一份刷新后报告，而不是原始设计报告。
4. 不改变选中的器件、磁芯、电容和散热器，只更新 operating-point dependent 数据。
5. 确认 GUI 状态仓库保存的是最终一致的报告。

### 重点位置

- `src/pe_claw_gui/app/controllers/efficiency_sweep_controller.py:24-96`
- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:94-148`
- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:255-390`

### 验收条件

- Efficiency 页面和硬件概览使用同一个最终报告状态。
- 运行 Efficiency Sweep 后，器件页不再回到旧的设计点损耗。
- 已选硬件 ID 不发生变化。

### 执行回执（2026-09-07）

- 状态：已完成。
- NPC Efficiency Sweep 完成后，控制器会刷新最终用户工况报告，并用同一份报告生成硬件概览和更新 GUI 状态。
- 验证了当前波形、三类当前器件损耗、run context 和 candidate 在最终报告链路中保持一致。
- NPC 定向验证：`26 passed`；未改变器件、磁件、电容或散热器选型。

## 第 5 步：统一 NPC 半导体数量和损耗聚合

### 修改内容

1. 明确每个 `DeviceLossResult` 首先代表单个物理器件损耗。
2. 对每个 NPC 角色只在统一的汇总层乘一次物理数量：
   - 外管：6 个位置。
   - 内管：6 个位置。
   - 钳位二极管：按实际是否有独立器件模型决定，不能把位置数和物理器件数重复相乘。
3. 修复 `SemiconductorSchemeResult.total_scheme_loss_w` 与 `SemiconductorRoleSchemeResult.total_loss_w` 的口径，使方案总损耗等于各角色总损耗之和。
4. 修复硬件概览组级和子项级损耗：
   - 组级损耗等于所有角色总损耗之和。
   - 子项损耗等于对应角色总损耗。
   - 不允许出现子项合计为组级损耗 6 倍的情况。
5. 几何数量、硬件数量和损耗数量分别使用清晰的字段，不通过隐含乘法互相转换。

### 重点位置

- `src/pe_claw_gui/pipeline/run_device_pipeline.py:1585-1632`
- `src/pe_claw_gui/pipeline/run_device_pipeline.py:1734-1763`
- `src/pe_claw_gui/engines/hardware_overview.py:709-784`
- `src/pe_claw_gui/engines/hardware_overview.py:1906-2006`
- `src/pe_claw_gui/models/device_result.py:11-71`

### 验收条件

- `group_loss == outer_role_loss + inner_role_loss + clamp_role_loss`。
- 组级损耗与子项损耗单位和数量口径一致。
- 不再出现最新 case 中的 `9.8854 W` 对 `59.3125 W` 的 6 倍差异。

### 执行回执（2026-09-07）

- 状态：已完成。
- 新增共享 NPC 损耗聚合契约，统一单器件、角色总量和方案总量的数量乘法。
- Efficiency Sweep、方案结果和硬件概览均使用同一套角色总损耗；真实 payload 验证组级损耗等于三类角色子项之和。
- NPC 定向验证：`27 passed`；未修改器件选型和开关事件损耗模型。

## 第 6 步：统一器件页、损耗页和硬件概览页

### 修改内容

1. 三个页面统一使用相同的损耗来源优先级：
   - 当前工况损耗存在时，统一使用当前工况损耗。
   - 当前工况损耗不存在时，统一使用设计点损耗，并明确标记 `design point`。
2. 器件页同时显示但明确区分：
   - 单个器件损耗。
   - 角色总损耗。
   - 半导体方案总损耗。
3. 损耗页的总损耗、角色损耗和明细字段使用同一套物理数量乘法。
4. 硬件概览页的 `loss_basis_label`、子项 metadata 和 notes 必须反映真实数据来源。
5. 页面不得在没有 warning 的情况下混合显示设计点器件损耗和当前工况总损耗。

### 重点位置

- `src/pe_claw_gui/app/result_views/device_view.py:223-253`
- `src/pe_claw_gui/app/result_views/loss_view.py:78-113`
- `src/pe_claw_gui/app/result_views/loss_view.py:373-403`
- `src/pe_claw_gui/engines/hardware_overview.py:1922-1959`

### 验收条件

- 三个页面显示的 NPC 半导体总损耗一致。
- 页面中能明确看出当前工况或设计点口径。
- 内管、外管的角色损耗与组级损耗可以互相核对。

## 第 7 步：修复开关频率、反向恢复说明和 manifest 状态

### 修改内容

1. 开关频率审计字段按以下优先级读取现有数据：
   - waveform metadata。
   - candidate metadata。
   - candidate 的 `fs_hz`。
2. 对本次输入应输出 `switching_frequency_Hz = 48000`，不能为 `null`。
3. 不再用固定的 `sic_reverse_recovery_loss_W` 字段描述所有器件。
4. 根据实际器件类型输出反向恢复损耗状态：
   - SiC 器件可明确为 0。
   - Infineon MOSFET with Diode 必须区分其 XML Eon/Eoff 模型是否已经包含相关效应，不能错误标记为 SiC。
5. 检查 NPC 完整设计结束时的 manifest：
   - 总状态不能停留在 `running`。
   - 已完成的 semiconductor、loss、thermal、efficiency_sweep 和 hardware_overview 状态要正确反映。
   - artifact group 和状态不能显示为 `not_started` 或空值。
6. manifest 修复必须遵循现有 run-scoped 输出目录规则。

### 重点位置

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py:886-960`
- `src/pe_claw_gui/engines/devices/loss_evaluator.py:141-150`
- `src/pe_claw_gui/engines/devices/loss_evaluator.py:285-313`
- `src/pe_claw_gui/pipeline/run_manifest_pipeline.py`
- `src/pe_claw_gui/app/controllers/efficiency_sweep_controller.py:73-96`

### 验收条件

- 审计输出包含正确的开关频率。
- 反向恢复字段与器件类型一致，说明不误导。
- manifest 与实际生成阶段和 artifact 一致。

## 第 8 步：NPC 定向验证和结果验收

### 修改内容

只对三相三电平 NPC 拓扑执行定向验证，不扩大到全拓扑回归：

1. 使用现有用户输入运行一次 NPC 设计。
2. 检查 5%、50%、100% 负载点。
3. 检查效率扫描 CSV：
   - 半导体损耗不再恒定。
   - 磁性损耗和电容损耗仍然可用。
   - 总损耗等于各损耗项之和。
4. 检查开关事件：
   - 使用实际事件电流。
   - 负电流开通为软开通，开通损耗为 0。
   - 正电流开通使用 Eon 模型。
   - 关断损耗使用实际关断电流。
5. 检查内管、外管和钳位二极管的数量与损耗汇总。
6. 检查器件页、损耗页和硬件概览页的一致性。
7. 检查 `switching_frequency_Hz`、manifest、输出目录和 `pytest_temp`。
8. 保存本次验证结果，并记录剩余限制，例如死区、Coss、寄生参数和中点电压动态仍未建模的情况。

### 验收条件

- NPC 设计结果可以通过电流、损耗、数量、页面和状态五个维度的核对。
- 不存在固定设计点损耗被错误用于全负载扫描的情况。
- 不存在组级与角色级损耗的数量倍增错误。
- 结果目录、测试临时文件和 Git 提交记录符合工程规则。

## 完成判定

全部 8 步完成，并且每一步都已完成 NPC 定向验证、独立 commit 和 push 后，才将本计划移动到 `Plan/completed`。

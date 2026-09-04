# 三相三电平 NPC 精确开关损耗最小实现计划

## 1. 目标与边界

- 状态：Active
- 目标拓扑：三相三电平二极管箝位 NPC 逆变器
- 拓扑标识：`three_phase_three_level_npc_inverter`
- 目标：基于一个工频周期内每个实际开关时刻的电感电流和阻断电压，准确汇总 NPC 的开通、关断开关损耗。
- 本计划只做保证开关损耗计算准确所需的最小修改，不扩展其他热设计、电容设计、拓扑器件选型或控制功能。

## 2. 不变的用户输入约束

GUI 和设计请求必须保持原有用户输入，不新增任何输入字段、配置项或额外交互。开关频率必须继续从原有用户输入 `fsw_hz` 获取，不允许引入第二个开关频率输入。

NPC 现有输入字段保持为：

- `vdc_nom`
- `vac_ll_rms`
- `f_line_hz`
- `fsw_hz`
- `pout_w`
- `power_factor`
- `inductor_current_ripple_ratio`
- `dc_link_voltage_ripple_ratio`
- `ambient_temp_c`
- `target_junction_temp_c`

## 3. 实施与提交规则

本计划包含 6 个实施步骤，必须按顺序执行。每个步骤均必须完成以下闭环后，才能勾选完成并开始下一步：

1. 修改代码和对应测试。
2. 运行该步骤的专项验证及必要的回归测试。
3. 更新本计划的步骤状态、验证结果、commit 和 push 记录。
4. 更新根目录 `ChangeLog.md`。
5. 单独执行 `git commit`，不得把多个步骤合并为一个提交。
6. 单独执行 `git push` 到当前远端跟踪分支，并确认远端包含该 commit。

不得提交 `outputs/`、`pytest_temp/`、`__pycache__/`、`*.pyc` 或其他生成文件。已有设计结果必须保留。

## 4. 六个实施步骤

### 步骤 1：建立连续的工频周期电流波形

状态：已完成

修改文件：

- `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py`
- 与波形契约直接相关的 NPC 测试文件

修改内容：

1. 继续使用原有输入和原有 `fsw_hz`，生成一个完整工频周期的三相电感电流以及 12 路门极波形。
2. 修正 `_integrate_phase_current_by_cycle()`，不允许每个 PWM 周期都重新用基波电流锚定，从而丢失开关纹波和开关时刻电流信息。
3. 在整个工频周期上连续积分电感电流；必要时只做明确记录的周期稳态修正，不能用峰值电流替代采样波形。
4. 保留三相电流、时间轴、12 路门极波形和既有统计字段，保证旧 GUI 和报告字段兼容。
5. 在 waveform metadata 中记录采样周期、积分方式和周期修正量，便于结果审计。

验收条件：

- 时间轴覆盖恰好一个工频周期。
- 电流波形在 PWM 周期之间连续，且保留开关纹波。
- 三相电流和既有门极波形字段仍可被现有 GUI、stress 和报告流程读取。
- 测试证明修改没有新增用户输入。

### 步骤 2：提取实际的 NPC 开关事件

状态：已完成

修改文件：

- `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py`
- NPC 波形和事件提取测试

修改内容：

1. 遍历三相 12 路有源开关门极波形，检测 `0 -> 1` 开通和 `1 -> 0` 关断边沿。
2. 对每个边沿在线性区间内插值，取得实际事件时间，而不是直接使用采样点时间。
3. 在同一事件时间插值三相电感电流，保留有符号电流 `signed_current_A`，并同时记录 `absolute_current_A`。
4. 根据 NPC 开关位置和当时的直流母线状态记录该事件的阻断电压 `blocking_voltage_V`，使其随实际母线电压变化。
5. 每个事件至少写入 `phase`、`switch_index`、`role`、`event_type`、`event_time_s`、`signed_current_A`、`absolute_current_A` 和 `blocking_voltage_V`。
6. 将完整事件列表写入 `waveform.metadata["three_phase_npc_switching_events"]`，不通过峰值电流字段重建事件。

验收条件：

- 12 个物理开关的位置和角色可区分，事件数量与门极边沿数量一致。
- 事件电流包含正负号，且同一工频周期内不是全部固定为峰值。
- 事件时间落在工频周期内并按时间排序。
- 阻断电压不是无条件固定常数，计算依据与直流电压相关。

### 步骤 3：实现事件级器件开关能量模型

状态：已完成

修改文件：

- `src/pe_claw_gui/engines/devices/loss_evaluator.py`
- 事件级开关能量测试

修改内容：

1. 增加只供 NPC 调用的事件级开关能量计算入口，输入事件实际电流、阻断电压、结温以及器件已有的开通/关断参数。
2. 开通事件使用有符号实际电流判断软硬开通：
   - `signed_current_A < 0`：认为体二极管或反向通道先导通，`Eon = 0`。
   - `signed_current_A >= 0`：按 `Eon(Ievent, Vblock, Tj, Rg_on)` 计算硬开通能量。
3. 关断事件使用实际事件电流的绝对值，按 `Eoff(|Ievent|, Vblock, Tj, Rg_off)` 计算，不能使用工频峰值替代。
4. SiC 二极管的反向恢复损耗固定为 0；二极管正向导通损耗保持现有模型。
5. 非 NPC 拓扑继续使用现有逻辑，避免本步骤改变其他拓扑行为。
6. 对并联器件，按并联数量分摊事件电流后调用器件模型，并保留数量语义供上层汇总。

验收条件：

- 负电流开通事件的 `Eon` 严格为 0。
- 正电流开通事件确实调用器件 Eon 模型。
- 关断能量使用事件实际电流和实际阻断电压。
- SiC 反向恢复项为 0，既有导通损耗仍存在。
- 峰值电流不再作为 NPC 所有事件的统一开关电流。

### 步骤 4：按工频周期汇总 NPC 开关损耗

状态：已完成

修改文件：

- `src/pe_claw_gui/engines/devices/stress_adapter.py`
- `src/pe_claw_gui/pipeline/run_device_pipeline.py`
- NPC stress、device loss 和汇总测试

修改内容：

1. 将事件级 Eon/Eoff 列表从波形和器件模型传递到 NPC 应力及器件损耗汇总层。
2. 使用原有输入的 `f_line_hz` 计算工频周期 `Tline = 1 / f_line_hz`。
3. 按 `Psw_on = sum(Eon_events) / Tline`、`Psw_off = sum(Eoff_events) / Tline`、`Psw = Psw_on + Psw_off` 汇总，不再直接用 `E * fsw` 乘峰值代表值。
4. 分别统计 `npc_outer_switch`、`npc_inner_switch` 和 `npc_clamp_diode`，整机事件列表已包含所有物理位置，不再额外乘 6。
5. 只替换 NPC 的事件级开通、关断和 SiC 反向恢复项；原有导通、Eoss 和栅极损耗暂时保持。
6. 保持器件明细、器件组和上层报告使用相同的汇总结果及单位。

验收条件：

- NPC 开关损耗等于一个工频周期内全部事件能量除以工频周期。
- 外管、内管、箝位二极管的损耗没有重复计数或漏计数。
- 改变 `fsw_hz`、负载或功率因数会通过事件数量/事件电流影响结果，且 `fsw_hz` 来自原有输入。
- 现有其他拓扑损耗测试保持通过。

### 步骤 5：接入运行点、效率扫描和报告

状态：已完成

修改文件：

- `src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py`
- `src/pe_claw_gui/reports/structured_output.py`
- `src/pe_claw_gui/app/result_views/loss_view.py`
- NPC 效率扫描、报告和 GUI 测试

修改内容：

1. 设计点和每个效率扫描负载点都执行同一流程：当前运行点 -> 三相连续电流波形 -> NPC 开关事件 -> 事件电流/电压 -> Eon/Eoff -> 工频平均损耗。
2. PF 扫描复用事件级流程，不复用设计点的固定峰值电流或固定半导体开关损耗。
3. 将开关损耗分项、事件统计、工频平均值和计算来源写入已有结构化报告字段；只有确有需要的审计数据写入当前运行目录的 `semiconductor_design/npc_switching_events.csv`。
4. GUI 损耗视图读取当前运行上下文中的 NPC 结果，保持原有输入窗口和已有显示交互，不新增输入控件。
5. 确保器件明细、效率 CSV、损耗 breakdown 和 GUI 显示来自同一个事件级汇总结果。

验收条件：

- 负载扫描和 PF 扫描的每个点都重新计算实际事件损耗。
- GUI、效率 CSV 和器件损耗明细中的 NPC 开关损耗一致。
- 报告能追溯事件数、事件电流范围、阻断电压和工频平均公式。
- 不出现新增用户输入字段或第二套开关频率来源。

执行结果：

- `EfficiencySweepPoint` 增加可选的 `switching_loss_audit` 字段，负载扫描和 PF 扫描的每个 NPC 运行点均从当前波形事件生成摘要。
- 效率 CSV 增加 `switching_loss_audit` 列；结构化报告增加 `loss.npc_switching` 以及 `efficiency_sweep.points/pf_points` 中的事件审计摘要。
- GUI 损耗视图更新为工频事件平均依据，明确负电流开通 `Eon=0`、实际事件电流/阻断电压和 SiC 反向恢复为零。
- 未增加任何 GUI 输入字段，`fsw_hz` 仍来自原有用户输入。

验证：NPC 专项运行点与扫描测试 `16 passed`；结构化输出和 GUI 效率回归 `6 passed`；运行级验证确认 2 个负载点和 20 个 PF 点均重新生成 4800 个事件并随 PF 改变事件电流范围；`compileall` 和 `git diff --check` 通过。

commit：待记录

push：待记录

### 步骤 6：回归验证并完成计划收口

状态：待执行

修改文件：

- `tests/test_npc_switching_loss.py`
- `tests/test_dc_ac_three_phase_three_level_npc_contract.py`
- `tests/test_dc_ac_efficiency_sweep.py`
- 必要的最终验证记录和本计划

修改内容：

1. 覆盖一个工频周期内 12 个开关位置的事件提取、门极边沿一致性和事件电流非峰值化。
2. 覆盖负电流开通 `Eon == 0`、正电流开通调用 Eon、关断使用实际事件电流、SiC 反向恢复为 0。
3. 覆盖 `Psw = sum(Eevent) / Tline`、外管/内管/箝位二极管不重复计数，以及负载/PF 改变对事件电流和损耗的影响。
4. 运行 NPC 专项测试、受影响 DC-AC 回归、报告/效率扫描测试和全量回归。
5. 完成 `compileall`、`git diff --check`、工作区生成文件检查，并核对没有提交 `outputs/`、`pytest_temp/` 或缓存。
6. 记录最终验证结果、所有步骤的 commit/push 回执，并将计划标记为完成；若有剩余建模限制，明确列出而不隐藏。

验收条件：

- 所有必须测试通过，失败或环境限制有明确记录。
- 六个步骤均有独立 commit 和 push 记录。
- 计算结果、报告和 GUI 行为满足本计划边界。
- 计划与 `ChangeLog.md` 状态一致。

## 5. 完成定义

计划完成必须同时满足：NPC 开关损耗基于工频周期内的实际开关事件电流和阻断电压；负电流开通按软开关处理；SiC 反向恢复损耗为零；开关频率来自原有用户输入；GUI 没有新增输入；效率扫描和报告复用同一计算链；所有步骤均已验证、独立 commit 并 push。

## 6. 执行记录

### 计划切换

- 状态：已完成
- 旧计划：`Plan/Active/three_phase_three_level_npc_revision_plan.md`
- 新计划：`Plan/Active/three_phase_three_level_npc_switching_loss_plan.md`
- 说明：旧的九步综合整改计划由本最小实现计划替代；不删除任何输出结果。
- commit：`efd7bcd` (`docs: define NPC switching loss minimum plan`)
- push：已成功推送至 `origin/codex/npc-output-run-isolation-step1`，远端 HEAD 已核对为 `efd7bcdca909933dc902311ef4c109993bde9b6f`

### 步骤 1 至步骤 6

| 步骤 | 状态 | 验证 | commit | push |
|---|---|---|---|---|
| 1 | 已完成 | NPC 契约 11 passed；受影响 DC-AC 回归 20 passed；compileall 和 `git diff --check` 通过 | `12f1180` (`fix: integrate NPC phase current continuously`) | 已成功推送，远端 HEAD：`12f1180da9bde5193ad8a944bc0f8fc00497a314` |
| 2 | 已完成 | NPC 契约 12 passed；受影响 DC-AC 回归 21 passed；compileall 和 `git diff --check` 通过 | `0334142` (`feat: extract NPC switching events`) | 已成功推送，远端 HEAD：`0334142b64030c9e472c12cadff6713e7161d6e5` |
| 3 | 已完成 | 相关专项与器件回归 27 passed；受影响 DC-AC/器件回归 38 passed；compileall 和 `git diff --check` 通过 | `0a63c21` (`feat: add NPC event switching energy model`) | 已成功推送，远端 HEAD：`0a63c2187133b6177be27941fbb1ce11f7e4c54e` |
| 4 | 已完成 | NPC 契约 15 passed；其余受影响 DC-AC/器件回归 24 passed；此前完整效率扫描回归 55 passed；公式级事件汇总断言通过；compileall 和 `git diff --check` 通过 | `8002624` (`fix: aggregate NPC switching loss by line cycle`) | 已成功推送，远端 HEAD：`80026241d31fe5a3129fdfab9fad5200428fe324` |
| 5 | 已完成 | NPC 扫描/报告专项 16 passed；结构化输出和 GUI 效率回归 6 passed；运行级负载 2 点、PF 20 点均生成事件审计；compileall 和 `git diff --check` 通过 | 待记录 | 待记录 |
| 6 | 待执行 | 待执行 | 待记录 | 待记录 |

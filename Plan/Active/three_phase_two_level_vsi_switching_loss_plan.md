# 三相两电平 VSI 逐事件开关损耗修正计划

## 1. 任务目标

将三相两电平电压源逆变器（three-phase two-level VSI）的开关损耗计算，从当前基于代表性电流/频率的损耗模型，修正为类似三相三电平 NPC 的工频周期逐事件计算模型。

最终目标是：

- 每个 PWM 开关周期内识别实际门极换相事件；
- 获取每个事件对应的实际三相电感电流；
- 获取事件时刻对应的实际 DC-link 电压；
- 根据开通时刻电流极性区分硬开通和软开通；
- 调用现有公共开关事件损耗模型计算 Eon/Eoff/Err；
- 将一个工频周期内的事件总能量换算为平均开关损耗；
- 保持现有用户输入、器件选择、NPC 逻辑和公共损耗接口兼容。

## 2. 修改范围

### 包含范围

- 三相两电平 VSI 波形事件数据；
- 三相两电平 VSI 开关损耗入口；
- VSI 事件统计和损耗审计字段；
- VSI 相关专项测试；
- 本计划和 ChangeLog；
- 每一步独立测试、commit 和 push。

### 不包含范围

- 不新增用户输入；
- 不修改三相三电平 NPC 的计算逻辑；
- 不修改公共器件 Eon/Eoff 损耗公式；
- 不引入死区、Coss、寄生振铃或详细门极驱动模型；
- 不扩展到其他拓扑的开关损耗修正；
- 不改变器件选型算法和导通损耗算法；
- 不改变 `Other loss` 的现有语义，当前应保持为零。

## 3. 当前问题

当前三相两电平 VSI 已生成以下波形信息：

- 三相实际电感电流；
- 三相 PWM 门极信号；
- 三相桥臂状态；
- DC-link 电流和电压波形；
- 相电流 RMS/峰值统计。

但是当前器件损耗流程没有像 NPC 一样读取 VSI 的逐事件列表。`run_device_pipeline.py` 已有单相全桥逐事件分支和 NPC 逐事件分支，但没有三相两电平 VSI 专用的逐事件开关损耗分支。因此 VSI 仍可能使用代表性 `SwitchStress` 中的峰值电流和固定开关频率，无法反映每个开关时刻的实际电流。

## 4. 物理和计数约定

### 4.1 开关编号

三相两电平 VSI 共 6 个物理开关位置：

| 相别 | 上管 | 下管 |
|---|---|---|
| A 相 | S1 | S2 |
| B 相 | S3 | S4 |
| C 相 | S5 | S6 |

### 4.2 桥臂互补关系

- 每个桥臂的下管门极是上管门极的互补信号；
- 暂不建模死区；
- 一个上管门极变化对应一个上管事件和一个互补下管事件；
- 事件必须根据实际门极数组提取，不能按理论固定次数硬编码。

### 4.3 损耗汇总

事件总能量按 6 个物理开关位置和一个工频周期换算：

```text
Psw_on  = sum(Eon_event)  / (6 * Tline)
Psw_off = sum(Eoff_event) / (6 * Tline)
Prr     = sum(Err_event)  / (6 * Tline)
```

对于 SiC 器件：

```text
Err = 0
```

### 4.4 开通极性规则

- `signed_current_A < 0` 且事件为 `turn_on`：软开通，`Eon = 0`；
- `signed_current_A >= 0` 且事件为 `turn_on`：硬开通，使用实际电流计算 `Eon`；
- `turn_off`：使用实际关断时刻电流计算 `Eoff`；
- 不能使用全周期最大电流替代事件电流。

## 5. 分步实施方案

### 第一步：建立 VSI 当前损耗基线和代码边界

**目标：** 固化当前三相两电平 VSI 的损耗行为，明确现有代码入口和测试基线。

**详细内容：**

1. 读取三相两电平 VSI 的输入 schema、synthesizer、waveform、stress 和 evaluator；
2. 读取 `run_device_pipeline.py` 中 VSI 的器件损耗入口；
3. 确认当前 `SwitchStress` 使用的电流、频率和阻断电压来源；
4. 记录当前设计点开关损耗、总损耗和 efficiency sweep 中的半导体损耗；
5. 确认当前 VSI 波形数组覆盖一个完整工频周期；
6. 增加或整理 VSI 基线合同测试，不修改生产计算逻辑；
7. 将基线结果写入 `pytest_temp/three-phase-two-level-vsi-step1/`。

**验收标准：**

- 明确当前损耗使用的是代表性值还是事件值；
- 明确六个开关的物理位置数为 6；
- 基线测试通过；
- 不修改 NPC 和公共损耗模型。

**提交要求：**

```text
test: establish three-phase VSI switching-loss baseline
```

完成测试后必须 commit 并 push，再更新本计划和 ChangeLog 回执。

### 第二步：定义三相两电平 VSI 事件数据结构

**目标：** 建立与 NPC 类似、但适用于两电平六开关桥的事件数据结构。

**详细内容：**

1. 在 VSI waveform metadata 中新增：
   - `three_phase_vsi_switching_events`；
   - `three_phase_vsi_switching_event_count`；
   - `three_phase_vsi_switching_event_audit`；
2. 统一开关字段：
   - `phase`；
   - `switch_name`；
   - `switch_index`；
   - `bridge_leg`；
   - `event_type`；
   - `event_time_s`；
   - `signed_current_A`；
   - `absolute_current_A`；
   - `blocking_voltage_V`；
   - `gate_before`；
   - `gate_after`；
   - `event_source`；
   - `current_source`；
   - `blocking_voltage_source`；
3. 明确事件时间范围为 `[0, Tline)` 或按项目现有周期边界约定处理；
4. 记录事件电流正负、硬/软开通统计和阻断电压范围；
5. 不在这一阶段接入损耗计算，只建立结构和审计测试。

**验收标准：**

- 元数据中存在事件列表和审计信息；
- 每个事件可追溯到一个相、一个开关、一个时间点和一个实际电流；
- 事件字段单位和符号约定明确；
- 事件数量不通过固定常数伪造。

**提交要求：**

```text
feat: add three-phase VSI switching event contract
```

完成测试后必须 commit 并 push，再更新计划和 ChangeLog。

### 第三步：从实际门极边沿提取 VSI 开关事件

**目标：** 根据三相两电平实际 PWM 门极变化，生成完整工频周期的六开关事件。

**详细内容：**

1. 复用 NPC 的事件提取思想，读取完整波形中的三相桥臂门极状态；
2. 建立 A/B/C 三个桥臂到 S1-S6 的映射；
3. 检测每个桥臂上管门极的 `0 -> 1` 和 `1 -> 0`；
4. 同时生成互补下管对应的状态变化事件；
5. 从连续积分电流或已有完整波形中插值获取事件时刻电流；
6. 从实际 DC-link 电压波形中插值获取事件时刻阻断电压；
7. 处理工频周期边界，避免首尾事件重复或遗漏；
8. 记录事件来自实际门极边界，而不是预览数组峰值推断；
9. 增加 S1-S6 分项事件统计测试。

**验收标准：**

- 事件覆盖一个完整工频周期；
- S1-S6 均可按实际门极活动情况审计；
- 事件时间单调排序且不越界；
- 事件电流不是统一峰值；
- 事件阻断电压与 DC-link 波形一致；
- 互补门极关系保持成立。

**提交要求：**

```text
feat: extract three-phase VSI switching events from gate edges
```

完成测试后必须 commit 并 push，再更新计划和 ChangeLog。

### 第四步：将 VSI 事件接入公共开关损耗模型

**目标：** 使用实际事件电流和电压计算 VSI 的 Eon/Eoff/Err。

**详细内容：**

1. 在 `run_device_pipeline.py` 增加 VSI 专用事件损耗入口；
2. 读取 `three_phase_vsi_switching_events`；
3. 调用公共 `evaluate_switching_events()`；
4. 按事件电流极性判定硬/软开通；
5. 负电流开通强制得到 `Eon = 0`；
6. 非负电流开通使用事件实际电流计算 `Eon`；
7. 关断使用事件实际电流计算 `Eoff`；
8. SiC 器件反向恢复损耗设置为零；
9. 先扣除旧代表性开关损耗和反向恢复损耗，再写入事件汇总，避免重复计数；
10. 按 `6 * Tline` 进行物理位置和工频周期归一化；
11. 保持导通损耗、Eoss、栅极损耗、并联器件电流分配和器件选型不变。

**验收标准：**

- VSI 损耗模式明确标记为逐事件模式；
- 软开通事件的 Eon 为零；
- 硬开通和关断能量随事件电流变化；
- SiC Err 为零；
- 总损耗闭合；
- 不出现旧模型和新模型叠加。

**提交要求：**

```text
fix: calculate three-phase VSI switching loss per event
```

完成测试后必须 commit 并 push，再更新计划和 ChangeLog。

### 第五步：验证运行点和 efficiency sweep 传递

**目标：** 确保不同负载和 PF operating point 都重新生成 VSI 事件，并使用对应事件损耗。

**详细内容：**

1. 检查 `_sweep_operating_point()` 对 VSI 的负载和 PF 传递；
2. 检查每个 operating point 是否重新生成完整三相波形；
3. 检查事件数量、事件电流和硬/软开通统计是否随工况变化；
4. 检查 efficiency sweep 不复用满载设计点事件损耗；
5. 检查半导体损耗不再在所有负载点固定为同一个峰值结果；
6. 检查 `Other loss = 0`；
7. 检查 VSI 的电感、电容和半导体损耗字段仍然闭合；
8. 保持固定硬件选择，不在 sweep 中重新选择器件。

**验收标准：**

- 低载、半载、满载事件数据可区分；
- 半导体开关损耗随实际电流和事件数变化；
- PF 变化会影响事件电流和损耗；
- 不改变器件选择结果；
- efficiency sweep 输出路径仍位于当前 run 目录。

**提交要求：**

```text
test: verify three-phase VSI operating-point event-loss refresh
```

完成测试后必须 commit 并 push，再更新计划和 ChangeLog。

### 第六步：最终三相两电平 VSI 专项验收

**目标：** 完成最小闭环验收，确认 VSI 逐事件开关损耗不会影响 NPC。

**详细内容：**

1. 默认三相两电平 VSI 工况；
2. 低载、半载、满载工况；
3. PF 正常值和非单位 PF 工况；
4. 不同 DC-link 电压工况；
5. GUI Generate waveform 合同；
6. 六开关事件统计；
7. 硬/软开通和 SiC Err 统计；
8. 电感、电容、半导体和效率汇总；
9. `Other loss = 0`；
10. NPC 定向合同测试；
11. `compileall` 和 `git diff --check`；
12. 保存测试证据到 `pytest_temp/three-phase-two-level-vsi-step6/`；
13. 完成后将本计划移动到 `Plan/completed/`。

**建议测试命令：**

```powershell
New-Item -ItemType Directory -Force -Path pytest_temp/three-phase-two-level-vsi-step6 | Out-Null
python -B -m pytest -q `
  tests/test_dc_ac_three_phase_two_level_vsi_contract.py `
  tests/test_three_phase_two_level_vsi_switching_loss.py `
  tests/test_dc_ac_operating_refresh_gui_chain.py `
  tests/test_dc_ac_three_phase_three_level_npc_contract.py `
  --basetemp=pytest_temp/three-phase-two-level-vsi-step6/final-tests `
  --junitxml=pytest_temp/three-phase-two-level-vsi-step6/final-tests.xml

python -B -m compileall -q src tests
git diff --check
```

**验收标准：**

- VSI 波形完整覆盖一个工频周期；
- 六开关事件来源和电流可审计；
- 开通损耗遵守电流极性规则；
- 关断损耗使用实际事件电流；
- 实际 DC-link 电压进入事件模型；
- SiC 反向恢复为零；
- 半导体总损耗闭合且不重复计数；
- efficiency sweep 工况变化可反映到损耗；
- NPC 定向合同保持通过；
- 所有阶段独立 commit 和 push；
- 计划归档到 `Plan/completed/`。

## 6. 测试和证据规则

每一步必须记录：

- 修改文件；
- 测试命令和结果；
- `compileall` 结果；
- `git diff --check` 结果；
- pytest 证据路径；
- 实现 commit；
- 文档回执 commit；
- 远端 branch 和 HEAD。

不得提交：

- `outputs/`；
- `pytest_temp/`；
- `__pycache__/`；
- `*.pyc`；
- 临时日志。

## 7. 风险控制

| 风险 | 控制措施 |
|---|---|
| 事件重复计数 | 根据真实门极边沿生成事件，按六个物理开关位置归一化 |
| 事件电流被峰值替代 | 测试事件电流唯一值和范围，禁止统一 peak-current 字段 |
| 上下管事件映射错误 | 测试 S1-S6 门极互补关系和每相桥臂事件顺序 |
| DC-link 电压使用固定值 | 测试事件电压来自实际 DC-link 波形插值 |
| VSI 修改影响 NPC | 每一步运行 NPC 定向合同测试并检查 diff 范围 |
| efficiency sweep 复用设计点事件 | 对低载/半载/满载比较事件数据和损耗 |
| 负电流开通错误计算 Eon | 增加软开通事件的 Eon=0 断言 |
| SiC Err 非零 | 增加 SiC 器件 reverse recovery=0 断言 |
| 状态或输出污染其他 run | 所有证据写入当前 `pytest_temp` 或当前 run 输出目录 |

## 8. 计划状态表

| 步骤 | 状态 | 实现 commit | 回执 commit | 远端 push | 证据 |
|---|---|---|---|---|---|
| 1 | 已完成 | `e63152d` | `e63152d` | 已推送 | `pytest_temp/three-phase-two-level-vsi-step1/` |
| 2 | 待执行 | - | - | - | - |
| 3 | 待执行 | - | - | - | - |
| 4 | 待执行 | - | - | - | - |
| 5 | 待执行 | - | - | - | - |
| 6 | 待执行 | - | - | - | - |

## 第一步执行回执

- 已确认当前 VSI 入口：`three_phase_two_level_voltage_source_inverter/waveform.py`、`stress.py`、`run_device_pipeline.py`。
- 当前波形覆盖一个工频周期：默认 `0.02 s`，`38401` 个采样点，`fsw=20 kHz`，`fline=50 Hz`。
- 当前应力使用波形支持的相电流峰值/RMS：默认峰值 `22.4133 A`、RMS `14.4578 A`；尚未使用逐开关事件电流。
- 当前器件基线：六个主开关位置，默认选中 `SCT4018KR`，设计点半导体总损耗 `87.3178 W`。
- 当前波形已保存 Q1-Q6 分支电流统计，但尚无 VSI 专用逐事件列表和事件级损耗入口。
- 定向验证：`15 passed`；证据见 `pytest_temp/three-phase-two-level-vsi-step1/baseline-tests.xml` 和 `baseline-report.json`。
- `compileall`、`git diff --check` 在本步提交前复核。

## 9. 完成和归档规则

1. 第 1 至第 6 步全部完成并通过专项测试；
2. 每一步实现和文档回执独立 commit 并 push；
3. 最终更新本计划和 `ChangeLog.md`；
4. 确认远端 branch 和 HEAD；
5. 将本文件从 `Plan/Active/` 移动到 `Plan/completed/`；
6. 归档动作单独 commit 并 push；
7. 保留最终测试证据和当前 VSI 输出目录供人工检查。

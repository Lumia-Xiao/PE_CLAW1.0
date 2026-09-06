# 单相全桥逆变器电感电流波形修正计划

## 1. 计划目标

修正 `single_phase_full_bridge_inverter` 当前电感电流计算异常问题。

当前问题表现为：

- 正弦电流参考峰值约为 6 A，但连续积分后的实际电流峰值可超过 30 A；
- 实际电流不是“正弦平均值叠加高频 PWM 纹波”；
- 周期首尾残差虽然很小，但每个开关周期的平均电流没有跟踪正弦参考；
- 低分辨率离散 PWM 产生的桥输出平均电压误差被电感积分放大；
- 电感设计电流与波形积分电流不一致，可能导致电感饱和裕量判断失真。

本计划的目标是使单相全桥电流计算采用与 NPC 一致的核心方法：

```text
正弦电流参考
  -> 逐开关周期计算目标平均桥电压
  -> 生成单相全桥实际开关状态序列
  -> 逐段积分实际电感电流
  -> 计算周期平均电流误差
  -> 修正目标平均桥电压
  -> 满足周期稳态条件
  -> 在真实开关事件时刻提取电流和电压
```

最终实际电流应满足：

```text
i_L(t) = i_reference_fundamental(t) + i_switching_ripple(t)
```

本计划只处理单相全桥的电感电流、开关事件时序和由此依赖的开关损耗输入，不扩大到其他拓扑。

## 2. 适用范围和不变约束

### 2.1 必须保持

- 保持现有用户输入字段、GUI 表单、默认值、输入校验和输入语义。
- 保持单相全桥现有拓扑 ID、器件角色 `main_switch`、器件选择和并联数合同。
- 保持单极性 SPWM 拓扑和门极互补关系：`S2 = 1 - S1`、`S4 = 1 - S3`。
- 保持 NPC 已完成的事件级损耗模型和其他拓扑代码不变。
- 保持 SiC 反向恢复损耗为 0。
- 保持导通损耗、Eoss、栅极损耗、磁性件损耗、电容损耗和热设计逻辑不变，除非电流波形数据传递必须做最小调整。
- 保持输出目录隔离规则和 `pytest_temp` 临时文件规则。

### 2.2 明确不做

- 不新增采样点数、死区时间、软开关阈值等用户输入。
- 不将单极性 SPWM 改为双极性 SPWM。
- 不用工频末端人工线性修正掩盖周期误差。
- 不使用正弦峰值电流、工频中点电流或固定峰值作为开关事件电流。
- 不修改 NPC 的计算公式、输出字段或效率扫描逻辑。
- 不通过放宽测试断言、删除失败证据或调整损耗系数来掩盖电流波形问题。

## 3. 已确认根因

### 3.1 单相全桥当前路径

主要文件：

- `src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/waveform.py`
- `src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/synthesizer.py`

当前 refined waveform 路径：

1. 使用固定 `samples_per_switching_period = 12`；
2. 在离散采样点比较调制波和载波；
3. 用离散门极状态构造 `v_ab_pwm_v`；
4. 用 `di/dt = (v_ab_pwm - v_ac) / L` 连续积分；
5. 只通过初始电流偏置满足 `i(Tline) - i(0) = 0`。

### 3.2 与 NPC 的关键差异

NPC 还包含：

- 每个开关周期的目标平均电压计算；
- 实际周期平均电流与参考电流的误差反馈；
- 目标电压修正后重新生成周期状态序列；
- 统一事件时间轴和精确分段电流积分；
- 周期稳态初始电流求解。

本计划需要补齐的是这些缺失的单相全桥对应逻辑，而不是只提高采样点数量。

## 4. 统一计算合同

### 4.1 电感方程

理想电感模型使用：

```text
di/dt = (v_bridge(t) - v_ac(t)) / L
```

其中：

- `v_bridge(t)` 是实际单相全桥桥输出电压；
- `v_ac(t)` 是当前设计的正弦输出电压；
- `L` 使用当前候选设计对应的有效输出电感。

### 4.2 周期平均电流目标

对每个开关周期：

```text
Vbridge_target_avg
  = Vac_avg + 2L × (Iref_avg - Istart) / Tsw
```

其中：

- `Vac_avg`：本开关周期输出正弦电压平均值；
- `Iref_avg`：本开关周期正弦电流参考平均值；
- `Istart`：本开关周期实际电感电流起始值；
- `Tsw`：开关周期。

目标电压必须限制在单相全桥允许范围：

```text
-Vdc <= Vbridge_target_avg <= +Vdc
```

### 4.3 周期平均反馈

每个开关周期迭代：

```text
Ierror = Iactual_avg - Iref_avg
Vtarget_new = Vtarget_old - K × 2L × Ierror / Tsw
```

默认建议：

- `K = 1.0`；
- 每周期最多 3 至 5 次修正；
- 记录每周期迭代次数、误差和是否发生电压限幅。

### 4.4 周期稳态

工频周期初始电流必须通过周期 shooting/fixed-point 求解：

```text
i(Tline) - i(0) = 0
```

周期首尾条件与逐开关周期平均电流条件必须同时满足。

## 5. 总体执行规则

本计划分为 8 步。每一步独立完成，不合并提交。

每一步严格执行：

1. 阅读本步骤涉及代码、测试和当前差异；
2. 明确修改文件和验证命令；
3. 只实施本步骤范围内的最小修改；
4. 测试临时文件写入 `pytest_temp/single-phase-full-bridge-current-stepN/`；
5. 运行本步骤专项测试和必要静态检查；
6. 执行 `git diff --check`，检查没有混入 `outputs/`、`pytest_temp/`、缓存或无关文件；
7. 更新本计划状态、验证结果和 Git 回执；
8. 更新根目录 `ChangeLog.md`；
9. 独立执行 `git commit`、`git push`，并核对远端 HEAD；
10. commit 和 push 完成后才能开始下一步。

默认分支：当前工作分支。不得直接修改或推送 `master`。

## 6. 分步实施安排

### 第一步：建立当前异常基线

**目标：** 固化当前异常，防止修正过程中失去前后对比依据。

**修改内容：**

- 在单相全桥专项测试中记录默认工况的：
  - 电感值；
  - 正弦参考电流 RMS/峰值；
  - 实际电流 RMS/峰值；
  - 实际电流与参考电流相关性；
  - PWM 纹波 RMS/峰峰值；
  - 桥输出电压基波幅值；
  - 周期首尾残差；
  - 输出有功功率；
  - 电感饱和电流与实际电流峰值比较。
- 将诊断输出写入 `pytest_temp/single-phase-full-bridge-current-step1/`。
- 本步骤不修改生产计算逻辑。

**验收：**

- 基线可重复；
- 异常电流峰值、桥电压基波误差和电流误差均被明确记录；
- 现有单相全桥损耗合同测试保持通过。

**提交：**

```text
test: establish full-bridge current waveform baseline
```

### 第二步：建立统一单相全桥开关周期和事件时间轴

**目标：** 将 GUI 波形采样轴与实际开关事件轴分离。

**修改文件：**

- `waveform.py`；
- 单相全桥专项测试。

**修改内容：**

- 建立 `0, Tsw, 2Tsw, ..., Tline` 的统一开关周期边界；
- 从调制波与载波交点计算门极翻转时间，或在采样区间内进行确定性线性插值；
- 为 `S1`、`S2`、`S3`、`S4` 生成开通/关断事件；
- 去除工频首尾重复事件，采用 `[0, Tline)` 半开区间合同；
- 为每个事件保存前后状态和事件来源；
- 保持 GUI 可用的低频采样数组不变。

**验收：**

- 事件时间严格单调且无重复物理事件；
- 每个开关均有开通和关断事件；
- 互补门极关系保持；
- 事件时间不再只等于最近采样点；
- 周期平均桥电压误差可被测量。

**提交：**

```text
feat: add full-bridge switching event time axis
```

### 第三步：实现每个开关周期的目标平均桥电压

**目标：** 使每个开关周期的桥电压平均值由电流参考和实际电流状态共同决定。

**修改文件：**

- `waveform.py`；
- 必要的单相全桥内部 helper 测试。

**修改内容：**

- 新增单相全桥目标平均电压函数；
- 按统一周期边界计算 `Vac_avg` 和 `Iref_avg`；
- 使用当前周期起始实际电流计算目标桥电压；
- 对目标桥电压执行 `[-Vdc, +Vdc]` 限幅；
- 记录限幅前/后的目标电压和饱和状态；
- 不新增用户输入。

**验收：**

- 每个开关周期都有目标平均桥电压；
- 目标电压与参考电流、起始实际电流和电感值相关；
- 超出调制能力时明确记录饱和，而不是静默改变电流目标。

**提交：**

```text
feat: calculate full-bridge period-average voltage target
```

### 第四步：根据目标平均电压生成合法单相全桥开关序列

**目标：** 将目标桥电压转换成实际单极性 SPWM 开关状态。

**修改内容：**

- 保持单极性 SPWM 和互补门极结构；
- 根据目标平均桥电压生成每周期占空比/状态序列；
- 使用实际 DC-link 电压计算桥输出电平；
- 生成 `-Vdc`、`0`、`+Vdc` 的实际桥电压区间；
- 记录每个区间的起止时间、桥状态和门极状态；
- 校验周期平均桥电压与目标值的误差。

**验收：**

- 不产生非法上下管同时导通；
- 桥输出状态和门极状态一致；
- 周期平均桥电压误差处于设定容差；
- 实际 DC-link 纹波被正确带入桥电压。

**提交：**

```text
feat: generate corrected full-bridge switching sequence
```

### 第五步：加入逐开关周期平均电流反馈修正

**目标：** 让实际电感电流的周期平均值跟踪正弦参考。

**修改内容：**

每个开关周期执行：

1. 根据当前状态计算目标桥电压；
2. 生成实际状态序列；
3. 对每个电压区间积分电感电流；
4. 计算实际周期平均电流；
5. 与参考周期平均电流比较；
6. 修正目标桥电压；
7. 迭代至收敛或达到最大迭代次数；
8. 将周期结束电流传递给下一周期。

**必须记录：**

- `reference_current_average_A`；
- `actual_current_average_A`；
- `current_average_error_A`；
- `average_current_correction_iterations`；
- `average_current_correction_saturated`；
- `target_voltage_before_correction_V`；
- `target_voltage_after_correction_V`。

**验收：**

- 默认工况每周期平均电流误差满足容差；
- 反馈未收敛或发生饱和时有明确诊断；
- 不使用工频末端人工修正；
- 实际电流不再因桥电压偏差产生异常低频漂移。

**提交：**

```text
feat: add full-bridge average-current feedback
```

### 第六步：实现跨工频周期连续积分和周期稳态求解

**目标：** 让整个工频周期的实际电流连续，并满足周期稳态。

**修改内容：**

- 将所有开关周期的电流状态连续传递；
- 使用 shooting/fixed-point 求解工频周期初始电流；
- 同时检查周期首尾电流残差和逐周期平均电流误差；
- 记录迭代次数、残差、收敛状态、饱和周期数量；
- 删除或旁路任何周期独立去漂移、工频末端线性修正逻辑；
- 低频参考数组仅作为目标，不作为实际事件电流。

**验收：**

- `i(Tline) - i(0)` 满足容差；
- 实际电流覆盖完整工频周期；
- 实际电流包含合理 PWM 高频纹波；
- 实际电流 RMS/峰值与参考及电感设计结果一致；
- 默认工况不会超过电感饱和电流，或明确给出饱和诊断。

**提交：**

```text
feat: solve continuous full-bridge periodic current
```

### 第七步：将实际积分电流接入开关事件

**目标：** 让每个开关事件使用真实积分电流和真实阻断电压。

**修改内容：**

- 事件电流取门极切换前的连续状态；
- 门极状态取切换后的状态；
- 事件阻断电压取事件时刻实际 DC-link 电压；
- 保存事件所在积分区间和来源字段；
- 重新统计硬开通、软开通、关断次数以及电流/电压范围；
- 保持第五步拓扑中立事件能量模型接口不变。

**验收：**

- 负电流开通标记为软开通；
- 非负电流开通标记为硬开通；
- 事件电流不是正弦峰值或工频中点电流；
- 事件时间、事件电流和积分区间逐项对应。

**提交：**

```text
feat: attach corrected integrated current to full-bridge events
```

### 第八步：完成损耗、运行点和专项验收

**目标：** 证明修正后的电流波形已经正确传递到损耗和设计结果。

**测试范围：** 单相全桥及必要的 NPC 回归，不执行无关拓扑全量回归。

**验证内容：**

- 实际电流基波幅值接近参考值；
- 实际 RMS 和峰值处于合理范围；
- PWM 纹波小于基波且与电感设计目标一致；
- 每个开关周期平均电流误差满足容差；
- 工频周期首尾残差满足容差；
- `average(v_ac * i_L)` 接近目标输出功率；
- 实际电流峰值不超过电感饱和能力；
- 负电流开通 `Eon = 0`；
- 非负电流开通使用实际电流计算 Eon；
- 关断使用实际电流计算 Eoff；
- SiC `Err = 0`；
- 运行点刷新保持固定硬件并继续使用修正后的事件级损耗；
- efficiency sweep 不退回旧模型；
- `Other loss = 0`；
- `manifest.status` 和阶段状态正确收尾。

**建议测试命令：**

```powershell
python -m pytest -q tests/test_single_phase_full_bridge_switching_loss.py tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_dc_ac_operating_refresh_gui_chain.py tests/test_dc_ac_three_phase_three_level_npc_contract.py
python -m compileall -q src tests
git diff --check
```

**提交：**

```text
test: validate full-bridge sinusoidal current and switching loss
```

## 7. 最终验收标准

默认单相全桥工况至少满足：

```text
实际电流基波幅值接近参考值
实际电流 RMS 接近设计目标
PWM 纹波处于合理范围
每周期平均电流误差满足容差
工频周期首尾残差满足容差
输出有功功率接近目标功率
实际电流峰值不超过电感设计能力
硬/软开通统计可解释
事件电流来源可审计
效率和损耗结果闭合
```

## 8. 计划状态和证据记录

| 步骤 | 状态 | 实现 commit | 回执 commit | 远端 push | 验证证据 |
|---|---|---|---|---|---|
| 1 | 已完成 | `4247065` | `de6f78e` | 已推送 | `pytest_temp/single-phase-full-bridge-current-step1/baseline.json`; `13 passed`; `git diff --check` |
| 2 | 已完成 | `02c8a90` | `065f1d7` | 已推送 | `10 passed`; `14 passed`; `git diff --check`; `switching_event_time_quantized_to_waveform_grid=False` |
| 3 | 已完成 | `f55e145` | `4368196` | 已推送 | `25 passed`; `git diff --check`; per-cycle formula and clamp diagnostics |
| 4 | 已完成 | `996a595` | `906e374` | 已推送 | `26 passed`; `git diff --check`; valid complementary three-level sequence |
| 5 | 待执行 | - | - | - | - |
| 6 | 待执行 | - | - | - | - |
| 7 | 待执行 | - | - | - | - |
| 8 | 待执行 | - | - | - | - |

每一步完成后必须填写实际 commit、回执 commit、远端 HEAD 和测试证据。只有 commit 和 push 均完成后，才能将该步骤标记为已完成。

### 第一步执行回执

- 实现提交：`4247065` (`test: establish full-bridge current waveform baseline`)
- 验证：`python -m pytest -q tests/test_single_phase_full_bridge_current_baseline.py tests/test_single_phase_full_bridge_switching_loss.py` -> `13 passed`
- 基线生成：`python scripts/record_single_phase_full_bridge_current_step1_baseline.py`
- 基线文件：`pytest_temp/single-phase-full-bridge-current-step1/baseline.json`
- 关键结果：参考峰值 `6.1483 A`，实际峰值 `31.1782 A`，相关性 `0.3093`，PWM 纹波 RMS `13.8982 A`，周期首尾残差 `1.61e-12 A`
- 生产波形逻辑：未修改
- 回执提交：`de6f78e` (`docs: record full-bridge current baseline receipt`)
- 远端 HEAD：`de6f78ed245708cf609401ec17e261caaeba80b2`

### 第二步执行回执

- 实现提交：`02c8a90` (`feat: add full-bridge switching event time axis`)
- 变更：新增统一开关周期边界轴、事件时间轴，以及调制波/载波交点线性插值；GUI 波形采样轴保持不变
- 验证：`python -m pytest -q tests/test_single_phase_full_bridge_switching_loss.py` -> `10 passed`
- 验证：`python -m pytest -q tests/test_single_phase_full_bridge_current_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py` -> `14 passed`
- 验证：`git diff --check` -> passed
- 关键验收：四个开关事件完整；互补门极保持；事件不再量化到波形采样网格；周期边界为 `[0, Tline]`
- 回执提交：`065f1d7` (`docs: record full-bridge event axis receipt`)
- 远端 HEAD：`065f1d7accb512e4c2010de1a00fe95449d7d112`

### 第三步执行回执

- 实现提交：`f55e145` (`feat: calculate full-bridge period-average voltage target`)
- 变更：按统一开关周期计算 `Vac_avg + 2L * (Iref_avg - Istart) / Tsw`，并执行 `[-Vdc, +Vdc]` 限幅
- 记录：未限幅目标、限幅后目标、参考电流平均值、周期起始实际电流、周期平均 AC 电压、周期时长和饱和标志
- 验证：`python -m pytest -q tests/test_single_phase_full_bridge_switching_loss.py tests/test_single_phase_full_bridge_current_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py` -> `25 passed`
- 验证：`git diff --check` -> passed
- 用户输入：未新增
- 实际 PWM 开关序列：本步骤未替换，留待第 4 步
- 回执提交：`4368196` (`docs: record full-bridge voltage target receipt`)
- 远端 HEAD：`4368196632025eb2ae765916cb80040a8bb6e181`

### 第四步执行回执

- 实现提交：`996a595` (`feat: generate corrected full-bridge switching sequence`)
- 变更：由逐周期限幅目标电压生成单极性 SPWM 互补门极、`-Vdc/0/+Vdc` 桥状态和实际 DC-link 电压桥波形
- 记录：实际周期平均桥电压、目标误差、状态区间数量和序列生成方法
- 验证：`python -m pytest -q tests/test_single_phase_full_bridge_switching_loss.py tests/test_single_phase_full_bridge_current_baseline.py tests/test_dc_ac_single_phase_full_bridge_contract.py` -> `26 passed`
- 验证：`git diff --check` -> passed
- 事件数量：不再固定为旧采样序列的 `3200`，测试改为验证四个开关均有开关事件且审计数量一致
- 用户输入：未新增
- 第五步平均电流反馈：尚未实施
- 回执提交：`906e374` (`docs: record corrected full-bridge sequence receipt`)
- 远端 HEAD：`906e3746c386586cddd5cff068eade9f8c7a05dc`

## 9. 风险和控制

| 风险 | 控制 |
|---|---|
| 周期平均电压无法达到目标 | 记录调制饱和，不静默修正电流结果 |
| 开关事件时间量化误差 | 使用事件交点或确定性区间插值 |
| 电流反馈振荡 | 限制每周期迭代次数并记录修正历史 |
| 周期稳态不收敛 | 保留残差和初始值诊断，不做末端人工修正 |
| 实际电流超过电感能力 | 在验收中明确失败，不继续接受损耗结果 |
| 事件损耗重复计算 | 继续从旧代表性开关损耗中扣除后再写入事件级损耗 |
| NPC 回归 | 每个涉及共享 helper 的步骤运行 NPC 合同测试 |

## 10. 归档规则

第 1 至第 8 步全部完成、验证、commit 和 push 后：

1. 更新本计划最终状态；
2. 更新 `ChangeLog.md`；
3. 将本文件从 `Plan/Active/` 移动到 `Plan/completed/`；
4. 归档动作单独 commit 和 push；
5. 保留测试结果、远端 HEAD 和最终提交记录供人工检查。

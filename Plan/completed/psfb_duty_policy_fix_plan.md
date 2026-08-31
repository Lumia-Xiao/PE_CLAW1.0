# PSFB Duty Policy 修复计划

## 1. 计划状态

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `completed` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-24` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 基准工程 | `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw` |
| 目标拓扑 | `phase_shifted_full_bridge_diode_rectifier_isolated` |
| 设计请求矩阵 | `07_psfb_diode` |
| 工况数量 | 7 |
| 当前阻塞工况 | `c02_low_input_full_load` |
| 主迁移计划 | `Plan/active/complete_migration_2_to_1_plan.md` |
| 本计划位置 | `Plan/active/psfb_duty_policy_fix_plan.md` |

本计划只处理 PSFB duty policy 及其直接调用链。除 PSFB 专项测试和必要的
PSFB 证据更新外，不运行或修改其他拓扑的验证流程。

## 2. 问题基线

当前 PSFB 低输入固定硬件 refresh 工况：

`07_psfb_diode/c02_low_input_full_load`

失败信息：

`PSFB duties must satisfy 0 <= effective <= command <= 1.`

当前实现存在设计点和工作点 duty 口径混用的风险：工作点根据当前输入电压
重新计算 `effective_duty`，但 primary-current 路径仍可能使用设计点的
`command_duty_nom` 和 `duty_loss_nom`。低输入时可能导致：

```text
effective_duty_operating > command_duty_nom
```

从而违反：

```text
0 <= effective_duty <= command_duty <= 1
```

本计划禁止通过简单截断 duty 或屏蔽异常来伪造通过。必须使当前工作点的
`effective_duty`、`duty_loss` 和 `command_duty` 使用同一工况输入计算，并
保持物理约束和 2.0 兼容行为。

## 3. 修复目标

1. 设计点 duty 与工作点 duty 语义分离。
2. 工作点根据当前 `vin`、`vout`、负载、电感参数和开关频率重新计算 duty。
3. primary-current、waveform、stress 和 structured report 使用同一组工作点 duty。
4. 固定硬件 refresh 不重新选择器件、磁芯、电容或电感。
5. PSFB 7 个工况全部可执行，且不再出现 duty boundary failure。
6. 保留设计点 duty、工作点 duty 和 duty 限制值的可审计字段。
7. 不影响其他拓扑，不执行全量 103 工况回放。

## 4. 验证范围

### PSFB 工况

| 工况 | 目的 |
| --- | --- |
| `c01_nominal_full_load` | 设计点基线 |
| `c02_low_input_full_load` | 原始失败边界 |
| `c03_high_input_full_load` | 高输入 duty 方向 |
| `c04_nominal_light_load_20pct` | 轻载 duty-loss 行为 |
| `c05_nominal_very_light_load_10pct` | 极轻载边界 |
| `c06_nominal_high_frequency` | 频率对 duty loss 的影响 |
| `c07_nominal_high_ripple` | 输出纹波输入不改变 duty 约束 |

### 允许运行的测试

- PSFB topology/plugin contract tests。
- PSFB duty policy 单元测试。
- PSFB waveform、stress 和 primary-current 相关测试。
- PSFB operating-point refresh 测试。
- 已有 DC-DC 测试中只针对 PSFB 的测试项。
- PSFB 7 工况 replay 和结构化输出验证。

### 本计划明确不运行

- 全量 `103` 工况回放。
- 其他 16 个设计请求矩阵的 replay。
- 其他拓扑的全量测试。
- 全量 `pytest`，除非后续发现跨拓扑公共代码回归且另行批准。

## 5. 五步实施计划

### 第 1 步：冻结 PSFB 专项基线

#### 工作内容

1. 读取 `07_psfb_diode` 的 7 个工况和现有 replay 结果。
2. 保存每个工况的输入、执行路径、状态、硬件 snapshot checksum 和
   operating-point input checksum。
3. 提取并记录：`effective_duty`、`duty_loss`、`command_duty`、
   `max_effective_duty`、`max_command_duty`。
4. 确认只有 `c02_low_input_full_load` 为 duty boundary failure。
5. 建立 PSFB 修复前基线文件，禁止覆盖 2.0 golden baseline。

#### 主要证据

- `migration/evidence/20260824/step12_final_acceptance/comparison/comparison_final.json`
- `migration/evidence/20260824/step9_operating_points/current_repaired/operating_point_replay_matrix.csv`
- 新增 PSFB 专项基线 JSON/CSV。

#### 完成条件

- 7 个 PSFB 工况均有唯一记录。
- 失败原因与原始异常完全一致。
- 基线包含修复前 duty 数值和 checksum。

#### 提交要求

完成验证后创建独立 commit 并 push，commit message 必须包含：

`PSFB Step 1: freeze duty policy baseline`

---

### 第 2 步：定义并锁定 PSFB duty policy

状态：`completed`（2026-08-24）

#### 工作内容

1. 将 duty 计算整理为可复用的 PSFB 专用函数或明确的 policy 层。
2. 明确三类字段：设计点 duty、工作点 duty、
   `max_effective_duty` 和 `max_command_duty` 限制值。
3. 工作点统一计算：

```text
effective_duty = turns_ratio * (vout + diode_drop) / vin_operating
duty_loss = leakage_loss(vin_operating, load_current, fs)
command_duty = effective_duty + duty_loss
```

4. 统一约束检查：

```text
0 <= effective_duty <= command_duty <= 1
```

5. 对超出配置上限的情况返回明确的 feasibility/boundary 状态，不静默截断。
6. 增加正常、低输入、高输入、轻载和极轻载 duty policy 单元测试。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/phase_shifted_full_bridge_diode_rectifier_isolated/`
- 必要时同步 `primary_current_model.py` 和 PSFB report metadata。

#### 完成条件

- policy 对 nominal、low-line、high-line、light-load 输入有确定性结果。
- duty loss 与 `command_duty - effective_duty` 一致。
- 非法 duty 仍被正确拒绝。

#### 提交要求

完成验证后创建独立 commit 并 push，commit message 必须包含：

`PSFB Step 2: define duty policy`

---

### 第 3 步：修复 operating-point 调用链

状态：`completed`（2026-08-24）

#### 工作内容

1. 修改 PSFB operating-point waveform 生成，使其使用当前工况的
   `effective_duty`、`duty_loss` 和 `command_duty`。
2. 修改 primary-current model 调用，禁止用 nominal command duty 覆盖当前工作点。
3. 检查 stress、loss 和 structured report 是否引用正确 duty 来源。
4. 保留设计点字段，例如 `command_duty_nom`，同时增加或明确工作点字段，
   例如 `command_duty_operating`。
5. 固定硬件 refresh 只更新工作点波形和派生指标，不重新运行器件、磁芯、
   电容或电感选择。
6. 对 nominal full-load 进行回归，确保修复没有改变设计点硬件快照。

#### 主要修改范围

- `synthesizer.py`
- `waveform.py`
- `primary_current_model.py`
- PSFB stress/evaluator/report 适配层（仅在确认直接受影响时修改）。

#### 完成条件

- 低输入 refresh 不再将 nominal command duty 与 operating effective duty 混用。
- waveform、stress、loss 使用同一组 operating duty。
- nominal 设计点 candidate 和硬件 snapshot checksum 保持不变。
- 没有通过删除异常检查或统一 clamp 来掩盖非法状态。

#### 提交要求

完成验证后创建独立 commit 并 push，commit message 必须包含：

`PSFB Step 3: align operating-point duty`

---

### 第 4 步：运行 PSFB 专项回归

状态：`completed`（2026-08-24）

#### 工作内容

1. 运行 PSFB 7 个工况。
2. 运行 PSFB topology/plugin contract tests。
3. 运行 PSFB duty policy、primary-current、waveform、stress 和 refresh tests。
4. 对每个工况检查执行状态、boundary_failure、
   `0 <= effective_duty <= command_duty <= 1`、NaN/Inf 和物理时间比例。
5. 对比修复前后 PSFB 输出，只接受 duty policy 直接导致的变化。

#### 完成条件

- PSFB `7/7` 工况执行成功。
- PSFB duty boundary failure 数量为 `0`。
- PSFB 专项测试全部通过。
- fixed-hardware refresh 未重新选择硬件。

#### 提交要求

完成验证后创建独立 commit 并 push，commit message 必须包含：

`PSFB Step 4: pass topology regression`

第 4 步已完成。已对 `07_psfb_diode` 的 7 个工况执行 PSFB 专项回归，
并对 duty 顺序、duty-loss 恒等式、NaN/Inf、primary-current 时间分区、
固定硬件 checksum 和 c02 boundary 状态转换进行量化检查。差异分类仅限
PSFB operating duty policy、primary-current、waveform 和 stress refresh。

第 4 步专项验证：

- 回归脚本：`scripts/validate_psfb_step4_regression.py`
- 回归证据：`migration/evidence/20260824/psfb_duty_policy/psfb_step4_regression_results.json`
- 回归结果：`7/7 executed`、`0 boundary failure`、`0 execution error`
- c02 状态转换：`boundary_failure -> executed`
- 所有 duty 和派生数值：有限值，无 NaN/Inf
- primary-current 时间分区：7/7 个工况均满足三段时间之和等于半周期
- fixed-hardware checksum：7 个工况共享 1 个 checksum
- 专项测试命令：`$env:PYTHONPATH='src'; python -m pytest -q tests/test_psfb_step4_regression.py tests/test_psfb_duty_policy.py tests/test_psfb_duty_policy_baseline.py`
- 专项测试结果：`13 passed`
- PSFB contract 测试：`1 passed, 20 deselected`
- 编译检查：通过
- `git diff --check`：通过

### 第 4 步提交与同步记录

- 实现与回归证据 commit：`7bd3a91`（`PSFB Step 4: pass topology regression`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功
- 计划记录 commit：`85b7c1b`（`PSFB Step 4: finalize regression record`）
- 计划记录 push 结果：成功

第 5 步已完成。PSFB 专项验收证据已生成，原始 baseline 未覆盖；修复后
replay、duty 对比、checksum 和 validation report 均已保存。主迁移计划中
第 9 步的 PSFB boundary 引用已更新为“专项已收敛”，第 11、12 步仍保持
`in_progress`，并明确要求重跑修复后的全量 103 工况。

第 5 步专项验证：

- 证据脚本：`scripts/record_psfb_step5_evidence.py`
- replay：`migration/evidence/20260824/psfb_duty_policy/psfb_replay_results.json`
- duty 对比：`migration/evidence/20260824/psfb_duty_policy/psfb_duty_comparison.csv`
- validation report：`migration/evidence/20260824/psfb_duty_policy/psfb_validation_report.md`、`psfb_validation_report.json`
- 结果：7/7 executed、0 个修复后 boundary failure、0 个 execution error
- c02：`boundary_failure -> executed`
- 固定硬件：7 个工况共享 1 个 checksum，均与修复前 c01 硬件 checksum 一致
- 专项测试：`15 passed`
- 全量 103 工况：本步骤未重跑，主迁移计划仍保持 active

### 第 5 步提交与同步记录

- 实现与验收证据 commit：`87fcc3d`（`PSFB Step 5: record validation evidence`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功

### 修复后 PSFB 全部工况重跑记录（2026-08-24）

- 重跑结果：`migration/evidence/20260824/psfb_duty_policy/psfb_rerun_results_20260824.json`
- 重跑回归：`migration/evidence/20260824/psfb_duty_policy/psfb_rerun_regression_results_20260824.json`
- 覆盖：7/7 PSFB 工况
- 结果：7/7 `executed`、0 个 boundary failure、0 个 execution error
- 硬件：7 个工况共享 1 个 hardware checksum
- 重复性：case ID、输入、执行模式和硬件 checksum 与上一轮修复后结果一致
- 回归判定：所有 duty 数值有限，c02 boundary 已解决，7/7 主电流时间分区有效
- 专项测试：`15 passed`
- 本次仍未运行全量 103 工况，主迁移计划第 11、12 步保持 `in_progress`

---

### 第 5 步：更新 PSFB 验收证据和主计划状态

#### 工作内容

1. 生成 PSFB 专项 replay matrix、duty 对比表和 checksum 报告。
2. 更新 PSFB 7 工况的结构化输出和差异说明。
3. 将 PSFB 原始 boundary failure 更新为修复后的实际状态。
4. 更新主迁移计划第 9、11、12 步中的 PSFB 状态引用。
5. 明确本计划只完成 PSFB 专项修复；不据此直接宣称全量 103 工况验收完成。
6. 只有在 PSFB 专项测试和 7 工况 replay 都通过后，才将本计划状态改为
   `completed`。

#### 主要产出物

- `migration/evidence/20260824/psfb_duty_policy/psfb_baseline.json`
- `migration/evidence/20260824/psfb_duty_policy/psfb_replay_results.json`
- `migration/evidence/20260824/psfb_duty_policy/psfb_duty_comparison.csv`
- `migration/evidence/20260824/psfb_duty_policy/psfb_validation_report.md`
- `migration/evidence/20260824/psfb_duty_policy/psfb_validation_report.json`
- 主计划中第 9、11、12 步的更新记录。

#### 完成条件

- 7/7 PSFB 工况成功。
- 0 个 PSFB duty boundary failure。
- 所有修复行为有测试和 replay 证据。
- 本计划每一步均有独立 commit 和 push 记录。

#### 提交要求

完成验证后创建独立 commit 并 push，commit message 必须包含：

`PSFB Step 5: record validation evidence`

## 6. 通用提交和同步规则

每一步必须严格执行：

1. 修改代码、测试或证据文件。
2. 只运行本计划允许的 PSFB 相关验证。
3. 检查 `git diff`，排除缓存、`outputs/` 和无关文件。
4. 创建独立 commit。
5. push 到 `origin/codex/sync-gui-backend-from-2`。
6. 在本文件记录 commit hash、远端分支、push 时间、测试命令和结果。
7. push 成功后才允许将该步骤标记为 `completed`。

如果 commit 或 push 失败，该步骤必须保持 `in_progress`，不得伪造完成状态。

## 7. 预期结果

本计划完成后，预期得到：

- PSFB 7/7 工况执行成功。
- `c02_low_input_full_load` 不再触发 duty boundary failure。
- PSFB 当前工作点的 effective/command duty 口径一致。
- 固定硬件 refresh 的硬件选择保持不变。
- PSFB 专项证据可独立审计。
- 主迁移计划仍需在后续重新执行全量 103 工况后，才能重新评估第 11、12 步是否可以关闭。

## 8. 当前状态

`completed`

### 第 1 步执行结果（2026-08-24）

- 基线脚本：`scripts/freeze_psfb_duty_baseline.py`
- 基线目录：`migration/evidence/20260824/psfb_duty_policy/`
- 基线文件：`psfb_baseline.json`、`psfb_baseline.csv`
- PSFB 工况覆盖：7/7
- boundary failure：1 个，仅为 `c02_low_input_full_load`
- execution error：0 个
- 共享硬件 checksum：1 个，7 个工况均使用同一硬件快照
- 专项基线测试：`tests/test_psfb_duty_policy_baseline.py`
- 验证命令：`python scripts/freeze_psfb_duty_baseline.py`；
  `python -m pytest -q tests/test_psfb_duty_policy_baseline.py`

第 1 步的基线已冻结。

第 2 步已完成。已新增 PSFB 专用 `duty_policy.py`，将设计点和工作点
duty 语义分离，并由同一 policy 统一计算和审计 `effective_duty`、
`duty_loss`、`command_duty`。`synthesizer.py` 的设计点、低线和高线
duty 计算均已复用 policy；`primary_current_model.py` 的物理 duty 顺序
及 duty-loss 一致性检查也已复用 policy。policy 不静默 clamp，超出物理
范围或配置上限时返回明确的 boundary/invalid 状态。

第 2 步专项验证：

- 测试命令：`$env:PYTHONPATH='src'; python -m pytest -q tests/test_psfb_duty_policy.py tests/test_psfb_duty_policy_baseline.py`
- 结果：`8 passed`
- 编译命令：`python -m py_compile src/pe_claw_gui/topologies/dc_dc/phase_shifted_full_bridge_diode_rectifier_isolated/duty_policy.py src/pe_claw_gui/topologies/dc_dc/phase_shifted_full_bridge_diode_rectifier_isolated/synthesizer.py src/pe_claw_gui/topologies/dc_dc/phase_shifted_full_bridge_diode_rectifier_isolated/primary_current_model.py tests/test_psfb_duty_policy.py`
- 结果：通过
- `git diff --check`：通过

- 设计点回归：nominal、低线和高线 duty 数值与第 1 步冻结基线一致
- 覆盖：nominal、low-line、high-line、light-load、very-light-load、high-frequency、配置上限超限和非法 duty

第 3 步已完成。PSFB waveform 现在根据当前 operating point 的 `vin`、
`vout`、负载和开关频率调用统一 duty policy，并将同一组
`effective_duty`、`duty_loss`、`command_duty` 传入 primary-current model。
PSFB stress 优先读取 operating waveform 的 primary-current metadata；设备
刷新路径复用 duty policy，并保留设计点 `*_nom` 字段和 operating policy
字段。固定硬件 refresh 未重新选择器件，名义设计参数保持不变。

第 3 步专项验证：

- replay 脚本：`scripts/validate_psfb_step3_refresh.py`
- replay 证据：`migration/evidence/20260824/psfb_duty_policy/psfb_step3_refresh_results.json`
- replay 结果：`7/7 executed`、`0 boundary failure`、`0 execution error`
- 共享硬件 checksum：`1`，7 个工况一致
- 低输入验证：`effective_duty=0.780000`，`command_duty=0.8415613715672887`，`status=pass`
- 低输入设计点对照：`command_duty_nom=0.7293531886916502`，未再与 operating effective duty 混用
- 专项测试命令：`$env:PYTHONPATH='src'; python -m pytest -q tests/test_psfb_duty_policy.py tests/test_psfb_duty_policy_baseline.py`
- 专项测试结果：`11 passed`
- PSFB contract 测试：`1 passed, 20 deselected`
- 编译检查：通过
- `git diff --check`：通过

### 第 3 步提交与同步记录

- 实现 commit：`daf730d`（`PSFB Step 3: align operating-point duty`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功
- 计划记录 commit：`88db376`（`PSFB Step 3: record operating-point validation`）
- 计划记录 push 结果：成功

### 第 2 步提交与同步记录

- 实现 commit：`6c740b4`（`PSFB Step 2: define duty policy`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功
- 计划记录 commit：`74cf51c`（`PSFB Step 2: record duty policy validation`）
- 计划记录 push 结果：成功

### 第 1 步提交与同步记录

- 实现与基线 commit：`6ceb845`（`PSFB Step 1: freeze duty policy baseline`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 时间：`2026-08-24T18:28:32+08:00`
- 实现 push 结果：成功
- 验证命令：`python scripts/freeze_psfb_duty_baseline.py`；
  `python -m pytest -q tests/test_psfb_duty_policy_baseline.py`；
  `python -m py_compile scripts/freeze_psfb_duty_baseline.py tests/test_psfb_duty_policy_baseline.py`；
  `git diff --check`
- 验证结果：7/7 PSFB 工况基线，1 个已知 boundary，0 个 execution error；
  `3 passed`；编译通过；diff check 通过
- 步骤状态：`completed`

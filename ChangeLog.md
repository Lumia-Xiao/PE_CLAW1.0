# Change Log

## 2026-09-04 NPC 电感电流波形修正计划第七步

- 通过周期射击法求解三相三电平 NPC 工频周期稳态初始电流，使用阻尼固定点迭代，并将初值投影到三相三线制约束 `ia + ib + ic = 0`。
- 求解后以最终初值重新执行完整统一事件时间轴仿真，周期首尾不再依赖工频末端人工线性修正。
- 删除旧的 legacy 事件仿真副本和 `_integrate_phase_current_by_cycle()` 人工端点修正函数，避免旧路径重新被调用。
- 新增周期稳态求解 metadata 和专项测试；默认工况最大首尾残差约 `2.95e-9 A`，重复运行初值一致；低 `Vdc` 工况明确报告迭代未收敛及调制饱和。
- 验证：第七步专项 `7 passed`；NPC 专项与合同回归 `22 passed`；`py_compile`、`git diff --check` 通过。
- Git：第七步功能与文档 commit/push 回执待本次提交完成后补充。

## 2026-09-04 NPC 电感电流波形修正计划第六步

- 将 NPC 电流仿真改为逐开关周期的实际平均电流反馈校正：先生成三相电压候选序列，再在统一事件分段上积分实际电流。
- 使用每个周期的时间积分平均电流与正弦参考平均值比较，并按理想电感灵敏度 `2L/Tsw` 修正目标平均电压，最多执行 4 次内部迭代。
- 保持目标电压在 `+/-Vdc/2` 范围内，累计记录电压限幅、周期平均误差、迭代次数和剩余不可跟踪误差；没有增加 GUI 用户输入。
- 新增波形字段和 metadata：实际周期平均电流、平均误差及第六步校正审计信息。
- 验证：第六步专项测试 `5 passed`；默认工况最大周期平均电流误差约 `4.04e-11 A`，无调制饱和。

## 2026-09-04 NPC 电感电流波形修正计划第五步

- 将 NPC 候选三电平序列接入统一三相事件时间轴，按合并后的事件区间确定三相状态和公共模式相电压。
- 使用理想电感模型逐段积分，并对正弦电网电压使用解析积分；显示波形仍映射到既有时间轴和字段。
- 取消本路径的工频末端人工线性修正，新增统一事件时间轴、区间数量和分段积分方法 metadata。
- 新增正弦积分、统一事件时间轴、实际电流数组和无末端修正测试；更新旧合同测试以匹配第五步语义。
- 数值验收：默认输入下三相电流均值接近 `0 A`，三相电流和最大误差约 `2.61e-12 A`，周期首尾误差约 `1.18e-11 A`，默认工况无调制饱和。
- 验证：第五步及前四步、NPC 合同专项 `35 passed`；`compileall`、`git diff --check` 通过。
- Git：步骤 5 commit `fa01342` (`feat: integrate NPC current on unified event timeline`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`。

## 2026-09-04 NPC 电感电流波形修正计划第四步

- 将第三步的 NPC 平均相电压目标转换为 `D+、D0、D-` 三电平作用时间。
- 新增以零电平为起止的中心对称候选序列：正电压为 `0 -> +1 -> 0`，负电压为 `0 -> -1 -> 0`。
- 保持现有实际 PWM 波形和电流积分路径不变，候选序列通过 waveform metadata 提供给后续统一事件时间轴实现。
- 新增电平占空比、序列合法性、周期作用时间和无新增输入测试。
- 验证：第四步专项测试 `6 passed`；`compileall`、`git diff --check` 通过。
- Git：步骤 4 commit `9c49fbb` (`feat: add NPC three-level duty sequences`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`。

## 2026-09-04 NPC 电感电流波形修正计划第三步

- 按无电阻电感方程新增每相每个开关周期的平均逆变器电压目标：`v_grid_avg + 2L*(i_ref_avg-i_start)/Tsw`。
- 目标电压按 NPC `+Vdc/2` 和 `-Vdc/2` 范围限幅，并记录限幅状态、目标数组和计算方法 metadata。
- 保持当前实际 PWM 状态、电流积分逻辑、GUI 输入和损耗逻辑不变。
- 新增目标电压公式、时间平均电网电压、NPC 电压限幅及无新增输入测试。
- 验证：第三步及前两步、NPC 合同专项 `26 passed`；`compileall`、`git diff --check` 通过。
- Git：步骤 3 commit `d75b3aa` (`feat: calculate NPC average inverter voltage targets`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`。

## 2026-09-04 NPC 电感电流波形修正计划第二步

- 在 NPC waveform metadata 中保留三相瞬时正弦电流参考，并新增每个完整开关周期的时间加权梯形平均参考。
- 新增参考定义、平均方法、平均时间轴和周期平均数组，供后续平均电流控制及电压计算步骤复用。
- 保持原有 GUI 输入、PF 正负方向约定和实际 PWM 电流积分行为不变。
- 新增正负 PF、三相参考和为零及时间加权平均测试。
- 验证：第二步、NPC 合同和第一步基线专项 `22 passed`；`compileall`、`git diff --check` 通过。
- Git：步骤 2 commit `d3c8310` (`feat: add NPC switching-period current references`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`。

## 2026-09-04 NPC 电感电流波形修正计划第一步基线

- 新增 `scripts/record_npc_step1_baseline.py`，采集当前三相三电平 NPC 默认输入下的接口、波形、周期修正和开关事件基线。
- 新增 `tests/test_npc_step1_baseline.py`，验证基线可重复、NPC 波形字段完整且 JSON 可序列化。
- 测试临时输出约束为工程根目录 `pytest_temp`；设计结果目录 `outputs/` 不写入基线工具。
- 未修改 NPC 电流计算、GUI 输入或损耗公式。
- 验证：NPC 基线和合同专项 `18 passed`；`compileall`、`git diff --check` 通过。
- Git：步骤 1 commit `4d100f5` (`test: establish NPC current waveform baseline`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`。

## 2026-09-04 NPC 计划全量回归与收口

- 更新 NPC 目标集成测试，使连续工频电流波形的角色最大应力成为测试依据，不再使用连续积分修复前的历史开关峰值。
- 完成三相三电平 NPC 精确开关损耗六步计划的全量验收：`495 passed, 1 skipped`；步骤 6 DC-AC/NPC 回归 `28 passed`。
- `compileall`、`git diff --check` 和生成文件边界检查通过；未提交 `outputs/`、`pytest_temp/` 或缓存文件。
- Git：步骤 6 主 commit `2d91bb0` (`test: close NPC switching loss plan`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`；本条最终回执随后的记录提交完成。

## 2026-09-04 NPC 运行点、效率扫描和报告审计

- 为 `EfficiencySweepPoint` 增加可选的 `switching_loss_audit`，NPC 负载扫描和 PF 扫描的每个运行点都保存当前波形事件数、事件电流/阻断电压范围、软硬开通计数及工频平均公式。
- 将 NPC 事件审计摘要写入效率 CSV 和结构化报告；结构化报告同时保留负载点和 PF 点的同源摘要。
- 更新 GUI 损耗视图，显示实际事件电流、阻断电压、负电流软开通、`Psw=sum(Eon+Eoff)/Tline` 以及 SiC 反向恢复为零的计算依据。
- 保持原有 GUI 输入字段不变，开关频率仍来自 `fsw_hz`。
- 验证：NPC 扫描/报告专项 `16 passed`；结构化输出和 GUI 效率回归 `6 passed`；`compileall` 和 `git diff --check` 通过。
- Git：步骤 5 主 commit `bb76778` (`feat: audit NPC switching loss across sweeps`) 已成功推送至 `origin/codex/npc-output-run-isolation-step1`；本条回执随后的记录提交待完成。

## 2026-09-04 NPC 精确开关损耗最小实现计划

- 新建 `Plan/Active/three_phase_three_level_npc_switching_loss_plan.md`，将三相三电平 NPC 精确开关损耗收敛为 6 个实施步骤。
- 删除已被替代的 `Plan/Active/three_phase_three_level_npc_revision_plan.md`。
- 明确保持原有 GUI 用户输入，不新增字段；开关频率继续使用既有 `fsw_hz`。
- 明确每个步骤必须验证、更新计划和 ChangeLog、独立 commit 并 push 后才可完成。
- 本次仅变更计划文档，未修改计算代码，未删除 `outputs/` 或其他用户生成结果。
- 验证：计划文件切换和工作区边界检查通过；待本计划切换提交后记录 commit/push 回执。

## 2026-09-04 NPC 连续工频电流波形

- 修正 `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py`，使 NPC 相电感电流在整个工频周期连续积分，不再在每个 PWM 周期重新锚定基波电流。
- 增加周期稳态线性修正及其 metadata 审计字段，保留开关纹波和原有用户输入契约。
- 增加 NPC 连续积分边界测试。
- 验证：NPC 契约测试 `11 passed`；受影响 DC-AC 回归 `20 passed`；`compileall` 和 `git diff --check` 通过。
- Git：本步骤 commit `12f1180da9bde5193ad8a944bc0f8fc00497a314` 已成功推送至 `origin/codex/npc-output-run-isolation-step1`，远端 HEAD 已核对一致。

## 2026-09-04 NPC 实际开关事件提取

- 在 `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py` 增加 12 路有源开关的门极边沿提取。
- 对事件时间、三相有符号电感电流和上下分裂母线阻断电压进行线性插值，写入现有 waveform metadata。
- 保持 GUI 用户输入不变，未新增字段。
- 验证：NPC 契约测试 `12 passed`；受影响 DC-AC 回归 `21 passed`；`compileall` 和 `git diff --check` 通过。
- Git：本步骤 commit `0334142b64030c9e472c12cadff6713e7161d6e5` 已成功推送至 `origin/codex/npc-output-run-isolation-step1`，远端 HEAD 已核对一致。

## 2026-09-04 NPC 事件级器件开关能量入口

- 在 `src/pe_claw_gui/engines/devices/loss_evaluator.py` 增加 NPC 单事件和事件列表能量计算入口。
- 负电流开通事件按软开关处理并令 `Eon=0`；正电流开通和关断使用事件实际电流、阻断电压及现有器件模型。
- SiC 器件反向恢复事件能量置零；其他拓扑的既有损耗入口保持不变。
- 增加 NPC 事件级极性、电流和 SiC 反向恢复测试。
- 验证：相关专项与器件回归 `27 passed`；受影响 DC-AC/器件回归 `38 passed`；`compileall` 和 `git diff --check` 通过。
- Git：本步骤 commit `0a63c2187133b6177be27941fbb1ce11f7e4c54e` 已成功推送至 `origin/codex/npc-output-run-isolation-step1`，远端 HEAD 已核对一致。

## 2026-09-04 NPC 工频事件损耗汇总接入

- 在 `src/pe_claw_gui/engines/devices/stress_adapter.py` 中使用 NPC 事件电流更新开通/关断代表值。
- 在 `src/pe_claw_gui/pipeline/run_device_pipeline.py` 中将 NPC 事件 Eon/Eoff 按 6 个物理位置和工频周期汇总到每位置损耗；并联方案先分摊事件电流，SiC 反向恢复损耗置零并保留正向导通损耗。
- 增加公式级测试，核对报告损耗与事件能量汇总一致且没有额外乘 6。
- 保持 GUI 用户输入和其他拓扑损耗逻辑不变。
- 验证：NPC 契约 `15 passed`；其余受影响 DC-AC/器件回归 `24 passed`；此前完整效率扫描回归 `55 passed`；公式级事件汇总断言通过；`compileall` 和 `git diff --check` 通过。
- Git：本步骤 commit `80026241d31fe5a3129fdfab9fad5200428fe324` 已成功推送至 `origin/codex/npc-output-run-isolation-step1`，远端 HEAD 已核对一致。

This file records meaningful repository changes. Entries are chronological and
append-only. Generated caches and ordinary runtime output generation are not
listed here.

## 2026-09-04 Pytest Temporary Output Verification

- Fixed the GUI end-to-end test's isolated subprocess cleanup and updated its
  assertions for date/alias/short-ID run directories under `pytest_temp`.
- Fixed hardware-overview hotspot extraction when efficiency is run before
  thermal design has produced a recommended estimate.
- Updated the LLC efficiency artifact test to use the current run-scoped CSV
  location.
- Validation: the two previously failing tests passed; syntax and diff checks
  passed; focused regression passed (`36 passed`); full regression passed
  (`489 passed, 1 skipped`).

## 2026-09-03 All-Topology Design Output Isolation

- Added an active `DesignRunContext` resolver so topology internals, operating-point refresh, device stress refresh, capacitor refresh, efficiency sweep, loss refresh, and full-pipeline execution share one isolated run directory.
- Routed AC-DC rectifier synthesis and refresh waveform artifacts into the current run's `validation` directory.
- Prevented GUI capacitor, inductor, and hardware-overview views from loading public legacy artifacts for reports that carry a run context.
- Added cross-topology isolation tests for single-phase and three-phase AC-DC rectifier synthesis.
- Required future topologies to use the shared run context and documented the commit/push rule in the active NPC plan.
- Validation: focused output-isolation, LLC context, AC-DC topology, and AC-DC efficiency tests passed; full-suite execution was affected by the host pytest temporary-directory permission conflict.

## 2026-09-03 Short Run Directory Names

- Changed new run directories to `YYYYMMDD_<topology_alias>_<run_id_8>`.
- Kept the full topology ID and full run ID in the manifest and design request for traceability.
- Added explicit aliases for registered topologies and a generic abbreviation fallback for future topology plugins.
- Existing output directories are intentionally left unchanged.
- Validation: output-isolation tests cover date-only naming, eight-character run IDs, and future-topology fallback naming.

## 2026-09-03 Repository-Local Pytest Temporary Directory

- Added `pytest_temp/` to `.gitignore` so pytest-generated files and caches are not committed.
- Recorded the repository-local pytest temporary-directory rule in the active NPC plan.

## 2026-09-03 Pytest Temporary Path Cleanup

- Updated LLC and GUI tests that created temporary files directly under the repository root to use pytest `tmp_path` fixtures.
- Kept read-only historical evidence and existing user design outputs unchanged.
- The affected tests now place generated files below the configured `pytest_temp/` base directory.

## 2026-09-03 Pytest Temporary Path Boundary Scan

- Updated the AC-DC GUI end-to-end test to use its pytest `tmp_path` as the subprocess output root.
- Scanned tests for repository-root temporary output paths; remaining `outputs` and `migration` references are read-only historical evidence.

## 2026-08-28 AC-DC Efficiency Sweep Step 12 Real GUI Delivery

- What changed:
  - Replaced the synthetic AC-DC GUI result test with a real isolated
    `PEClawMainWindow` five-topology button-chain test.
  - Drove real design, capacitor, required magnetics, waveform, and efficiency
    controllers without mocking `run_efficiency_sweep`.
  - Retained ten production-generated GUI efficiency artifacts and recorded
    their sizes and SHA-256 values.
  - Added the Step 12 delivery report and machine-readable manifest.
- Validation:
  - Final real GUI chain: `3 passed` in `404.71s`.
  - AC-DC: `32 passed`; DC-AC: `64 passed`; DC-DC/PSFB: `25 passed`.
  - GUI/packaging: `14 passed`.
  - Full suite: `343 passed, 1 skipped`; no failures or errors.
  - Compileall and `git diff --check`: passed.
- Git:
  - Steps 10 and 11 are present on `origin/codex/sync-gui-backend-from-2`.
  - Step 12 subject commit `4af87e6fa93711f00d83017a7f33825b1d1dc9a1`
    is present on `origin/codex/sync-gui-backend-from-2`.
  - This independent receipt archives the completed plan and records remote
    containment.
  - Merge, tag, release, and `master` push are outside this step.

## 2026-08-28 AC-DC Step 12 Closeout Correction

- What changed:
  - Added explicit real-GUI assertions for stress and topology results.
  - Added a real GUI partial-load-failure check proving that a failed point
    does not discard the valid point, warning text, Efficiency page, or plots.
  - Recorded the Step 12 receipt commit and final receipt remote HEAD in the
    delivery manifest, report, and completed plan.
  - Clarified that the plan's earlier "steps 10-12 pending" text is a historical
    Step 9 state rather than the current final status.
- Validation:
  - Corrected real GUI module: `3 passed in 402.08s`.
  - Corrected AC-DC focused group: `32 passed in 766.79s`.

## 2026-08-27 DC-AC Migration Step 10 Packaged GUI Runtime

- What changed:
  - Restored the shared `BaseTopologyForm` numeric parsing helpers required by
    DC-AC operating-point controls.
  - Added packaged GUI runtime coverage for editable installation, target
    package/resource resolution, Windows launcher startup, and the three DC-AC
    design-to-waveform GUI flows.
  - Recorded Step 10 startup and GUI smoke evidence.
- Why:
  - The first packaged GUI smoke exposed an `AttributeError` when the single-phase
    full-bridge form read its default operating point. The missing shared helper
    also affected both three-phase inverter forms.
- Files:
  - `src/pe_claw_gui/app/topology_forms/base_form.py`
  - `tests/test_dc_ac_packaged_gui_runtime.py`
  - `migration/evidence/20260827/step10_dc_ac/packaged_gui_runtime_validation.json`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - Editable install in isolated `.step10-venv`: passed.
  - Packaged runtime: 19 registered topologies, 3 DC-AC topologies, 3 DC-AC
    resources, and Windows launcher startup check passed.
  - GUI/package regression: `26 passed`.
  - `python -m compileall -q src tests`: passed.
  - `git diff --check`: passed.

## 2026-08-27 DC-AC Migration Step 6 Three-Phase Three-Level NPC Contract

- What changed:
  - Added target-engineering contract coverage for the three-phase three-level NPC inverter.
  - Covered PD level-shifted SPWM, 12 active-switch positions, six clamp-diode positions,
    split upper/lower DC-link capacitor data, NPC role stress, operating-point refresh, and GUI controls.
  - Preserved first-pass limitations for neutral-point balancing, dead-time, Coss, commutation overlap,
    and parasitic transients.
  - Marked Step 6 completed in the active migration plan after remote push verification.
- Why:
  - The target NPC runtime and form already match the source implementation; this step locks the
    migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_three_phase_three_level_npc_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_three_phase_three_level_npc_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 16 passed.
  - Implementation commit: `2ebc79fc08e8df0d1bb81dc726d1eb3f710a5b98`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

## 2026-08-27 DC-AC Migration Step 5 Three-Phase Two-Level VSI Contract

- What changed:
  - Added target-engineering contract coverage for the three-phase two-level voltage-source inverter.
  - Covered line-line RMS input normalization, six-switch SPWM metadata, phase voltage/current and
    DC-link current waveforms, waveform-backed stress, operating-point refresh, and GUI controls.
  - Marked Step 5 completed in the active migration plan after remote push verification.
- Why:
  - The target three-phase two-level VSI runtime and form already match the source implementation;
    this step locks the migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_three_phase_two_level_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_three_phase_two_level_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 16 passed.
  - Implementation commit: `209807872d3095cc464b45c194c01933b3704837`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

## 2026-08-27 DC-AC Migration Step 4 Single-Phase Full-Bridge Contract

- What changed:
  - Added target-engineering contract coverage for the single-phase full-bridge inverter.
  - Covered CCM and TCM input boundaries, unipolar-SPWM/refined waveform metadata, switch stress,
    full-pipeline report assembly, operating-point refresh, and GUI form fields.
  - Marked Step 4 completed in the active migration plan after remote push verification.
- Why:
  - The target single-phase full-bridge runtime and form already match the source implementation;
    this step locks the migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_single_phase_full_bridge_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 17 passed.
  - Implementation commit: `3fe828f5cdbd64dfbacf0bd0ecca6f0b0690ee16`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

## 2026-08-27 DC-AC Migration Step 0 Baseline

- What changed:
  - Recorded the source/target repository baseline and dedicated DC-AC Step 0 evidence.
  - Created the weekly target backup and documented preserved untracked outputs.
  - Made `scripts/backup_weekly.ps1` compatible with the active Windows PowerShell runtime.
- Why:
  - Establish a recoverable, independently auditable starting point before runtime migration.
- Files:
  - `migration/phase0/dc_ac_step0_baseline.md`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `scripts/backup_weekly.ps1`
  - `ChangeLog.md`
- Validation:
  - DC-AC registry: 3 implemented topologies.
  - `python -B -m compileall -q src/pe_claw_gui`: passed.
  - DC-AC migration, topology, GUI integration, and GUI bootstrap tests: 12 passed.
  - GUI startup smoke: passed.
  - Full pytest collection: 267 tests collected.
  - Weekly ZIP opened and manifest read; SHA-256 `3E3395A51F3EF47505899887480C27A2B6CE6C2C8D7099BF3AB209CB374C7A2A`.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `faf5e3f06f2874a25d106a68144c5cc78eeb6032` (`chore: record dc-ac migration baseline`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 1 Dependency Matrix

- What changed:
  - Added the current-baseline DC-AC file, import, static-resource, test, and exclusion matrix.
  - Added the matrix summary with explicit ownership, merge/adapt steps, and prohibited dependency audit.
  - Updated the active migration plan to mark Step 1 in progress.
- Why:
  - Freeze the migration boundary before changing shared runtime contracts or copying implementation files.
- Files:
  - `migration/phase1/dc_ac_dependency_matrix.csv`
  - `migration/phase1/dc_ac_dependency_matrix_summary.md`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - CSV parsed with 58 rows, 11 columns, and 0 malformed rows.
  - Classification counts: keep 24, merge 11, adapt 12, add 3, exclude 8.
  - No `review_required` rows.
  - Source/target hash and file-ownership scans completed.
  - Deterministic DC-AC runtime prohibited-import scan found no agentic/AI/skills imports.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `f9c85d58c38d86b4d4d3bc410879ce7333ddf097` (`docs: add dc-ac migration dependency matrix`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 2 Shared Contracts

- What changed:
  - Exported `TopologyCapability` and `get_topology_capability` from the public topology package.
  - Added DC-AC shared-contract tests for registry, capabilities, models, and package data.
  - Updated the active migration plan to mark Step 2 in progress.
- Why:
  - Make the DC-AC runtime contract explicit and testable before topology registry and GUI routing changes.
- Files:
  - `src/pe_claw_gui/topologies/__init__.py`
  - `tests/test_dc_ac_shared_contracts.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Shared-contract, Phase 2 packaging, Phase 3 shared-contract, and Phase 4 topology tests: 33 passed.
  - DC-AC topology and GUI bootstrap regression: 7 passed.
  - `python -B -m compileall -q src/pe_claw_gui tests/test_dc_ac_shared_contracts.py`: passed.
  - Deterministic runtime prohibited-import scan: passed.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `01a2d1fa76a36d448ccf7826b61d30dd58e41612` (`refactor: merge shared dc-ac runtime contracts`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 3 Registry And Category

- What changed:
  - Removed placeholder wording from the DC-AC category page and fallback label.
  - Added registry, form, category hint, packaged-image, and source-path contract tests.
  - Updated the active migration plan to mark Step 3 in progress.
- Why:
  - Lock the three implemented DC-AC topology entries and package-resource boundary before controller migration.
- Files:
  - `src/pe_claw_gui/app/category_views/dc_ac_page.py`
  - `tests/test_dc_ac_registry_category.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Registry/category/resource, shared-contract, topology, and GUI integration tests: 33 passed.
  - `python -B -m compileall -q src/pe_claw_gui tests/test_dc_ac_registry_category.py`: passed.
  - Source absolute-path scan for registry/category/resource runtime: passed.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `00b408aad6afac72f12d95c8a4ca43f9c1e1b33c` (`feat: register dc-ac topology family`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-26

- What changed:
  - Added repository-wide `AGENTS.md` rules for LLM-assisted development.
  - Added the append-only `ChangeLog.md` policy and initial entry.
  - Added `scripts/backup_weekly.ps1` for dated weekly ZIP backups.
- Why:
  - Establish consistent engineering, validation, backup, and documentation
    rules for future changes.
- Files:
  - `AGENTS.md`
  - `ChangeLog.md`
  - `scripts/backup_weekly.ps1`
- Validation:
  - Reviewed the repository layout, migration evidence authority, Git rules,
    test configuration, and generated-output policy.
- Git:
  - Implementation commit: `20da8cc` (`docs: add agent rules changelog and weekly backup`).
  - This metadata update is committed separately after the implementation commit.
- Backup:
  - No weekly archive was generated by this documentation change.
## 2026-08-27

- What changed:
  - Connected DC-AC Generate Waveforms to current-form synchronization and operating-point refresh.
  - Added topology-specific DC-AC waveform renderers and summary/stress readback for the single-phase full bridge, three-phase two-level VSI, and three-level NPC inverter.
  - Added focused tests for redesign-on-input-change, fixed-hardware refresh, and topology-specific result labels.
- Validation:
  - `tests/test_dc_ac_operating_refresh_gui_chain.py`: 5 passed.
  - DC-AC registry/shared/topology contract suite: 37 passed.
  - `tests/test_phase7_dc_ac_migration.py tests/test_phase9_dc_ac_topologies.py`: 7 passed.
  - `python -B -m compileall -q src tests`: passed.
  - `git diff --check`: passed.
- Git:
  - Step implementation commit: `342ebf8f973089b94e14e957d56fd29b54646701` (`feat: connect dc-ac waveform refresh and result views`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 11 Final Acceptance

- What changed:
  - Added a reproducible Step 11 evidence builder for source/target DC-AC probes,
    field-level comparison, acceptance matrix, changed-file inventory, and
    runtime path/dependency scans.
  - Added the final DC-AC acceptance evidence under
    `migration/evidence/20260827/step11_dc_ac/`.
  - Updated the active plan with the final validation classifications and
    evidence paths while leaving the remote receipt pending until push.
- Why:
  - Close the DC-AC migration with auditable evidence for all three topologies
    and classify full-suite failures, errors, skips, and warnings explicitly.
- Files:
  - `scripts/build_dc_ac_step11_evidence.py`
  - `migration/evidence/20260827/step11_dc_ac/`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Focused DC-AC, operating refresh, GUI, device, capacitor, magnetic, loss,
    and efficiency regression: `183 passed, 1 skipped`.
  - Full suite with repository-local basetemp: `323 passed, 1 skipped` in
    `1018.49s`; `0 failures`, `0 errors`, and `0 warnings`.
  - The one skip is the optional legacy external OpenMagnetics reference path;
    the packaged normalized production magnetic chain passed.
  - Source/target deterministic comparison: 3 topologies, 45 fields,
    0 differences at 1e-9 relative tolerance or exact nonnumeric equality.
  - Runtime source-workspace absolute-path scan: 0 hits.
  - Runtime AI/agentic/skills import and package-directory scan: 0 hits.
  - `python -B -m py_compile scripts/build_dc_ac_step11_evidence.py`: passed.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Planned step commit: `docs: finalize dc-ac migration evidence and acceptance`.
  - Commit and push receipt are recorded in a separate plan update after the
    implementation push succeeds.

## 2026-08-27 DC-AC Migration Step 12 Delivery Archive

- What changed:
  - Added a reproducible DC-AC delivery manifest and user-acceptance checklist.
  - Verified the Step 0 through Step 11 commit chain and checksummed the focused
    Step 9 through Step 11 evidence set.
  - Documented the dedicated 2026-08-27 DC-AC evidence authority and release
    boundary in `migration/README.md`.
  - Moved the DC-AC migration plan from `Plan/active` to `Plan/completed` with
    Step 12 kept in progress until the subject commit is pushed and verified.
- Why:
  - Close the dedicated migration as an auditable delivery without treating
    plan completion as permission to merge, tag, release, or push to `master`.
- Files:
  - `scripts/build_dc_ac_step12_delivery.py`
  - `migration/evidence/20260827/step12_dc_ac/`
  - `migration/README.md`
  - `Plan/completed/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Delivery manifest generator verifies the pre-Step-12 local/remote commit
    `9268813a6e7d8a0e86b31c3afb47577075b63ef4` and the expected migration
    commit chain.
  - DC-AC registry, target integration, packaged GUI, and AI-isolation smoke
    tests are rerun before the Step 12 commit.
  - Compileall, runtime source-path scan, agentic/AI import scan, plan archive
    checks, and `git diff --check` are required before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Planned step commit: `docs: archive dc-ac migration delivery`.
  - Merge, tag, release, and `master` push are not part of this step.

## 2026-08-27 DC-AC Step 12 Manifest Reproducibility Repair

- What changed:
  - Updated the Step 12 delivery generator to validate the final archived
    `completed` plan instead of the temporary pre-receipt state.
  - Added the Step 12 subject and receipt commits to the verified chain, for a
    total of 26 migration subject/receipt commits through delivery closure.
  - Regenerated the final manifest with the current archived-plan SHA-256 and
    explicit Step 12 closure commits.
- Why:
  - The original generator intentionally targeted the pre-push state and could
    not be rerun after the plan and remote branch reached their final state.
- Validation:
  - Two consecutive generator runs produced byte-identical manifest SHA-256
    `D08CDD2D3B353FF3112C3E05588E279D0395E71C2348CB1677319CCE2AFA5614`.
  - Manifest contract `dc_ac_step12_delivery_manifest_v2` records 26 commits,
    Step 12 subject/receipt hashes, and the current archived-plan SHA-256.
  - The generator verifies local and remote ancestry from the Step 12 receipt;
    `origin/master` does not contain Step 12 and no containing tag exists.
  - DC-AC delivery smoke: `23 passed`.
  - Manifest evidence hashes: 0 mismatches; runtime source-path and AI/agentic
    import scans: 0 hits; compileall and `git diff --check`: passed.

## 2026-08-28 AC-DC Efficiency Sweep Final Delivery

- What changed:
  - Added the final AC-DC efficiency-sweep repair report and machine-readable
    delivery manifest.
  - Recorded the before/after failure matrix, fixed-hardware prerequisites,
    evaluator dispatch, included loss paths, artifacts, validation results,
    commit chain, push state, and remaining modeling limits.
  - Archived the completed nine-step plan under `Plan/completed/` and updated
    the migration evidence index.
- Validation:
  - AC-DC focused regression: `27 passed`.
  - DC-AC regression: `64 passed`.
  - DC-DC and PSFB regression: `25 passed`.
  - GUI and packaging chain: `13 passed`.
  - Full suite: `338 passed, 1 skipped`; no failures or errors.
  - JSON parsing, commit-chain ancestry, remote-head, artifact inventory,
    syntax, and whitespace checks are required before the delivery commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step 9 subject commit: `e95183924f871745bfec624ad4857faa24744c91`
    (`docs: finalize AC-DC efficiency sweep delivery`).
  - Subject push passed and the remote branch containment check succeeded; this
    metadata update is the independent push receipt.
  - Merge, tag, release, and `master` push are outside this step.

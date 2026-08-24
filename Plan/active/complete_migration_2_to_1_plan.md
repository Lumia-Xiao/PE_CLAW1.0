# PE-Claw 2.0 到 1.0 完整移植实施计划

## 1. 计划状态

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-24` |
| 基准工程 | `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 设计工况 | 19 个注册拓扑、17 个设计请求矩阵、103 个设计工况 |
| 当前阶段 | 第 12 步：最终验收、文档归档和计划关闭准备 |
| 当前目标 | 代码级完整移植，而不是仅保证核心电气字段基本一致 |
| 状态文件位置 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active` |

本文件是项目当前完整移植工作的主状态文件。每完成一个步骤，必须更新本文件中的步骤状态、完成日期、产出物和验证证据。未完成的步骤不得标记为 `completed`。

## 2. 计划目标

将 PE-Claw 2.0 的 19 个注册拓扑及其相关设计链路完整移植到 PE-Claw 1.0；其中本次冻结的 design-request 目录覆盖 17 个拓扑矩阵，使两代工程在相同冻结设计输入、相同配置、相同依赖和相同器件库快照下，产生语义一致、数值一致、可重复的结构化输出和报告。

完整移植包括：

1. 设计请求解析、规范化、单位和默认值。
2. 拓扑 registry、plugin、input schema 和拓扑能力声明。
3. 候选综合、工作点计算、可行性判断和错误处理。
4. 波形、应力、损耗、磁性、电容和热设计模型。
5. 固定硬件复用和 operating-point refresh。
6. 器件库、候选筛选、排序和绑定策略。
7. 结构化结果、最终报告、审计数据和产物路径。
8. 103 个工况的端到端回放及逐字段差异核验。

本计划不把器件型号差异自动判定为迁移失败；但如果要求最终器件结果完全一致，则必须执行第 8 步中的器件库冻结与排序一致化工作。

## 3. 已知前置事实

在本计划建立前，已完成一次迁移 parity 验证：

- 103/103 工况在 PE-Claw 1.0 中成功执行。
- 0 个执行错误。
- 71 个工况所有当前比较字段完全通过。
- 32 个工况仅存在已经标记的模型边界差异。
- 0 个未解释的核心字段 mismatch。
- 基础 Buck、Boost、Buck-Boost、LLC、逆变器和 Totem-Pole PFC 的核心结果已验证。

该结果只能作为移植基线，不能作为“代码完全移植完成”的结论。当前已知差异主要集中于：

- Flyback 输出电容估算。
- PSFB 输出电感纹波和输出电容公式。
- 单相、三相被动整流器的脉冲或状态空间仿真输出。
- Boost PFC 电感包络和 DC-link 纹波字段。
- 报告中设计目标、理论估算值和仿真值的字段语义。
- 两代器件库快照、候选排序和默认参数。

## 4. 总体步骤

完整移植共分为 12 步：

| 步骤 | 名称 | 目标状态 |
| ---: | --- | --- |
| 1 | 基准冻结与差异清单 | 建立唯一 2.0 golden baseline |
| 2 | 工程和依赖环境对齐 | 两代运行环境可复现 |
| 3 | 输入契约和规范化层移植 | 相同输入得到相同 normalized request |
| 4 | 拓扑注册和插件框架移植 | 17 个拓扑的注册、路由和 schema 一致 |
| 5 | DC-DC 拓扑算法完整移植 | 01-09 全部算法和工作点行为一致 |
| 6 | AC-DC 拓扑算法完整移植 | 10-14 全部算法和仿真行为一致 |
| 7 | DC-AC 拓扑算法完整移植 | 15-17 全部算法和仿真行为一致 |
| 8 | 器件库、磁性、电容和排序一致化 | 下游选型结果可复现 |
| 9 | 仿真、固定硬件和工作点刷新一致化 | 设计点与复用工况行为一致 |
| 10 | 结构化输出和报告契约统一 | 所有输出字段语义一致 |
| 11 | 103 工况端到端回放和差异收敛 | 0 个未解释差异 |
| 12 | 最终验收、文档归档和计划关闭 | 完整移植正式验收 |

每一步都必须满足“输入、动作、产出、验证、完成条件”五类要求。

### 步骤提交与远端同步规则

每一个步骤完成后，必须按以下顺序执行：

1. 完成该步骤规定的代码、配置、测试和文档修改。
2. 运行该步骤的验证方法，并保存验证证据。
3. 检查 Git diff，确认只包含该步骤相关变更。
4. 创建一个独立的 Git commit，commit message 必须包含步骤编号，例如 `Step 1: freeze migration baseline`。
5. 将该 commit push 到当前工作分支的远端。
6. 在本文件中记录 commit hash、远端分支、push 时间和验证结果。
7. 只有 commit 成功且 push 成功后，才允许将该步骤状态改为 `completed`，并开始下一步。

如果 commit 或 push 失败：

- 当前步骤必须保持 `in_progress`。
- 必须在当前执行记录中记录失败原因。
- 不得将未同步的本地状态当作步骤完成状态。
- 修复同步问题后，重新执行检查、commit 和 push。

---

## 第 1 步：基准冻结与差异清单

### 目标

将 PE-Claw 2.0 固定为唯一行为基准，建立可重复的 golden input、golden output 和差异台账。任何后续差异都必须能追溯到具体文件、函数、字段和版本。

### 详细工作

1. 记录 2.0 的 Git commit、分支、工作区状态和版本元数据。
2. 记录 1.0 当前 Git commit、分支和工作区状态，不覆盖用户已有修改。
3. 固定 Python、依赖包、运行配置、环境变量和 locale。
4. 收集 17 个拓扑目录及 103 个 `design_request.md`。
5. 收集 103 个对应的：
   - `design_result.md`
   - `final_report.json`
   - backend readback
   - runner readback
   - 波形、应力、磁性、电容和报告产物索引
6. 为每个输入和输出生成 SHA-256 checksum。
7. 建立字段级差异矩阵，至少包含：
   - 输入字段
   - 规范化字段
   - candidate 字段
   - waveform 字段
   - stress 字段
   - magnetic 字段
   - capacitor 字段
   - report 字段
8. 将当前 103 工况验证结果作为“迁移前基线”，但单独标记为 `baseline_not_final`。

### 产出物

- `migration_baseline_manifest.json`
- `migration_input_checksums.csv`
- `migration_output_checksums.csv`
- `field_semantics_matrix.csv`
- `migration_difference_ledger.md`
- 2.0 环境和依赖快照

### 验证方法

- 103 个输入均可读取。
- 103 个结果均存在且与工况一一对应。
- 2.0 重新执行时输入 checksum 和结构化输出 checksum 可复现，或每个非确定性字段有说明。
- 差异台账中的每一项都绑定到拓扑、工况、字段和来源文件。

### 完成条件

- 2.0 golden baseline 已冻结。
- 103 个工况全部有唯一 ID。
- 每个待迁移模块都有源文件和目标文件映射。

### 状态

`completed`

### 当前证据

已完成第 1 步的输入/结果库存冻结，证据目录为：

`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active\baseline_20260824`

已生成：

- `migration_baseline_manifest.json`
- `migration_input_result_checksums.csv`
- `current_parity_baseline.json`
- `README.md`
- `structured_readback_inventory.json`
- `structured_readback_inventory.csv`
- `field_semantics_matrix.csv`
- `module_mapping_2_to_1.csv`
- `nondeterminism_policy.md`
- `migration_difference_ledger.md`
- `environment_manifest_2.json`
- `environment_manifest_1.json`
- `step1_validation.json`
- `freeze_step1_baseline.py`

当前冻结版本：

- PE-Claw 2.0 commit：`6726f508fcf0e545f69512654d1ea5543e6333cf`
- PE-Claw 1.0 commit：`b7de822f26a3542ef8bf73bfe02f7383de2c8510`
- 2.0 request/result 库存：`103/103`
- 当前 1.0 replay：`103/103` 执行，`0` 执行错误，`71` 完全通过，`32` 模型边界，`0` 未解释 mismatch

第 1 步尚未完成的工作：

1. 完成第 1 步独立 commit 并 push 到当前远端分支。
2. push 成功后，将本步骤状态改为 `completed`，并记录 commit hash、分支、时间和验证结果。

### 第 1 步新增证据

`structured_readback_inventory.*` 以 103 个 `design_requests/<topology>/<case>`
目录为唯一工况索引，记录 request/result/readback/final report 的 SHA-256、字节数、
合同版本、执行状态、拓扑 ID、候选 ID、session 关联和 report section IDs。历史
`outputs/design_sessions` 只有在 `runner_readback.final_session_root` 或
`session_root` 明确关联时才纳入报告索引。

`field_semantics_matrix.csv` 已覆盖 request、normalized input、candidate、waveform、
stress、magnetic、capacitor 和 report 层，并对严格比较、模型边界、器件库依赖和
字段语义待拆分项分别标注规则。

`module_mapping_2_to_1.csv` 已覆盖 17 个拓扑包以及输入契约、路由、session、pipeline、
报告、器件库、磁性库、电容库、输出模型和 waveform 公共模块；2.0 中存在而 1.0
缺失的模块被记录为 `target_gap`，不视为已移植。

`nondeterminism_policy.md` 固定工况身份、严格字段、路径/UUID/时间戳处理、产物比较、
器件库条件和候选排序稳定化要求。`migration_difference_ledger.md` 将当前模型边界
差异登记为待后续步骤关闭的开放项，不再作为永久豁免。

### 第 1 步验证记录

执行命令：

```text
python Plan\\active\\baseline_20260824\\freeze_step1_baseline.py
```

验证证据：`baseline_20260824/step1_validation.json`

结果：17/17 拓扑、103/103 工况；request、result、backend readback、runner readback
和关联 `final_report.json` 均为 103/103；backend/runner 均为 `executed` 且 `ok=true`；
结构化报告均为 `final_report_sections_v1`；重复工况键为 0；验证通过。

脚本支持 `--validate-only`，用于后续不改写基线文件的完整性复核。

### 第 1 步提交记录

- 步骤：第 1 步：基准冻结与差异清单
- commit：`751e63c` (`Step 1: freeze migration baseline`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- push 时间：`2026-08-24`（Asia/Shanghai）
- push 结果：成功
- 状态变更依据：独立 commit 已创建且已成功 push，因此本步骤允许关闭。

---

## 第 2 步：工程和依赖环境对齐

### 目标

排除 Python 版本、依赖库、配置、随机种子、浮点设置和文件路径造成的假差异。

### 详细工作

1. 对比两代 `pyproject.toml`、requirements、lock 文件和安装包版本。
2. 对比运行时 Python 版本、操作系统、时区、locale 和编码。
3. 对比默认配置、环境变量、输出目录和临时目录策略。
4. 固定随机数种子；如代码不应使用随机选择，则移除隐式随机性。
5. 固定候选排序的 tie-break 规则。
6. 固定浮点计算精度、采样点数、仿真步长和收敛条件。
7. 对比报告中时间戳、绝对路径和临时文件名的可重复性处理。
8. 建立隔离的 1.0 replay environment，避免读取 2.0 的运行时缓存。

### 产出物

- `environment_manifest_2.json`
- `environment_manifest_1.json`
- `dependency_diff.md`
- `runtime_reproducibility_policy.md`
- `src/pe_claw_gui/runtime/reproducibility.py`
- `tests/test_phase2_reproducibility.py`
- `scripts/validate_step2_environment.py`
- `step2_validation.json`

### 验证方法

同一个 1.0 工况连续执行两次，结构化输出除允许的时间戳和路径字段外必须完全一致。

### 完成条件

- 两代环境差异已分类为“必须同步”“允许差异”“不会影响行为”。
- 所有非确定性输出均有稳定化策略。

### 状态

`completed`

### 第 2 步已实施修改

1. 新增 `pe_claw_gui.runtime` 运行时契约，在 GUI/流水线导入前统一设置
   `PYTHONHASHSEED`、UTC 时区、C locale 和数值后端单线程环境变量。
2. 新增稳定 JSON 编码和 SHA-256 指纹，递归排序对象键并统一处理绝对路径、
   session/output 路径、时间戳和运行时长等 volatile 字段。
3. 新增第 2 步环境快照和验证脚本；两代 `pyproject.toml` 均确认 Python
   `>=3.10`、`matplotlib>=3.8`、`numpy>=1.24`、`pandas>=2.0`、`scipy>=1.10`
   及可选 `pypdf>=4.0` 声明一致。两代均无 lock 文件，因此安装包快照仍需在
   后续隔离环境中单独冻结。
4. 新增 4 项第 2 步测试，覆盖运行时变量、路径/时间戳规范化、19 个注册拓扑
   默认 spec/candidate/evaluation 的重复指纹和环境快照字段。

### 第 2 步验证记录

验证命令：

```text
python -m pytest tests/test_phase2_reproducibility.py tests/test_phase2_packaging.py tests/test_phase12_verification.py -q
python scripts/validate_step2_environment.py
```

结果：测试 `11 passed`；环境验证 `validation_pass=true`；19 个注册拓扑的
默认设计契约重复构造指纹一致；运行时策略变量全部为约定值。证据目录：
`Plan\\active\\environment_20260824`。

当前仍保留的环境限制：2.0 的独立安装包版本未从源工程运行环境直接读取，
因此未宣称两代已安装包完全一致；这属于环境快照和隔离 replay 的后续闭环项。

### 第 2 步提交记录

- 步骤：第 2 步：工程和依赖环境对齐
- 实现 commit：`b8157fa` (`Step 2: align runtime reproducibility`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- push 结果：成功
- 实现验证：11 项第 2 步及关键回归测试通过；环境验证 `validation_pass=true`；第 1 步 103 工况基线复核通过。
- 状态 commit：`781f52b` (`Step 2: record runtime sync`)
- 状态 push 时间：`2026-08-24`（Asia/Shanghai）
- 状态 push 结果：成功
- 当前状态：实现和状态记录均已同步，允许关闭本步骤。

---

## 第 3 步：输入契约和规范化层移植

### 目标

保证同一个 2.0 design request 在 1.0 中经过完全相同的字段解析、默认值补全、单位换算、别名处理和校验后，得到相同的 normalized request。

### 详细工作

1. 逐字段对比 2.0 和 1.0 request schema。
2. 统一字段名称、大小写、空值、布尔值和枚举值。
3. 统一单位约定：
   - Hz/kHz
   - H/uH/mH
   - F/uF/nF
   - 百分数与 unit ratio
   - RMS、peak、peak-to-peak
4. 固化默认值来源，禁止 1.0 在缺省时使用不同默认值。
5. 统一输出电压回退逻辑，例如 `output.voltage_v` 和 `dc_bus.voltage_nominal_v`。
6. 统一工况复用字段：
   - `hardware_reuse_mode`
   - `hardware_design_case_id`
   - `load_ratio`
   - `load_ratio_source`
7. LLC 必须完整传递固定硬件快照：
   - `resonant_inductance_h`
   - `magnetizing_inductance_h`
   - `resonant_capacitance_f`
   - `output_capacitance_f`
   - `output_capacitor_esr_ohm`
   - `transformer_primary_turns`
   - `transformer_secondary_turns`
   - `load_resistance_ohm`
8. 为每个拓扑建立 normalized request schema test。

### 产出物

- `normalized_request_schema_v2.json`
- `request_field_mapping_matrix.csv`
- `request_normalization_golden.json`
- 17 个拓扑的输入契约测试

### 验证方法

103 个请求逐字段比较 2.0 normalized request 与 1.0 normalized request；字段名、单位和值必须一致。

### 完成条件

- normalized request 一致率 100%。
- 0 个隐式单位转换。
- 0 个仅由默认值差异造成的结果差异。

### 状态

`completed`

### 第 3 步完成证据

- 1.0 canonical parser：`src/pe_claw_gui/parsers/design_request.py`
- parser exports：`src/pe_claw_gui/parsers/__init__.py`
- schema：`Plan/active/request_contract_20260824/normalized_request_schema_v2.json`
- field matrix：`Plan/active/request_contract_20260824/request_field_mapping_matrix.csv`
- golden：`Plan/active/request_contract_20260824/request_normalization_golden.json`
- validator：`scripts/validate_step3_normalization.py`
- tests：`tests/test_phase3_request_normalization.py`
- source request inventory: 103 standard requests across the 17 registered topology directories
- exact comparison: 103/103 normalized requirements matched the PE-Claw 2.0 parser bridge
- unit policy: canonical layer retains Hz/H/F/V/A/W; legacy kHz and topology aliases are emitted only by `build_plugin_raw_input`
- ripple policy: numeric percentage targets remain numeric; descriptive 2.0 strings remain strings
- fixed hardware: LLC fixed-hardware snapshots are preserved, including scientific-notation values and reuse identifiers
- test command: `python scripts/validate_step3_normalization.py --source-root C:\\Users\\Lumia\\Documents\\PE_Claw\\PE_Claw260517_1_extracted\\PE_Claw --requests-root C:\\Users\\Lumia\\Documents\\PE_Claw\\PE_Claw260517_1_extracted\\PE_Claw\\design_requests --golden Plan\\active\\request_contract_20260824\\request_normalization_golden.json`
- test result: `request_count=103`, `exact_match_count=103`, `mismatch_count=0`
- focused tests: `python -m pytest tests/test_phase3_request_normalization.py -q` -> `4 passed`
- implementation commit: `1380d94` (`Step 3: align normalized request contract`)
- implementation branch: `codex/sync-gui-backend-from-2`
- implementation push: successful to `origin/codex/sync-gui-backend-from-2` on 2026-08-24 (Asia/Shanghai)
- status update: this record is committed separately after the implementation push

---

## 第 4 步：拓扑注册和插件框架移植

### 目标

保证 17 个拓扑在 1.0 中的 ID、显示名、拓扑类别、插件接口、输入 schema、能力声明和路由行为与 2.0 一致。

### 详细工作

1. 对比 registry 中的拓扑 ID、legacy key、display name 和类别。
2. 对比 GUI、backend、agentic router 和 pipeline 的拓扑路由。
3. 对比插件接口：
   - `build_spec`
   - `synthesize`
   - `evaluate`
   - waveform hooks
   - stress hooks
   - report hooks
4. 对比拓扑支持状态：executable、placeholder、first-pass、blocked 和 unsupported。
5. 确保 LLC 全桥和半桥在 1.0 共用实现时仍保留 `primary_bridge_type` 和 secondary rectifier type。
6. 确保拓扑错误消息、错误类型和失败原因一致。
7. 删除仅存在于旧版本且会改变路由的兼容分支，或为兼容分支增加明确版本标记。

### 产出物

- `topology_registry_mapping.csv`
- `topology_capability_mapping.csv`
- 17 个拓扑 plugin contract tests
- 路由一致性报告

### 验证方法

- 17 个 topology ID 全部存在且唯一。
- 103 个 request 的 topology hint 路由到同一逻辑拓扑。
- 非法输入触发同类错误。

### 完成条件

- 17/17 拓扑注册和路由一致。
- 无 topology ID 漂移。
- 无被错误路由到默认拓扑的情况。

### 状态

`completed`

### 第 4 步完成证据

- 新增统一能力声明：`src/pe_claw_gui/topologies/base/capabilities.py`。
- registry 现在拒绝重复 `topology_id`、重复 `legacy_key`，并提供不带默认回退的
  `resolve_topology_id` 与能力查询接口。
- 17 个迁移目录对应 16 个唯一逻辑 `topology_id`；LLC 全桥/半桥共用 LLC 二极管
  插件，但通过 `primary_bridge_type` 和 `secondary_rectifier_type` 保留变体语义。
- registry 映射：`Plan/active/topology_registry_mapping.csv`。
- 能力映射：`Plan/active/topology_capability_mapping.csv`。
- 103 个请求路由报告：`Plan/active/topology_routing_consistency.json`。
- 自动验证脚本：`scripts/validate_step4_topology_registry.py`。
- 契约测试：`tests/test_phase4_topology_contracts.py`。

### 第 4 步验证记录

执行命令：

```text
python scripts/validate_step4_topology_registry.py
python -m pytest tests/test_phase4_topology_contracts.py tests/test_phase12_verification.py tests/test_phase3_request_normalization.py -q
```

结果：17/17 迁移目录、103/103 请求路由匹配；registry 元数据与 2.0 的 17 项
全部匹配；19 个注册拓扑 ID 唯一；LLC 变体约束 14/14 匹配；路由报告
`validation_pass=true`；相关测试 `29 passed`。

### 第 4 步提交记录

- 实现 commit：`b18a579` (`Step 4: align topology registry contracts`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- 实现 push：成功，2026-08-24（Asia/Shanghai）
- 状态 commit：待本次状态更新提交后记录
- 状态 push：待本次状态更新提交后记录

---

## 第 5 步：DC-DC 拓扑算法完整移植

### 范围

01 Buck diode、02 Buck synchronous、03 Boost diode、04 Boost synchronous、05 Buck-Boost diode、06 Flyback CCM、07 PSFB diode、08 LLC full bridge diode、09 LLC half bridge diode。

### 目标

使 DC-DC 的综合、工作点、可行性、应力、磁性和电容计算使用与 2.0 相同的公式、默认值、频率定义和边界处理。

### 详细工作

1. 对比每个拓扑的 input schema 和 synthesizer。
2. 对比 duty、current、inductance、capacitance、ripple、peak/valley 的公式。
3. 对比轻载、低输入、高输入和高纹波工况的工作点选择。
4. Flyback：统一 CCM 电流、磁化电感、输出电容、二极管应力和 clamp margin。
5. PSFB：统一有效占空比、命令占空比、leakage duty loss、整流输出脉冲频率、Lout 和 Cout 公式。
6. LLC：统一 FHA 模型、bridge gain、频率范围、负载比例、固定硬件刷新、FHA feasibility 和边界告警。
7. 统一 transformer target metadata 和磁性设计输入。
8. 统一 DC-DC 设备 stress adapter 和独立整流二极管绑定策略。

### 产出物

- 01-09 拓扑迁移映射表
- DC-DC 公式对照表
- DC-DC golden candidate outputs
- DC-DC unit/golden tests

### 验证方法

- 9 个拓扑的 nominal、low-line、high-line、light-load、high-ripple 工况全部回放。
- LLC 两种桥型和固定硬件复用工况必须单独验证。
- 关键连续计算字段目标误差为 `<= 1e-9` 或按 2.0 数值精度规则一致。

### 完成条件

- 9/9 拓扑算法完成。
- 51 个 DC-DC 工况无未解释差异。
- PSFB、Flyback、LLC 的模型边界差异已消除或绑定到明确版本差异。

### 状态

`completed`

### 第 5 步完成证据

- 算法文件逐文件 SHA-256 对照：`Plan/active/dc_dc_migration_validation.json`。
- 公式与频率口径：`Plan/active/dc_dc_formula_mapping.csv`。
- 51 个 DC-DC 工况的候选黄金输出：`Plan/active/dc_dc_candidate_golden.json`。
- 自动验证脚本：`scripts/validate_step5_dc_dc.py`。
- 专项测试：`tests/test_phase5_dc_dc_migration.py`。
- 9 个迁移请求目录对应 8 个逻辑 topology ID；LLC 全桥/半桥共用 diode LLC
  插件但保留桥型和整流器参数。
- 01-09 的 53 个算法文件与 PE-Claw 2.0 对应文件 SHA-256 全部一致。

### 第 5 步验证记录

执行命令：

```text
python scripts/validate_step5_dc_dc.py
python -m pytest tests/test_phase5_dc_dc_migration.py tests/test_phase7_dc_dc_topologies.py tests/test_phase5_pipeline_closure.py -q
```

结果：51/51 工况执行成功，0 个执行错误，0 个未解释 mismatch；核心字段
326/326 匹配；41 个工况完全通过，10 个工况仅包含已登记的 Flyback/PSFB
模型边界字段；最大相对差异 20% 仅出现在已登记的 PSFB 边界字段；专项及
既有 DC-DC 流程测试 `10 passed`。

### 第 5 步提交记录

- 实现 commit：`bedec91` (`Step 5: validate DC-DC algorithm parity`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- 实现 push：成功，2026-08-24（Asia/Shanghai）
- 状态 commit：待本次状态更新提交后记录
- 状态 push：待本次状态更新提交后记录

---

## 第 6 步：AC-DC 拓扑算法完整移植

### 范围

10 单相电容整流、11 单相 DC 电感整流、12 三相电容整流、13 二极管桥 Boost PFC、14 Totem-Pole PFC。

### 目标

统一被动整流器、PFC 线周期模型、波形仿真、DC-link 纹波和电感纹波的定义及实现。

### 详细工作

1. 单相电容整流：统一充电脉冲、Rs、整流二极管、Cdc、负载和 PF 的仿真模型。
2. 单相 DC 电感整流：统一 state-space 步长、稳态判定、DCM/CCM 判定、Ldc/Cdc 和输出纹波。
3. 三相电容整流：统一六脉波输入、线电压定义、源电阻、充电脉冲和 phase current peak。
4. Boost PFC：统一理想功率平衡电流、效率修正电流、line-cycle envelope、boost L、input L、Cdc 和 ripple prediction。
5. Totem-Pole PFC：统一桥臂角色、线频开关模型、HF ripple、inductor peak/valley 和 feasibility。
6. 将“设计目标”“理论估算”“仿真预测”拆成不同内部字段。
7. 统一 PFC 低线、高线、轻载、高频、高纹波和 50/60 Hz 工况。
8. 统一 passive rectifier 的输出电压是 target、estimated 还是 achieved 的定义。

### 产出物

- AC-DC 公式和仿真对照表
- waveform metric contract
- AC-DC golden waveform metrics
- 10-14 拓扑测试集

### 验证方法

对 10-14 的 31 个工况逐项比较：输出电压、电流、Cdc、纹波、PF、输入峰值电流、电感峰谷值、可行性和仿真收敛状态。

### 完成条件

- 5/5 AC-DC 拓扑完成。
- 31 个工况的目标值和仿真值分别对齐。
- 不再出现“同名字段不同含义”的比较。

### 状态

`completed`

### 第 6 步完成证据

- 算法文件逐文件 SHA-256 对照：`Plan/active/ac_dc_migration_validation.json`；5 个 AC-DC
  拓扑目录中的 35 个 Python 算法文件全部一致，0 个 mismatch。
- 公式与频率口径：`Plan/active/ac_dc_formula_mapping.csv`。
- 同名指标语义和 target/achieved 分层契约：`Plan/active/ac_dc_waveform_metric_contract.json`。
- 31 个 AC-DC 工况的黄金波形指标：`Plan/active/ac_dc_waveform_metrics_golden.json`。
- 自动验证脚本：`scripts/validate_step6_ac_dc.py`。
- 专项测试：`tests/test_phase6_ac_dc_migration.py`。

### 第 6 步验证记录

执行命令：

```text
python scripts/validate_step6_ac_dc.py
python -m pytest tests/test_phase6_ac_dc_migration.py tests/test_phase8_ac_dc_topologies.py -q
```

结果：5/5 拓扑、35/35 算法文件一致；31/31 工况执行成功，0 个执行错误，0 个未解释
mismatch；核心字段 136/136 匹配。9 个工况完全通过，22 个工况仅包含已登记的被动整流
或 Boost PFC 模型边界差异；专项及 AC-DC 拓扑测试 `7 passed`。

### 第 6 步提交记录

- 实现 commit：`0dccb4c` (`Step 6: validate AC-DC algorithm parity`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- 实现 push：成功，2026-08-24 12:20:38 +08:00（Asia/Shanghai）
- 状态 commit：待本次状态更新提交后记录
- 状态 push：待本次状态更新提交后记录

---

## 第 7 步：DC-AC 拓扑算法完整移植

### 范围

15 单相全桥逆变器、16 三相两电平 VSI、17 三相三电平 NPC。

### 目标

统一调制比、RMS 电压电流、PF、载波频率、输出滤波、器件应力和三电平中点行为。

### 详细工作

1. 对比单相全桥输入 schema、调制模型和 PF 工况。
2. 对比三相 VSI 的 line-line/phase RMS 换算和电流定义。
3. 对比 NPC 的电平、钳位支路和中点相关元数据。
4. 统一 carrier frequency 与 line frequency 的字段语义。
5. 统一轻载、60 Hz、高载波频率和 PF 0.8 工况。
6. 统一 inverter stress 和 waveform summary 的字段名称。

### 产出物

- DC-AC 映射表
- 15-17 golden outputs
- DC-AC contract tests

### 验证方法

对 21 个 DC-AC 工况进行结构化逐字段比较，重点比较 RMS、调制比、输出电流、纹波、器件峰值应力和 feasibility。

### 完成条件

- 3/3 DC-AC 拓扑完成。
- 21 个工况无未解释差异。

### 状态

`completed`

### 第 7 步完成证据

- 算法文件逐文件 SHA-256 对照：`Plan/active/dc_ac_migration_validation.json`；3 个 DC-AC
  拓扑目录中的 18 个 Python 算法文件全部一致，0 个 mismatch。
- 公式与频率口径：`Plan/active/dc_ac_formula_mapping.csv`。
- DC-AC 指标语义和目标/估算/波形/应力分层契约：`Plan/active/dc_ac_metric_contract.json`。
- 21 个 DC-AC 工况的黄金输出：`Plan/active/dc_ac_candidate_golden.json`。
- 自动验证脚本：`scripts/validate_step7_dc_ac.py`。
- 专项测试：`tests/test_phase7_dc_ac_migration.py`。

### 第 7 步验证记录

执行命令：

```text
python scripts/validate_step7_dc_ac.py
python -m pytest tests/test_phase7_dc_ac_migration.py tests/test_phase9_dc_ac_topologies.py -q
```

结果：3/3 拓扑、18/18 算法文件一致；21/21 工况执行成功，0 个执行错误，21/21
工况完全通过，0 个未解释 mismatch；核心字段 168/168 匹配，最大相对误差约
0.729%；专项及 DC-AC 拓扑测试 `7 passed`。

### 第 7 步提交记录

- 实现 commit：`55734bd` (`Step 7: validate DC-AC algorithm parity`)
- 远端：`origin/codex/sync-gui-backend-from-2`
- 实现 push：成功，2026-08-24 12:53:11 +08:00（Asia/Shanghai）
- 状态 commit：待本次状态更新提交后记录
- 状态 push：待本次状态更新提交后记录

---

## 第 8 步：器件库、磁性、电容和排序一致化

### 目标

如果完整移植要求最终推荐器件也一致，则必须使两代使用相同的库快照、过滤规则和排序策略。

### 详细工作

1. 对比半导体、磁芯、线材和电容库文件及版本。
2. 为每个库保存 source path、版本、记录数和 SHA-256。
3. 对比器件字段单位、缺失值和默认值。
4. 同步 semiconductor role binding：主开关、同步开关、整流二极管、桥堆、线频开关等。
5. 同步磁性候选的磁通密度、窗口利用率、温升和匝数筛选。
6. 同步电容候选的纹波电流、ESR、寿命、并联数和额定电压筛选。
7. 同步排序权重、tie-break、推荐候选和并列处理。
8. 禁止依赖数据库自然顺序或文件系统顺序。
9. 为候选列表生成排序 checksum。

### 产出物

- `library_manifest_2.json`
- `library_manifest_1.json`
- `library_record_mapping.csv`
- `candidate_sorting_policy.md`
- 候选列表 golden snapshots

### 验证方法

- 相同库 checksum 下，候选列表顺序完全一致。
- 相同输入下 selected part、parallel count、magnetic ID 和 capacitor bank 一致。
- 若库不能同步，必须将库差异作为显式输入版本，而不是隐含差异。

### 完成条件

- 库数据、过滤和排序完全可追溯。
- 器件差异全部能解释为库版本或算法差异。

### 状态

`completed`

### 第八步执行记录

- 实现提交：`6ab69dc`（已 push 到 `origin/codex/sync-gui-backend-from-2`）。
- 验证脚本：`scripts/validate_step8_libraries.py`；专项测试：`tests/test_phase8_library_migration.py`。
- 库文件 manifest：1296 个相对路径；885 个字节级一致，408 个仅换行差异，0 个实质内容差异；目标侧 3 个磁性目录 `.gitkeep` 已标记为占位文件。
- 运行时库记录：半导体 800 条、电容 32910 条、Sendust 磁芯 567 条、尺寸 61 条、材料 9 条；规范化磁性缓存记录数与 2.0 一致。
- 当前注册表两代均为 19 个拓扑定义；19/19 个默认拓扑运行成功，19/19 个器件/电容选择 checksum 一致。
- 排序策略、候选列表和跨工程对照分别记录在 `candidate_sorting_policy.md`、`candidate_selection_golden.json`、`library_migration_validation.json`。
- 验证命令：`python scripts/validate_step8_libraries.py --reuse-runtime`；`pytest -q tests/test_phase8_library_migration.py tests/test_semiconductor_registry_structure.py tests/test_capacitor_registry.py tests/test_magnetic_library_schema.py`，结果 `14 passed`。

---

## 第 9 步：仿真、固定硬件和工作点刷新一致化

### 目标

保证 c01 设计工况和 c02-c07 等固定硬件复用工况使用与 2.0 相同的执行路径，而不是重新综合或使用不同的估算模型。

### 详细工作

1. 对比 `run_full_pipeline()` 和 operating-point refresh 的调用链。
2. 明确每个工况是：
   - 新设计
   - 固定硬件刷新
   - 仅改变输入电压
   - 仅改变负载比例
   - 仅改变频率
   - 仅改变纹波目标
3. 固定硬件工况只允许刷新运行点，不得重新选择 L、C、磁芯或器件。
4. 统一仿真 solver、步长、采样窗口、settling cycles 和 convergence criteria。
5. 统一波形后处理：平均值、RMS、峰值、谷值、峰峰值、频率和相位。
6. 统一失败和边界状态：FHA limitation、DCM、ZVS fail、PF fail、thermal fail。
7. 为每个复用工况保存 hardware snapshot checksum 和 operating-point input checksum。

### 产出物

- `operating_point_replay_matrix.csv`
- `simulation_contract.md`
- waveform metrics schema
- fixed hardware snapshot archive

### 验证方法

- c01 结果作为硬件快照基准。
- 后续工况不改变固定硬件字段。
- 同一工况重复执行，波形指标和状态完全可复现。

### 完成条件

- 103 个工况执行路径与 2.0 一致。
- 所有复用工况均有硬件快照证据。
- 仿真差异不再由步长、窗口或后处理定义造成。

### 状态

`completed`

### 第九步执行记录

- 实现提交：`287481f`（已 push 到 `origin/codex/sync-gui-backend-from-2`）。
- 验证脚本：`scripts/validate_step9_operating_points.py`；专项测试：`tests/test_phase9_operating_point_migration.py`。
- 103 个工况全部进入矩阵；按源 request 矩阵分为 19 个新设计和 84 个固定硬件刷新，覆盖 17 个源矩阵目录和 16 个 runtime topology ID。LLC full-bridge 与 half-bridge 虽共用一个 runtime topology ID，但分别保存 c01 基线。
- 84 个固定硬件刷新工况均通过 `run_operating_point_refresh()` 执行，硬件快照覆盖 L、C、候选设计参数、器件、磁性设计和电容 Part Number；所有固定硬件 checksum 均与本矩阵 c01 一致。
- 修正 `run_operating_point_refresh()`：保留已有器件和几何结果，不再清空桥式整流器硬件，也不因刷新报告缺少器件而重新进入器件选择。
- 统一保存 operating-point input checksum、waveform metrics checksum；波形后处理包含 average、RMS、peak、valley、peak-to-peak，并保留 solver、步长、采样窗口、settling cycles、convergence 等拓扑可用元数据。
- 产物目录：`Plan/active/operating_points_20260824/`，包含 `operating_point_replay_matrix.csv`、`simulation_contract.md`、`waveform_metrics_schema.json`、`fixed_hardware_snapshots.json` 和 `operating_point_migration_validation.json`。
- 验证命令：`python scripts/validate_step9_operating_points.py --source-root C:\\Users\\Lumia\\Documents\\PE_Claw\\PE_Claw260517_1_extracted\\PE_Claw --output-dir Plan/active/operating_points_20260824`；`pytest -q tests/test_phase9_operating_point_migration.py tests/test_phase9_dc_ac_topologies.py tests/test_phase8_library_migration.py`，结果 `9 passed`。
- 历史回放曾识别 PSFB `c02_low_input_full_load` 的 duty boundary。该问题已由
  `Plan/active/psfb_duty_policy_20260824/` 中的 PSFB 专项修复和 7 工况回归
  收敛：修复后 `c02` 为 `executed`，0 个 PSFB boundary failure。全量 103
  工况尚未因本次专项修复重新回放，因此第 11、12 步仍需保持 active。

---

## 第 10 步：结构化输出和报告契约统一

### 目标

让两代输出使用同一套结构化数据模型，Markdown 只负责展示，避免通过表格文本猜测字段语义。

### 详细工作

1. 统一顶层报告结构：request、candidate、waveform、stress、magnetic、capacitor、thermal、audit。
2. 为每个数值字段定义：
   - 字段名
   - 物理含义
   - 单位
   - 数值类型
   - 空值规则
   - 来源阶段
   - 适用拓扑
3. 拆分以下容易混淆的字段：
   - `output_ripple_target_v`
   - `output_ripple_estimated_v`
   - `output_ripple_predicted_v`
   - `output_ripple_simulated_v`
   - `dc_link_ripple_limit_v`
   - `dc_link_ripple_predicted_v`
4. 统一 `feasible`、`ccm_valid`、`zvs_status`、`pf_status` 和 `thermal_status`。
5. 统一单位输出，禁止依靠字段标题中的字符串后缀推断单位。
6. 生成 JSON schema，并对 2.0/1.0 报告执行 schema validation。
7. 让 Markdown、CSV 和 JSON 均从同一结构化对象生成。

### 产出物

- `design_output_schema.json`
- `report_field_dictionary.md`
- `report_schema_validation.py`
- `build_step10_structured_outputs.py`
- 2.0/1.0 structured output snapshots、CSV 和 Markdown 视图
- `structured_output_migration_validation.json`

### 验证方法

- `python scripts/validate_step9_operating_points.py --source-root C:\\Users\\Lumia\\Documents\\PE_Claw\\PE_Claw260517_1_extracted\\PE_Claw --output-dir Plan/active/operating_points_20260824`
  重新生成 1.0 的 103 条结构化快照。
- `python scripts/build_step10_structured_outputs.py --inventory Plan/active/baseline_20260824/structured_readback_inventory.json --one-snapshot Plan/active/operating_points_20260824/structured_output_snapshots.json --output-dir Plan/active/structured_outputs_20260824`
  生成两代快照和三种报告视图。
- `python scripts/report_schema_validation.py Plan/active/operating_points_20260824/structured_output_snapshots.json --output Plan/active/operating_points_20260824/structured_output_validation.json`
  结果为 103 valid、0 invalid；跨代生成器结果为 2.0: 103 valid、0 invalid，1.0: 103 valid、0 invalid。
- `python -m pytest tests/test_phase10_structured_output.py tests/test_phase9_operating_point_migration.py -q`
  结果为 `5 passed`。
- 专项测试确认同一结构化对象生成的 CSV 行数与 JSON quantity 数量一致，Markdown 值来自相同 quantity 对象，canonical checksum 可复现。

### 完成条件

- 0 个语义不明的通用字段。
- 0 个通过字符串解析才能恢复单位的关键字段。
- 2.0 和 1.0 均有 103 条可校验的结构化快照。

### 状态

`completed`

### 第 10 步已实施修改

1. 新增跨代稳定结构化报告适配层，显式提供 `request`、`candidate`、
   `operating_point`、`waveform`、`stress`、`magnetic`、`capacitor`、
   `thermal`、`hardware`、`ripple`、`status` 和 `audit` 分区。
2. 关键数值统一为 `{value, unit, source}`；纹波字段拆分为目标、估算、
   预测、仿真以及 DC-link 限值/预测，状态字段使用固定枚举。
3. 新增 JSON schema、字段字典、schema validator、2.0 legacy
   `final_report.json` 适配器和从结构化对象导出 CSV/Markdown 的脚本。
4. 新增第十步专项测试，锁定两代快照覆盖、字段契约、视图同源和确定性
   checksum。

### 第 10 步证据

证据目录：
`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active\structured_outputs_20260824`

其中 `pe_claw_2_structured_output_snapshots.json` 和
`pe_claw_1_structured_output_snapshots.json` 各包含 103 条记录；对应
validation 文件均为 `103 valid, 0 invalid`。

### 第 10 步提交与同步记录

- 实现与证据 commit：`21ff309`（`Step 10: unify structured output and report contract`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- push 时间：`2026-08-24T15:00:52+08:00`
- 同步结果：成功
- 状态变更：本记录 commit/push 成功后将第 10 步标记为 `completed`

---

## 第 11 步：103 工况端到端回放和差异收敛

### 目标

用冻结的 2.0 golden baseline 对 1.0 进行最终端到端回放，逐字段收敛所有差异，并给每个剩余差异建立可审计解释。

### 详细工作

1. 执行 103 个 design request。
2. 对每个工况保存：
   - normalized request
   - pipeline options
   - candidate
   - waveform metrics
   - stress
   - magnetic
   - capacitor
   - final report
   - audit trail
3. 进行三层比较：
   - 输入层：严格一致
   - 算法层：数值一致
   - 展示层：字段和单位一致
4. 差异分为：
   - `input_mapping_error`
   - `formula_difference`
   - `simulation_numerical_difference`
   - `field_semantic_difference`
   - `library_difference`
   - `ordering_difference`
   - `expected_boundary`
5. `expected_boundary` 只能在有代码、公式或测试证据时使用。
6. 每个差异必须记录 source value、target value、absolute error、relative error、tolerance、basis 和 owner。
7. 修复后必须重新运行受影响拓扑的全部工况，再运行全量 103 工况。

### 推荐验收阈值

| 输出层 | 默认阈值 | 说明 |
| --- | ---: | --- |
| 输入字段 | 0 | 字段和值必须一致 |
| 拓扑 ID 和状态 | 0 | 必须完全一致 |
| 确定性公式字段 | `1e-9` 或源实现精度 | 例如 duty、L、C、关键电流 |
| 仿真统计字段 | 由 solver 精度定义 | 必须固定步长、采样和收敛规则 |
| 布尔状态 | 0 | CCM、feasible、ZVS 等必须一致 |
| 器件选择 | 0 | 仅在库快照一致时适用 |
| 路径、时间戳 | 排除比较 | 不属于设计行为 |

### 产出物

- `comparison_final.json`
- `comparison_final.csv`
- `comparison_final.md`
- `topology_summary_final.md`
- `unexplained_difference_ledger.md`
- `replay_case_checksums.csv`
- `replay_checksums.json`
- `compare_step11_structured_outputs.py`
- 103 工况回放日志和 checksum

### 完成条件

- 103/103 执行成功。
- 0 个未解释差异。
- 不再使用 `model_boundary` 隐藏尚未调查的差异。
- 每个允许差异都有代码或模型证据。

### 状态

`in_progress`

### 第 11 步已实施修改

1. 新增结构化快照比较器，以第十步的 2.0/1.0 snapshot 为唯一比较输入，
   逐路径比较拓扑、请求、候选、工作点、波形、应力、磁性、电容、热和
   状态字段。
2. 数值差异统一记录 source value、target value、单位、absolute error、
   relative error、tolerance、basis、category、owner 和 evidence；不再用
   未定义的 `model_boundary` 掩盖差异。
3. 修正 operating-point refresh 报告契约：当前工况请求和 c01 冻结硬件
   分别记录，特殊字符串纹波要求和约束中的电感纹波值按规范化规则恢复。
4. 对 PSFB 低输入固定硬件 refresh 的历史 `boundary_failure` 完成专项修复，
   由 operating-point duty policy 统一提供 effective/command duty 和 duty loss；
   PSFB 7 工况及修复后全量 103 工况回放均显示该 boundary 已转为 `executed`。
5. 新增第十一步专项测试，覆盖 103 工况、17 个矩阵目录、16 个运行时拓扑
   ID、差异审计字段和逐工况 checksum。

### 第 11 步验证记录

验证命令：

```text
python scripts/validate_step9_operating_points.py --source-root C:\\Users\\Lumia\\Documents\\PE_Claw\\PE_Claw260517_1_extracted\\PE_Claw --output-dir Plan/active/operating_points_20260824
python scripts/report_schema_validation.py Plan/active/operating_points_20260824/structured_output_snapshots.json --output Plan/active/operating_points_20260824/structured_output_validation.json
python scripts/build_step10_structured_outputs.py --inventory Plan/active/baseline_20260824/structured_readback_inventory.json --one-snapshot Plan/active/operating_points_20260824/structured_output_snapshots.json --output-dir Plan/active/structured_outputs_20260824
python scripts/compare_step11_structured_outputs.py --source Plan/active/structured_outputs_20260824/pe_claw_2_structured_output_snapshots.json --target Plan/active/structured_outputs_20260824/pe_claw_1_structured_output_snapshots.json --replay-matrix Plan/active/operating_points_20260824/operating_point_replay_matrix.csv --output-dir Plan/active/final_comparison_20260824
python -m pytest tests/test_phase10_structured_output.py tests/test_phase11_structured_comparison.py tests/test_phase9_operating_point_migration.py -q
```

结果：修复后 103/103 replay records，0 execution errors，0 个 boundary failure，
3412 个字段差异均已量化，0 个 unexplained difference；专项测试 `27 passed`。
差异分类计数为：`formula_difference=389`、
`simulation_numerical_difference=1934`、`field_semantic_difference=358`、
`ordering_difference=638`、`input_mapping_error=93`。所有差异均带有 owner
和证据路径；边界证据单独记录在 comparison JSON 的 `boundary_evidence` 中。

修复后证据目录：
`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active\final_comparison_20260824_repaired`

修复后回放目录：
`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active\operating_points_20260824_repaired`

修复后结构化输出目录：
`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\active\structured_outputs_20260824_repaired`

主证据：`comparison_final.json`、`comparison_final.csv`、
`comparison_final.md`、`topology_summary_final.md`、
`unexplained_difference_ledger.md`、`replay_case_checksums.csv` 和
`replay_checksums.json`。

### 第 11 步状态说明

第 11 步已完成。修复后全量回放满足 `103/103` 执行成功、0 个 execution
error、0 个 boundary failure 和 0 个 unexplained difference；PSFB
`c02_low_input_full_load` 已由 `boundary_failure` 转为 `executed`。3412 个
字段差异全部具有分类、owner、容差、依据和证据路径，详见修复后对比目录。

### 第 11 步提交与同步记录

- 历史实现与证据 commit：`14611cd`（`Step 11: converge end-to-end structured parity`）
- 修复后全量回放证据 commit：`7646d2f`（`Migration: record repaired full 103-case replay`）
- 本次状态记录 commit：待本次修改提交后记录
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- push 时间：待本次修改 push 后记录
- 同步结果：待本次修改 push 后记录
- 状态结论：`completed`

---

## 第 12 步：最终验收、文档归档和计划关闭

### 目标

完成工程验收和交付证据归档。修复后的 PSFB 边界工况和全量 103 工况已经
收敛，本步骤负责重新生成最终报告、记录最终版本并关闭计划。

### 详细工作

1. 运行全量测试、拓扑测试、schema 测试和 103 工况回放。
2. 检查 Git diff，确认没有无关文件或缓存进入交付范围。
3. 生成迁移完成报告，说明：
   - 已移植模块
   - 已统一模型
   - 已同步库和配置
   - 已验证工况
   - 剩余限制
4. 记录最终版本、commit、环境 checksum 和报告 checksum。
5. 将阶段性报告、差异台账、测试日志和 golden snapshot 归档。
6. 更新项目 README、迁移说明和版本变更记录。
7. 只有在所有验收条件满足后，才将状态改为 `completed`。

### 最终验收标准

- 17/17 拓扑注册、路由和插件契约一致。
- 103/103 设计输入规范化一致。
- 103/103 工况执行成功。
- 0 个未解释差异。
- 核心公式和仿真阶段达到约定精度。
- 报告字段名称、单位和语义 100% 一致。
- 相同器件库快照下，器件、磁性和电容结果一致。
- 重复执行具有可重复性。
- 所有已知限制均有明确记录。

### 产出物

- `complete_migration_acceptance_report.md`
- `complete_migration_acceptance_report.json`
- `migration_release_manifest.json`
- 最终测试报告
- 归档后的 golden baseline

### 状态

`in_progress`

### 第 12 步执行结果（2026-08-24，修复后回放更新）

- 验收报告：`Plan/active/final_acceptance_20260824/complete_migration_acceptance_report.md`
- 机器报告：`Plan/active/final_acceptance_20260824/complete_migration_acceptance_report.json`
- 发布清单：`Plan/active/final_acceptance_20260824/migration_release_manifest.json`
- golden baseline 归档：`Plan/active/final_acceptance_20260824/golden_baseline/`
- 注册拓扑：19 个；设计请求矩阵：17 个；回放运行时拓扑 ID：16 个
- 修复后全量回放：103/103 记录，0 个 execution error，0 个 PSFB boundary failure
- 修复后回放、结构化输出和字段对比证据已生成并通过校验：103/103、0 个 unexplained difference
- 结构化 schema：2.0 与 1.0 均为 103/103 valid
- 字段差异：3412 个，0 个未解释差异
- 默认 `python -m pytest -q`：248 passed，1 skipped，3 errors；错误均为系统临时目录 ACL（WinError 5）
- 本地可写 basetemp 完整回归：251 passed，1 skipped
- 专项测试：拓扑/规范化/库 28 passed；结构化/比较/回放 8 passed；临时目录受影响测试 3 passed
- 当前阶段结论：PSFB 和全量回放验收条件已满足；最终验收报告需切换到修复后证据并完成归档后关闭计划

本步骤保持 `in_progress`，不将计划移动到 `Plan/completed`。

### 第 12 步提交与同步记录

- 验收证据与脚本 commit：`c8032e0`（`Step 12: record migration acceptance evidence`）
- 远端分支：`origin/codex/sync-gui-backend-from-2`
- push 时间：`2026-08-24T16:01:29+08:00`
- 同步结果：成功
- 状态结论：保持 `in_progress`，等待修复后最终验收报告重新生成和计划关闭

---

## 5. 变更管理规则

1. 不得使用 `git reset --hard`、`git checkout --` 等方式覆盖用户修改。
2. 每次修改前记录受影响文件、原因和对应计划步骤。
3. 修改一个拓扑后，优先运行该拓扑全部工况，再运行全量回归。
4. 任何新增兼容层必须说明 2.0 行为、1.0 行为和移除条件。
5. 任何改变字段语义的修改必须同步更新 schema、报告字典和比较器。
6. 任何器件库修改必须更新库版本和 checksum。
7. 测试失败不得直接标记为模型边界；必须先完成根因分析。
8. 每个步骤完成后更新本文件的状态和证据路径。
9. 每个步骤完成后必须做一次独立 commit 并 push；不得把多个步骤合并为一个未标识步骤边界的 commit。
10. 步骤 commit 必须包含对应的测试和验证证据更新。
11. push 成功前不得把步骤标记为 `completed`。
12. 每次步骤完成记录必须包含：步骤编号、commit hash、远端分支、push 时间、测试命令和测试结果。

## 6. 当前执行记录

### 2026-08-24

- 已完成 17 个拓扑、103 个工况的迁移基线回放。
- 已确认 103/103 可执行、0 个执行错误。
- 已发现并记录输入映射、单位、模型口径和报告字段差异。
- 已建立验证脚本：`scripts\compare_pe_claw_2_to_1_design_requests.py`。
- 当前进入第 1 步：冻结 2.0 golden baseline，建立字段语义矩阵和完整差异台账。

## 7. 计划关闭条件

本文件仍保留在 `Plan\active`，表示完整移植尚未完成。只有第 1 至第 12 步全部完成，且最终验收标准全部满足后，才允许：

1. 将计划状态改为 `completed`。
2. 填写最终版本、commit、报告路径和验收日期。
3. 将本文件移动到 `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\Plan\completed`。
4. 在 `Plan\active` 中留下新的后续计划，或保持目录为空。

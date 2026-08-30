# LLC 重新设计结果链路修复计划

## 1. 计划目的

修复 LLC 重新设计后输出结果不完整、旧结果被引用、磁件结果与硬件总览不一致，以及谐振电容超出误差限制仍被标记为推荐的问题。

本计划针对以下现象制定：

- `outputs/transformer_design` 目录为空，但后续仍生成了 LLC 外置谐振电感几何和硬件总览。
- `resonant_inductor_design` 只生成几何文件，没有与本次运行绑定的候选 CSV、Pareto CSV 和 chosen candidates CSV。
- 硬件总览仍引用历史的 `E_80_38_32_SMP97_Np18_Ns18` 和 `Lr_ext_E_55_28_25_SMP97_N11_P4`。
- LLC 谐振电容推荐 `80 nF`，相对目标 `74.3748 nF` 的误差为 `+7.563%`，超过 5% 限制，但仍被标记为推荐。
- 效率扫描和硬件总览可以在磁件结果不完整时继续生成，造成“结果已完成”的错误印象。
- 结果目录中缺少能够绑定拓扑、输入、组件推荐和所有输出文件的最终 manifest。

## 2. 计划范围

### 涉及范围

- LLC 拓扑运行上下文和输出目录管理。
- LLC 变压器候选搜索、结果持久化和失败处理。
- LLC 外置谐振电感搜索、结果持久化和几何生成。
- LLC 谐振电容推荐约束和排序策略。
- 磁件结果之间的参数传递和一致性校验。
- 效率扫描、硬件总览、几何结果和最终 manifest 的依赖关系。
- LLC 相关单元测试、集成测试和手动输出验收。

### 不在本计划范围内

- 重新设计 LLC FHA 数学模型。
- 替换磁芯、半导体或电容器件数据库。
- 完善变压器三维 CAD、绕组制造工艺和详细寄生参数模型。
- 修改 AC-DC、DC-AC 或其他非 LLC 拓扑的既有结果。
- 删除历史迁移对比结果和其他拓扑的 outputs。

## 3. 当前基线和目标状态

### 当前基线

本次重跑之后，以下文件已经生成：

- `outputs/resonant_capacitor_design/llc_resonant_capacitor_*.csv`
- `outputs/resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_*`
- `outputs/capacitor_design/*`
- `outputs/efficiency_sweep/efficiency_curve.png`
- `outputs/efficiency_sweep/loss_breakdown_stacked.png`
- `outputs/hardware_overview/*`

但以下关键结果没有生成：

- `outputs/transformer_design/llc_transformer_feasible_candidates.csv`
- `outputs/transformer_design/llc_transformer_pareto_front.csv`
- `outputs/transformer_design/llc_transformer_chosen_candidates.csv`
- `outputs/resonant_inductor_design/llc_external_resonant_inductor_feasible_candidates.csv`
- `outputs/resonant_inductor_design/llc_external_resonant_inductor_pareto_front.csv`
- `outputs/resonant_inductor_design/llc_external_resonant_inductor_chosen_candidates.csv`

### 目标状态

一次 LLC 运行必须满足以下顺序：

```text
创建 run context
-> 清理/隔离本次输出
-> 完成电气计算
-> 生成变压器结果
-> 生成外置 Lr 结果
-> 生成 Cr 结果
-> 生成器件和效率结果
-> 生成几何与硬件总览
-> 校验全部结果引用
-> 写入最终 manifest
```

任一必需阶段失败时，后续阶段必须停止，或明确标记为 `blocked`，不能读取历史结果继续生成最终总览。

## 4. 执行规则

- 每一步只修改该步骤声明的代码、测试和计划状态。
- 每一步完成后先运行该步骤的测试，再检查 `git diff` 和 `git status`。
- 每一步必须单独执行 `commit` 和 `push`；commit message 使用能说明步骤和行为的英文短语。
- 不覆盖用户已有的未提交修改；如发现目标文件存在无关改动，应先隔离处理。
- 每一步完成后在本计划中更新对应步骤的状态、commit ID、测试命令和结果。
- 输出验证使用全新临时 run 目录或清空后的 LLC 专用目录，避免历史文件掩盖问题。

## 5. 分步修改安排

## 第 1 步：建立 LLC 运行上下文和结果边界

### 目标

让一次 LLC 运行拥有明确的 `run_id`、输入快照、输出根目录和阶段状态，阻止旧运行结果进入当前运行。

### 具体修改

1. 定位 LLC 主运行入口、磁件 pipeline、效率扫描入口和硬件总览入口。
2. 定义 LLC 运行上下文，至少包含：
   - `run_id`
   - `topology_id`
   - 输入参数快照或输入摘要哈希
   - 本次输出根目录
   - 当前阶段状态
   - 变压器、外置电感、谐振电容和器件结果 ID
3. 让 LLC 输出写入本次运行边界内的目录，或在现有目录结构下为每个文件记录 `run_id`。
4. 在开始运行时清除当前 LLC 结果引用；清除只针对 LLC 专用输出，不删除其他拓扑历史产物。
5. 对旧状态、旧 `DesignReport`、旧磁件推荐对象进行显式初始化，禁止隐式复用。
6. 定义阶段状态：`not_started`、`running`、`succeeded`、`failed`、`blocked`。

### 验收标准

- 新运行生成唯一 `run_id`。
- 空输出目录运行后，不会出现历史变压器或外置电感 ID。
- 运行失败时上下文能记录失败阶段和错误原因。
- 同一进程连续运行两次时，第二次不继承第一次的磁件结果。

### 预计测试

- 运行上下文单元测试。
- 连续两次 LLC 运行的状态隔离测试。
- 清理旧结果后的输出边界集成测试。

## 第 2 步：修复 LLC 变压器结果生成和持久化

### 目标

确保 LLC 变压器搜索确实执行，并且成功或失败都产生可判断的结果状态。

### 具体修改

1. 检查 LLC 主流程是否调用变压器候选搜索，而不是直接复用旧的 transformer result。
2. 检查调用参数是否完整传递：
   - `Vin` 范围
   - `Vout` 和功率
   - `fs` 或 FHA 求解频率
   - `Lm target`
   - 匝比
   - 漏感目标或允许范围
   - 磁通密度限制
   - 绕组和热约束
3. 确保成功时写出：
   - `llc_transformer_feasible_candidates.csv`
   - `llc_transformer_pareto_front.csv`
   - `llc_transformer_chosen_candidates.csv`
   - `llc_transformer_leakage_rejection_audit.csv`
4. 确保 chosen candidates 至少包含 `recommended`、`min-volume`、`min-loss` 或明确缺失状态。
5. 搜索无候选、参数无效、文件写入失败时，记录结构化失败原因，不生成伪造的 chosen result。
6. 变压器结果写入完成后才把 transformer result ID 放入运行上下文。

### 验收标准

- 成功运行时 `transformer_design` 中的必需 CSV 均存在且非空。
- CSV 中的推荐 ID 与运行上下文中的 transformer ID 相同。
- 失败运行时不会生成外置 Lr、硬件总览或最终 manifest 的成功状态。
- 变压器目录为空时，系统明确报告 `transformer_search_failed` 或等价状态。

### 预计测试

- 变压器搜索成功持久化测试。
- 变压器无候选测试。
- 变压器结果文件缺失时的阻断测试。

## 第 3 步：修复外置谐振电感结果链路

### 目标

确保外置 Lr 只使用本次成功的变压器结果，并且 CSV、Pareto 和几何文件成套生成。

### 具体修改

1. 将外置 Lr 搜索的前置条件改为当前运行的变压器阶段必须为 `succeeded`。
2. 使用当前变压器的 `estimated_lk_uH` 计算：

   ```text
   external_Lr_target = total_Lr_target - transformer_leakage
   ```

3. 禁止从全局状态、上次页面状态或旧硬件总览读取变压器漏感。
4. 确保成功时写出：
   - `llc_external_resonant_inductor_feasible_candidates.csv`
   - `llc_external_resonant_inductor_pareto_front.csv`
   - `llc_external_resonant_inductor_chosen_candidates.csv`
   - 推荐、最小体积、最小损耗 2D/3D 几何文件
5. 几何生成必须接收当前 chosen candidate，而不是按固定文件名或历史推荐 ID 查找。
6. 无外置 Lr 目标、目标小于等于零、无可行候选或几何渲染失败时，记录对应阶段状态和原因。

### 验收标准

- 外置电感 CSV 和几何文件来自同一个 `run_id` 和 design ID。
- `target_l_uH`、`actual_l_uH`、`transformer_lk_uH` 和 `total_lr_actual_uH` 均存在。
- 仅有几何文件而没有 CSV 时，运行状态判定为不完整。
- 变压器阶段失败时不会生成外置 Lr 成功结果。

### 预计测试

- 外置 Lr 结果持久化测试。
- 变压器漏感传递和总 Lr 闭合测试。
- 几何文件与 chosen candidate ID 一致性测试。

## 第 4 步：统一磁件参数和结果 ID 传递

### 目标

建立变压器、外置 Lr 和组合磁件之间的单一结果合同，消除旧 ID 和旧参数混入。

### 具体修改

1. 为 LLC 磁件组合定义结构化结果合同，至少包含：
   - `run_id`
   - `topology_id`
   - `transformer_design_id`
   - `external_lr_design_id`
   - `combined_magnetic_design_id`
   - `Np`、`Ns`
   - `Lm target`、`Lm actual`
   - `transformer leakage`
   - `external Lr target`、`external Lr actual`
   - `total Lr target`、`total Lr actual`
   - `fs`、电压和电流基准
2. 在 pipeline 边界处使用该合同，不使用散落的字符串字段拼接结果。
3. 增加硬性闭合校验：

   ```text
   total_Lr_target = transformer_leakage + external_Lr_target
   total_Lr_actual = transformer_leakage + external_Lr_actual
   ```

4. 对 ID 做存在性检查：每个 ID 必须能在本次运行的 CSV 或结构化结果中找到。
5. 任意拓扑 ID、run ID、design ID 不一致时，返回错误或 `blocked`，不得继续生成总览。

### 验收标准

- 当前运行的所有磁件 ID 可相互追溯。
- 总 Lr 目标和实际值在设定容差内闭合。
- 使用旧结果 ID 的测试会失败并给出清晰错误。
- 页面、报告、几何和硬件总览使用同一份磁件组合合同。

### 预计测试

- 磁件合同序列化/反序列化测试。
- ID 追溯和旧 ID 拒绝测试。
- Lr 闭合误差边界测试。

## 第 5 步：修复 LLC 谐振电容推荐约束

### 目标

不允许容量误差超过 10% 的候选成为 LLC 谐振电容推荐方案。

### 具体修改

1. 将 `Cr` 容量误差限制定义为明确配置或设计约束，当前上限为 `10%`。
2. 将容量误差纳入候选可行性判定，而不只是 warning。
3. 推荐排序必须先过滤超出误差限制的候选，再执行体积、损耗和热性能排序。
4. 当存在 `75 nF` 方案时，验证其：
   - 目标 `Cr = 74.3748 nF`
   - 实际 `Cr = 75 nF`
   - 误差约 `+0.841%`
   - 电压和电流利用率满足约束
5. 如果没有满足 10% 误差的候选，输出“无合格推荐”，不得选择超过 10% 的候选冒充推荐。
6. chosen candidates、Pareto front、报告和页面显示同一推荐结果及其约束状态。

### 验收标准

- `recommended` 候选的 `abs(capacitance_error_percent) <= 10`。
- 当前数据下 `80 nF / +7.563%` 属于 10% 约束内候选，最终是否推荐由其他可行性和排序条件决定。
- `75 nF` 候选可被识别为满足容量误差约束的候选。
- 超限候选仍可保留在审计或 near-miss 文件中，但不能进入推荐字段。
- 推荐为空时页面显示明确的无合格候选状态。

### 预计测试

- 容量误差边界测试：9.99%、10.00%、10.01%。
- 推荐排序过滤测试。
- 当前 LLC 电容候选回归测试。

## 第 6 步：修复几何、硬件总览和旧引用

### 目标

让所有几何和硬件总览只使用本次运行已经验证过的结果合同。

### 具体修改

1. 硬件总览生成前校验运行阶段：变压器、外置 Lr、Cr、器件结果必须达到规定状态。
2. 总览只从当前运行上下文和磁件组合合同读取推荐 ID。
3. 删除按固定默认 ID、上一次页面状态或历史 payload 回退的逻辑。
4. 变压器结果缺失时，总览显示缺失状态并阻止生成“完整硬件总览”。
5. 外置电感总览的几何文件必须与当前 `external_lr_design_id` 相同。
6. 总览中的器件名称、损耗、体积和告警均带有来源结果 ID 或 run ID。
7. 对已有旧 payload 做兼容读取时，只允许用于历史查看，不允许作为当前运行输入。

### 验收标准

- 总览中的变压器和外置电感 ID 与本次 chosen candidates 完全一致。
- 不再出现 `Np18:Ns18` 或 `E 55/28/25` 等历史 ID 被当前运行引用的情况。
- 变压器缺失时，不生成误导性的完整总览图。
- 几何文件、CSV 和硬件总览的 run ID、design ID 可相互追溯。

### 预计测试

- 硬件总览装配测试。
- 旧 payload 污染测试。
- 几何文件 ID 一致性测试。

## 第 7 步：修复效率扫描、报告和最终 manifest 依赖

### 目标

保证效率扫描和最终报告只在依赖完整时生成，并让所有结果可审计。

### 具体修改

1. 明确效率扫描依赖：
   - 当前电气设计结果
   - 当前半导体推荐
   - 当前变压器合同
   - 当前外置 Lr 合同
   - 当前 Cr 推荐
2. 依赖缺失、推荐为空或结果 ID 不一致时，效率扫描状态设为 `blocked`，不生成成功图。
3. 在效率结果或 manifest 中记录：
   - `run_id`
   - `topology_id`
   - 输入摘要
   - `transformer_design_id`
   - `external_lr_design_id`
   - `cr_design_id`
   - 推荐器件 ID
   - `Lm`、总 `Lr`、`Cr`
4. 修复报告中 `fs`、电流、吞吐功率、模式等字段显示为 `-` 的问题；无数据时显示“未计算”并给出原因。
5. 生成最终 manifest，列出每个阶段状态、结果文件、结果 ID、校验摘要和告警。
6. manifest 的成功状态必须由结果文件存在性、非空性、ID 一致性和约束校验共同决定。

### 验收标准

- 磁件结果不完整时，效率扫描不会被标记为成功。
- 最终 manifest 能完整列出本次运行输入、阶段、文件和推荐项。
- 所有结果文件均能通过 manifest 追溯。
- 报告不再以 `-` 隐藏关键缺失数据。

### 预计测试

- 效率扫描依赖阻断测试。
- manifest 生成和完整性校验测试。
- 缺失字段报告测试。

## 第 8 步：回归测试、全流程验收和手动复核

### 目标

验证清空旧输出后重新运行 LLC，能够生成一组完整、一致、可追溯的结果。

### 具体修改

1. 建立清空旧 LLC 结果后的端到端测试场景。
2. 至少覆盖：
   - 正常 LLC 全流程
   - 变压器搜索失败
   - 外置 Lr 搜索失败
   - 无满足 10% Cr 误差的候选
   - 旧结果文件存在但 run ID 不匹配
   - 几何生成失败
   - 效率扫描依赖缺失
3. 自动检查必需文件：
   - 变压器 feasible、Pareto、chosen 和漏感审计 CSV
   - 外置 Lr feasible、Pareto、chosen CSV
   - Cr feasible、Pareto、chosen CSV
   - 推荐几何文件
   - 效率结果
   - 硬件总览
   - 最终 manifest
4. 自动检查关键约束：
   - `Cr` 误差不超过 10%
   - 变压器 `Lm` 误差满足配置
   - 变压器磁通和热约束通过
   - 外置 Lr 电感误差满足配置
   - 总 Lr 闭合
   - 结果 ID 和 run ID 一致
5. 进行一次真实手动 LLC 设计，保存控制台输出、manifest 和关键 CSV 摘要。
6. 使用人工检查表复核变压器、外置电感、电容、效率、几何和硬件总览。
7. 更新本计划为完成状态，记录最终 commit、测试命令和输出目录。

### 验收标准

- 清空旧结果后，完整 LLC 运行能够重新生成所有必需结果。
- 不读取旧变压器或旧外置电感推荐。
- 推荐 Cr 误差不超过 10%。
- 所有组件、效率和总览属于同一 run ID。
- 失败场景不会生成误导性的成功结果。
- 手动检查表与自动检查结果一致。

### 预计测试

- 完整 pytest 回归测试。
- LLC 端到端运行测试。
- 输出 manifest 校验脚本。
- 人工检查最新 outputs。

## 6. 步骤依赖关系

```text
第 1 步
   |
   +--> 第 2 步 --> 第 3 步 --> 第 4 步
                                  |
                  +---------------+---------------+
                  |                               |
                第 5 步                          第 6 步
                  |                               |
                  +---------------+---------------+
                                  |
                                第 7 步
                                  |
                                第 8 步
```

第 5 步可在第 4 步完成后独立实现，但最终推荐结果必须在第 6、7 步统一接入。第 8 步必须在前 7 步完成后执行。

## 7. 最终交付物

完成本计划后，应具备以下交付物：

- LLC 运行上下文和阶段状态记录。
- 当前运行专属的变压器结果文件。
- 当前运行专属的外置谐振电感结果和几何文件。
- 满足 10% Cr 误差限制的推荐电容，或明确的无合格候选状态。
- 参数和 design ID 一致的硬件总览。
- 依赖完整且可审计的效率扫描结果。
- 最终运行 manifest。
- 覆盖成功、失败、旧结果污染和边界约束的回归测试。
- 每一步对应的 commit 和 push 记录。

## 8. 当前状态

- [x] 第 1 步：运行上下文和结果边界
- [x] 第 2 步：LLC 变压器结果生成和持久化
- [x] 第 3 步：外置谐振电感结果链路
- [x] 第 4 步：磁件参数和结果 ID 统一
- [ ] 第 5 步：谐振电容推荐约束
- [ ] 第 6 步：几何、硬件总览和旧引用
- [ ] 第 7 步：效率扫描、报告和最终 manifest
- [ ] 第 8 步：回归测试和全流程验收

## 9. 第 1 步执行记录

### 已完成的修改

1. 新增 `src/pe_claw_gui/models/llc_run_context.py`，定义 LLC 专用的 `LlcRunContext`：
   - 为每次运行生成唯一 `run_id`。
   - 对规范化后的原始输入生成稳定的 `input_sha256`，并保存输入快照。
   - 为本次运行预留独立的 `outputs/llc_runs/<run_id>` 输出根目录。
   - 初始化 `design`、`magnetics`、`capacitors`、`loss`、`thermal`、`geometry`、`efficiency_sweep`、`hardware_overview`、`manifest` 阶段。
   - 支持 `not_started`、`running`、`succeeded`、`failed`、`blocked` 状态，以及失败阶段和原因记录。
   - 保存变压器、外置 Lr、Cr 和器件结果 ID，并提供 JSON 兼容的 `to_dict()`。
2. `DesignReport` 增加 `llc_run_context` 字段，使上下文随报告在各 pipeline 之间传递。
3. `run_topology_pipeline` 在 LLC 拓扑完成电气报告后创建全新的运行上下文；非 LLC 拓扑不改变原有行为。
4. GUI `Run Design` 在 LLC 重新运行前清空旧的 `design_report`；设计、磁件、电容和效率阶段进入/离开时更新上下文，异常时记录失败原因并清除失败的设计报告引用。
5. 新增第 1 步专项测试，覆盖运行 ID 隔离、输入摘要稳定性、阶段状态、失败原因、结果 ID 累计和 LLC 拓扑边界。

### 验证记录

- `PYTHONPATH=src python -m pytest tests/test_llc_run_context_step1.py tests/test_dc_ac_operating_refresh_gui_chain.py tests/test_llc_magnetic_requirements_step4.py -q`
- 结果：`13 passed in 15.76s`。
- `python -m compileall -q` 覆盖本步新增/修改的 Python 模块，通过。
- `git diff --check` 通过。

### 提交记录

- 功能提交：`bb9213d feat: add LLC run context isolation`，已 push 到 `origin/codex/sync-gui-backend-from-2`。
- 本计划记录更新提交：`87396ab docs: record LLC run context step 1 commit`，已 push 到 `origin/codex/sync-gui-backend-from-2`。

## 10. 第 2 步执行记录

### 已完成的修改

1. LLC 变压器搜索正式接入本次运行的 `llc_run_context.output_root/transformer_design`，不再依赖 debug 开关或固定历史诊断目录。
2. 变压器搜索和 Pareto 结果始终持久化正式 CSV：
   - `llc_transformer_feasible_candidates.csv`
   - `llc_transformer_pareto_front.csv`
   - `llc_transformer_chosen_candidates.csv`
   - `llc_transformer_leakage_rejection_audit.csv`
3. 在外置 Lr 搜索前校验四个文件存在、非空，且 chosen CSV 与内存结果至少包含 `recommended`、`min-volume`、`min-loss` 三个角色；chosen ID 必须存在于 feasible 集合。
4. 只有上述 artifact 校验完成后，才通过 `LlcRunContext.with_result_ids()` 写入本次运行的 `transformer_design_id`。
5. 增加 `failure_code`、`failure_reason` 和 `artifact_paths` 字段，并覆盖目标缺失、无可行候选、参数异常、文件写入异常和 artifact 不完整等失败状态；失败时不生成外置 Lr 成功结果。
6. GUI `run_active_magnetics()` 检查 LLC 变压器阶段状态，失败或阻断时停止损耗、热和几何后续阶段，不再无条件标记 `magnetics=succeeded`。
7. 结构化报告输出同步暴露失败原因和变压器 artifact 路径。
8. 新增变压器持久化、run-scoped 输出路径和结构化失败状态专项测试，并同步更新正式 artifact 输出策略测试。

### 验证记录

- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step2 tests/test_llc_transformer_persistence_step2.py tests/test_llc_magnetic_result_display_step2.py -q`
- 结果：`9 passed in 3.42s`。
- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step2 tests/test_llc_magnetic_performance_baseline.py tests/test_llc_magnetic_result_display_step2.py tests/test_llc_transformer_persistence_step2.py -q`
- 结果：`27 passed in 76.92s`。
- `PYTHONPATH=src python -m compileall -q src` 通过。
- `git diff --check` 通过。
- 系统默认 pytest 临时目录因权限返回 `WinError 5`，验证已切换到工程内未跟踪的 `.pytest-tmp-step2`；该目录未加入 Git。

### 提交记录

- 功能提交：`73f4bfe fix: persist LLC transformer magnetic results`，已 push 到 `origin/codex/sync-gui-backend-from-2`。
- 本计划记录提交：`0ad55aa docs: record LLC transformer persistence step 2`，已 push 到 `origin/codex/sync-gui-backend-from-2`。

## 11. 第 3 步执行记录

### 已完成的修改

1. LLC 变压器搜索成功后，外置谐振电感搜索始终生成本次运行的正式结果 CSV，不再依赖 `llc_debug_outputs`：
   - `llc_external_resonant_inductor_feasible_candidates.csv`
   - `llc_external_resonant_inductor_pareto_front.csv`
   - `llc_external_resonant_inductor_chosen_candidates.csv`
2. 外置 Lr 的正式 CSV 写入当前 `LlcRunContext.output_root/resonant_inductor_design`，几何 pipeline 也从同一运行目录读取和写入结果，避免引用固定目录中的历史文件。
3. 外置 Lr 目标继续根据当前变压器候选的漏感计算：
   `external_Lr_target = total_Lr_target - transformer_leakage`。
4. 在接受外置 Lr 结果前校验三类 CSV 均存在且非空，并校验 chosen candidates 包含 `recommended`、`min-volume`、`min-loss` 三个角色。
5. 增加 chosen candidate ID 一致性校验：chosen ID 必须存在于当前 feasible candidates，chosen CSV 中的持久化 ID 必须与当前内存结果一致；校验通过后才写入 `external_lr_design_id`。
6. 外置 Lr 无可行候选、正式 artifact 缺失或 chosen ID 不一致时，记录 `failure_code`、`failure_reason` 和 artifact 路径，将磁件阶段标记为 `blocked`，不生成成功的组合磁件结果。
7. 几何目标生成失败时将 geometry 阶段标记为 `blocked` 并记录原因，全部成功时才将 geometry 阶段标记为 `succeeded`。
8. `RunDesignController` 同时检查变压器和外置 Lr 阶段状态，只有两者均可接受时才将 LLC 磁件阶段标记为 `succeeded`。
9. 新增外置 Lr 结果持久化专项测试，并更新正式输出策略测试，覆盖 CSV 集合、代表角色、stale ID 拒绝及 run-scoped 几何输出路径。

### 验证记录

- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step3 tests/test_llc_external_lr_persistence_step3.py tests/test_llc_external_lr_prefilter.py tests/test_llc_magnetic_result_display_step2.py tests/test_llc_magnetic_performance_baseline.py -q`
- 结果：`30 passed in 80.29s`。
- `PYTHONPATH=src python -m compileall -q src` 通过。
- `git diff --check` 通过。
- 测试临时目录和既有 `outputs/` 均未加入 Git。

### 提交记录

- 功能提交：`49d189b fix: persist LLC external resonant inductor results`，已 push 到 `origin/codex/sync-gui-backend-from-2`。
- 本计划记录提交：`3263628 docs: record LLC external resonant inductor step 3`，已 push 到 `origin/codex/sync-gui-backend-from-2`；本次文档准确性修正随后单独提交并 push。

## 12. 第 4 步执行记录

### 已完成的修改

1. 新增 `LlcMagneticCombinationContract`，作为分离式 LLC 变压器、外置 Lr 和组合磁件的统一结果合同，包含：
   - `run_id`、`topology_id`；
   - 变压器、外置 Lr 和组合磁件 design ID；
   - `Np`、`Ns`、`Lm target/actual`；
   - 变压器漏感、外置 Lr target/actual、总 Lr target/actual；
   - 频率、电压范围、电流基准和电流值；
   - 变压器及外置 Lr artifact 路径。
2. 为合同增加 `to_dict()` / `from_dict()`，用于结构化报告、硬件总览和后续 manifest 的统一序列化与恢复。
3. 为 `LlcRunContext` 增加 `combined_magnetic_design_id`，使组合 ID 与变压器、外置 Lr ID 一起处于当前运行上下文中。
4. LLC 磁件 pipeline 改为从当前推荐候选一次性构造组合合同，并在下游阶段前执行硬性校验：
   - 拓扑 ID 与 run ID 必须匹配；
   - 变压器及外置 Lr design ID 必须存在于当前运行的 feasible candidate 集合；
   - 组合 ID 必须严格等于 `transformer_id+external_lr_id`；
   - `total_Lr_target = transformer_leakage + external_Lr_target`；
   - `total_Lr_actual = transformer_leakage + external_Lr_actual`。
5. 合同校验失败时，磁件结果记录 `contract_inconsistent` 和明确原因，磁件阶段标记为 `blocked`，不再继续生成可信的组合结果。
6. 损耗、热、几何元数据、结构化报告、硬件总览和 LLC 结果文本优先读取统一合同；无运行上下文的历史展示夹具保留兼容读取路径。
7. 新增第 4 步专项测试，覆盖合同序列化/反序列化、ID 追溯、旧 design ID、旧 run、错误拓扑、目标/实际 Lr 闭合边界，以及外置 Lr 不需要时的合法状态。

### 验证记录

- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step4 tests/test_llc_magnetic_combination_contract_step4.py -q`
- 结果：`4 passed in 3.61s`。
- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step4 tests/test_llc_magnetic_combination_contract_step4.py tests/test_llc_magnetic_result_reporting_step5.py tests/test_llc_magnetic_result_display_step2.py -q`
- 结果：`15 passed in 3.45s`。
- `PYTHONPATH=src python -m pytest --basetemp .pytest-tmp-step4 tests/test_llc*.py -q`（PowerShell 中使用显式文件列表执行）
- 结果：`67 passed in 100.07s`。
- `PYTHONPATH=src python -m compileall -q src tests` 通过。
- `git diff --check` 通过。
- 第 4 步测试临时目录及既有 `outputs/`、`__pycache__` 均未加入 Git。

### 提交记录

- 功能提交：`a16a3cf fix: unify LLC magnetic result contract`，已 push 到 `origin/codex/sync-gui-backend-from-2`。
- 本计划记录提交：`f675ea8 docs: record LLC magnetic contract step 4`，已 push 到 `origin/codex/sync-gui-backend-from-2`；本次文档准确性修正随后单独提交并 push。

## 13. LLC 谐振电容第 5 步修复执行记录

### 第 1 步：统一 10% 约束合同

- 已将本计划中的活动 LLC Cr 约束、验收标准和测试边界从 5% 同步为 10%；原第 1 节保留历史问题现象说明。
- LLC Cr 搜索将 warning threshold 绑定到 hard limit 配置，并将 coverage summary 统计字段改为通用的 `within_error_limit_*` 命名，同时记录约束来源。
- 验证：`PYTHONPATH=src python -m pytest tests/test_capacitor_selection.py -q --basetemp .pytest-tmp-step5-step1`，结果 `33 passed`。
- `PYTHONPATH=src python -m compileall -q src` 和 `git diff --check` 通过。
- 本修复计划：`Plan/active/llc_resonant_capacitor_step5_fix_plan.md`。

### 第 2 步：补齐 LLC Cr 专项测试和候选状态

- 新增 LLC Cr 专项边界和回归测试，覆盖 9.99%、10.00%、10.01%、75 nF、80 nF、无推荐和 near-miss 场景。
- Cr CSV 增加 `is_pareto`、`recommended_flag` 和 `rejection_reason` 审计字段。
- 验证：`PYTHONPATH=src python -m pytest tests/test_llc_resonant_capacitor_constraint_step5.py tests/test_capacitor_selection.py -q --basetemp .pytest-tmp-step5-step2c`，结果 `37 passed`。
- `PYTHONPATH=src python -m compileall -q src tests` 和 `git diff --check` 通过。

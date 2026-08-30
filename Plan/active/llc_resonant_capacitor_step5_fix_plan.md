# LLC 谐振电容第 5 步修复计划

## 1. 目标

完成 LLC 谐振电容推荐约束的第 5 步收口，解决以下问题：

1. 计划文件仍使用旧的 5% 容量误差口径，而代码已经改为 10%。
2. LLC Cr 缺少专用边界测试，无法证明 10% 硬限制、推荐过滤和无候选行为正确。
3. 本次没有可行候选时，旧的 Cr CSV、Pareto 文件或推荐结果可能残留。
4. LLC Cr 搜索结果没有完整进入结构化报告、Capacitor 页面和 Pareto 页面。
5. 当前 `outputs` 是旧阈值下的运行结果，不能作为最新实现的验收依据。

## 2. 执行规则

- 按第 1 步到第 5 步顺序执行。
- 每一步只修改该步骤范围内的文件。
- 每一步完成后执行针对性测试、`git diff --check`、提交并 push。
- 不回退用户已有修改，不删除与本次 LLC Cr 修复无关的历史结果。
- `CAPACITANCE_ERROR_LIMIT_PERCENT` 和 `CAPACITANCE_WARNING_PERCENT` 当前统一为 10%。
- 10% 是容量误差硬限制：`abs(capacitance_error_percent) <= 10%` 才能进入 feasible、Pareto、chosen 或 recommended。

## 3. 第 1 步：统一 10% 约束合同

### 修改安排

1. 将本计划及原 LLC 结果链路计划中第 5 步、第 8 步、最终交付物和验收标准中的 LLC Cr `5%` 统一改为 `10%`。
2. 检查 LLC Cr 搜索实现中的筛选、Pareto、推荐、warning 和无候选文案，确保全部使用统一配置。
3. 将重复的 `within_10_percent` 等统计改为由实际限制值派生，避免以后修改阈值时统计名称和数值不一致。
4. 在 `coverage_summary` 和结构化结果准备字段中记录实际 hard limit、warning threshold 和约束来源。
5. 保持当前用户决策：hard limit 和 warning threshold 均为 10%，不恢复 5% warning。

### 验证安排

- 搜索代码和计划文件，确认没有与当前实现冲突的 LLC Cr `5%` 要求。
- 检查结果 summary 中限制值为 10%。
- 执行相关单元测试和 `git diff --check`。

### 提交边界

建议提交信息：`docs: sync LLC capacitor plan with 10 percent constraint`

## 4. 第 2 步：补齐 LLC Cr 专项测试和候选状态

### 修改安排

1. 新增 LLC Cr 专项测试文件，构造最小化的电容候选和设计请求。
2. 覆盖 `9.99%`、`10.00%`、`10.01%` 三个误差边界。
3. 覆盖当前实际场景：目标约 `74.3748 nF`、`75 nF` 约 `+0.841%`、`80 nF` 约 `+7.563%`。
4. 验证容量误差超限候选的 `rejection_reason` 为 `capacitance_error`，不能进入 feasible、Pareto、chosen 或 recommended。
5. 验证只有超限候选时推荐为空，但 near-miss 仍然保留。
6. 验证 feasible、Pareto、chosen 和 recommended 的候选 ID、推荐标记、Pareto 标记和约束状态一致。
7. 扩展 LLC Cr CSV 字段，至少记录 `rejection_reason`、`is_pareto` 和 `recommended_flag`，让审计结果不依赖推断。

### 验证安排

- 运行新增专项测试、通用电容测试。
- 检查所有被标记为 recommended 的候选均满足 10% 限制。
- 检查 near-miss 文件仍记录超限容量候选和拒绝原因。

### 提交边界

建议提交信息：`test: cover LLC resonant capacitor 10 percent constraint`

## 5. 第 3 步：修复旧 Cr artifact 残留

### 修改安排

1. LLC Cr 搜索开始时清理当前输出边界内的旧 Cr 专用 artifact。
2. 清理范围限定为 LLC Cr feasible、Pareto、chosen、near-miss 和 Pareto 图，不影响其他拓扑、变压器和电感结果。
3. 有可行候选时，成套生成 feasible、Pareto、chosen 和 Pareto 图，并返回本次生成的路径。
4. 无可行候选时，返回空推荐和空 chosen；不生成推荐 Pareto 图，不允许读取旧推荐。
5. 对无候选场景生成稳定的空结果文件或明确的缺失状态，使调用方可以区分“本次无候选”和“未执行”。
6. 增加重复运行测试：第一次有推荐，第二次无候选，第二次不能继承第一次的推荐。

### 验证安排

- 使用临时输出目录测试有候选和无候选两种运行。
- 检查无候选后固定文件名下不存在旧的 chosen/Pareto 内容。
- 检查 near-miss 可以独立保留。

### 提交边界

建议提交信息：`fix: prevent stale LLC capacitor artifacts`

## 6. 第 4 步：接入结构化报告和 GUI

### 修改安排

1. 在 `structured_output.py` 中增加 LLC Cr 专用 payload。
2. 输出搜索状态、Cr target、推荐 bank 容量、误差、10% 限制、候选数量、推荐 ID、near-miss 信息、拒绝统计和 artifact 路径。
3. 在 Capacitor 页面摘要中显示 LLC Cr 的目标、实际推荐、容量误差和约束状态。
4. 无推荐时显示明确的 `recommended: none` 和无合格候选原因。
5. 在 Capacitor Pareto 页面增加 LLC Cr 结果入口或专用摘要，避免只显示普通 input/output capacitor。
6. 所有页面和报告只从 `report.capacitor.llc_resonant_capacitor_search_result` 读取，不从固定输出路径或历史 payload 回退。
7. 增加报告和页面测试，验证推荐 ID、容量误差和 10% 状态一致。

### 验证安排

- 构造有推荐和无推荐两种 `DesignReport`。
- 检查结构化报告与页面摘要均能表达推荐和失败状态。
- 检查展示的推荐 ID 与 chosen CSV 中的推荐候选一致。

### 提交边界

建议提交信息：`feat: expose LLC resonant capacitor results in reports and GUI`

## 7. 第 5 步：清理旧输出并完成端到端验收

### 修改安排

1. 仅清理当前旧的 `outputs/resonant_capacitor_design` 结果，不修改源代码和其他拓扑输出。
2. 使用最新代码重新运行 LLC 设计。
3. 检查新 chosen CSV 不含超过 10% 的推荐候选，且不存在旧的 5% warning 文案。
4. 检查 near-miss 中保留容量超限候选，并记录明确拒绝原因。
5. 检查结构化报告、Capacitor 页面、Pareto 页面和 CSV 使用同一 Cr design ID。
6. 运行 LLC Cr 专项测试、通用电容测试、报告/UI 测试和 LLC 回归测试。
7. 执行 Python 编译检查、`git diff --check`、artifact 存在性和 CSV 内容检查。
8. 更新原 LLC 结果链路计划，将第 5 步标记为完成，记录本次测试命令、输出目录和最终 commit。

### 验收标准

- 推荐候选容量误差不超过 10%。
- 10.01% 候选不能进入推荐链路。
- 无可行候选时推荐为空，且没有旧结果污染。
- Cr 结果在 CSV、结构化报告和 GUI 中可追溯且一致。
- 最新手动运行产物不再出现 5% 旧文案。

### 提交边界

建议提交信息：`test: validate LLC capacitor constraint end to end`

## 8. 计划状态

- [x] 已建立修复范围和五步执行安排
- [x] 第 1 步：统一 10% 约束合同
- [x] 第 2 步：LLC Cr 专项测试和候选状态
- [x] 第 3 步：旧 Cr artifact 生命周期
- [ ] 第 4 步：结构化报告和 GUI 接入
- [ ] 第 5 步：清理旧输出和端到端验收

## 9. 执行记录

| 步骤 | 状态 | Commit | Push | 验证 |
|---|---|---|---|---|
| 计划文件 | 已建立 | `0fe72bd` | 已 push | 已完成 |
| 第 1 步 | 已完成 | `fed2fef` | 已 push | `33 passed`；compileall、diff-check 通过 |
| 第 2 步 | 已完成 | `2a8dbef` | 已 push | `37 passed`；compileall、diff-check 通过 |
| 第 3 步 | 已完成 | 待提交 | 待 push | `38 passed`；compileall、diff-check 通过 |
| 第 4 步 | 未开始 | - | - | - |
| 第 5 步 | 未开始 | - | - | - |

### 第 1 步执行记录

- 已将原 LLC 结果链路计划中第 5 步、第 8 步、验收标准和最终交付物的活动约束统一为 10%。
- LLC Cr 搜索的 warning threshold 与 hard limit 改为同一配置来源；coverage summary 增加约束来源，并使用与实际阈值无关的通用统计字段名。
- 验证：`PYTHONPATH=src python -m pytest tests/test_capacitor_selection.py -q --basetemp .pytest-tmp-step5-step1`，结果 `33 passed`。
- 验证：`python -m compileall -q src` 通过；`git diff --check` 通过。
- Commit：待提交；Push：待 push。

### 第 2 步执行记录

- 新增 `tests/test_llc_resonant_capacitor_constraint_step5.py`，覆盖 9.99%、10.00%、10.01% 边界、75 nF/80 nF 场景、仅超限候选、near-miss 以及推荐/CSV 状态一致性。
- LLC Cr CSV 增加 `is_pareto`、`recommended_flag` 和 `rejection_reason` 字段。
- 验证：`PYTHONPATH=src python -m pytest tests/test_llc_resonant_capacitor_constraint_step5.py tests/test_capacitor_selection.py -q --basetemp .pytest-tmp-step5-step2c`，结果 `37 passed`。
- 验证：`python -m compileall -q src tests` 通过；`git diff --check` 通过。
- Commit：待提交；Push：待 push。

### 第 3 步执行记录

- LLC Cr 搜索入口现在只清理 LLC Cr 专用的 feasible、Pareto、chosen、near-miss CSV、Pareto 图和 Cr 几何图，不影响其他磁件及拓扑输出。
- 有候选时成套写出本次 feasible、Pareto、chosen CSV；无候选时写出只有表头的空结果 CSV，并返回空推荐和空 chosen。
- 新增重复运行回归测试：第一次有推荐、第二次仅有超限候选时，旧 Pareto 图和推荐几何被清理，第二次不继承旧推荐。
- 验证：`PYTHONPATH=src python -m pytest tests/test_llc_resonant_capacitor_constraint_step5.py tests/test_capacitor_selection.py -q --basetemp .pytest-tmp-step5-step3`，结果 `38 passed`。
- `PYTHONPATH=src python -m compileall -q src tests` 和 `git diff --check` 通过。
- Commit：待提交；Push：待 push。

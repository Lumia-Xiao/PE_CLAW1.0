# LLC 磁件 PF 导航与代表性结果显示修复计划

## 1. 计划信息

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-31` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 用户指定路径 | `C:\Users\Lumia\Documents\PE\_Claw\PE-Claw1.0`（当前不存在） |
| 目标拓扑 | `llc_resonant_converter_diode_rectifier` |
| 目标功能 | LLC 变压器/外置 Lr PF 导航及磁件代表性结果显示 |
| 计划步骤 | 6 步 |
| 计划文件 | `Plan/active/llc_magnetic_pf_and_representatives_ui_fix_plan.md` |

本计划只处理 LLC 磁件结果的 PF 导航、代表性候选显示、几何代表性结果显示和相关
结果契约。不修改 LLC FHA 电气模型、变压器搜索算法、外置 Lr 搜索算法、磁损模型、
热模型或 Pareto 判定规则，除非验证发现结果字段无法完整传递且需要进行最小范围的
契约补齐。

## 2. 问题基线

当前 LLC 运行结果已经能够生成以下两类 Pareto 图和候选文件：

- 变压器 PF：`llc_transformer_pareto_front.png`、对应 CSV 和 chosen CSV。
- 外置谐振电感 PF：`llc_external_resonant_inductor_pareto_front.png`、对应 CSV 和 chosen CSV。

当前界面存在以下问题：

1. `InductorPFView` 只有一条通用电感 PF 图片显示路径，没有像电容 PF 页面那样按
   LLC 磁件角色切换的导航控件，因此用户无法在变压器 PF 和外置 Lr PF 之间切换。
2. LLC 磁件结果对象和搜索结果中已经存在 `recommended`、`min-volume` 和 `min-loss`
   代表性候选，但页面摘要主要显示推荐设计，不能完整查看三个代表性结果。
3. LLC 默认输出策略可能只启用 `recommended` 几何角色，导致 `min-volume` 和 `min-loss`
   几何结果没有进入默认结果页面。
4. 通用 `magnetic.artifact_paths` 同时承载多种 LLC artifact，界面如果依赖文件顺序或
   文件名猜测角色，容易出现 PF 图片和结果 ID 错配。

## 3. 现状代码范围

重点检查和可能修改的文件：

- `src/pe_claw_gui/app/result_views/inductor_pf_view.py`
- `src/pe_claw_gui/app/result_views/capacitor_pf_view.py`
- `src/pe_claw_gui/app/result_views/inductor_view.py`
- `src/pe_claw_gui/app/result_views/geometry_view.py`
- `src/pe_claw_gui/app/result_views/llc_result_text.py`
- `src/pe_claw_gui/app/shell/workspace.py`
- `src/pe_claw_gui/models/magnetic_result.py`
- `src/pe_claw_gui/reports/structured_output.py`
- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/pipeline/run_geometry_pipeline.py`
- LLC 变压器和外置 Lr 设计结果生成模块

重点复用的现有模式：

- `CapacitorPFView` 的多页 PF Notebook 结构。
- `GeometryView` 已有的 `Min-volume`、`Min-loss`、`Recommended` 三列布局。
- LLC 变压器和外置 Lr 搜索结果中已有的 `representative_by_role`、
  `min_volume_candidate`、`min_loss_candidate` 和 chosen CSV 机制。

## 4. 执行规则

1. 严格按第 1 步至第 6 步执行；前一步验证通过后再进入下一步。
2. 每一步只修改该步骤声明的代码、测试和计划记录，避免无关重构。
3. 每一步完成后必须执行针对性测试、`compileall` 或等价编译检查，以及
   `git diff --check`。
4. 每一步验证通过后单独创建 commit，并立即 push 到当前工作分支对应的远端分支。
5. push 成功前，该步骤不得标记为 `completed`。
6. 计划记录更新应有独立的计划记录 commit；如果实现提交与计划记录无法合并，必须
   单独 commit/push，并在本文件记录两个 commit ID。
7. 不删除历史设计结果，不修改用户未授权的其他拓扑页面。
8. 发现当前 run、历史 run 或 artifact 路径不一致时，必须显示 unavailable/blocked
   原因，不得使用历史文件或另一类磁件结果进行回退显示。

## 5. 预期目标状态

完成本计划后，LLC 页面应满足：

- `Inductor PF` 页面提供两个 LLC 专用切换页：
  - `Transformer PF`
  - `External Resonant Inductor PF`
- 两个切换页分别显示对应的 PF PNG、Pareto 数量、候选数量、chosen 数量和推荐 ID。
- 变压器和外置 Lr 均能显示 `recommended`、`min-volume`、`min-loss` 三类代表性结果。
- 默认 LLC 几何页面和磁件摘要不会只展示推荐结果而隐藏另外两类结果。
- PF、CSV、geometry、report 和 run context 的拓扑、run ID、design ID 能够相互追溯。
- 非 LLC 普通电感 PF 页面继续保持原有单图行为。
- 电容 PF 页面及其 input/output/LLC Cr 切换功能不受影响。
- 无候选、缺 artifact、缺代表性角色和结果 ID 不一致时，页面显示明确状态，不伪造结果。

## 6. 六步实施计划

### 第 1 步：冻结 LLC PF 与代表性结果基线

#### 目标

建立可重复的 LLC 界面和结果基线，确认问题来自结果消费/显示链路，而不是 PF 搜索
本身没有生成数据。

#### 具体安排

1. 选取当前有效的 `400 V -> 400 V` LLC run 作为基线；记录 run ID、topology ID、输入
   checksum 和 manifest 状态。
2. 检查变压器和外置 Lr 的 feasible CSV、Pareto CSV、chosen CSV 和 PF PNG 是否存在、
   非空且属于同一个 run。
3. 从两个搜索结果中读取 `recommended`、`min-volume`、`min-loss` 的 design ID，记录
   候选数量、Pareto 数量、体积、损耗和热点等关键字段。
4. 记录当前界面行为：`Inductor PF` 仅有一张图片，LLC 磁件摘要和几何页当前显示的
   代表性角色集合。
5. 新增或冻结测试 fixture，至少覆盖：完整 LLC 结果、缺少外置 Lr PF、缺少某个代表性
   候选、非 LLC 普通电感结果。
6. 生成本步骤基线证据，不能覆盖现有 migration evidence 或历史 golden baseline。

#### 验收标准

- 能明确证明变压器 PF 和外置 Lr PF 文件均已由后端生成。
- 能明确记录两个搜索结果的三类代表性候选是否存在。
- 基线测试稳定复现当前单图/推荐结果行为。
- 缺文件和缺候选 fixture 能表达 unavailable，而不是抛出未处理异常。

#### 预计验证

- LLC 结果显示相关专项测试。
- artifact 存在性、非空性和 run ID 一致性检查。
- `python -m compileall -q src tests`。
- `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 1: freeze PF representative baseline`

计划记录提交必须记录实现 commit、测试命令和 push 结果。

### 第 2 步：增加 LLC PF 双图切换导航

#### 目标

参考 `CapacitorPFView`，将单一 `InductorPFView` 扩展为对 LLC 角色有明确区分的 PF
切换界面。

#### 具体安排

1. 在 `InductorPFView` 中增加 Notebook 或等价切换控件，提供：
   - `Transformer PF`
   - `External Resonant Inductor PF`
2. LLC 拓扑显示两个专用页；非 LLC 拓扑保留原有单图电感 PF 页，不出现 LLC 专用页。
3. 为每个页建立独立的 plot host、placeholder、summary 文本和 canvas 生命周期，避免
   切换后复用旧 canvas 或旧 summary。
4. 变压器页只解析变压器 PF PNG；外置 Lr 页只解析外置 Lr PF PNG，禁止交叉回退。
5. 页面摘要分别显示来源 artifact 路径、Pareto 数量、候选数量、chosen 数量以及
   对应推荐设计 ID。
6. 缺少某一类 PF 图片时，仅该页显示 unavailable 原因，另一页仍可正常显示。
7. 检查窗口缩放、Notebook 重绘、报告刷新和从 LLC 切换到非 LLC 拓扑时的状态清理。

#### 验收标准

- LLC `Inductor PF` 下可见且可切换两个 PF 页面。
- 变压器页显示 `llc_transformer_pareto_front.png`。
- 外置 Lr 页显示 `llc_external_resonant_inductor_pareto_front.png`。
- 两个页的摘要不混用对方的 CSV、图片或 design ID。
- 普通电感和电容 PF 页面回归通过。

#### 预计验证

- `InductorPFView` 单元/视图构造和路径解析测试。
- LLC/非 LLC 页面切换回归。
- 现有 `test_phase10_gui_integration.py` 相关测试。
- `python -m compileall -q src tests`。
- `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 2: add transformer and external Lr PF tabs`

### 第 3 步：补齐 PF artifact 与结果 ID 的独立契约

#### 目标

让界面直接消费有明确角色含义的 PF artifact 和结果字段，消除依赖通用 artifact 列表
顺序的隐式行为。

#### 具体安排

1. 检查 `MagneticResult`、LLC transformer Pareto result 和 external Lr search result
   中的 artifact 字段，确认变压器和外置 Lr 的 PF PNG/CSV 可以独立访问。
2. 如现有字段不足，增加最小范围的角色化字段，例如 transformer PF artifact、external
   Lr PF artifact 及对应 CSV；保持旧字段向后兼容。
3. 在 pipeline 写入字段时绑定当前 run 的绝对路径或规范化路径，并验证文件存在性、
   非空性和当前 run 所属关系。
4. 在 `structured_output.py` 中写入两个磁件 PF 的结构化 artifact 区块，包含：
   - role
   - pareto PNG
   - pareto CSV
   - feasible CSV
   - chosen CSV
   - run ID
   - topology ID
5. 结果 ID 必须从当前搜索结果和当前 run context 读取；不得从旧页面状态、固定默认
   ID 或上一次 run 的 payload 回退。
6. 对缺失 artifact、类型不匹配、空文件和 run ID 不一致返回结构化 unavailable 或
   blocked 状态，并保留诊断原因。

#### 验收标准

- 变压器和外置 Lr 的 PF artifact 可以独立、确定性地解析。
- structured output 中两类 PF 的路径和 result ID 与当前 run 一致。
- 旧结果文件存在时不会污染当前 LLC 页面。
- 非 LLC 结构化输出不增加错误的 LLC 字段或错误状态。

#### 预计验证

- 结果契约和结构化输出专项测试。
- stale artifact、missing artifact、wrong-role artifact 测试。
- 当前 run ID 与 artifact 路径一致性测试。
- `compileall` 和 `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 3: expose role-specific PF artifacts`

### 第 4 步：补齐 Transformer 与 External Lr 三类代表性结果

#### 目标

确保后端结果、chosen CSV、结构化报告和界面都能稳定访问三类代表性候选，而不是只有
推荐候选可见。

#### 具体安排

1. 核对变压器 `representative_by_role` 是否始终包含：
   - `recommended`
   - `min-volume`
   - `min-loss`
2. 核对外置 Lr `chosen_candidates`、`min_volume_candidate` 和 `min_loss_candidate`
   是否始终包含同样三类角色。
3. 如果搜索结果已有字段，只修复映射和序列化，不修改代表性候选的选择算法。
4. 确保 transformer chosen CSV 和 external Lr chosen CSV 各自保存三类角色、design ID、
   体积、损耗、热点和关键磁件参数。
5. 为结构化输出增加两个独立的 representatives 区块，明确记录 role、design ID、
   source stage 和主要性能字段。
6. 修改 LLC 结果文本格式化器，使磁件摘要列出变压器和外置 Lr 的三类代表性结果；
   缺少某角色时显示该角色 unavailable 及原因。
7. 保持原有 recommended selection policy 不变；`recommended` 不因新增显示项而被
   `min-volume` 或 `min-loss` 替换。

#### 验收标准

- 两类磁件均能独立返回三类代表性候选或明确缺失原因。
- chosen CSV、structured output、文本摘要中的 role 和 design ID 完全一致。
- recommended、min-volume、min-loss 的体积和损耗字段来源正确。
- 不再用 recommended 结果冒充缺失的 min-volume 或 min-loss。

#### 预计验证

- transformer representative 测试。
- external Lr representative 和 chosen CSV 测试。
- LLC 文本序列化和 structured output 测试。
- 无候选、单一候选和缺角色边界测试。
- `compileall` 和 `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 4: expose magnetic representative designs`

### 第 5 步：接通默认 LLC 几何和磁件页面的三类结果

#### 目标

让默认 LLC 结果页面不再只显示 recommended，并使三类几何结果与对应 role 和 design ID
一一对应。

#### 具体安排

1. 检查 LLC output policy 中 `geometry_roles` 的默认值，调整为：
   - `min-volume`
   - `min-loss`
   - `recommended`
2. 保持 debug/full 模式的完整诊断能力，不因默认显示三类结果而重新生成无关的巨大
   调试输出。
3. 变压器和外置 Lr 分别生成三类 geometry target；每个 target 绑定唯一 role、design
   ID、artifact 路径、体积和损耗。
4. 修改 `InductorView` 和 LLC 文本格式化器，分别显示：
   - Transformer representatives
   - External resonant inductor representatives
   - 每个角色的 design ID、volume、loss、hotspot 和可用状态
5. 修改 `GeometryView` 的 LLC 结果消费，确保 `Min-volume`、`Min-loss`、`Recommended`
   三列使用各自候选；禁止按推荐结果回退填充其他列。
6. 处理代表性结果重复的情况：可以显示相同 design ID，但必须通过 duplicate 标记
   说明原因，不得误报为三个不同候选。
7. 保持非 LLC 固定电感页面原有代表性结果和 geometry 行为不变。

#### 验收标准

- 默认 LLC 磁件页同时显示三类代表性结果。
- 默认 LLC geometry 页同时显示三类角色，且图片/metadata/design ID 对应正确。
- 变压器和外置 Lr 的角色不会互相混淆。
- 缺少某个角色时只影响该角色，不阻塞可用的其他角色显示。
- recommended selection 的实际 design ID 和效率/损耗链路不发生意外改变。

#### 预计验证

- LLC geometry representative 专项测试。
- LLC magnetic result display 专项测试。
- output policy 默认/显式角色模式测试。
- structured output、loss、thermal 和 hardware overview 回归。
- `compileall` 和 `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 5: show all magnetic geometry representatives`

### 第 6 步：全量回归、真实运行验收和计划收口

#### 目标

使用真实 LLC 运行验证 PF 双图切换、三类代表性结果和整个结果链路，确认没有历史结果
污染或非 LLC 回归。

#### 具体安排

1. 清理或隔离本次验收的 LLC 输出目录，不能让旧 run artifact 被当前 run 复用。
2. 使用 `400 V -> 400 V` LLC 输入执行完整流程，至少覆盖 Run Design、Run Magnetics、
   Cr、Loss、Thermal、Geometry、Efficiency Sweep 和 Hardware Overview。
3. 检查变压器和外置 Lr 的 PF PNG 在各自导航页正确显示；记录截图或等价可审计证据。
4. 检查三类代表性结果的页面文本、structured output、chosen CSV、geometry artifact
   和 manifest 是否一致。
5. 运行失败场景：
   - 缺少变压器 PF artifact。
   - 缺少外置 Lr PF artifact。
   - 缺少某个代表性候选。
   - 旧 run artifact 与当前 run ID 不一致。
   - LLC 磁件阶段 blocked。
6. 运行非 LLC 普通电感 PF、非 LLC 磁件页面和 LLC Cr PF 回归，确认原有页面不受影响。
7. 运行专项测试、LLC 回归、必要的工程回归、`compileall` 和 `git diff --check`。
8. 更新本计划每一步的状态、实现 commit、计划记录 commit、push 结果、测试命令和
   验收证据。
9. 只有所有验收项通过且所有提交已 push 后，将计划状态改为 `completed`；如果仍有
   问题，保持 `active` 并记录阻塞原因。

#### 验收标准

- LLC PF 双图切换真实运行通过。
- 变压器和外置 Lr 的 PF 图片、CSV、chosen 结果和 report 互相一致。
- 三类代表性结果在磁件摘要和几何页面均可追溯。
- 正常、缺失、阻断和 stale artifact 场景状态正确。
- 非 LLC 和 LLC 电容页面回归通过。
- 实现 commit、计划记录 commit 均已成功 push。

#### 预计验证

- LLC PF 导航专项测试。
- LLC representative/result display/geometry 专项测试。
- LLC manifest、hardware overview、loss、thermal 和 structured output 回归。
- 真实 `400 V -> 400 V` LLC 全流程验收。
- `python -m compileall -q src tests`。
- `git diff --check`。

#### 提交要求

实现提交信息建议包含：

`LLC UI Step 6: close PF and representative display acceptance`

## 7. 风险和保护边界

1. **旧 artifact 污染风险**：所有 PF、CSV、geometry 和 summary 必须使用当前 run 的
   结果上下文；不得回退到根目录历史输出。
2. **角色错配风险**：变压器 PF、外置 Lr PF、Cr PF 三者必须使用独立字段和独立页面，
   不得只根据通用文件名或列表位置判断角色。
3. **代表性候选为空**：页面必须显示 `unavailable` 或明确原因，不得复制推荐候选填充。
4. **默认输出体积风险**：三类角色的几何输出应复用已有候选和 renderer，不重新启用
   不必要的全量 debug CSV 或大规模诊断输出。
5. **非 LLC 回归风险**：普通电感、AC-DC 磁件、LLC Cr 和电容 PF 页面必须保留既有行为。
6. **历史路径风险**：计划和证据中的历史源工程路径可以保留用于审计，但当前工程目标
   路径必须统一使用实际存在的 `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`。

## 8. 计划状态记录

| 步骤 | 状态 | 实现 commit | 计划记录 commit | Push | 验证摘要 |
| --- | --- | --- | --- | --- | --- |
| 第 1 步 | `completed` | `1010c8d` | 待记录 | `pushed` | 已冻结当前 run `b28792595095416f872f5d9a8b8800f6`；变压器 feasible/Pareto/chosen 为 `10269/16/4`，外置 Lr 为 `11536/28/4`；两类 chosen 均包含 `recommended`、`min-volume`、`min-loss`；输入 checksum 和 run manifest 在当前 payload 中不可用，已明确记录为 unavailable；新增缺失 artifact、缺失角色、非 LLC 边界测试；专项测试 `5 passed`，compileall 与 diff check 通过。实现 commit 已 push。 |
| 第 2 步 | `completed` | `a54bdba` | 待记录 | `pushed` | `InductorPFView` 已增加 LLC 专用 `Transformer PF` 与 `External Resonant Inductor PF` Notebook 页；每页独立维护 plot、placeholder、summary 和 canvas；变压器与外置 Lr 只从各自角色 artifact 集合解析 PF PNG；缺失 artifact、summary 缺失、LLC/非 LLC 模式切换均有明确状态和测试；专项、基线及 GUI 导航回归共 `20 passed`，compileall 与 diff check 通过。实现 commit 已 push。 |
| 第 3 步 | `completed` | `ade4bde` | `77a0026` | `pushed` | 已新增 `LlcPfArtifactContract` 及 role-specific artifact builder；变压器和外置 Lr 的成功、缺失、失败路径均写入当前 run 的独立 contract；结构化输出增加 `magnetic.llc.pf_artifacts.transformer/external_lr`，包含路径、文件状态、SHA256、run/topology identity、推荐 ID 和诊断；PF GUI 优先读取当前 LLC run 的角色化 contract 路径并拒绝错配/越界文件；新增第 3 步专项测试覆盖完整、缺失、空文件、错角色、越界路径、run/topology 错配、structured output、非 LLC 隔离和 GUI 路径解析；专项及相关 LLC 回归共 `42 passed`，compileall 与 diff check 通过。实现 commit 已 push。 |
| 第 4 步 | `pending` |  |  |  | 等待第 3 步完成 |
| 第 5 步 | `pending` |  |  |  | 等待第 4 步完成 |
| 第 6 步 | `pending` |  |  |  | 等待第 5 步完成 |

## 9. 交付物清单

- LLC Transformer PF 导航页。
- LLC External Resonant Inductor PF 导航页。
- 两类磁件的 role-specific PF artifact 契约。
- Transformer 和 External Lr 的 `recommended`、`min-volume`、`min-loss` 结构化结果。
- 默认 LLC 三类 geometry targets 和对应页面显示。
- 失败、缺失和 stale artifact 的结构化诊断。
- 专项测试、真实 LLC 全流程验收证据。
- 每一步独立 commit/push 记录。

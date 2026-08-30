# LLC 最新运行结果链收口修复计划

## 1. 计划信息

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-30` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 目标拓扑 | `llc_resonant_converter_diode_rectifier` |
| 参考运行 | `255120bd9d1b45a5ac3845bf2830927d` |
| 计划步骤 | 8 步 |
| 计划文件 | `Plan/active/llc_latest_run_result_chain_polish_plan.md` |

本计划用于修复最新 LLC 手动测试中发现的结果链和展示层问题。当前运行的磁件搜索、
Pareto 筛选、损耗计算、热筛选、几何输出和 manifest 均已成功生成；本计划不重新设计
LLC FHA 模型、变压器搜索算法、外置 `Lr` 搜索算法、磁芯损耗模型或热模型，而是让
已经产生的有效结果在 DTO、结构化输出、各结果页面和最终验收中保持一致。

## 2. 最新运行基线

参考运行 `255120bd9d1b45a5ac3845bf2830927d` 的 manifest 显示：

- 所有阶段状态为 `succeeded`，manifest `valid=true`。
- 变压器 Pareto 数量为 `16`，推荐变压器为
  `E_80_38_32_SMP97_Np18_Ns18`。
- 外置谐振电感推荐为
  `Lr_ext_E_55_28_25_SMP97_N11_P4`。
- 组合磁件推荐 ID 已生成：
  `E_80_38_32_SMP97_Np18_Ns18+Lr_ext_E_55_28_25_SMP97_N11_P4`。
- `Cr` 实际值相对目标误差为约 `7.563%`，满足当前 `10%` 阈值。
- 热汇总 CSV 已包含真实热点代理值：变压器约 `54.975 C`，外置 `Lr` 约 `46.614 C`。
- 变压器和外置 `Lr` 的候选、Pareto、chosen CSV 均已生成。

## 3. 已确认的问题

### 3.1 Pareto 与 chosen 数量不一致

页面显示 `Pareto count: 16`、`chosen design count: 0`，同时又显示了有效推荐 ID。
原因是 LLC 的变压器和外置 `Lr` 代表性候选保存在 LLC 专用结果结构或专用 CSV 中，
但通用电感 Pareto 页面仍读取 `magnetic.chosen_designs`。该字段为空不能解释为
“没有 chosen 候选”。

### 3.2 热结果已生成但通用热字段为空

`thermal_summary.csv` 和 `llc_component_thermal` 中有真实热点值，但
`ThermalResult.recommended_estimate`、`chosen_design_estimates` 和
`best_by_stack_count` 没有为分离式 LLC 结构建立可显示的映射，导致页面出现
`Recommended hotspot proxy: - C` 和 `No thermal estimate`。

### 3.3 LLC 仍显示不适用的 stack-count 文案

分离式 LLC 是“变压器 + 外置谐振电感”两个独立磁件，不是固定电感的 1-core、2-core、
3-core 堆叠候选。当前 `unavailable` 文案会把有效结果误导为筛选失败。

### 3.4 Design requirements 没有完整读取 LLC 字段

页面仍读取固定电感字段，导致 `fs`、电流、吞吐量、模式等位置出现 `-`。需要明确
哪些电气参数由 LLC 运行上下文提供，哪些只能从磁件候选或 FHA 结果读取；没有真实来源
的字段应显示“未提供”或“不适用”，不能伪造数值。

### 3.5 过期 warning 与成功状态冲突

manifest 在磁件阶段成功且有磁件损耗时仍保留
`Magnetic design has not been run; magnetic loss is omitted.`。需要按当前 report 状态
清理或改写旧 warning，避免最终结果同时声称“已成功”和“磁件未运行”。

### 3.6 几何代表项和角色标识不完整

外置 `Lr` 的 Pareto CSV 中存在 min-volume、min-loss 和 compromise/recommended 代表项，
但页面有时只显示 recommended；同时外置 `Lr` 几何不能被标成 LLC 变压器几何。需要
确保代表项 ID、体积、损耗、重复关系和 component role 一致。

### 3.7 文本转义和字符拆分需要区分处理

粘贴结果中的 `\_` 可能只是 Markdown 转义，不能直接修改路径生成。热 summary 路径
提示被逐字符显示，则需要检查原始字符串、序列化内容和前端渲染过程，确认是数据污染
还是 widget 的换行/文本布局问题。

## 4. 总体目标

完成后，同一份 LLC report、结构化输出、CSV 和页面文本必须满足：

1. Pareto、chosen、recommended 三种数量和 ID 来自同一套 LLC 结果契约。
2. 变压器、外置 `Lr`、组合磁件三个层级明确区分。
3. 热页面能显示推荐组合对应的变压器热点和外置 `Lr` 热点，并保留“分别估算、未建立
   组合热网络”的边界说明。
4. LLC 页面不再显示固定电感专用的 allow/compression/stack-count 默认值。
5. Design requirements 显示真实可追溯的 LLC 参数；缺失参数有明确原因。
6. 成功运行不保留互相矛盾的旧 warning。
7. 几何页面显示真实存在的 LLC 外置 `Lr` 代表项，并标明其组件角色。
8. 原始 CSV、manifest、其他拓扑和固定电感页面不发生回归。

## 5. 保护边界

### 允许修改

- LLC 结果 DTO 的字段映射和适配 helper。
- LLC 专用结果视图、热视图、几何视图和结构化输出格式化。
- LLC warning、阶段状态和结果引用的一致性处理。
- LLC 相关单元测试、集成测试和手动验收脚本。

### 不修改

- LLC FHA 方程、增益求解和工作点计算。
- 变压器/外置 `Lr` 候选生成、可行性条件、损耗模型、Pareto 排序和推荐算法。
- 热模型的物理公式、气隙公差模型和精确 CAD 模型。
- 其他拓扑的结果契约，除非共享代码改动必须增加兼容性分支。
- 用户现有 `outputs/`、pytest 临时目录、缓存和历史运行文件。

### 强制规则

- 不得用 `post_allow_count`、`post_compression_count` 等固定电感字段冒充 LLC 候选数。
- 不得用硬编码的 `54.975 C`、`46.614 C` 或示例 ID 修复页面。
- 不得因修复显示而改变候选搜索结果或推荐选择。
- 每一步只修改该步骤声明的范围。
- 每一步完成后必须先验证，再单独 `commit` 和 `push`；未完成 push 不得标记该步完成。
- 计划状态、commit ID、测试命令和结果必须在本文件对应步骤中记录。

## 6. 分步实施安排

### 第 1 步：冻结最新运行的结果契约和回归基线

#### 修改/准备内容

1. 读取参考 run 的 manifest、变压器候选 CSV、外置 `Lr` 候选 CSV 和 thermal summary，
   记录真实的候选数量、代表性角色、推荐 ID、损耗、体积和热点值。
2. 建立受控 fixture 或最小 report 构造，包含变压器、外置 `Lr`、组合推荐以及热组件数据。
3. 为结果视图、结构化输出和热结果增加当前行为的回归测试，明确捕获：
   - `chosen design count: 0`；
   - `Recommended hotspot proxy: - C`；
   - LLC stack-count 空结果文案；
   - 过期磁件 warning；
   - 几何代表项缺失。
4. 固定 LLC 专用结果契约，明确字段来源、单位、缺失值策略和组件角色。

#### 交付物与验收

- 测试能够稳定复现上述问题，不依赖用户 `outputs/` 中的临时文件。
- 基线记录与参考 run 的 manifest、CSV 数值一致。
- 本步不改变物理计算和候选内容。

#### 预计涉及文件

- `tests/` 下 LLC 结果链、视图和结构化输出测试。
- 必要时新增受控 fixture 文件；不得复制大体积 outputs。

### 第 2 步：统一 LLC Pareto/chosen/recommended 结果映射

#### 修改内容

1. 梳理 `MagneticResult`、LLC transformer result、external `Lr` search result 和
   combined result 的字段关系。
2. 为 LLC 增加明确的 transformer Pareto count、transformer chosen count、external
   `Lr` Pareto count、external `Lr` chosen count 和 combined recommended ID 映射。
3. 让 LLC 结果视图优先读取 LLC 专用字段；只有非 LLC 拓扑继续使用通用固定电感字段。
4. 明确推荐对象层级：
   - transformer recommendation：负责 `Np:Ns` 和 `Lm`；
   - external `Lr` recommendation：负责外置谐振电感；
   - combined recommendation：负责组合结果引用。
5. 让 chosen 计数来自实际 chosen CSV/结构化代表项，而不是空的通用列表。

#### 验收标准

- 页面不再出现 Pareto 有值而 chosen 为 0 的矛盾。
- 变压器和外置 `Lr` 数量分别显示，组合推荐 ID 与 manifest 一致。
- 固定电感、Flyback、PSFB 等页面的 chosen count 行为不变。

#### 预计验证

- LLC 视图单元测试。
- LLC pipeline/structured result mapping 测试。
- 非 LLC 磁件结果回归测试。

### 第 3 步：接通 LLC 热结果到推荐显示字段

#### 修改内容

1. 将 LLC `llc_component_thermal` 中的 transformer 和 external `Lr` 热估算适配到
   页面可消费的结果结构，至少包括 design ID、assembly type、loss basis、ambient、
   hotspot、core loss 和 copper loss。
2. 为推荐组合建立明确的热结果策略：分别显示变压器热点和外置 `Lr` 热点；不把两者
   简单相加为一个虚构的组合温度。
3. 统一 `recommended_estimate`、组件热字段和 thermal CSV 的来源，避免同一运行出现
   CSV 有值但页面字段为空。
4. 将 LLC 的 stack-count 热比较替换为 component comparison，或明确标记该区块不适用于
   分离式 LLC。
5. 保留一阶 hotspot proxy、未建立组合热网络、未进行 CFD/制造级热验证等边界说明。

#### 验收标准

- 推荐变压器显示约 `54.975 C`，推荐外置 `Lr` 显示约 `46.614 C`，数值来自 fixture
  或 report 字段而非硬编码。
- 页面不再显示推荐热点为 `- C`，也不再显示无意义的 1/2/3-core unavailable。
- 热 CSV 与页面的 design ID、损耗和热点值一致。
- 无热数据时仍能正确显示 unavailable，而不是误报 valid。

#### 预计验证

- thermal pipeline 测试。
- LLC thermal result text 测试。
- 无推荐、仅变压器、变压器加外置 `Lr` 三种边界测试。

### 第 4 步：修复 LLC Design requirements 和运行参数传递

#### 修改内容

1. 确认 LLC Design requirements 的真实来源，包括 topology、bridge/rectifier、输入输出
   范围、功率、开关频率、`Lm`、`Lr`、`Cr`、匝比和工作模式。
2. 将 LLC 专用字段映射到结果视图和结构化输出，单位统一为 Hz、V、W、uH、nF、A 等。
3. 对不属于 LLC 或当前 report 未提供的固定电感字段，不显示无上下文的 `-`；改为
   `N/A`、`not provided` 或 LLC 语义等价文本，并在 notes 说明来源。
4. 将电气设计结果、磁件候选结果和 manifest fixed parameters 的数值做一致性检查，
   特别是 `fs`、`Lm actual`、`total Lr actual`、`Cr actual` 和误差阈值。
5. 禁止从候选 CSV 的单个推荐行反向伪造完整电气需求；缺失值必须可追溯地保留为空。

#### 验收标准

- 页面不再把 LLC 的设计需求整体显示成固定电感字段的 `-`。
- 显示数值与 manifest/raw input snapshot/FHA 结果的来源一致。
- `Cr` 误差 `7.563%` 被正确标示为在 `10%` 限制内。
- 不改变任何设计计算结果。

#### 预计验证

- LLC Design requirements 文本测试。
- manifest fixed-parameter consistency 测试。
- 空白字段、边界输入和非 LLC 页面回归测试。

### 第 5 步：修复几何代表项和磁件角色展示

#### 修改内容

1. 从外置 `Lr` Pareto/chosen 结构中绑定 min-volume、min-loss、compromise/recommended
   代表项，按实际存在情况生成页面行。
2. 对不存在的代表项显示明确 unavailable 原因，不把推荐项复制成其他角色而不说明。
3. 在 geometry DTO、页面标题、artifact 清单和硬件总览中标注 `transformer`、
   `external_lr`、`combined` 等角色。
4. 继续把外置 `Lr` 的 2D/3D 几何输出放在其组件目录，不能被误命名为变压器几何。
5. 校验几何页面的 design ID、体积、损耗与对应 CSV 行一致，并保留 duplicate_of 关系。

#### 验收标准

- min-volume、min-loss、recommended 行与 CSV 中的真实代表项一致。
- 推荐外置 `Lr` 的 2D/3D artifact 均可定位，组件角色明确。
- 变压器几何缺失时显示“transformer geometry unavailable”，不隐藏真实限制。

#### 预计验证

- geometry pipeline 测试。
- LLC geometry result view 测试。
- artifact path/role consistency 测试。

### 第 6 步：清理过期 warning 并加强阶段状态一致性

#### 修改内容

1. 找到通用 warning `Magnetic design has not been run; magnetic loss is omitted.` 的生成、
   传播和最终汇总位置。
2. 对 LLC 磁件成功且损耗可用的 report 删除该 warning，或替换为说明当前磁件使用
   first-pass screening 的准确说明。
3. 检查磁件、loss、thermal、geometry、hardware overview 和 manifest 的阶段状态是否
   由同一 report 结果驱动。
4. 对真实失败、无推荐、无热数据和非必需外置 `Lr` 分别保留可解释状态，不能简单全部
   改为 succeeded。
5. 保证 warning 清理不会掩盖磁件模型仍是一阶估算、几何为 proxy 等重要限制。

#### 验收标准

- 参考 run 不再同时出现“磁件成功/损耗存在”和“磁件未运行/损耗省略”。
- 失败或未运行场景仍有正确 warning 和 blocked/unavailable 状态。
- 最终 manifest warning、stage status、result IDs 与页面摘要一致。

#### 预计验证

- manifest validator。
- LLC success/failure/partial-result 集成测试。
- warning snapshot/regression 测试。

### 第 7 步：修复文本序列化、Markdown 转义和页面布局问题

#### 修改内容

1. 对热 summary artifact 提示分别检查：原始 Python 字符串、结构化 JSON、UI 文本模型
   和最终 widget 渲染，定位逐字符拆分发生的层级。
2. 只有确认原始数据包含错误字符时才修改序列化；如果只是 Markdown/HTML 转义或布局
   处理，则修复渲染边界，不改文件路径生成。
3. 验证 Windows 路径中的反斜杠、下划线和空格在页面、manifest 和 artifact link 中均能
   正确显示。
4. 统一换行与列表处理，避免普通 note 被当作逐字符 iterable 展开。
5. 增加包含 Windows 路径和下划线的最小渲染 fixture。

#### 验收标准

- `Thermal summary artifact saved to ...` 以完整一行显示。
- 实际路径不被改写，`_`、反斜杠和目录名在原始数据中保持正确。
- Markdown 转义只影响呈现，不改变 manifest/CSV 的真实字符串。
- 长路径在页面中可读且不覆盖相邻内容。

#### 预计验证

- result text formatter 测试。
- 结构化输出序列化/反序列化测试。
- 真实 Windows 路径手动 UI 验收。

### 第 8 步：全链路重跑、逐项验收和最终收口

#### 修改内容

1. 在新的隔离 LLC run 目录执行完整链路：Design、Magnetics、loss、thermal、geometry、
   hardware overview、efficiency sweep 和 manifest。
2. 使用 manifest validator 检查所有必需 artifact、result ID、stage status、输入摘要和
   fixed parameters。
3. 将页面显示与 CSV/manifest 逐项对照，至少核对：
   - 变压器 evaluated/feasible/Pareto/chosen/recommended；
   - 外置 `Lr` target/feasible/Pareto/chosen/recommended；
   - 组合磁件 ID、总损耗和总体积；
   - 变压器与外置 `Lr` 热点；
   - Cr 实际值和 `10%` 误差阈值；
   - 几何代表项和 artifact 路径；
   - warning 与 stage status。
4. 运行 LLC 全量回归和受影响的非 LLC 回归，检查没有提交 outputs、缓存和临时目录。
5. 在本计划中记录每一步的实现 commit、push 状态、测试命令、测试结果和遗留风险。
6. 仅当所有验收项通过后，将计划状态改为 `completed`；如有未完成项，保留为 `active`
   并明确阻塞原因，不得提前宣告完成。

#### 最终验收标准

- 新 run 的 manifest `valid=true`，必需阶段和 artifact 均成功。
- 页面不再出现本计划列出的数量、热结果、stack-count、warning 和几何代表项错误。
- 页面、结构化输出、CSV 和 manifest 的 ID/数值一致。
- LLC 回归通过，非 LLC 既有测试不回归。
- 工作区不新增用户运行 outputs、pytest 临时目录或缓存提交。

## 7. 计划执行记录

| 步骤 | 状态 | 实现 commit | 计划记录 commit | push | 测试/验收 |
| --- | --- | --- | --- | --- | --- |
| 第 1 步 | `completed` | `b349847` | `2311c67` | `pushed` | `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_latest_run_result_chain_polish_step1.py tests/test_llc_magnetic_result_display_baseline.py tests/test_llc_magnetic_result_display_step2.py tests/test_llc_magnetic_result_reporting_step5.py` -> `20 passed`; evidence fixture generated |
| 第 2 步 | `completed` | `27ab107` | `3d21f5a` | `pushed` | 专项 `23 passed`；相关回归 `14 passed`；完整 LLC 回归 `96 passed` |
| 第 3 步 | `completed` | `f6ee297` | `pending` | `pushed` | LLC 全量 `99 passed in 104.41s`；受影响专项 `21 passed`；全仓库 `433 passed, 1 skipped`，另有既有 AC-DC Tk/Tcl 环境错误和 1 个既有 GUI 断言失败，详见本步记录 |
| 第 4 步 | `completed` | `74291cb` | `pending` | `pushed` | LLC 全量 `101 passed in 102.98s`；第 4 步及相关结构化输出专项 `25 passed` |
| 第 5 步 | `completed` | `981308d` | `pending` | `pushed` | 专项 `17 passed`；LLC 全量 `111 passed, 343 deselected`；编译与 `git diff --check` 通过 |
| 第 6 步 | `completed` | `b651c58` | `pending` | `pushed` | warning/manifest 专项 `10 passed`；manifest/hardware 回归 `9 passed`；LLC 全量 `115 passed, 343 deselected`；AC-DC 先决条件 `1 passed, 16 deselected` |
| 第 7 步 | `completed` | `85092bf` | `pending` | `pushed` | 文本序列化专项 `11 passed`；结构化输出相关回归 `8 passed`；LLC 全量 `118 passed, 343 deselected`；`git diff --check` 通过 |
| 第 8 步 | `pending` | - | - | - | - |

### 第 1 步执行记录

- 实现 commit：`b349847 test: freeze latest LLC result-chain baseline`
- 本步内容：新增基于 run `255120bd9d1b45a5ac3845bf2830927d` 的轻量 LLC 结果 fixture、
  结果视图/热视图异常基线测试和 JSON evidence；未读取或提交用户 `outputs/` 产物。
- Evidence：
  `migration/evidence/20260830/llc_latest_run_result_chain_polish_step1/llc_latest_run_result_chain_polish_step1_baseline.json`
- 验证：专项及历史相关测试共 `20 passed`。
- 计划记录 commit：`2311c67 docs: record LLC result-chain baseline step`。
- Push：已成功推送到 `origin/codex/sync-gui-backend-from-2`。

### 第 2 步执行记录

- 实现 commit：`27ab107 fix: align LLC Pareto selection reporting`。
- 本步内容：为 LLC 磁件 stage 增加 chosen 数量契约；成功和失败收口分支统一填充；
  结构化输出暴露 transformer/external Lr chosen 数量；Pareto 页面改用 LLC 专用
  组件计数和 transformer/external Lr/combined 三层推荐信息；非 LLC 页面保持原逻辑。
- 验证：
  - LLC 结果显示、最新基线和报告测试：`23 passed`。
  - 持久化、外置 Lr、需求、硬件相关回归：`14 passed`。
  - 全部 `test_llc_*.py`：`96 passed in 108.36s`。
- 计划记录 commit：`3d21f5a docs: record LLC Pareto mapping step`。
- Push：已成功推送到 `origin/codex/sync-gui-backend-from-2`。

### 第 3 步执行记录

- 实现 commit：`f6ee297 fix: connect LLC component thermal results`。
- 本步内容：将分离式 LLC 的 transformer 和 external Lr 组件热估算接入
  `ThermalResult` 的组件条目和推荐消费字段；组件记录统一携带 design ID、assembly type、
  loss basis、ambient、core/copper/total loss、hotspot 和 source；Thermal 页面改为分别
  展示两个组件，不再显示固定电感专用的 1/2/3-core stack-count 区块，也不生成虚构的组合温度；
  结构化输出补齐 LLC 组件热字段；硬件总览在 LLC 无通用推荐热条目时使用最大组件热点作为
  明确的组件热点上限 proxy，普通拓扑逻辑保持不变；LLC 文本摘要补齐组件损耗。
- 测试：
  - 第 3 步专项、结构化输出、最新基线和相关回归：`21 passed`。
  - 全部 `test_llc_*.py`：`99 passed in 104.41s`。
  - 全仓库：`433 passed, 1 skipped`；其余为既有 AC-DC GUI/绘图环境问题：Python Tk
    安装缺少 `ttk/menubutton.tcl` 导致 13 个 setup error，另有 1 个 AC-DC GUI 断言失败，
    均不涉及本步 LLC 改动。
- 计划记录 commit：待提交。
- Push：实现提交已成功推送；计划记录提交待推送。

### 第 5 步执行记录

- 实现 commit：`981308d fix: align LLC geometry representatives and roles`。
- 本步内容：为 `GeometryTarget` 增加 `component_role` 和 `representative_role`；LLC 外置
  `Lr` 几何代表项优先从 `chosen_candidates` 读取，并由专用
  `recommended_candidate`、`min_volume_candidate`、`min_loss_candidate` 和
  `compromise_candidate` 字段补齐；缺失代表项保留对应几何比较列并明确显示 unavailable，
  不再静默复制或伪造推荐项；当专用推荐不存在时，推荐几何仅明确标注由真实 Pareto
  compromise 代表项承接。几何页面、LLC 文本摘要和 structured output 均输出组件角色与
  代表项来源，外置 `Lr` 继续使用独立的 artifact 命名和目录，不能被当作 LLC 变压器几何。
- 测试：
  - 第 5 步专项、报告、外置 Lr 持久化和硬件总览：`17 passed`。
  - 全部 LLC 相关测试：`111 passed, 343 deselected in 114.24s`。
  - 全源码编译、`git diff --check`：通过。
  - 首次定向测试遇到系统 pytest 临时目录权限错误，改用工程内隔离 `--basetemp`
    后完成通过；该环境问题未产生代码失败。
- 计划记录 commit：`cfe75ec docs: record LLC geometry roles step`。
- Push：实现提交和计划记录提交均已成功推送到 `origin/codex/sync-gui-backend-from-2`。

### 第 6 步执行记录

- 实现 commit：`b651c58 fix: reconcile LLC magnetic warning states`。
- 本步内容：修复效率 sweep 对 LLC 错用通用固定电感 `chosen_designs` 判断的问题；当前
  LLC 专用依赖校验通过时不再追加
  `Magnetic design has not been run; magnetic loss is omitted.`。manifest warning 汇总
  增加状态感知过滤，仅在当前 LLC 磁件阶段为 `succeeded`、结果类型为分离式 LLC、组合
  contract 完整且 loss 推荐 ID/总损耗与 contract 一致时清除这条历史陈旧 warning。
  磁件 blocked、未运行、结果类型不匹配、loss 推荐不匹配及非 LLC 拓扑仍保留原 warning；
  first-pass 磁件、几何 proxy 和热模型限制说明不受影响。
- 测试：
  - warning/manifest 专项：`10 passed`。
  - manifest、hardware overview、几何和结果链回归：`9 passed`。
  - 全部 LLC 相关测试：`115 passed, 343 deselected in 130.84s`。
  - AC-DC 非 LLC 先决条件回归：`1 passed, 16 deselected in 291.87s`。
  - 全源码编译、`git diff --check`：通过。
- 计划记录 commit：待提交。
- Push：实现提交已成功推送到 `origin/codex/sync-gui-backend-from-2`；计划记录提交待推送。

### 第 4 步执行记录

- 实现 commit：`74291cb fix: expose LLC design requirement readback`。
- 本步内容：统一 LLC Design requirements 的 FHA 目标、桥式/整流结构、工作模式、频率
  基准、匝比、电流、`Lm/Lr/Cr` 目标与实际值的显示契约；磁件阶段回写推荐变压器实际
  `Lm`、外置 Lr 实际值和总 `Lr` 实际值；Cr 选择收口回写 `Cr actual`、误差、`10%`
  限制和状态；结构化输出新增仅 LLC 使用的 `llc_design_requirements`，所有工程量带
  单位和来源；缺失值保持明确 unavailable，不从单个候选行伪造电气需求；非 LLC 结构化
  输出保持原有字段形态。
- 测试：
  - 第 4 步需求、结构化输出及相关回归：`25 passed`。
  - 全部 `test_llc_*.py`：`101 passed in 102.98s`。
  - 验收覆盖 `Cr` 实际值、`7.563%` 误差、`10%` 限制、`Lm/Lr` 实际值、频率基准、
    LLC 电流与约束字段，以及缺失 Cr 场景。
- 计划记录 commit：待提交。
- Push：实现提交已成功推送；计划记录提交待推送。

### 第 7 步执行记录

- 实现 commit：`85092bf fix: preserve LLC thermal artifact notes`。
- 本步内容：修复分离式 LLC 热结果分支中 artifact note 的字符串展开错误；原实现使用
  `*` 展开完整路径字符串，导致 UI notes 按字符逐行显示。修复后路径提示作为单个
  note 保持完整写入 `ThermalResult.notes`，不改写 Windows 路径生成，也不改变
  结构化 JSON 的 `ensure_ascii=True` 确定性序列化策略。
- 新增专项测试：`tests/test_llc_text_serialization_step7.py`，覆盖完整 note、Windows
  反斜杠、下划线、空格、热页面单行显示，以及 JSON 编码/解码后的路径保真。
- 测试：
  - 文本序列化、热页面和磁件结果相关专项：`11 passed`。
  - 结构化输出相关回归：`8 passed`。
  - 全部 LLC 相关测试：`118 passed, 343 deselected in 114.84s`。
  - `git diff --check`：通过。
- 计划记录 commit：待提交。
- Push：实现提交已成功推送到 `origin/codex/sync-gui-backend-from-2`；计划记录提交待推送。

## 8. 预期结果

本计划完成后，用户重新运行 LLC 时，结果页面应明确表达：变压器和外置 `Lr` 都已完成
一阶筛选；推荐对象、Pareto/chosen 数量、损耗、热点和几何 artifact 均可追溯；组合
磁件只是推荐引用关系，不被错误地当成单一磁芯温度或单一几何实体；仍未实现的详细
绕组、漏感、绝缘、气隙公差、精确热网络和生产级 CAD 能力继续以限制说明呈现。

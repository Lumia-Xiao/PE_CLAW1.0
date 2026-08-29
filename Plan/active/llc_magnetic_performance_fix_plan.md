# LLC 磁件设计性能修复计划

## 1. 计划状态

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-28` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 目标功能 | LLC 变换器磁件设计性能优化 |
| 目标拓扑 | `llc_resonant_converter_diode_rectifier` |
| 本计划位置 | `Plan/active/llc_magnetic_performance_fix_plan.md` |
| 计划步骤 | 10 步 |

本计划只处理 LLC 二极管整流变换器的磁件设计耗时问题，以及该问题直接影响的
磁件搜索、FHA 求解、磁芯损耗、外置 `Lr`、Pareto 筛选、几何输出和性能证据。
除非回归发现共享模块存在明确回归，不修改其他拓扑的设计策略，也不以降低物理
计算准确度或删除约束为代价换取速度。

用户要求后续按步骤执行。本计划执行时，每一步都必须在验证通过后单独创建
commit 并 push；没有成功 push 时，该步骤不得标记为 `completed`。

## 2. 问题基线

### 2.1 主要调用链

磁件设计入口和 LLC 专用实现位于：

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/fha_design.py`
- `src/pe_claw_gui/engines/magnetics/core_loss_role_adapter.py`
- `src/pe_claw_gui/engines/magnetics/core_loss_kernel.py`

`Run Magnetics` 当前会连续执行变压器搜索、变压器 Pareto、外置 `Lr` 搜索、
外置 `Lr` Pareto、几何渲染和调试 CSV 输出，因此界面上的一次操作并不只包含
单一的候选搜索。

### 2.2 已知搜索规模

当前默认磁性数据库约有：

- 637 个磁芯
- 160 个磁芯材料
- 1628 个导线

LLC 变压器搜索当前约使用：

- 48 个磁芯
- 16 个材料
- 16 个导线
- 每个磁芯约 79 至 80 组匝数
- 理论变压器候选约 61,360 个

外置 `Lr` 搜索最多约使用：

- 18 个磁芯
- 16 个材料
- 最多 41 个匝数
- 10 个导线
- 理论候选最多约 118,080 个

### 2.3 已定位的主要耗时来源

1. 每个候选重复执行完整磁通、绕组、漏感、磁芯损耗和热计算。
2. 每个候选都构建边界磁通工况。
3. 磁芯损耗默认构建约 1001 点波形，并逐点执行 iGSE 积分。
4. FHA 边界频率求解最多扫描约 1501 个频率点。
5. 变压器和外置 `Lr` 的 Pareto 前沿使用候选之间的 O(n²) 双重比较。
6. 候选搜索、Pareto、几何渲染和调试 CSV 在一次磁件运行中全部同步执行。

### 2.4 已有轻量基准

当前已获得的搜索基准，用于后续对比：

| 搜索 | 限制规模 | 候选数 | 耗时 |
| --- | --- | ---: | ---: |
| 变压器 | `(1, 1, 4)` | 24 | 约 0.129 秒 |
| 变压器 | `(2, 2, 4)` | 90 | 约 0.454 秒 |
| 变压器 | `(4, 4, 8)` | 352 | 约 1.439 秒 |
| 外置 `Lr` | `(2, 2, 3)` | 414 | 约 1.602 秒 |
| 外置 `Lr` | `(4, 4, 5)` | 3020 | 约 11.65 秒 |

完整生产规模搜索曾长时间运行且未返回统计，说明需要先建立可分阶段读取的
性能证据，再进行代码优化。

## 3. 修复目标

1. 能够分别记录候选生成、廉价预筛选、精确评估、损耗、Pareto、几何渲染和
   调试输出的耗时。
2. 在不改变 LLC 物理约束、候选可行性和最终排序语义的前提下，显著减少重复计算。
3. 缓存可复用的 FHA 边界结果，以及与磁芯、匝数、材料独立的中间计算。
4. 让廉价且确定性的约束尽早淘汰不可能的候选，避免进入高成本模型。
5. 使磁芯、材料、匝数、导线和候选上限可配置，并保留完整搜索模式用于审计。
6. 将 Pareto 筛选从 O(n²) 改为保持结果语义的排序扫描或等价算法。
7. 避免默认运行中的重复几何渲染和无必要调试 CSV 输出。
8. 提供性能前后对比证据，并确认设计结果数值和边界行为没有被速度优化改变。

## 4. 验证范围和保护边界

### 4.1 允许的验证

- LLC 二极管整流器磁件设计单元测试。
- LLC 的 FHA、波形、磁芯损耗、变压器和外置 `Lr` 相关测试。
- 磁件 pipeline 的 LLC 专项测试。
- 小规模、中规模和受控生产规模性能基准。
- LLC 结果、可行性、排序、Pareto 和几何输出回归。

### 4.2 暂不默认执行

- 全量其他拓扑回放。
- 与 LLC 无关的全量性能测试。
- 会长时间阻塞且无法输出阶段统计的完整默认搜索，除非前置步骤已加入
  超时保护、阶段日志和可中断机制。

### 4.3 不允许的优化方式

- 不得删除磁通密度、窗口填充、漏感、温升、磁芯损耗或可行性约束。
- 不得静默降低物理模型精度或改变单位、边界条件和额定工况。
- 不得通过固定返回值、跳过失败候选或吞掉异常制造“运行成功”。
- 不得把 `outputs/`、Python 缓存或临时虚拟环境加入提交。

## 5. 十步实施计划

### 第 1 步：冻结 LLC 磁件性能基线

#### 工作内容

1. 确认当前 LLC 二极管整流器磁件入口、默认参数、搜索限制和数据库版本。
2. 为变压器和外置 `Lr` 分别运行小规模和中规模基准，记录候选数、可行数、
   失败原因和总耗时。
3. 在不改变算法的前提下，给磁件 pipeline 增加阶段级计时采集；至少区分：
   参数准备、候选生成、候选评估、磁芯损耗、热计算、Pareto、几何和调试输出。
4. 对每次基准记录输入 checksum、数据库或候选池标识、搜索限制、Python 版本、
   结果数量和代表性结果字段。
5. 对一次受控的较大规模运行设置明确超时，保存已完成阶段和部分统计，避免
   无法判断程序停留位置。

#### 主要修改范围

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- LLC 磁件基准脚本和专项测试目录
- `migration/evidence/` 下的新 LLC 性能证据目录

#### 完成条件

- 变压器和外置 `Lr` 都有可重复的至少两档规模基线。
- 每个阶段有耗时和候选数量记录。
- 基线不会覆盖既有迁移 golden evidence。
- 已确认默认运行的主要耗时阶段及其占比。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 1: freeze magnetic performance baseline`

---

### 第 2 步：缓存 FHA 边界频率求解

#### 工作内容

1. 检查 `fha_design.py` 中边界频率扫描的输入参数和结果依赖关系，明确缓存
   key 必须覆盖输入电压、输出电压、负载、谐振参数、变比、频率上下限、扫描点数
   以及求解版本。
2. 将相同工作点和相同 FHA 参数的重复扫描改为内存缓存；必要时使用有界缓存，
   防止大量候选导致缓存无限增长。
3. 对没有有效边界或扫描失败的结果缓存明确的失败状态，避免同一失败被反复计算，
   同时保留原有诊断信息。
4. 保证浮点 key 使用稳定的规范化方式，避免由于无意义的小数差异造成缓存失效。
5. 验证缓存命中前后的边界频率、可行性、异常类型和候选排序一致。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/fha_design.py`
- LLC 磁件调用方及 FHA 专项测试

#### 完成条件

- 重复输入能够命中缓存，并输出命中/未命中统计。
- FHA 边界结果与未缓存实现数值一致或仅有明确的浮点容差差异。
- 缓存不会跨不兼容的设计请求错误复用结果。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 2: cache FHA boundary solves`

---

### 第 3 步：优化磁芯损耗计算路径

#### 工作内容

1. 检查 `core_loss_role_adapter.py`、`core_loss_kernel.py` 和激励构建路径，定位
   标量三角波在每个候选中反复生成 1001 点波形的调用关系。
2. 对标准、可识别的 LLC 三角波或分段线性激励，引入等价的解析/分段计算路径，
   保留现有逐点 iGSE 路径作为通用 fallback。
3. 对相同磁芯材料、频率、磁通摆幅和波形形状的计算复用中间结果；缓存 key
   必须包含所有影响损耗的参数和模型版本。
4. 限制候选搜索阶段不必要的高分辨率波形构建；最终选中候选的详细报告仍使用
   规定的完整精度重新计算。
5. 对比优化前后的磁芯损耗、总损耗、热约束和失败分类，确认没有以省略峰值或
   改变积分区间来换取速度。

#### 主要修改范围

- `src/pe_claw_gui/engines/magnetics/core_loss_role_adapter.py`
- `src/pe_claw_gui/engines/magnetics/core_loss_kernel.py`
- `src/pe_claw_gui/engines/magnetics/core_loss_excitation_builder.py`
- LLC 磁芯损耗专项测试和 golden reference 对比

#### 完成条件

- 标准 LLC 激励不再对每个候选重复构建相同的高成本波形。
- 通用非标准激励仍走原有可靠路径。
- 关键参考输入的损耗误差在预先定义的容差内。
- 性能基准能显示磁芯损耗阶段的加速和缓存命中率。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 3: optimize core-loss evaluation`

---

### 第 4 步：增加变压器候选廉价预筛选

#### 工作内容

1. 在 `transformer_design.py` 的完整候选评估前加入确定性的 cheap filters。
2. 优先检查匝数比、最低匝数、磁通密度上限、窗口面积、铜截面积、线径和绕组
   几何等不需要完整损耗模型即可判断的条件。
3. 确保预筛选使用与精确评估相同的单位、边界包含关系和额定工况，不把可能可行
   的候选错误淘汰。
4. 为每个预筛选原因计数，并将“生成候选数、预筛选淘汰数、进入精评数、精评可行数”
   写入性能统计。
5. 对边界候选增加专门测试，覆盖刚好通过、刚好失败和缺少数据的情况；缺少数据
   时必须按照既有安全策略处理并保留原因。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- 必要时复用 `src/pe_claw_gui/engines/magnetics/checks.py`
- LLC 变压器候选筛选测试

#### 完成条件

- 大部分明显不可能候选在进入完整磁性模型前被淘汰。
- 优化前后最终可行候选集合和排序在容差内一致。
- 每个淘汰原因可审计，不能以“其他”吞掉主要分类。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 4: add transformer prefilters`

---

### 第 5 步：收紧并配置化搜索边界

#### 工作内容

1. 盘点变压器和外置 `Lr` 搜索中磁芯、材料、匝数和导线候选的生成规则，区分
   设计必需范围、默认快速范围和审计完整范围。
2. 将候选上限、每类数据库的截取策略和是否启用快速模式改为明确配置，避免
   在函数内部散落硬编码常量。
3. 默认快速范围必须由设计参数驱动，例如功率、频率、磁通密度和窗口需求；
   不能只取数据库前 N 项而导致结果依赖数据排列顺序。
4. 保留 `full_search` 或等价显式选项，使用户能够在性能基线和审计时恢复完整
   搜索；快速模式的范围和理由必须出现在结构化报告中。
5. 对默认范围、边界值、空候选池和完整搜索模式添加测试，并确认默认候选池
   不会因数据库排序变化而产生不可解释的结果变化。

#### 主要修改范围

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- LLC 设计配置、结果 metadata 和专项测试

#### 完成条件

- 快速搜索和完整搜索均可显式选择。
- 默认快速范围有可解释的设计依据并可审计。
- 收紧范围没有改变受控基准中本应选出的最优可行候选。
- 所有上限都能通过结构化输出追溯。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 5: configure magnetic search bounds`

---

### 第 6 步：拆分并缓存磁芯/匝数与材料相关计算

#### 工作内容

1. 梳理变压器候选评估的数据依赖，区分由磁芯和匝数决定的量、由材料决定的量、
   由导线和绕组决定的量以及由工作点决定的量。
2. 将磁芯几何、有效截面积、窗口、磁路长度、匝数对应的磁通和可复用几何中间量
   从每个材料候选的重复路径中提取出来。
3. 对相同 `(core, turns, winding arrangement, operating point)` 的中间值缓存，
   对材料相关损耗单独计算；缓存必须包含模型版本和必要单位信息。
4. 检查缓存对象是否可安全复用，避免可变对象污染后续候选；必要时返回不可变
   数据或复制轻量结果。
5. 在性能统计中增加各层缓存命中率和因缓存带来的评估次数减少量。
6. 用随机抽样和固定 golden candidates 对比拆分前后的完整候选结果。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- `src/pe_claw_gui/engines/magnetics/candidate_metrics.py`
- 必要时同步磁件候选缓存辅助模块和专项测试

#### 完成条件

- 材料循环不再重复计算与材料无关的磁芯/匝数数据。
- 缓存命中不会改变结果、异常和排序。
- 候选评估阶段的调用次数和耗时有量化下降。
- 缓存边界、失效条件和模型版本均有测试。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 6: cache reusable magnetic metrics`

---

### 第 7 步：优化外置 `Lr` 搜索和预筛选

#### 工作内容

1. 对照变压器搜索优化后的结构，检查外置 `Lr` 的磁芯、材料、匝数和导线候选
   生成及完整评估路径。
2. 在精确损耗和热模型前加入电感值范围、磁通密度、窗口填充、最小匝数、导线
   电流能力和几何可行性的廉价预筛选。
3. 复用第 2、3、6 步中适用的 FHA、磁芯损耗和磁性中间量缓存，但严格检查
   外置 `Lr` 与变压器激励、气隙和损耗依赖并不完全相同。
4. 将外置 `Lr` 的候选数、淘汰原因、进入精评数和可行数纳入统一性能统计。
5. 对外置 `Lr` 禁用、启用、边界电感值、无可行候选和完整搜索进行回归。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- `src/pe_claw_gui/engines/magnetics/inductor_design.py`
- `src/pe_claw_gui/engines/magnetics/inductor_adapter.py`
- LLC 外置 `Lr` 专项测试

#### 完成条件

- 外置 `Lr` 的明显不可能候选在高成本计算前淘汰。
- 启用和禁用外置 `Lr` 时结果状态、错误信息和报告字段正确。
- 优化前后受控样例的可行性和排序保持一致。
- 外置 `Lr` 阶段耗时与候选缩减可量化。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 7: optimize external resonant-inductor search`

---

### 第 8 步：将 Pareto 筛选改为高效等价算法

#### 工作内容

1. 固定当前变压器和外置 `Lr` Pareto 的支配定义、字段方向、NaN/Inf 处理、
   稳定排序和 tie-break 规则。
2. 将 `transformer_design.py` 中的候选双重比较改为按主目标排序后进行扫描，
   对多目标情况使用等价的前缀最优或分层数据结构；如不能证明完全等价，先保留
   原算法作为 reference oracle。
3. 对外置 `Lr` 使用同样原则优化其 Pareto 路径，避免两处实现产生不同语义。
4. 对空列表、单候选、相同指标、互相支配、不可比较指标和包含 NaN 的候选添加
   单元测试。
5. 在中规模随机数据上对比新旧算法的 Pareto 集合和顺序，并记录复杂度和耗时。

#### 主要修改范围

- `src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py`
- 相关候选排序/压缩工具
- LLC Pareto 专项测试

#### 完成条件

- 新算法与 reference oracle 返回相同 Pareto 候选集合和规定顺序。
- 大候选集上的 Pareto 阶段不再表现为明显 O(n²) 增长。
- 所有特殊值和 tie-break 行为均有覆盖。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 8: optimize Pareto filtering`

---

### 第 9 步：控制几何渲染和调试输出

#### 工作内容

1. 检查 `run_magnetic_pipeline.py` 在默认磁件运行中触发的变压器、外置 `Lr`
   和候选几何渲染次数，区分用户可见结果与调试产物。
2. 默认只渲染最终选中候选或用户明确请求的候选；候选搜索阶段不重复生成相同
   几何图像。
3. 将调试 CSV 改为显式诊断选项，或使用一次性批量写出，避免每个候选同步写盘。
4. 保留正式结构化报告、失败原因和必要审计数据；不能因关闭调试输出而丢失
   候选计数、阶段计时和配置摘要。
5. 增加输出目录隔离和文件命名测试，确认重复运行不会相互覆盖正式结果，也不会
   把运行缓存误加入 Git。

#### 主要修改范围

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- LLC 磁件几何输出、报告和诊断辅助模块
- 必要时更新相关 UI 参数映射和专项测试

#### 完成条件

- 默认运行的几何渲染和调试写盘次数明显减少。
- 正式结果仍包含用户需要的几何和结构化字段。
- 调试模式仍能复现完整诊断输出。
- 输出路径、文件数量和覆盖行为有测试或可审计证据。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 9: reduce duplicate magnetic outputs`

---

### 第 10 步：完整回归、性能复测和交付收口

#### 工作内容

1. 使用第 1 步完全相同的输入、数据库快照和搜索限制重新运行所有基准。
2. 对比各阶段耗时、候选数、预筛选数、缓存命中率、Pareto 数量、几何输出数
   和总耗时，生成前后对比 JSON/CSV/Markdown 证据。
3. 对 LLC 二极管整流器执行专项回归，至少覆盖 nominal、低输入、高输入、轻载、
   外置 `Lr` 启用/禁用、边界不可行和无可行候选场景。
4. 对代表性候选逐项比较磁通密度、铜损、磁芯损耗、温升、漏感/电感值、总损耗、
   可行性状态和 Pareto 结果；任何差异必须能归因于修复且在批准容差内。
5. 运行静态检查、编译检查、专项 pytest 和 `git diff --check`；确认没有缓存、
   `outputs/`、临时目录或 `.step10-venv` 等非交付文件进入提交。
6. 更新本计划每一步的状态、commit hash、push 结果、验证命令和最终性能数据。
7. 只有所有证据生成、回归通过并成功 push 后，才将计划状态改为 `completed`。

#### 主要证据

- `migration/evidence/<date>/llc_magnetic_performance/`
- 性能基线与优化后对比文件
- LLC 专项回归结果
- 结构化结果和候选排序对比报告

#### 完成条件

- LLC 磁件设计不再无期限阻塞，生产规模运行有阶段进度和明确完成/失败状态。
- 目标阶段耗时达到后续执行时确定的验收阈值，且阈值和测量环境记录在证据中。
- 物理结果、可行性边界、Pareto 语义和正式输出保持兼容。
- 计划中的 10 步全部有独立提交和 push 记录。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Step 10: close magnetic performance optimization`

## 6. 每一步通用执行规则

每个步骤严格按以下顺序执行：

1. 读取该步骤涉及的现状代码和上一阶段证据。
2. 在开始编辑前说明将修改的文件和验证范围。
3. 只实施当前步骤范围内的代码、测试或证据变更。
4. 运行该步骤允许的专项测试、基准和静态检查。
5. 检查 `git diff`、`git status` 和 `git diff --check`，排除缓存、`outputs/`
   和无关变更。
6. 创建该步骤独立 commit，提交信息必须包含本计划规定的关键词。
7. push 到当前工作分支对应的远端分支。
8. 确认 push 成功后，将本步骤状态、commit hash、push 时间、测试命令和结果
   写回本计划，并为计划记录再创建独立 commit/push（如计划记录不在同一个
   实现 commit 中）。
9. 如果 commit 或 push 失败，步骤保持 `in_progress`，不得声称完成；记录失败
   原因并在下一次执行中继续处理。

## 7. 步骤状态记录

| 步骤 | 状态 | 实现 commit | 计划记录 commit | 验证摘要 |
| ---: | --- | --- | --- | --- |
| 1 | `completed` | `8310634` | `0fed73e` | 4/4 baseline cases completed; 0 timeout; 0 error; LLC regression 7 passed |
| 2 | `completed` | `ff8fc27` | `5cc6955` | FHA cache tests 10 passed; baseline 4/4 completed; real cache hits recorded |
| 3 | `completed` | `e4c2141` | `4774027` | 68 项专项/LLC 回归通过；四档基准 4/4 完成；中规模变压器核心损耗阶段约 0.96 s 降至约 0.11--0.13 s，外置 `Lr` 约 8.17 s 降至约 0.85--0.99 s；候选数、可行数、拒绝分类和代表性结果保持一致 |
| 4 | `completed` | `0a20914` | `9320bd3` | 预筛选专项 5 passed；磁损/LLC 回归 67 passed；四档基准 4/4 completed；中规模变压器 352 生成候选中 336 个预筛选淘汰、16 个精评、9 个可行，代表候选保持一致 |
| 5 | `completed` | `b4dce50` | `c792d14` | LLC 边界专项 11 passed；四档基准 4/4 completed；默认 fast 保持原 golden 代表候选；支持显式 full 审计搜索 |
| 6 | `completed` | `aa9956c` | `ce7b189` | reusable metrics cache implemented; 14 LLC baseline/cache tests and 67 shared regressions passed; controlled transformer-small evidence completed |
| 7 | `completed` | `7547fc1` | `185df50` | external Lr cheap prefilters implemented; 16 LLC/external-Lr tests and 4 topology regressions passed; medium 3020 = 2764 prefiltered + 256 precise, 186 feasible |
| 8 | `pending` | - | - | - |
| 9 | `pending` | - | - | - |
| 10 | `pending` | - | - | - |

## 8. 预期交付物

- LLC 磁件性能基线和优化后对比证据。
- 可配置的搜索边界和性能统计字段。
- FHA、磁芯损耗、候选预筛选、中间量缓存和 Pareto 优化实现。
- 外置 `Lr` 的独立性能优化和回归证据。
- 几何/调试输出控制及其测试。
- LLC 二极管整流器专项回归结果。
- 本计划中 10 个步骤的独立 commit/push 记录。

## 9. 当前状态

第 1、2、3、4、5、6、7 步已完成，后续从第 8 步开始。第 1 步冻结了四档可重复 LLC 磁件性能基线，
第 2 步加入了 FHA 边界频率有界缓存并验证了实际缓存命中，第 3 步完成了标准标量
三角波的精确分段损耗路径、候选筛选采样优化和有界缓存，第 4 步完成了变压器候选
的确定性廉价预筛选和可审计统计，第 5 步完成了 LLC 磁性搜索边界的统一配置化和
快速/完整模式切换，第 6 步完成了变压器材料无关磁性指标的版本化不可变缓存，
并将缓存命中率、重复构建减少量和模型单位语义接入结构化证据。后续步骤仍必须严格按照
本文件的范围、完成条件和提交同步规则推进。

### 第 1 步执行结果（2026-08-28）

- 阶段计时已加入 `MagneticResult.performance_timing`，并通过结构化输出的
  `magnetic.metadata.performance_timing` 对外暴露。
- 变压器搜索结果记录：参数准备、候选生成、候选评估、磁芯损耗、热计算、
  调试输出和总耗时，以及数据库候选规模、匝数候选数、理论候选数、评估数和
  可行数。
- 外置 `Lr` 搜索结果记录：参数准备、候选评估、磁芯损耗、热计算、Pareto、
  调试输出和总耗时，以及核心/材料/导线、匝数、评估、可行和 Pareto 数量。
- 基准脚本：`scripts/freeze_llc_magnetic_performance_baseline.py`
- 基准证据：`migration/evidence/20260828/llc_magnetic_performance/llc_magnetic_performance_baseline.json`
- 基准测试：`tests/test_llc_magnetic_performance_baseline.py`
- 数据库后端：`packaged_normalized_v2` / `normalized_v2_production`
- 数据库规模：637 cores、160 materials、1628 wires
- `transformer-small`：90 candidates、0 feasible、0.294 s
- `transformer-medium`：352 candidates、9 feasible、1.103 s
- `external-lr-small`：transformer seed 352/9/1.024 s；external `Lr` 414/0/1.230 s
- `external-lr-medium`：transformer seed 352/9/1.018 s；external `Lr` 3020/186/8.294 s
- 四档基线结果：4/4 completed、0 timeout、0 error
- 专项验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_magnetic_performance_baseline.py tests/test_phase7_dc_dc_topologies.py tests/test_phase5_pipeline_closure.py`
- 专项验证结果：`7 passed`
- 编译检查：通过
- `git diff --check`：通过
- 实现 commit：`8310634`（`LLC Step 1: freeze magnetic performance baseline`）
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功
- 计划记录 commit：`0fed73e`（`docs: record LLC Step 1 baseline`）
- 计划记录 push 结果：成功

### 第 2 步执行结果（2026-08-28）

- FHA 边界频率扫描结果加入进程内有界 LRU 缓存，最大容量为 `512`。
- 缓存 key 覆盖求解器版本、拓扑、`vin`、`vout`、`pout`、`Zr`、变比、桥臂
  增益、`fr`、`Ln`、频率上下限和扫描点数 `1501`。
- 缓存结果使用不可变 `LLCOperatingPointResult`；扫描异常保存异常类型和消息，
  后续重复失败会恢复相同异常类别和消息。
- FHA coverage 已接入同一缓存，避免磁件候选循环绕过缓存统计。
- 提供 `clear_fha_boundary_frequency_cache()` 和
  `fha_boundary_frequency_cache_info()` 用于隔离测试和性能证据。
- LLC pipeline 结构化计时中增加 `fha_boundary_cache` 命中/未命中/容量信息。
- 专项测试：`tests/test_llc_fha_boundary_cache.py`
- 专项验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_fha_boundary_cache.py tests/test_llc_magnetic_performance_baseline.py tests/test_phase7_dc_dc_topologies.py`
- 专项验证结果：`10 passed`
- 正式四档基线：`4/4 completed`、`0 timeout`、`0 error`
- FHA 缓存证据：medium 变压器档 `1422 hits / 1575 misses`；四档均记录了
  cache size、solver version 和 scan points。
- 结果回归：变压器 medium `352 candidates / 9 feasible`；外置 `Lr` medium
  `3020 candidates / 186 feasible`，与第 1 步规模基线一致。
- 编译检查：通过
- `git diff --check`：通过
- 实现 commit：`ff8fc27`（`LLC Step 2: cache FHA boundary solves`）
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`
- 实现 push 结果：成功
- 计划记录 commit：待本次计划记录提交后填写
- 计划记录 commit：`5cc6955`（`docs: record LLC Step 2 FHA cache`）
- 计划记录 push 结果：成功

### 第 3 步执行结果（2026-08-28）

- 标准 `bipolar_triangular`、`dc_biased_triangular` 和
  `piecewise_linear_current` 标量激励在 LLC 候选筛选中显式使用 5 个精确节点，
  不再为每个候选生成约 1001 点波形；共享 builder 的默认详细分辨率仍保持
  `requested_sample_count=1001`。
- `core_loss_kernel.py` 增加标准五节点三角波的解析 iGSE 路径。解析路径只在波形
  标签、周期断点、直流偏置和四段斜率均满足校验时启用，不满足时继续使用原有逐点
  iGSE fallback。
- 增加版本化有界 LRU 缓存，最大容量为 `4096`；缓存 key 覆盖模型版本、材料、
  模型、波形形状、频率、磁通峰峰值、温度、Steinmetz 系数和温度修正因子；候选
  体积和质量保持候选本地换算，不会串用总瓦数。
- `CoreLossResult.model_evaluation_details` 记录 `igse_path`、模型版本和波形定义；
  基准脚本记录三角损耗缓存容量、命中、未命中和当前大小。生产基准中命中为 0
  是因为受控候选的材料/频率/摆幅组合没有重复；专项单元测试验证了重复输入命中。
- 增加了精确五节点、默认 1001 点详细路径、解析与 1001 点逐点 iGSE 等价、非标准
  波形 fallback、缓存命中和候选适配器分辨率隔离测试。
- 优化后证据：`migration/evidence/20260828/llc_magnetic_performance_step3/llc_magnetic_performance_baseline.json`。
- 专项验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_core_loss_kernel.py tests/test_core_loss_router.py tests/test_magnetic_loss_contract.py tests/test_llc_magnetic_performance_baseline.py tests/test_phase7_dc_dc_topologies.py`
- 专项验证结果：`68 passed`；另有 LLC FHA、拓扑回归 `9 passed`，编译检查和
  `git diff --check` 通过。
- 四档受控基准：`4/4 completed`、`0 timeout`、`0 error`；变压器候选/可行数分别
  保持 `90/0`、`352/9`，外置 `Lr` 候选/可行数保持 `414/0`、`3020/186`。
- 实现 commit：`e4c2141`（`LLC Step 3: optimize core-loss evaluation`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`。
- 实现 push 结果：成功。
- 计划记录 commit：`4774027`（`docs: record LLC Step 3 core-loss optimization`）。
- 计划记录 push 结果：成功。

### 第 5 步执行结果（2026-08-28）

- 新增不可变 `LLCMagneticSearchBounds`，统一描述变压器和外置 `Lr` 的核心、材料、
  导线、变压器匝数缩放及外置 `Lr` 匝数上限；搜索结果、`design_requirements` 和
  `performance_timing` 均保存完整边界字典和选择策略。
- 生产 pipeline 新增 `llc_search_mode` 参数，默认使用设计驱动的 `fast` 模式，
  也可以通过 `run_full_pipeline(..., llc_search_mode="full")` 显式执行完整数据库审计
  搜索。`full` 模式取消核心/材料/导线目录截取，并保留无损耗模型材料，使缺失数据
  结果仍可追溯。
- `fast` 模式根据功率、绕组最大设计电流和频率范围计算边界，再使用原有物理筛选、
  Bsat/几何/电流排序及均匀分布截取；不依赖数据库原始排列顺序。变压器和外置 `Lr`
  使用独立边界，所有上限均在结构化报告中可审计。
- 基准脚本保留显式边界以维持第 1 至第 4 步证据可比性，并新增边界字段；第五步证据：
  `migration/evidence/20260828/llc_magnetic_performance_step5/llc_magnetic_performance_baseline.json`。
  四档均 `completed`，`0 timeout`，`0 error`；medium 变压器仍为 `352` 生成候选、
  `16` 精评、`9` 可行，代表候选仍为 `T_134_77_155_FT-3M_Np16_Ns2`；外置 `Lr`
  medium 仍为 `3020/186`。
- 默认 4 kW LLC pipeline 烟测得到 `495` 个可行候选和 `7` 个 Pareto 候选，结构化
  边界为变压器 `48/16/16/80`，外置 `Lr` `24/12/12/180`；与旧默认变压器 golden
  代表 `PQ_107_87_SMP97_Np16_Ns2` 一致。
- 新增默认范围、`full_search`、未知模式、空候选池、数据库输入顺序稳定性和 pipeline
  审计字段测试。
- 专项验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_magnetic_performance_baseline.py`
- 专项验证结果：`11 passed`。相关回归命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_core_loss_kernel.py tests/test_core_loss_router.py tests/test_magnetic_loss_contract.py tests/test_phase7_dc_dc_topologies.py`
- 相关回归结果：`67 passed`；默认后端/闭环回归 `7 passed, 1 skipped`；编译检查和
  `git diff --check` 通过。
- 实现 commit：`b4dce50`（`LLC Step 5: configure magnetic search bounds`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`。
- 实现 push 结果：成功。
- 计划记录 commit：`c792d14`（`docs: record LLC Step 5 search bounds`）。
- 计划记录 push 结果：成功。

### 第 6 步执行结果（2026-08-28）

- 在 LLC 变压器候选评估中拆分材料无关的可复用指标：四个边界磁通 case、Lm/气隙、
  匝数磁通、primary/secondary 绕组选择与铜损、漏感几何和漏感估算；材料相关的
  Steinmetz/core-loss 与最终热计算仍按材料独立执行。
- 新增版本化、单位显式的不可变缓存 DTO 与有界 LRU：模型版本为
  `llc-transformer-reusable-metrics-v1`，单位语义为 `SI: m, m2, m3, H, T, Hz, A, W`，
  容量为 4096；key 覆盖 core、turns、完整工作点、导线集合、绕组排列和频率求解器身份。
- 缓存内部使用 tuple 和 frozen dataclass；候选输出对边界 case、winding notes/warnings
  等可变字段建立独立副本，避免一个候选修改后污染后续候选。
- 新增 `clear_llc_reusable_magnetic_metrics_cache()` 和
  `llc_reusable_magnetic_metrics_cache_info()`；pipeline 与基准证据记录版本、单位、
  容量、命中、未命中、缓存大小、命中率和避免的重复构建数。
- 新增固定 fixture 测试覆盖相同工况命中、core/匝数/工作点变化失效、不可变缓存对象、
  两个材料共享一次可复用构建，以及性能统计守恒。
- 证据文件：`migration/evidence/20260828/llc_magnetic_performance_step6/llc_magnetic_performance_baseline.json`。
  受控 transformer-small 档完成；缓存统计为 3 hits、3 misses、3 次避免重复构建、
  命中率 0.5，候选数量和既有筛选语义保持一致。
- 验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_magnetic_performance_baseline.py`
  （14 passed）；
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_core_loss_kernel.py tests/test_core_loss_router.py tests/test_magnetic_loss_contract.py tests/test_phase7_dc_dc_topologies.py`
  （67 passed）；编译检查和 `git diff --check` 通过。
- 实现 commit：`aa9956c`（`LLC Step 6: cache reusable magnetic metrics`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`。
- 实现 push 结果：成功。
- 计划记录 commit：`ce7b189`（`docs: record LLC Step 6 reusable metrics cache`）。
- 计划记录 push 结果：成功。

### 第 4 步执行结果（2026-08-28）

- 在变压器完整候选精评前增加确定性的廉价预筛选，覆盖饱和所需最小匝数、`Lm`/
  气隙边界、绕组最低电流承载能力和理论最小窗口填充；预筛选使用与完整筛选相同
  的单位、边界关系和额定设计电流。
- 预筛选不替代已有完整评估。通过预筛选的候选继续执行原有绕组、漏感、磁芯损耗、
  热和可行性判定；缺少导线记录时保留既有缺失数据处理路径，不将缺失数据误判为
  电流承载失败。
- 搜索结果新增 `prefilter_rejection_counts`，性能统计新增生成候选数、预筛选淘汰
  数、预筛选通过数、精确评估数，以及按饱和、`Lm`/气隙、电流密度、填充和缺失数据
  分类的淘汰计数。
- 新增饱和失败、边界通过、缺失导线数据和电流密度失败测试，验证预筛选边界和原因
  可审计性。
- 受控四档基准证据：
  `migration/evidence/20260828/llc_magnetic_performance_step4/llc_magnetic_performance_baseline.json`。
  四档均 `completed`，`0 timeout`，`0 error`。变压器 small 为 `90 -> 6` 精评、
  medium 为 `352 -> 16` 精评；medium 仍有 `9` 个可行候选，代表候选仍为
  `T_134_77_155_FT-3M_Np16_Ns2`。外置 `Lr` medium 仍为 `3020` 候选、`186`
  个可行候选。
- medium 变压器预筛选原因计数允许重叠：饱和 `16`、`Lm`/气隙 `260`、填充 `268`、
  电流密度 `0`、缺失数据 `0`；候选总数守恒为 `352 = 336 + 16`。
- 专项验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_magnetic_performance_baseline.py`
- 专项验证结果：`5 passed`。相关回归命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_core_loss_kernel.py tests/test_core_loss_router.py tests/test_magnetic_loss_contract.py tests/test_phase7_dc_dc_topologies.py`
- 相关回归结果：`67 passed`；编译检查和 `git diff --check` 通过。
- 实现 commit：`0a20914`（`LLC Step 4: add transformer prefilters`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`。
- 实现 push 结果：成功。
- 计划记录 commit：`9320bd3`（`docs: record LLC Step 4 transformer prefilters`）。
- 计划记录 push 结果：成功。

### 第 7 步执行结果（2026-08-29）

- 在外置 `Lr` 的 `(core, material, turns, wire)` 组合进入完整模型前增加确定性 cheap
  prefilter，先计算气隙、实际电感、总电感误差、Bpeak、Bmargin、最小并联数、填充率
  和电流密度；明确失败的几何、气隙、电感误差、饱和、填充和电流密度候选不再进入
  core-loss 与 thermal 计算。
- 预筛选候选仍保留在完整候选审计列表中，并生成轻量候选对象及 `prefilter:<reason>`
  失败原因，避免候选计数、失败分类和 CSV 审计丢失；材料 core-loss 和最终 thermal
  对通过预筛选的候选继续执行原有路径。
- 外置 `Lr` 搜索结果新增 `prefilter_rejection_counts`；性能统计新增 generated、
  prefilter rejected/pass、precise evaluated 和各主要预筛选原因计数。pipeline 和基准
  脚本同步暴露该字段。
- 新增测试覆盖气隙/饱和/填充/电流边界、候选总数守恒，以及预筛选候选不会触发
  core-loss 模型。
- 证据文件：`migration/evidence/20260829/llc_magnetic_performance_step7/llc_magnetic_performance_baseline.json`。
  `external-lr-small`：`414 = 390` 预筛选淘汰 `+ 24` 精确评估，0 可行；耗时约
  `0.045 s`。`external-lr-medium`：`3020 = 2764 + 256`，186 可行、18 Pareto，
  气隙类淘汰 2400、填充类淘汰 2016，耗时约 `0.166 s`。
- 验证命令：
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_external_lr_prefilter.py tests/test_llc_magnetic_performance_baseline.py`
  （16 passed）；
  `$env:PYTHONPATH='src'; python -m pytest -q tests/test_phase7_dc_dc_topologies.py`
  （4 passed）；共享磁损/拓扑回归 67 passed；编译检查和 `git diff --check` 通过。
- 实现 commit：`7547fc1`（`LLC Step 7: optimize external resonant-inductor search`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`。
- 实现 push 结果：成功。
- 计划记录 commit：`185df50`（`docs: record LLC Step 7 external Lr prefilters`）。
- 计划记录 push 结果：成功。

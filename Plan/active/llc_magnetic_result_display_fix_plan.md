# LLC 磁件结果显示与字段契约修复计划

## 1. 计划状态

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active` |
| 计划版本 | `v1.0` |
| 建立日期 | `2026-08-29` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 目标拓扑 | `llc_resonant_converter_diode_rectifier` |
| 目标功能 | LLC 分离式变压器、外置 `Lr`、组合磁件结果的字段契约和显示修复 |
| 本计划位置 | `Plan/active/llc_magnetic_result_display_fix_plan.md` |
| 计划步骤 | 6 步 |

本计划处理 LLC 磁件计算已经成功，但结果页面仍复用固定电感显示字段而产生的错误信息。
主要表现包括：实际已有 `10269` 个可行变压器候选，但页面显示 engineering allow、
compression 和 final combined 数量为 `0`；固定电感的 stack-count 区块显示三个
`unavailable`；LLC 的 Design requirements 被显示为一组 `-`；变压器推荐、外置 `Lr`
推荐和组合磁件推荐缺少清晰区分。

本计划不重新设计 LLC 的候选搜索、损耗模型、预筛选、Pareto 算法或搜索边界。
除非验证发现已有结构化结果本身缺失必要字段，否则修改集中在结果 DTO 映射、GUI 文本构建、
结构化输出和相应测试。

用户要求后续按步骤执行。每一步必须在验证通过后创建独立 commit 并 push；push 成功前，
该步骤不得标记为 `completed`。计划记录更新应与实现提交分开 commit/push。

## 2. 已确认的问题基线

### 2.1 当前实际计算结果

用户运行的 LLC 示例已经得到以下有效结果：

- 变压器精确评估候选：`19216`
- 变压器可行候选：`10269`
- 变压器 Pareto 候选：`16`
- 推荐变压器：`E_80_38_32_SMP97_Np18_Ns18`
- 推荐变压器损耗：约 `3.74375 W`
- 推荐外置 `Lr`：`Lr_ext_E_55_28_25_SMP97_N11_P4`
- 推荐外置 `Lr` 损耗：约 `1.27589 W`
- 组合磁件损耗：约 `5.01963 W`
- 外置 `Lr` 推荐几何 PNG/SVG 已生成

变压器与外置 `Lr` 损耗之和与组合磁件总损耗一致，仅有显示精度带来的舍入差异，
因此当前主要问题不是候选搜索失败或损耗聚合失败。

### 2.2 已定位的字段契约错配

LLC pipeline 在 `MagneticResult` 中写入：

- `basic_feasible_count = evaluated_candidate_count`
- `feasible_count = feasible_candidate_count`
- `pareto_count = transformer Pareto count`
- `selected_design_id = recommended transformer candidate ID`
- `llc_transformer_result`
- `transformer_pareto_result`
- `llc_external_resonant_inductor_target`
- `llc_external_resonant_inductor_search_result`

但通用磁件页面仍无条件读取固定电感专用字段：

- `post_allow_count`
- `post_compression_count`
- `final_post_allow_count`
- `final_post_compression_count`
- `chosen_designs`
- `best_by_stack_count`

LLC 分支没有使用固定电感的 engineering allow、redundancy compression 或 stacked-core
流程，所以这些通用字段保持默认 `0` 或空集合。界面把默认值显示成真实计算结果，造成
“已有大量可行候选但筛选后为 0”的假象。

### 2.3 Design requirements 字段错配

LLC pipeline 当前提供：

- `topology_id`
- `design_type`
- `np`、`ns`
- `lm_target_h`、`lr_target_h`
- `b_limit_t`
- `primary_bridge_type`
- `secondary_rectifier_type`
- 边界磁通工况与候选计数

通用视图当前读取的是固定电感字段，例如 `inductance_h`、`fs_hz`、`i_avg_a`、
`delta_i_pp_a`、`throughput_power_w` 和 `mode`。字段名和物理语义不一致，因此 LLC 页面
显示大量无上下文的 `-`。

### 2.4 推荐结果层级不清晰

当前至少存在三个不同语义的推荐对象：

1. 推荐 LLC 变压器，负责 `Np:Ns` 和 `Lm`。
2. 推荐外置谐振电感，负责 `Lr_ext = Lr_target - transformer Llk`。
3. 推荐组合磁件，由推荐变压器和推荐外置 `Lr` 组成。

当前不同页面均使用 `selected/recommended design`，导致变压器 ID 与组合 ID 看起来相互冲突。

### 2.5 主要涉及文件

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/models/magnetic_result.py`
- `src/pe_claw_gui/app/result_views/magnetic_view.py`
- `src/pe_claw_gui/app/result_views/inductor_view.py`
- `src/pe_claw_gui/pipeline/run_loss_pipeline.py`
- `src/pe_claw_gui/pipeline/run_geometry_pipeline.py`
- `src/pe_claw_gui/reports/structured_output.py`
- LLC pipeline、结果视图和结构化输出专项测试

## 3. 修复目标

1. LLC 页面只显示与分离式 LLC 变压器和外置 `Lr` 实际流程一致的统计字段。
2. 不适用于 LLC 的固定电感 allow/compression/stack-count 区块不得显示默认零值。
3. 候选统计明确区分生成、预筛选淘汰、精确评估、可行和 Pareto 数量。
4. Design requirements 使用 LLC 专用物理字段和单位，不再显示一组无意义的 `-`。
5. 变压器、外置 `Lr` 和组合磁件推荐分别命名、分别展示并保持 ID 一致。
6. 损耗、体积、热结果和几何 artifact 明确标注来源角色，不把外置 `Lr` 几何误称为变压器几何。
7. 结构化输出将 LLC 的有效推荐识别为 `pass`，不能因为 `chosen_designs` 为空而误报
   `not_evaluated`。
8. 固定电感、Flyback、PSFB、AC-DC reactor 等现有结果页面不发生行为回归。

## 4. 保护边界

### 4.1 本计划允许修改

- LLC 结果字段映射与明确命名。
- LLC 专用视图分支或结果格式化 helper。
- LLC 结构化输出中的推荐对象和选择状态。
- LLC 损耗、热、几何的显示标签和来源说明。
- 为上述行为增加单元测试、GUI 文本测试和回归证据。

### 4.2 本计划不修改

- 变压器候选生成规则。
- 变压器和外置 `Lr` 的物理可行性约束。
- FHA 求解、磁芯损耗、铜损、热模型和漏感模型。
- LLC 预筛选、缓存和 Pareto 算法。
- 搜索边界的 fast/full 策略。
- 现有候选推荐排序，除非发现展示层选择了错误对象。

### 4.3 禁止的修复方式

- 不得把 `post_allow_count` 等字段简单复制为可行候选数来伪装固定电感流程已执行。
- 不得用硬编码示例数值修复页面。
- 不得通过隐藏全部诊断信息掩盖字段错配。
- 不得改变候选可行性、损耗或 Pareto 结果以匹配显示文本。
- 不得提交 `outputs/`、pytest 临时目录、Python 缓存或用户运行产生的图像。

## 5. 六步实施计划

### 第 1 步：冻结 LLC 结果显示问题与专用契约

#### 工作内容

1. 使用用户示例或等价的受控 LLC fixture 完成 Run Design、Run Magnetics、loss、thermal
   和 geometry 链路，保存磁件结果对象中的关键字段。
2. 分别记录变压器搜索、变压器 Pareto、外置 `Lr` 搜索、组合损耗和几何结果，确认每个
   数量和推荐 ID 的真实数据来源。
3. 为 `MagneticView` 与 `build_inductor_summary_text()` 增加文本回归测试，冻结当前错误：
   LLC 有可行候选时仍显示 allow/compression 为 0、stack count unavailable 和 Design
   requirements 为 `-`。
4. 建立 LLC 专用显示契约，定义必须显示和不得显示的字段：
   - 必须显示 transformer generated/evaluated/feasible/Pareto/recommended。
   - 必须显示 external `Lr` required/target/candidate/feasible/Pareto/recommended。
   - 必须显示 combined recommendation。
   - 不得显示固定电感 engineering allow、compression 和 stack count。
5. 建立结构化基线证据，记录当前 `MagneticResult`、视图文本关键行、结构化输出状态及
   artifact 角色，不保存整个 `outputs/`。

#### 主要修改范围

- LLC 结果视图测试文件
- LLC pipeline/structured-output 测试文件
- `migration/evidence/<date>/llc_magnetic_result_display_step1/`

#### 验证安排

- 运行受控 LLC pipeline fixture。
- 断言计算结果确实包含非零可行候选和有效推荐。
- 断言当前错误显示可被测试稳定复现。
- 运行现有 LLC 磁件专项测试，确认基线未改变业务代码。

#### 完成条件

- 已明确每个显示字段的数据来源和物理语义。
- 已区分计算结果错误与显示错误。
- 两个结果视图和结构化输出均有可重复基线。
- 第 2 至第 5 步可以依赖同一 fixture，而不重新运行无边界的大规模搜索。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 1: freeze magnetic result contract`

---

### 第 2 步：补齐 LLC 专用结果字段和候选统计映射

#### 工作内容

1. 检查 `LLCTransformerCandidateSearchResult.performance_counts`，统一读取：
   - `generated_candidate_count`
   - `prefilter_rejected_candidate_count`
   - `prefilter_pass_count`
   - `precise_evaluated_candidate_count`
   - `feasible_candidate_count`
2. 检查外置 `Lr` 的对应统计，明确生成、预筛选淘汰、精评、可行和 Pareto 数量。
3. 在 `MagneticResult` 中增加明确的 LLC 专用展示 DTO/字段，或增加一个结构化
   `llc_result_summary`；不得继续借用固定电感的 allow/compression 字段表达 LLC 统计。
4. 明确保存三个推荐 ID：
   - `recommended_transformer_design_id`
   - `recommended_external_lr_design_id`
   - `recommended_combined_magnetic_design_id`
5. 组合 ID 只在推荐变压器与需要的外置 `Lr` 均存在时由结构化 helper 构建；外置 `Lr`
   不需要设计、目标无效或无可行候选时必须返回清晰状态，不能产生半截 ID。
6. 兼容现有 `selected_design_id`：明确它在 LLC pipeline 中代表变压器推荐还是组合推荐，
   并避免下游页面对其作不同解释。若保留旧字段，必须在注释和测试中固定语义。
7. 将 LLC 结果统计写入结构化输出 metadata，保留现有 `feasible_count` 和 `pareto_count`
   的兼容字段。

#### 主要修改范围

- `src/pe_claw_gui/models/magnetic_result.py`
- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/reports/structured_output.py`
- LLC 结果 DTO 和 pipeline 测试

#### 验证安排

- 对候选数执行守恒检查：generated = prefilter rejected + precise evaluated。
- 检查 precise evaluated、feasible、Pareto 数与底层搜索对象一致。
- 覆盖外置 `Lr` 启用、禁用和无可行候选三种状态。
- 检查三个推荐 ID 的存在条件和组合顺序。
- 检查序列化后字段仍为 JSON-safe 数据。

#### 完成条件

- LLC 结果不再依赖固定电感统计字段表达候选转移。
- 所有展示统计均能追溯到底层 search/Pareto 对象。
- 变压器、外置 `Lr`、组合推荐 ID 的语义唯一且有测试。
- 旧结构化字段保持兼容或有明确迁移说明。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 2: map dedicated magnetic result fields`

---

### 第 3 步：修复两个 LLC 磁件结果视图

#### 工作内容

1. 在 `MagneticView.render()` 中按 `result_type == "separated_llc_transformer"` 使用 LLC
   专用渲染分支，通用固定电感分支保持原行为。
2. 在 `build_inductor_summary_text()` 中加入同样的 LLC 专用摘要分支，确保主磁件页面和
   consolidated inductor 页面显示一致。
3. LLC 候选区显示：
   - transformer generated candidates
   - transformer prefilter rejected candidates
   - transformer precise evaluated candidates
   - transformer feasible candidates
   - transformer Pareto candidates
4. LLC 推荐区分别显示：
   - recommended transformer
   - recommended external resonant inductor
   - recommended combined magnetic design
5. 当外置 `Lr` 不需要设计、无目标或无可行候选时显示明确状态，不显示空 ID 或无上下文的
   `0`。
6. LLC 视图不得显示：
   - single-core after engineering allow screening
   - redundancy compression
   - final combined allow/compression
   - Best by stack count
7. 对 `0`、`None`、空列表和不适用状态分别格式化；只有实际计算得到零候选时才显示 `0`，
   不适用字段隐藏或显示 `N/A` 和原因。
8. 保持固定电感、Flyback、PSFB、AC-DC reactor 的现有标题、计数和 stack-count 页面不变。

#### 主要修改范围

- `src/pe_claw_gui/app/result_views/magnetic_view.py`
- `src/pe_claw_gui/app/result_views/inductor_view.py`
- 结果视图专项测试

#### 验证安排

- 使用同一 LLC fixture 对两个视图文本逐行断言。
- 断言 `19216/10269/16` 等值来自结果对象而非硬编码。
- 断言 LLC 文本不包含 engineering allow、compression 和 stack-count 区块。
- 覆盖外置 `Lr` 启用、禁用、无可行候选。
- 运行至少一个普通 Buck/Boost 固定电感视图回归，确认原区块仍存在。

#### 完成条件

- 两个 LLC 页面不再显示虚假的 0 候选转移。
- 两个页面对三个推荐对象使用相同名称和 ID。
- 不适用区块已从 LLC 页面移除。
- 非 LLC 页面显示无回归。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 3: render topology-specific magnetic results`

---

### 第 4 步：修复 LLC Design requirements 显示

#### 工作内容

1. 扩展 `_llc_transformer_design_requirements()`，从 FHA design、transformer target 和
   external `Lr` target 提供完整、带单位语义的 LLC 字段。
2. 至少包含：
   - topology/display name
   - design type
   - `Vin min/nom/max`
   - `Vout nominal`
   - `Pout min/max`
   - `fs min/nom/max` 或实际设计频率 basis
   - base `Np:Ns` 与推荐 `Np:Ns`
   - `Lm target`
   - total `Lr target`
   - transformer estimated `Llk`
   - external `Lr target`
   - transformer primary/secondary RMS design current
   - external `Lr` RMS/peak current
   - `B limit`
   - primary bridge type
   - secondary rectifier type
   - search mode 和边界摘要
3. LLC 视图使用专用 requirement formatter；不再显示固定电感的 `L target`、`Iavg`、
   `Delta iL` 和 `Mode` 模板，除非这些字段在 LLC 中确有对应且名称明确。
4. 每个缺失字段必须区分：not applicable、not available、not evaluated；不得统一用无说明的
   `-` 掩盖来源问题。
5. 保持 requirement 字典 JSON-safe，不放入 dataclass、Path 或不可序列化对象。
6. 核对显示单位：H/uH、Hz/kHz、A、V、W 和 T，避免字段名与缩放重复。

#### 主要修改范围

- `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
- `src/pe_claw_gui/app/result_views/magnetic_view.py`
- `src/pe_claw_gui/app/result_views/inductor_view.py`
- LLC Design requirements 和单位测试

#### 验证安排

- 对受控 LLC fixture 检查所有必需字段非空且数值来自 FHA/磁件对象。
- 对输入范围、频率范围、Lm/Lr 和电流执行单位和值的交叉检查。
- 检查 recommended transformer 与 external `Lr` 使用的频率/电流 basis 一致。
- 检查结构化输出可 JSON 序列化。
- 回归固定电感 Design requirements 的原字段和显示。

#### 完成条件

- LLC Design requirements 不再出现整组 `-`。
- 所有核心电气和磁件目标均有来源明确的值。
- 不适用字段有明确状态，不与真实零值混淆。
- 单位和字段命名通过测试固定。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 4: expose magnetic design requirements`

---

### 第 5 步：统一推荐、损耗、热、几何和结构化输出

#### 工作内容

1. 检查 `run_loss_pipeline.py` 的 LLC 聚合逻辑，确认并明确展示：
   - transformer core/copper/total loss
   - external `Lr` core/copper/total loss
   - combined core/copper/total loss
2. 详细结果页不再只读取通用 `inductor_core_loss_w` 和 `inductor_copper_loss_w`，应使用 LLC
   专用 breakdown 字段，从而避免总损耗有值但 core/copper 显示 `-`。
3. 明确体积来源：变压器体积、外置 `Lr` 体积和组合体积分别显示，不能把组合体积写成
   external `Lr` 或反之。
4. LLC thermal 区明确说明 transformer hotspot 来自磁件筛选；若 external `Lr` 有 hotspot，
   单独显示；固定电感 thermal comparison 不适用时不显示空推荐 ID。
5. 几何区明确标识当前 artifact 是 external resonant inductor，而不是 transformer；
   transformer renderer unavailable warning 只描述变压器 geometry，不得与已成功生成的外置
   `Lr` geometry 形成表面矛盾。
6. 结构化输出中的 magnetic `selection_status` 对 LLC 应依据有效推荐 ID/LLC representative，
   不能只依赖固定电感的 `chosen_designs`。
7. `chosen_design_ids` 对 LLC 输出三个角色或专用字段；不把 external `Lr` 候选伪装成
   `FixedInductorDesignCandidate` 的通用 chosen list。
8. 检查 hardware overview、loss、geometry 和 structured report 对推荐 ID 的读取，保证同一页
   不再同时把变压器 ID 和组合 ID 都称为唯一的 selected design。

#### 主要修改范围

- `src/pe_claw_gui/pipeline/run_loss_pipeline.py`
- `src/pe_claw_gui/pipeline/run_geometry_pipeline.py`
- `src/pe_claw_gui/pipeline/run_thermal_pipeline.py`
- `src/pe_claw_gui/app/result_views/inductor_view.py`
- `src/pe_claw_gui/reports/structured_output.py`
- 必要时调整 hardware overview 的 LLC 显示映射
- LLC 聚合、geometry、thermal 和 structured-output 测试

#### 验证安排

- 检查 transformer total + external `Lr` total = combined total，使用明确浮点容差。
- 检查 combined core/copper 分量分别守恒。
- 检查 transformer、external `Lr`、combined 体积不混用。
- 检查 geometry artifact 文件存在、角色名正确、页面说明一致。
- 检查 LLC 结构化输出 `selection_status == "pass"`，并包含三个推荐层级。
- 覆盖 transformer geometry renderer unavailable、external `Lr` geometry 成功的组合场景。

#### 完成条件

- 三类推荐对象在所有页面和结构化输出中命名一致。
- 损耗和体积能够按角色拆分并正确聚合。
- thermal 和 geometry 不再显示不适用的空固定电感字段。
- LLC 有有效推荐时结构化 selection status 为 `pass`。
- 不改变底层候选选择和损耗数值。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 5: align recommendation and artifact reporting`

---

### 第 6 步：完整回归、真实示例验收和交付收口

#### 工作内容

1. 使用第 1 步冻结的同一 LLC 示例重新运行完整链路，生成最终文本和结构化证据。
2. 对比修复前后：
   - 底层 candidate/Pareto 数量必须保持一致。
   - 推荐 transformer、external `Lr` 和 combined ID 必须保持一致。
   - 损耗、体积、hotspot 和几何 artifact 必须保持一致或仅有显示精度差异。
   - 错误的 0、stack-count unavailable 和整组 `-` 必须消失。
3. 执行两个结果视图的 GUI/text 回归，检查窗口更新后没有旧文本残留。
4. 执行 LLC pipeline、FHA、磁芯损耗、磁件结果、loss、thermal、geometry、structured output
   专项测试。
5. 执行固定电感、Flyback、PSFB、AC-DC reactor 的代表性回归，确认 topology-specific
   分支没有改变其他拓扑显示。
6. 执行 `compileall`、适用的静态检查和 `git diff --check`。
7. 生成最终 JSON/Markdown 证据，记录测试命令、测试结果、示例关键字段和前后显示差异。
8. 检查 Git 暂存清单，排除 `outputs/`、`.pytest-*`、`__pycache__` 和用户已有文件。
9. 更新本计划的 6 步状态、实现 commit、计划记录 commit、push 结果和验证摘要；全部 push
   成功后将计划状态改为 `completed`。

#### 主要证据

- `migration/evidence/<date>/llc_magnetic_result_display_step6/`
- 修复前后视图文本对比
- 结构化输出对比
- LLC 真实示例关键结果摘要
- 测试与静态检查结果

#### 验证安排

- LLC 专项回归必须全部通过。
- 非 LLC 代表性磁件视图回归必须通过。
- 受控真实示例必须显示非零可行候选、有效 Pareto 和三个明确推荐层级。
- 不允许仅通过 snapshot 更新接受错误内容；关键物理字段必须有独立语义断言。

#### 完成条件

- 用户示例不再出现“10269 feasible 但后续统计全为 0”的矛盾。
- Design requirements 显示完整 LLC 参数和单位。
- 固定电感专用区块不再出现在 LLC 页面。
- 推荐、损耗、热和几何结果在两个页面及结构化输出中一致。
- 所有 6 个步骤均有独立实现 commit 和成功 push 记录。
- 工作区不存在本计划生成且未处理的临时文件。

#### 提交要求

验证通过后创建独立 commit 并 push，commit message 必须包含：

`LLC Display Step 6: close magnetic result reporting fix`

## 6. 每一步通用执行规则

每一步严格按以下顺序执行：

1. 读取该步骤涉及的现状代码、上一阶段证据和当前工作区状态。
2. 在编辑前说明本步骤修改文件、行为边界和验证范围。
3. 只修改当前步骤要求的字段、视图、测试或证据，不顺带重构无关模块。
4. 运行当前步骤专项测试和必要回归。
5. 运行 `git diff --check`，检查 diff 和未跟踪文件。
6. 只暂存当前步骤文件，排除 `outputs/`、pytest 临时目录和 Python 缓存。
7. 使用本计划规定的 commit message 创建独立实现 commit。
8. push 到当前分支对应的远端分支。
9. push 成功后，将实现 commit、push 结果和验证摘要写回本计划。
10. 计划记录使用独立 commit/push；如需回填计划记录 commit hash，再创建仅修改计划文件的
    最终记录 commit/push。
11. 如果实现、测试、commit 或 push 失败，本步骤保持 `in_progress`，不得标记完成。

## 7. 步骤状态记录

| 步骤 | 状态 | 实现 commit | 计划记录 commit | 验证摘要 |
| ---: | --- | --- | --- | --- |
| 1 | `completed` | `1cd24c6` | `e200dce` | 新增确定性 LLC 结果显示基线 fixture、两个视图基线测试和结构化输出基线；`35 passed`（含既有 LLC 专项）；生成器、证据和实现已 push |
| 2 | `completed` | `10d3ad6` | `95dc179` | 增加 LLC 专用阶段摘要 DTO、变压器/外置 Lr 统计映射、三个推荐 ID 和组合 ID 边界 helper；结构化输出增加 JSON-safe LLC 区块，LLC hardware selection 不再依赖固定电感 chosen list；`12 passed`，`compileall` 和 `git diff --check` 通过，已 push |
| 3 | `completed` | `e108410` | `2560327` | 两个磁件结果视图接入共享 LLC 专用文本格式化器；显示 transformer/external Lr 阶段统计和三个推荐层级，隐藏固定电感 allow/compression/stack-count 区块，并对 not-required 状态隐藏无意义的零计数；`11 passed`，`compileall` 和 `git diff --check` 通过，已 push |
| 4 | `completed` | `0f99073` | `568e00c` | 扩展 LLC requirements 字典并接入 FHA、transformer target、external Lr target 与搜索边界；视图显示完整输入/输出/功率/频率、匝比、Lm/Lr、Llk、电流、B 限值和搜索模式；缺失字段区分状态；专项集合 39 tests 无失败，`compileall` 和 `git diff --check` 通过，已 push |
| 5 | `completed` | `ef5ad4c` | `1d523d2` | `44 passed`；`compileall` 和 `git diff --check` 通过；统一 LLC transformer、external Lr、combined 的损耗、体积、热、几何角色和结构化输出；实现已 push |
| 6 | `pending` | - | - | - |

## 8. 预期交付物

- LLC 专用候选统计和推荐结果契约。
- LLC 专用 `MagneticView` 与 consolidated inductor summary。
- 完整的 LLC Design requirements 显示。
- transformer、external `Lr` 和 combined 推荐的统一命名与结构化输出。
- LLC 损耗、体积、thermal 和 geometry 的角色化显示。
- 修复前后证据、专项测试和非 LLC 回归结果。
- 6 个步骤的独立 commit/push 记录。

## 9. 当前状态

第 1 至第 5 步已完成，第 6 步“完整回归、真实示例验收和交付收口”待执行，并严格按照本文件的
完成条件和 commit/push 规则逐步执行。当前计划仍保持 `active`，不能提前标记为完成。

### 第 1 步执行结果（2026-08-29）

- 新增确定性 fixture，保留用户运行中的 LLC 结果来源：变压器 `19216` evaluated、`10269` feasible、`16` Pareto；外置 `Lr` `3020` generated、`186` feasible、`18` Pareto。
- 固定三个推荐层级的基线 ID：变压器 `E_80_38_32_SMP97_Np18_Ns18`、外置 `Lr` `Lr_ext_E_55_28_25_SMP97_N11_P4`、组合 `E_80_38_32_SMP97_Np18_Ns18+Lr_ext_E_55_28_25_SMP97_N11_P4`。
- `MagneticView` 和 `build_inductor_summary_text()` 当前均稳定复现：allow/compression/final 统计显示为 `0`、stack-count 区块显示 unavailable、LLC requirements 显示 `-`。
- 结构化输出基线确认：`magnetic.available = true` 且可行数/Pareto 数有效，但 `hardware.magnetic.selection_status = not_evaluated`，原因是 LLC 不使用通用 `chosen_designs`。
- 基线证据：`migration/evidence/20260829/llc_magnetic_result_display_step1/llc_magnetic_result_display_step1_baseline.json`。
- 生成器：`scripts/build_llc_magnetic_result_display_step1_baseline.py`。
- 测试：`tests/test_llc_magnetic_result_display_baseline.py`。

### 第 5 步执行结果（2026-08-29）

- LLC loss pipeline 按角色保留 transformer、external `Lr` 和 combined 的 core/copper/total loss，
  并分别保存 transformer、external `Lr` 和 combined 体积；组合 ID 优先使用 MagneticResult 的明确推荐字段。
- LLC thermal pipeline 分别报告 transformer 与 external `Lr` 的 hotspot、design ID、状态和来源，
  使用 combined recommendation 作为聚合推荐，不再生成固定电感 thermal comparison 占位结果。
- LLC geometry result 明确标记 `component_type=external_resonant_inductor`，避免把外置 `Lr` artifact
  误称为 transformer geometry；hardware overview 将该组件显示为 `External Resonant Inductor`，并保留三个推荐 ID。
- LLC 两个文本结果视图和 structured output 已按角色显示损耗、体积、热和几何信息；structured output
  的 LLC 有效推荐状态为 `pass`，不依赖固定电感 `chosen_designs`。
- 新增 `tests/test_llc_magnetic_result_reporting_step5.py`，覆盖损耗/体积守恒、双组件热结果、文本摘要、
  structured output 和 hardware overview 角色命名。
- 验证命令：`python -m compileall -q src tests scripts`；LLC 第五步及相关回归集合共 `44 passed`；
  `git diff --check` 通过。
- 实现 commit：`ef5ad4c`（`LLC Display Step 5: align recommendation and artifact reporting`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`；实现 push 结果：成功。
- 验证命令：`$env:PYTHONPATH='src'; python -m pytest -q tests/test_llc_magnetic_result_display_baseline.py tests/test_llc_magnetic_performance_baseline.py tests/test_llc_fha_boundary_cache.py tests/test_llc_external_lr_prefilter.py tests/test_llc_pareto_filter.py`。
- 验证结果：`35 passed`；`python -m compileall -q scripts tests` 和 `git diff --check` 通过。
- 实现 commit：`1cd24c6`（`LLC Display Step 1: freeze magnetic result contract`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`；实现 push 结果：成功。

### 第 3 步执行结果（2026-08-29）

- 新增共享格式化器 `src/pe_claw_gui/app/result_views/llc_result_text.py`，统一主磁件页面与 consolidated inductor 页面对 separated LLC magnetic result 的文本输出。
- `MagneticView.render()` 和 `build_inductor_summary_text()` 在完整 LLC 专用结果摘要存在时进入 topology-specific 分支；历史缺少摘要 DTO 的对象保留原有回退行为，不影响第 1 步冻结的旧行为证据。
- LLC 候选区现在显示 transformer 与 external resonant inductor 的 generated、prefilter rejected、precise evaluated、feasible 和 Pareto 数量；不再显示 single-core allow/compression、final allow/compression 或 Best by stack count。
- LLC 推荐区分别显示 transformer、external resonant inductor 和 combined magnetic design；缺少推荐时显示带状态的 `N/A`，不输出空 ID。
- external `Lr` 为 `not_required`、`invalid_target` 或 `not_evaluated` 时只显示清晰状态并隐藏阶段零计数；真实执行且候选为零时保留实际计数。
- 扩展 `tests/test_llc_magnetic_result_display_step2.py`，覆盖两视图文本一致性、专用计数、推荐层级、禁止的固定电感区块以及 not-required 状态。
- 验证命令：`$env:PYTHONPATH='src'; python -m compileall -q src tests scripts; python -m pytest -q tests/test_llc_magnetic_result_display_step2.py tests/test_llc_magnetic_result_display_baseline.py tests/test_llc_magnetic_performance_baseline.py tests/test_llc_external_lr_prefilter.py tests/test_llc_pareto_filter.py; git diff --check`。
- 验证结果：专项与基线回归 `14 passed`（提交前精简回归 `11 passed`）；`compileall` 通过；`git diff --check` 通过。全量 pytest 进程正常退出，但当前环境未返回测试摘要。
- 实现 commit：`e108410`（`LLC Display Step 3: render topology-specific magnetic results`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`；实现 push 结果：成功。

### 第 4 步执行结果（2026-08-29）

- 扩展 `_llc_transformer_design_requirements()`，从重建的 `LLCFHADesign`、transformer target、推荐 transformer candidate、external `Lr` target 和 `LLCMagneticSearchBounds` 生成完整 JSON-safe requirements 字典。
- 新增 LLC requirements 字段：Vin/Vout min-nom-max、Pout min/max、fs min/nom/max、基础与推荐 Np:Ns、Lm target、总 Lr target、推荐 transformer 估算 Llk、external Lr target、电流 RMS/peak、B limit、桥式/整流器类型、饱和边界、搜索模式、搜索策略和边界摘要。
- external `Lr` 的 requirement status 在实际搜索完成后同步为 `available`、`no_feasible_candidate`、`not_required` 或 `not_evaluated`，避免把目标存在误报为候选搜索成功。
- LLC 共享结果 formatter 新增专用 Design requirements 区块，使用 V、W、Hz、A、uH 和 T 单位；不再输出固定电感的 `L target`、`Iavg`、`Delta iL`、`Mode` 模板。
- 缺失数值以 `N/A (not available)` 表示，未执行/不需要设计保留明确状态；搜索边界只输出摘要文本，requirements 中仍保存 JSON-safe 完整边界字典。
- 新增 `tests/test_llc_magnetic_requirements_step4.py`，覆盖字段来源和值、单位显示、LLC 专用标签和 external Lr 未评估状态。
- 验证命令：`$env:PYTHONPATH='src'; python -m compileall -q src tests scripts; python -m pytest -q tests/test_llc_magnetic_requirements_step4.py tests/test_llc_magnetic_result_display_step2.py tests/test_llc_magnetic_result_display_baseline.py tests/test_llc_magnetic_performance_baseline.py tests/test_llc_external_lr_prefilter.py tests/test_llc_pareto_filter.py; git diff --check`。
- 验证结果：专项集合 `39 tests collected`，执行无失败；`compileall` 通过；`git diff --check` 通过。
- 实现 commit：`0f99073`（`LLC Display Step 4: expose magnetic design requirements`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`；实现 push 结果：成功。

### 第 2 步执行结果（2026-08-29）

- `MagneticResult` 新增 `LlcMagneticStageSummary` 和 `LlcMagneticResultSummary`，专门承载 transformer 与 external `Lr` 的 generated、prefilter rejected/pass、precise evaluated、feasible、Pareto 数量及阶段状态。
- LLC pipeline 从 `LLCTransformerCandidateSearchResult.performance_counts` 和 `LlcExternalResonantInductorSearchResult.performance_counts` 映射专用统计；保留原有 `basic_feasible_count`、`feasible_count`、`pareto_count` 兼容字段，不再使用固定电感 allow/compression 字段表达 LLC 阶段。
- `MagneticResult` 明确保存 `recommended_transformer_design_id`、`recommended_external_lr_design_id` 和 `recommended_combined_magnetic_design_id`；`selected_design_id` 继续保持“变压器推荐 ID”语义。
- `build_llc_combined_magnetic_design_id()` 仅在变压器推荐、外置 `Lr` 推荐和 external `Lr` 状态均有效时生成组合 ID；`not_required`、无效目标、无可行候选或缺少任一推荐时返回 `None`。
- 结构化输出增加 `magnetic.llc.transformer`、`magnetic.llc.external_lr` 和 `magnetic.llc.recommendations`，阶段计数使用单位为 `count` 的 JSON-safe metric；LLC hardware selection status 基于 LLC 推荐层级，非 LLC 分支保持原逻辑。
- 新增 `tests/test_llc_magnetic_result_display_step2.py`，覆盖统计映射、组合 ID 边界、结构化输出推荐层级和 LLC 专用字段。
- 验证命令：`$env:PYTHONPATH='src'; python -m compileall -q src tests scripts; python -m pytest -q tests/test_llc_magnetic_result_display_step2.py tests/test_llc_magnetic_result_display_baseline.py tests/test_llc_magnetic_performance_baseline.py tests/test_llc_external_lr_prefilter.py tests/test_llc_pareto_filter.py; git diff --check`。
- 验证结果：`12 passed`；`compileall` 通过；`git diff --check` 通过。
- 实现 commit：`10d3ad6`（`LLC Display Step 2: map dedicated magnetic result fields`）。
- 实现 push 分支：`origin/codex/sync-gui-backend-from-2`；实现 push 结果：成功。

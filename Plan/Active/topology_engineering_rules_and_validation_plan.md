# 拓扑工程规则与验证机制加强计划

- **状态**：Active / 步骤 0–1 已完成并推送；步骤 2–7 待执行。
- **创建日期**：2026-10-10。
- **当前授权**：执行步骤 1，只补强 AGENTS.md 并同步本计划和 ChangeLog，不执行步骤 2–7。
- **目标**：使智能体能够从开发规则找到工程契约，从契约找到可执行断言，并以可复核证据说明修改完成范围，减少新增拓扑时的跨阶段遗漏和返工。
- **首个试点**：`single_phase_interleaved_boost_pfc_diode_bridge`；必要时保留单相 Boost PFC 最小配对验证。
- **Git 分支**：`codex/llc-waveform-operating-point-plan`。
- **推送目标**：`pe-claw-1.1/codex/llc-waveform-operating-point-plan`，对应 `https://github.com/Lumia-Xiao/PE-Claw_1.1.git`。
- **历史关系**：两相拓扑原计划已在 `Plan/completed/two_phase_interleaved_boost_pfc_plan.md` 归档；本计划引用其问题和证据，不重新打开或改写历史完成结论。

## 1. 问题来源与目标边界

两相交错 Boost PFC 的历史修正表明：局部公式可运行、结果稳定和隔离通过，并不能独立证明完整工程链正确。主要遗漏为设计边界未传递到所有适配器、平均/RMS 电流混用、专用分支漏接扩大搜索、多实例结果未完整进入几何及总览、运行点复用设计数组，以及 Loss 页误读磁件阶段总量或未与 Efficiency Sweep 同源。

本计划加强规则与验证机制，不预设现有生产实现仍存在这些已修复问题。实现检查时必须以当前版本代码和测试确认现状，历史缺陷用于设计负向案例。

### 1.1 本计划范围

1. 补强根 `AGENTS.md` 的修改前要求、工程验收门槛和完成声明。
2. 建立公共工程语义契约，补齐两相拓扑作为具体示例。
3. 建立可按风险简化的新增拓扑与修改计划模板。
4. 从现有测试提取确有复用价值的断言，补充关键遗漏及负向检查。
5. 建立分层专项验证入口和结构化执行回执。
6. 在两相拓扑真实链路上试运行，并保留必要的旧 Boost 配对。

### 1.2 非目标

- 不在本计划中默认重构全部拓扑、公共流水线或报告模型。
- 不要求所有历史拓扑立即接入新入口，也不把未适配拓扑显示为通过。
- 不修改拓扑公式、库记录、选型策略、公共字段或状态含义以迁就检查器。
- 不引入 Web、AI 设计、控制仿真或新的拓扑功能。
- 不默认执行全量 pytest、全部旧拓扑回归或完整发布验收。
- 不清理用户 outputs、历史基线和证据，不自动重新生成基线消除差异。

若实施中发现生产缺陷，先记录根因、消费者及测试证据；超出本计划边界的修正单独安排，不能混入规则建设。

## 2. 已有基础与文件归属

以下文件已存在，应在实施前阅读并优先复用：

| 现有文件 | 复用目的 |
|---|---|
| `AGENTS.md` | 现有修改分类、拓扑隔离、测试范围、ChangeLog、提交及完成规则 |
| `docs/two_phase_interleaved_boost_pfc.md` | 两相模型、字段口径和用户可见边界 |
| `Plan/completed/two_phase_interleaved_boost_pfc_plan.md` | 10A–10I 及损耗展示修正的历史根因与限定证据 |
| `scripts/report_schema_validation.py` | 既有报告 schema 校验；不得另造相互冲突的校验口径 |
| `tests/test_two_phase_interleaved_boost_pfc_loss_display_consistency.py` | 系统损耗同源、五分量求和、回退与 blocked 路径 |
| `tests/test_two_phase_interleaved_boost_pfc_step8_efficiency.py` | 固定硬件、逐点损耗和效率产物 |
| `tests/test_two_phase_interleaved_boost_pfc_step10g_frontier.py` | 初筛、扩大搜索、耗尽和异常分支 |
| `tests/test_two_phase_interleaved_boost_pfc_step10i_contract.py` | 输入交流 RMS、电压、负载及可选运行点字段 |
| `tests/test_two_phase_interleaved_boost_pfc_step10i2_loss.py` | 运行点磁件/桥损耗与缺相处理 |
| `tests/test_two_phase_interleaved_boost_pfc_step10i3_artifacts.py` | 不完整效率点的产物阻塞 |
| `tests/test_two_phase_interleaved_boost_pfc_step9_gui.py` | 真实 Tk 操作入口、结果与效率流程 |
| `tests/test_two_phase_interleaved_boost_pfc_step10_isolation.py` | 双顺序、旧报告/文件不变、独立运行身份 |
| `scripts/record_two_phase_interleaved_boost_pfc_step10h_baseline.py` | 真实链路快照和明确归一化政策 |
| `pyproject.toml` | 现有 pytest 配置及测试目录 |

拟新增或修改的载体如下；除本计划与 ChangeLog 外，均尚未实施：

| 载体 | 计划处理 |
|---|---|
| `AGENTS.md` | 修改相关现有段落，补充门槛和权威引用，避免重复规则 |
| `docs/engineering_contracts.md` | 新增公共语义契约；名称在步骤 0 核对后冻结 |
| `docs/two_phase_interleaved_boost_pfc.md` | 补齐实际字段生产者、消费者、工况及验证映射 |
| `Plan/templates/topology_change_plan_template.md` | 新增完整模板及小改动简化方式 |
| `tests/` 下必要支持模块与专项测试 | 复用已有用例，提取最小公共断言；具体文件在步骤 0/4 确认 |
| `scripts/validate_topology_engineering.py` | 拟新增专项验证入口；参数及回执契约在步骤 0/5 确认 |
| `ChangeLog.md` | 每个有意义阶段追加记录 |

公共断言属于测试支持层，不把测试读取适配放入生产 electrical models。只有存在真实重复或稳定消费者时才提取抽象。

## 3. 必须落实的规则与工程契约

### 3.1 修改前与完成前门槛

- 修改前声明：变更分类、关键工程口径、完整影响链、共享消费者及验证范围。
- 新拓扑尽早用真实库贯通代表性案例，不等所有模块分别完成后才验证最终结果。
- 工程正确性、阶段契约、用户链路和隔离分别验收，任何一类不能替代其他类别。
- 完成前提供实际验证、未覆盖范围、阻塞项、ChangeLog 和 commit/push 状态。
- 用户限定范围收尾时保留未验证事项，不将其改写为通过。
- 小范围修复允许简化计划，但不能省略受影响的关键契约及必要验证。
- 现有明确授权内的常规实现选择自主完成；只有物理假设、字段含义或任务范围无法确定时才请求必要澄清，不增加逐步审批要求。

### 3.2 每个关键指标的契约内容

至少记录：字段/指标、物理对象及数量范围、单位、平均/RMS/峰值/峰峰值类型、设计边界或运行工况、生产者、消费者、刷新/失效条件、完整性要求、缺项语义及对应验证。

契约文档描述现有行为和明确目标，不自动引入公共数据类或改写 schema。公共原则只保留一个权威来源，拓扑文档填写具体公式，计划引用而不复制多份口径。

首个两相示例必须涵盖：每相 Boost 电感与总串联电感、低线电流/高线电压组合边界、实际运行点、固定硬件身份、各相平均/RMS/峰值及纹波、磁件损耗与系统损耗、结果来源与刷新、初筛/扩大/耗尽语义。

### 3.3 结果一致性的比较前提

只有硬件、输入电压、输出电压、负载、频率、模型范围及其他影响计算的参数一致时才直接比较。设计组合边界与额定运行点应分别标识，不能强制数值相等。

结构化值按明确单位和容差比较；GUI 文本按显示精度比较，并核对来源标签。不得通过仅匹配标题或比较两个调用同一错误计算的结果，代替独立公式验证。

## 4. 分步骤实施

| 步骤 | 状态 | 主要交付 |
|---|---|---|
| 0 | 已完成并推送 | 现状、依赖、复用和验证范围冻结 |
| 1 | 已完成并推送 | AGENTS.md 完成门槛 |
| 2 | 待执行 | 公共工程契约及两相实例 |
| 3 | 待执行 | 计划模板 |
| 4 | 待执行 | 可复用断言及负向测试 |
| 5 | 待执行 | 分层验证入口与回执 |
| 6 | 待执行 | 两相真实试运行和必要旧拓扑配对 |
| 7 | 待执行 | 范围核对与收尾 |

每一步修改前说明预期行为与命令；完成必要验证、追加 ChangeLog、检查差异、commit 并 push 后才能标记完成。计划创建本身不代表步骤 0 已执行。

### 步骤 0：现状盘点与边界冻结

1. 阅读当前规则、上述代码/测试/文档及实际消费者，检查已有支持模块以免重复建设。
2. 将历史问题映射为当前实现、已有断言、遗漏断言和计划补充项；已修复行为不能再标作当前缺陷。
3. 冻结拟修改文件、文档权威关系、公共断言最小接口、试点适配范围及测试分组。
4. 确认解释器、源码导入位置、临时输出根和 GUI 环境；不得因旧包可导入而误测历史工程。
5. 明确哪些验收可共享一次真实设计结果，哪些隔离案例必须独立重跑；昂贵磁件搜索默认串行。

**验证与完成条件**：引用及文件存在性检查、定向文档 diff 检查；记录可审查的现状/契约/测试映射和后续命令。无生产变更时不运行完整电气链。

### 步骤 1：补强 AGENTS.md 完成门槛

修改现有 Change Workflow、Topology/Testing Rules 和 Completion Checklist，写入第 3 节要求及六类不可替代关系：隔离不替代公式、稳定基线不替代正确性、代数求和不替代工况、标签不替代数值、unavailable 不替代搜索充分性、设计边界覆盖不替代实际运行点覆盖。

对后续契约和模板的引用明确标注建设状态，目标文件尚未建立时不能声称已可读取或制造必需读取的失效链接。后续步骤建立文件后再同步正式引用。

**验证与完成条件**：人工检查规则可判定性、冲突、用户指令优先关系、限定回归规则和引用；定向 `git diff --check` 通过。不为纯规则编辑运行电气测试。

### 步骤 2：建立工程契约及两相实例

建立公共语义文档，补齐两相文档中的字段来源、消费者和断言映射。对照真实模型及适配器确认，不以文档重新定义旧字段。公共报告字段若有冲突先登记问题，不在文档步骤悄然修改生产契约。

**验证与完成条件**：关键字段均能追溯到实际代码和对应测试；同工况比较前提、缺项处理、刷新与失效条件明确；引用及文档差异检查通过。此步骤描述已存在行为，不把未运行历史测试记为本次通过。

### 步骤 3：建立计划模板

模板包含目标/非目标、模型边界、变更分类、消费者、工程契约、复用流程、早期真实案例、正常/边界/失败矩阵、分步骤交付和完成条件、未验证项及 Git 回执。每步固定写预期行为、文件、来源、复用、验证断言和剩余问题。

提供小范围修复的简化方式。以两相历史根因作桌面审查，确认模板能要求边界传递、扩大搜索、双实例、运行点及最终展示一致性证据，但不改写原归档计划。

**验证与完成条件**：模板示例可填写、没有无意义必填项；各历史根因有明确对应门槛；文档引用及定向 diff 检查通过。桌面审查不能表述成真实链路已验证。

### 步骤 4：整理可复用断言与负向检查

优先调用或整理现有测试，新增最少的测试支持接口。公共断言接收显式数据和契约要求；拓扑适配说明必需分量、系统结果来源、实例数及支持工况，不根据字段名猜测工程含义。

覆盖来源正确、损耗完整与守恒、效率公式、工况身份、固定硬件、多实例、页面/导出同源、搜索流程和隔离。针对已存在完整断言不复制一套平行实现。

至少构造以下独立负向案例：磁件损耗冒充系统总量、缺必需分量、过期运行点、缺第二相、运行点重新选型。还需验证总量或效率错误、非有限值和来源不匹配时能给出明确失败；具体参数适用性由拓扑契约决定。

**验证与完成条件**：正确案例通过，已知错误被拒绝并指出原因；迁移到支持模块的原断言不削弱；适用的公式有独立参考，不仅自我求和。运行新增支持模块测试及受影响的两相专项；没有生产契约变化时不扩到全部拓扑。

### 步骤 5：建立分层验证入口

入口按显式拓扑和层级组织测试，首版只适配两相及必要旧 Boost 配对。具体参数名在实施前冻结，计划中的文件名不代表入口已经可调用。

| 层级 | 内容 |
|---|---|
| 快速 | 源码来源、公式、契约、完整性和负向案例 |
| 真实集成 | 真实库选型、运行点、损耗及 JSON/CSV/图片产物 |
| GUI | 实际按钮顺序、结果刷新、页面/导出来源与数值 |
| 隔离 | 新旧配对、双顺序、旧结果及工件不变 |

入口先核实包来源属于当前工作区，记录解释器/源码位置、Git 版本与工作树状态、所选拓扑/层级、实际命令、退出码、执行结果和耗时。运行命令使用结构化参数，不拼接不可信 shell 文本。

无适配、空测试集合、收集失败、必要项未执行或失败均不能返回成功；环境问题与断言失败分别报告。为明确不适用项提供理由，不静默 skip。失败退出非零，成功只说明所选层级通过，不能升级为全拓扑验收。

回执使用结构化 JSON，拒绝非有限 JSON 数值；非有限诊断按明确编码策略保留。工件位于本次显式输出目录，不写用户历史结果、不提交运行产物；不自动更新基线或删除临时目录。

**验证与完成条件**：入口的参数、范围、来源验证、成功/失败/未执行/环境问题分类、空集合拒绝和回执均有测试；通过轻量受控子进程案例验证调度，不为入口每个分支重复昂贵搜索。不主动安装包、重建环境或全测。

### 步骤 6：两相试运行与必要配对验收

1. 执行全部快速检查及负向案例。
2. 用真实库贯通默认宽线代表性案例，并覆盖已有宽/窄线搜索路径。
3. 按两相既有支持边界覆盖 180/230/265 Vac × 0.1/0.5/1.0 p.u.，检查运行点来源、固定身份及损耗/效率；不把理想 CCM 范围外的行为包装成已验证物理模型。
4. 在真实 GUI 中执行设计、磁件/电容、波形及效率操作，核对刷新后的 Loss/Inductor/Efficiency 和导出数据；需要来源不同的设计与运行结果分别标识。
5. 运行必要单相 Boost/两相双顺序及重复隔离，确认旧报告、文件和 active run context。
6. 记录唯一用例和重复执行，记录各层耗时及真实搜索次数；以可复现结果说明成本，不预设或宣称未经测量的加速比。

**验证与完成条件**：入口结果与直接专项执行一致，真实工件存在且属于本 run，已知错误被负向检查拒绝；无未解释失败，环境限制单列。未运行全量及其他拓扑全面回归，不能声明其通过。

### 步骤 7：核对与收尾

核对规则引用、契约来源、模板可用性、入口帮助、测试映射和限定证据。确认必要实现均已提交推送，未覆盖项可追踪。满足本计划范围后更新 Completed 并归档到 `Plan/completed/`；未适配旧拓扑和未做发布验收不写成已完成。

**验证与完成条件**：文档及定向/暂存差异检查、必要验证回执、Git 远端状态核对。若步骤 6 后未改变代码或测试，不无理由重复昂贵验证。

## 5. 验证政策与证据

- 文档阶段：检查结构、相互引用、字段来源、规则冲突和定向 diff；不为新增 Markdown 写镜像测试。
- 检查器阶段：独立参考、正常与负向用例、明确诊断，验证检查器确能拦截缺陷。
- 入口阶段：验证选择范围、实际源码来源、子进程状态和回执完整性。
- 集成阶段：只运行两相和必要单相配对；若实际修改跨越未界定共享契约，先重新评估消费者和验证范围。
- 测试显式使用当前工作区源码及短临时根，绘图按现有测试设置 `MPLBACKEND=Agg`；无 GUI 环境不得将真实 GUI 记为通过。
- 用 `python -B` 和关闭字节码等合适方式减少无意义缓存；运行产物不纳入提交。
- 容差、路径归一化及基线更新必须有明确政策；时间、run ID 和临时路径可按政策排除，工程值、单位、硬件、状态、warning 和来源不能随意删去。

每阶段记录：预期/实际行为、修改边界、实际命令、结果、失败与修复、未执行项、工件位置及 commit/push 状态。没有运行的检查使用“未执行”，不能沿用历史 passed。

## 6. 最终完成标准

- AGENTS.md 对工程正确性、完整链路、结果一致性和隔离给出可判定门槛。
- 公共工程契约、两相实例和计划模板均可读取、相互引用有效。
- 公共断言最小且有真实复用，拓扑差异通过显式适配表达。
- 检查器对正常案例通过，对本轮已知错误有独立拒绝证据。
- 分层入口不会将未知适配、未执行、空集合、环境失败或部分结果报告为成功。
- 两相真实链路、必要单相配对及 GUI 限定验收完成，记录范围和运行成本。
- 没有改写历史证据、弱化断言、自动替换基线或改生产口径以获得通过。
- ChangeLog、计划、提交和指定远端推送一致；未验证的旧拓扑及发布事项保留。

## 7. 创建记录

2026-10-10：按用户要求建立本独立 Active plan。仅新增本计划并追加 ChangeLog；没有修改 AGENTS.md、工程契约、模板、生产代码、测试或验证脚本。步骤 0–7 均待执行。本次创建采用文件存在性、现有文件引用、状态检查及定向/暂存 diff 验证，不运行 pytest。创建提交与推送结果由 Git 记录和任务回执确认。

## 8. 步骤 0 执行记录与冻结清单（2026-10-10）

### 8.1 实际执行范围

基准提交为 `b7c2cbf`。读取根规则、现有拓扑文档、归档计划、相关模型、拓扑算法、请求适配、流水线、GUI controller/view、现有校验与基线脚本及全部 20 个两相专项测试文件。检查解释器、包导入来源、pytest 收集和隐藏 Tk 窗口；没有执行设计、选型、损耗、效率或真实 GUI 按钮链。

本阶段只更新本计划和 ChangeLog。既有 95 个无关 tracked 删除、两个无关 untracked 文件及用户 outputs 不处理；归档计划保持原样。本节冻结的文件和接口是后续实施目标，不表示已经建立。

### 8.2 历史问题到当前实现、断言和缺口的映射

以下“已有实现/覆盖”来自静态阅读和本次收集，不代表本次运行通过。

| 历史问题 | 当前实现及实际消费者 | 已有断言 | 后续补强或限制 |
|---|---|---|---|
| 低线电感与额定线请求混用、平均/RMS 混用 | 两相 `synthesizer.py` 保存 low/nominal/high metrics；`waveform.py` 提供 design boundary；`stress_adapter.py`、`inductor_adapter.py`、桥 pipeline 消费对应边界 | 步骤 2、10B、10C、10D 检查边界和请求 | 步骤 2 统一生产者/消费者表；独立公式参考保留，不能仅让适配器与同一个 metadata 相等 |
| 两相分支漏扩大搜索 | `run_magnetic_pipeline.py` 初筛 allow 为零时调用现有 `search_fixed_inductor_candidate_frontier`；phase 2 独立身份复用模型 | 10G mock 分支、步骤 8 真实宽/窄线、隔离案例 | 分支测试与真实库验收分别保留，不把 mock 成功当可用磁件证据 |
| 第二相缺失或总览只画一个电感 | magnetic、geometry、hardware overview 各保留相位实例/target/child/object | 步骤 6/7、10E 的完整、缺相、缺布局/工件和复用路径 | 公共断言显式要求实例数、role、ID 唯一；理想均流为两相契约，不能泛化成全部拓扑规则 |
| 运行点复用设计数组、负载重复缩放 | `waveform.py` 按 OperatingPoint 重采样；运行点磁件适配与桥损耗读取当前 waveform；`run_operating_point_refresh.py` 保留选定硬件 | 10I contract、10I-2、步骤 8 禁止 selector 调用 | 现有跨线波形测试为三个满载点，未独立覆盖完整 3×3 物理矩阵；步骤 4/6 补独立数值预期及旧工况注入拒绝 |
| Loss/Inductor 与 Sweep 来源不同 | 两相 `loss_readback.py` 优先取精确 1.0 p.u. 点；两页调用同一 resolver；controller 用 replace 将 sweep 写回 report | loss display 五项测试覆盖同源、回退、磁件冒充系统和 blocked | 补缺精确满载、缺单分量、NaN/Infinity、错误发布总量/效率的检查器负向例；比较 resolver 重算结果之外，还要检查原始 sweep 发布值 |
| GUI 链路成功但数值未核对 | `efficiency_sweep_controller.py` 更新 state report；Loss/Inductor/Efficiency 各有 view | 步骤 9 真实 Tk 检查按钮、实例、效率完整和标题；纯文本测试另查固定数值 | 真实 GUI 运行 sweep 后缺少跨页数值与 CSV/JSON 精确对照；步骤 4/6 补读取当前 report、页面和导出的一致性 |
| 空/部分结果被状态名掩盖 | 缺硬件前置返回可能保留默认 `status="available"`；`is_complete()` 检查非空及非 None，未证明网格齐全、有限性和守恒 | 步骤 8 缺硬件、10I-3 blocked 无产物 | 新门禁检查 status、期望网格、点/分量有限性、守恒、来源和工件；不在本计划改公共 status 或 `is_complete()` |
| 旧报告或文件被下一次运行改变 | run context、输出目录、保留旧对象与文件哈希 | 步骤 3 轻量顺序检查、步骤 10 真实双顺序与宽/窄线重复 | 保留独立重复设计，不能用共享 fixture 或复用缓存代替真实隔离 |

另有三项现状需要明确处理：

1. `docs/two_phase_interleaved_boost_pfc.md` 的 Design Boundary 段仍描述 10I 前“复用候选线路周期/只缩放低线电流”的限制，与当前 operating-point 实现不一致。步骤 2 修正文档并区分实际刷新支持与未完成的全工况物理验收；本步不改该文档。
2. `scripts/report_schema_validation.py` 校验历史 structured report v1；其快照入口对空 records 不会自动报错，不能直接把 CLI exit=0 当新验收门禁。后续只在适用 schema 上复用 `validate_report`，入口自行拒绝空集合，不修改历史脚本或 schema。
3. 部分现有测试会写默认 outputs：步骤 5/10D 的 `_report()` 未传 output_root，步骤 6 mock 磁件测试的报告没有 run context，可能回退共享 `outputs/inductor_design`。后续只在相关两相测试中补 tmp_path/显式工件目录，不新增影响全部 tests 的全局 fixture，也不改生产默认输出策略。10G 正常分支已经用 tmp_path 隔离，不重复改写。

### 8.3 文件与权威关系冻结

| 步骤 | 确认的新增或修改载体 | 边界 |
|---|---|---|
| 1 | `AGENTS.md` | 补强现有工作流/验收段落；后续文档不存在前不设失效必读链接 |
| 2 | 新增 `docs/engineering_contracts.md`；修改 `docs/two_phase_interleaved_boost_pfc.md` 和必要 AGENTS 引用 | 公共描述方式一个来源；具体两相字段/公式归拓扑文档；历史证据只引用 |
| 3 | 新增 `Plan/templates/topology_change_plan_template.md`；必要 AGENTS 引用 | 完整与简化模板共享门槛，模板不重复抄写全部公式 |
| 4 | 新增 `tests/engineering_support/__init__.py`、`assertions.py`、`interleaved_boost_pfc.py`；新增 `tests/test_topology_engineering_checks.py` | 测试支持层，无生产包依赖此支持层；拓扑适配只读取/构造测试快照 |
| 4 | 按必要性修改现有 loss display、步骤 8/9 用例；补步骤 5/6/10D 测试输出隔离；新矩阵可放新检查文件 | 复用既有断言，不删除原路径，不把真实测试替换成 mock；修改前再确认具体用例依赖 |
| 5 | 新增 `scripts/validate_topology_engineering.py`、`tests/test_topology_engineering_runner.py`；更新契约中的执行说明 | 显式测试映射、标准库 subprocess/XML/JSON；不新增 pytest 插件或第三方依赖 |
| 6/7 | 本计划、ChangeLog、必要验证说明 | 记录限定实测；超范围生产缺陷另行安排 |

`src/`、`pyproject.toml`、历史 fixtures/快照生成脚本不属于本轮预定修改范围。运行环境在入口及子进程显式设置，不全局改变 pytest 配置。导入测试支持模块使用 `engineering_support`，子进程 PYTHONPATH 依次包含本仓库 `src`、`tests`，且 cwd 为本仓库；不用 `tests` 同名包作为公共生产依赖。

`runtime/reproducibility.py` 已有 environment snapshot、canonicalization 和严格 JSON 工具，可阅读复用适用部分；它会移除 artifact/path 等 volatile 字段，不能无差别用于新来源/工件归属校验。10G `_audit_snapshot` 已保留 non-finite 诊断编码，历史 fixture 原样保留；新回执使用明确编码与 `allow_nan=False`，不靠删字段通过。

### 8.4 最小公共接口冻结（后续实现目标）

公共接口为普通测试辅助函数，失败抛 `AssertionError`，诊断含规则代码、字段、预期与实际；不修改生产模型、状态 enum 或引入通用计算框架。数值容差按契约显式传入，不设覆盖所有物理量的隐藏容差。

| 接口 | 最小输入及检查 |
|---|---|
| `assert_loss_balance` | components、required_components、发布 total_loss_w、output_power_w、efficiency 及明确容差；检查完整/有限/适用非负、原始总量和独立效率公式，不能先重算覆盖错误再检查 |
| `assert_operating_basis` | expected/actual 工况映射、required_keys、数值容差；检查 Vin RMS/Vout/load/frequency/PF/来源等适用参数，缺字段失败，拒绝混入旧工况 |
| `assert_fixed_hardware` | before/after 身份映射、required_roles、已捕获 selection 调用；检查角色完整、身份不变与调用为零，调用监视由测试安装，不通过快照猜测 |
| `assert_physical_instances` | 实例列表、expected_roles、expected_count；检查角色、design ID/physical ID、数量和唯一性；相同库型号可合法复用 |

`interleaved_boost_pfc.py` 负责显式字段映射：设计 breakdown 使用 `*_loss_w`，sweep 使用桥/半导体/磁件/电容/other 字段及精确满载点；每相子项不再计入系统分量以免重复求和。字段生产者、工况和完整性来自步骤 2 文档，适配器不得把缺项变成 0。

GUI 格式和 CSV/JSON 对照放在两相专项断言内，读取字段值及显示精度，不先提取一个泛化的任意文本解析器。搜索分支继续复用 10G 测试，隔离继续复用既有双顺序测试，不重复封装所有能力。

### 8.5 分组冻结与成本政策

本次成功 collect-only：20 文件 / 107 个独立参数化用例，13.66 s；以下按现有节点分组互不重叠。数字是当前收集基准，步骤 4 新增检查后必须重新收集，不把 107 当永久目标或 passed 数。

| 层级 | 当前节点归属 | 当前数量 |
|---|---|---:|
| quick | loss display、步骤 1/2/3/4/6、10B/10C/10G/10I-contract 全文件；10A 除真实 current-baseline replay 外四项；步骤 5 仅 role 声明；步骤 9 仅 user guide | 60 |
| integration | 步骤 5 其余三项、10D 三项、10I-2 三项、10I-3 一项、步骤 7 一项、步骤 8 十四项、10E 十六项、10A current-baseline replay 一项、步骤 9 前两个结果契约项 | 44 |
| gui | 步骤 9 `test_step9_real_gui_runs_two_phase_design_results_and_efficiency` | 1 |
| isolation | 步骤 10 的旧/新双顺序与宽/窄双顺序两项 | 2 |

quick 允许轻量文件和绘图 mock 工件，但不执行真实库选型；必要输出隔离修正完成后才满足入口要求。不能以文件名含 contract/gui 判断是否昂贵：10E 和步骤 9 前两项均依赖真实完整设计；10I-2 会执行部分真实 pipeline，归 integration。

现有 module fixture：步骤 8 每个宽/窄设计复用一次；10E 共用一次默认设计；步骤 9 结果检查共用一次。保持这些复用，不为了公共断言复制真实设计。3×3 工况矩阵应在同一固定宽线硬件上刷新九点，公式检查另用独立预期；真实 GUI、双顺序隔离及严格基线重放按其目的独立执行。昂贵搜索串行，不引入 xdist，也不跨隔离运行缓存。

以下新增用例在步骤 4/5 实现：通用损耗/工况/身份/实例负向与适配测试归 quick；真实跨线损耗矩阵与导出对照归 integration；刷新后的页面数值归 gui；入口参数、来源、空集合、子进程失败及回执测试归 quick，用受控轻量子进程，不触发真实搜索。测试列表使用显式文件/node ID，不用会隐式扩到全部测试的默认路径。

### 8.6 验证入口与回执边界冻结

首版参数为 `--topology`、可重复 `--level quick|integration|gui|isolation`、`--output-dir`，均要求显式给出。只接受两相 topology ID；旧 Boost 仅作为 isolation 内部配对，不宣称为第二个完整适配。未知拓扑/层级或空选择失败，不设置默认全量/全部层级。

入口相对自身定位仓库，使用当前解释器、结构化 argv、明确 cwd/PYTHONPATH，先核验实际包和所收集测试路径都属于当前仓库，再执行。新增支持层必须在来源检测后导入。子进程使用 `-B`、`PYTHONDONTWRITEBYTECODE=1`、现有确定性环境和 `MPLBACKEND=Agg`；GUI 层额外探测 Tk，失败单独分类。

每层使用 pytest `-o addopts=`、`-p no:cacheprovider`、独立 `--basetemp`、JUnit XML 及 stdout/stderr，避免继承共享 `pytest_temp`。输出根必须为本次新目录，拒绝复用已有目录；pytest basetemp 自带清空行为只允许作用于该新根的专属子目录。历史基线脚本使用的 TemporaryDirectory 通过子进程 TEMP/TMP 指向本次新根，不改用户历史输出，不自动清理。

JSON 回执至少包含版本、拓扑/层级、解释器/包与测试来源、Git HEAD/dirty 状态、期望/实际节点、实际命令/退出码、各类计数/耗时、工件路径及诊断。JUnit/stdout 互相核对，失败、不适用、未执行、收集错误和环境问题保留区别；required skip/xfail/空集合/缺期望节点均不能升级为 passed。合法不适用项按预先声明的适配范围列明，不通过 pytest skip 隐藏。

入口退出码：0 仅表示请求层级全部必要检查通过；1 为执行后的必要断言/测试失败；2 为配置、来源、环境、收集或未执行等不能完成验证的情况。实际 child returncode 原样记录，其他异常/中断也必须非零并保留诊断；未选择层级标为 not_requested，不能写成整体拓扑已验收。

### 8.7 本次环境与实际验证

- Python `3.12.10`，解释器 `C:\Users\Lumia\AppData\Local\Programs\Python\Python312\python.exe`；pytest `9.1.1`，matplotlib `3.11.0`，Tk `8.6.15`。
- **默认导入风险已证实**：未设置 PYTHONPATH 时 find_spec 指向 `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\src\pe_claw_gui\__init__.py`；这只是定位探测，没有从该旧包执行测试。
- 设置当前仓库 `src` 后，实际导入路径位于本仓库 `src/pe_claw_gui/__init__.py`，Path.is_relative_to 断言通过。
- 隐藏 Tk 窗口 `Tk → withdraw → update_idletasks → destroy` 成功；只证明当前会话可初始化 Tk，不证明真实应用按钮链或后续会话一直可用。
- collect-only 返回 0：`107 tests collected in 13.66s`；没有运行 fixture/test body。AST 辅助检查未发现 20 文件顶层直接执行设计或 Tk；它不是全部 import 副作用证明。
- 新契约、模板、支持包及入口目标路径均未存在，未创建占位文件。未生成根 `.pytest-tmp-*` 或共享 `outputs/inductor_design`；已有 `pytest_temp` 不清理。
- 早期只读搜索因 PowerShell 不展开 rg 文件通配符/不支持 Bash 花括号而报错，已用目录加 `-g` 或显式路径重查；不属于测试失败或工程缺陷。

本次关键命令（从仓库根运行）：

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLBACKEND = 'Agg'
$testFiles = @(Get-ChildItem tests -Filter 'test_two_phase_interleaved_boost_pfc_*.py' | Sort-Object Name | ForEach-Object FullName)
python -B -m pytest -o addopts= -p no:cacheprovider --collect-only -q @testFiles
git diff --check -- Plan/Active/topology_engineering_rules_and_validation_plan.md ChangeLog.md
git diff --cached --check
```

实际收集由 Python subprocess 以等价 argv 和 60 s timeout 调用上述 pytest，输出逐文件节点数量；环境/Tk 用 `python -B -` 内联诊断。步骤 0 不将任何 collected 用例写成 passed，也不重复历史电气验证。文档/引用和分组覆盖检查、定向及暂存 diff 审查完成后提交推送，再更新步骤 0 完成状态。

### 8.8 完成与推送回执

步骤 0 冻结记录提交 `b066fac` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；`git ls-remote` 核实远端为 `b066fac978d89dcea258ff47ddb243e71de9aa53`。28 个已有文件引用、20 文件分组基准、步骤 1–7 待执行状态、ChangeLog append-only 及定向/暂存 diff 检查通过。阶段状态在该提交推送后更新为完成；本回执随独立文档提交推送。下一步为步骤 1，尚未修改 AGENTS.md 或实施后续代码。

## 9. 步骤 1 执行记录（2026-10-10）

### 9.1 修改边界及实际规则

基准 `2777505`。仅修改根 `AGENTS.md`、本计划和 ChangeLog；未修改 src、测试、脚本、库、公共模型或历史证据。

| AGENTS.md 位置 | 补强内容 |
|---|---|
| Change Workflow | 修改分类、影响消费者、关键字段对象/单位/数值类型/工况/生产者/刷新与缺项语义；小改动允许简化记录，必要契约和验证不省略；常规已授权工作自主推进 |
| 文档引用 | 链接已存在 Active plan；契约/模板仅标为步骤 2/3 的未建设目标，不添加失效必读链接或额外审批；建立文件后同步权威引用 |
| Topology Rules | 尽早真实库代表性链路；复用时核查扩大搜索/终止、选型、诊断、刷新和产物策略；结果所有者及同工况比较前提；GUI 操作后当前结果、逐实例/系统区分、禁止缺项部分合计和旧值填补 |
| Testing Rules | 来源确认、四类独立证据、已知问题负向检查、真实与 mock 区分、六类不可替代关系、原始发布值/有限性/完整性和显示精度；文档变更只做文档检查，不默认全测 |
| Completion Checklist | 授权范围内必要门禁实际执行且通过、明确非适用理由、当前结果一致、未验证/阻塞和 commit/push 状态；用户限定收尾保留后续事项，规则本身不等于实现证据 |

六类不可替代关系按步骤 1 原范围完整写入：隔离不替代公式、基线不替代正确性、求和不替代工况、标签不替代数值、unavailable 不替代搜索充分性、设计 metadata 不替代实际运行点。搜索规则允许明确的前置条件失败，避免要求无效请求必须穷尽搜索。

### 9.2 验证范围与方法

本步为开发规则文档变更，验证为人工语义/冲突审查、计划要求映射、已有链接存在性、未建文件状态、ChangeLog append-only、只涉及三个文件的差异和暂存检查；不增加镜像 Markdown 测试，不运行 pytest、collect-only、GUI 或电气设计链。

审查重点：用户指令优先、破坏性操作授权和原隔离规则保留；工程四类证据只适用于受影响行为，不强制文档编辑跑整条链；必要共享消费者按实际影响选取，不把最小配对或用户限定门禁表述成全工程通过；尚未建成契约和模板不阻塞本次及常规授权工作。

计划验证命令：`git diff --check -- AGENTS.md Plan/Active/topology_engineering_rules_and_validation_plan.md ChangeLog.md`、`git diff --cached --check`，配合一次性只读引用/append-only 检查及 diff 审查。验证结果和推送回执完成后再更新步骤 1 状态，步骤 2–7 保持待执行。

**文档验证结果**：定向 diff 检查通过；规则人工审查确认上述五处与步骤 1 要求一致，原章节顺序和 Non-Negotiable Safety Rules 原文保持不变。一次性只读检查验证 AGENTS 唯一新增本地链接存在、两个待建目标仍未创建且被明确标注不可用、ChangeLog 仅追加、步骤 2–7 保持待执行。暂存检查在提交前执行；没有运行任何 pytest、收集、Tk 或电气链。既有无关改动不纳入本次提交。

### 9.3 完成与推送回执

步骤 1 规则及记录提交 `e24be2b` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，远端 SHA 已核实为 `e24be2b7562abd6e1cccd0b6281af8dc0c805176`。定向及暂存 `git diff --check` 均通过，暂存范围仅上述三个文档；阶段状态在该提交推送后更新为完成，本回执随独立文档提交推送。下一步为步骤 2：建立公共工程契约及两相实例；相关文档、模板和自动检查尚未实施。

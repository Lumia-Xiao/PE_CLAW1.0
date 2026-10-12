# 三相三电平 T-type 实施计划：第一轮基础链路跑通

- 状态：Active / 待实施；步骤 0–8 全部待执行。
- 创建日期：2026-10-12。
- 本轮授权：撰写本计划和追加 ChangeLog；不执行以下实施步骤，不修改生产代码、测试或拓扑契约。
- 后续实施目标：按照已讨论的首轮范围，跑通 T-type 参数计算、波形、门极/路径、应力、GUI 和固定参数运行点刷新。
- 拓扑 ID：拟定 `three_phase_three_level_t_type_inverter`；当前尚未注册。
- 工作区：`C:\Users\Lumia\OneDrive - Nanyang Technological University\PE-Claw1.1\PE_Claw_1.1_260928`。
- 撰写基准：`cf04284d4e8c966f57b537f7833c62f83b10c9e4`。
- 当前特性分支：`codex/llc-waveform-operating-point-plan`；已配置上游及本次文档推送目标：`pe-claw-1.1/codex/llc-waveform-operating-point-plan`，远端 `https://github.com/Lumia-Xiao/PE-Claw_1.1.git`。
- 初始工作区：95 项无关 tracked 删除、2 项无关 untracked；保留，不纳入本计划及日志提交。实施开始时再次核实分支、基准和工作区，不把本次基准当作未来验证版本。

## 1. 权威依据、授权范围与首轮交付

依据：[AGENTS.md](../../AGENTS.md)、[工程语义契约](../../docs/engineering_contracts.md)、[T-type 电路与换流契约](../../docs/three_phase_three_level_t_type_contract.md)、[拓扑变更计划模板](../templates/topology_change_plan_template.md)。

用户已明确暂缓契约第 12.3 节的五组事项，并认可先建立基础链路的分步方案。本计划将这些事项作为后续范围，不作为第一轮启动或完成的前置条件。契约第 2–5 节的连接、状态与方向继续适用；第 6–10 节的有限死区、器件能量、动态电容等按第 2 节首轮子集裁剪；第 11–12 节的完整硬件/效率目标属于后续完整工程链。暂缓是范围安排，不代表这些能力已经实现、验证或不再需要。

第一轮交付路径：

```text
选择 T-type → 填写输入 → Run Design
→ spec / candidate / 设计估计 / 基础应力与报告
→ Generate Waveforms
→ 三相电压电流 / 12 路门极 / 导通路径 / 理想换流 / 实际电流应力
→ 修改首轮支持的运行点 → Generate Waveforms
→ 复用原 candidate 参数并刷新当前报告及页面
```

当前 `RunDesignController` 使用 `include_waveforms=False`，`WaveformController` 负责波形刷新；沿用该交互，不要求改造所有拓扑为 Run Design 自动生成波形。后端可通过 `run_topology_pipeline(..., include_waveforms=True)` 尽早验证完整基础计算链。

首轮完成必须同时满足：可加载独立插件；代表案例完整执行；三相/12 位置结果有限且语义正确；GUI 两按钮及当前数字正确；固定参数刷新有效；不生成虚假硬件、损耗或效率；必要 NPC 回归与双顺序隔离通过。单纯注册成功、能打开表单或按钮没有异常都不足以完成首轮。

## 2. 第一轮模型与暂缓范围

### 2.1 明确采用的基础模型

| 项目 | 第一轮约定 |
|---|---|
| 电路 | 契约的常规 T-type，共源/共发射极中点支路；3 相、12 开关位置、6 主支路/6 中点支路 |
| 电网 | 对称三相三线、理想正弦电网；母线中点不接电网中性线 |
| 母线 | 给定且平衡的分裂母线，`V_U=V_L=Vdc/2`；不积分动态电容电压 |
| 调制 | 固定频率 PD-SPWM 基础，中心对齐相邻电平序列；以实际命令/占空比检查饱和 |
| 开关与死区 | 理想开关、零死区；保留合法 P↔O/O↔N 门极映射与事件，不实现有限死区时长/脉冲抑制/寄生换流 |
| 电感 | 3 相相同的理想 L；设计合成后保持固定，按三线电压与电网电压进行分段积分 |
| 电流与功率 | 正向平均有功输出；支持正负瞬时电流；PF 幅值与超前/滞后语义分开 |
| 导通路径 | 用契约的 IGBT 加反并联二极管理想方向表识别承载路径；这只是电路参考，不选择 IGBT 型号、不评估第三象限或器件损耗 |
| 换流记录 | 位置、时刻、相/局部电流方向、前后状态及理想电平阶跃；只标理想换流类别，不给 Eon/Eoff/ZVS 结论 |
| 电容 | 仅允许有依据且标注算法的标量初始估计；它不是已选银行或动态纹波结果；也允许首轮不交付该估计并按既有缺项契约表达 |
| 温度/效率 | 可以保留公共输入兼容性，但不计算温度、器件能量、系统损耗或效率；不能以理想无损假设显示 100% 系统效率 |

实现前步骤 0 固定首轮最小输入键、兼容字段和报告映射。原则：以 NPC 的 `vdc_nom`、`vac_ll_rms`、`f_line_hz`、`fsw_hz`、`pout_w`、`power_factor`、纹波目标等现有表达为基础；为超前/滞后增加拓扑局部的明确选项，不更改旧 PF 符号契约。缺失相位选项的默认采用滞后，在 PF=1 时相位为 0。运行点接口若不能携带该选项，先将相位类型固定于该次设计，通过运行点 PF 幅值刷新；不因此修改公共 `OperatingPoint` 或宣称支持 GUI 中未提供的独立相位切换。

零电流仍需能产生有限且确定的基础结果；可以对精确零值采用明确无载路径/事件标记，不设置硬件换流阈值，不推定 ZVS。详细零电流换流数值策略保留后续。

### 2.2 五组暂缓工作

| 暂缓内容 | 第一轮处理 | 后续接入触发 |
|---|---|---|
| 真实案例器件技术/型号/混合技术、数据手册曲线、第三象限、恢复覆盖、封装配对 | 不进入真实器件选型；不评估器件能量 | 开始真实硬件及器件损耗阶段 |
| 死区值、最短脉冲、零电流阈值、延迟、ZVS/Coss/寄生 | 使用第 2.1 节零死区理想模型，声明边界 | 开始有限死区及非理想换流阶段 |
| 完整母线/PF/负载包络、不平衡动态、闭环中点控制 | 只验证第 5 节有限案例和基础输入/调制合法性，不宣称完整工作范围 | 开始工程包络或控制扩展 |
| 电容源电流动态、损耗/热/辅助组件、实物磁件/散热/体积及精度 | 不接真实组件设计或相应结果 | 开始组件与多物理场链路 |
| 完整类型化适配、公共字段扩展、真实选型、完整实现/GUI/导出证据 | 暂缓完整工程链及新共享模型；只做首轮计算接口所必需的局部映射、基础测试及 GUI 数值核验；不要求完整 JSON/CSV 工程导出 | 扩展完整工程链；首轮不得把暂缓理解为完全不测试新增代码 |

不为暂缓项新增提前审批或反复澄清要求。首轮常规实现选择依既有架构完成；只有无法从契约判断的实质电路/字段含义才提出澄清。

## 3. 分类、文件影响和复用原则

当前写计划属于文档变更。后续新增 T-type 涉及注册、能力、共享求解与 GUI，因此按共享集成处理。下表是预定范围，步骤 0 按消费者核定；新路径均标为拟新增，不能当作已经存在。

| 路径/模块 | 预定工作 | 消费者与验证范围 |
|---|---|---|
| `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_t_type_inverter/`（拟新增） | `__init__.py`、`topology_contract.py`、`input_schema.py`、`synthesizer.py`、`waveform.py`、`stress.py`、`evaluator.py`；必要的局部数据/读回模块 | T-type 基础链全部测试 |
| [NPC waveform](../../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py) | 界定并最小提取输出侧公用计算；保留原接口包装及结果 | NPC 电流参考、占空比、分段积分、周期求解及事件回归 |
| 公用三电平计算模块（路径在步骤 0 确定） | 电平序列、三线共模、电感事件积分、周期求解；不混入 NPC/T-type 器件角色 | 仅有实际调用的拓扑；抽取前后 NPC 可比结果须核对 |
| [注册表](../../src/pe_claw_gui/topologies/base/registry.py) / [能力声明](../../src/pe_claw_gui/topologies/base/capabilities.py) | 增加 T-type 独立 ID、插件/表单入口、首轮边界说明 | 注册/插件/输入路由测试；旧 20 个 ID 保留，新总数 21 |
| [共享能力 helper](../../src/pe_claw_gui/topology_capabilities.py) | 优先利用 `FIRST_PASS_TOPOLOGY_ONLY_IDS` 表达 T-type 首轮状态，不沿用“所有已实现拓扑都可选器件”的默认推断 | full pipeline、refresh 和按钮支持范围；旧 ID 行为保持 |
| [拓扑流水线](../../src/pe_claw_gui/pipeline/run_topology_pipeline.py) / [完整流水线](../../src/pe_claw_gui/pipeline/run_full_pipeline.py) / [刷新](../../src/pe_claw_gui/pipeline/run_operating_point_refresh.py) | 优先复用现有接口和 first-pass 返回；必要时仅补能力驱动的入口保护 | 基础贯通、固定 candidate、未接下游不被调用 |
| `src/pe_claw_gui/app/topology_forms/three_phase_three_level_t_type_inverter_form.py`（拟新增） | 设计与运行点输入、首轮说明、两按钮、后续阶段禁用/明确阻塞 | GUI 实际操作和输入来源 |
| [设计控制器](../../src/pe_claw_gui/app/controllers/run_design_controller.py) / [波形控制器](../../src/pe_claw_gui/app/controllers/waveform_controller.py) | 优先复用；必要的未支持操作保护，不能只靠隐藏按钮 | 当前 state report、变更输入后的刷新、无错误选型 |
| [DC-AC 页面](../../src/pe_claw_gui/app/category_views/dc_ac_page.py) / [卡片资源](../../src/pe_claw_gui/app/topology_card_assets.py) | T-type 描述、独立识别；现有资源契约要求独立图时补简单准确的示意资源 | `test_dc_ac_registry_category.py`，不能用 NPC 图片冒充 T-type |
| [Summary](../../src/pe_claw_gui/app/result_views/summary_view.py) / [Waveforms](../../src/pe_claw_gui/app/result_views/waveform_view.py) / [Stress](../../src/pe_claw_gui/app/result_views/stress_view.py) | 适配 T-type 的三相/12 门极/主中点应力，显示当前工况及估计/实际差别 | 基础数值/曲线来源；禁止显示 NPC 箝位角色和未实现系统效率 |
| [DesignReport](../../src/pe_claw_gui/models/design_report.py)、[WaveformSet](../../src/pe_claw_gui/models/waveform.py)、[StressResult](../../src/pe_claw_gui/models/stress_result.py)、[OperatingPoint](../../src/pe_claw_gui/models/operating_point.py) | 原则上只消费现有模型；多相/逐位置数据用明确的拓扑局部载荷映射，不重定义旧字段 | 步骤 0 记录兼容字段具体含义；若需要公共字段变更，先修订影响及回归范围 |
| `tests/test_t_type_*.py`（拟新增） | 第 6 节各步测试 | 第 7 节矩阵与分层 |
| 本计划、T-type 契约、README、ChangeLog | 实现进展、首轮范围和 21 个注册项说明 | 不提前声称硬件/效率支持；日志 append-only |

不修改库记录、NPC 器件角色、公共损耗/热公式或历史迁移基线。器件/电容/磁件/损耗/热/几何阶段本轮只验证不误调用；首轮物理对象声明不等于已建立对应库角色。暂缓完整 structured-output schema 扩展及其工程导出验收。

当前没有 T-type 验证入口；现有 `scripts/validate_topology_engineering.py` 只适配两相 PFC，不能直接用其成功回执代表本拓扑。首轮使用显式 pytest 文件/节点；不为套用入口而扩展无关工具。

## 4. 关键数据语义、所有权和失效条件

具体连接/公式引用 T-type 契约第 2–5、8–9 节；本节仅限定首轮数据生命周期。新键名、数据类、兼容字段赋值在步骤 0 固定并补到契约首轮映射中，避免现在凭空承诺已有字段。

| 数据 | 对象/单位/统计 | 基础生产者 → 消费者 | 刷新/缺项口径 |
|---|---|---|---|
| 输入与工况 | 总母线 DC V，基波线电压 RMS V，有功 W，Hz，PF 幅值/相位类型 | input schema / operating point → 全链 | 数值有限且物理合法；运行点来源与设计来源分开 |
| 合成参数 | 每相 L（H）、目标纹波 pp/Ipk；如交付电容估计需区分 Ceq 与单银行 F | synthesizer → candidate / Summary / waveform | 设计时一次合成；刷新保持数值和身份不变；不是已选实物 |
| 电压序列 | 三相 pole-to-O、去共模相电压、线电压，瞬时 V | 三电平计算 → 电感/GUI | 不能把 pole-to-O 当电网相电压；当前母线重算 |
| 电流 | 三相瞬时 A、时间加权 RMS/峰值/局部纹波 A | event integration → stress / GUI | 目标基波 RMS 与含纹波实际 RMS 分开；不可用时不回填设计数组 |
| 门极/路径 | 12 个唯一位置，0/1 门极；带电流方向的承载路径 | T-type waveform → 导通/事件/GUI | 第 4/5 节契约；所有门极与电流同时间轴 |
| 逐位置应力 | 每位置局部电流 A、理想静态阻断 V；主/中点组保守摘要 | T-type stress → report / Stress | 无波形时仅明示设计估计；有波形后使用实际应力；不虚构额定耐压/选型通过 |
| 理想事件 | 前后电平、时刻 s、位置、相/局部电流 A、换流阶跃 V | 路径解析 → report / 基础诊断 | 零死区、无事件能量；零电流类别不强制标为软开关 |
| 当前报告 | topology/run/candidate 和实际工况身份 | pipeline/controller → state report / views | 不使用旧拓扑/旧工况；失败不得继续显示旧结果为当前有效结果 |
| 未接阶段 | device/capacitor/magnetic/loss/thermal/geometry/sweep | 能力入口 → GUI/报告 | 使用既有未运行/不可用/空结果语义和原因，禁止伪造成功或部分效率 |

`WaveformSet` 的通用数组可能默认用于单相；必须逐字段指定它代表 A 相、线电压或何种兼容量。无物理模型的电容数组不能填假波形以让绘图通过。`StressResult.rectifier` 不能静默改成“中点开关”；可优先在拓扑局部载荷保留完整数据并使用 T-type 专用读回，公共字段仅保留已有可解释含义。

固定参数刷新指 candidate 的 L、合成电容估计（如有）、额定设计功率、fsw 及身份不变，并非已完成“固定实物硬件”验收。刷新仅变更该次请求的母线、负载/PF幅值与相应波形应力；相位类型按首轮接口约定。三相电网电压及 fsw 的设计输入修改重新 Run Design，不在刷新中隐式重新合成。

## 5. 首轮有限案例与独立预期

不在此冻结完整工程支持包络。以下是用于确认基础链路的代表案例与受控失败，不表示实物可采购或全工作范围覆盖。

| 案例 | 输入/操作 | 必须检查 |
|---|---|---|
| B1 代表设计 | Vdc=700 V，VLL=400 V，P=10 kW，fline=50 Hz，fsw=20 kHz，PF=1，目标纹波 pp/Ipk=0.2 | 相电压 230.940108 V RMS，基波电流 14.433757 A RMS、20.412415 A peak，`m_grid≈0.933139`；L 后实际命令仍须可调制 |
| B2 固定参数负载 | 同一 B1 candidate，load=0.1/0.5/1.0 | 负载取当前请求；目标基波随功率变化，实际 RMS 单独积分；L 不变，不重新合成或选型 |
| B3 PF 相位 | PF=0.8、滞后/超前两次设计及各自刷新 | `phi=±acos(0.8)`，电流 18.042196 A 基波 RMS；超前/滞后方向独立核对；不可达点不能算有效通过 |
| B4 母线刷新 | 同一 candidate，在 700/800 V 运行 | 极点 ±Vdc/2，主开关静态上限 Vdc，中点 Vdc/2；每点命令可行性单独检查 |
| B5 强制不可达 | 设计或刷新 Vdc=500 V、VLL=400 V，或受控超限命令 | 给出可调制/饱和诊断，不把裁剪后的失败点当目标已达到；不沿用旧图为当前有效结果 |
| B6 状态/方向 | P/O/N × 正/负电流，及精确零电流 | 端子方向、门极互锁、12 位置、局部符号、无伪造 clamp role；零值有限且不宣称 ZVS |
| B7 理想事件 | P↔O/O↔N × 正/负电流 | 共 8 类；时刻取共同事件边界、局部方向正确、半母线阶跃；不计算器件能量 |
| B8 非法输入/状态 | 非有限、Vdc≤0、P≤0、fsw≤0、PF不在(0,1]、非法相位类型、直通门极及直接 P↔N | 明确原因，按既有异常族拒绝；不生成有效设计结果 |
| B9 状态隔离 | NPC→T-type、T-type→NPC，两顺序分别重复 | 相同模型/工况结果重复；原报告不变，run目录不串用，角色和绘图不串拓扑 |
| B10 用户链路 | 切换拓扑、Run Design、Generate Waveforms、修改运行点再生成 | 当前 state report 与 Summary/Waveforms/Stress 数值一致；不误触发真实选型/损耗/效率 |

公式参考必须独立于生产 helper：基础三相功率方程、单段电感 `di=(v_phase-v_grid)dt/L` 及正弦电网解析积分、三线 KCL、分段时间加权电流指标。相同电平/母线/L/工况的 NPC/T-type 输出波形一致性仅是复用回归，不代替器件路径正确性。

首轮建议数值门槛在步骤 0 经量纲审查固定：纯代数参考 `rtol=1e-9`、V/A/H 分别 `atol=1e-8/1e-8/1e-12`；单段解析电流 `atol=1e-7 A, rtol=1e-8`；三线瞬时电流和 `atol=1e-7 A`；周期端点电流差 `atol=1e-4 A, rtol=1e-5`。完整周期数值指标需同时记录时间步/事件积分精度及收敛证据；不能用宽容差掩盖饱和或周期求解失败。位置、状态、ID 精确比较，GUI 按实际显示位数核对。

## 6. 分步骤实施与完成门槛

以下步骤当前均待执行。每一步在其必要验证通过后更新 ChangeLog、检查 diff/暂存范围、独立 commit/push 并核实远端；随后才能标记完成。记录源码版本、解释器/包/测试来源、命令/退出码/耗时、证据与未验证范围。若完成状态回执另提交，记录两个 SHA；不得提前填写“通过”。

| 步骤 | 主要交付 | 依赖 | 当前状态 |
|---|---|---|---|
| 0 | 冻结首轮输入/输出映射、共用求解范围和验证基准 | 本计划 | 待执行 |
| 1 | 独立 T-type 契约、输入及插件骨架 | 0 | 待执行 |
| 2 | 基础参数合成 | 1 | 待执行 |
| 3 | 三电平输出与三相电感电流 | 2 | 待执行 |
| 4 | T-type 12 路门极、导通路径和理想事件 | 3 | 待执行 |
| 5 | 逐位置应力、报告及首次后端贯通 | 4 | 待执行 |
| 6 | 注册/能力/GUI 接入与未接阶段保护 | 5 | 待执行 |
| 7 | 固定参数运行点刷新 | 6 | 待执行 |
| 8 | 首轮贯通、旧拓扑回归、隔离与收尾 | 7 | 待执行 |

### 步骤 0：核对基础并冻结首轮接口

- 读取实际 NPC、registry/capability、模型、pipeline、controller/view 及下列已有测试；确认当前 20 项注册和 GUI 两按钮调用关系。
- 列明首轮输入键/单位、超前滞后承载方式、兼容 `WaveformSet/StressResult` 字段逐项映射及拓扑局部结构；不把尚未确定的映射写成已实现。
- 确定共享求解模块路径、调用者、NPC 保留包装函数和抽取前基准；记录归一化只排除 run ID/时间/专属临时路径，保留电压电流和事件等工程内容。
- 明确 L 合成公式的三电平调制依据与 target/achieved 区别；电容初值若交付则写清仅估计、不接动态电容；记录首轮绕过下游选择以及按钮保护位置。
- 文件：本计划、T-type 契约的首轮范围/字段映射（仅必要文档）；不提前修改生产代码。验证：来源预检；按将抽取的函数选择已有 NPC 基础测试执行并留基准；审查引用和 diff。
- 完成：输入/映射、代表案例、容差、具体后续命令、共享消费者和未支持阶段均可判定；当前测试实际回执与提交/推送齐全。若基准失败先记录根因，不靠修改黄金值开工。
- 实际执行/Git 回执：待执行。

### 步骤 1：独立拓扑身份、输入与插件骨架

- 拟新增 T-type 包的 `topology_contract.py/input_schema.py/__init__.py`；固定角色/位置、连接和阶段支持边界，提供默认输入及标准解析异常。
- 插件按现有 `build_spec/synthesize/generate_waveforms/extract_stress/evaluate/build_report` 接口组织；尚未实施的 hook 明确不可用，不假装返回成功，也不注册到 GUI 供用户运行。
- 拟新增 `tests/test_t_type_step1_contract.py`：身份唯一、3 相/12 位置、方向/互锁、默认 spec、单位转换、缺项/非法值；导入不得运行计算或写工件。
- 验证：上述新测试在创建后显式执行；不执行真实选型或 GUI。完成：默认输入与错误输入契约通过，导入隔离通过；插件完整计算仍标为后续，Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 2：基础参数合成

- 新增 `synthesizer.py`；计算三相电压/电流、调制量和相电感初值；电容初值按步骤 0 约定处理；candidate 保存首次合成参数及首轮模型说明。
- 继承 NPC 数学基础时使用独立方程核对，不能继承 NPC 半母线器件耐压到主开关。按目标纹波计算 L 后，后续 waveform 单独报告实际纹波。
- 拟新增 `tests/test_t_type_step2_synthesis.py`：B1/B3 代数、量纲、PF/相位、B5/B8 输入和不可达边界；验证不输出器件/效率假结果。
- 验证：step1+step2；若修改共享合成函数，增加其实际旧消费者。完成：基本 candidate 可用于电流求解，参数与目标/估计语义清楚；Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 3：复用输出侧求解，生成三相波形

- 最小提取步骤 0 冻结的电平占空比/中心对齐序列、统一事件时间轴、三线共模及电感分段积分/周期求解；保留 NPC 兼容包装，不移动器件映射进入公用模块。
- 实现 T-type `waveform.py` 输出侧；先支持理想平衡母线、一线路周期、明确时间轴和有限数组；精确分段电流不能仅用正弦加独立三角纹波替代。
- 对不可达电压与周期未收敛给诊断，不通过端点硬修正或裁剪隐藏失败。求解器可以有参考电流跟踪策略，但要声明它是基础稳态求解而非真实闭环控制仿真。
- 拟新增 `tests/test_t_type_step3_waveforms.py`：B1、B3/B4 可行点、B5；独立单段解析积分、KCL、事件连续性/周期、基础相位与实际 RMS；抽取前后 NPC 工程结果对比。
- 验证：step1–3 + 第 7 节 NPC 求解回归组；如调用图影响更多拓扑，补对应消费者。完成：电压/电流可用、公用提取前后 NPC 可解释且无意外差异，Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 4：独立门极、导通和理想换流

- 在 T-type 局部实现 `(g_P,g_N,g_A,g_O)` 门极表，得到 A/B/C 共 12 路门极；按契约解析 6 种 IGBT 参考路径和器件局部有符号电流。
- 从同一事件边界生成 8 类相邻电平理想换流记录；主/中点身份、前后状态、局部方向、半母线阶跃均明确。暂不调用共享器件事件能量函数，不把负相电流当作软开关证据。
- 精确零电流和消失占空段应确定且无重复/非法跳变；不引入有限死区/短脉冲硬件策略。不得出现 NPC clamp 角色。
- 拟新增 `tests/test_t_type_step4_paths_events.py`：B6/B7/B8 全部状态/方向、非法互锁/P↔N、事件时刻来源、逐位置电流独立路径计算。
- 验证：step1–4；公用序列发生变化时重跑 NPC 求解/事件组。完成：波形、门极与物理路径一致，有限结果与独立路径预期通过；Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 5：应力、报告及首次后端贯通

- 新增 `stress.py/evaluator.py` 并完成插件六个 hook；保留 12 位置电流和阻断电压，给主/中点两组保守摘要。
- `include_waveforms=False` 时明确提供设计估计；`True` 时使用实际波形电流。主开关 Vdc、中点 Vdc/2；不输出虚构过冲、选型耐压通过或器件损耗。
- 依据步骤 0 的兼容映射组装现有 DesignReport；未接硬件阶段为空/未运行且有原因；不创建新的共享字段语义。
- 尽早调用 `run_topology_pipeline` 跑 B1，无波形和有波形两种入口均实际执行；这就是首轮早期代表案例，不以真实库为本轮前提。补充一次受控失败链，保留失败原因/run 归属。
- 拟新增 `tests/test_t_type_step5_pipeline.py`：报告身份、B1 数值、12 位置、含纹波 RMS、估计/实际切换、空硬件/无效率、专属输出根。完成：首条后端完整基础链真实通过；Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 6：注册、能力、GUI 与入口保护

- 接入 registry/capability/form/category；总注册数由 20→21，DC-AC 3→4。调整对应精确预期时保留原 20 项及能力/legacy 唯一性断言，不把精确检查改成宽松下限来躲避问题。
- 优先加入现有 first-pass-only 能力集合，让 `run_full_pipeline` 与刷新跳过未接选型；核查 Run Capacitor/Run Magnetics/Efficiency Sweep 等独立入口，既要禁用 UI，也要拒绝绕过按钮直接调用。保护只作用于首轮 T-type，旧拓扑行为不变。
- 新增表单和最小准确卡片资源；复用 GUI 两按钮操作；波形页读取 T-type 独立载荷，显示三相电压电流及门极，不借用 NPC key。Stress 显示主/中点应力；Summary 标注理想模型、参数估计和实际运行点。
- 拟新增 `tests/test_t_type_step6_gui.py`：真实 Tk 选拓扑、填输入、Run Design、Generate Waveforms 和当前页面数值/曲线数据；另测能力绕过保护与旧拓扑支持范围。
- 更新 README 的当前计数与 T-type 首轮支持说明，历史 19 项迁移验收口径保留。完成：GUI 基础流程和未接阶段保护实际通过，必要注册/表单回归通过；Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 7：固定 candidate 参数的运行点刷新

- 利用 `run_operating_point_refresh` 与 WaveformController，接通首轮母线、load_ratio、PF 幅值；相位类型按步骤 0 的设计/运行点映射处理。
- 同一 candidate 刷新 B2/B4；按两次不同相位设计检查 B3。禁止调用 synthesize 或任何真实组件选择，电感、合成估计和额定设计身份保持不变。
- 当前 waveform/stress/topology_result 与报告工况一起更新；选择不同拓扑、失败刷新或变更设计参数时不显示旧有效结果。失败原因按现有控制器状态策略呈现；不能用旧设计数组补齐新点。
- 拟新增 `tests/test_t_type_step7_operating_point.py`：所有首轮有限工况、局部方向、固定参数、合成/选型调用为零、旧报告不可变、不可达点/来源失配及 GUI 当前数值。
- 验证：step1–7 +受影响 refresh/controller 旧消费者；完成：固定参数矩阵和状态失效通过，GUI 两次刷新数字匹配；Git 门槛满足。
- 实际执行/Git 回执：待执行。

### 步骤 8：首轮贯通、隔离及收尾

- 累积执行所有 T-type 首轮测试、注册/表单、NPC 求解/事件回归及步骤 0–7 实际触及的旧消费者；不以已收集或历史回执替代当前必要执行。
- 拟新增 `tests/test_t_type_step8_acceptance.py` 和 `tests/test_t_type_step8_isolation.py`；真实控制器/GUI B10，双顺序且重复 B9。波形核心可按明确容差比较；角色/ID 精确比较；归一化只排除明确易变字段。
- 分开记录公式、契约、用户链路和隔离证据；首次后端贯通不是 GUI 验收，NPC 同 helper 一致不是 T-type 路径独立证明。
- 纯基础链不验收原始系统损耗/效率、实物硬件和完整工程导出，注明本轮未交付；全量 pytest/发布验收不默认执行，若共享影响不能界定先扩大门禁并记录原因。
- 更新契约首轮实现映射、README 和计划状态，保留后续五组事项；全部本轮门槛通过且各步已推送后才归档到 `Plan/completed/`，核对移动后的相对链接。
- 完成：首轮完整交付可复核、无未解释的必要失败、生成工件未暂存、ChangeLog/diff/Git 收尾通过。只称“第一轮基础链路完成”。
- 实际执行/Git 回执：待执行。

## 7. 验证命令、测试清单和执行环境

本节命令是未来实施时的执行方案，本次写计划不执行电气测试。每步先核实当前解释器/包/测试来源；系统可能安装了另一份 PE-Claw，必须显式使用当前 `src`。例如在仓库根运行：

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
@'
from pathlib import Path
import sys, pe_claw_gui
root = Path.cwd().resolve()
print(sys.executable, sys.version)
print(pe_claw_gui.__file__)
assert Path(pe_claw_gui.__file__).resolve().is_relative_to(root / 'src')
'@ | python -B -
```

同时记录 pytest 版本、实际测试文件绝对位置、HEAD/dirty 状态和 GUI Tk 可用性。GUI 验证必须实际操作并读取当前数字，Tk 初始化成功只是环境探测。

### 7.1 已存在的旧测试组

| 组 | 已有测试文件/节点 | 使用时机 |
|---|---|---|
| NPC 求解 | `tests/test_npc_step2_current_reference.py`、`test_npc_step3_average_voltage_target.py`、`test_npc_step4_level_sequence.py`、`test_npc_step4_periodic_warm_start.py`、`test_npc_step5_event_segmented_current.py` | 步骤 0 按抽取函数选择；步骤 3 及相关后续变更/终验 |
| NPC 事件 | `tests/test_npc_switching_loss_events.py` | 输出事件或其时间轴受影响时及终验 |
| 注册 | `tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities`、`::test_phase4_router_fails_closed_for_unknown_topology` | 步骤 6 和终验；需要外部历史请求文件的其他节点另审依赖，不隐含已通过 |
| DC-AC 入口 | `tests/test_dc_ac_registry_category.py`、`tests/test_dc_ac_three_phase_three_level_npc_contract.py` | 注册/资源/表单/显示受影响时及终验 |
| 共享流水线/控制器 | 步骤 0 按实际改动挑选现有节点并补本表 | 发生变更时；不得用全 test 目录收集冒充执行 |

注册节点命令示例（执行时使用全新临时路径）：

```powershell
$tTypeValidationTemp = Join-Path (Get-Location).Path '.pytest-tmp-tt-r1-registry'
if (Test-Path -LiteralPath $tTypeValidationTemp) { throw 'Choose a fresh T-type validation directory.' }
python -B -m pytest -q --basetemp $tTypeValidationTemp tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology tests/test_dc_ac_registry_category.py
```

### 7.2 待新增测试和运行方式

步骤 1–8 所列 `tests/test_t_type_step*.py` 全部尚不存在。对应步骤先实现并审查，再执行显式文件；不将这些文件写成现成可用工具。各步累计的 T-type 文件必须全部执行，后续物理路径改动需要重跑已有基础断言。

创建步骤 1 文件之后的执行示例：

```powershell
$tTypeValidationTemp = Join-Path (Get-Location).Path '.pytest-tmp-tt-r1-s1'
if (Test-Path -LiteralPath $tTypeValidationTemp) { throw 'Choose a fresh T-type validation directory.' }
if (-not (Test-Path -LiteralPath 'tests/test_t_type_step1_contract.py')) { throw 'Implement the planned tests first.' }
python -B -m pytest -q --basetemp $tTypeValidationTemp tests/test_t_type_step1_contract.py
```

后续逐步替换/追加本计划中明确的文件，不用宽泛 glob 覆盖遗漏。步骤 0 把各步最终 argv 和消费者选择补齐；运行前检查节点存在，运行后记录通过/失败/errors/skipped/xfail/耗时，必要测试 skip/环境失败不算通过。

### 7.3 四类证据与成本

| 层级 | 首轮实际覆盖目标 | 成本/证据策略 |
|---|---|---|
| 快速公式/路径 | 代数、单段积分、状态、门极、局部方向、非法输入 | 独立预期，不只镜像赋值；轻量测试 |
| 基础后端贯通 | 插件六 hooks、真实 run context、完整三相波形/应力、未接阶段保护 | 使用真实计算而非 mock 全流程；无需库搜索 |
| GUI | 实际 Run Design/Generate Waveforms 及当前数值、未支持入口 | 独立 Tk 场景；共享可复用计算结果仅限不影响状态隔离的断言 |
| 隔离/旧消费者 | NPC/T-type 双顺序重复、NPC 抽取前后与必要旧路由 | 隔离场景独立执行；不得共用可变报告伪装重跑 |

所有工件写入本轮独占 run root/临时目录，测试将 output_root 显式传递；GUI 默认输出也需测试局部隔离。不得清理用户 outputs 或重用会被 pytest basetemp 删除的已有目录。Windows 输出根保持简短，避免嵌套长路径；记录实际工件路径但不提交。

## 8. 当前文档检查与后续完成记录

本次实际范围仅新建本计划并追加 ChangeLog。文档门槛为：状态/授权一致，0–8 步完整且均待执行；引用路径和已有测试节点有效；待新增文件/命令与现有文件区分；用户暂缓五组不成为首轮门槛；电气语义与首轮理想模型无矛盾；ChangeLog append-only；`git -c core.longpaths=true diff --check`、定向/暂存差异及范围检查。

本次不运行 pytest、收集、电气链、GUI、真实库或旧拓扑回归。文档提交/推送不代表步骤 0 开始或任何实现通过。

后续每步回执必填：`实际版本/环境 → 命令与退出码 → passed/failed/errors/skipped/xfail → 耗时 → 数值/工件证据 → 未验证项 → commit → push/远端核实`。若本轮范围内门槛未通过，保持该步未完成；五组后续事项不自动升级为阻塞。

| 首轮收尾门槛 | 当前状态 |
|---|---|
| 独立插件、公式、状态/路径/事件、应力 | 待实施与执行 |
| 后端基础贯通及未接阶段保护 | 待实施与执行 |
| GUI 当前数值与固定参数刷新 | 待实施与执行 |
| NPC 受影响回归、双顺序重复隔离 | 待实施与执行 |
| 各步验证/ChangeLog/提交/推送 | 待实施与执行 |
| 实物选型、损耗效率/热/几何、完整导出、工程包络、硬件验收 | 用户已暂缓；不属于首轮完成声明 |

本轮计划写作回执：计划结构、引用/既有节点、状态/范围、日志追加及 diff/暂存检查在提交前执行；实际提交和推送状态以 Git 回执为准。无生产行为变更，不执行备份或清理。

# 三相三电平 T-type 实施计划：第一轮基础链路跑通

- 状态：Active；步骤 0、步骤 1、步骤 2、步骤 3 已完成并推送；步骤 4–8 待执行。
- 创建日期：2026-10-12。
- 当前授权：执行步骤 4；导通/事件实现与验证已通过，待本次提交推送核实。不自动开始步骤 5。
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
| 电容 | 步骤 0 选定交付标量 Cbank_proxy，沿用明确标注假设的初始估算；不是已选银行、真实最小要求或动态纹波结果 |
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

当前步骤 0 属于文档变更。后续新增 T-type 涉及注册、能力、共享求解与 GUI，因此按共享集成处理。下表是预定范围，步骤 0 已按消费者核定；新路径均标为拟新增，不能当作已经存在。

| 路径/模块 | 预定工作 | 消费者与验证范围 |
|---|---|---|
| `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_t_type_inverter/`（拟新增） | `__init__.py`、`topology_contract.py`、`input_schema.py`、`synthesizer.py`、`waveform.py`、`stress.py`、`evaluator.py`；必要的局部数据/读回模块 | T-type 基础链全部测试 |
| [NPC waveform](../../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py) | 界定并最小提取输出侧公用计算；保留原接口包装及结果 | NPC 电流参考、占空比、分段积分、周期求解及事件回归 |
| `src/pe_claw_gui/topologies/dc_ac/three_level_common.py`（拟新增，步骤 0 冻结） | 电平序列、三线共模、电感事件积分、周期求解；不混入 NPC/T-type 器件角色 | 仅 NPC/T-type；抽取前后 NPC 可比结果须核对 |
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

具体连接/公式引用 T-type 契约第 2–5、8–9 节；本节限定首轮数据生命周期。步骤 0 已将输入键、局部载荷、兼容字段与缺项策略冻结于契约第 14 节；它们是未来实现约定，不是已有代码字段。

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

首轮数值门槛已在步骤 0 固定，见第 9.3 节。完整周期指标必须记录时间步/事件积分精度及收敛证据；不能用宽容差掩盖饱和或周期失败。位置、状态、ID 精确比较，GUI 按实际显示位数核对。

## 6. 分步骤实施与完成门槛

步骤 0–3 的历史实现/推送回执见第 9 节；步骤 4 的实际范围及本次收尾见第 9.10 节。每一步在其必要验证通过后更新 ChangeLog、检查 diff/暂存范围、独立 commit/push 并核实远端；随后才能标记完成。记录源码版本、解释器/包/测试来源、命令/退出码/耗时、证据与未验证范围。若完成状态回执另提交，记录两个 SHA；不得提前填写“通过”。

| 步骤 | 主要交付 | 依赖 | 当前状态 |
|---|---|---|---|
| 0 | 冻结首轮输入/输出映射、共用求解范围和验证基准 | 本计划 | 已完成并推送，见 9.6 |
| 1 | 独立 T-type 契约、输入及插件骨架 | 0 | 已实现并推送，见 9.7 |
| 2 | 基础参数合成 | 1 | 已实现并推送，见 9.8 |
| 3 | 三电平输出与三相电感电流 | 2 | 已实现并推送，见 9.9；共享提取仍待补齐 |
| 4 | T-type 12 路门极、导通路径和理想事件 | 3 | 验证通过，待本次提交推送 |
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
- 实际执行：2026-10-12，以 `7f96bbf` 为生产基准，来源/Tk 预检通过，NPC 六文件 26 项及注册两节点 2 项共 28 passed；完整插件快照 6 份保留，额定重复精确一致。契约第 14 节及本计划第 9 节为冻结成果和实际回执。
- Git 回执：文档提交 `f1dd748cafe052bab81f255dbefc5d193e12af07` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，`git ls-remote` 核实 SHA 相同；本次独立文档提交同步完成状态。步骤 1 不自动开始。

### 步骤 1：独立拓扑身份、输入与插件骨架

- 拟新增 T-type 包的 `topology_contract.py/input_schema.py/__init__.py`；固定角色/位置、连接和阶段支持边界，提供默认输入及标准解析异常。
- 插件按现有 `build_spec/synthesize/generate_waveforms/extract_stress/evaluate/build_report` 接口组织；尚未实施的 hook 明确不可用，不假装返回成功，也不注册到 GUI 供用户运行。
- 拟新增 `tests/test_t_type_step1_contract.py`：身份唯一、3 相/12 位置、方向/互锁、默认 spec、单位转换、缺项/非法值；导入不得运行计算或写工件。
- 验证：上述新测试在创建后显式执行；不执行真实选型或 GUI。完成：默认输入与错误输入契约通过，导入隔离通过；插件完整计算仍标为后续，Git 门槛满足。
- 实际执行：2026-10-12。新增 `topology_contract.py`、`input_schema.py` 和 `__init__.py`，建立独立拓扑 ID、三相/12 位置与 P/O/N 状态契约、首轮默认输入及 SI 规格解析，并提供 `build_spec/synthesize/generate_waveforms/extract_stress/evaluate/build_report` 插件接口骨架。未实现 hook 明确抛出 `NotImplementedError`；插件保持未注册、未接 GUI、未调用共享求解器或真实选型。
- 测试：`python -B -m pytest -q --basetemp .pytest-tmp-tt-r1-s1-final tests/test_t_type_step1_contract.py`；Python 3.12.10、pytest 9.1.1；63 passed，failed/errors/skipped/xfail 均为 0，耗时 8.13 s。既有 `cache_dir` 配置 warning 单列。测试覆盖默认/非法输入、有限值、端子/门极互锁、插件未注册及新进程导入隔离；未运行 GUI、完整设计链、真实库或步骤 2 以后测试。
- Git 回执：步骤 1 实现提交 `b32220dd4999fafb0203e55b06fa8aaa69c3366a` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，`git ls-remote` 核实远端同 SHA；步骤 2 不自动开始。

### 步骤 2：基础参数合成

- 新增 `synthesizer.py`；计算三相电压/电流、调制量和相电感初值；电容初值按步骤 0 约定处理；candidate 保存首次合成参数及首轮模型说明。
- 继承 NPC 数学基础时使用独立方程核对，不能继承 NPC 半母线器件耐压到主开关。按目标纹波计算 L 后，后续 waveform 单独报告实际纹波。
- 拟新增 `tests/test_t_type_step2_synthesis.py`：B1/B3 代数、量纲、PF/相位、B5/B8 输入和不可达边界；验证不输出器件/效率假结果。
- 验证：step1+step2；若修改共享合成函数，增加其实际旧消费者。完成：基本 candidate 可用于电流求解，参数与目标/估计语义清楚；Git 门槛满足。
- 实际执行：2026-10-12。新增 `synthesizer.py`，实现独立 T-type 三相电压/电流、PF 超前/滞后相量、电感初值、调制命令、分裂母线电容代理和逐位置电流估计；`PLUGIN.synthesize` 已接通，未接下游波形/应力/选型。
- 测试：步骤 1 与步骤 2 累计专项测试通过；具体命令、环境和边界见第 9.8 节。低母线不可达点保留显式 `feasible=False` 与原因，不通过裁剪伪造可行。
- Git 回执：步骤 2 实现提交 `87713671abd9ac42e703d0f6c3e190d3c185db58` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，`git ls-remote` 核实远端同 SHA；步骤 3 不自动开始。

### 步骤 3：复用输出侧求解，生成三相波形

- 最小提取步骤 0 冻结的电平占空比/中心对齐序列、统一事件时间轴、三线共模及电感分段积分/周期求解；保留 NPC 兼容包装，不移动器件映射进入公用模块。
- 实现 T-type `waveform.py` 输出侧；先支持理想平衡母线、一线路周期、明确时间轴和有限数组；精确分段电流不能仅用正弦加独立三角纹波替代。
- 对不可达电压与周期未收敛给诊断，不通过端点硬修正或裁剪隐藏失败。求解器可以有参考电流跟踪策略，但要声明它是基础稳态求解而非真实闭环控制仿真。
- 拟新增 `tests/test_t_type_step3_waveforms.py`：B1、B3/B4 可行点、B5；独立单段解析积分、KCL、事件连续性/周期、基础相位与实际 RMS；抽取前后 NPC 工程结果对比。
- 验证：step1–3 + 第 7 节 NPC 求解回归组；如调用图影响更多拓扑，补对应消费者。完成：电压/电流可用、公用提取前后 NPC 可解释且无意外差异，Git 门槛满足。
- 实际执行：2026-10-12。新增 `waveform.py`，实现一线路周期、统一采样时间轴、三相 P/O/N 电平、事件分段理想 L 电流积分、周期稳态求解、共模消除、线电压和 T-type 四门极载荷；`PLUGIN.generate_waveforms` 已接通。运行点可读取实际 `vin_v`、load/PF 幅值并保留 candidate 电感；频率和交流电压不支持覆盖时明确报错。动态分裂电容和中点电压本步骤保持未建模。
- 测试：步骤 1–3 专项测试和 NPC/注册回归均通过；具体命令、环境和边界见第 9.9 节。低母线命令保留 boundary/unreachable 诊断，不用裁剪隐藏失败。
- Git 回执：步骤 3 实现提交 `6cedc35f6d56c34b437222fe9b737b275880062a` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，`git ls-remote` 核实远端同 SHA；步骤 4 不自动开始。

### 步骤 4：独立门极、导通和理想换流

- 在 T-type 局部实现 `(g_P,g_N,g_A,g_O)` 门极表，得到 A/B/C 共 12 路门极；按契约解析 6 种 IGBT 参考路径和器件局部有符号电流。
- 从同一事件边界生成 8 类相邻电平理想换流记录；主/中点身份、前后状态、局部方向、半母线阶跃均明确。暂不调用共享器件事件能量函数，不把负相电流当作软开关证据。
- 精确零电流和消失占空段应确定且无重复/非法跳变；不引入有限死区/短脉冲硬件策略。不得出现 NPC clamp 角色。
- 拟新增 `tests/test_t_type_step4_paths_events.py`：B6/B7/B8 全部状态/方向、非法互锁/P↔N、事件时刻来源、逐位置电流独立路径计算。
- 验证：step1–4；公用序列发生变化时重跑 NPC 求解/事件组。完成：波形、门极与物理路径一致，有限结果与独立路径预期通过；Git 门槛满足。
- 实际执行：2026-10-12，新增 `paths_events.py` 及步骤 4 专项测试，连接 12 位置局部电流/IGBT 通道/反并联二极管、状态阻断电压及精确积分边界换流记录；非法状态/直跳/不连续片段明确拒绝。162 项累计及 NPC/注册专项通过，见第 9.10 节。
- Git 回执：验证通过，待本次独立实现提交与推送核实；不开始步骤 5。

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

本节命令用于后续实施；步骤 0 已执行的精确 argv 及结果见第 9.4 节。每步先核实当前解释器/包/测试来源；系统可能安装了另一份 PE-Claw，必须显式使用当前 `src`。例如在仓库根运行：

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
| 共享流水线/控制器 | `tests/test_dc_ac_operating_refresh_gui_chain.py`（3 个拓扑参数化显示、输入变化和固定硬件刷新） | 步骤 6/7/8 的受影响 DC-AC 消费者；新增 T-type 测试另检查旧 20 项 first-pass 能力不变；本步骤 0 未执行此文件 |

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

后续逐步替换/追加本计划中明确的文件，不用宽泛 glob 覆盖遗漏。各步冻结命令及消费者选择见第 9.5 节；运行前检查节点存在，运行后记录通过/失败/errors/skipped/xfail/耗时，必要测试 skip/环境失败不算通过。

### 7.3 四类证据与成本

| 层级 | 首轮实际覆盖目标 | 成本/证据策略 |
|---|---|---|
| 快速公式/路径 | 代数、单段积分、状态、门极、局部方向、非法输入 | 独立预期，不只镜像赋值；轻量测试 |
| 基础后端贯通 | 插件六 hooks、真实 run context、完整三相波形/应力、未接阶段保护 | 使用真实计算而非 mock 全流程；无需库搜索 |
| GUI | 实际 Run Design/Generate Waveforms 及当前数值、未支持入口 | 独立 Tk 场景；共享可复用计算结果仅限不影响状态隔离的断言 |
| 隔离/旧消费者 | NPC/T-type 双顺序重复、NPC 抽取前后与必要旧路由 | 隔离场景独立执行；不得共用可变报告伪装重跑 |

所有工件写入本轮独占 run root/临时目录，测试将 output_root 显式传递；GUI 默认输出也需测试局部隔离。不得清理用户 outputs 或重用会被 pytest basetemp 删除的已有目录。Windows 输出根保持简短，避免嵌套长路径；记录实际工件路径但不提交。

## 8. 计划创建的文档检查与后续完成记录（创建历史）

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

## 9. 步骤 0 冻结成果及实际验证（2026-10-12）

### 9.1 分类、输入输出和复用检查结论

本次是文档变更：仅本计划、[T-type 契约](../../docs/three_phase_three_level_t_type_contract.md) 第 14 节及 ChangeLog。生产 Python、测试、公共模型/枚举、选择策略、库及历史黄金/迁移证据不变。后续共享集成的实际消费者为 NPC、T-type、registry/capability、DC-AC 视图、三个控制器及 full/refresh 的 first-pass 能力入口。其余拓扑没有新的电气计算调用；新增能力只标 T-type，旧 20 项支持结果必须精确保持。

已核定完整路径：独立插件 → build_spec → synthesize → generate_waveforms → extract_stress/evaluate/build_report → 注册/表单 → RunDesignController/full pipeline → WaveformController/refresh → 当前 state report → Summary/Waveforms/Stress。GUI `MainWindow._on_generate_waveforms` 先用 `get_raw_input()` 检查设计变化，再读 `get_operating_point()`；因此运行点母线必须用独立控件，否则改母线会重新设计而不是固定 L 刷新。

冻结输入/默认值、规格单位转换、candidate 全部必填字段、WaveformSet 兼容字段、StressResult 两类及 12 位置载荷以契约第 14.1–14.3 节为准。选定：正 PF 幅值加 `power_factor_phase`，运行点相位类型固定于设计；实际母线从 OperatingPoint.vin_v 读取；电容提供明确假设的每银行标量代理，动态电流数组为空；rectifier 为反并联二极管路径，主/中点应力从本拓扑载荷读回。既有公共模型不增字段，不把 midpoint 填进 rectifier。

首轮不支持运行点改变网压/fsw：显式拒绝不相等覆盖；不静默忽略。支持设计 fsw/fline 正整数比，完整线路周期用于周期求解。表单仅给首轮输入，模型固定零死区/理想元件。温度、硬件曲线及器件筛选控件不进入首轮。

合成采用独立 `L=Vdc/(8*fsw*ΔI_target,pp)` 单极点初值，与 NPC 历史系数 16 区分；不是三相去共模实际纹波上界。Ceq_proxy=2·Idc/(fsw·ΔVdc,pp)，每银行=2·Ceq_proxy，标注假设充电量尺度，不证明物理纹波要求。B1/B3 标量与 m_command 已独立计算并记录契约；实际分段命令可行性/纹波待步骤 3 验证。

### 9.2 共享求解抽取清单和保留边界

拟新增 `src/pe_claw_gui/topologies/dc_ac/three_level_common.py`，只由 NPC 和 T-type 输出侧 waveform 导入。命名去除 NPC 前缀；显式导入。以下函数当前均在 NPC waveform 中，名单及必要下游依赖已核对，**本步骤未移动任何函数**。

| 当前函数 | 拟共用职责 / NPC 保留接口 |
|---|---|
| `_npc_level_duty_cycles`、`_center_aligned_npc_sequence`、`_sequence_state_at_time` | 对称三电平占空/中心对齐序列/序列采样；旧函数名和签名包装保留。T-type 在进入会裁剪的旧 helper 前验证实际命令并保留饱和诊断 |
| `_sinusoidal_voltage_integral`、`_sinusoidal_voltage_weighted_integral`、`_sinusoidal_voltage_average` | 电网正弦解析积分；不复制数值近似公式 |
| `_simulate_npc_cycle_segments` | 合并三相开关时刻，减共模、L 电流积分、每周期平均命令/电流 |
| `_project_three_phase_current`、`_valid_three_phase_current`、`_empty_periodic_solver_result`、`_solve_periodic_initial_current` | 三线 KCL 投影、输入检查、周期固定点求解；保留 NPC 1e-8 A / 8 次迭代及 warm-start/fallback 行为 |
| `_simulate_npc_event_segmented_currents` | 全周期事件分段求解；内部必须调用不带器件身份的采样核心，不依赖 NPC gate helper |
| `_build_segment_time_index`、`_segment_index_for_current`、`_segment_index_for_state`、`_current_at_event_time`、`_states_at_event_time` | 统一时间索引、精确边界电流及状态；右/左连续策略保留以保持事件与门极一致 |
| `_sample_npc_event_segments` | **只抽取**三相电流/state/pole/phase-neutral/line-line 采样核心；NPC 包装在返回结果上补原 `gates`，T-type 独立补 T-type gates。不能整函数搬迁后让共用模块调用 `_npc_gate_state` |
| `_interpolate`、`_interpolate_series_at_time`、`_switching_period_midpoints`、`_time_average_by_switching_period`、`_required_average_inverter_voltage_by_switching_period` | 周期参考/平均命令和其实际调用的插值工具；保持旧平均定义及参考采样点 |
| `_npc_operating_contract` | 共用理想 L 相量命令核心，显式 lag angle/功率方向参数；NPC 包装保留原返回键。PF 符号解释仍在各自拓扑，T-type 正有功使用符号 +1 和有符号 φ |

不能抽取：`generate_waveforms` 顶层工况/metadata/电容组装，`_npc_phase_state/_npc_gate_state`，`_extract_npc_switching_events_from_segments`，`_npc_device_current_metrics/_current_metrics`，`_rail_current_for_state`，`_operating_power_factor/_clamp_load_ratio`，`_integrate_periodic_capacitor_voltage/_remove_average`。局部波形统计 helper 可保留，不能为了省几行把 NPC 动态电容/样本平均统计带入 T-type 的应力时间积分。

经源码和实际基准确认：NPC `generate_waveforms` 从 candidate.metadata 取 vdc_nom_v/fsw_hz，不采用 OperatingPoint 的 vin_v/频率覆盖。本任务不修 NPC；NPC 原行为必须保留。T-type 明确采用实际 vin_v，拒绝本轮未支持的频率覆盖。负 PF 的 NPC 快照是反向有功兼容性，不是 T-type 超前相位证据。

原私有接口被既有测试导入，抽取后继续保留包装。NPC 事件、角色、电容、元数据/诊断和值不应改变。共用核心导入不得做计算、写工件或缓存本次运行数据；所有片段、初值、结果为每次调用所有。若实际抽取扩大到其他调用者或共享模型，先更新消费者/必要门禁，不沿用“仅 NPC/T-type”声明。

### 9.3 案例和冻结容差

B1–B10 维持第 5 节矩阵，B2 包含额外零负载基础边界（不宣称硬件轻载性能）。B3 两次设计分别生成 leading/lagging；刷新相位固定，各自检查 0.8/1 的 PF 幅值。B4 同一 B1 candidate 的 700/800 V 保留 L=1.071651762 mH；B5 的 500 V 应不可达且旧图不得被当当前成功结果。可行案例需要实际周期平均命令检查，解析 m<1 不能单独验收。

| 量/比较 | 冻结门槛与依据 |
|---|---|
| 三相功率/电压/电流/L/C 纯代数 | rtol=1e-9；V/A/H/F 的 atol=1e-8/1e-8/1e-12/1e-12；参考直接使用方程，不调用生产合成 helper |
| 单段电感解析积分 | atol=1e-7 A、rtol=1e-8；常量相电压与正弦电网解析积分独立实现 |
| KCL / 连续性 | max_abs(ia+ib+ic)≤1e-7 A；相邻片段电流端点差≤1e-7 A；不通过端点强制改写达标 |
| 周期解 | solver residual≤1e-8 A 且收敛；完整周期实际端点差≤1e-7 A。较宽 1e-4 A 建议门槛不再采用 |
| 状态/门极/角色/ID | 精确比较；12 位置和 P↔O/O↔N 八类方向完整；事件时间 atol=1e-12 s，电平阶跃 atol=1e-8 V |
| 应力/纹波时间积分 | 时间权重而非等权样本；单段可独立积分；两倍采样/积分加密后指标 rtol≤1e-4，A 的 atol≤1e-6；先证明收敛，不能把精度门槛当作基波跟踪误差允许值 |
| NPC 抽取前后 | 结构/key/角色/门极/状态/警告精确；V/A/H/F rtol=1e-10，atol=1e-8/1e-8/1e-12/1e-12；事件时间 atol=1e-12 s；周期迭代/诊断精确。任何差异记录字段、两值、误差、单位、basis、owner、容差和证据 |
| GUI | 当前 state report 与同工况载荷；文字按实际格式化位数核对，曲线 data 数组按上列容差，不能仅看标签或按钮完成 |

序列零时长段可以删除但不得形成 P↔N 或重复虚假事件；这是数学事件规范化，不是硬件最短脉冲模型。精确零局部电流标 no-current；不引入硬件阈值/ZVS。不可达/失败点先给具体原因，不能靠宽容差或裁剪隐藏。

### 9.4 实际环境、命令和 NPC 基准回执

生产源码版本 `7f96bbf4c2e41ec1fb59bcb8c5845badf4e35ef2`；分支 `codex/llc-waveform-operating-point-plan`。初始 95 tracked 删除、2 无关 untracked 全保留。解释器 `C:\Users\Lumia\AppData\Local\Programs\Python\Python312\python.exe`，Python 3.12.10 / pytest 9.1.1 / matplotlib 3.11.0 / Tk 8.6.15。包来源已 assert 属于当前 workspace/src；测试文件绝对来源及源码 SHA256 写入 preflight.json；registry=20、DC-AC=3。Tk 创建/销毁成功只证明环境，不是 GUI 流程通过。

本次独占证据根 `.pytest-tmp-tt-r1-s0/`（保持本地未提交），pytest basetemp 为其全新子目录 `pytest-temp/`，JUnit 在父目录，不会被 pytest 清理。显式 `PYTHONPATH=当前src;当前tests`、`PYTHONDONTWRITEBYTECODE=1`、`MPLBACKEND=Agg`；脚本用 python -B 执行。编辑前已说明 NPC 求解/事件/注册专项范围，未执行全量或完整硬件链。

实际测试 argv（在当前仓库根，python 为上列绝对解释器，证据路径在回执中为绝对路径）：

```powershell
python -B -m pytest -o addopts= -p no:cacheprovider -q `
  --basetemp .pytest-tmp-tt-r1-s0/pytest-temp `
  --junitxml .pytest-tmp-tt-r1-s0/junit.xml `
  tests/test_npc_step2_current_reference.py `
  tests/test_npc_step3_average_voltage_target.py `
  tests/test_npc_step4_level_sequence.py `
  tests/test_npc_step4_periodic_warm_start.py `
  tests/test_npc_step5_event_segmented_current.py `
  tests/test_npc_switching_loss_events.py `
  tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities `
  tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology
```

结果：exit 0，28 passed（NPC 26 + registry 2）；failures/errors/skipped/xfail 均 0。pytest 21.44 s，含启动进程墙钟 23.15 s。1 条既有 `Unknown config option: cache_dir` warning 单列；不修改配置。负向边界/饱和、周期 warm-start、精确事件用例属于这 28 项已有覆盖，不是新增测试。

本地 `validate_step0.py` 执行环境预检、pytest 并调用真实 NPC plugin 六 hook 中的 build_spec/synthesize/generate_waveforms/extract_stress/evaluate（不调用 full pipeline、选型或 GUI）；后续补充脚本生成真正 10 kHz 设计快照。快照采用完整 dataclasses.asdict 载荷，allow_nan=False；不归一化，不删字段；没有 run ID、时间戳或输出路径的 direct-plugin 快照。基准记录输入、spec、candidate、OperatingPoint、完整 WaveformSet（含门极、事件、器件指标、旧电容数组）、StressResult、TopologyResult。不是完整 DesignReport/GUI/硬件基准。

| 文件 | 工况/实际行为 | SHA256 |
|---|---|---|
| `nominal.json` | 默认 700 V/400 V/10 kW/PF1/20 kHz；周期残差最大 2.941e-9 A | `c82774144d7b6638ad9f896e189a3c5989692dc42c37b4adac3a383127c10d70` |
| `half_load_pf08.json` | 原 candidate，load0.5/PF0.8；700 V/20 kHz | `f030711f141d620062f90814df350c8be5f1cc4471b697dfa43781710c45cbc2` |
| `reverse_pf08.json` | 原 candidate，load0.5/PF−0.8；保留 NPC 反向有功行为 | `7c231edc1c64daeaa6df3ce5934a8c8d1817db6faa250e935e2ca185ff5fdfb7` |
| `fsw10k.json` | 请求 OperatingPoint 10 kHz，**实际仍 20 kHz**；诊断快照保留，不当 10 kHz 证据 | `014a186c00c4a81c36d104421ca34ff65295d99a82bcd420270a6951053d787f` |
| `nominal_repeat.json` | 独立重新生成 nominal，全载荷 hash 精确相等 | `c82774144d7b6638ad9f896e189a3c5989692dc42c37b4adac3a383127c10d70` |
| `design_fsw10k.json` | 原默认输入仅设计 fsw=10000；200 周期/实际 Ts=100 μs，收敛 | `635d033a8390d46f9faeb7934610cccd217def5ba41b4608e5047ce67ea1ddeb` |

`preflight.json/test_receipt.json/pytest.log/junit.xml/baseline_manifest.json` 保存精确路径/命令/退出码/耗时和源码校验。前 5 次生成/序列化各约 1.05–1.17 s；补充设计 10 kHz 约 0.46 s，6 份共 51,524,494 字节，全部周期收敛。本地证据不纳入 Git，不覆盖 migration/evidence 或用户 outputs。实施步骤 3 前先核实 hash 和源码版本；若本地快照不可用，从本步明确生产基准在独立 checkout 重建并核实既有 hash，不能用抽取后的输出自称抽取前基准。

本次证据分别支持：独立标量推导及字段语义审查、既有 NPC 求解/事件/注册专项、同工况 nominal 重复确定性。**不支持** T-type 数值正确性、T-type 后端贯通/GUI、跨拓扑双顺序隔离、全量旧拓扑验收或真实硬件/损耗/效率；对应必要门禁仍在步骤 1–8。

### 9.5 冻结的逐步验证命令和未支持入口

后续新增 `tests/test_t_type_step1_contract.py`、`test_t_type_step2_synthesis.py`、`test_t_type_step3_waveforms.py`、`test_t_type_step4_paths_events.py`、`test_t_type_step5_pipeline.py`、`test_t_type_step6_gui.py`、`test_t_type_step7_operating_point.py`、`test_t_type_step8_acceptance.py`、`test_t_type_step8_isolation.py`，当前均不存在。以下数组明确各步累计 argv，不执行 glob，也不把不存在文件视作通过；先完成本步实现与必要测试，再运行。

```powershell
$ttNewTests = @(
  'tests/test_t_type_step1_contract.py',
  'tests/test_t_type_step2_synthesis.py',
  'tests/test_t_type_step3_waveforms.py',
  'tests/test_t_type_step4_paths_events.py',
  'tests/test_t_type_step5_pipeline.py',
  'tests/test_t_type_step6_gui.py',
  'tests/test_t_type_step7_operating_point.py',
  'tests/test_t_type_step8_acceptance.py',
  'tests/test_t_type_step8_isolation.py'
)
$ttNpcTests = @(
  'tests/test_npc_step2_current_reference.py',
  'tests/test_npc_step3_average_voltage_target.py',
  'tests/test_npc_step4_level_sequence.py',
  'tests/test_npc_step4_periodic_warm_start.py',
  'tests/test_npc_step5_event_segmented_current.py',
  'tests/test_npc_switching_loss_events.py'
)
$ttRoutingTests = @(
  'tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities',
  'tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology',
  'tests/test_dc_ac_registry_category.py',
  'tests/test_dc_ac_three_phase_three_level_npc_contract.py',
  'tests/test_dc_ac_operating_refresh_gui_chain.py'
)
# 每步执行一次；设为当前已实现步骤 1..8；retry 时更换专属目录名。
$ttStepNumber = 1
$ttValidationRoot = Join-Path (Get-Location).Path ".pytest-tmp-tt-r1-s$ttStepNumber"
if (Test-Path -LiteralPath $ttValidationRoot) { throw 'Choose a fresh validation root.' }
$ttTestCount = if ($ttStepNumber -eq 8) { 9 } else { $ttStepNumber }
$ttSelectedTests = @($ttNewTests[0..($ttTestCount - 1)])
if ($ttStepNumber -ge 3) { $ttSelectedTests += $ttNpcTests }
if ($ttStepNumber -ge 6) { $ttSelectedTests += $ttRoutingTests }
foreach ($ttNode in $ttSelectedTests) {
  if (-not (Test-Path -LiteralPath ($ttNode.Split('::')[0]))) { throw "Missing test: $ttNode" }
}
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src') + ';' + (Join-Path (Get-Location).Path 'tests')
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLBACKEND = 'Agg'
# 完成第 7 节来源/解释器/Tk 预检后，创建证据根。
New-Item -ItemType Directory -Path $ttValidationRoot | Out-Null
python -B -m pytest -o addopts= -p no:cacheprovider -q `
  --basetemp (Join-Path $ttValidationRoot 'pytest-temp') `
  --junitxml (Join-Path $ttValidationRoot 'junit.xml') @ttSelectedTests
```

步骤 1/2：累计新文件；步骤 3–5：累计新文件+NPC 求解/事件；步骤 6/7：累计新文件+NPC+注册/三个 DC-AC 消费者；步骤 8：全部 9 个新文件+相同旧组。每次记录日志/退出码/JUnit，pytest 不替代 GUI 当前数字的专门断言。抽取前后全 payload 比较纳入 step3 文件；双顺序独立重跑纳入 step8 isolation 文件，不共享可变 fixture 伪装重复。若实际改动导致更多 consumers，扩充清单而不是只沿用本矩阵。

后续测试显式 scoped output_root/run context，GUI 控制器工件也进入专属根；已有测试若默认写全局 outputs，先核实或以适用测试 fixture 隔离输出，不能删除用户结果。`test_phase5_pipeline_closure.py` 的全部拓扑真实库链不属于本次冻结所需门禁；仅能力成员新增、NPC 输出侧抽取与 DC-AC 视图受影响时按上述组覆盖。如改公共模型、阶段次序、选择器或通用结果语义，增加对应所有消费者，影响无法界定才使用全量门禁。

未支持入口保护归属：`FIRST_PASS_TOPOLOGY_ONLY_IDS` 只新增 T-type，full pipeline 与 refresh 复用已有 early return；`RunDesignController.run_active_capacitors/run_active_magnetics` 和 `EfficiencySweepController` 独立入口需检查同一能力。表单隐藏/禁用组件、磁件、效率按钮只是辅助，直接调用控制器仍须明确拒绝；T-type 测试断言真实选择器/损耗/热/几何调用为零，并确认旧 20 项能力 unchanged。波形失败在 WaveformController/current state 和 MainWindow 页面清除有效旧数据；保留固定 candidate 供恢复，不沿用旧图为当前成功。

### 9.6 步骤 0 Git 与收尾

文档/语义/引用/函数与节点存在性、生产源校验不变、ChangeLog append-only、定向/暂存 diff 和范围在提交前核对。仅提交三个文档至既有 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；不修改 master 或 origin，不纳入既有删除和本地证据。完成状态须在提交已推送并核实远端后同步；本轮不备份、不清理、不开始步骤 1。

实际静态检查：两文档 36 个本地引用有效，源函数清单与实际 AST 核对、两个注册节点存在、9 个实施步骤/9 个拟新增测试文件状态正确；651 个生产 Python 文件 SHA256 不变；6 个基准 payload hash 及字节数核实；ChangeLog 对 HEAD append-only；定向差异已审查，`git -c core.longpaths=true diff --check` exit 0。无电气行为变更，不重复 pytest；本地 `documentation_checks.json` 留回执。

- 本步骤三文档提交 `f1dd748cafe052bab81f255dbefc5d193e12af07` 已推送；`git ls-remote pe-claw-1.1 refs/heads/codex/llc-waveform-operating-point-plan` 返回相同 SHA，步骤 0 本体门禁完成。
- 完成状态以独立计划/ChangeLog 文档提交同步；该回执提交 SHA 与最终推送核实见本次完成报告及 Git 历史，不重复工程测试。步骤 1–8 仍待执行，计划保持 Active。

### 9.7 步骤 1 实际执行与 Git 回执（2026-10-12）

步骤 1 按本计划的拓扑局部范围执行，分类为拓扑插件/输入契约新增；没有修改 registry、GUI、共享模型、共享求解器、NPC 行为、库记录或用户结果。新增文件为 `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_t_type_inverter/topology_contract.py`、`input_schema.py`、`__init__.py`，以及 `tests/test_t_type_step1_contract.py`。契约固定三相、P/O/N 三状态、12 个开关位置、端子/反并联方向和互锁；输入层实现步骤 0 冻结的默认值、SI 转换、范围/有限性/频率整数比校验，并对非零死区、未知模型范围和非 PD-SPWM 请求 fail-closed；插件未注册且计算 hook 明确不可用。

验证命令为 `python -B -m pytest -q --basetemp .pytest-tmp-tt-r1-s1-final tests/test_t_type_step1_contract.py`，解释器 Python 3.12.10、pytest 9.1.1，结果 63 passed、0 failed/errors/skipped/xfail，8.13 s；既有 `Unknown config option: cache_dir` warning 单列。专项测试实际检查默认/部分输入、非法和非有限输入、物理端子映射、门极互锁、未注册状态、hook fail-closed，以及新进程导入无计算/写入。未验证 GUI、完整 T-type 计算链、真实器件/选型、旧拓扑回归或步骤 2–8；`outputs/` 和 pytest 临时目录保留为本地工件，未纳入提交。

实现提交 `b32220dd4999fafb0203e55b06fa8aaa69c3366a` 已完成并推送；本计划/ChangeLog 的状态回执随后以独立提交同步。步骤 2 当时仍待用户确认，计划保持 Active。

### 9.8 步骤 2 实际执行与 Git 回执（2026-10-12）

步骤 2 按计划作为拓扑局部合成实现执行，没有修改共享合成函数、registry、GUI、共享模型、NPC 行为、库记录或用户结果。新增 `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_t_type_inverter/synthesizer.py`，并将插件 `synthesize` hook 接通；新增 `tests/test_t_type_step2_synthesis.py`，同时更新步骤 1 插件断言以反映步骤 2 已实现。

合成输出包括三相相电压/基波电流、PF 相位有符号相量、独立 `L=Vdc/(8*fsw*delta_I_target_pp)` 初值、`m_command`（含电感压降相量）、目标纹波、`Ceq_proxy`/单银行 `Cbank_proxy`、CCM 启发式和 12 个物理位置的初始峰值电流估计。`candidate.inductance_h` 为每相 L，`candidate.capacitance_f` 为一个分裂母线银行的初始代理；设计估计、公式 ID、单位/模型范围和 target/achieved 语义均保存于 `candidate.metadata`。不产生器件、损耗、效率、热、磁件或几何选择结果。调制命令超限保留 candidate 数值但设置 `feasible=False` 和明确失败原因。

验证使用当前工作区源码，Python 3.12.10 / pytest 9.1.1：`python -B -m pytest -q --basetemp .pytest-tmp-tt-r1-s2-final3 tests/test_t_type_step1_contract.py tests/test_t_type_step2_synthesis.py`，78 passed，failed/errors/skipped/xfail 均为 0，8.24 s；既有 `Unknown config option: cache_dir` warning 单列。独立参考覆盖 B1 标量、PF=0.8 超前/滞后、500 V 不可达、输入边界、candidate 映射、无硬件结果和元数据隔离。未验证波形、实际 PWM 纹波、GUI、完整设计链、真实选型、旧拓扑回归或步骤 3–8。

实现提交 `87713671abd9ac42e703d0f6c3e190d3c185db58` 已完成并推送；本计划/ChangeLog 的状态回执随后以独立提交同步。步骤 3 当时仍待用户确认，计划保持 Active。

### 9.9 步骤 3 实际执行与 Git 回执（2026-10-12）

步骤 3 按输出侧波形范围执行，分类为 T-type 拓扑局部波形新增；未修改 NPC 波形文件、共享模型、registry、GUI、库、选型或公共字段。新增 `src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_t_type_inverter/waveform.py` 和 `tests/test_t_type_step3_waveforms.py`，插件 `generate_waveforms` 已接通。实现复用 NPC 输出侧事件分段理想 L 积分核心作为临时局部依赖，T-type 在本地重建 P/O/N 门极 `(QP, QN, QA, QO)`，未引入 NPC clamp 角色；共享提取和 NPC 包装调整仍保留在后续边界内。

波形结果覆盖完整线路周期、统一时间轴、三相极点/相电压/线电压、参考与实际电流、周期固定点残差、事件片段和诊断。三线 KCL、状态/互锁、PF=0.8 超前/滞后、固定 candidate 的 800 V/半载刷新、频率/交流电压覆盖拒绝和 500 V 不可达诊断均有专项断言。电容电流/动态中点电压、器件应力、有限死区、寄生和闭环硬件行为明确未建模。

验证命令一：`python -B -m pytest -q --basetemp .pytest-tmp-tt-r1-s3-a tests/test_t_type_step1_contract.py tests/test_t_type_step2_synthesis.py tests/test_t_type_step3_waveforms.py`，Python 3.12.10 / pytest 9.1.1，85 passed、0 failed/errors/skipped/xfail，10.68 s。验证命令二：`python -B -m pytest -q --basetemp .pytest-tmp-tt-r1-s3-npc tests/test_npc_step2_current_reference.py tests/test_npc_step3_average_voltage_target.py tests/test_npc_step4_level_sequence.py tests/test_npc_step4_periodic_warm_start.py tests/test_npc_step5_event_segmented_current.py tests/test_npc_switching_loss_events.py tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology`，28 passed、0 failed/errors/skipped/xfail，10.43 s。既有 `cache_dir` warning 单列；未运行 GUI、完整设计链、真实选型或步骤 4–8。

实现提交 `6cedc35f6d56c34b437222fe9b737b275880062a` 已完成并推送；本计划/ChangeLog 的状态回执随后以独立提交同步。步骤 4 仍待用户确认，计划保持 Active。

### 9.10 步骤 4：导通路径与理想换流实际回执（2026-10-12）

- 基准/影响：`d9e825dc4f47f0768b75c0d075623a5990ba59ff`，既有 `codex/llc-waveform-operating-point-plan` 分支及 `pe-claw-1.1` 同名上游。分类为拓扑局部变更：新增 `paths_events.py`、`tests/test_t_type_step4_paths_events.py`，修改 T-type `waveform.py` 及步骤 3 低母线负向测试；计划/日志同步。NPC、公用求解器、注册/能力、GUI、库、公共模型/报告未改变，旧拓扑没有新增调用或字段消费；不运行全套测试。既有无关删除、untracked 与用户结果均保留。
- 物理/字段：按契约第 4/5/7/8/14 节，`three_phase_t_type_pd_spwm_waveforms.positions` 保留 12 个位置瞬时 `signed_current_a/channel_current_a/antiparallel_diode_current_a/reference_path/static_blocking_voltage_v`，单位 A/V，同当前母线/负载/PF/固定 L。O 状态 QA=-i、QO=i，P 状态 QP=i，N 状态 QN=-i，其余承载电流为零。采用 IGBT＋反并联二极管参考，不是 MOSFET 通道分流或型号选择；通道与二极管分解不重叠。位置周期 peak/RMS/average 与应力属于步骤 5，本步不使用等权样本冒充完整周期积分。
- 事件：`events` 由积分片段相邻边界读取真实状态变化，包含相位/时刻 s/前后状态/相电流 A/局部电流 A/通道路径/两处门极翻转/前后阻断 V/带载边沿/潜在恢复二极管身份/半母线阶跃 V。原统一时间线保存为 `event_timeline`。没有能量、恢复能量或 ZVS 字段；ideal-clamped 开通不证明实物软开关。精确零电流记 no_current，不引入硬件阈值；零时长记录删除后仍检查真实相邻状态，不能靠虚假 O 区间合法化 P↔N。完整周期实际用例两端状态相同，无遗漏的周期接缝状态变化。
- 所有权/兼容：`paths_events.py` 生产本地载荷，`waveform.py` 每次调用生成新数据；未来应力/视图/报告只读取当前载荷，当前尚未接通。固定 candidate 和旧结果不得原地修改；非法或缺失片段不返回有效事件。按冻结契约将 `WaveformSet.switch_current_a/diode_current_a` 从原三相最大值代理/空项改为 A_QP 非负通道/反并联电流；其他公共消费者仍因未注册而不触达。身份/状态/门极精确检查，时间容差 1e-12 s、电流连续性 1e-7 A。
- 根因与兼容变化：首轮 126 项中 1 项失败，原步骤 3 的 500 V boundary 波形实际上包含饱和后 P→N 直跳（A 相，12.9 ms，约 −18.8623532 A）。本步按既有禁止直跳契约改为抛 `TTypeWaveformError`，保留原未裁剪调制命令、周期残差和具体相位/时间原因，不返回非法波形。步骤 3 测试加强为必须拒绝并保持 m>1/超限诊断；未增加 skip、放宽容差或构造假的 O 驻留，不修改 NPC 饱和策略。
- 环境/命令：Python 3.12.10、pytest 9.1.1，`sys.executable` 为 `C:\Users\Lumia\AppData\Local\Programs\Python\Python312\python.exe`；显式 PYTHONPATH=本工作区 src;tests，PYTHONDONTWRITEBYTECODE=1、MPLBACKEND=Agg，包来源已 assert 为当前 src，测试来源为当前 tests。最终执行如下，exit 0，162 passed（累计 T-type 134、NPC/注册 28），failed/errors/skipped/xfail 均 0，pytest 22.92 s，1 条既有 cache_dir warning。

```powershell
python -B -m pytest -o addopts= -p no:cacheprovider -q `
  --basetemp .pytest-tmp-tt-r1-s4/pytest-temp-final `
  --junitxml .pytest-tmp-tt-r1-s4/junit-final.xml `
  tests/test_t_type_step1_contract.py tests/test_t_type_step2_synthesis.py `
  tests/test_t_type_step3_waveforms.py tests/test_t_type_step4_paths_events.py `
  tests/test_npc_step2_current_reference.py tests/test_npc_step3_average_voltage_target.py `
  tests/test_npc_step4_level_sequence.py tests/test_npc_step4_periodic_warm_start.py `
  tests/test_npc_step5_event_segmented_current.py tests/test_npc_switching_loss_events.py `
  tests/test_phase4_topology_contracts.py::test_phase4_registry_has_unique_ids_and_capabilities `
  tests/test_phase4_topology_contracts.py::test_phase4_router_fails_closed_for_unknown_topology
```

- 分层证据：独立六导通情况、八非零换流、全部零电流换流、三状态阻断及门极互锁；实际事件电流用 `i_end=i_start+(v_phase*dt−Vgrid_pk/omega*(cos(theta0)−cos(theta1)))/L` 独立验证，abs=1e-7 A、rel=1e-8。B6/B7/B8 包括非法状态/直跳、非有限输入、不连续时间/电流和消失脉冲；B1/B3/B4/B2 实际覆盖 leading/lagging PF0.8、零/0.1/0.5/1 负载、700/800 V，以及之前累计用例。当前输入→插件→波形→位置/事件载荷真实执行；候选不可变、导入隔离和独立返回数据可审查。JUnit 及验证回执保留 `.pytest-tmp-tt-r1-s4/`，失败历史不覆盖，全不提交。
- 未验证/后续：器件时间加权应力、完整后端报告、GUI、选型/损耗/效率、有限死区/恢复能量/寄生、NPC/T-type 双顺序隔离仍待后续步骤。步骤 3 未完成共享模块抽取、事件边界联合绘图时间轴等冻结目标，已明确留作后续修正，不能把本步 NPC 测试当作抽取前后全载荷比较。没有改公共求解/公式，本步无需重新生成 NPC 历史快照或全套回归。
- Git：本次实现/文档暂存范围、ChangeLog append-only、diff --check 与远端 SHA 在收尾核实；推送前不标步骤 4 完成。

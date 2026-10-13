# 三相三电平 T-type 第二轮工程链接入计划

- 状态：Active / 待实施；本次只建立计划，不实施步骤 0–7。
- 创建日期：2026-10-13。
- 当前授权：撰写第二轮工程计划；用户认可接入顺序，生产代码实施尚未开始。
- 拓扑 ID：`three_phase_three_level_t_type_inverter`。
- 工作区：`C:\Users\Lumia\OneDrive - Nanyang Technological University\PE-Claw1.1\PE_Claw_1.1_260928`。
- 撰写基准：`622920211ffa1185799365d0f4d1f50e0119a521`；分支 `codex/llc-waveform-operating-point-plan`。
- 已核实上游及文档推送目标：`pe-claw-1.1/codex/llc-waveform-operating-point-plan`；远端 `https://github.com/Lumia-Xiao/PE-Claw_1.1.git`。不推送 origin 或 master。
- 初始状态：95 项既有无关 tracked 删除及既有 untracked 用户文件、outputs、测试证据；暂存区为空。保留全部，不恢复、不删除、不纳入提交。

## 1. 依据、现状与交付目标

依据：[仓库规则](../../AGENTS.md)、[工程语义契约](../../docs/engineering_contracts.md)、[T-type 电路契约](../../docs/three_phase_three_level_t_type_contract.md) 第 2–5、9–11、14 节、[拓扑计划模板](../templates/topology_change_plan_template.md)、[第一轮已完成计划](../completed/three_phase_three_level_t_type_implementation_plan.md) 第 2.2、9.14 节。

第一轮已经实现独立拓扑、参数合成、三相事件积分、12 门极、方向路径、逐位置应力、GUI 和固定 candidate 参数刷新。首轮 426 个不同测试项及 NPC 六份完整快照回执是历史证据，不能代替第二轮当前版本的工程验收。第一轮归档保持原范围和历史回执。

当前 T-type 属于 `FIRST_PASS_TOPOLOGY_ONLY_IDS`；完整流水线及刷新提前返回，组件/扫描入口被保护。真实选型、两银行电流模型、磁件适配、损耗、热、几何、扫描和完整工程导出尚未接通。

第二轮交付顺序：

```text
半导体两角色选型
→ 每相电感与上/下母线电容银行
→ 选定硬件回读、当前工况刷新与失效管理
→ 本轮范围内损耗、热、几何
→ 固定硬件扫描、当前 GUI 与完整工程报告/导出
```

采用 NPC 已有工程库、数值模型、筛选/排序、搜索扩展和产物机制。T-type 负责正确的电路数据和类型化适配；不创建另一套元器件数据库，也不复制 NPC 的固定型号、磁芯、温度、参考损耗或中点平衡结论。

## 2. 第二轮模型范围与暂缓事项

### 2.1 本轮纳入与计算口径

| 项目 | 本轮约定 |
|---|---|
| 电路 | 沿用常规 T-type、平衡三相三线、共发射极中点支路；6 主支路＋6 中点支路，没有独立 NPC clamp 角色 |
| 器件 | 先以当前 IGBT＋反并联二极管方向契约接入真实注册库；两组允许分别选型号；混合技术及 MOSFET 第三象限不自动认定已支持 |
| 调制/电感 | 保留首轮 PD-SPWM 和事件积分；沿用已实现每相 L 合成，不为匹配 NPC 重写公式；选定磁件按实际 L 重新校核命令与纹波 |
| 母线 | 电气求解仍以给定、平衡母线为基准；电容电压积分是附加纹波估计，不作为反馈改变开关电平的完整动态母线状态 |
| 电容源模型 | 使用完整周期平均供电电流恒定的一阶模型；保存原始 rail/neutral 电流、平均值与电荷漂移；不暗中独立去均值抹平中点漂移 |
| 磁件 | 使用当前 normalized OpenMagnetics v2 生产后端、既有允许策略及搜索；3 个物理相电感；保持 virtual/catalog 来源区别，不把 virtual 推荐写成可采购型号 |
| 热/几何 | 复用现有器件热阻、热界面、磁件热估算、封装和磁件几何；共享散热器采用明确参数的工程近似，重新计算 T-type 结果 |
| 工程范围 | 完整接通本轮所声明的组件、页面和导出；“完整工程报告”表示数据链完整，不等于包含所有物理损耗或硬件验收 |

### 2.2 死区与换流能量继续暂缓

用户明确“不需要管死区以及换流能量”。本轮不新增有限死区、最短脉冲、传播延迟、ZVS/Coss/寄生仿真，不计算 T-type Eon/Eoff/恢复事件能量，也不把这些作为选型启动条件。

公共 NPC 选型流程会调用含开关能量的 loss evaluator；T-type 应利用 selector 已有 `loss_evaluator` 回调复用流程，在适配层供给本轮导通损耗评价及公共热计算。不得为跑通选型隐式启用 NPC 事件能量，或改变 NPC/其他拓扑现有损耗语义。

本轮系统损耗范围明确为：全部开关位置的通道与反并联二极管导通损耗、三相电感铜损/磁芯损耗、上下银行 ESR 等既有电容模型损耗。门极驱动、开关/恢复/Coss、控制、风扇、吸收、均压/预充等未纳入项独立列为 excluded/unmodeled；如库的内置计算将能量项捆绑，步骤 0 冻结可分离接口，不能直接使用其全损耗冒充本轮结果。

损耗、排名、热与效率均携带同一 model scope。效率显示为“本轮建模效率（未含开关/恢复等损耗）”；热结果相应为该范围内的估算，不宣称完整器件结温裕量。被排除项不得写为“实测/物理零损耗”。如果公共字段无法表达范围和不可用项，增加明确的类型化结果/字段及消费者适配；不重定义现有 `DeviceLossResult` 或磁件 `LossResult.total_loss_w`。

完整母线/PF/过载包络、不平衡动态与闭环中点控制、硬件保护/EMI/双脉冲、实物采购与装配实测、全物理效率仍保留后续。无需为这些暂缓项增设提前审批。

## 3. 实际复用入口与影响范围

本次撰写为文档变更；未来步骤为共享集成。每步实施前按实际消费者再次核定，不能仅凭文件位于 topology 包判定隔离。

| 入口/文件 | 已有实现与 T-type 接入方法 | 必须保留的政策/受影响消费者 |
|---|---|---|
| [角色声明](../../src/pe_claw_gui/libraries/semiconductors/topology_roles.py)、[半导体库](../../src/pe_claw_gui/libraries/semiconductors/registry.py) | 新增 `t_type_main_switch` / `t_type_midpoint_switch`，各 6 位置；复用注册库与封装结构过滤 | 不改库记录；角色查询、器件页、布局、全部角色契约消费者 |
| [应力适配](../../src/pe_claw_gui/engines/devices/stress_adapter.py) | 新增两角色设计 envelope / 当前工况请求；从 T-type 逐位置 channel/diode 数据读入 | 设计边界与实际工况分开；NPC/两电平/全桥及依赖该 adapter 的旧家族 |
| [selector](../../src/pe_claw_gui/engines/devices/selector.py)、[器件流水线](../../src/pe_claw_gui/pipeline/run_device_pipeline.py) | `select_switch_device_with_audit`、`merge_switch_stresses`、并联方案与电热筛选；T-type 专用本轮损耗回调 | 审计淘汰原因、完整角色、理想均流、优先较少并联再损耗的现有方案选择；无候选不改过滤条件 |
| [能力](../../src/pe_claw_gui/topology_capabilities.py)、[完整流水线](../../src/pe_claw_gui/pipeline/run_full_pipeline.py) | 按阶段开放 T-type；不能只移出 first-pass 集合便让所有尚未适配下游执行 | 旧 20 拓扑行为不变；registry/capability、full/refresh/controller 路由消费者 |
| [磁件适配](../../src/pe_claw_gui/engines/magnetics/inductor_adapter.py)、[磁件流水线](../../src/pe_claw_gui/pipeline/run_magnetic_pipeline.py) | T-type `InductorDesignRequest` / `InductorOperatingPointRequest`；现有生产后端与固定电感设计搜索 | 初筛、allow、压缩、frontier 扩展、终止/耗尽及 Pareto 推荐；真实范围不得缩小以加速测试 |
| [电容流水线](../../src/pe_claw_gui/pipeline/run_capacitor_pipeline.py)、[电容选型](../../src/pe_claw_gui/engines/capacitors/selection.py) | T-type 上/下 `CapacitorSizingRequest`；同 `list_registered_capacitors`、`select_capacitor_bank` | 技术/耐压/纹波/温度/容量过滤、串并联上限及 min-volume/min-loss/compromise 推荐；不复用 NPC metadata 名 |
| [刷新](../../src/pe_claw_gui/pipeline/run_operating_point_refresh.py) | 复用已选器件/绕组/银行的刷新政策；保留 T-type 来源校验与失败恢复 | 当前 report 所有权、不得重新选型、旧报告不可变；相关控制器/缓存/扫描消费者 |
| [损耗](../../src/pe_claw_gui/pipeline/run_loss_pipeline.py)、[热](../../src/pe_claw_gui/pipeline/run_thermal_pipeline.py)、[总览](../../src/pe_claw_gui/engines/hardware_overview.py) | 单实例计算、数量汇总、热界面和几何方法；增加两角色/两银行/三相布局 | NPC 三角色 helper 不能直接处理 T-type；其他磁件、热、系统总量、geometry 消费者 |
| [扫描](../../src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py)、[结构报告](../../src/pe_claw_gui/reports/structured_output.py) | 同固定硬件扫描、JSON/CSV/曲线机制；增加 T-type 完整性和 scope 读回 | schema validator、字段字典、Summary/Loss/Thermal/Efficiency/Overview/导出及旧报告消费者 |

拓扑局部数据/适配的建议位置：在现有 T-type 包新增 `engineering_adapter.py`（名称在步骤 0 冻结），拥有位置→角色、端口电流、运行依据和硬件读回；数值器件/电容/磁件计算留在各自 engines，编排留 pipeline，展示留 app。只在 NPC/T-type 存在真实重复且合同稳定时提取共同 helper，保留 NPC 包装与回归；不创建万能框架。

输入/归一化/注册/合成基础已经存在，仅按新增工程输入或能力需要扩展。其他拓扑物理公式、库数据、选择政策、历史迁移证据不在改动范围；共享消费者测试仍按字段和调用关系覆盖。旧缺陷若不影响本次接入单列后续，不扩大成无边界修复。

## 4. 数据合同、所有者与失效规则

表中名称为第二轮拟用语义，不是宣称已有生产字段。步骤 0 必须冻结准确 dataclass/metadata 路径、字段字典、适配来源与 model scope，再改代码。T-type 第一轮 `StressResult.rectifier` 是反并联二极管包络，不得映射为中点开关。

| 数据 | 物理对象/单位/统计 | 设计或运行依据；生产者 → 消费者 | 刷新/失效/缺项 |
|---|---|---|---|
| 两组器件应力 | main/midpoint 各 6；V 静态阻断；每位置 A 的 peak/RMS/mean，channel/diode 分开 | main=Vdc、midpoint=Vdc/2；topology stress → 两角色 adapter → selector | 选型用已声明设计 envelope；刷新用当前波形；无数据拒绝，不用全桥公共包络代填 |
| 型号/并联方案 | 每角色型号、每位置 n；物理数量 6n/角色，合计 12n（若统一 n） | device selection → loss/thermal/geometry/report | 包装/module section 与采购封装数量另记，不假设 12n 个位置必为 12n 个独立模块；缺角色阻塞 |
| 导通损耗 | 每位置/每物理器件 W，时间加权通道和反并联二极管功耗 | 逐位置电流＋同库压降/电阻模型 → device / 热 / scope 总量 | 非线性压降不能直接用组平均 RMS；并联每器件电流缩放后求损耗，数量只乘一次 |
| L 与磁件 | 每相 H；3 物理实例；A 有符号瞬时、完整周期 RMS/peak/局部 ripple pp | candidate/波形 → magnetics adapter → 搜索/铜损/磁芯/热/体积 | 选后以实际 L 重新电气校核；设计重新选择与固定硬件刷新分开；缺一相不能出三相合计 |
| 母线端口电流 | J_P/J_O/J_N/I_src，瞬时 A、mean、RMS、C 电荷积分 | T-type 状态及相电流 → capacitor adapter | 保存方向、raw mean 与 charge drift；源模型明确；时间轴/来源不匹配拒绝 |
| 银行容量与纹波 | C_U/C_L 各 F、bank V/Vpp/A RMS、S/P、单只/银行 W | 电容请求→选型→回读→当前 ripple/loss | `Ceq=C_U*C_L/(C_U+C_L)`；首轮 `candidate.capacitance_f` 为单银行初估，不能静默改为 Ceq/已选银行 |
| 热/几何 | 单器件 °C、K/W；单银行/磁件/封装及系统 m³ | 本轮当前损耗＋选定热阻/布局 → thermal/geometry/overview | 明示模型范围与工程近似；更换硬件清旧热/几何/扫描；未知尺寸不补零 |
| 本轮总损耗/效率 | 非重叠必需组件 W；效率 ratio，显示百分数 | 当前 report 两组导通＋3 电感＋2 银行 → typed scope 系统汇总 → views/sweep/export | 必需项完整、有限且≥0；缺任一不可发布 total/eta；不挪用磁件小计字段 |
| 运行身份 | topology/run/candidate/hardware ID、bus/load/PF phase、VLL/fline/fsw、scope | 设计/运行请求 → 所有 producer/readback | source 不匹配、失败或输入变更立即清依赖结果；保留有效硬件供同 run 恢复，旧结果不能填当前缺项 |

端口公式采用电路契约第 10 节：`J_P+J_O+J_N=0`，`i_CU=I_src-J_P`，`i_CL=I_src+J_N`，`i_CU-i_CL=J_O`。I_src 取当前完整周期平均桥端功率/Vdc，并独立检查 `<J_P>` / `-<J_N>` 与平均电荷条件。NPC rail 去均值数组有不同方向口径，只能转换后复用方法，不能直接复制数组。允许用于 ripple 的平均供电移除必须有记录；持续漂移超过周期性容差明确标不可用，不能重置电压伪造稳态。

导通参考：MOSFET 若后续有授权方向模型可用 `Rds(T)*I_channel,rms²`；本轮 IGBT/二极管按各自压降曲线或既有有依据近似，`P=(1/Tline)∫v(i,T)|i|dt`。复用库曲线与插值，必要时在 engine 增加可复用逐位置积分接口，不在 pipeline 写新电气公式。降阶近似记录误差/适用范围，不把组包络用于非线性系统总损耗。

系统结果唯一所有者是当前 report 的本轮范围汇总；`P_scope=P_semiconductor_conduction+P_L_total+P_CU+P_CL`，`eta_scope=P_ac/(P_ac+P_scope)`，P_ac 为该运行点正向平均有功。硬件、母线、VLL、负载、有功、频率、PF 幅值/相位和 scope 相同才比较。0 负载可校核波形及硬件损耗，但 eta 明确不可用；不可达运行点不算有效效率点。

## 5. 分步骤实施与完成门槛

| 步骤 | 交付 | 依赖 | 当前状态 |
|---|---|---|---|
| 0 | 冻结二轮接口、范围、基线和阶段开放方案 | 本计划 | 待实施 |
| 1 | 半导体两角色真实库选型 | 0 | 待实施 |
| 2 | 三相电感接入 | 1 | 待实施 |
| 3 | 上/下银行电流与真实电容选型 | 0、2 | 待实施 |
| 4 | 选定硬件回读、固定硬件刷新与全链来源校验 | 1–3 | 待实施 |
| 5 | 本轮损耗、热、几何及最早真实工程贯通 | 4 | 待实施 |
| 6 | 固定硬件扫描、完整工程 GUI/报告/导出 | 5 | 待实施 |
| 7 | 二轮完整验收、旧消费者回归、隔离与归档 | 6 | 待实施 |

各步实施前写明本步影响与精确验证清单；必要验证通过、ChangeLog 追加、diff 检查、独立 commit/push 并核实远端后才能标完成。当前只是计划撰写授权；本计划不自动触发生产实施，也不新增逐步审批要求。

### 步骤 0：冻结接口、损耗范围与基线

- 读取实际 roles、selector/loss callback、module/diode/geometry、磁件/电容搜索、full/refresh/sweep/controller/report；核实运行环境，记录当前源文件/库来源及校验和。
- 在 T-type 契约新增第二轮映射节；冻结两角色请求、逐位置导通评价、选定磁件/银行读回结构、scope 总量字段、包装统计、设计 envelope 与支持运行范围。公共字段按原义使用，新增类型仅覆盖稳定需要。
- 冻结分阶段能力：保留尚未实现阶段保护；step1 只开放选器件，step2/3 分别开放组件，step5 之后才开放有效 scope 总量，step6 才开放扫描/完整导出。优先既有 capability/adapter；不能用一个全链布尔标记掩盖阶段差异。
- 设计边界使用用户实际输入和可调制性；本轮必验 700/800 V、负载 0.1/0.5/1、PF=1/0.8 的超前/滞后。冻结选择 envelope 的实际波形工况，若某点不可达给出诊断，不抹掉失败，也不默默扩大成 110% 支持。
- 获取当前 NPC 基础与真实工程 report 基线及其他受影响消费者基线。归一化仅排除 run ID/时间/独立临时路径，保留硬件、工程值、单位、scope、状态/警告、来源。
- 文件：T-type 契约、本计划、必要 baseline 工具/测试与 ChangeLog；不提前改物理公式。建议新增 `tests/test_t_type_engineering_step0_contract.py`，检查真实接口/方向/范围和数据读回，不写镜像 Markdown 的测试。
- 验证：第 7 节基础组＋实际 NPC baseline 生成；冻结准确命令/工况/容差，不以 collection 算通过。完成条件为可实施字段表、scope 回调路径及路由方案清楚、有效基线保存、必要验证及 Git 回执完成。

### 步骤 1：半导体两角色真实选型

- 文件：roles、stress_adapter、run_device_pipeline、能力/控制器及 T-type adapter；本轮损耗支持留 device engine。不改 NPC clamp 角色、不改库数据。
- 从 12 位置指标构建设计选择 envelope：主/中点独立耐压、电流、热目标；角色型规格与 package/module section 兼容。单型号在各自 6 位置重复使用，逐位置热/导通评价保留，额定耐压不等于换流阶跃。
- 复用 selector 审计、制造商/技术/结构过滤及单/两/三并联比较；callback 使用本轮导通范围。保留方案完整与 feasible 的区别，不能因选择器返回 complete 但 infeasible 方案就发布通过。
- 选型顺序与评分沿用公共政策；本轮范围分数与 NPC 全损耗分数不同，不作同精度效率比较。记录候选数、过滤、排名、方案与全部失败原因。
- 选型成功后创建器件与封装结果；尚未接磁件/电容/扫描继续 blocked。缺第二角色、耐压不足、非有限曲线或 incompatible module 受控负例保留诊断。
- 新增 `tests/test_t_type_engineering_step1_devices.py`：700 V 主/中点静态 700/350 V，800 V 为 800/400 V；各 6n 位置；反并联二极管无 clamp/BOM 重计；模型 scope、库 provenance、零能量接口调用、并联均流、真实库接受/拒绝及旧角色回归。
- 完成：真实库两角色有效选中或真实搜索失败根因明确并解决到代表案例可用；至少一个真实案例通过，不能用 mock 成功代替。验证第 7 节 devices 组和累计 T-type；Git 回执完成。

### 步骤 2：三相电感接入

- 文件：T-type adapter、inductor_adapter、run_magnetic_pipeline、core-loss excitation 适配、必要磁件 view/能力；不复制 NPC 固定 E80/FT-3M/匝数或 Litz 参考损耗。
- 设计请求用每相 L、实际 waveform RMS/peak/local ripple、双向电流、fline/fsw、每相吞吐与 quantity=3；运行请求用当前 PF/母线/负载及同一硬件。
- 使用 normalized-v2 production 后端与原 allow/search/Pareto；记录初筛、allow 失败后 frontier 扩展、耗尽与前置失败。库版本/数量/过滤/排序/校验和留证。共享型号可以只搜索一次，但三物理实例来源、损耗、体积不能只算一相。
- 用当前电感电压/电流接 core loss excitation audit；既有 half-bus screening proxy 如保留须标明设计筛查，与实际运行励磁区分；B/Ipk、热和损耗不得以平均电流为 0 就判无励磁。
- 推荐磁件实际 L 若改变，存独立已选值并留首轮目标，step4 完整回读前至少做局部电气可调制校核。无磁件时保留器件及搜索诊断，不产假系统总量。
- 新增 `tests/test_t_type_engineering_step2_magnetics.py`：每相/系统数量、实际 ripple、来源、allow/扩展/耗尽及不缩搜索的真实库案例；复用磁件公式独立参考。
- 完成：真实推荐磁件、模型/工程限制清楚，三相计数与最低下游损耗读回验证；第 7 节 magnetics 组＋累计测试，Git 回执完成。

### 步骤 3：上/下银行模型与真实电容选型

- 文件：T-type 端口/波形 adapter、run_capacitor_pipeline、split-link capability、必要电容报告/页面；同一 registered capacitor 库与串并联 selection，不将上/下假称 input/output 普通储能对象。
- 按第 4 节 KCL 建立 T-type 有符号端口电流，保存供电常值、mean、charge drift 和时间积分；输出每银行 current/voltage ripple 与方向。母线依旧平衡给定，电压积分标为估计，不新增完整前级/控制仿真。
- 独立构建上下 `CapacitorSizingRequest`，技术/最小容量/电压 margin/纹波/温度及 S/P 限制来自实际设计。NPC 当前 split request 有 min_series_count=2；T-type 不直接继承固定 2S 或 B43705 基准，明确参数后使用同算法。
- 保留 Nmax/Smax、优化/推荐、初筛不足/上限耗尽诊断。选中 C_U/C_L 后计算 Ceq，回读预测每只/银行电流、ESR/纹波、loss、体积和来源；均压寿命等 NPC 近似可作为明示附加审查，不能称闭环中点控制通过。
- 新增 `tests/test_t_type_engineering_step3_capacitors.py`：三线 KCL、两银行电流差、正确积分符号、相等/不等 C、非零平均漂移拒绝/诊断、真实 S/P、缺上/下银行、NaN/错时间轴/错误来源；至少真实库两银行案例。
- 完成：真实两银行有效，端口公式与原始电荷证据独立通过；第 7 节 capacitors 组＋累计测试，Git 回执完成。

### 步骤 4：选定硬件回读与固定硬件刷新

- 文件：T-type adapter/报告来源验证、run_operating_point_refresh、full pipeline、run_device_pipeline 的 fixed selection 分支、run_capacitor_pipeline、loss 的固定磁件分支、WaveformController/RunDesignController/表单。
- 建立不可混用的 hardware snapshot：两角色型号与 n、三相磁件 model/design/winding/L、上下型号/S/P/C、封装和热配置、scope、run/candidate 身份。保留原 target/初估字段，effective hardware 参数由 typed adapter 提供，不能静默重定义 candidate 字段。
- 选后顺序：形成硬件快照→用 actual L/C 生成当前波形/银行纹波→stress/feasibility→device current evaluation→selected magnetics/capacitors 当前损耗→后续热/几何/总量。若现有接口必须创建新 candidate，明确其 parent/selected 身份，切换原子完成并保留历史对象。
- 当前 full pipeline 对非 LLC 的 capacitor 位于 loss/thermal/geometry 之后；T-type 必须增加限定范围的选后 closure 或阶段 adapter，完成刷新后才发布结果，不全局重排旧拓扑、不把早期小计当最终值。
- 用户选择新推荐组件属于硬件变更；清全部旧 operating/sweep/export，生成新硬件身份。改变运行 bus/load/PF magnitude 只刷新，保留所有型号、数量、L/C、geometry 身份；相位保持设计，切相位重新设计，VLL/fsw 设计修改按现有失效策略处理。
- 缺角色/银行/相磁件、错 run/scope、失败波形清当前结果，保留已选硬件供恢复；禁止 fallback 到旧工况或设计损耗。计数测试断言 selector/synthesis 不被运行点刷新调用。
- 新增 `tests/test_t_type_engineering_step4_refresh.py`：完整固定硬件矩阵、选择更新、无效→有效恢复、旧对象不可变、来源注入及零重选；局部刷新后原 published values 来源核查。
- 完成：所有下游使用同一 actual hardware 与当前 basis，第 7 节 refresh 组＋累计测试及旧 NPC/其他刷新消费者通过，Git 回执完成。

### 步骤 5：本轮损耗、热、几何与最早真实工程贯通

- 文件：device loss integration/aggregation、run_loss_pipeline、run_thermal_pipeline、run_geometry_pipeline、semiconductor geometry、hardware_overview、T-type adapter、类型化模型及 GUI 基础结果。
- 逐位置 channel/diode 导通损耗→两组总量，磁件运行铜/磁芯损耗→3 相总量，银行当前 ESR 模型→上下总量。数量、并联及包装节区只按其物理定义汇总一次，复用公共计算而不把磁件总量字段扩成系统量。
- 在同一 current report 发布第 4 节 scope 总量/效率，完整性检查包括 finite、≥0、全部 physical instance、scope/hardware/basis。缺必需损耗留 partial diagnostics，total/eta unavailable。
- 热采用已选器件 Rth/TIM 和 scope 功耗；共享散热器 Rth/风量/耦合系数均作为明示工程配置，复用 NPC 方法但重新计算，不继承“NPC 已通过”。磁件热沿用现有引擎，验证范围与来源。
- 几何按当前封装、三电感、两银行、散热器模型组装。包装 section 与共享模块外形避免重计；缺尺寸阻塞系统体积，只可保留明确组件小计；不编造物理布置或体积。
- 尽早真实库贯通：代表案例设计→器件→磁件→电容→选后刷新→本轮 loss/thermal/geometry→当前 GUI/报告最小读回。在修饰全部页面之前执行；失败保留 stage、根因、真实候选和 search audit，修复后重跑，不降规格凑成功。
- 新增 `tests/test_t_type_engineering_step5_system.py`：独立积分/电阻解析与库曲线边界、数量、原发布总量/eta、热阻解析、缺组件/非有限/陈旧 scope、真实库同 basis 读回；本轮不要求换流能量结果。
- 完成：真实组件链及范围内系统结果成立，公式/契约/用户链证据分别保存；第 7 节 system 组＋累计测试，Git 回执完成。

### 步骤 6：固定硬件扫描与完整报告/导出

- 文件：run_efficiency_sweep_pipeline、EfficiencySweepController、result views、T-type form、hardware_overview、structured_output、[schema validator](../../scripts/report_schema_validation.py) 和适用字段字典。
- 对第 6 节矩阵使用同一硬件；复用 selected-only magnetic refresh、器件当前评价和 capacitor OP refresh，不重复设计/搜索。T-type PF magnitude/phase 明确转换，不套 NPC 负 PF 约定或 ZVS 标签。
- 每有效点保存完整 components、published total/eta、hardware/basis/scope；失败点保留不可达/缺项诊断，无效点不进入有效曲线，也不能让全局 available/is_complete() 掩盖缺必验点。
- Summary/Device/Magnetics/Capacitors/Loss/Thermal/Efficiency/Overview 均读当前 report；选择组件、改变输入、连续刷新后数字/曲线与来源一致。模型范围、设计 vs operating、per instance vs total 全部可见。
- JSON/CSV/曲线与 BOM/Overview 按现有产物机制输出到当前 run；T-type 两角色、12 位置、3 电感、2 银行与 package count、scope/excluded、固定硬件身份、有效/失败点保留。完整导出不是只导 L/C 摘要。
- 新字段更新 validator/字典及结构输出测试；历史 [迁移字段字典](../../migration/evidence/20260824/step10_structured_outputs/report_field_dictionary.md) 留 provenance，不手改冻结证据。本轮当前字段/证据建在明确位置；需要迁移证据更新时只用现有脚本生成独立 current evidence。
- 新增 `tests/test_t_type_engineering_step6_sweep_export.py`、`tests/test_t_type_engineering_step6_gui.py`：真实 Tk 按钮、同硬件扫点/负例、原 report totals 与 JSON/CSV/页面、默认/最小窗口及无旧文件冒充。
- 完成：全部必验点与缺项/失败行为、当前 GUI 数字及产物一致；第 7 节 sweep/report/gui 组＋累计测试，Git 回执完成。

### 步骤 7：最终回归、隔离与归档

- 汇总当前实际修改消费者，显式列出 cumulative T-type 和受影响旧拓扑全部节点；不能把前序计划清单遗漏解释为无影响。
- NPC↔T-type 双顺序并重复真实工程运行；独立 output roots/run IDs，原 report 不变、库对象/缓存/typed metadata 不串用、硬件/产物不串拓扑。比较当前 NPC 与步骤 0 的归一化工程基线，并核查变动原因/容差/字段，而非只比 totals。
- 实施公共模型、stage ordering、report schema 或无法界定依赖时完整 pytest；仅限定 adapter 时按消费者进行集成门禁并明确未跑范围，不默认每步 full suite。
- 新增 `tests/test_t_type_engineering_step7_acceptance.py`、`tests/test_t_type_engineering_step7_isolation.py`；实际数值、来源、失败与重复运行覆盖。最早真实库案例和最终 GUI/export 均保留当次环境/版本证据。
- 更新契约/README/本计划/ChangeLog，逐项说明本轮 deliverable 和继续暂缓项。必要 gate 全通过且各步推送后再归档；关闭本轮不声明死区/换流能量、全物理效率、硬件安全或可采购验收。

## 6. 必验矩阵、独立参考与容差

| 案例 | 输入或操作 | 必要结论 | 类型与计划归属 |
|---|---|---|---|
| E1 代表真实库 | 700 V/400 VLL/10 kW/50 Hz/20 kHz/PF1，首轮纹波目标 0.2 | 基波 14.433757 A RMS，主/中点 700/350 V；实际 L 后可调制；两器件角色/三磁件/两银行有效且 scope 一致 | real library，steps1–5/7 |
| E2 固定负载 | E1 硬件，0/0.1/0.5/1 | 硬件精确不变；当前 RMS/损耗独立变化；0 load eta 不可用 | real refresh，steps4/6 |
| E3 母线 | 同硬件 700/800 V | 主/中点阻断随当前母线；800 V 器件/银行额定检查；不重选；超额定明确 infeasible | real refresh＋controlled rating failure |
| E4 PF | 0.8/1；超前/滞后分别设计，各自固定硬件扫描 | 0.8 时目标基波 18.042196 A RMS；相位保持，current basis 不用 NPC 符号替代 | real pipeline，steps1/4/6 |
| E5 必验组合 | bus={700,800}×load={0.1,0.5,1}×PF={0.8,1}，超前/滞后设计族 | 每设计族 12 点，PF1 两族等价核对；每族内部固定硬件；每点调制/额定与组件完整性单独判定 | real sweep，step6/7；不能用设计 metadata 代替实际刷新 |
| E6 不可达 | 当前 500 V/400 VLL 或受控饱和，随后恢复 | 清当前波形/损耗/效率/导出；保留硬件，恢复同硬件正确结果 | controlled GUI/refresh failure |
| E7 搜索 | 无有效器件、磁件 allow 初筛失败/扩展/耗尽、电容 S/P 上限 | 明确原因、原 search policy 与审计；不改库/排序/限制凑成功 | controlled negative＋真实库接受分开 |
| E8 物理计数 | 两并联；共享 module sections；删除一相/一银行/一角色 | 无包装/位置重计；缺实例禁止系统总量/体积 | contract/system tests |
| E9 数值与来源 | NaN/Inf、负损耗、错时间轴、旧 run/basis/scope、电荷漂移 | 明确字段/原因；无 fallback/假零/假完整结果 | negative tests |
| E10 用户/导出 | 选卡→Run Design→组件选择→连续刷新→扫描→导出 | 当前 report、页面、JSON/CSV/曲线同硬件同工况同 scope；变化清旧结果 | real Tk + export |
| E11 隔离 | NPC→T-type→NPC；反向重复 | 旧工程基线、对象与工件独立；同模型计算可重复 | 独立真实运行，step7 |

700/800 V、PF0.8 的组合不保证相同额定器件天然覆盖；步骤 0 冻结的设计 envelope 应覆盖目标验证范围，所有点仍须实际校核。若有效 envelope 找不到硬件，应报告具体选型约束，不更改标称库记录；不把不可用结果当 E1 成功。

公式证据使用独立三相功率方程、电路 KCL、分段电荷积分、解析 R*I²、独立库曲线积分、串并联 C/ESR、热阻网络及数量手算；NPC/T-type 共 helper 一致只证明一致性。契约证据检查 role/identity/单位/缺项/搜索；用户证据为真实当前数字/产物；隔离证据为双顺序独立运行。

新公式标量 SI 比较初始门槛为相对 1e-6、零附近绝对 1e-9（A/V/W/H/F 各按物理量另记录适用值）；独立积分的数值量先进行加密收敛，目标相对 1e-4，并记录实际误差及分段精度，不能用全局 abs 容差覆盖量纲。系统加和/效率计算相对 1e-9、绝对 1e-8 W / 1e-12 ratio；银行 KCL 绝对 1e-8 A。身份/数量精确比较；GUI 按实际显示位数，结构值不得先四舍五入；旧 NPC baseline 优先精确，浮点差异要有依据。步骤 0 按 engine 近似和独立参考进一步冻结每字段门槛，修改必须给根因，不能事后放宽凑通过。

## 7. 验证入口、成本与回归范围

本次仅文档审查，不运行电气链。以下为未来实施命令/清单；新增 step0–7 文件当前不存在，只有实际创建并审查后才能执行，不将收集当执行。

实施前在仓库根设置当前 `src` 和仓库根的 PYTHONPATH，预检 `sys.executable`/版本、`pe_claw_gui.__file__`、pytest 与显式测试位置。示例（实际 argv 和路径写当步回执）：

```powershell
$ttEngineeringRoot = (Get-Location).Path
$env:PYTHONPATH = (Join-Path $ttEngineeringRoot 'src') + ';' + $ttEngineeringRoot
python -B -c "import sys, pe_claw_gui; print(sys.executable); print(sys.version); print(pe_claw_gui.__file__)"
python -B -m pytest -q --basetemp .pytest-tmp-tt-r2-s1 tests/test_t_type_engineering_step1_devices.py
```

每步用新建且专属的 basetemp/输出根，不用用户 outputs 或复用旧证据目录。可扩展已有 `validate_t_type_step8_acceptance.py` 的环境/回执机制为新 `scripts/validate_t_type_engineering.py`（待建），保存 source/test SHA、dirty state、argv、JUnit/log、模型 basis、数值 readback、候选/搜索/库 provenance。该工具必须有本轮显式清单，不能直接沿用首轮 zero-downstream gate，也不能将现有两相 PFC validation 入口当作已支持 T-type。

| 验证组 | 已存在的显式回归文件 | 使用阶段/范围 |
|---|---|---|
| 基础 T-type | `test_t_type_step1_contract.py`、`test_t_type_step2_synthesis.py`、`test_t_type_step3_waveforms.py`、`test_t_type_common_solver.py`、`test_t_type_step4_paths_events.py`、`test_t_type_step5_pipeline.py`、`test_t_type_step6_gui.py`、`test_t_type_step7_operating_point.py`、`test_t_type_step8_acceptance.py`、`test_t_type_step8_isolation.py` | 每步按影响累计；首轮“不接下游”断言仅在已开放阶段改为新能力契约，仍保留未开放阻塞，不删除其负例 |
| NPC 电气基线 | `test_dc_ac_three_phase_three_level_npc_contract.py`、`test_npc_step2_current_reference.py`、`test_npc_step3_average_voltage_target.py`、`test_npc_step4_level_sequence.py`、`test_npc_step4_periodic_warm_start.py`、`test_npc_step5_event_segmented_current.py` | step0、共享 waveform/adapter 改动与终验；六快照仅基础范围，另保留真实工程 baseline |
| devices | `test_semiconductor_registry_structure.py`、`test_semiconductor_package_library.py`、`test_device_selector_single_candidate.py`、`test_device_selector_rejects_overstress.py`、`test_npc_loss_model_step5.py`、`test_npc_loss_consistency_step1.py`、`test_npc_switching_loss_events.py`、`test_two_phase_interleaved_boost_pfc_step5_devices.py` | step1/5；NPC energy 回归证明未改变旧行为，不把其能量结果计为 T-type 验收 |
| magnetics | `test_default_packaged_normalized_magnetic_backend.py`、`test_magnetic_library_schema.py`、`test_magnetic_loss_contract.py`、`test_npc_inductor_filter_step8.py`、`test_two_phase_interleaved_boost_pfc_step6_magnetics.py` | step2/4/5；改变公共磁件公式/请求需追加实际所有消费者 |
| capacitors | `test_capacitor_registry.py`、`test_capacitor_selection.py`、`test_npc_split_link_capacitor_step7.py`、`test_npc_capacitor_pf_view.py` | step3/4/6；公共选择器变更追加 AC-DC/LLC/全桥/两电平对应案例 |
| thermal/system | `test_npc_thermal_design_step6.py`、`test_npc_system_validation_step9.py`、`test_llc_hardware_overview_step6.py`、`test_llc_thermal_display_step3.py` | step5/7；物理热/geometry 引擎改变追加所属家族；NPC step9 proxy 矩阵不代替 T-type 实际运行点 |
| routing/refresh/GUI | `test_phase4_topology_contracts.py`、`test_phase9_dc_ac_topologies.py`、`test_phase9_operating_point_migration.py`、`test_phase10_gui_integration.py`、`test_phase12_verification.py` | 能力/表单/full/refresh 改动；实际 nodes 在步骤0核实冻结；改变共享 controller/full 补旧 AC-DC GUI 完整链 |
| sweep/report | `test_npc_efficiency_performance_baseline.py`、`test_ac_dc_efficiency_sweep.py`、`test_two_phase_interleaved_boost_pfc_step8_efficiency.py`、`test_phase10_structured_output.py`、`test_phase11_structured_comparison.py` | step6/7；schema/总量共享接口涉及旧 DC-AC/AC-DC/LLC/PSFB/Flyback，按消费者补齐，不以这张最小清单替代 |

命令模板：`python -B -m pytest -q --basetemp .pytest-tmp-tt-r2-<step>-<group> <本步新增显式文件> <表中适用显式 tests/... 文件/节点>`。每次实际展开 argv 写入回执，不运行宽泛 glob；终验 union 去重后核查无遗漏。广泛共享/无法界定影响或最终 full gate 使用 `python -m pytest -q --basetemp .pytest-tmp-full`，确保该临时目录无用户数据并记录环境与适用范围。

昂贵真实磁件搜索串行执行，允许同一已验证设计复用给同硬件数值/页面读回；隔离测试必须独立运行。性能优化不减少库、search 上限或测试案例。旧 warning、skips、xfail、environment errors 与 passed 分开；必要 gate skipped/unexecuted/failed 不算通过。历史 426 项不累加成新 gate 结果。

## 8. 执行回执与完成清单

每步追加：`授权范围/分类 → 源码版本与环境 → 实际变更/字段/消费者 → 精确 argv → exit/通过/失败/errors/skips/xfail/耗时 → 公式/契约/用户链/隔离证据 → 数值/库/产物路径 → 未验证/失败根因 → implementation commit → push/远端核实 → 状态记录提交`。

| 完成门槛 | 当前状态 |
|---|---|
| 步骤0–7 全部必要验证、独立提交推送 | 待实施 |
| 真实库两角色、三相磁件、两银行、选后闭环 | 待实施 |
| 同 scope/basis 的本轮损耗、热、几何、固定硬件扫描 | 待实施 |
| 当前 GUI/report/JSON/CSV/BOM/overview 数值、来源与身份 | 待实施 |
| 独立公式、producer/consumer、真实工作流、双顺序隔离 | 待实施 |
| NPC baseline 与所有受影响旧消费者 gate，无遗漏或隐藏失败 | 待实施 |
| 文档/ChangeLog、diff 检查、无生成物暂存、Git 回执 | 仅本次文档创建检查，实施回执待后续 |

完成声明限定本轮工程链与损耗范围；完整物理效率、有限死区/换流能量、不平衡控制、采购/装配/硬件验收继续未验证。范围内 gate 失败不归档；后续范围不会因未做而自动阻塞本轮。完成时移动到 `Plan/completed/` 并复核链接，第一轮归档保持原样。

## 9. 本次计划撰写回执

- 2026-10-13：只新增本计划并向 ChangeLog 追加；未改生产代码、库、测试或首轮契约/计划，步骤0–7均待实施。
- 依据实际 NPC/T-type roles、selector callback、capability、full stage order、KCL 契约及旧测试文件建立方法；24 个本地链接和 47 个既有测试文件引用检查通过，ChangeLog 原有字节保持前缀、仅追加。语义审查覆盖暂缓能量、KCL 方向、逐位置数量、选后闭环和 scope 完整性；`git -c core.longpaths=true diff --check` 通过。普通全差异命令曾遇历史长路径，改用单次 longpaths 参数后检查完成，不修改仓库配置或历史文件。
- 本次文档无电气行为改变，不运行 pytest/真实设计，不宣称第二轮验证通过；初始用户文件/95项删除/outputs/证据保留。
- 文档提交使用上述特性分支并推送已核实上游；最终 SHA 与远端确认以本次完成报告和 Git 历史为准，本节不提前填写实施通过或推送成功。

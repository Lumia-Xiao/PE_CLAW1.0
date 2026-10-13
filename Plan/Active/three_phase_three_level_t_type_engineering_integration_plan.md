# 三相三电平 T-type 第二轮工程链接入计划

- 状态：Active / 步骤 0–1 的原合同实现已推送，历史回执保留；新增 NPC 输入/半导体一致性纠偏前置，尚未适配验收；步骤 2–7 待实施。
- 创建日期：2026-10-13。
- 当前授权：先冻结与 NPC 完全一致的用户输入及半导体选择合同，再调整 T-type 后台，随后继续工程链。本次执行文档冻结与计划纠偏，生产代码留待下一步；仅关注 T-type 验证，死区及换流能量仍排除。
- 拓扑 ID：`three_phase_three_level_t_type_inverter`。
- 工作区：`C:\Users\Lumia\OneDrive - Nanyang Technological University\PE-Claw1.1\PE_Claw_1.1_260928`。
- 撰写基准：`622920211ffa1185799365d0f4d1f50e0119a521`；分支 `codex/llc-waveform-operating-point-plan`。
- 已核实上游及文档推送目标：`pe-claw-1.1/codex/llc-waveform-operating-point-plan`；远端 `https://github.com/Lumia-Xiao/PE-Claw_1.1.git`。不推送 origin 或 master。
- 初始状态：95 项既有无关 tracked 删除及既有 untracked 用户文件、outputs、测试证据；暂存区为空。保留全部，不恢复、不删除、不纳入提交。

## 1. 依据、现状与交付目标

依据：[仓库规则](../../AGENTS.md)、[工程语义契约](../../docs/engineering_contracts.md)、[T-type 电路契约](../../docs/three_phase_three_level_t_type_contract.md) 第 2–5、9–11、14 节、[拓扑计划模板](../templates/topology_change_plan_template.md)、[第一轮已完成计划](../completed/three_phase_three_level_t_type_implementation_plan.md) 第 2.2、9.14 节。

第一轮已经实现独立拓扑、参数合成、三相事件积分、12 门极、方向路径、逐位置应力、GUI 和固定 candidate 参数刷新。首轮 426 个不同测试项及 NPC 六份完整快照回执是历史证据，不能代替第二轮当前版本的工程验收。第一轮归档保持原范围和历史回执。

计划创建时 T-type 属于 `FIRST_PASS_TOPOLOGY_ONLY_IDS`，全部工程入口被保护。步骤1接入两角色真实选型和封装参考后，按逐阶段capability继续保护两银行/磁件/当前系统损耗热几何/扫描；完整工程导出仍待后续步骤。

第二轮交付顺序：

```text
NPC 一致用户输入及半导体选择合同冻结
→ T-type 用户字段/后台/两角色选择纠偏与验收
→ 半导体两角色选型
→ 每相电感与上/下母线电容银行
→ 选定硬件回读、当前工况刷新与失效管理
→ 本轮范围内损耗、热、几何
→ 固定硬件扫描、当前 GUI 与完整工程报告/导出
```

采用 NPC 已有工程库、数值模型、筛选/排序、搜索扩展和产物机制。T-type 负责正确的电路数据和类型化适配；不创建另一套元器件数据库，也不复制 NPC 的固定型号、磁芯、温度、参考损耗或中点平衡结论。

最新权威要求见 [T-type 契约第 17 节](../../docs/three_phase_three_level_t_type_contract.md)和本计划第 12 节。其覆盖本计划旧的独立 engineering 输入、ROHM/IGBT 限定、无条件 n=1/2/3、24 点默认设计包络及超前/滞后 GUI 方案；这些旧设计与第 10–11 节执行证据保留为历史，不能据此继续步骤 2。后续验收矩阵按第 12 节重定，不能将旧 E3/E5 强行转换为用户的新默认设计范围。

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
| 0 | 冻结二轮接口、范围、基线和阶段开放方案 | 本计划 | 已完成，见第 10 节 |
| 1 | 半导体两角色真实库选型 | 0 | 原合同已推送，见11.2–11.3；新一致性要求需先纠偏 |
| 前置纠偏 | NPC 输入/选择合同及 T-type 后台适配 | 0–1 历史实现 | 合同本次冻结；适配/新验收待实施，见12 |
| 2 | 三相电感接入 | 1、前置纠偏验收 | 待实施 |
| 3 | 上/下银行电流与真实电容选型 | 0、2 | 待实施 |
| 4 | 选定硬件回读、固定硬件刷新与全链来源校验 | 1–3 | 待实施 |
| 5 | 本轮损耗、热、几何及最早真实工程贯通 | 4 | 待实施 |
| 6 | 固定硬件扫描、完整工程 GUI/报告/导出 | 5 | 待实施 |
| 7 | 二轮完整验收、旧消费者回归、隔离与归档 | 6 | 待实施 |

各步实施前写明本步影响与精确验证清单；必要验证通过、ChangeLog 追加、diff 检查、独立 commit/push 并核实远端后才能标完成。本次只执行第 12.1 节文档冻结，不触发后续生产实施。

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

步骤 0 已建立 `tests/test_t_type_engineering_step0_contract.py` 和 `scripts/validate_t_type_engineering_step0.py`，当前执行记录见第 10 节。步骤 1–7 新增测试仍待创建；以下为分步命令/清单，只有实际创建并审查后才能执行，不将收集当执行。

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
| 步骤0–7 全部必要验证、独立提交推送 | 步骤0–1完成（步骤1限T-type）；步骤2–7待实施，全面回归仍后续 |
| 真实库两角色、三相磁件、两银行、选后闭环 | 待实施 |
| 同 scope/basis 的本轮损耗、热、几何、固定硬件扫描 | 待实施 |
| 当前 GUI/report/JSON/CSV/BOM/overview 数值、来源与身份 | 待实施 |
| 独立公式、producer/consumer、真实工作流、双顺序隔离 | 待实施 |
| NPC baseline 与所有受影响旧消费者 gate，无遗漏或隐藏失败 | 待实施 |
| 文档/ChangeLog、diff 检查、无生成物暂存、Git 回执 | 步骤0已核实；后续步骤待实施 |

完成声明限定本轮工程链与损耗范围；完整物理效率、有限死区/换流能量、不平衡控制、采购/装配/硬件验收继续未验证。范围内 gate 失败不归档；后续范围不会因未做而自动阻塞本轮。完成时移动到 `Plan/completed/` 并复核链接，第一轮归档保持原样。

## 9. 本次计划撰写回执

- 2026-10-13：只新增本计划并向 ChangeLog 追加；未改生产代码、库、测试或首轮契约/计划，步骤0–7均待实施。
- 依据实际 NPC/T-type roles、selector callback、capability、full stage order、KCL 契约及旧测试文件建立方法；24 个本地链接和 47 个既有测试文件引用检查通过，ChangeLog 原有字节保持前缀、仅追加。语义审查覆盖暂缓能量、KCL 方向、逐位置数量、选后闭环和 scope 完整性；`git -c core.longpaths=true diff --check` 通过。普通全差异命令曾遇历史长路径，改用单次 longpaths 参数后检查完成，不修改仓库配置或历史文件。
- 本次文档无电气行为改变，不运行 pytest/真实设计，不宣称第二轮验证通过；初始用户文件/95项删除/outputs/证据保留。
- 文档提交使用上述特性分支并推送已核实上游；最终 SHA 与远端确认以本次完成报告和 Git 历史为准，本节不提前填写实施通过或推送成功。

## 10. 第二轮步骤 0 执行回执（2026-10-13）

### 10.1 授权、分类与冻结内容

- 授权仅执行步骤 0；分类为文档/测试工具变更。新增验证工具和接口探针，扩充 T-type 契约第 15 节、更新本计划与 ChangeLog；未修改生产模型、角色注册、公共 dataclass、库记录、筛选政策或实际 capability。旧生产消费者仍使用原合同，其他 AC-DC/DC-DC 完整链不在本次验证范围。
- [契约第 15 节](../../docs/three_phase_three_level_t_type_contract.md#15-第二轮步骤-0-冻结的工程接口2026-10-13) 冻结精确的拟新增类型/字段、adapter 请求、producer/consumer、单位/统计/实例计数、缺项/失效策略、阶段能力和数值容差。首个真实路径为注册库带 FRD 的 ROHM RG 离散 IGBT；模块终端组合未经验证不能视为可用。
- 本轮范围 ID 为 `t_type_conduction_magnetics_capacitors_v1`，导通/三相磁件/上下银行损耗纳入；死区、开关/恢复能量等排除项按 not_modeled 标注。selector 使用现有 callback 读取导通曲线，禁止默认整套能量评价；逐位置实际损耗不能用组包络乘位置数替代。
- 设计 candidate 保留原 L/C 目标，实际硬件进入拟建 typed snapshot/effective 参数视图；三个相实例、两银行、12 位置与采购封装分别计数。stage0 保留全部工程入口保护，steps1–6 逐项开放；步骤 1 尚未实施。

### 10.2 环境与本次证据

- 基准 HEAD `3bab9d13b08243ebf12764799032f08c031476c6`，当前 Python 3.12.10、工作区 src 和显式 tests；每次 preflight 保存解释器路径、package 路径、分支/dirty status、src/tests/scripts/docs SHA。95 项既有 tracked 删除、用户 outputs、既有证据均保留。
- 工具 [validate_t_type_engineering_step0.py](../../scripts/validate_t_type_engineering_step0.py) 为当前运行建立独立输出根，保存完整原始/归一化 report、structured、overview 和库清单。只删除显式 timing/run-ID 键、替换当前精确 run root；NaN/Inf 保留标签，工程字段、硬件、警告、来源不隐藏。快照用于后续旧行为比较，不能替代物理正确性证明。
- 聚焦命令：`python -B scripts/validate_t_type_engineering_step0.py .tt-r2-s0-focus tests/test_t_type_engineering_step0_contract.py`。13 passed、0 failures/errors/skips，128.21 s；现有 cache_dir 配置 warning 1。路径 `.tt-r2-s0-focus/{preflight.json,test_receipt.json,junit.xml,pytest.log}`。
- 方向表 6 个独立正负电流例、真实 IGBT 导通表调用且禁止能量接口、selector callback 路由与电压/热受控拒绝、非有限保留探针通过。callback 的热/损耗数值是受控 fixture，不是 T-type 真实器件选型。
- 两个实际 waveform 测试各生成 bus={700,800}×load={0.1,0.5,1}×PF={0.8,1} 的 12 点，超前/滞后共 24 点；同一 PF1 设计 L=1.0716517624676405 mH，candidate 不变，12 位置静态耐压及实际命令可调制性通过。`temp/**/envelope.json` 保存原指标；不是实物 L 选后范围验收。

### 10.3 当前旧拓扑权威基线

- 命令：`python -B scripts/validate_t_type_engineering_step0.py .tt-r2-s0-baseline-fixed --baseline-only`，exit 0，409.42 s。权威索引 `.tt-r2-s0-baseline-fixed/baseline_manifest.json`，环境/SHA 在 `preflight.json`，最终回执在 `completion.json`。生成物仅本地保留，不暂存。
- NPC 六份当前完整电气 payload 与历史源 SHA 精确一致。另以当前真实注册库运行 NPC 完整器件/磁件/上下银行及 0.5/1.0 固定硬件扫描；必需损耗有限且非负，原发布 total 等于三类损耗之和，eta 等于 Pout/(Pout+total)，按冻结 W/ratio 容差验证。三个报告的 structured schema_errors=[]。
- 器件读回：NPC outer/inner=`CAB011M12FM3`、clamp=`SCS320KN`；旧两电平=`SCT4018KR`；旧全桥=`SCT4045DLL`。后两组为默认输入的器件链，未启用其磁件/电容，不能宣称完整系统验收。
- 归一化 SHA：NPC `912f3be557c22631b50ab3fafce35a09f08c7e94b428cc022f113d2214489739`；两电平 `4b60d4e2bd9663df925c502b24310f80a99b41312d91e0700b8294bec5655708`；全桥 `30d08447d1bea628ee434351e70369c7a87f897cc7ad497c0a7268b57920e074`。原始快照与字节数见 manifest；不删巨型报告以缩减证据。
- 基线保存旧状态原值：NPC 调用扫描后 stage_status 仍为 not_started，两电平可有选中器件而状态仍为 not_started。这些字段不用于替代本次组件/数值检查，本步不修旧生产状态。未来 step4/6 来源与状态完善须分别审查。
- 首次 `.tt-r2-s0-baseline` 已完成 NPC 部分，随后因工具给两电平传空输入缺少 vdc_nom 失败；保留 baseline_failure.json 和所有已生成证据。修正为插件现有 build_default_inputs 后在新目录重跑全部三组，不改生产代码或门槛。

### 10.4 验证边界与 Git

当前新增生产公式、物理系统总量、T-type 真实硬件选择均不适用本步骤；用户工作流/隔离以当前首轮基本链回归为限，真实工程 GUI/export 仍属后续步骤。本次不运行 full suite、完整旧家族矩阵或 NPC step9 proxy 验收；不宣称模型边界外物理精度/采购/硬件验收，不以历史 426 项替代。

- 主组命令：`python -B scripts/validate_t_type_engineering_step0.py .tt-r2-s0-gate`，pytest 部分 241 passed，1114.14 s；测试 exit 0。进程在修正前已加载工具，后续基线仍因空输入失败（整个命令 exit 1），保留 `.tt-r2-s0-gate/baseline_failure.json`；不能宣称这条整命令成功。权威基线采用 10.3 的修正后独立运行。
- 补充基础组命令：`python -B scripts/validate_t_type_engineering_step0.py .tt-r2-s0-basic-rest tests/test_t_type_step6_gui.py tests/test_t_type_step7_operating_point.py tests/test_t_type_step8_acceptance.py tests/test_t_type_step8_isolation.py`，exit 0，44 passed，947.93 s。覆盖真实基础 Tk/当前报告读回、不可达后恢复、固定 candidate 刷新与 NPC/T-type 双顺序重复隔离。
- 两组各 0 failures/errors/skips，仅既有 cache_dir warning；JUnit 核对 241+44=285 个不同测试项，src/tests SHA 一致，节点文件集合覆盖工具最终显式清单。聚焦 13 项不重复计入 285。`.tt-r2-s0-baseline-fixed/aggregate_validation.json` 保存核对结果；不是一次全量 pytest。
- 两个 Python 文件 AST 检查、40 个本地文档链接检查、ChangeLog 原文前缀（保留工作区 CRLF）和 `git -c core.longpaths=true diff --check` 通过。步骤 0 验证完成，Git 提交推送待回执；仅提交五个任务文件，运行证据/outputs/95 项既有删除不暂存。

- Git 完成回执：实现/契约/工具/测试/日志提交 `9d8284f44df212af8525179a8e2a72c7cb9d7c81` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，`git ls-remote` 核实远端同 SHA。步骤 0 必需验证及推送门槛已完成；本条状态回执另作文档提交并推送，最终回执提交以 Git 历史为准。后续步骤保持待实施，不重复运行未变的电气测试。

## 11. 步骤 1 影响与执行记录（T-type授权范围完成）

- 用户授权步骤1；基准 `896ff1d871fdfc1bdb990b93a92aa7b2bad4fb39`，分支/远端沿用步骤0；95项既有 tracked 删除和用户输出保留。
- 分类：共享集成。角色图/capability、可选 DesignReport typed 字段、full/refresh/controller/GUI/schema 消费者受影响。新增 T-type adapter、导通 engine 和选型 stage；旧模型/库/selector/ranking 公式不改。旧拓扑 stage 返回原路径；旧 report 新 optional None 字段属于明确兼容结构差异，旧 structured 不新增 engineering_result。
- 字段含义/单位/设计与运行依据/数量/缺项/失效见 [当前字段字典](../../docs/t_type_engineering_field_dictionary.md) 和契约第15节；步骤1只发布器件/离散封装与设计包络参考，完整 hardware/system 字段留后续实现。不将包络参考×6当当前损耗。每角色6n位置设备、12n采购封装，FRD无新增clamp。
- 最小真实路径采用 ROHM RG IGBT+FRD，二维导通表范围明确检查；曲线按 target Tj 计算，组合功耗和 max(IGBT/FRD Rth_jc)进行保守TIM/sink反求，thermal feasible是选型参考非共享散热器验收。保留公共额定/热过滤和评分及优先最少并联完整可行方案；本拓扑按步骤0约定显式比较1/2/3并联，旧公共IGBT单方案策略保持不改。
- 默认 envelope 700/800×0.1/0.5/1×0.8/1，每phase实际12点；省略工程包络输入时纳入首轮设计母线/PF，显式边界不包含设计点则拒绝，不改变首轮电路公式。用户自定义范围仍按实际可调制性检查。
- 先执行 `python -B -m pytest -o addopts= -p no:cacheprovider -q --basetemp .pytest-tmp-tt-r2-s1-focus --junitxml .tt-r2-s1-focus.xml tests/test_t_type_engineering_step1_devices.py`；后执行显式累计T-type、devices组、registry/forms/structured/controller及旧DC-AC/PFC/LLC消费者。独立公式：仿射曲线解析、库标量查表、8/16点加密；契约：范围/峰值/缺FRD/NaN/额定负例；用户链：实际Tk按钮/当前报告数值；隔离：双顺序重复和当前NPC旧基线。
- 公共模型和报告增加optional合同，schema/报告消费者必须广泛回归；stage guard只针对T-type，旧families返回原值，不通过削弱旧断言处理失败。最终测试命令/环境/SHA/结果及Git收据实际执行后追加；本节不提前声明完成。

### 11.1 剩余失败修复与验证范围

- 用户授权：解决步骤1剩余失败，补齐回执并提交推送；不实施步骤2。此前完成说法早于必要门禁，本节以实际结果纠正，不复用失败命令作为通过回执。
- GUI 根因：开放 device 后，`EfficiencyView.render` 仍用 first-pass 集合判断，误显示可运行扫描。改用 `supports_engineering_stage(topology_id, "sweep")`；T-type 显示明确 unavailable，旧拓扑能力返回原值。受影响消费者为效率页、当前 GUI 读回和旧 AC-DC 完整效率页面，追加真实 GUI 验证。系统损耗、效率、磁件/电容、散热器与固定硬件扫描尚未开放。
- 旧注册断言须冻结为实际 21 项及 DC-AC 四项；旧三拓扑完整链仍独立验证。低母线边界案例显式指定工程母线下界，保留原可调制性失败断言，避免新输入包络验证抢先覆盖原物理边界。
- 测试工具只在专属输出目录复制 Git HEAD 中历史证据，保存来源提交/路径/SHA 并临时重定向测试的 PLAN/EVIDENCE；保留用户工作区删除，不修改历史文件、断言或生产路径。累计运行追加每项 setup/call/teardown 实时记录，失败历史保留。
- 当前环境误用系统 Temp 的一次运行为 18 passed/15 errors（WinError 5），单列环境错误；已改回工作区专属 basetemp。之前被中断的两个长期验证进程无完整回执，不计通过。最终所选节点覆盖、实际结果和源文件关联待收尾记录。
- 新真实选型执行12个设计包络工况，最新聚焦完整设计 fixture 为241.648 s；首轮两项真实 GUI 子进程240 s预算不足，改为900 s等待上限，全部电气、当前页面数字、来源、失效及恢复断言保留。此改动是测试执行预算扩展，不是放宽工程容差或减少搜索。追加 gui_repair 显式6项和 gui_consumers 显式3文件，重跑失败节点并保存新源码回执。
- 用户最新收窄：“现在就只关注T-Type变换器，不需要对其他拓扑做测试”。已停止旧 GUI 消费者及混合累计运行，保留日志且不计完整通过。最终门禁改用 `python -B scripts/validate_t_type_engineering_step1.py .tt-r2-s1-t-type-final t_type`：只选T-type文件及纯T-type重复刷新隔离节点，显式不选NPC电气/双拓扑隔离节点；注册与切换清理仍是T-type接入契约。其他拓扑回归、跨拓扑隔离和full suite保留后续，不声称本次全面兼容验收。原已执行旧基线/测试仅作历史记录，不扩展本次结论。
- 专属累计发现最小窗口可达性失败。尺寸诊断表明1240×760可视高693 px，顶部Run Design位于y=668、高31，越界6 px；底部波形/扫描按钮滚动后可达。只在T-type表单将设计输入行pady从6缩为4，保留公共表单及原窗口/可达性断言。此修复为GUI布局，不改变工程数据或计算；追加当前布局重跑和真实GUI读回，原失败保留。

### 11.2 步骤 1 实际验证回执

- 环境：Python 3.12.10，`C:\Users\Lumia\AppData\Local\Programs\Python\Python312\python.exe`；实际包为当前工作区`src/pe_claw_gui/__init__.py`，测试来自当前`tests/`，基准HEAD `896ff1d871fdfc1bdb990b93a92aa7b2bad4fb39`＋本步工作区源码。各脚本preflight/test_receipt保存解释器、精确pytest argv和src/scripts/tests逐文件SHA；输出、basetemp均在本步专属目录。
- 累计命令：`python -B scripts/validate_t_type_engineering_step1.py .tt-r2-s1-t-type-final t_type`，285 passed/1 failed/0 errors/skips，2227.42 s，exit1；2 deselected为明确排除的NPC执行节点，不算通过。唯一失败为修复前的最小窗口Run Design越界。GUI修复命令：`python -B scripts/validate_t_type_engineering_step1.py .tt-r2-s1-gui-repair-final gui_repair`，6 passed/0 failures/errors/skips，830.95 s，exit0。两组各1条既有Unknown config option: cache_dir警告，单列非工程失败。
- `.tt-r2-s1-t-type-final/aggregate_validation.json`核验286个不同所选节点全部有实际通过记录，修复组覆盖原失败；不是一次全通过suite。累计开始后唯一代码变化为T-type表单pady，修复组preflight的src/tests/scripts与最终源码全部相同，原公式/契约/全部运行点通过证据保持适用。聚焦最新30 passed/328.026 s和布局独立1 passed/15.89 s另列，不重复累加。
- 真实库案例：默认10 kW/400 VLL/50 Hz/20 kHz，固定L=1.0716517624676405 mH，700/800 V×0.1/0.5/1×PF0.8/1；main=`RGHX5TRX2DF`、midpoint=`RGWX5TS65EHR`，n=1，共12离散IGBT＋FRD封装。选型channel/diode参考分别6.497900187793574/0.2021854536400135 W（700 V/满载/PF0.8，b_QP）与4.061070808431853/3.7695404600459197 W（800 V/满载/PF0.8，c_QA）；属于最坏单封装参考，不是角色/当前/系统损耗。
- 四类证据：公式为独立仿射积分、8/16点加密、库标量查表和实际分段独立adaptive积分（rel1e-4/abs1e-6 W）、热阻解析；契约为角色/位置/12n封装、零能量接口调用、曲线范围/额定/NaN/缺FRD、无完整可行方案不发布及direct-stage保护；用户链为真实Tk按钮→当前report的型号、数字、全部曲线、连续刷新、清理恢复和bounded导出；隔离为纯T-type重复刷新数组独立、旧报告不变及来源拒绝。对应源测试为step1_devices、step5_pipeline、step6_gui、step7_operating_point、step8_acceptance和选定step8_isolation节点。
- 数值读回：`.tt-r2-s1-t-type-final/temp/test_real_two_role_selection_a0/selection_readback.json`；最终GUI的readback/PNG在`.tt-r2-s1-gui-repair-final/temp/`各测试目录。schema与typed选择证据通过，但当前系统损耗/效率、完整硬件快照及完整工程导出不可用，不假定组件小计或空损耗为系统结果。
- 历史失败/未执行：系统Temp WinError5及一次布局重跑缺PYTHONPATH收集错误分别保留，不计电气通过；所有中断的混合/旧GUI进程无完整回执。用户收窄前旧consumer为80 passed/1旧注册失败、shared34 passed及旧baseline工程差异0，仅记录历史，不纳入286，不宣称最终全面兼容。其他拓扑完整回归、跨拓扑隔离、full suite、步骤2–7、死区/换流能量、实物采购/硬件验收未执行。
- 审查与Git：42本地链接、任务Python AST、定向及暂存diff检查通过；仅明确任务文件暂存，95项既有删除和outputs/本地证据保持。实现提交/推送及远端核实待实际完成后追加；此时步骤1仍未标完成，无清理或备份操作。

### 11.3 步骤 1 Git 与状态回执

- 实现提交 `facd572740aebdf9411d708aebb4e8810d364e01`，44个明确任务文件；已执行`git push pe-claw-1.1 codex/llc-waveform-operating-point-plan`并以`git ls-remote pe-claw-1.1 refs/heads/codex/llc-waveform-operating-point-plan`核实同SHA。
- 步骤1在用户指定的T-type范围内完成：真实两角色选型、范围与数量合同、明确未接阶段、最终GUI失败修复及286个不同通过项成立。其他拓扑全面回归/跨拓扑隔离仍后续；不将本次收窄范围当全部旧拓扑兼容或发布验收。
- 本次后续文档提交只同步计划状态与ChangeLog Git回执，复用11.2有效电气证据；不改生产/测试，无需重复电气链。最终文档SHA及远端核实见Git历史和完成报告。步骤2–7待实施；下一步是步骤2三相电感接入。

## 12. NPC 输入与半导体选择一致性纠偏前置（2026-10-13）

第 11.3 节“下一步步骤2”是当时的历史结论；最新顺序以本节为准。用户首先要求输入内容和字段一致，随后明确半导体选择也一致。本次在基准 `d1ac433610d0d4af37b092d5ece2ba90dab9bf36` 只读核对实际 NPC 表单/schema/metadata/应力适配/方案政策，冻结[契约第 17 节](../../docs/three_phase_three_level_t_type_contract.md)。原步骤0/1回执不撤销，也不算新合同验收。

### 12.1 当前文档冻结范围

- 分类：文档；本次只改 T-type 契约、本计划、字段字典与 ChangeLog，生产 Python/GUI/报告 schema、工程库、公式、证据均不改。
- 交付：NPC 精确 12 个设计字段＋2 个运行字段、类型/厂家完整选项、唯一温度/筛选来源、负 PF 反向有功语义、额定设计点选型及公共并联政策；取消独立 engineering 用户字段。后续优先级覆盖旧 phase/24 点包络和 ROHM-only 默认方案。
- 验证：源码及语义交叉审阅，三个合同/计划文档共53个本地引用存在性检查通过，原文日志只追加核验通过；定向及暂存 `git diff --check`、差异及范围检查。不运行 pytest、GUI、电气设计或 NPC 测试；没有新工程通过结论。
- Git：沿用现分支与 `pe-claw-1.1` 同名上游，只定向提交四个文档；既有95项删除及生成物保留。实际 SHA、push/远端核实见本次完成报告及 Git 历史。提交推送核实前不称文档步骤完成。

### 12.2 后台适配实施顺序（待实施）

| 纠偏步 | 文件及交付 | 完成门槛 |
|---|---|---|
| A1 用户输入/归一化 | T-type form/input_schema、必要公共字段入口及 runtime overrides；复用公共字段构造和 metadata；删除 GUI 独立 phase/engineering/运行母线控件；明确旧 API 别名/冲突诊断 | key/label/default/order/choices 精确 12+2；运行母线取设计；公共温度和厂家实际到达消费者；未接阶段按钮禁用；不忽略输入 |
| A2 电路与工程依据 | T-type synthesis/waveform/engineering_adapter/models；有符号 PF 和反向基波目标；设计点选择 basis 替换默认24点包络；保留正确电路方向、静态阻断及原 L 公式 | 正/负/零 PF 独立物理/兼容边界证据；basis/当前点分开；不可调制与非法数据有根因；旧历史 basis 不重标 |
| A3 两角色选择 | topology_roles、T-type conduction engine/device pipeline、公共选择策略入口及 typed readback；公共库和过滤，复用 scheme variants/审计/用户方案选择；MOSFET/IGBT 和可连接封装适配 | Any及指定类型/厂家真实生效；IGBT只single，其余按公共1/2/3；两角色完整feasible；真实技术导通模型/终端连接可追溯；零能量调用 |
| A4 T-type 验收与回执 | 更新旧合同断言和 T-type 工具清单，增加新输入/筛选/方向/方案负例，真实 GUI/报告读回；每个实施步骤验证提交推送 | 仅T-type全相关工况实际运行，新合同验证和Git收据齐全；随后才恢复步骤2 |

A1–A3 是依赖顺序，可以按最小可验证变更分别提交；A1 的页面一致不能当 A2/A3 后台完成。若选择共有机制抽取 helper，保持其原策略，逐个记录其他消费者，按用户限定只运行 T-type，未测试旧消费者显式留作后续，不能声称全面兼容。

公共流程复用不能直接调用 NPC 全能量评价。MOSFET 通道/反向路径、IGBT/FRD、其他厂家曲线接口需由实际库模型提供，经独立导通参考与负例验证。当前 ROHM-only 路径可留为已验证分支，不能成为新的全局技术/厂家限制。模块必须证明终端连接与 section→位置映射；无兼容记录应报告耗尽/连接拒绝，不能复制型号或无条件放行。

### 12.3 新验收矩阵及命令准备

| 类别 | 必验内容 | 证据 |
|---|---|---|
| 输入合同 | 默认12设计＋2运行，与NPC静态字段定义比较；所有类型/厂家选项；load/PF裁剪回写；设计PF零、非法/非有限、旧别名冲突 | T-type schema/form测试与真实Tk页面；NPC仅读取定义，不跑其电气链 |
| 设计选择依据 | 默认700 V、400 VLL、10 kW、PF1、满载；另独立800 V设计；设计PF=0.8/−0.8在合法前置范围下各自设计 | 实际case数量/值/来源，独立三相功率与电流方向参考；不再默认枚举700/800固定硬件包络 |
| 公共筛选/方案 | Any；MOSFET；IGBT仅single；Diode无主动候选；指定厂家真实匹配与无匹配；1/2/3方案电流缩放及完整性 | 真实库IGBT/MOSFET各代表案例、受控无候选/曲线/连接拒绝；候选计数与ranking/audit，不以mock代替真实接受 |
| 运行及边界 | 当前load=0/0.1/0.5/1，PF=1/0.8/−0.8/0；固定硬件来源、刷新不重选、失败清理恢复 | 电路公式/积分依据和数值证据分开；可达点通过，不可达点根因明确；零PF兼容不能当物理接受 |
| GUI/报告/隔离 | 所选方案/厂家/温度/型号/数量来自当前report；设计参考不冒充当前功耗；两次独立设计及连续刷新 | 当前Tk数值/structured/typed一致、硬件ID及scope；T-type重复运行，其他拓扑和跨拓扑执行仍未验证 |

未来定向命令在更新断言/工具后执行，当前文档步不执行：

```powershell
python -B -m pytest -q --basetemp .pytest-tmp-tt-input-parity tests/test_t_type_step1_contract.py tests/test_t_type_step6_gui.py tests/test_t_type_engineering_step1_devices.py
```

累计验收需更新 `scripts/validate_t_type_engineering_step1.py` 的 t_type 清单和新负PF/筛选工况，再运行 T-type 全相关 schema/synthesis/waveform/stress/刷新/真实选型/GUI/报告/重复隔离。旧脚本通过不能代替新断言；不得直接以历史286项或旧超前/滞后24点认定一致。实际 argv/环境/current源码/库checksum/结果在实施回执记录，收集不算执行。

### 12.4 恢复原工程链的条件

前置纠偏通过并提交推送后，依次步骤2三相电感、步骤3上下银行、步骤4真实硬件回读、步骤5损耗热几何、步骤6扫描完整导出、步骤7收尾。所有阶段读取新公共字段和已冻结选择政策，不再引入独立用户输入。反向有功下的组件方向和效率口径应在相应步骤明确；旧正功率公式不自动适用。

死区/换流能量继续排除；其他拓扑测试继续按用户限定不执行。共享集成未验证消费者、技术模型缺口和系统尚未开放范围需保留，不因文档冻结宣称实现、全面回归或硬件验收完成。

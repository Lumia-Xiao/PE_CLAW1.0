# 两相交错 Boost PFC 拓扑新增计划

- **状态**：Active / 10G 复核及 10H 补齐限定门禁完成并已推送；10I 运行点一致性方案已冻结，尚未实施（全面发布验收仍单独保留）
- **目标拓扑 ID**：`single_phase_interleaved_boost_pfc_diode_bridge`
- **所属类别**：AC-DC
- **计划范围**：在现有单相二极管桥 Boost PFC 基础上，新增两相、180° 交错、单向、CCM 一阶工程设计拓扑。
- **当前阶段**：步骤 0–10、10A–10H 及本轮 10H 补齐已实施并推送，本轮 10G 复核通过；10I 仅完成方案冻结。既有验证范围按用户要求限定为全部两相专项及必要的单相 Boost PFC 双顺序隔离配对；80 个独立用例通过、无 skip，未运行全量测试或其他拓扑全面回归。

## 1. 计划目标和边界

本计划的目标是为 PE-Claw 1.1 增加一个独立的两相交错 Boost PFC 拓扑。该拓扑由单相二极管桥、两个并联 Boost 功率相、两个独立 Boost 电感、两个高频开关、两个 Boost 二极管和共同的 DC-link 电容组成。

首个实现版本固定以下边界：

1. 相数固定为 2，不把首版扩展成任意 `N` 相通用求解器。
2. 两相开关频率相同，理想相移固定为 180°。
3. 两相使用相同的设计目标并直接采用理想均流假设，设计电流固定按总电流的一半分配；本计划不设计仿真或闭环均流控制器。
4. 采用与现有单相 Boost PFC 相同的一阶平均电流、半线路周期采样和 CCM 设计边界。
5. 设计点执行器件、电感和电容选择；运行点刷新和效率扫描复用已选硬件，不在每个负载点重新选择硬件。
6. 线路零点换相、THD、EMI 滤波器、数字控制环路、DCM/CrM 和详细寄生参数不属于首版验收范围，但必须在结果中作为明确边界记录。

首版不能采用以下简化：

- 不能把单相总电流直接复制到两相；
- 不能只把现有 Boost PFC 的电感电流和损耗乘以 2；
- 不能用一个未定义语义的 `inductor_current_a` 同时表示单相总电流、单相电流和两相电流；
- 不能用一个 `main_switch` 或 `rectifier_diode` 结果掩盖两个相位的独立器件应力；
- 不能为了接入新拓扑而改变现有单相 Boost PFC 的公式、字段含义或选择策略。

## 2. 现有基础从哪里来

### 2.1 拓扑插件和公共运行路径

现有单相 Boost PFC 拓扑位于：

```text
src/pe_claw_gui/topologies/ac_dc/single_phase_boost_pfc_diode_bridge/
```

其插件遵循公共接口：

```text
build_spec()
    -> synthesize()
    -> generate_waveforms()
    -> extract_stress()
    -> evaluate()
    -> build_report()
```

公共接口定义在 `src/pe_claw_gui/topologies/base/interface.py`，结果边界主要经过：

- `TopologySpec`：归一化输入和拓扑元数据；
- `TopologyCandidate`：设计点合成结果；
- `WaveformSet`：线路周期和开关纹波结果；
- `StressResult`：器件电压、电流应力；
- `DesignReport`：供器件、电容、磁件、损耗、热、几何和 GUI 使用的统一报告。

两相拓扑必须使用这些公共结果类型，但不能改变现有字段对旧拓扑的既有含义。

### 2.2 现有输入字段

现有 Boost PFC 输入 schema 位于：

```text
src/pe_claw_gui/topologies/ac_dc/single_phase_boost_pfc_diode_bridge/input_schema.py
```

当前设计输入包括：

- `vac_rms`、`vac_rms_min`、`vac_rms_max`；
- `f_line_hz`；
- `vdc_target_v`；
- `pout_w`；
- `fsw_hz`；
- `dc_bus_ripple_percent`；
- `inductor_current_ripple_ratio`；
- `power_factor_target`；
- `input_inductance_h`；
- 环境温度、结温目标和半导体筛选字段。

现有单相 Boost PFC schema 还保留 `sizing_efficiency_assumption` 这一历史输入；它仅用于说明旧拓扑现状，不复制到两相交错 Boost PFC 的用户输入或新拓扑公式。

两相拓扑的用户设计输入应尽量与现有单相 Boost PFC 保持一致：复用电压、功率、频率、母线纹波、`inductor_current_ripple_ratio`、`input_inductance_h`、环境温度和器件筛选字段，不新增 `sizing_efficiency_assumption`。

`phase_count=2` 和 `phase_shift_deg=180` 是拓扑固定能力，放在内部 capability/metadata 中，不作为用户可调设计输入。每相 Boost 电感目标由现有纹波率和总电流按理想均流推导，不新增 `phase_inductor_current_ripple_ratio` 或 `phase_inductance_h` 用户字段。

由于现有 `input_inductance_h` 的命名可能被理解为单相输入串联电感，实施步骤 1 必须先冻结它在新拓扑中的确切物理位置；不得在不更新字段说明的情况下把它静默改成每相电感。若两相模型需要一个额外的公共桥后电感，才考虑新增明确命名的内部字段或可选输入。

### 2.3 现有线路周期模型

现有线路周期模型位于：

```text
src/pe_claw_gui/topologies/ac_dc/single_phase_boost_pfc_diode_bridge/line_cycle.py
```

它在整流半线路周期 `theta ∈ [0, pi]` 采样：

- 整流输入电压；
- 正弦输入电流目标；
- Boost 占空比；
- 电感平均电流；
- 允许的开关纹波。

线路周期采样结果目前存入候选元数据，并由波形、应力和磁件适配器继续读取。两相实现应保留同一个线路周期基准，但在每个采样点上计算两个相位的相电感电流和相位交错的开关纹波。

### 2.4 现有单相 Boost 设计公式

当前合成逻辑位于：

```text
src/pe_claw_gui/topologies/ac_dc/single_phase_boost_pfc_diode_bridge/synthesizer.py
```

当前核心关系为：

```text
V_ac,peak = sqrt(2) * V_ac,rms
V_rec(theta) = V_ac,peak * sin(theta)
D(theta) = clamp(1 - V_rec(theta) / V_dc, 0, 1)
I_line,rms = P_out / V_ac,rms
I_line,peak = sqrt(2) * I_line,rms
Delta_I_allowed = ripple_ratio * I_line,peak
L_total >= max[V_rec(theta) * D(theta) / (Delta_I_allowed * f_sw)]
```

当前单相 Boost PFC 同时保存电气电流和由 `sizing_efficiency_assumption` 推导的设计电流。两相拓扑不新增也不使用该输入，直接采用与理想 PFC 功率平衡一致的 `P_in = P_out` 设计电流；如未来需要固定工程裕量，应作为明确的拓扑策略或额定值规则记录，不能重新引入一个隐藏的效率输入。两相实现也不能悄然修改既有单相 Boost PFC 的 `power_factor_target` 解释。

当前还会计算：

- 高线整流峰值和 DC 母线可行性；
- DC-link 电容需求；
- Boost 开关、Boost 二极管和输入桥应力；
- 线路周期波形和开关纹波积分指标。

### 2.5 现有下游路径

现有单相 Boost PFC 已有以下专用路径：

- 拓扑注册：`src/pe_claw_gui/topologies/base/registry.py`；
- 能力声明：`src/pe_claw_gui/topologies/base/capabilities.py`；
- GUI 表单：`src/pe_claw_gui/app/topology_forms/single_phase_boost_pfc_diode_bridge_form.py`；
- 输入桥选择：`pipeline/run_bridge_rectifier_pipeline.py` 和 `pipeline/run_full_pipeline.py`；
- 半导体选择：`pipeline/run_device_pipeline.py`；
- Boost 电感适配：`engines/magnetics/inductor_adapter.py`；
- 损耗、热、几何和效率扫描：`pipeline/run_loss_pipeline.py`、`run_thermal_pipeline.py`、`run_geometry_pipeline.py`、`run_efficiency_sweep_pipeline.py`；
- 现有 AC-DC 回归：`tests/test_phase8_ac_dc_topologies.py` 和 `tests/test_ac_dc_efficiency_sweep.py`。

两相拓扑优先复用这些阶段的调用顺序和运行隔离机制；需要扩展的重点是“多相角色、多相波形和多磁件结果”，而不是重新创建一套公共流水线。

## 3. 两相交错 Boost PFC 的目标物理模型和公式

### 3.1 统一符号

```text
N = 2                         相数
phi_1 = 0                     第 1 相开关相位
phi_2 = pi                    第 2 相开关相位
Tsw = 1 / f_sw                开关周期
Vac,rms                       交流输入 RMS 电压
Vdc                           目标 DC 母线电压
Pout                          输出功率
L1, L2                        两相 Boost 电感
inductor_current_ripple_ratio 现有 Boost PFC 输入中的电感电流纹波率
```

首版默认 `L1 = L2 = L_phase`，但实现和报告应保留每相结果，不能只保留一个没有相位标识的电感值。

### 3.2 线路周期电压和总输入电流

在整流半线路周期 `theta ∈ [0, pi]`：

```text
V_rec(theta) = sqrt(2) * Vac,rms * sin(theta)
D(theta) = clamp(1 - V_rec(theta) / Vdc, 0, 1)
```

首版沿用现有理想 PFC 功率平衡：

```text
P_in = Pout
I_line,rms = P_in / Vac,rms
I_line,peak = sqrt(2) * I_line,rms
I_total(theta) = I_line,peak * sin(theta)
```

这里的 `I_total(theta)` 是桥后两相电感电流的总平均包络，不是任一相的电流。

### 3.3 两相理想均流假设

理想均流时：

```text
I_phase,1(theta) = I_phase,2(theta) = I_total(theta) / 2
I_phase,peak = I_line,peak / 2
```

这是变换器设计阶段的理想均流前提，不是控制器仿真结果。首版不计算相间失配、不引入均流容差输入，也不输出不均流下的最坏相应力。报告只需记录 `current_sharing_assumption = ideal_equal_phase_current`。

### 3.4 每相电感纹波和电感需求

每相的 Boost 电感电流纹波在 CCM 一阶模型下为：

```text
Delta_i_phase,k(theta) = V_rec(theta) * D(theta) / (L_k * f_sw)
```

相电感的允许纹波定义为：

```text
Delta_i_allowed,phase = inductor_current_ripple_ratio * I_phase,peak
```

因此每相目标电感为：

```text
L_k,required >= max_theta[
    V_rec(theta) * D(theta)
    / (Delta_i_allowed,phase * f_sw)
]
```

如果存在不同的 `L1`、`L2`，必须分别计算相 1 和相 2 的纹波、峰值、谷值和磁件需求；不能用两个电感的平均值替代最坏相。

### 3.5 180° 交错后的总纹波

两相开关调制使用：

```text
phi_1 = 0
phi_2 = Tsw / 2
```

在每个线路周期采样点，分别构造两相的开关纹波函数 `r_1(t, theta)` 和 `r_2(t, theta)`，然后计算：

```text
r_total(t, theta) = r_1(t, theta) + r_2(t + Tsw/2, theta)
Delta_i_total,pp(theta) = max_t(r_total) - min_t(r_total)
```

首版不得用固定的 `Delta_i_phase / 2` 代替总纹波，因为交错抵消量随占空比变化，在 `D ≈ 0.5` 附近最强，在其他占空比下不同。实现上应采用确定性的分段三角波或等价的一个开关周期采样器，并在以下边界验证：

- `D = 0` 和 `D = 1`；
- `D = 0.5` 的理想抵消；
- 低线、高线和线路零点附近；
- 两相电感不完全相等时的残余纹波。

线路周期的总输入电流仍由两相平均电流之和决定；交错主要改变开关频率附近的纹波、器件 RMS 电流和 EMI 相关指标，不能把它误写成改变了低频 PFC 功率平衡。

### 3.6 器件电流和电压应力

每相开关和二极管的导通窗口沿用 Boost 关系，但输入电流使用该相电流：

```text
i_switch,k(t, theta) = D(theta) * i_phase,k(t, theta)
i_diode,k(t, theta) = (1 - D(theta)) * i_phase,k(t, theta)
```

每相应分别计算：

- 峰值电流；
- RMS 电流；
- 平均电流；
- 开关电压最大值；
- 二极管反向电压；
- 低线、高线和理想均流条件下的设计值。

输入桥的电流由两相总输入电流计算，不能把桥电流再乘以 2。Boost 二极管和主开关则按相独立选择或按相位实例复用同一候选，但报告必须保留两个位置的应力。

### 3.7 DC-link 电容和低频纹波

首版 DC-link 低频电容需求沿用现有一阶能量平衡：

```text
Delta_Vdc,pp = Vdc * dc_bus_ripple_percent / 100
Cdc,required >= Pout / (2 * pi * f_line * Vdc * Delta_Vdc,pp)
```

这个公式基于总输出功率，不应因为相数为 2 而直接除以 2。两相交错主要降低开关频率纹波，低频二倍线频能量摆动仍由总功率决定。

输出电容 RMS 电流应由两相二极管电流、负载 DC 电流和交错开关纹波的合成结果计算，并至少同时保留：

- 每相二极管电流；
- 两相合计二极管电流；
- 电容电流；
- 低频和开关频率分解口径。

### 3.8 损耗、磁件和热量合并

总损耗必须按物理位置求和：

```text
P_semiconductor,total = P_switch,1 + P_diode,1 + P_switch,2 + P_diode,2 + P_bridge
P_magnetic,total = P_inductor,1 + P_inductor,2
P_capacitor,total = P_dc_link
P_total = P_semiconductor,total + P_magnetic,total + P_capacitor,total + P_other
```

热设计不能只使用总损耗平均分配。每个主开关、Boost 二极管和 Boost 电感都应有独立位置损耗；当两相共用一个器件候选时，只能复用候选参数，不能合并应力和热阻位置。

## 4. 代码新增和修改的设计方案

### 4.1 新增独立拓扑包

推荐新增：

```text
src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/
    __init__.py
    input_schema.py
    synthesizer.py
    line_cycle.py
    interleaving.py
    waveform.py
    stress.py
    evaluator.py
```

职责建议如下：

- `input_schema.py`：只负责输入归一化、字段范围和两相默认值；
- `synthesizer.py`：负责总功率、两相电流、电感、电容和可行性；
- `line_cycle.py`：负责线路周期电压、总电流、相电流和占空比；
- `interleaving.py`：负责 180° 相移、两相开关纹波和总纹波合成；
- `waveform.py`：构造兼容公共 `WaveformSet` 的聚合结果和相位明细；
- `stress.py`：输出每个器件位置的独立应力；
- `evaluator.py`：组装拓扑结果、公式口径、边界和警告；
- `__init__.py`：暴露独立 `PLUGIN`，不导入或执行其他拓扑设计。

不建议直接复制现有 Boost PFC 目录后进行大量字符串替换。应复用稳定的基础工具，但让两相公式和结果字段由新包拥有。

### 4.2 公共结果契约

现有 `TopologyCandidate` 仍可承载公共设计点字段，但新增两相数据必须使用明确的 metadata 命名或新的 typed adapter。建议最少包含：

```text
phase_count = 2
phase_shift_deg = 180.0
phase_inductance_h = {"phase_1": ..., "phase_2": ...}
current_sharing_assumption = "ideal_equal_phase_current"
phase_current_share = {"phase_1": 0.5, "phase_2": 0.5}
phase_line_cycle = {"phase_1": {...}, "phase_2": {...}}
interleaved_ripple_metadata = {...}
phase_device_roles = {...}
```

公共 `WaveformSet` 的已有字段应保留稳定语义。推荐方案是：

1. 既有 `inductor_current_a`、`switch_current_a` 和 `diode_current_a` 表示可审计的聚合或主结果，并在 metadata 中明确其定义；
2. 相 1、相 2 的完整数组存入明确命名的 `phase_waveforms` typed 结构或版本化 metadata；
3. 下游应力和器件适配器优先读取相位明细，不能从聚合电流反推单相应力；
4. 若决定扩展 `WaveformSet` 字段，必须同步更新 schema、报告、GUI 读取和旧拓扑回归，不能让旧拓扑出现空的伪相位字段。

`StressResult` 当前只有 `switch` 和 `rectifier` 两个通用槽位。两相实现需要在不改变旧槽位意义的前提下，引入相位角色明细，例如 `phase_1_main_switch`、`phase_2_main_switch`、`phase_1_boost_diode` 和 `phase_2_boost_diode`。如果公共模型暂不扩展，应通过拓扑专用应力映射和报告 metadata 保存完整角色结果，不能把两个相位的最大值伪装成单个器件的完整结果。

### 4.3 Registry、能力和 GUI 路由

需要新增但本计划阶段不实施的集成点：

- `src/pe_claw_gui/topologies/base/registry.py`：注册新的 topology ID、显示名、插件路径、表单路径和 legacy key；
- `src/pe_claw_gui/topologies/base/capabilities.py`：新增 AC-DC 两相 PFC 所需字段、hook、支持状态和边界说明；
- 新增 `single_phase_interleaved_boost_pfc_diode_bridge_form.py`；
- AC-DC 分类页、表单路由和结果页增加新 ID；
- 用户文档列出新拓扑的“首版 CCM、180° 交错、理想均流和未覆盖控制边界”。

表单不应直接暴露内部数组和 Python 对象。首版只允许明确的工程输入，`phase_count=2` 和 `phase_shift_deg=180` 可以作为只读能力展示或隐藏默认值。

### 4.4 输入桥和半导体角色

新拓扑仍使用单相二极管输入桥，因此应接入现有 AC-DC 桥式整流器选择流程。桥式整流器的电流使用两相总输入电流，桥损耗不能重复计算。

Boost 功率级需要四个物理位置：

```text
phase_1_main_switch
phase_2_main_switch
phase_1_boost_diode
phase_2_boost_diode
```

实现前应先检查现有半导体角色契约是否支持“同一角色的两个位置”。推荐增加可审计的角色/位置描述或 topology adapter，而不是在 `run_device_pipeline.py` 中继续堆积不可扩展的 `topology_id` 特判。

首版可以允许两相选择相同型号，但报告必须记录：

- 每个物理位置的候选 ID；
- 相位数量和位置数量；
- 相 1、相 2 的电流应力；
- 选择是否强制同型号；
- 若不同型号，是否经过匹配规则；
- 每个位置的损耗和热结果。

### 4.5 两个 Boost 电感的磁件路径

现有单相 Boost PFC 电感请求在：

```text
src/pe_claw_gui/engines/magnetics/inductor_adapter.py
```

两相实现需要新增独立的 design request 和 operating-point request。推荐策略是：

1. 分别建立 phase 1 和 phase 2 的 `InductorDesignRequest`；
2. 在均流和参数相同的默认情况下优先选择同一磁件设计作为两个物理实例；
3. 报告保留两个实例 ID、每相电流、每相损耗和匹配状态；
4. 首版不建模相间磁件失配；若后续允许独立选型，必须另行定义匹配约束和适用范围；
5. 效率扫描只刷新两个已选电感的损耗，不重新搜索磁件。

不能把两个电感的损耗简单写入一个单相 `selected_design_id` 而丢失相位信息。若现有 `MagneticResult` 不支持多实例，应增加明确的 phase result 结构或 topology-specific magnetic adapter。

### 4.6 效率扫描和运行点刷新

现有 AC-DC 效率扫描已经为单相 Boost PFC 提供专用 evaluator。两相实现需要增加单独的分发路径：

```text
two-phase interleaved Boost PFC
    -> two-phase load-point evaluator
single-phase Boost PFC
    -> existing single-phase evaluator
```

两相负载点 evaluator 必须：

- 固定两相器件候选、电感候选和 DC-link 电容候选；
- 按负载比例缩放总电流和每相电流；
- 重新生成两相 180° 交错波形；
- 重新计算每个相位的器件、电感和电容损耗；
- 合并总效率和损耗；
- 保留 phase-level warnings 和 aggregate warnings；
- 不触发新的器件或磁件选择。

操作点刷新也必须验证旧的单相 Boost PFC 结果不被两相分支覆盖。新拓扑的运行目录、artifact 和 report provenance 必须使用当前 run context。

### 4.7 报告和 GUI 展示

结果报告至少应能显示：

- 总输入电流和每相输入/电感电流；
- 相 1、相 2 的电感值、峰值、谷值和纹波；
- 180° 相移和总纹波抵消指标；
- 两相主开关和 Boost 二极管的独立应力；
- 两个 Boost 电感的独立磁件结果；
- 输入桥的总电流和桥损耗；
- 总损耗与分相损耗之和；
- 理想均流假设、相位设置和模型边界警告。

GUI 不应把两个相位渲染成一个无标签的“Boost switch”或“Boost inductor”。聚合视图可以保留，但必须能追溯到 phase 1 和 phase 2。

## 5. 分步骤实施方案

每一步都必须在开始前检查当前工作区，完成后运行该步骤的聚焦验证、检查 diff 和 status，并记录提交和验证结果。步骤之间不能用未验证的共享契约继续推进。

### 步骤 0：冻结现有单相 Boost PFC 基线

**目的**：证明新拓扑开发不会改变旧拓扑。

**工作内容**：

- 固定现有单相 Boost PFC 默认输入和至少一组低线/高线输入；
- 记录 candidate、waveform、stress、device、bridge、magnetic、capacitor、loss、thermal、geometry 和 efficiency sweep 的关键字段；
- 保存旧拓扑的硬件候选 ID、警告、artifact 清单和稳定输出摘要；
- 明确现有字段单位和 `power_factor_target` 的当前语义；
- 确认当前未提交用户修改，不将其纳入基线。

**验收**：现有单相 Boost PFC 的焦点测试通过，形成可比较的 baseline fixture 或结构化摘要。

**步骤 0 执行记录（2026-09-28）**：

- 新增 `scripts/record_single_phase_boost_pfc_step0_baseline.py`，以临时隔离目录运行现有单相 Boost PFC 的完整设计链；
- 固化 nominal、180 Vac low-line 和 265 Vac high-line 三个工况；
- 固化 candidate、waveform、stress、device、输入桥、magnetic、capacitor、loss、thermal、geometry 和固定硬件 efficiency sweep 的稳定字段；
- 新增 `tests/fixtures/single_phase_boost_pfc_step0_baseline.json` 和 `tests/test_single_phase_boost_pfc_step0_baseline.py`；
- 快照排除了 run ID、时间戳、运行时长、临时路径和 efficiency sweep signature；
- 当前基线记录的 efficiency sweep artifact 是 `efficiency_curve` 和 `loss_breakdown_stacked`，没有把未返回的 CSV artifact 写入基线；
- 验证：结构验收 `1 passed`；重复性验收 `1 passed`；完整两项测试运行约 2 分 59 秒，未发现基线重复性差异。

### 步骤 1：冻结两相拓扑输入和结果契约

**目的**：在写公式和代码前确定字段含义，防止后续把单相字段复用成多相字段。

**工作内容**：

- 确认 topology ID、显示名、legacy key 和 support status；
- 确认 `phase_count=2`、`phase_shift_deg=180` 是否固定；
- 确认相电感纹波率的参考电流；
- 确认公共输入电感和相电感是否同时存在；
- 定义 phase-level device roles、magnetic instances、waveform metadata 和 report 字段；
- 定义总电流、相电流、总纹波和每相纹波的单位与计算来源；
- 写出首版不支持的 DCM、CrM、THD 和 EMI 边界，并明确理想均流是设计前提而非控制仿真结果。

**验收**：输入字段、输出字段、单位、状态和 provenance 可由 schema/contract 测试表达，且没有复用歧义字段。

**步骤 1 执行记录（2026-09-28）**：

- 冻结 topology ID、显示名、legacy key、AC-DC 类别和 `planned` 支持状态；
- 冻结 `phase_count=2`、`phase_shift_deg=180`、理想 50/50 均流和 CCM first-pass 边界；
- 冻结用户输入复用现有 Boost PFC 字段，不新增 `sizing_efficiency_assumption`、相数、相移、均流容差或相电感用户输入；
- 冻结 `input_inductance_h` 为每相串联电感贡献，公共标量 candidate 字段使用每相语义，完整 phase-level 数据使用明确 metadata；
- 冻结四个功率器件位置、两个 Boost 电感实例、共享输入桥和 DC-link 电容的报告角色；
- 新增 `tests/fixtures/two_phase_interleaved_boost_pfc_step1_contract.json` 和 `tests/test_two_phase_interleaved_boost_pfc_step1_contract.py`；
- 明确记录 DCM、CrM、动态均流控制、相间参数失配、零点控制动态、THD、EMI 和详细寄生模型为首版不支持边界。

### 步骤 2：实现独立 topology package 的输入和公式内核

**目的**：先在拓扑包内完成可测试的电气合成，不接入公共流水线。

**工作内容**：

- 新增 `input_schema.py`、`synthesizer.py`、`line_cycle.py` 和 `interleaving.py`；
- 实现总线路周期电压和总输入电流；
- 实现固定的理想均流分配 `I_phase = I_total / 2`；
- 实现每相 Boost 电感纹波和电感需求；
- 实现 180° 交错开关纹波和总纹波；
- 实现 DC-link 低频电容需求；
- 实现低线、高线和母线可行性判断；
- 在 metadata 中记录每个公式的 basis、单位和边界。

**验收**：拓扑包可以独立完成 `build_spec()` 和 `synthesize()`；公式单元测试覆盖零点、峰值、`D=0.5` 交错抵消、低线和高线边界；未导入 GUI 或公共 pipeline。

**步骤 2 执行记录（2026-09-28）**：

- 新增独立包 `src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/`，包含 `input_schema.py`、`line_cycle.py`、`interleaving.py`、`synthesizer.py` 和包导出文件；未修改 registry、capability、GUI 或公共 pipeline；
- 输入复用步骤 1 冻结的 Boost PFC 字段，不读取或生成 `sizing_efficiency_assumption`、`phase_count`、`phase_shift_deg` 或相电感用户输入；
- 总输入电流使用 `Iline_rms = Pout/(Vac_rms * PF_target)`，相电流使用固定 `Iphase = Iline/2`；低线线路周期用于每相电感最坏需求，高线峰值用于母线可行性；
- 每相总串联电感使用 `Ltotal = Vrect*D/(DeltaI_phase*fsw)`，再拆分为 `Linput_phase + Lboost_phase`；公共 candidate 的 `inductance_h` 保持每相总串联电感语义；
- 180 度交错总纹波使用 `DeltaIaggregate = DeltaIphase * abs(1 - 2D)`，并在 metadata 中保存总量、相量、公式、单位和边界；
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step2_core.py`，覆盖输入边界、线路周期零点/峰值、50/50 均流、`D=0.5` 抵消、低线电感设计和高线母线失败边界；
- 验证：步骤 1 契约与步骤 2 核心测试共 `10 passed`，新增包 `compileall` 通过；步骤 0 单相 Boost PFC 基线回归 `2 passed in 183.98s`。

### 步骤 3：实现两相波形、应力和拓扑结果

**目的**：把每相物理量建立完整，再映射到公共结果模型。

**工作内容**：

- 实现两个相位的线路周期平均电流；
- 实现每相开关纹波、开关电流、二极管电流和电感电压；
- 实现输入桥总电流；
- 实现两相开关和二极管的独立 RMS/峰值/平均值；
- 实现 phase-level stress metadata 或 typed adapter；
- 实现 `evaluator.py`，记录总量与分相量的计算关系；
- 保持现有 `WaveformSet` 旧字段对其他拓扑的兼容性。

**验收**：拓扑独立测试可以验证 `phase_1 + phase_2 = total` 的平均电流关系、两相相移、总纹波抵消趋势、器件应力和报告字段完整性。

**步骤 3 执行记录（2026-09-29）**：

- 在两相 topology package 内新增 `waveform.py`、`stress.py` 和 `evaluator.py`，完成线路周期电流、每相开关/Boost 二极管包络、每相电感电压、聚合输入桥电流、相级 RMS/峰值/平均应力和拓扑汇总；
- `WaveformSet` 旧数组继续按步骤 1 定义提供聚合或代表相投影，完整两相数组、180° carrier offset、纹波抵消和字段 basis 放在该拓扑自己的 metadata；没有扩展共享 `WaveformSet`/`StressResult` 模型；
- 相级应力通过拓扑内 typed `InterleavedPFCStress` adapter 暴露，公共 `StressResult` 两个兼容槽代表 phase 1，输入桥应力单独保存在 adapter；
- 固定硬件 operating-point 波形中电流按 load ratio 缩放，电感纹波保持由既定电感与开关频率决定；
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step3_waveform.py`，验证相电流和等于总电流、180°相移、D=0.5 总纹波抵消、固定硬件纹波、相级器件应力、输入桥应力和 evaluator 汇总；
- 增加旧单相与新两相拓扑在两个执行顺序下重复运行的隔离检查，并用步骤 0 nominal baseline 核对旧拓扑 candidate 电感和电容；
- 影响分类：topology-local；未变更共享结果模型、registry、capability、pipeline、器件/磁件角色或 GUI，因此运行步骤 1/2/3 聚焦测试、compileall 和旧/新拓扑隔离检查，不运行全量测试；步骤 4 及之后的集成阶段另行验证 downstream consumers；
- 验证：步骤 1/2/3 聚焦测试 `15 passed`；隔离检查包含在该测试结果内；新增包 `compileall` 通过。

### 步骤 4：接入 registry、capability 和 GUI form

**目的**：让新拓扑可以被发现和选择，但暂时限制下游阶段在契约完成后接入。

**工作内容**：

- 注册 topology definition；
- 添加 capability required/default fields 和 boundary notes；
- 新增独立 topology form；
- 接入 AC-DC 分类页和表单路由；
- 添加 registry、capability、form switching 和 import isolation 测试；
- 验证导入插件不会运行设计、修改共享状态或写 artifact。

**验收**：registry 能解析新拓扑、form 能加载默认输入、旧 19 个拓扑的注册集合和表单路由不改变。

**步骤 4 执行记录（2026-09-29）**：

- 将 `single_phase_interleaved_boost_pfc_diode_bridge` 注册到 AC-DC registry，保留 legacy key，并新增 runtime plugin adapter；plugin hooks 委托步骤 1–3 的 topology-local core，`build_report()` 只组装电气结果，不触发后续公共流水线；
- 新增 planned capability `ac_dc_single_phase_interleaved_boost_pfc`，required/default fields 与冻结输入契约一致，不包含 `sizing_efficiency_assumption`、相数、相移或均流控制字段；boundary notes 明确 CCM、180 度交错、理想均流及 DCM/CrM/控制动态/THD/EMI/寄生模型边界；
- 新增独立 GUI form，显示冻结的 13 个设计输入，禁止后续设计、器件、磁件和波形按钮，避免步骤 4 提前调用尚未接入的公共 pipeline；AC-DC 分类页加入两相交错、180 度相移、理想均流和首版边界说明；
- 新拓扑暂时复用单相 Boost PFC 卡片 PNG，并在资源映射中显式记录复用关系；
- 更新 registry 数量和 planned 拓扑例外测试，新增 `tests/test_two_phase_interleaved_boost_pfc_step4_integration.py`，覆盖 legacy routing、capability/form contract、topology-local report 和 import side-effect isolation；
- 影响分类：integration change（registry、capability、form、AC-DC 路由和资源映射）；旧 19 个拓扑的定义、plugin、表单和 pipeline 行为保持原有边界，planned 新拓扑未加入步骤 8 的完整 pipeline 回归；
- 验证：步骤 1–4 聚焦及受影响 registry/GUI 测试 `62 passed`；AC-DC registry/旧 PFC 边界测试 `2 passed`（`MPLBACKEND=Agg`）；完整 AC-DC pipeline 测试未纳入本步骤，因为当前 Python Tk 安装缺少 `entry.tcl`，且旧三相整流 waveform 测试在该环境尝试创建 Tk 窗口；该环境失败与步骤 4 代码无关；
- 本步骤未运行全量测试；未修改 `outputs/` 及既有 migration/Web/deployment 工作区变更。

### 步骤 5：接入输入桥和半导体选择

**目的**：让输入桥和四个功率器件位置具有正确的选择与 provenance。

**工作内容**：

- 将新拓扑加入 AC-DC 输入桥选择映射；
- 定义两个主开关和两个 Boost 二极管的 role/position 契约；
- 确认候选筛选、额定电压、电流和位置数量；
- 实现相同型号复用或相间匹配策略；
- 保留每一物理位置的候选、拒绝原因、评分和来源；
- 对输入桥使用总输入电流，避免桥损耗重复计算。

**验收**：完整设计后四个功率位置和输入桥均有可审计结果；任一相的器件候选缺失时返回明确 warning/failure；旧拓扑器件角色测试不回归。

**步骤 5 执行记录（2026-09-29）**：

- 将新拓扑接入 AC-DC bridge selector，使用聚合两相输入源电流波形构造桥请求；没有把相电流重复计入输入桥；
- 新增四个独立半导体 role：`phase_1_main_switch`、`phase_2_main_switch`、`phase_1_boost_diode`、`phase_2_boost_diode`，每个 role 对应一个物理位置并保留候选计数、筛选轨迹、选中器件和来源；
- 新拓扑的两个 Boost 二极管强制使用 `independent` binding policy，不绑定主开关内部二极管；相位器件仍沿用现有库筛选、额定电压/电流和并联方案机制；
- `run_full_pipeline` 在步骤 5 对新拓扑只执行器件和输入桥选择，随后返回，不提前进入两相磁件、损耗、热和几何阶段；旧拓扑路径保持不变；
- 更新 topology role note、phase role routing、GUI 共享器件筛选字段和步骤 5 专项测试 `tests/test_two_phase_interleaved_boost_pfc_step5_devices.py`；
- 影响分类：integration change（semiconductor role map、stress adapter、bridge selector、pipeline routing）；共享 `DeviceSelectionResult`、`StressResult` 和 bridge/report 数据结构未扩展；
- 验证：步骤 1–5、registry、旧 AC-DC 边界、bridge library、semiconductor library 和单相 Boost baseline 共 `55 passed`；使用 `MPLBACKEND=Agg`；未运行全量测试；
- 完整 AC-DC downstream stages 仍留在步骤 7，未把步骤 5 的器件选择结果误标记为损耗、热或几何完成。

### 步骤 6：接入两相电感磁件设计

**目的**：让两个 Boost 电感进入现有磁件库和选择流程。

**工作内容**：

- 新增两相 design request 和 operating-point request；
- 将每相电流、纹波、频率、伏秒和功率输入磁件筛选；
- 设计默认策略优先选择同一磁件型号的两个物理实例；
- 保存 phase 1/phase 2 的设计 ID、损耗、热和匹配状态；
- 让效率扫描只刷新选定磁件的运行损耗；
- 不改变单相 Boost PFC 的磁件请求和结果语义。

**验收**：两相均有磁件结果，两个实例可以追溯到库记录；不允许只生成一个没有实例数量说明的总电感结果；单相和其他拓扑磁件测试通过。

**步骤 6 执行记录（2026-09-29）**：

- 在 `inductor_adapter.py` 增加两相 Boost PFC 的 per-phase design request 和 operating-point request；每相使用总输入电流的一半、相同的 CCM 纹波目标、开关频率、伏秒条件和每相功率代理，phase 2 明确记录 180° 相移；
- 在 `run_magnetic_pipeline.py` 增加新拓扑专用磁件分支。磁件库只执行一次 phase 1 候选搜索，phase 2 在理想均流和相同设计目标下复用同一库型号作为第二个物理实例，避免无意义的重复搜索；
- 聚合结果保留 `magnetic_quantity=2`、phase 1/phase 2 设计 ID、物理实例 ID、匹配状态和匹配策略；每个选定候选的 metadata 记录 `phase_role` 与 `physical_instance_id`，可以追溯到相位和库记录；
- 不改变单相 Boost PFC 的磁件请求、候选筛选或 `MagneticResult` 公共字段；效率扫描的固定硬件刷新、总损耗、热和几何接入仍留在后续步骤；
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step6_magnetics.py`，覆盖每相请求、180° 标识、50/50 功率电流分配、固定硬件纹波和双实例磁件报告；
- 影响分类：integration change（磁件 adapter 和新拓扑磁件 pipeline routing）；共享磁件结果模型未扩展；
- 验证：两相步骤 6 专项测试 `3 passed`；步骤 1–6 两相拓扑聚焦回归 `26 passed`；默认磁件库实际运行完成并返回两个 phase 设计 ID，均为 `T_24_14_19_FT-3M_Litz_10x0.15_-_Grade_1_-_Unserved_N62_P4`；未运行其他拓扑全量测试。

### 步骤 7：接入完整 pipeline、损耗、热和几何

**目的**：让两相拓扑完成与现有 AC-DC 拓扑一致的设计阶段。

**工作内容**：

- 接入 `run_full_pipeline` 的输入桥、器件、磁件、损耗、热、几何顺序；
- 只为新 topology ID 或 capability adapter 增加必要路由；
- 校验总损耗等于桥、两相器件、两相电感、电容和其他损耗之和；
- 为每相生成热输入和几何位置；
- 维护 run-scoped state 和 artifact isolation。

**验收**：默认输入可以完成设计；阶段状态、warning、失败原因和报告 provenance 完整；运行两相拓扑不会修改已有报告对象或旧拓扑缓存。

**步骤 7 执行记录（2026-09-30）**：

- 在 `run_full_pipeline` 中移除该拓扑器件选择后的早退，使其继续执行磁件、损耗、热、几何和电容阶段，并记录阶段状态；输入桥、四个相位功率器件仍由此前步骤的专用路由提供。
- 接入共用 DC-link 电容选择，并以两相 Boost 二极管电流合成的电容电流刷新拓扑波形和应力；所选电容只代表两相共享母线电容组。
- 损耗阶段分别刷新 phase 1 和 phase 2 固定电感运行损耗，报告保留两相损耗并将其相加；没有把单相结果乘以 2。磁件候选 ID 增加相位后缀以区分两个物理实例，同时保留原磁件库候选 ID。
- 在电容阶段完成后生成两相拓扑的系统设计点损耗汇总：桥损耗 + 活动半导体方案总损耗 + 两相电感总损耗 + 共用 DC-link 电容组损耗 + 其他损耗。当前首版未建模额外损耗，`other_loss_w` 明确记为 `0 W`；任一必需损耗分量不可用时，系统总损耗置为 unavailable 并记录缺项，不发布部分和。
- 几何结果分别列出 phase 1/phase 2 电感目标；热分析复用现有流程及其状态语义。电容、loss、thermal 和 geometry 仍遵循各自现有阶段边界。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step7_pipeline.py` 覆盖默认输入完整 pipeline、桥/器件/电容/磁件结果、两相损耗合计、热状态、分相几何及阶段状态；更新步骤 5/6 专项断言以反映完整 pipeline 启用后的结果结构。
- 影响分类：integration change（公共 pipeline 阶段路由及电容、磁件损耗、几何下游适配）；改动限定为新拓扑 ID 的显式分支，未更改既有拓扑的计算公式或共享报告字段。
- 验证：设置 `PYTHONPATH=src` 以确保导入当前仓库，设置 `MPLBACKEND=Agg`；步骤 1–7 两相拓扑专项测试 `27 passed`（59.80s）。未运行其他拓扑测试或全量测试，符合本次拓扑范围要求。首次未设置 `PYTHONPATH` 的测试收集误导入本机 PE-Claw 1.0 包，未执行用例；修正导入路径后的正式测试通过。
- 实现提交 `2e409dc` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；本记录由后续文档提交记录。步骤 8–10 未执行。
- 系统损耗汇总实现提交 `808de30`；步骤 1–7 两相拓扑专项测试 `27 passed`。之后对缺项时清除过期系统分量字段的边界加固，步骤 7 测试最终复跑 `1 passed`。详见 ChangeLog 的同日后续记录；步骤 8–10 尚未执行。

### 步骤 8：接入 operating-point refresh 和 efficiency sweep

**目的**：验证固定硬件下两相负载点行为正确。

**工作内容**：

- 新增两相专用 load-point evaluator；
- 固定器件、两相电感和 DC-link 电容候选；
- 按总负载比例缩放两相电流；
- 重新计算交错纹波、相位器件损耗、磁损和电容损耗；
- 生成效率曲线、损耗分解和结构化 CSV/JSON artifact；
- 前置检查区分缺少相 1/相 2 器件、任一磁件、桥选择和电容选择；
- 验证 `Generate Waveforms` 不重新选择硬件。

**验收**：负载点网格全部完成或按明确边界失败；硬件候选 ID 在扫描前后不变；旧 AC-DC 五拓扑效率扫描结果不回归。

**步骤 8 执行记录（2026-09-30）**：

- 为两相拓扑增加独立效率扫描路由和固定硬件前置检查，分别指出缺失的输入桥、phase 1/phase 2 开关或 Boost 二极管、任一已选相电感及共享 DC-link 电容。
- 每个负载点按总负载比例生成两相波形与 180° 交错纹波，刷新现有选定器件、phase 1/phase 2 电感和电容的运行点损耗，并按当前输入电流重算桥损耗；不调用器件、磁件、电容重新选型。
- 点级报告汇总桥、半导体、两相磁件、电容和 `other_loss_w=0`。缺任一必需损耗时该点不生成部分总损耗，整个 sweep 状态标记为 blocked 并保留明确 warning。
- 点级 switching-loss audit 记录相移、理想均流、两相电感 RMS、最坏合成纹波和固定硬件 ID；sweep signature 纳入两相磁件 ID。新增 CSV、结构化 JSON 与效率/损耗图表产物。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step8_efficiency.py`，覆盖 0.1/0.5/1.0 p.u.、逐点损耗守恒、输出功率/相电流随负载变化、相位纹波审计、硬件 ID 不变、artifact 内容及四类前置缺项。
- 验证：两相步骤 1–8 组合专项回归 `32 passed`；最终步骤 8 专项复跑 `5 passed`；`git diff --check` 通过。未运行其他拓扑或全量测试；旧 AC-DC 五拓扑效率对比留待步骤 10 集成门禁，未宣称旧拓扑回归已验证。
- 实现提交 `d9a8064` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；步骤 9–10 尚未执行。

### 步骤 9：GUI 结果和用户文档

**目的**：保证 phase-level 结果对用户可解释。

**工作内容**：

- 增加两相波形、两相器件、两相磁件和总量/分量损耗展示；
- 明确显示 180° 相移、理想均流假设和模型边界；
- 使警告、失败原因和硬件前置条件可见；
- 更新 README、拓扑目录、用户输入说明和工程文档；
- 不将“交错降低纹波”表述成已完成 EMI 或控制环路验证。

**验收**：真实 GUI 选择新拓扑、执行设计、生成波形、运行磁件/电容和效率扫描时，结果页不会把两个相位混成一个无标签器件。

**步骤 9 执行记录**：

- 将 topology definition、plugin、表单和 capability 从 planned 切换为可运行的 first-pass；设计成功后开放电容、磁件和波形操作，固定硬件条件齐备后开放效率扫描。
- AC-DC 拓扑选择页和专用表单明确两相 CCM、固定 180° 交错、理想 50/50 均流假设以及不支持的控制/波形/EMI 边界；拓扑卡仍临时复用单相 Boost PFC 图片，专用图片后续替换。
- Design Summary 展示相数、相移、每相总串联电感、设计/运行相电流、纹波和 switching-edge 边界；波形页分别绘制 phase 1、phase 2 与合成电流、逐相开关/二极管电流包络及合成纹波包络。磁件结果增加物理相位标记；损耗页使用拓扑级系统总量和分量，避免把系统损耗误作磁件损耗。
- 更新 README、`docs/two_phase_interleaved_boost_pfc.md` 和针对当前拓扑状态的路由/契约断言；新增步骤 9 结果与文档专项测试。旧迁移验收中的 19 拓扑计数保留为历史记录。
- 验证：步骤 1–9 专项回归 `35 passed`；步骤 9 最终 GUI、结果和文档专项测试 `4 passed`（含真实 Tk GUI 端到端按钮链）；`py_compile` 与 `git diff --check` 通过。未运行其他拓扑或全量测试。
- Git：实现、测试和文档提交 `b074599` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；本执行回执为后续独立文档提交。步骤 10 集成门禁仍待执行。

### 步骤 10：隔离回归和集成门禁

**目的**：证明新增拓扑不会影响现有拓扑。

**工作内容**：

- 新拓扑执行 schema、公式、波形、应力、registry、器件、磁件和效率测试；
- 现有单相 Boost PFC 执行完整 baseline comparison；
- AC-DC 五拓扑执行既有回归；
- 新旧拓扑按两种顺序运行：旧拓扑后新拓扑、新拓扑后旧拓扑；
- 重复运行相同输入，检查 candidate、hardware、report、artifact 和 warning 稳定；
- 检查运行目录、临时文件和共享缓存没有跨拓扑泄漏；
- 在集成门禁再运行全量测试。

**验收**：旧拓扑的工程字段、单位、候选、状态和报告结构无非预期变化；新拓扑独立通过所有验收；全量测试结果和任何环境限制均有记录。

**步骤 10 执行记录（2026-09-30）**：

- 新增 `tests/test_two_phase_interleaved_boost_pfc_step10_isolation.py`。同一个 registry/plugin 实例按“单相 Boost PFC → 两相交错 Boost PFC”和相反顺序运行，输入分别重复；比较 candidate、report/stress/loss/thermal、器件/桥/磁件/电容硬件、manifest 阶段状态、warning、0.1/0.5/1.0 p.u. efficiency sweep 和结构化结果。运行间保留先前 report 与 artifacts，验证对象快照及文件哈希不变、run ID 独立、artifact 归属各自 run root、活动 run context 在调用后清空。结构化 JSON artifact 比较时仅归一化 run ID 与本次运行根路径。
- 验证：步骤 1–10 两相拓扑专项回归 `37 passed`（451.87s）；步骤 10 双顺序隔离用例单独复跑 `1 passed`（217.13s）。命令均设置 `PYTHONPATH=src`、`MPLBACKEND=Agg`。
- 用户要求本步骤只运行两相拓扑，不做其他拓扑全测试。因此旧 AC-DC 五拓扑全面回归和全量 pytest 不作为本步骤验收门槛；隔离用例只为验证跨运行状态保留单相 Boost PFC 作为配对对照。全量 pytest 曾启动但按用户随后指示中止，不记录为通过或失败结果。
- 在范围缩小指示前，曾额外运行选择性基线/AC-DC/输出隔离/GUI 集成集合：`25 passed, 8 failed`（892.31s）。两个单相 Boost PFC baseline fixture 测试通过；失败包括旧效率测试预期的 `csv` artifact key 与当前实现不一致，以及旧输出隔离测试在本机 Windows 长路径下写 artifact 失败。调查发现部分 `tests/` 路径解析到 `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\tests`，该集合不作为两相拓扑验收结果；未修改其断言或生产代码。
- 一次早期隔离夹具使用长临时路径触发 Windows 文件名长度错误；缩短临时目录名后，两相专项隔离用例通过。未因此更改生产 pipeline。
- 影响分类：test-only；新增隔离测试，没有修改拓扑实现或其他拓扑行为。`git diff --check` 对工作树整体报告既有 migration/evidence 长路径问题，相关文件均是预存删除项，不属于本步骤改动；本次新增/修改文件单独检查通过。

### 步骤 10 后修正：设计边界一致性修正（10A–10F 已按限定验证范围完成）

**触发原因**：步骤 10 的隔离测试证明两相拓扑在当前实现下可以独立运行，但手动对比发现电感、磁件和器件选型没有完全使用同一设计边界。两相电感合成使用低线输入，而磁件请求、相位器件应力和输入桥电流主要读取额定线路波形；磁件请求还把相电流 RMS 填入了平均电流字段。该问题属于两相拓扑的设计边界和下游适配一致性问题，不改变步骤 10 已完成的运行隔离结论。

**修正目标和约束**：

- 只修正 `single_phase_interleaved_boost_pfc_diode_bridge` 的拓扑分支；不修改单相 Boost PFC 的公式、字段含义、库记录或选择策略；
- 保留两相低线电感设计作为保守设计边界，不为了接近单相数值而把低线设计改回额定线设计；
- 不新增 `sizing_efficiency_assumption`，继续使用现有两相输入和理想 50/50 均流假设；
- 明确区分每相 Boost 电感、每相总串联电感、相电流平均值、RMS 值和峰值；
- 高线主要承担电压阻断边界，低线主要承担电流和磁件边界；报告必须分别记录两类边界；
- 不把四个相位器件合并成一个无相位标识的应力结果，也不把两相电感损耗简单乘以 2。

**步骤 10A：冻结当前差异和字段语义**

- 记录当前 nominal、low-line 和 high-line 下的 candidate、waveform、phase stress、bridge stress、device、magnetic、loss 和 GUI 摘要；
- 冻结 `candidate.inductance_h` 在两相拓扑中的每相总串联电感语义；
- 冻结 `phase_boost_inductance_h` 为磁件实际搜索目标；
- 冻结 `input_inductance_h` 为每相串联输入电感贡献；
- 定义相电流 `average`、`RMS`、`peak` 和开关纹波 RMS 的来源及单位；
- 将差异分为“保守设计造成的合理差异”和“设计边界未传递造成的实现缺陷”。

**步骤 10B：补充两相设计边界元数据**

修改范围限于拓扑包的 `synthesizer.py`、必要时的 `line_cycle.py`：

- 保留低线电感最坏点计算；
- 在候选 metadata 中保存 low-line、nominal、high-line 的总输入电流、每相电流、允许纹波和实际纹波；
- 保存每相平均值、RMS、峰值以及对应的线路电压条件；
- 为电感、功率器件和输入桥分别记录 `current_design_basis` 与 `voltage_design_basis`；
- 不改变公共 `TopologyCandidate` 字段的旧拓扑语义。

**步骤 10C：修正波形和相位应力适配**

修改范围限于两相拓扑的 `waveform.py`、`stress.py` 以及共享应力适配器中的两相显式分支：

- 额定波形继续用于 GUI 运行点展示；
- 设计点器件应力使用低线电流边界和高线电压边界的组合上界；
- 保留 phase 1、phase 2 的主开关和 Boost 二极管独立 RMS、平均值、峰值；
- 输入桥使用两相总输入电流，不能再次乘以相数；
- 在 stress metadata 和 notes 中记录这是“低线电流 / 高线电压”的组合设计边界，而不是单一线路工况的仿真结果。

**步骤 10D：修正磁件请求和桥选型请求**

修改范围限于两相拓扑分支：

- `engines/magnetics/inductor_adapter.py` 中，`i_avg_a` 使用相电流线路周期平均值；
- `i_rms_a` 使用相电流 RMS 与三角纹波 RMS 的合成值；
- `i_peak_a` 使用低线设计边界的相电流峰值加半个纹波；
- `delta_i_pp_a`、伏秒和目标电感与低线电感设计使用同一口径；
- `pipeline/run_bridge_rectifier_pipeline.py` 中，桥电流容量使用低线聚合输入电流，反向电压仍使用高线边界；
- 两相磁件仍优先复用相同库型号作为两个物理实例，报告保留 phase 1/phase 2 实例信息。

**步骤 10D 执行记录（2026-09-30）**：

- `src/pe_claw_gui/engines/magnetics/inductor_adapter.py` 的两相磁件请求改为明确使用 low-line 每相线路周期平均电流、相电流 RMS 包络与三角开关纹波 RMS 的合成值、低线相峰值加半个允许纹波，以及 low-line 允许纹波和 Boost 电感目标；请求 metadata 记录 current/voltage design line、相电流包络和纹波来源。运行点固定硬件请求仍保留独立语义。
- `src/pe_claw_gui/pipeline/run_bridge_rectifier_pipeline.py` 的两相桥请求改为只使用一次 low-line 两相聚合输入电流波形；反向电压要求使用 high-line `bridge_reverse_stress_v`，推荐 VRRM 继续保留 margin。没有再次乘以相数，也没有改变单相 Boost PFC 分支。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step10d_requests.py`，验证磁件请求的平均/RMS/峰值/纹波公式、每相 Boost 电感目标、桥请求的低线聚合电流和高线反压，以及当前磁性库 allow profile 下磁件不可用时的显式结果。
- 新增 `tests/fixtures/two_phase_interleaved_boost_pfc_step10d_baseline.json`。保留 10A 和 10C fixture，不覆盖历史证据；当前基线重复性测试改为读取 10D fixture，并规范化其 schema/version 标记。
- 结果边界：在当前默认设计和磁性库 allow profile 下，磁性搜索基本候选存在但最终没有通过 allow profile 的候选，phase 1/phase 2 design ID 和 chosen physical instances 显式为 unavailable，不能把步骤 7 的损耗/几何和步骤 8 的效率扫描标记为已完成。未放宽 allow profile、未伪造磁件结果，也未改变共享磁件筛选策略。
- 验证仅限两相拓扑：10D 请求专项及 10B/10C 相关测试 `14 passed`；10D 基线结构/重复性测试 `2 passed`；目标代码 `py_compile` 与 `git diff --check` 通过。一次包含步骤 7/8 的探索性 focused run 为 `14 passed, 5 failed`，失败均为新低线磁件边界导致的无选中磁件及其下游前置条件/旧基线引用，不纳入通过结论；未运行其他拓扑或全量测试。
- 影响分类：两相 topology-local 磁件/桥请求适配，桥 pipeline 有两相显式分支；公共字段语义、单相 Boost PFC、运行点刷新和其他拓扑未修改。下一步为步骤 10E，处理不可用磁件状态和设计边界在结果展示中的明确表达。

**步骤 10E：修正结果展示和用户可读性**

修改范围限于两相结果视图和相关文档：

- 同时展示每相 Boost 电感和每相总串联电感；
- 展示电感和器件选型所依据的线电压边界；
- 区分设计点相电流和 nominal 运行点相电流；
- 对“低线电流、高线电压组合边界”给出明确说明；
- 保留理想均流、180° 交错和未建模控制/EMI 边界提示。

**步骤 10E 执行记录（2026-10-08）**：

- 更新 `summary_view.py`，同时展示每相 Boost 电感目标与每相总串联电感，分别列出 low-line 设计点和 nominal 运行点的相电流平均值、RMS、峰值，并说明磁件和功率器件的设计边界。
- 更新 `magnetic_view.py`，展示理想均流、180° 交错、low-line 电流/电压边界、high-line 器件电压边界、每相电感设计口径；当当前 allow profile 未选中 phase 1/phase 2 磁件时，明确显示 unavailable 原因。
- 更新 `loss_view.py`，明确低线电流与高线电压是组合设计边界，并在磁件缺失时将系统总损耗保持为 unavailable，同时提示缺少两相磁性硬件。
- 更新 `docs/two_phase_interleaved_boost_pfc.md`，补充 Boost 电感与总串联电感区别、组合设计边界和磁件 unavailable 状态；更新步骤 9 GUI 测试以同时覆盖已选磁件与不可用磁件分支；新增 `tests/test_two_phase_interleaved_boost_pfc_step10e_results.py`。
- 验证仅限两相拓扑结果视图和相邻步骤：`tests/test_two_phase_interleaved_boost_pfc_step10e_results.py`、`tests/test_two_phase_interleaved_boost_pfc_step10d_requests.py`、`tests/test_two_phase_interleaved_boost_pfc_step9_gui.py` 共 `9 passed`；目标生产代码和测试 `py_compile` 通过。未运行其他拓扑或全量测试。
- `git diff --check` 的检查范围受工作区既有超长路径删除项影响，已单独检查本步骤相关文件无空白错误；既有 migration/deployment/Web 删除、`outputs/` 和 pytest 临时目录未纳入本步骤提交。下一步为步骤 10F。
- 追加两相步骤 5/6/10D smoke 验证 `10 passed`（58.36s）；前述 9 项结果/请求/真实 Tk GUI 测试耗时 201.15s。两批中的 10D 用例重复执行，不作为独立用例累加。
- Git：实现、测试与用户文档提交 `1a127ac` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；本执行记录和状态更新随独立文档提交推送。步骤 10E 完成，步骤 10F 待执行。

**步骤 10F：两相专项验证和低影响隔离门禁**

只运行与本修正直接相关的测试，不执行全量测试：

- 步骤 2/3：验证低线、额定线、高线 metadata、相电流守恒、纹波和相位应力；
- 步骤 5：验证四个功率器件位置和输入桥使用设计边界电流；
- 步骤 6：验证磁件请求的平均值、RMS、峰值和 Boost 电感口径；
- 步骤 7/8：验证两相损耗合计、固定硬件运行点和效率扫描不重新选型；
- 步骤 9：验证 GUI 同时显示 Boost 电感与总串联电感；
- 步骤 10：重复两相拓扑并保留最小单相 Boost PFC 配对 smoke test，确认两相适配器分支没有改变旧拓扑结果；
- 对每个修改步骤执行 `git diff --check`、聚焦测试、提交和推送；不把未运行的其他拓扑全量回归标记为通过。

**步骤 10F 执行记录（2026-10-08）**：

- 影响分类为 test/evidence/documentation-only。修改步骤 7、8、10 隔离测试和当前基线重复性测试，新增 `scripts/record_two_phase_interleaved_boost_pfc_step10f_baseline.py` 与 `tests/fixtures/two_phase_interleaved_boost_pfc_step10f_baseline.json`，补充用户文档。不修改生产公式、共享模型、库记录、磁件 allow profile、选型政策或其他拓扑。
- 完整硬件成功路径使用真实库支持的 230–265 Vac 工况：仅将默认 `vac_rms_min` 改为 230，nominal 230 Vac、400 Vdc、1 kW、100 kHz 等其他输入不变。实际筛选得到两个可追溯的物理电感，总设计损耗约 `25.0454313765 W`；严格验证桥、四个器件位置、两相电感、共享电容的系统损耗守恒、分相几何和阶段状态。桥、半导体、电感损耗或电容任一必需分量缺失时，总损耗不得返回部分和。
- 默认 180–265 Vac 工况单独严格验证：基本可行磁件候选存在，但当前 allow profile 无通过候选，两相 design ID 均为 None、chosen designs 为空、系统损耗为 unavailable。扫描必须返回 phase 1 磁件缺项警告、无点集、无效率产物且 `is_complete()` 为 False。现有前置返回仍使用默认 `status="available"`，本步骤不改共享状态语义，不把该字段当作扫描成功证据。
- 固定硬件扫描覆盖 0.1/0.5/1.0 p.u.，保持所有硬件 ID 不变；用禁止调用的断言替换磁件搜索、半导体、电容和桥选型入口，证明扫描未重新选型。保留逐点损耗求和、电流趋势、理想均流、180° 交错和 CSV/JSON/图像产物检查；补充任一相主开关或电感缺失的前置诊断。
- 最小单相 Boost PFC / 两相配对完整链路按两个顺序运行，比较归一化报告、硬件、损耗、warnings、阶段、扫描结果和产物。另在同一 registry/plugin 内按“默认无磁件 → 可选磁件”和反向顺序重复两相设计。使用 pickle 对象快照和文件 SHA256 检查先前报告及产物不变、run ID 独立、产物路径归属及活动 run context 清空；同工况重复结果严格相等。
- 新 10F 快照由脚本生成，覆盖 nominal、low-line、high-line 三组设计输入并重复验证；10A/10C/10D 历史快照保留。与 10D 比较仅排除 10E 明确修改的 `gui` 文本，其余工程字段全部严格相等，不放宽数值或选型断言。
- 初轮诊断 `42 passed, 5 failed`（433.14s）：步骤 7/8 旧用例假定默认工况必有磁件，导致完整链路与下游缺项断言失败；10D 快照还包含被 10E 更新的 GUI 文本。上述根因分别通过独立真实成功/不可用工况和新版本快照解决，不删除失败证据、不伪造磁件、不放宽公共公式或筛选规则。
- 最终两组不重叠专项验证合计 **51 passed，无 skip**：步骤 7/8/10 隔离组 `10 passed`（820.89s）；步骤 1–6、9、10A–10E 组 `41 passed`（660.23s，含真实 Tk 按钮链、快照重复性与设计边界测试）。未运行全量测试或其他拓扑全面回归，仅保留计划要求的单相 Boost 最小配对对照。
- 复现命令（本次两组分别运行；完整覆盖所有两相专项测试文件）：

```powershell
$env:PYTHONPATH = 'src'
$env:MPLBACKEND = 'Agg'
$focusNames = @(
    'test_two_phase_interleaved_boost_pfc_step7_pipeline.py',
    'test_two_phase_interleaved_boost_pfc_step8_efficiency.py',
    'test_two_phase_interleaved_boost_pfc_step10_isolation.py'
)
$twoPhaseTests = @(Get-ChildItem tests -Filter 'test_two_phase_interleaved_boost_pfc_*.py')
$focusTests = @($twoPhaseTests | Where-Object Name -In $focusNames | ForEach-Object FullName)
$restTests = @($twoPhaseTests | Where-Object Name -NotIn $focusNames | ForEach-Object FullName)
python -m pytest -q --basetemp .pytest-tmp-10f-focus @focusTests
python -m pytest -q --basetemp .pytest-tmp-10f-rest @restTests
```

- 验证范围限制：设计边界 metadata 的三种线电压检查不等于固定硬件跨线电压刷新验证。当前波形复用候选线路周期，磁件 operating request 按负载缩放 low-line 平均值和含纹波 RMS，保留设计纹波及伏秒，未按 operating voltage 重算电流。硬件固定和损耗代数守恒的通过不证明跨线/跨负载损耗图的完整物理一致性，该问题已写入用户文档，未在本验证步骤中修改生产模型。
- 本计划继续保留 Active：默认宽线工况的磁件可用性、上述 operating-point 模型限制，以及未执行的旧拓扑全面/发布验收，均不能被 10F 的专项通过替代。图卡仍为占位。暂不归档本计划，也不声称旧 19 拓扑全面回归完成。
- Python 编译、定向 `git diff --check` 和暂存差异检查随提交执行；既有 migration/deployment/Web 删除、outputs 和 pytest 临时文件不纳入本次提交，不清理、不执行备份。专项验证已通过，提交推送完成后再更新 10F 完成状态。

**10F 提交推送回执（2026-10-08）**：专项测试、快照脚本/证据、用户文档和执行记录提交 `201abbb`，已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`。本次目标 Python 文件编译、定向与暂存 `git diff --check` 均通过；全工作区既有超长路径删除项不属于本次验证通过范围。步骤 10F 的限定门禁完成，本状态回执随独立文档提交推送。此前记录中的“待提交推送”为提交前状态，不代表仍待执行。未运行的其他拓扑全面回归、默认磁件可用性和运行点物理模型限制继续保留。

**步骤 10G：两相磁件扩大搜索与完整链路修正（2026-10-09 新增，限定门禁完成）**

触发 case 为 `outputs/20261009_spibpdb_fe6cd98f`：180–265 Vac、nominal 230 Vac、1 kW、400 Vdc、100 kHz。只读重放发现每相前 14 个磁芯生成 103,494 个基本候选、allow 后为 0；保持同一请求/库/工程限值扩大到前 48 个磁芯后有 181 个通过。该数字是诊断证据，不作为永久固定的验收数量。两相分支没有复用公共路径已有 frontier fallback，不能据初始筛选为空断言整个库没有可行磁件。

影响分类：共享 `run_magnetic_pipeline.py` 内已有两相显式分支的 integration change；调用现有 engine，不修改公共搜索实现、allow profile、库记录、输入、公式、单位或其他拓扑分支。搜索按相只执行一次，phase 2 在理想均流下复用模型、保留独立身份。不会新增叠芯竞争搜索，不顺带修正公共 NaN 处理或运行点物理模型。

按以下四个阶段顺序实施，每阶段验证后独立 commit/push，推送后才能标记该阶段完成：

1. **10G-0 计划冻结**：将根因、影响范围、修改方案、验证范围和剩余问题写入本计划与 ChangeLog。定向检查文档差异后提交并推送。
2. **10G-1 搜索接入、两相实例与审计**：在初始工程筛选 `post_allow_count == 0` 时调用已有 `search_fixed_inductor_candidate_frontier`；传入同一 phase 1 request、context、profile、backend，以及已生成的基本候选和 compression，避免重复初始搜索。沿用已有 14→24→48→96 磁芯分阶段边界，合格即停止；无基本候选也允许扩大搜索，避免遗漏更大磁芯。使用最终 compression 进入既有 Pareto/代表性选择。只对 phase 1 搜索；phase 2 与其物理设计参数一致，但 design ID/phase_role/physical_instance_id 独立。使用既有 `MagneticResult.frontier_search_audit` 保存 stage bounds、候选数、通过数、淘汰原因和 final stage；phase 2 审计注明共享搜索来源，aggregate 用按相审计结构保留真实单次搜索数量。专项单元测试覆盖 fallback 参数不变、初筛成功不扩大、全部搜索耗尽、零基本候选和异常；更新默认工况旧 unavailable 断言为成功，并保留独立失败路径，不伪造生产成功硬件。
3. **10G-2 真实宽线／窄线硬件、损耗与效率**：默认 180–265 Vac 和既有 230–265 Vac 都用真实库全链路验证。严格检查两个所选实例参数一致/身份不同/工程限值通过、逐相电感损耗合计、桥/半导体/电感/共享电容系统求和、分相几何和阶段；0.1/0.5/1.0 p.u. sweep 完整，硬件 ID 固定，搜索与四类选型入口禁止调用。必需硬件或损耗缺失必须诊断，不返回部分和。保留 10A/10C/10D/10F 历史快照，新增脚本生成 10G 基线；设计输入、candidate、line metadata、waveform/stress、桥请求和器件身份等未修改边界应与 10F 一致，磁件／损耗／热／几何／GUI 下游变化单独记录。用户文档说明扩大搜索和模型候选边界；不把虚拟 shape/material 配对宣称为已验证商业料号或实物。
4. **10G-3 隔离和最终专项门禁**：单相 Boost PFC／两相默认宽线按两顺序运行，保留最小旧拓扑配对对照；宽线／窄线两相也双顺序重复，比较归一化报告、硬件、损耗、警告、阶段、效率和产物，校验旧 report pickle 与文件哈希不变、run ID 独立、路径归属及活动 context 清空。明确无候选场景另测，不能继续假定默认宽线必失败。最终运行全部两相 step1–10G 专项文件；不运行全量 pytest 或其他拓扑全面回归。更新验证数字、耗时、commit/push、真实默认 case 结果及剩余事项。

验证命令：环境 `PYTHONPATH=src`、`MPLBACKEND=Agg`。10G-1 先运行 `tests/test_two_phase_interleaved_boost_pfc_step10g_frontier.py` 中纯分支测试；10G-2 运行真实磁件、步骤 7/8、10D 请求和 baseline 用例；10G-3 按两相文件列表运行（只枚举 `tests/test_two_phase_interleaved_boost_pfc_*.py`），隔离测试可单独一批。Windows 使用短 basetemp 名（如 `.pytest-tmp-10g`），避免 artifact 超长路径。新增/修改 Python 文件编译、定向 `git diff --check`、暂存差异和 Git 状态检查随每阶段执行；不清理或提交 outputs、缓存及既有无关删除。

验收：默认宽线真实库得到两个可追溯的合格模型实例；扫描固定硬件且损耗代数守恒；搜索复用与失败路径有证据；未修改输入范围或工程筛选限值；配对和重复隔离通过。最终候选数不冻结为 181，默认选型成功也不代表所有输入范围均有候选或损耗模型已全面验证。

继续保留的限制：100℃ 饱和数据 NaN 会进入饱和淘汰，诊断应区分数据缺失和真实超限；manifest stage succeeded 表示阶段执行完成，不能单独证明推荐硬件存在；nominal 线路波形／low-line 磁件 operating request 的负载缩放及跨线刷新问题仍未修正；旧拓扑全面／发布验收、实物验证及专用卡片图片仍未执行。以上不通过放宽本次断言解决。

**10G-0/1 执行记录（2026-10-09）**：10G-0 文档提交 `df24fdf` 已推送。10G-1 在既有两相分支接入共享 frontier fallback，复用初始候选/compression，不重复初始搜索；phase 2 复用 phase 1 搜索、保留同一原始 library_candidate_id 和独立实例 ID，aggregate 的既有 audit 字段按相记录搜索和复用关系。新增 step10g_frontier 分支测试覆盖初筛已通过、不通过后扩大成功、扩大耗尽、空初始候选及异常，步骤 6 实例/请求测试一并验证 `8 passed`（4.91s），末次来源 ID 匹配修正后复跑记录随提交。纯分支测试使用数值 fixture 验证路由；真实库宽线/窄线完整链路在 10G-2 执行，不用该 fixture 宣称生产硬件成功。历史默认 unavailable 与当前基线的预期更新留到下一阶段，不把未运行的测试记为通过。定向 diff/编译检查随本阶段提交执行，推送后进入 10G-2。

**10G-1 推送回执 / 10G-2 执行记录（2026-10-09）**：

- 10G-1 实现提交 `bcfb899` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`；末次分支/步骤 6 复跑为 `8 passed`（3.70s），编译及定向/暂存 diff 检查通过。10G-0、10G-1 完成。
- 步骤 7 恢复默认 180–265 Vac；步骤 8 同时验证真实宽线/窄线模型的饱和、损耗、电流密度、填充限值，两相参数一致但实例/design ID 不同、原始 library ID 相同。宽线初筛无通过、扩大后通过；窄线不触发扩大。扫描禁止磁件 basic/frontier 搜索及器件/桥/电容重选，三负载点硬件身份固定、损耗守恒。
- 默认失败断言改为独立注入的搜索耗尽用例：两个电感无 ID、系统总损耗 None、missing-inductor 诊断、无扫描点/文件。结果视图缺硬件分支也独立覆盖；真实 Tk 默认设计必须选中两相磁件并完成效率扫描，不保留成功/失败任选的断言。
- 新增 `scripts/record_two_phase_interleaved_boost_pfc_step10g_baseline.py` 和脚本生成的 10G fixture。10A/10C/10D/10F 历史证据保持不变。三工况与 10F 严格比较输入、candidate/metadata、线路、波形、应力、器件、桥请求及电容身份；变化限于磁件及其损耗、热、几何、GUI 和 frontier 审计。
- 实际 14→24→48 搜索在三工况均得到可选模型。额定/高线选中两个 PQ 35/35、FT-3M、43 匝、8 并绕模型；低线两个 PQ 40/30、FT-3M、38 匝、1 并绕模型。系统估算损耗分别为 nominal `30.957926132850 W`、low-line `31.870757008381 W`、high-line `31.353494887234 W`，不作为所有输入或实物的承诺。
- 验证：步骤 7/8/10D `18 passed`（478.62s）；真实 Tk/10D 最新耗尽断言/10E 视图 `9 passed`（578.42s）；新格式基线结构、诊断编码及独立完整复跑 `4 passed`（333.90s）。10D 三用例重复，两阶段本批合计 28 个独立用例通过，无 skip。环境 `PYTHONPATH=src`、`MPLBACKEND=Agg`，basetemp 分别 `.pytest-tmp-10g-p`、`.pytest-tmp-10g-v`、`.pytest-tmp-10g-b2`，未全测试。
- 首次基线重复检查 `2 passed, 1 failed`（542.62s）：审计中的 NaN 不等于自身，旧通用稳定化函数不能直接用于审计快照。只在新证据脚本将 NaN/±Infinity 编码为明确字符串，保留全部诊断字段并使用 `allow_nan=False`；新增编码测试，重新运行脚本生成基线后独立复跑通过。未删除字段、放宽工程断言或改生产 NaN 处理。
- 用户文档更新搜索机制、实例/计数语义、耗尽状态与虚拟模型限制。目标 Python 编译及定向/暂存 diff 检查通过；本阶段提交推送后再记完成，随后进入 10G-3。原用户输出、无关删除、pytest 临时文件保留且不提交，不清理或备份。

**10G-2 推送回执 / 10G-3 专项门禁记录（2026-10-09）**：

- 10G-2 提交 `b7e9079` 已推送至指定远端分支，10G-2 完成。10G-3 只修改隔离测试与本计划/ChangeLog，不再修改生产代码。
- 单相 Boost PFC／两相默认宽线双顺序重复通过；两相宽线／窄线也双顺序重复通过。后者宽线冻结原用户 case 的全部 17 个原始输入字段（含 `diode_binding_policy=auto`），已与原 manifest 的 raw_input_snapshot 精确核对；窄线只改 vac_rms_min 为 230。回归不依赖本机 outputs 文件的存在。
- 归一化快照增加 frontier 审计，保留 non-finite 明确编码、硬件、损耗、警告、阶段、效率与产物检查。宽线扩大、窄线不扩大，phase 2 复用而不再搜索。复用同一插件/registry，保留旧报告和文件，pickle/文件哈希不变、run ID 独立、artifact 属于本 run、active context 清空均通过。搜索耗尽的失败路径在 10D/10G 分支测试独立通过。
- 原用户 case 重放选中两个 PQ 35/35 / FT-3M / Litz 75x0.04 Grade 1 Single Served / 43 匝 / 8 并绕模型，设计 ID 分别以 `::phase_1`、`::phase_2` 结尾。设计点系统估算损耗 `30.957926132850 W`；nominal operating sweep 的 0.1/0.5/1.0 p.u. 损耗分别 `4.002510473180 / 12.455468002578 / 24.733962566017 W`，效率分别 `0.961515251363 / 0.975694535857 / 0.975863040097`。设计组合边界和 operating 点口径分别记录，不能混为同一工况；既有跨线刷新/磁件 low-line 负载缩放限制不因扫描完成而消失。
- 原 case manifest SHA256 前后均为 `33834eecdce929e932839522fd007d2e5620cb80aac240f365de370c067a1e52`，没有覆盖旧结果。测试生成可复核的首轮宽/窄 `isolation_receipt.json`，位于 `.pytest-tmp-10g-i/test_step10g_user_wide_and_nar0/0/{wide,narrow}/`；这些是可重建临时证据，不提交。
- 最终隔离组 `2 passed`（675.72s）；剩余步骤 1–6、10B/10C/10G 组 `35 passed`（19.42s）。加上 10G-2 的 28 个独立用例，全部 16 个两相专项文件共 **65 passed、无 skip**；pytest collect-only 核对为 65。10G-1 的 8 项已包含于最终剩余组，不重复累计。未运行全量 pytest 或其他拓扑全面回归，旧拓扑只做上述单相最小配对。
- 复现命令如下；10D 在前两批重复，最终按唯一用例计数。最初在 PowerShell 将通配符直接交给 pytest 的 collection 命令没有展开路径，未收集用例；改用显式文件列表后完成收集，不计为测试通过或生产失败。

```powershell
$env:PYTHONPATH = 'src'
$env:MPLBACKEND = 'Agg'
$lossTests = @(
    'tests/test_two_phase_interleaved_boost_pfc_step7_pipeline.py',
    'tests/test_two_phase_interleaved_boost_pfc_step8_efficiency.py',
    'tests/test_two_phase_interleaved_boost_pfc_step10d_requests.py'
)
$guiTests = @(
    'tests/test_two_phase_interleaved_boost_pfc_step9_gui.py',
    'tests/test_two_phase_interleaved_boost_pfc_step10d_requests.py',
    'tests/test_two_phase_interleaved_boost_pfc_step10e_results.py'
)
$baselineTest = 'tests/test_two_phase_interleaved_boost_pfc_step10a_baseline.py'
$isolationTest = 'tests/test_two_phase_interleaved_boost_pfc_step10_isolation.py'
$coveredNames = @($lossTests + $guiTests + @($baselineTest, $isolationTest) | ForEach-Object { Split-Path $_ -Leaf })
$allTests = @(Get-ChildItem tests -Filter 'test_two_phase_interleaved_boost_pfc_*.py')
$restTests = @($allTests | Where-Object Name -NotIn $coveredNames | ForEach-Object FullName)
python -B -m pytest -q --basetemp .pytest-tmp-10g-p @lossTests
python -B -m pytest -q --basetemp .pytest-tmp-10g-v @guiTests
python -B -m pytest -q --basetemp .pytest-tmp-10g-b2 $baselineTest
python -B -m pytest -q --basetemp .pytest-tmp-10g-r @restTests
python -B -m pytest -q --basetemp .pytest-tmp-10g-i $isolationTest
```

- 本阶段编译、定向/暂存 diff 检查和 Git 审查随提交执行；验证已通过，提交推送后再更新完成回执。既有 95 个无关删除、用户 outputs 和临时产物不纳入提交，不清理或备份。本计划仍 Active，保留运行点模型、公共 NaN 数据/状态语义、实物、卡片图片以及未执行的旧拓扑全面/发布验收事项。

**10G 完成与推送回执（2026-10-09）**：10G-3 测试与记录提交 `3b7a919` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`。10G-0 `df24fdf`、10G-1 `bcfb899`、10G-2 `b7e9079`、10G-3 `3b7a919` 均已按顺序验证、提交和推送，10G 限定门禁完成；本完成回执随后独立文档提交推送。最终 18 个目标 Python 文件编译、阶段定向及暂存 diff 检查通过，复现分组实际枚举为 16 个两相文件 / 9 个剩余文件。全部 65 个独立专项用例通过，无 skip；没有运行全量或其他拓扑全面回归。默认宽线及原用户 case 的扩大搜索可用性已解决，历史 unavailable 记录不再表示当前结果。原 outputs 和 95 个无关删除保持原样，未清理、未备份；运行点物理模型、公共 NaN 数据/状态语义、实物/图片与发布验收仍留在 Active，不宣称整个计划全面验收完成。

## 10H：两相结果展示、几何与硬件总览修正

10H 处理 10G 后仍可复现的结果层问题。范围只覆盖两相交错 Boost PFC 的结果展示和下游产物，不改变设计输入、均流假设、磁件筛选边界、损耗公式或其他拓扑的公共语义。

1. **10H-0 计划冻结**：记录根因、影响边界、验收字段和专项测试；每个后续阶段独立验证、更新 ChangeLog、提交并推送后才标记完成。
2. **10H-1 结果页**：电感页和磁件页读取 `design_requirements.phase_1/phase_2`，显示每相 L、频率、电流、纹波、吞吐和模式；两相明确说明未执行 1/2/3-core stack comparison；磁件损耗显示逐相及合计电感损耗，并与系统总损耗区分。单相及其他拓扑既有文本保持不变。
3. **10H-2 几何与 Pareto**：两相几何按 library/model/mechanical/electrical signature 复用相同布局，保持 phase ID 和每相 target；signature 不匹配时分别渲染；两相磁件导出真实 phase-1 搜索 frontier 的 Pareto 工件和元数据一次， operating-point refresh 不重复搜索或导出。
4. **10H-3 硬件总览**：两相电感组必须包含 phase 1、phase 2 两个 child entry、各自身份/几何/损耗/体积，并给出合计数量、体积和损耗以及 integrated layout；缺一相时状态为 incomplete/unavailable，禁止用单相代表值伪装完整总览。
5. **10H-4 专项门禁**：覆盖实际 GUI 入口、结果文本、几何复用/不复用、Pareto artifact、硬件总览完整/缺相路径；运行两相全部受影响测试并保留最小单相 Boost 隔离配对，不运行全量 pytest。新增展示基线时保留 10G 历史工程边界基线。

### 10H 验收标准

- 两相结果页不再显示虚假的 `1-core/2-core/3-core unavailable`，且每相设计请求和损耗可追溯。
- 两个 phase geometry target 均有明确 layout 状态；相同物理模型只共享渲染结果，不丢失 phase identity；不匹配模型分别生成布局并报告失败原因。
- `MagneticResult.artifact_paths` 包含实际 Pareto 图及其搜索数据来源，图来自一次 phase-1 frontier；硬件总览包含两个 phase child entries 和聚合值。
- 缺失 phase、缺失 layout 或缺失工件返回诊断状态，不生成部分合计。
- 每阶段 Python 编译、定向 pytest、`git diff --check`、提交和推送均有记录；不提交 `outputs/`、缓存或既有无关删除。

**10H-0/10H-1/10H-2 执行记录（2026-10-09）**：10H-0 计划冻结提交 `06403ec` 已推送；10H-1 结果页修正提交 `e394173` 已推送。10H-1 编译及视图/LLC 回归为 `15 passed`（117.66s），两相页已显示嵌套 phase request、逐相损耗和明确的未执行 stack comparison。10H-2 接入两相 phase-1 Pareto 工件一次性导出，并按物理模型签名复用相同几何、保留 phase-2 layout design ID；步骤 7 真实几何验证 `1 passed`（118.59s）。10H-2 的硬件总览实现和专门测试仍在执行，推送前不标记完成。

**10H-2/10H-3 推送回执（2026-10-09）**：10H-2 几何复用和 Pareto 导出提交 `a607165` 已推送。10H-2 的步骤 7 真实验证为 `1 passed`（118.59s）。10H-3 两相硬件总览已实现两个 child entries、side-by-side integrated bbox、数量/体积/损耗合计和缺相诊断；结果页、总览完整路径及缺相路径共 `5 passed`（117.83s），待完成提交推送后进入 10H-4。

10H-4 将运行实际 Tk GUI 设计/磁件/波形/效率入口，检查两相 Pareto artifact、两个几何 target 和硬件总览 child entries；同时保留步骤 10E/10F 的结果与隔离测试作为专项门禁，不运行全量 pytest。

**10H-4 完成与推送回执（2026-10-09）**：最终实际 Tk GUI 入口验证 `4 passed`（263.22s），覆盖 Magnetics 后自动进入 Inductor 页、phase-1 Pareto PNG 和 PF view 加载、phase 1/2 geometry layout、两相 Hardware Overview child entries 及效率扫描。最终两相隔离门禁 `2 passed`（644.53s），保留宽/窄线双顺序和单相 Boost 配对；10H 相关结果/总览专项无 skip。10H 的 10H-0 `06403ec`、10H-1 `e394173`、10H-2 `a607165`、10H-3 `4dc3fca`、H-4 `c8236a8` 均已推送。

10H 全部阶段已完成并推送到 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`。本轮最终验证数字以最后一次复跑为准：结果/总览/frontier `10 passed`，几何 `1 passed`，真实 Tk GUI `4 passed`，隔离 `2 passed`；全部无 skip，未运行全量 pytest。

最终 H-4 快速专项还包括结果/总览/前沿分支 `10 passed`（118.29s）和几何全链路 `1 passed`（114.77s）；这些测试没有运行全量 pytest。

10H 仍不宣称全量工程验收：未运行全量 pytest，未改变运行点物理模型、公共 NaN 饱和语义、实物可采购性或拓扑图片；Pareto 工件表达一次 phase-1 搜索 frontier，phase 2 是同一物理模型的独立实例。

### 10H 补齐：总览绘制、遗漏路径和当前版本基线

此前 10H 的完成记录对应当时已执行的专项范围。随后复核发现：child entries 已有两相，但 integrated layout 和绘图仍以单个聚合电感表示；几何签名不匹配及部分缺工件路径没有独立验收；10G 基线仍用于当前版本重放，未记录 10H 新增的展示说明。本轮补齐以下内容，历史记录和 fixture 保持可追溯。

1. **总览展示**：将两相组转换为 `inductor_phase_1` / `inductor_phase_2` 两个 integrated objects，保留各自尺寸、损耗、体积、身份和标签。组图和整体 2D/3D 图分别绘制两个实体，同排放置并保持明确间距；合计仍由两个实例求和。这是工程包络总览，不是已验证 PCB 或机械排布。
2. **遗漏路径**：明确验证同签名复用、不同签名独立渲染、独立渲染失败、缺 layout/target、几何身份不匹配、丢失几何文件和 Pareto PNG/CSV。缺项显示诊断占位，不生成完整数量/体积/损耗合计或 integrated 电感实体。
3. **搜索数据来源**：仅两相分支开启现有 CSV 导出机制，与 phase-1 PNG 同次导出；校验候选 ID 和损耗值，不重复 phase-2 搜索或导出。运行点刷新和效率链保留固定硬件契约。
4. **当前基线**：新增 `scripts/record_two_phase_interleaved_boost_pfc_step10h_baseline.py` 和独立 `tests/fixtures/two_phase_interleaved_boost_pfc_step10h_baseline.json`，覆盖 nominal/low/high 三工况的真实完整设计链、逐相几何、总览对象、文本及工件存在性。仅运行 ID、时间、耗时和临时路径按明确规则归一化；工件比较 basename 和存在性，几何、身份、布局、状态、警告及工程数值保留。10G fixture 作为历史证据保持原样；除已知新增 Pareto 来源说明外，全部旧工程字段严格一致。
5. **专项门禁**：运行全部两相测试文件，真实 Tk GUI 检查双实体和真实文件；最小单相/两相双顺序重复配对增加总览生成，继续检查旧报告和工件未被后续运行改变。单独记录未执行的全量/其他拓扑发布验收，不以本轮专项结果替代。

**影响分类**：共享总览、渲染、几何和磁件文件中的两相限定分支及相应专项测试/证据。公共公式、库数据、筛选排序、输入契约和其他拓扑计算路径未变。两相总览布局属于本轮预期变化；最小旧 Boost 配对用于验证该共享展示路径的兼容与状态隔离。

**当前状态**：实现、专项验证和当前基线重放已完成；本轮记录、提交和推送随本计划更新完成。10G 复核仍按原计划只运行两相专项和必要的单相 Boost 配对，未运行全量或其他拓扑全面回归。整个计划继续保留 Active：跨线/运行点物理模型、公共 NaN 数据/状态语义、实物与卡片图片及发布验收未由本轮解决。

**10G 复核执行记录（2026-10-09）**：按本计划重新执行 10G 核心门禁：`tests/test_two_phase_interleaved_boost_pfc_step10g_frontier.py` 的扩大搜索/耗尽/异常分支 `5 passed`（4.84s）；10G 相关结果、CSV 来源和异常路径复跑 `16 passed`（174.81s）；用户宽线/窄线两相双顺序隔离 `1 passed`（320.94s）；单相 Boost 与两相配对双顺序隔离 `1 passed`（436.11s）。四组真实搜索均串行执行，避免约 8 GB 环境并发换页。10G-0 至 10G-3 的既有提交和推送回执保持不变，本次为复核，不修改 10G 生产逻辑。

**10H 补齐最终回执（2026-10-09）**：当前 10H 基线严格重放 `5 passed`（361.79s）；结果/总览/frontier `21 passed`（142.01s）；步骤 7/8/9 完整链路和真实 Tk GUI `19 passed`（564.13s）；标签修正后的结果视图 `16 passed`（174.81s）；10G CSV 来源追加校验 `5 passed`（16.99s）。全部两相专项 collect-only 共 80 项；本轮未运行全量 pytest 或其他拓扑全面回归。图片人工检查确认两相在组图和整体 2D/3D 图中为独立实体，保留工程包络语义。当前基线三工况损耗为 30.957926132850 / 31.870757008381 / 31.353494887234 W，fixture SHA256 为 `bd5b99ac4ddb3cbb0decf1e7fa9846d89eb435e467159dc2e9a64f0ea5e66578`。本轮修改与文档同步后提交并推送，计划仍保持 Active。

**本轮提交推送回执（2026-10-09）**：10H 补齐实现、测试、基线及文档提交 `d02d617` 已推送至 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`，远端分支核实为 `d02d6174415f3bda7513f4f1c893a8a607d14604`。全部 16 个两相专项文件的 80 个独立用例已分组执行通过（33 + 5 + 21 + 19 + 2），无 skip；末次标签/CSV/10G 复跑不重复累计。10G 复核和 10H 补齐的限定门禁完成，本回执与首页状态同步作为独立文档提交推送。计划仍 Active，保留上述未执行或未解决的工程与发布验收事项。

## 10I：固定硬件运行点与跨线设计边界一致性修正方案冻结

**冻结状态（2026-10-10）**：本节只冻结公式、字段口径、影响边界和测试矩阵，不代表 10I 代码已经修改或验证完成。10I 实施前不得把运行点跨线一致性写成已实现能力；10G/10H 的已完成结果和历史基线保持不变。

### 10I-0 运行点契约

- `OperatingPoint.vin_v` 在两相交错 Boost PFC 中冻结为输入交流 RMS 电压，单位 V；不得把它解释为整流瞬时电压、峰值电压或 DC-link 电压。
- `OperatingPoint.load_ratio` 冻结为额定输出功率比例；允许值按现有效率扫描边界处理，运行点功率使用 `Pout * load_ratio`。首版沿用现有理想功率平衡和 `power_factor` 语义，不引入 `sizing_efficiency_assumption`。
- `OperatingPoint.vout_v` 若未提供，继续使用设计目标 DC-link 电压；若提供，必须在两相拓扑的运行点波形、应力和损耗链中保持一致并记录来源。
- 两相数量固定为 2、相移固定为 180°、相电流固定为 50/50 理想均流；运行点不引入动态均流、相间失配、DCM 或 CrM 模型。
- 运行点始终复用设计阶段已经选定的 phase 1/phase 2 开关、Boost 二极管、两个电感和共享 DC-link 电容；任何运行点不得调用新的器件、磁件、电容或桥选型。

### 10I-1 冻结公式与字段来源

对每个运行点的线路角 `theta`，两相拓扑使用实际 `vin_v` 重新生成线路周期：

```text
v_rect(theta) = sqrt(2) * vin_v * abs(sin(theta))
P_load = candidate.pout_target * load_ratio
I_input_rms = P_load / (vin_v * power_factor)
I_phase_rms = I_input_rms / 2
D(theta) = clip(1 - v_rect(theta) / Vdc_operating, 0, 1)
DeltaI_phase(theta) = v_rect(theta) * D(theta) / (L_phase * fsw)
DeltaI_aggregate(theta) = DeltaI_phase(theta) * abs(1 - 2 * D(theta))
```

- `v_rect`、`D`、`phase_currents_a`、`phase_ripple_pp_a`、`interleaved_ripple_pp_a` 和 `phase_device_metrics` 必须来自当前运行点线路周期，不能继续直接复用设计点 nominal 数组。
- `WaveformSet.operating_vin_v` 必须等于当前 `OperatingPoint.vin_v`；metadata 中的 `load_ratio`、`operating_active_power_w`、`phase_count`、`phase_shift_deg` 和 `current_sharing_assumption` 必须与运行点请求一致。
- `candidate.inductance_h` 继续表示每相总串联电感；运行点不会把它解释成两相合计电感。两个物理磁件的 design ID、physical instance ID 和 phase role 不得变化。
- 设计点的 `design_boundary_stress` 仍表示低线电流、高线电压的组合选型边界；运行点 stress 表示当前实际线路和负载，不覆盖或改写设计边界字段。

### 10I-2 固定硬件损耗链

每个运行点重新计算当前波形下的 phase 1/phase 2 开关损耗、Boost 二极管损耗、两个电感铜损/磁芯损耗、输入桥聚合损耗和共享 DC-link 电容损耗。总损耗必须保持：

```text
P_loss_total = P_bridge + P_phase_1 + P_phase_2 + P_capacitor + P_other
```

缺失任一必需硬件或关键损耗时，点结果必须明确为 incomplete/unavailable，不能用另一相或设计点数值补齐，也不能生成部分总损耗或伪造效率。

### 10I-3 计划修改边界

预计修改边界如下，实施时必须保持两相显式分支：

- `src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/waveform.py`：按运行点输入电压重建线路周期和两相应力数组。
- 两相拓扑的 stress/evaluator：消费当前运行点数组，保留设计边界与运行点语义分离。
- `src/pe_claw_gui/engines/magnetics/inductor_adapter.py`：运行点请求使用当前运行点的相电流、RMS 和纹波，同时保留固定物理实例身份。
- `src/pe_claw_gui/pipeline/run_loss_pipeline.py` 与 `run_efficiency_sweep_pipeline.py`：仅修正两相固定硬件刷新和损耗汇总路径，不改变单相 Boost PFC 或其他拓扑的默认行为。
- 两相专项测试、用户文档、Active plan 和 `ChangeLog.md`：记录字段、公式、诊断和验证证据。

由于后两个 pipeline 文件是共享文件，本阶段按 integration change 管理；不得以“只有两相调用”为理由跳过最小单相 Boost PFC 配对验证。

### 10I-4 冻结测试矩阵

实施后按以下顺序执行，测试失败时不得通过放宽断言、隐藏诊断或改变状态含义来通过：

1. **公式与字段测试**：两相 nominal/low/high 运行点波形，验证 `vin_v`、功率、电流、50/50 均流、180° 相移、占空比、相纹波和交错总纹波。
2. **负载矩阵测试**：180/230/265 Vac × 0.1/0.5/1.0 p.u.，验证电流随负载比例变化、输出功率、逐相应力和损耗字段。
3. **固定硬件门禁**：对每个运行点断言器件、电感、电容、桥和两个物理磁件 ID 与设计点一致；禁止调用所有选择器入口。
4. **损耗守恒测试**：逐相电感/半导体损耗、输入桥损耗、共享电容损耗与总损耗严格求和；缺件路径返回明确 incomplete/unavailable。
5. **效率产物测试**：效率 sweep 生成完整有效点时，CSV/JSON/图表使用当前运行点数据；无效点不生成伪造产物。
6. **隔离测试**：两相→单相 Boost、单相 Boost→两相两个顺序各运行并重复，比较旧报告、硬件 ID、损耗、warning、stage status 和 artifact 哈希；确认 active run context 清空。
7. **回归门禁**：运行全部两相 10I 相关文件及必要的单相 Boost 配对；不默认运行全量 pytest，除非实际修改扩大到公共模型、报告 schema 或无法界定的共享行为。

### 10I-5 完成标准

10I 只能在代码、专项测试、隔离测试、ChangeLog、提交和推送全部完成后标记完成。完成前计划继续保持 Active，并明确保留全量发布验收、公共 NaN 数据语义、实物可采购性和卡片图片等未决事项。

**修正验收标准**：

- 两相电感、磁件和器件电流选型都覆盖低线设计边界；
- 高线电压边界仍覆盖器件阻断电压和输入桥反向电压；
- `i_avg_a` 不再等同于相电流 RMS；
- 磁件请求使用每相 Boost 电感，GUI 同时显示总串联电感；
- 输入桥只使用聚合输入电流一次；
- 四个相位器件、两个物理电感和总损耗仍可独立追溯；
- 两相固定硬件效率扫描和损耗汇总保持守恒；
- 单相 Boost PFC 的结果、字段和选择策略没有非预期变化；
- 修正后的专项测试、提交和推送记录补充到本计划和 `ChangeLog.md` 后，才能将该修正阶段标记为完成。

**步骤 10A 执行记录（2026-09-30）**：

- 新增 `scripts/record_two_phase_interleaved_boost_pfc_step10a_baseline.py`，对 nominal（230 Vac）、low-line（180 Vac）和 high-line（265 Vac）三种设计输入运行当前两相拓扑完整设计链；新增 `tests/fixtures/two_phase_interleaved_boost_pfc_step10a_baseline.json` 作为稳定字段证据。
- 基线冻结 candidate、候选 metadata、三组线路周期数组、聚合和分相波形指标、代表性 StressResult、四个相位器件角色、输入桥请求、两相磁件结果、电容、损耗、热、几何以及 Summary/Loss GUI 文本行；排除 run ID、时间戳、运行时长、临时路径和 artifact 路径。
- 冻结字段语义：`candidate.inductance_h` 是每相总串联电感；`phase_boost_inductance_h` 是磁件搜索使用的每相 Boost 电感；`input_inductance_h` 是每相串联输入电感贡献；相电流 average、RMS、peak 保留各自物理来源。
- 当前默认设计数据显示每相总串联电感约 `840.035426 uH`、每相 Boost 电感约 `740.035426 uH`。Nominal 相电流 RMS 约 `2.195872 A`，low-line 约 `2.805836 A`，high-line 约 `1.905851 A`，确认 low-line 是当前电流边界。
- Nominal 和 high-line 当前各返回两个可追溯的物理磁件实例；low-line 当前磁件结果对象存在但没有选中实例，损耗为 unavailable，并在基线中保留明确的磁件 notes。该状态作为 10B 磁件边界修正前的事实基线，不被标记为测试失败或被隐藏。
- 三种工况均保留四个功率器件角色和输入桥请求；桥请求使用聚合输入电流，反向电压要求仍记录高线母线边界。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step10a_baseline.py`，验证三工况、字段语义、相位角色、磁件实例或明确不可用状态、GUI 摘要和基线重复性。
- 验证：基线结构测试 `1 passed`；完整基线重复性测试 `1 passed in 140.00s`；新增脚本和测试 `py_compile` 通过；新增文件 `git diff --check` 通过；未运行其他拓扑或全量测试。
- 影响分类：test/evidence/documentation-only；未修改生产拓扑、共享模型、公共 pipeline 或其他拓扑行为。步骤 10B 继续处理低线设计边界向磁件和器件适配的传递。

**步骤 10B 执行记录（2026-09-30）**：

- 修改 `src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/synthesizer.py`，保留低线电感最坏点公式，在候选 metadata 中新增 nominal、low-line、high-line 的输入/相电流、平均值、RMS、峰值、允许纹波和实际纹波指标；同时记录电感、功率器件和输入桥各自的电流/电压设计边界。没有修改公共 `TopologyCandidate` 字段语义，也没有新增 `sizing_efficiency_assumption`。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step10b_boundaries.py`，验证三种线路条件的电流大小规律、两相均流、纹波口径、低线最坏纹波和独立的电流/电压边界 metadata。
- 设计 RMS 继续使用输入 RMS 的理想 50/50 相分配，同时保留采样相电流包络 RMS 和叠加三角开关纹波 RMS，避免线路周期端点离散采样误差被误认为公共字段语义变化。
- 验证仅限两相拓扑：10B 边界测试与步骤 2 合计 `7 passed`；步骤 1–3、步骤 6、10A 结构、10B 综合 focused run 合计 `21 passed`；10A 基线重复性回归 `1 passed`（110.81s）；目标文件 `py_compile` 通过，新增/修改文件 `git diff --check` 通过。未运行其他拓扑或全量测试。
- 影响分类：topology-local metadata/test change；未修改 `waveform.py`、`stress.py`、共享适配器、磁件/桥选型 pipeline 或其他拓扑行为。下一步为步骤 10C，处理低线电流/高线电压边界向相位应力的适配。

**步骤 10C 执行记录（2026-09-30）**：

- 在 `waveform.py` 中增加 topology-local `design_boundary_stress` readback：低线生成两相独立器件电流指标和聚合输入桥电流，高线提供整流峰值/目标 DC bus 电压边界；nominal 或 operating-point 波形数组及其 `phase_device_metrics` 保持原运行点语义。
- 在 `stress.py` 中新增 `extract_design_phase_stress`，明确生成 phase 1/phase 2 的主开关和 Boost 二极管独立设计应力，以及只使用一次的聚合输入桥应力；`StressResult.notes` 记录“低线电流 / 高线电压组合边界”不是单一线路运行波形。
- 在 `engines/devices/stress_adapter.py` 增加仅针对 `single_phase_interleaved_boost_pfc_diode_bridge` 的 design-point 显式分支，使器件选型使用组合边界；current operating-point/efficiency refresh 继续调用普通波形应力，不被设计边界覆盖。
- 保留步骤 10A 的历史 fixture，新增 `tests/fixtures/two_phase_interleaved_boost_pfc_step10c_baseline.json` 验证修正后的完整硬件/损耗快照；10A 结构语义测试仍读取历史 fixture，当前重复性测试改用 10C 快照，未覆盖历史证据。
- 新增 `tests/test_two_phase_interleaved_boost_pfc_step10c_stress.py`，覆盖组合边界、相位独立性、聚合桥应力和共享 design-point adapter 路径。
- 验证仅限两相拓扑：步骤 3、5、10A/10B/10C focused run `15 passed`；清理 design-point adapter 重复调用后的最终 stress/器件复跑 `6 passed`；目标文件 `py_compile` 通过。未运行其他拓扑或全量测试。
- 影响分类：两相 topology-local waveform/stress change，另有共享 stress adapter 中的两相显式路由；未改变单相 Boost PFC、公共 StressResult 字段或运行点 refresh 语义。下一步为步骤 10D，处理磁件请求和桥选型请求的低线电流口径。

## 6. 测试分层和验证矩阵

### 6.1 拓扑局部测试

- 输入默认值、缺失字段、单位和边界值；
- `phase_count=2` 和 `phase_shift_deg=180` 合约；
- 总电流与相电流守恒；
- 两相电感纹波和最坏线电压点；
- `D=0.5` 的交错抵消和非 `D=0.5` 的残余纹波；
- 理想均流下的相位应力和总量守恒；
- 波形、应力和拓扑结果的 phase-level 字段；
- 不支持 DCM/CrM/零点控制时的明确 warning。

### 6.2 集成测试

- registry/capability/form contract；
- 输入桥选择和桥损耗顺序；
- 四个功率器件角色选择；
- 两相磁件选择和实例报告；
- 完整 pipeline stage status；
- operating-point refresh 固定硬件；
- efficiency sweep 固定硬件和两相损耗合计；
- GUI 真实按钮链和结果页字段。

### 6.3 工况矩阵

至少覆盖：

- nominal：230 Vac、400 Vdc、1 kW；
- low line：180 Vac；
- high line：265 Vac；
- 最小和最大允许 DC bus；
- 0.1、0.5、1.0 p.u. 负载；
- 不同 `inductor_current_ripple_ratio`；
- 两相电感按相同设计目标生成；
- 过低母线电压导致的可行性失败；
- 任一相器件、磁件或电容缺失时的失败路径。

### 6.4 低影响修改下的测试范围

- 只改新拓扑包且公共契约不变：运行新拓扑全部工况、插件契约、最小 pipeline smoke test，并比较旧 Boost PFC baseline；
- 改 registry/capability/form：增加 registry、路由和所有 AC-DC 表单切换测试；
- 改 WaveformSet、StressResult、MagneticResult 或器件角色契约：运行所有直接消费者和受影响拓扑回归；
- 改公共 pipeline、损耗、热、几何或报告 schema：运行所有受影响拓扑，必要时运行结构化输出比较和全量测试；
- 不以“新增拓扑未被调用”为理由跳过共享消费者测试。

## 7. 主要风险和未决设计决定

1. **公共波形模型是否扩展**：如果不扩展 `WaveformSet`，相位明细必须有严格 typed adapter；如果扩展，必须保护所有旧拓扑默认值和序列化兼容性。
2. **器件角色的多实例表达**：应优先使用角色规格和位置数量，而不是继续增加散落的 topology ID 分支。
3. **磁件选择政策**：首版两个相位采用相同设计目标并优先使用同型号磁件，报告仍保留两个物理实例；相间失配不在首版模型内。
4. **相电感纹波率的基准**：必须固定为相峰值电流，不能沿用总输入峰值而不改字段说明。
5. **总纹波公式**：必须由相移后的开关波形求和得到，不能假设所有占空比下都恰好减半。
6. **PF 目标语义**：新拓扑首版沿用旧 Boost 的理想 PF 功率平衡；若使用 `power_factor_target` 修正电流，需单独建立新的公式和旧拓扑兼容策略。
7. **控制和 EMI 边界**：交错 PWM 的确定性波形和理想均流假设不等于闭环均流、THD 或 EMI 认证结果。
8. **高风险共享修改**：多相器件、磁件、波形和报告若一次性改公共模型，影响范围会从 topology-local 变成 shared integration，必须提高测试等级。

## 8. 完成标准

本计划对应的实现只有同时满足以下条件，才能从 Active 进入完成状态：

- 新 topology ID、capability、form、plugin 和所有路由已注册；
- 输入、合成、两相波形、应力、拓扑报告和边界说明完整；
- 两相相位、相电流、相电感、器件角色和损耗可独立追溯；
- 输入桥使用总电流，功率级器件和电感按相计算；
- 运行点刷新和 efficiency sweep 不重新选择硬件；
- 两相和现有单相 Boost PFC 的 baseline 对比完成；
- 步骤 10 后设计边界一致性修正已完成，低线电流、高线电压、磁件电流字段和 GUI 电感口径均有专项证据；
- 旧的 19 个拓扑没有非预期的字段、数值、状态、候选或 artifact 变化；
- 交错拓扑在新旧拓扑交替运行和重复运行下没有状态泄漏；
- 聚焦测试、受影响回归和集成门禁结果已记录；
- `ChangeLog.md`、用户文档和迁移/证据记录与实际实现一致；
- 未把 DCM、CrM、动态均流、THD、EMI 或控制环路能力写成已实现功能；理想均流只作为设计假设。

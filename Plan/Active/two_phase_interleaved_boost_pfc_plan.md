# 两相交错 Boost PFC 拓扑新增计划

- **状态**：Active / 实施中（步骤 0–10 已按用户限定范围执行；步骤 10A、10B、10C、10D 已完成；步骤 10E–10F 待执行）
- **目标拓扑 ID**：`single_phase_interleaved_boost_pfc_diode_bridge`
- **所属类别**：AC-DC
- **计划范围**：在现有单相二极管桥 Boost PFC 基础上，新增两相、180° 交错、单向、CCM 一阶工程设计拓扑。
- **当前阶段**：步骤 0–10 已实施，步骤 10A/10B/10C 修正已完成；步骤 10 的验证范围按用户要求限定为两相拓扑专项及与单相 Boost PFC 的双顺序隔离回归。

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

### 步骤 10 后修正：设计边界一致性修正（10A、10B、10C、10D 已完成；10E–10F 待执行）

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

**步骤 10F：两相专项验证和低影响隔离门禁**

只运行与本修正直接相关的测试，不执行全量测试：

- 步骤 2/3：验证低线、额定线、高线 metadata、相电流守恒、纹波和相位应力；
- 步骤 5：验证四个功率器件位置和输入桥使用设计边界电流；
- 步骤 6：验证磁件请求的平均值、RMS、峰值和 Boost 电感口径；
- 步骤 7/8：验证两相损耗合计、固定硬件运行点和效率扫描不重新选型；
- 步骤 9：验证 GUI 同时显示 Boost 电感与总串联电感；
- 步骤 10：重复两相拓扑并保留最小单相 Boost PFC 配对 smoke test，确认两相适配器分支没有改变旧拓扑结果；
- 对每个修改步骤执行 `git diff --check`、聚焦测试、提交和推送；不把未运行的其他拓扑全量回归标记为通过。

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

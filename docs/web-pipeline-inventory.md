# Tkinter GUI 与 Pipeline 调用链清单

> 范围：PE-Claw 1.0 当前 `run_pe_claw_gui.bat` 启动的桌面程序，以及 19 个已注册拓扑从输入、校验、综合、工作点刷新到报告输出的真实路径。本文是 Web 迁移的接口盘点，不改变现有公式、单位或选择策略。

## 1. 入口与导航结构

### 1.1 启动链

```text
run_pe_claw_gui.bat
  -> scripts/check_runtime_dependencies.py
  -> python -m pe_claw_gui
  -> pe_claw_gui.__main__
  -> pe_claw_gui.app.main.main
  -> PEClawMainWindow
```

批处理文件选择 `PE_CLAW_PYTHON`、项目 `.venv` 或系统 Python，设置 `PYTHONPATH=src`，然后启动模块。GUI shell、控制器和页面都在 `src/pe_claw_gui/app/`；旧的 `src/pe_claw_gui/ui.py` 不是当前入口。

### 1.2 页面层级

```text
PEClawMainWindow
  -> NavigationBar: Categories / Topologies / 当前选择
  -> Workspace
       -> ConverterCategoryPage
       -> AC-DC / DC-AC / DC-DC / AC-AC category page
       -> topology-specific form
       -> results notebook
```

结果 notebook 固定注册以下页签，页面按报告中是否有对应结果显示数据或 unavailable：

`Summary`、`Waveforms`、`Stress`、`Devices`、`Capacitor PF`、`Capacitors`、`Inductor PF`、`Inductor`、`Magnetic`、`Loss`、`Thermal`、`Geometry`、`Efficiency`、`Hardware Overview`。

AC-AC 当前只有保留页，没有注册拓扑。注册表共有 19 个可执行拓扑：AC-DC 5 个、DC-AC 3 个、DC-DC 11 个。

## 2. 注册表与能力声明

注册权威是 `topologies/base/registry.py::build_default_registry()`；每项绑定 category、稳定 `topology_id`、插件模块、Tkinter form class 和 legacy key。能力分流位于 `topology_capabilities.py`。

| 类别 | `topology_id` | GUI 表单 | 关键能力路径 |
| --- | --- | --- | --- |
| AC-DC | `single_phase_diode_bridge_rectifier_capacitor_filter` | `SinglePhaseDiodeBridgeRectifierCapacitorFilterForm` | 专用桥式整流器/电容路径；无通用磁件页 |
| AC-DC | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | `SinglePhaseDiodeBridgeRectifierDCInductorFilterForm` | 专用桥式整流器 + DC reactor |
| AC-DC | `three_phase_diode_bridge_rectifier_capacitor_filter` | `ThreePhaseDiodeBridgeRectifierCapacitorFilterForm` | 专用三相桥式整流器/电容路径 |
| AC-DC | `single_phase_boost_pfc_diode_bridge` | `SinglePhaseBoostPFCDiodeBridgeForm` | 通用半导体、磁件、DC-link 电容、损耗/热 |
| AC-DC | `single_phase_totem_pole_bridgeless_pfc` | `SinglePhaseTotemPoleBridgelessPFCForm` | 通用半导体、磁件、DC-link 电容、损耗/热 |
| DC-AC | `single_phase_full_bridge_inverter` | `SinglePhaseFullBridgeInverterForm` | CCM/TCM；当前 full pipeline 的 selection-only 特例 |
| DC-AC | `three_phase_two_level_voltage_source_inverter` | `ThreePhaseTwoLevelVoltageSourceInverterForm` | 三相半导体、三只输出电感、DC-link 电容 |
| DC-AC | `three_phase_three_level_npc_inverter` | `ThreePhaseThreeLevelNPCInverterForm` | NPC 角色化器件、分裂 DC-link、系统验证 |
| DC-DC | `buck_diode_rectified_unidirectional` | `BuckDiodeRectifiedUnidirectionalForm` | 二角色器件、L/C、磁件、损耗/热 |
| DC-DC | `buck_synchronous_rectified_unidirectional` | `BuckSynchronousRectifiedUnidirectionalForm` | 双有源开关角色、L/C、磁件、损耗/热 |
| DC-DC | `buck_boost_diode_rectified_unidirectional` | `BuckBoostDiodeRectifiedUnidirectionalForm` | 二角色器件、L/C、磁件、损耗/热 |
| DC-DC | `four_switch_buck_boost_simplified_four_mode` | `FourSwitchBuckBoostSimplifiedFourModeForm` | 四开关实现、分模式综合 |
| DC-DC | `three_level_tzcm_fixed_frequency` | `ThreeLevelTZCMFixedFrequencyForm` | 三电平开关、TZCM 固定频率模型 |
| DC-DC | `boost_diode_rectified_unidirectional` | `BoostDiodeRectifiedUnidirectionalForm` | 二角色器件、L/C、磁件、损耗/热 |
| DC-DC | `boost_synchronous_rectified_unidirectional` | `BoostSynchronousRectifiedUnidirectionalForm` | 双有源开关角色、L/C、磁件、损耗/热 |
| DC-DC | `llc_resonant_converter_diode_rectifier` | `LLCResonantConverterDiodeRectifierForm` | FHA、变压器 + 外置 Lr、Cr、自动调频 |
| DC-DC | `llc_resonant_converter_synchronous_rectifier` | `LLCResonantConverterSynchronousRectifierForm` | FHA、同步整流角色、变压器 + 外置 Lr、Cr |
| DC-DC | `flyback_diode_rectified_isolated` | `FlybackDiodeRectifiedIsolatedForm` | primary switch + 独立 secondary diode；selection-only 条件分支 |
| DC-DC | `phase_shifted_full_bridge_diode_rectifier_isolated` | `PSFBTopologyForm` | primary bridge + 独立 secondary diode、成对磁件 |

## 3. 输入契约

### 3.1 类型和校验位置

`TopologyField` 只有 `key`、`label`、字符串 `default` 和可选 `choices`。普通字段由 `ttk.Entry` 编辑，枚举由只读 `ttk.Combobox` 编辑。GUI 不设置 Spinbox 边界，也不执行实时数值校验；点击动作后，插件的 `build_spec()` 调用拓扑 `input_schema.py`，在那里转换为 `float`/枚举并检查范围和字段间关系。

下表中的 `number` 表示 GUI 传字符串、schema 转为浮点数；`enum` 表示只读选项。`+inf`/`-inf` 表示代码没有固定有限上/下界。边界括号遵循数学惯例，例如 `(0, 1]` 不含 0、包含 1。

### 3.2 共享选择与温度字段

| 字段 | 类型 | 单位 | GUI 默认 | 最小/最大或选项 | 适用范围 |
| --- | --- | --- | --- | --- | --- |
| `ambient_temp_c` | number | °C | `25` 或 `25.0` | 使用共享 parser 时为 `[-40, 150]`；未使用者只能保证可转为 number | 声明温度输入的表单 |
| `target_junction_temp_c` | number | °C | `100` 或 `100.0` | 使用共享 parser 时为 `[25, 175]`；未使用者只能保证可转为 number | 声明温度输入的表单 |
| `semiconductor_device_type` | enum | — | `Any` | `Any/MOSFET/IGBT/Diode` | 单角色通用器件表单 |
| `semiconductor_manufacturer` | enum | — | `Any` | `Any/Infineon/Navitas/Mitsubishi/ROHM/Wolfspeed` | 通用及多角色表单 |
| `main_switch_category` | enum | — | `Any active switch` | 离散 MOSFET/Si/SiC/GaN/IGBT 及兼容模块类别 | 二极管整流或三电平主开关 |
| `rectifier_diode_category` | enum | — | `Any diode` | SiC SBD、Schottky、FRD/FWD、JBS、diode module；部分拓扑允许模块内部 diode | 二极管整流第二角色 |
| `sync_switch_category` | enum | — | `Any active switch` | 同步开关兼容类别 | 同步 Buck/Boost 等第二角色 |
| `switch_implementation_category` | enum | — | `Any compatible active switch` | discrete MOSFET/IGBT、两个 half bridge、一个 full bridge、module section | 四开关 Buck-Boost |

当主开关选择带内部二极管的模块类别时，GUI 自动联动 `rectifier_diode_category`，并在 `get_raw_input()` 追加派生的 `diode_binding_policy`。该 policy 不是用户输入。Flyback 和 PSFB 强制 secondary diode 独立；LLC 使用 primary/secondary 角色专用字段。

三个 diode-bridge rectifier 表单目前还从 `BaseTopologyForm.get_design_fields()` 继承通用 semiconductor type/manufacturer 控件，但对应 input schema 不消费这些键，full pipeline 也改走专用 bridge-rectifier selector。Web 表单不应把这两个当前无效的桌面控件当成有效后端筛选契约。

### 3.3 经典非隔离 DC-DC 字段

适用：Buck diode、Buck synchronous、Buck-Boost diode、Boost diode、Boost synchronous。全部为 `number`。

| 字段 | 单位 | Buck 默认 | Buck-Boost 默认 | Boost 默认 | 后端最小/最大及关系 |
| --- | --- | --- | --- | --- | --- |
| `vin_min` | V | `36` | `18` | `18` | `(0, +inf)` |
| `vin_max` | V | `60` | `36` | `36` | `[vin_min, +inf)` |
| `vout` | V | `12` | `24` | `48` | `(0, +inf)`；Buck 要求 `< vin_min`；Boost 要求 `> vin_max` |
| `pout` | W | `120` | `120` | `120` | `(0, +inf)` |
| `fs_khz` | kHz | `100` | `100` | `100` | `(0, +inf)` |
| `ripple_current_ratio` | ratio | `0.30` | `0.30` | `0.30` | `(0, +inf)` |
| `ripple_voltage_ratio_percent` | % | `1.0` | `1.0` | `1.0` | `(0, +inf)` |

四开关 Buck-Boost 使用 Buck-Boost 的前七项默认值，并增加：

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大 |
| --- | --- | --- | --- | --- | --- |
| `duty_clamp` | number | ratio | `0.10` | `> 0` | `< 0.5` |
| `transition_band_ratio` | number | ratio | `0.10` | `> 0` | `< 0.5` |

### 3.4 三电平 TZCM 字段

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大/关系 |
| --- | --- | --- | --- | --- | --- |
| `vin_nom` | number | V | `400` | `> 0` | 当前 GUI 未暴露 min/max，schema 令其同时作为范围端点 |
| `vout_nom` | number | V | `200` | `> 0` | `+inf` |
| `pout_nom` | number | W | `2000` | `> 0` | `+inf` |
| `fsw_khz` | number | kHz | `40` | `> 0` | `+inf` |
| `izvs` | number | A | `2` | `0` | `+inf` |
| `ripple_voltage_ratio_percent` | number | % | `1.0` | `> 0` | `+inf` |

### 3.5 Flyback 字段

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大/选项 |
| --- | --- | --- | --- | --- | --- |
| `vin_min` | number | V | `600` | `> 0` | `vin_max` |
| `vin_max` | number | V | `800` | `vin_min` | `+inf` |
| `vout` | number | V | `320` | `> 0` | `+inf` |
| `pout` | number | W | `500` | `> 0` | `+inf` |
| `fs_khz` | number | kHz | `100` | `> 0` | `+inf` |
| `ripple_current_ratio` | number | ratio | `1.20` | `> 0` | `+inf` |
| `ripple_voltage_ratio_percent` | number | % | `1.0` | `> 0` | `+inf` |
| `target_duty` | number | ratio | `0.32` | `0.05` | `0.80` |
| `turns_ratio_ns_np` | number or literal | ratio | `auto` | 数值时 `> 0` | `+inf` 或 `auto` |
| `rectifier_diode_drop_v` | number | V | `1.5` | `0` | `+inf` |
| `clamp_spike_margin_v` | number | V | `100` | `0` | `+inf` |
| `efficiency_estimate` | number | ratio | `0.90` | `> 0.10` | `1.0` |
| `flyback_mode` | enum | — | `bcm` | — | `bcm/dcm/ccm` |

### 3.6 PSFB 字段

GUI 只暴露以下八个电气字段；`max_effective_duty`、deadtime、ZVS load threshold、Bmax、漏感/励磁电感等由 `build_default_inputs()` 补为后端默认，不是当前 GUI 输入。

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大/关系 |
| --- | --- | --- | --- | --- | --- |
| `vin_min` | number | V | `650` | `> 0` | `vin_nom` |
| `vin_nom` | number | V | `750` | `vin_min` | `vin_max` |
| `vin_max` | number | V | `850` | `vin_nom` | `+inf` |
| `vout` | number | V | `400` | `> 0` | `+inf` |
| `pout` | number | W | `5000` | `> 0` | `+inf` |
| `fs_khz` | number | kHz | `100` | `> 0` | `+inf` |
| `ripple_current_ratio` | number | ratio | `0.25` | `> 0` | `+inf` |
| `ripple_voltage_ratio_percent` | number | % | `1.0` | `> 0` | `+inf` |

### 3.7 LLC 字段

两种 LLC 共用 FHA 电气字段。二极管版和同步整流版只在 secondary rectifier 枚举及角色化器件筛选字段上不同。

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大/关系 |
| --- | --- | --- | --- | --- | --- |
| `vin_min` | number | V | `360` | `> 0` | `vin_nom` |
| `vin_nom` | number | V | `400` | `vin_min` | `vin_max` |
| `vin_max` | number | V | `420` | `vin_nom` | `+inf` |
| `vout_min` | number | V | `48` | `> 0` | `vout_nom` |
| `vout_nom` | number | V | `48` | `vout_min` | `vout_max` |
| `vout_max` | number | V | `48` | `vout_nom` | `+inf` |
| `pout_max` | number | W | `4000` | `> 0` | `+inf` |
| `min_load_ratio` | number | p.u. | `0.1` | `0` | `1` |
| `fs_min_hz` | number | Hz | `80000` | `> 0` | `fs_max_hz` |
| `fs_max_hz` | number | Hz | `180000` | `fs_min_hz` | `+inf` |
| `ripple_voltage_ratio_percent` | number | % | `1.0` | `0` | `+inf` |
| `turns_ratio_tolerance_percent` | number | % | `5.0` | `0` | `100` |
| `primary_bridge_type` | enum | — | `full_bridge` | — | `full_bridge/half_bridge` |
| `secondary_rectifier_type` | enum | — | diode: `full_bridge_rectifier`; sync: `full_bridge_synchronous_rectifier` | — | diode 另允许 `full_wave_center_tapped_rectifier`; sync 仅固定值 |

角色化筛选字段均为 enum、无单位：二极管版是 `primary_switch_device_type`、`primary_switch_manufacturer`、`rectifier_diode_device_type`、`rectifier_diode_manufacturer`；同步版将后二者替换为 `secondary_sync_switch_device_type`、`secondary_sync_switch_manufacturer`。类别默认分别为 `Any active switch`/`Any diode`，厂商默认 `Any`。

### 3.8 AC-DC 字段

#### 单相电容滤波整流器

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大 |
| --- | --- | --- | --- | --- | --- |
| `vac_rms` | number | V rms | `230` | `> 0` | `+inf` |
| `f_line_hz` | number | Hz | `50` | `> 0` | `+inf` |
| `vout_v` | number | V | `325` | `> 0` | `+inf` |
| `pout_w` | number | W | `1000` | `> 0` | `+inf` |
| `ripple_ratio` | number | pp/nom ratio | `0.05` | `> 0` | `+inf` |
| `diode_forward_drop_v` | number | V | `1.0` | `0` | `+inf` |
| `diode_voltage_margin` | number | ratio | `2.0` | `> 0` | `+inf` |
| `source_resistance_ohm` | number | Ω | `0.1` | schema 仅要求可转为 number，未设显式下界 | 未设显式上界 |
| `ambient_temp_c` | number | °C | `25` | 见共享温度 | 见共享温度 |
| `target_junction_temp_c` | number | °C | `100` | 见共享温度 | 见共享温度 |

#### 单相 DC 侧电感滤波整流器

字段 `vac_rms`、`f_line_hz`、`vout_v`、`pout_w`、`ripple_ratio`、`ambient_temp_c`、`target_junction_temp_c` 与上表同类型和范围；默认分别为 `230/50/325/1000/0.01/25/100`。另有：

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大 |
| --- | --- | --- | --- | --- | --- |
| `dc_reactor_inductance_mh` | number | mH | `2` | `> 0` | 后端内部默认上限 `5 mH` |
| `source_resistance_ohm` | number | Ω | `0.1` | `0` | `+inf` |

#### 三相电容滤波整流器

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大 |
| --- | --- | --- | --- | --- | --- |
| `vll_rms` | number | V rms line-line | `400` | `> 0` | `+inf` |
| `f_line_hz` | number | Hz | `50` | `> 0` | `+inf` |
| `vout_v` | number | V | `540` | `> 0` | `+inf` |
| `pout_w` | number | W | `3000` | `> 0` | `+inf` |
| `dc_link_ripple_ratio` | number | pp/nom ratio | `0.02` | `> 0` | `+inf` |
| `diode_forward_drop_v` | number | V | `1.0` | `0` | `+inf` |
| `diode_voltage_margin` | number | ratio | `2.0` | `> 0` | `+inf` |
| `source_resistance_ohm` | number | Ω/phase | `0.05` | `> 0` | `+inf` |
| `power_factor_target` | optional number | ratio | blank | `> 0` | `1.0` |
| `ambient_temp_c` / `target_junction_temp_c` | number | °C | `25` / `100` | 见共享温度 | 见共享温度 |

#### Boost PFC 与 Totem-Pole PFC

| 字段 | 类型 | 单位 | Boost 默认 | Totem-Pole 默认 | 最小/最大及关系 |
| --- | --- | --- | --- | --- | --- |
| `vac_rms_min` | number | V rms | `180` | `180` | `> 0`，且 `<= vac_rms` |
| `vac_rms` | number | V rms | `230` | `230` | `[vac_rms_min, vac_rms_max]` |
| `vac_rms_max` | number | V rms | `265` | `265` | `>= vac_rms` |
| `f_line_hz` | number | Hz | `50` | `50` | `(0, +inf)` |
| `vdc_target_v` | number | V | `400` | `400` | `(0, +inf)` |
| `pout_w` | number | W | `1000` | `1000` | `(0, +inf)` |
| `fsw_hz` | number | Hz | `100000` | `100000` | `(0, +inf)` |
| `dc_bus_ripple_percent` | number | % | `5` | `5` | `(0, +inf)` |
| `inductor_current_ripple_ratio` | number | ratio | `0.3` | `0.3` | `(0, +inf)` |
| `power_factor_target` | number | ratio | `0.99` | `0.99` | `(0, 1]` |
| `sizing_efficiency_assumption` | number | ratio | `0.95` | `0.98` | `(0, 1]` |
| `input_inductance_h` | number | H | `0.0001` | 不显示 | `[0, +inf)`；仅 Boost |
| `ambient_temp_c` / `target_junction_temp_c` | number | °C | `25` / `100` | `25` / `100` | Boost 使用共享温度边界；Totem-Pole 当前 schema 只要求可转为 number、未设显式上下界 |

### 3.9 DC-AC 字段

#### 单相全桥逆变器

| 字段 | 类型 | 单位 | 默认 | 最小 | 最大/关系 |
| --- | --- | --- | --- | --- | --- |
| `conduction_mode` | enum | — | `CCM` | — | `CCM/TCM` |
| `vdc_nom` | number | V | `400` | `> 0` | 必须能满足目标 AC 峰值/调制约束 |
| `vac_rms` | number | V rms | `230` | `> 0` | `+inf` |
| `f_line_hz` | number | Hz | `50` | `> 0` | `+inf` |
| `pout_w` | number | W | `1000` | `> 0` | `+inf` |
| `power_factor` | number | ratio | `1.0` | `> 0` | `1.0` |
| `dc_link_voltage_ripple_ratio` | number | ratio | `0.05` | `> 0` | `+inf` |
| `fsw_hz` | number | Hz | `20000` | `> 0` | `+inf`；CCM 使用 |
| `inductor_current_ripple_ratio` | number | ratio | `0.2` | `> 0` | `+inf`；CCM 使用 |
| `fsw_min_hz` | number | Hz | `50000` | `> 0` | `fsw_max_hz`；TCM 使用 |
| `fsw_max_hz` | number | Hz | `300000` | `> fsw_min_hz` | `+inf`；TCM 使用 |
| `tcm_valley_current_target_a` | number | A | `-1` | 无固定有限下界 | `< 0` 才符合当前 TCM valley 目标语义 |
| `ambient_temp_c` / `target_junction_temp_c` | number | °C | `25` / `100` | 见共享温度 | 见共享温度 |

#### 三相两电平 VSI 与三相三电平 NPC

| 字段 | 类型 | 单位 | 两电平默认 | NPC 默认 | 最小/最大及关系 |
| --- | --- | --- | --- | --- | --- |
| `vdc_nom` | number | V | `700` | `700` | `(0, +inf)`，并满足调制可行性 |
| `vac_ll_rms` | number | V rms line-line | `400` | `400` | `(0, +inf)` |
| `f_line_hz` | number | Hz | `50` | `50` | `(0, +inf)` |
| `fsw_hz` | number | Hz | `20000` | `20000` | `(0, +inf)` |
| `pout_w` | number | W | `10000` | `10000` | `(0, +inf)` |
| `power_factor` | number | ratio | `1.0` | `1.0` | 两电平 `(0, 1]`；NPC 允许正负号且要求 `0 < abs(PF) <= 1`，还必须落在 design-basis PF 范围内 |
| `inductor_current_ripple_ratio` | number | ratio | `0.2` | `0.2` | `(0, +inf)` |
| `dc_link_voltage_ripple_ratio` | number | ratio | `0.05` | `0.05` | `(0, +inf)` |
| `ambient_temp_c` / `target_junction_temp_c` | number | °C | `25` / `100` | `25` / `100` | 见共享温度 |

NPC schema 还会在 `normalize_design_basis()` 中补全 Vdc min/max、环境上限、过载、deadtime、过压假设等工程 basis；这些是后端默认/请求扩展字段，不是当前 Tkinter 表单控件。

### 3.10 波形工作点字段

`OperatingPoint` 的纯 Python 契约是 `vin_v`、`load_ratio=1.0`、可选 `vout_v`、`power_factor`、`switching_frequency_hz`。各表单的可见字段如下：

| 拓扑组 | 可见字段与默认 | GUI/控制器处理 |
| --- | --- | --- |
| 经典 DC-DC、四开关、Flyback、PSFB | `vin_v`（各自 nominal/midpoint）、`load_ratio=1.0` | 转 float；拓扑 waveform/evaluator 再校验可行性 |
| TZCM | `vin_operating=400`、`load_ratio=1.0` | 转 float |
| LLC 两类 | `vin_v=vin_nom`、`vout_v=vout_nom`、`load_ratio=1.0` | 目标 Vout 驱动自动调频；load 必须 `(0,1]` |
| AC-DC 三种桥式、Boost PFC、Totem-Pole PFC | `load_ratio=1.0` | 表单把它夹到 `[0,1.0]`；输入电压取设计字段 |
| 单相/三相逆变器、NPC | `load_ratio=1.0`、`power_factor=设计值` | load 夹到 `[0,1.0]`，PF 夹到 `[-1,1]` |

注意：设计字段变化会使旧报告/效率结果失效；工作点字段变化走 fixed-hardware refresh，不得重新选择器件或磁件。

## 4. GUI 动作到 Pipeline 的真实调用链

### 4.1 Run Design

```text
BaseTopologyForm.get_raw_input()
  -> PEClawMainWindow callback
  -> RunDesignController.run_active_topology(raw_input)
  -> registry.get_plugin(topology_id)
  -> run_full_pipeline(...,
       include_waveforms=False,
       PipelineOptions(enable_magnetic_design=False,
                       enable_capacitor_design=False))
```

`run_full_pipeline()` 首先执行 `run_topology_pipeline()`：

1. `DesignRunContext.create()` 创建隔离的 run/output identity。
2. `plugin.build_spec(raw_input)`：解析、规范化、单位转换和校验。
3. `plugin.synthesize(spec)`：生成固定的 `TopologyCandidate`。
4. 若请求波形，`plugin.generate_waveforms(candidate, operating_point)`。
5. `plugin.extract_stress(candidate, waveform_set)`。
6. `plugin.evaluate(candidate, waveform_set, stress_result)`。
7. `plugin.build_report(...)` 生成初始 `DesignReport`。
8. 按能力执行器件选择和半导体几何；桥式整流器走专用 selector。
9. Run Design 控制器默认关闭磁件与电容阶段，因此初次点击不是“全部阶段一次跑完”。

### 4.2 Run Capacitor

`RunDesignController.run_active_capacitors()` 要求已有 candidate，调用 `run_capacitor_pipeline()`；它读取 spec/candidate、已有 waveform/stress/device（若适用），执行拓扑对应的输出/DC-link/分裂 DC-link/LLC Cr 选择，并生成 capacitor geometry 或角色化产物。LLC 在磁件前也可运行 Cr 选择，但最终闭环状态要求当前 run 推荐 bank 存在。

### 4.3 Run Magnetics

`RunDesignController.run_active_magnetics()` 依次调用：

```text
run_magnetic_pipeline(report)
  -> run_loss_pipeline(report, enable_magnetic_design=True)
  -> run_thermal_pipeline(report, enable_magnetic_design=True)
  -> run_geometry_pipeline(report, enable_magnetic_design=True)
```

磁件阶段产生候选、筛选/Pareto、chosen designs 和推荐 ID；损耗依赖 chosen magnetic design 与当前/设计工作点；热依赖器件/磁件/损耗；几何依赖已选磁件。LLC 要求 transformer 可用，external Lr 为 available/not_required/not_evaluated，否则阶段为 blocked。

### 4.4 Generate Waveforms

```text
form.get_operating_point()
  -> WaveformController.generate_waveforms()
  -> run_operating_point_refresh(existing_report, plugin, operating_point)
  -> plugin.generate_waveforms(existing candidate)
  -> plugin.extract_stress()
  -> plugin.evaluate()
  -> device operating-point refresh
  -> selected magnetic loss/thermal refresh（有固定磁件时）
  -> capacitor operating-point refresh
```

该路径明确复用 `report.candidate` 和已选 hardware；不会调用 `plugin.synthesize()`，也不会把缺失的器件结果升级成一次新选型。这是 Web API 必须保留的设计点/工作点边界。

### 4.5 Run Efficiency Sweep

`EfficiencySweepController` 要求已有 candidate，调用 `run_efficiency_sweep(report, plugin)`，在固定硬件上扫描 load（部分拓扑也扫描 PF），写回 `EfficiencySweepResult`。NPC 最后用全载点的周期初始电流刷新一次工作点。随后构建 Hardware Overview，并更新 run manifest/stage status；LLC 另写 LLC manifest。

## 5. 阶段顺序和依赖

通用“全阶段启用”顺序为：

```text
raw input
  -> spec/normalization
  -> synthesis candidate
  -> optional waveform
  -> stress + topology evaluation
  -> DesignReport
  -> semiconductor or bridge-rectifier selection
  -> semiconductor geometry
  -> magnetic design
  -> LLC capacitor (LLC 特例在 loss 前)
  -> loss
  -> thermal
  -> magnetic geometry
  -> non-LLC capacitor + capacitor geometry
  -> optional efficiency sweep
  -> hardware overview / validation / manifests
```

| 下游结果 | 必需上游 | 主要消费者 |
| --- | --- | --- |
| `spec` | raw input + input schema | synthesis、报告 request |
| `candidate` | spec + topology synthesizer | waveform、stress、器件/磁件/电容 |
| `waveform` | candidate + OperatingPoint | stress、器件工况损耗、电容工况、图表 |
| `stress` | candidate，通常加 waveform | 器件额定筛选、报告 |
| `device` | stress/candidate + semiconductor library + role policy | loss、thermal、hardware overview |
| `magnetic` | candidate/spec，部分拓扑加 waveform | loss、thermal、geometry、hardware overview |
| `capacitor` | candidate/spec，部分拓扑加 waveform/device | capacitor geometry、loss/efficiency、overview |
| `loss` | selected device/magnetic/capacitor + operating point | thermal、efficiency、报告 |
| `thermal` | loss + component thermal data + ambient/target | feasibility、overview、报告 |
| `geometry` | selected magnetic design | GUI geometry、overview、结构化报告 |
| `efficiency_sweep` | 固定 candidate 与已选硬件 | Efficiency view、overview、validation |

不能把所有拓扑强行套进完全相同的非空阶段：桥式整流器、单相逆变器 selection-only 分支、LLC、NPC 都有显式特例；缺失结果以 `not_applicable`、`not_evaluated`、`blocked` 或 unavailable 表示，不能伪造空数值。

## 6. 报告对象与结构化输出入口

运行中的唯一聚合对象是 `models/design_report.py::DesignReport`，主要字段为：

`spec`、`candidate`、`operating_point`、`waveform`、`stress`、`topology_result`、`device`、`semiconductor_geometry`、`magnetic`、`loss`、`thermal`、`geometry`、`capacitor`、`efficiency_sweep`、`system_validation`、run context、notes 及各阶段时间。

GUI result views 直接消费该 dataclass，不应该从 Markdown 或控件文本反向解析数据。

稳定结构化出口是：

- `reports.structured_output.build_structured_report(report) -> dict`：schema `pe_claw_structured_design_report_v1`，输出带 `{value, unit, source}` 的 quantity。
- `reports.structured_output.canonical_json(payload) -> str`：确定性 JSON 序列化。
- `reports.structured_output.render_markdown_report(payload) -> str`：由结构化 payload 渲染 Markdown。
- `reports.structured_output.flatten_quantity_rows(payload)`：用于字段级比较/导出。
- `scripts/generate_structured_report.py`：CLI/维护脚本级 JSON、Markdown 生成入口。

顶层 payload 包含 `topology`、`request`、`candidate`、`operating_point`、`waveform`、`stress`、`semiconductor_voltage_checks`、`magnetic`、`loss`、`efficiency_sweep`、`geometry`、`capacitor`、`thermal`、`hardware`、`ripple`、`status`、`audit`，以及适用时的 `topology_contract`、`semiconductor_topology`、`system_validation`、`llc_design_requirements`。

运行产物写入 run-scoped output root；`DesignRunContext`/LLC context 管理 identity、阶段状态、失败原因和 manifest。Web 层不得改用全局 `outputs/latest` 之类共享可变目录替代当前隔离策略。

## 7. GUI 专属代码与可复用纯 Python 边界

### 7.1 可直接复用

- `topologies/base/` 与 19 个插件：registry、capability、spec、synthesizer、waveform、stress、evaluator、report builder。
- `models/`：`TopologySpec`、`TopologyCandidate`、`OperatingPoint`、`DesignReport` 及各阶段结果 dataclass。
- `pipeline/`：设计、工作点刷新、器件、桥式整流器、磁件、电容、损耗、热、几何、效率和 manifest orchestration。
- `libraries/` 与 `engines/`：器件/电容/磁件数据、筛选、排序和工程计算。
- `reports/structured_output.py`：Web API/worker 应共同使用的稳定输出契约。
- `utils/ambient_temperature.py`、半导体 metadata normalization 等无 Tk 依赖 helper。

这些模块接收普通 dict/dataclass/path 并返回普通 Python 对象；Web 层应调用它们，而不是复制公式。

### 7.2 不能直接复用或只应提取声明数据

- `app/topology_forms/`：依赖 `tkinter`, `ttk`, `StringVar`, widget lifecycle 和回调；Web 不能实例化它们。字段声明目前与控件创建混在一起，可迁移为独立 schema/DTO，但校验权威仍应是 topology input schema。
- `app/shell/`、`app/category_views/`、`app/result_views/`：窗口、grid/pack、Notebook、Matplotlib Tk canvas、messagebox 与页面状态都是桌面专属。
- `app/controllers/`：其中编排意图可复用，但类本身持有 `AppStateStore` 并面向同步 UI callback。Web 应使用 service/job 层直接调用 pipeline，并显式持久化 state。
- `run_pe_claw_gui.bat` 与 `app/main.py`：只负责桌面启动，不是 Web server 入口。
- `ExportController.export_summary()`：是 GUI 轻量文本，不是完整报告契约；Web 导出必须走 `build_structured_report()`。

### 7.3 不能照搬的原因

1. Tk 变量是进程内、单窗口可变状态，不支持多用户、重试、worker 或进程恢复。
2. GUI 回调同步执行；磁件搜索、效率扫描等在 Web 中必须成为可跟踪 job，不能占用请求线程。
3. messagebox/按钮 enable state 不是 API 状态；应映射为 HTTP validation error、job stage/status 和可审计 failure reason。
4. result view 格式化会丢失 source/unit/availability 语义；结构化报告才是跨前端契约。
5. 表单中对 load/PF 的 clamp 是交互便利行为。Web API 应明确接受范围并返回规范化值或验证错误，不能静默产生与桌面不同的工程输入。

## 8. Web 接入建议边界

最小可复用 Web service 链应是：

```text
request schema
  -> topology registry lookup
  -> plugin.build_spec / run_full_pipeline
  -> persisted DesignReport/job identity
  -> staged capacitor/magnetics/efficiency actions
  -> run_operating_point_refresh for fixed hardware
  -> build_structured_report
  -> JSON response / artifact links
```

必须保留的契约包括稳定 topology ID、原单位、raw input snapshot、设计点与固定硬件刷新区分、确定性筛选排序、角色化器件 provenance、run-scoped artifacts、stage status，以及结构化报告的 `value/unit/source`。Tkinter 控件名称、布局、按钮状态和视图文本不属于后端契约。

## 9. 代码依据与验证入口

- 启动：`run_pe_claw_gui.bat`、`src/pe_claw_gui/__main__.py`、`src/pe_claw_gui/app/main.py`
- GUI shell：`app/shell/main_window.py`、`navigation.py`、`workspace.py`
- 表单：`app/topology_forms/base_form.py` 及 19 个注册 form class
- 注册与能力：`topologies/base/registry.py`、`topology_capabilities.py`
- 输入校验：各拓扑目录的 `input_schema.py`
- 管线：`pipeline/run_topology_pipeline.py`、`run_full_pipeline.py`、`run_operating_point_refresh.py` 及各阶段 runner
- 报告：`models/design_report.py`、`reports/structured_output.py`
- 相关回归：`tests/test_phase2_gui_bootstrap.py`、`test_phase10_gui_integration.py`、`test_phase10_structured_output.py`、`test_web_schemas.py`、`test_web_api.py`、各拓扑 contract/operating-point 测试

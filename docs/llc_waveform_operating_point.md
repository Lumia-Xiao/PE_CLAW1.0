# LLC 波形工况与自动调频

LLC 二极管整流和同步整流的 Generate Waveforms 根据 **Vin、目标 Vout、负载率**，在已设计的频率范围内自动求开关频率，再计算 FHA 波形。120 kHz 是默认设计的谐振参考频率，不是 GUI 工况的固定开关频率。

1. 运行设计，得到固定的 Lr、Cr、Lm、变比及器件。
2. 在 Waveform Operating Point 中填写 Vin、Target waveform Vout 和 load ratio，点击 Generate Waveforms。
3. 读取 Actual waveform Vout 和 Calculated switching frequency；图标题显示目标与实际电压、实际频率及负载。左侧可用滚动条访问下方工况控件。

例如默认全桥设计，目标 48 V、负载率 1：Vin=360/400/420 V 时，分别求得约 101.078/132.492/148.076 kHz；Vin=400 V、负载率 0.5 时约 134.107 kHz。频率与电流随工况变化，固定的设计参数及已选硬件不重新搜索。

负载率仍表示名义负载电阻的缩放：`Rload = Rnom / load_ratio`，`Rnom = Vout_nom² / Pmax`；功率约为 `Vout_target² / Rload`。因此改变目标 Vout 后，负载率不等同于额定功率百分比。本次不改变既有负载定义。

求解复用 LLC FHA 增益模型，在 fs_min/fs_max 范围内按增益峰值分段二分，包含端点和峰值切点；多解时确定性地选最高频率解。目标电压相对数值误差要求不超过 1e-8。此误差只描述 FHA 方程求解，不代表真实电路精度，也不保证 ZVS。

无匹配频率时显示输入工况和频率范围，清除旧图和旧结果显示；内部保留上次设计硬件以便修改工况后重试。输入变化会先清空实际读数。Vin、目标 Vout、负载率必须为正有限数；零负载控制不在此模型内。默认设计在 400 V、满载、80–180 kHz 内不能达到 36 V 或 60 V，必须调整工况或重新设计，不能继续展示 120 kHz 的旧图。

后端兼容接口：传入 Vout 且未指定 switching_frequency_hz 时自动调频；显式 switching_frequency_hz 优先，供固定频率诊断及既有硬件评估调用；未提供 Vout 的旧调用保留候选频率回退。显式固定频率模式不会假称达到输入目标 Vout。GUI 始终提供目标 Vout，不提供固定频率输入。

应力、器件当前工况损耗和电容工况频率使用本次波形，效率扫描保留目标 Vout。既有磁件候选损耗汇总并不等于全面重算任意工况下的磁件损耗，本次不扩展该模型。FHA 波形仍不包含真实死区、寄生振荡和开关瞬态。

结构化报告沿用原字段：`operating_point.output_voltage` 为输入目标，`operating_point.switching_frequency` 为可选显式频率输入（自动模式为 null），`waveform.operating.output_voltage` 和 `waveform.operating.switching_frequency` 为实际求解值。`candidate.switching_frequency` 仍是设计参考值，不能替代实际频率。

# LLC 波形工况

LLC 二极管整流和同步整流的 Generate Waveforms 使用固定开关频率 FHA 估算。

1. 先运行设计。设计区的 Vout min/nom/max 用于设计覆盖范围检查。
2. 在 Waveform Operating Point 中填写 Vin 和 load ratio，点击 Generate Waveforms。
3. 从 Actual waveform Vout 和 Actual switching frequency 读取本次计算结果。图标题也显示实际 Vout、频率及负载率。

Vout 由当前 Vin、负载、频率及已设计的谐振元件决定，波形工况中不提供目标 Vout 调节。更改波形输入时，实际读数清空，生成成功后重新显示。

负载率通过 `Rload = Rnom / load_ratio` 改变负载电阻，并不代表实际输出功率一定等于额定功率乘负载率。在谐振点改变负载时，电压可能不变，但电流会变化。各图自动调整纵轴，因此曲线外形相似时应比较刻度、数值和图标题。

当前界面不提供波形频率输入。后端仍支持 OperatingPoint.switching_frequency_hz；未指定时依次使用候选命令频率或候选默认频率。旧调用方的 OperatingPoint.vout_v 字段保留，但不控制 LLC 波形。

频率越界仍生成标记为诊断用途的波形，不能将其视为有效设计。零或负负载率保持旧接口的近似空载处理；波形只是 FHA 估算，不包含真实空载控制、死区、ZVS 过渡和寄生振荡。

工况刷新复用已选器件并重算当前损耗。若报告没有器件选型结果，只生成电气波形和应力并注明器件损耗刷新跳过，需运行设计取得器件结果。器件选型覆盖边界与当前工况损耗分别保留；SR 报告中的设计点 timing/loss 记录不会被当作当前工况数据。

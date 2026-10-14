# 三相三电平 T-type：电路、状态、导通与换流契约

- 日期：2026-10-13；版本：工作契约 v0.4（步骤 8 首轮贯通收尾）。
- 状态：步骤 0–8 已验证；T-type 第一轮基础链路已完成。证据和 Git 回执见实施计划第 9.14 节；后续真实工程范围仍未交付。
- 本轮授权：完成实施计划步骤 8；不处理真实器件、死区或换流能量、损耗/效率/热设计及完整工程导出。
- 拓扑 ID：`three_phase_three_level_t_type_inverter`；首轮 topology-only 注册与 GUI 已接入。
- 本契约选定常规 T-type、中点支路共源／共发射极连接；连接形式和驱动策略是本版明确的建模选择，不代表所有 T-type 变体。
- 首版目标：三相三线并网逆变、分裂直流母线、固定频率三电平调制、正向有功输出；正负瞬时相电流及无功交换必须建模。有源整流、反向平均功率、离网负载、闭环中点平衡和故障运行不属于本版实现目标。

## 1. 文档边界、依据和变更影响

本文件定义物理含义与字段契约；实际交付和验证以实施计划第 9 节回执为准。步骤 6–8 属于共享集成，接入注册/能力/表单、当前报告视图、运行点刷新和隔离验收；不新增公共报告字段或选型策略。各项后续目标不能因写入契约或首轮链路通过而视为已验证。

遵循 [公共工程语义契约](engineering_contracts.md) 和 [拓扑变更计划模板](../Plan/templates/topology_change_plan_template.md)。当前 NPC 的 [拓扑契约](../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/topology_contract.py)、[波形模型](../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py) 和 [事件损耗接口](../src/pe_claw_gui/engines/devices/loss_evaluator.py) 用于分析复用边界，不作为 T-type 导通或换流正确性的独立参考。

物理推导依据是第 2 节规定的连接、单向二极管约束、KCL/KVL 和电感伏秒积分。第 7 节换流表采用电流源近似和理想钳位路径；它没有寄生换流、双脉冲或硬件验证证据。器件损耗数值还必须依赖具体数据手册及其测试条件。

完整工程链的影响路径为：注册/能力/输入 → 合成 → 实际运行点波形 → 逐器件应力与选型 → 分裂母线电容/三相电感 → 损耗/热/几何 → 报告/GUI/扫描/导出。当前首轮只接入理想合成、波形、应力、报告与 GUI；组件及损耗阶段保持不可用。共享集成按实际依赖补充旧拓扑回归，旧注册与能力声明保留。

## 2. 电路、节点和器件方向

### 2.1 一相电路

三相 A/B/C 各复制下述桥臂；每相中点支路有自己的内部节点 `X_k`。

```text
直流母线：       P ── C_U ── O ── C_L ── N

一相桥臂 k：
                P
                │
               Q_P     正向通道 P → k；D_P：k → P
                │
                k ───────── L_k ───────── 电网相 k
                │
               Q_N     正向通道 k → N；D_N：N → k
                │
                N

中点支路：      k ── Q_A ── X_k ── Q_O ── O
                      D/C → S/E  E/S ← C/D
                  D_A：X_k → k   D_O：X_k → O
```

文字端子定义优先于简图中器件符号；简图不是 PCB、驱动或布线图。

| 器件 | 漏极 D / 集电极 C | 源极 S / 发射极 E | 正向通道电流 | 反并联／体二极管方向 |
|---|---|---|---|---|
| `Q_P` | P | 相节点 k | P → k | `D_P`：k → P |
| `Q_N` | 相节点 k | N | k → N | `D_N`：N → k |
| `Q_A` | 相节点 k | 内部节点 X_k | k → X_k | `D_A`：X_k → k |
| `Q_O` | 母线中点 O | 内部节点 X_k | O → X_k | `D_O`：X_k → O |

`Q_A` 与 `Q_O` 共源／共发射极，组成可阻断双向电压的中点开关。共漏／共集电极连接的器件方向与换流表不同，不能混用本表。

### 2.2 物理数量与包装

- 主支路：每相 `Q_P/Q_N`，三相共 6 个位置。
- 中点支路：每相 `Q_A/Q_O`，三相共 6 个位置。
- 合计 12 个主动开关位置；每位置对应自己的反向导通路径。不存在 NPC 的 6 个独立中点箝位二极管位置。
- 3 个独立相电感；2 个独立物理电容银行 `C_U/C_L`。
- 同型号可以复用，但 A/B/C、P/N/A/O 的物理身份不能合并。模块包装、每位置并联数量、内部二极管覆盖和散热耦合另行审计，12 个位置不等于 12 个独立封装。
- 拟议选型角色为 `t_type_main_switch`（6 位置）和 `t_type_midpoint_switch`（6 位置）。可在选型时按对称条件分组；损耗、应力和热读回保留全部物理位置，不能先平均 RMS 再当作每个器件相同。

## 3. 电压、电流、功率和工作条件

定义 `V_U = V_P - V_O > 0`，`V_L = V_O - V_N > 0`，`Vdc = V_U + V_L`。极点电压 `v_kO` 以 O 为参考；母线平衡时 `V_U = V_L = Vdc/2`。

相电流 `i_k > 0` 指桥臂节点 k 经电感流向电网；`i_k < 0` 指电网流回桥臂。三相三线理想模型要求 `i_A+i_B+i_C=0`。O 是直流母线中点，不能接作电网中性线。

正向平均有功输出为 `P_ac > 0`；瞬时负电流或负瞬时功率不等于反向平均功率。相位使用 `i_k = Ipk sin(theta_k-phi)`：`phi>0` 表示电流滞后，`phi<0` 表示超前。首版 `|phi|<pi/2`，`PF=cos(phi)>0`；超前/滞后独立记录，不能靠 PF 正负号代替该信息。

| 量 | 定义及单位 | 适用边界 |
|---|---|---|
| `V_LL,rms` | 电网基波线电压 RMS，V | 对称三相基波 |
| `V_phase,rms` | `V_LL,rms / sqrt(3)`，V | 与相电压定义对应 |
| `I_phase,1,rms` | `P_ac/(sqrt(3)*V_LL,rms*PF)`，A | 基波目标 RMS；含 PWM 纹波的实际 RMS 另算 |
| `m_grid` | `2*sqrt(2/3)*V_LL,rms/Vdc` | 平衡母线下电网基波的归一化量；不包含电感压降 |
| `v_cmd,k` | 电网相电压 + `L_k di_k/dt`，V | 理想相电感；绕组电阻加入后还需 `R_k i_k` |
| `m_cmd` | 平衡母线时命令电压峰值除以 `Vdc/2` | 需在完整运行点验证；`m_grid<=1` 不足以证明可调制 |

初版采用与现有 NPC 可对齐的固定频率、同相双载波三电平 PD-SPWM 基础及中心对齐相邻电平序列。相电压目标、共模和占空比生成必须明确一致；不将零序注入/SVPWM、过调制或闭环电流控制仿真默认为已支持。

对于三线系统：`v_k,phase = v_kO - (v_AO+v_BO+v_CO)/3`，`L_k di_k/dt = v_k,phase-v_grid,k`。电平序列、全部相位事件和实际选定电感必须共享同一时间轴。

母线不平衡时极点电平为 `+V_U/0/-V_L`；按对应电压计算占空比和电感积分。不能仍按 `±Vdc/2` 计算后声称已模拟不平衡。若实现仅支持平衡母线动态，则不平衡耐压包络可以独立审计，但必须把不平衡波形标为未支持。

## 4. 稳定状态与门极映射

门极向量顺序固定为 `(g_P,g_N,g_A,g_O)`；1/0 表示通道开通命令，不意味着该器件必然正向通道导电。

本版选定“保持非互补中点器件导通”的策略。它与 P/N 状态关闭两只中点管的另一种策略不同；后者需要重新推导换流，不属于本契约。

| 状态 | 门极向量 | 理想 `v_kO` | 理想内部节点 X_k | 保持导通但不承载相电流的器件 |
|---|---|---|---|---|
| P | `(1,0,0,1)` | `+V_U` | O | `Q_O` |
| O | `(0,0,1,1)` | 0 | k = O | 无；中点支路承载相电流 |
| N | `(0,1,1,0)` | `-V_L` | k | `Q_A` |

合法正常换流为 `P↔O` 和 `O↔N`。禁止直接 `P↔N`。改变使用的互补对必须经过 O，并满足门极时序；跨零点、零占空比及脉冲消失不能跳过此约束。

硬约束：`g_P*g_N=0`，`g_P*g_A=0`，`g_N*g_O=0`。违例会形成母线直通或半母线短路，必须显式拒绝。三项约束仅用于正常导通拓扑检查，不代替考虑延迟、尾电流和故障的驱动硬件设计。

## 5. 正负电流导通表

### 5.1 IGBT 加反并联二极管的参考路径

| 状态 | 电流方向 | 导通路径 | 有效正向通道／二极管 |
|---|---|---|---|
| P | `i_k>0` | P → k → 电网 | `Q_P` |
| P | `i_k<0` | 电网 → k → P | `D_P` |
| O | `i_k>0` | O → X_k → k → 电网 | `Q_O + D_A` |
| O | `i_k<0` | 电网 → k → X_k → O | `Q_A + D_O` |
| N | `i_k>0` | N → k → 电网 | `D_N` |
| N | `i_k<0` | 电网 → k → N | `Q_N` |

`Q_A/Q_O` 在 O 状态均有门极命令，但对 IGBT 不代表两只晶体管串联正向导通；其路径是一只 IGBT 加另一只的反并联二极管。

### 5.2 MOSFET 的区别

对具有相应能力的已开通 MOSFET，反向电流可以经第三象限通道导通：P/N 状态可由对应主开关反向通道承载；O 状态可以由两只中点 MOSFET 通道串联承载，一只正向、一只反向。体二极管可能在死区或通道/二极管分流时导通。

不能同时把全部反向电流计入通道损耗和二极管损耗。第三象限压降、温度、门极条件和是否采用通道/二极管分流近似，必须以器件模型能力为依据记录。IGBT 路径表不能无修改套入 MOSFET，也不能无依据把死区二极管导通抹掉。

基于所选连接，正常承载电流时的器件局部 D→S/C→E 有符号电流为：P 状态 `i_QP=i_k`；N 状态 `i_QN=-i_k`；O 状态 `i_QA=-i_k`、`i_QO=i_k`。实际通道和二极管电流按器件技术继续分解，其余非承载器件电流为零（本理想模型不含位移电流）。

## 6. 死区、互锁和实际电平

| 互补对 | 固定条件 | 死区门极向量 | `i_k>0` 的钳位路径/电平 | `i_k<0` 的钳位路径/电平 |
|---|---|---|---|---|
| `Q_P / Q_A` | `Q_O=1, Q_N=0` | `(0,0,0,1)` | `Q_O+D_A`，O | `D_P`，P |
| `Q_N / Q_O` | `Q_A=1, Q_P=0` | `(0,0,1,0)` | `D_N`，N | `Q_A+D_O`，O |

每次换流先关闭离开状态的互补器件，等待声明的 `t_dead`，再开通进入状态的器件。`t_dead` 单位为 s，来源需标为用户输入、设计假设或测量；不能继承 NPC 的某个默认值作为 T-type 硬件依据。

死区是实际电平区间，必须进入电感伏秒、导通时长和损耗。若选用“零死区理想电流＋单独死区损耗修正”的降阶模型，须作为另一明确模式报告，不能称为已经耦合的死区电流仿真。

短脉冲不足以容纳时序时，按明确的脉冲抑制/合并策略处理并记录目标与实际电压差，禁止产生负持续时间或重复事件。传播延迟、Miller 误导通、IGBT 尾电流和寄生过冲不由本理想死区表证明。

`i_k≈0` 时理想电流源不再唯一决定二极管钳位。采用有单位的零电流判定阈值并记录为待实现数值策略；不能按任意符号把它标为 ZVS。该区间若未加入 Coss/寄生模型，应标为换流类别未确定，损耗采用有依据的保守策略或显式不可用。

## 7. 八种相邻电平换流

下表适用非零电流、上述死区门极及理想钳位。`i_k` 在一次短换流内近似不变；实际事件电流应由事件时间轴上的电感电流求得。

“钳位后开通”只描述理想拓扑路径，不证明实物已完成 Coss 充放电或实现零开关能量。

| 换流 | 电流 | 关断 → 死区 → 开通 | 死区路径 | 强制承载换流的器件 | 可能发生恢复的二极管 |
|---|---|---|---|---|---|
| P → O | 正 | `Q_P off → dt → Q_A on` | `Q_O+D_A` | `Q_P` 带载关断；`Q_A` 钳位后开通 | 此过程不指定一次强制二极管恢复 |
| P → O | 负 | `Q_P off → dt → Q_A on` | `D_P` | `Q_A` 带载硬开通 | `D_P` |
| O → P | 正 | `Q_A off → dt → Q_P on` | `Q_O+D_A` | `Q_P` 带载硬开通 | `D_A` |
| O → P | 负 | `Q_A off → dt → Q_P on` | `D_P` | `Q_A` 带载关断；`Q_P` 钳位后开通 | 此过程不指定一次强制二极管恢复 |
| O → N | 正 | `Q_O off → dt → Q_N on` | `D_N` | `Q_O` 带载关断；`Q_N` 钳位后开通 | 此过程不指定一次强制二极管恢复 |
| O → N | 负 | `Q_O off → dt → Q_N on` | `Q_A+D_O` | `Q_N` 带载硬开通 | `D_O` |
| N → O | 正 | `Q_N off → dt → Q_O on` | `D_N` | `Q_O` 带载硬开通 | `D_N` |
| N → O | 负 | `Q_N off → dt → Q_O on` | `Q_A+D_O` | `Q_N` 带载关断；`Q_O` 钳位后开通 | 此过程不指定一次强制二极管恢复 |

在 IGBT 参考模型中，关闭一只处于反并联二极管承载方向的晶体管门极，不应自动算作该晶体管一次带载关断。在 MOSFET 模型中，反向通道关断转入二极管也需保留通道切换及其适用能量模型，不能照搬 IGBT 的零通道电流判断。

恢复能量属于实际受反向偏置的二极管换流过程；仅有门极跳变不能触发一份 `Qrr*V`。即使 SiC 器件少数载流子恢复很小，也不能据此把输出电容能量或所有反向换流损耗统一设零。

## 8. 静态阻断、额定耐压和事件电压

### 8.1 稳定状态的理想阻断电压

以下为器件 D-S/C-E 电压幅值，忽略导通压降。

| 状态 | `Q_P` | `Q_N` | `Q_A` | `Q_O` |
|---|---|---|---|---|
| P | 0 | `Vdc` | `V_U` | 0 |
| O | `V_U` | `V_L` | 0 | 0 |
| N | `Vdc` | 0 | 0 | `V_L` |

对应反并联／体二极管的反向耐压随其器件端子电压检查。主开关按全母线设计，中点开关按其实际半母线包络设计；中点同角色选型取 `Q_A/Q_O` 中更严的要求。

`V_required,j = (max_allowed_static_blocking_j + V_overshoot,j) * (1 + margin_j)`。

`max_allowed_static_blocking_j` 来自已声明的母线及不平衡边界。若边界已直接给出 `V_U,max/V_L,max`，不能再重复乘一次同含义的不平衡因子。过冲和裕量独立记录来源；未经测量的过冲值是工程假设。启动、全关断、故障及 X_k 浮动暂态不由该正常状态表覆盖。

### 8.2 事件电压

P↔O 的理想换流电压阶跃为该时刻 `V_U(t)`；O↔N 为 `V_L(t)`。器件事件记录需给出其实际开通前阻断电压或关断后的阻断电压及来源。钳位后开通的残余电压需要单独模型，不允许用“电流为负”直接推定为零。

额定全母线耐压不意味着主开关每次 PWM 都以全母线硬开通；反之，正常半母线换流不意味着主开关可以只选半母线耐压。

## 9. 逐器件事件、应力和损耗语义

本节是拟议语义，不定义当前 Python 报告的新字段。实现时以类型化适配器映射，保留旧拓扑字段含义。

| 数据 | 物理对象/单位/统计 | 生产者 → 消费者 | 刷新与缺项规则 |
|---|---|---|---|
| 工况身份 | 当前拓扑、run、硬件、母线、功率、频率、PF/相位及模型模式 | 运行点 → 全部结果 | 任一电气输入变化使波形及下游失效；不能借旧工况填缺值 |
| 三相电流 | 每相瞬时 A；周期平均、实际 RMS、峰值和局部纹波 A | 电感事件积分 → 应力/磁件/电容 | 使用固定已选 L；设计纹波目标不代替实际纹波 |
| 支路电流 | 12 位置；局部有符号 A；通道及二极管分量分别积分 | T-type 导通解析 → 器件损耗/热 | 瞬时路径缺失则对应损耗不完整；不得用全相 RMS 填全部位置 |
| 耐压包络 | 每位置最大阻断 V、要求额定 V、假设来源 | 拓扑/设计边界 → 选型/报告 | 按设计 envelope；不能用额定工况事件电压代替 |
| 换流事件 | 位置、互补对、前/死区/后状态、事件时刻 s、局部电流 A、端子电压 V、路径/类别/恢复对象 | T-type 时序解析 → 事件能量模型 | 电流正负以器件局部方向为准；不确定类别显式保留 |
| 事件能量 | 每事件 Eon/Eoff/Erec J，器件、温度、曲线及覆盖来源 | 已选器件曲线＋合法事件 → 损耗汇总 | 缺曲线需声明可用近似及依据或不可用，不能静默设零 |
| 导通损耗 | 每物理位置通道/二极管 W，完整线路周期平均 | 分段电流＋温度相关模型 → 热/系统损耗 | 通道与二极管不能重复承载全部电流 |
| 半导体总量 | 全部位置非重叠损耗之和 W | 每位置损耗 → loss/sweep/report/GUI | 缺任何必需位置则禁止完整系统效率 |
| 电容/电感损耗 | 2 银行、3 相实例 W | 已选硬件＋当前电流 → 系统损耗 | 实例完整、有限、同工况；阶段总量不代替运行点值 |

`P_cond,j = (1/T_line) * integral(v_channel,j*i_channel,j + v_diode,j*i_diode,j) dt`，每项采用其自身正功耗约定。MOSFET 的简单通道近似是 `Rds_on(T)*I_channel,rms^2`；IGBT/二极管需要相应压降曲线或有依据的分段近似。

`P_sw,j = sum(Eon_j + Eoff_j + Erec_allocated_j) / T_line`。

事件列表若已经覆盖全部物理位置，直接汇总并除以线路周期，不再乘位置数或 fsw。若角色接口要求单器件平均，先声明除数和成员，再乘回数量，检查与逐位置总和一致；非线性损耗不能用角色平均 RMS 替代逐位置计算。

应审查厂商 Eon 测试是否已包含对侧二极管恢复，并规定一次恢复能量只计一次。Coss、门极驱动、吸收、均压/放电电阻等是否纳入系统总量，必须有明确组件列表和证据；未建模应报告模型范围，不能伪装成物理零损耗。

现有共享 `evaluate_switching_event_energy` 将负局部电流的开通归为 soft turn-on。T-type 适配必须先核查路径、器件技术和残余电压；本契约不授权把该实现视为任意 T-type 事件的通用正确判据。

## 10. 分裂母线与功率守恒

定义 `J_P/J_O/J_N` 为从对应母线节点流入三相桥的总电流，按实际电平及死区路径累加，单位 A。

稳定状态的理想值：`J_P=sum(i_k where state=P)`，`J_O=sum(i_k where state=O)`，`J_N=sum(i_k where state=N)`。三线系统 `J_P+J_O+J_N=0`。死区采用第 6 节实际钳位电平，不采用门极目标电平。

电容正电流分别为 P→O、O→N；直流源正电流 `I_src` 定义为源向 P 供电并从 N 回流。忽略辅助负载时：

```text
i_CU = I_src - J_P
i_CL = I_src + J_N
i_CU - i_CL = J_O
dV_U/dt = i_CU/C_U
dV_L/dt = i_CL/C_L
```

两银行相等为 C 时，`d(V_U-V_L)/dt=J_O/C`。若二者不同，使用各自电容，不能继续套该简式。O 输出电流在模型中为 `J_O`；外部参考若把中点注入电流定义为 `-J_O`，比较前必须转换方向。

源电流模型必须显式声明。可采用“完整周期平均供电电流恒定”的一阶纹波模型，但它不是实际前级动态；母线电压强制恒定和按电容积分得到的动态电压也不能同时充当同一个自洽状态。均压电阻、辅助负载加入时重新写对应 KCL。

不得为了强制周期闭合，默默移除非零平均中点电流或重置电压。可移除已声明供电平均分量以计算纹波，但要保留原始电流、被移除分量和实际电荷不平衡诊断。

用于独立检查的无损功率恒等式：

```text
P_bridge = V_U*J_P - V_L*J_N
dW_C/dt = Vdc*I_src - P_bridge
dW_L/dt = P_bridge - sum(v_grid,k*i_k)
```

以上使用同一瞬时状态；加入导通、电阻或其他损耗后相应能量方程需加损耗项。不能用不同工况的设计包络损耗验证瞬时能量守恒。

每银行电流 RMS、纹波电压、额定电压和损耗分别交付。`Ceq=C_U*C_L/(C_U+C_L)` 仅表示串联等效电容；相等银行有 `C_bank=2*Ceq`。中点平衡控制能力不由两银行选型成功证明。

## 11. NPC 复用边界与结果所有者

| 当前来源 | 可复用内容 | T-type 必须独立拥有的内容 |
|---|---|---|
| NPC 输入/合成 | 三相功率、电压、基础频率、目标纹波及设计 envelope 方法 | T-type 连接、角色、耐压与模型模式；PF 超前/滞后不丢失 |
| NPC waveform | 经界定的电平序列、共模消除、统一事件积分、周期求解 | 门极、死区、导通路径、器件局部电流、换流事件及来源 |
| [器件角色](../src/pe_claw_gui/libraries/semiconductors/topology_roles.py) / [应力适配](../src/pe_claw_gui/engines/devices/stress_adapter.py) | 选型约束、确定性筛选、物理角色接口 | 主开关/中点开关两组新角色；12 位置与单实例边界 |
| [电容流水线](../src/pe_claw_gui/pipeline/run_capacitor_pipeline.py) | 两银行库搜索、选型、已选电容回写方法 | T-type 母线电流、选后刷新和不平衡边界；不假冒 NPC metadata |
| [NPC 电感审计](../src/pe_claw_gui/engines/magnetics/npc_output_filter_audit.py) | 检查项目和方法 | 真实 T-type 电感选型与当前波形；不能复制固定磁芯/匝数/参考损耗 |
| [运行点刷新](../src/pe_claw_gui/pipeline/run_operating_point_refresh.py) / [扫描](../src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py) | 固定硬件、当前结果和扫描流程 | T-type 路由、相位语义、事件数据和完整性检查 |
| [热流水线](../src/pe_claw_gui/pipeline/run_thermal_pipeline.py) | 逐器件功耗、场景与散热校核方法 | 与 T-type 包装对应的损耗/热阻/耦合假设；不继承 NPC 固定散热器及风量结论 |
| 报告/GUI/导出 | 已有框架、显示精度和当前报告所有权 | T-type 标识、两角色、12 位置、两银行、三电感以及缺项状态 |

拓扑层拥有电路、波形、应力和事件；库/引擎拥有已选器件及其曲线计算；流水线负责组合、刷新与失效。最终系统损耗和效率必须由当前报告中同一固定硬件、同一运行点的完整组件得出。

首版核心组件为全部半导体、3 相电感和 2 个母线银行的损耗；其他实际组件的纳入/排除需要逐项声明，报告效率应注明建模范围。核心结果：`P_loss=sum(required_components)`，`eta=P_ac/(P_ac+P_loss)`，仅适用正向平均输出且周期稳态。不能输出部分组件的“完整系统效率”。

## 12. 独立数值参考与后续验证

### 12.1 文档数值例子

例子用于复核定义，不是默认器件、默认输入或当前生产运行结果。

1. 对称 `V_LL=400 V`、`P_ac=10000 W`、`PF=1`：`V_phase,rms=230.940108 V`，`I_phase,1,rms=14.433757 A`，`Ipk=20.412415 A`。`Vdc=700 V` 时 `m_grid=0.933139`；实际命令还需电感压降。
2. `V_U=440 V`、`V_L=360 V`：P/O/N 极点电压是 `440/0/-360 V`；两主开关最大静态阻断为 800 V，中点 `Q_A/Q_O` 为 `440/360 V`。若仅为示例分别取过冲 50 V、裕量 20%，要求耐压为主开关 1020 V、`Q_A` 588 V、`Q_O` 492 V；这不是型号选定或实测过冲。
3. P↔O 换流阶跃为 440 V，O↔N 为 360 V；不能因为主开关要求 1020 V 就用 1020 V 代入每一次 Eon。
4. `C_U=C_L=1000 uF`、`J_O=2 A` 持续 `10 us`：上下电压差增加 `0.02 V`。该差值由 KCL 得到，不代表具体前级供电模型。

### 12.2 实现前和实现后的门槛

下表保留 v0.1 撰写时的完整工程门槛；当前首轮子集的实现和实际验证见第 14 节及实施计划 9.14。

| 证据类别 | 必需检查 | v0.1 撰写时状态 |
|---|---|---|
| 公式/电路 | 端子表与连接图一致；3 状态×2 电流方向；8 种换流；局部符号；静态与事件电压；母线 KCL/能量 | 文档推导与数值复核；无生产实现验证 |
| 独立参考 | 用手算分段解或独立开关电路模型核对事件时刻、换流对象、电压和电流；不只比较 NPC/T-type 同一个 helper | 待实现阶段执行 |
| 契约/负向 | 非法门极、直接 P↔N、短脉冲、零电流、母线无效、缺曲线/角色/电容/电感、非有限和旧工况注入 | 待新增并执行 |
| 真实库 | 一个完整代表案例尽早跑通选型、损耗和导出；记录搜索扩大/耗尽、包装和真实数据来源 | 待实施计划确定案例和执行 |
| 运行点 | 低/额定/高母线、轻/半/满载、超前/滞后 PF、调制边界；硬件保持固定；模型不支持点显式阻塞 | 待实施；不能把全部输入矩阵自动认定为有效 |
| 用户链路 | GUI 当前数值、原始总损耗/效率、扫描及 JSON/CSV 同工况匹配 | 待实现并执行 |
| 隔离/旧拓扑 | NPC→T-type、T-type→NPC 并重复；共享组件受影响旧拓扑最小回归，必要时扩大范围 | 待实现并执行 |

电压/电流/能量分别设有单位的绝对及相对容差；标识和角色数量精确比较；近零量使用绝对容差。具体容差和矩阵放入实施计划，不能把本节例子的显示位数当作统一验收精度。

相同电平序列、母线、电感、电网与时间轴下，NPC/T-type 的无死区理想输出侧波形可做一致性检查。它不能验证 T-type 内部器件路径、换流、器件耐压、损耗或物理可采购性。

### 12.3 明确的待验证/待选择项

- 首个真实案例器件技术、主/中点型号及是否支持混合技术；完整数据手册曲线、第三象限模型、恢复能量覆盖和封装配对。
- 死区值、最短脉冲处理、零电流阈值、传播延迟及所需降阶模型；硬件 ZVS、Coss 和寄生暂态仍无证据。
- 支持的母线/PF/负载范围、不平衡动态与闭环平衡扩展；基波可行不等于 PWM 电感压降后可行。
- 电容源电流模型、损耗/热/辅助组件范围、实际磁件/散热/体积模型及精度。
- T-type 的类型化适配、公共字段映射、真实选型、实现测试和 GUI/导出证据。本版不把这些写成已完成。

上述未决项不阻止形成此份电路与换流契约；相应数值实现、选型或工程结论必须在使用前落实，不得静默沿用 NPC 假设。

## 13. v0.1 契约撰写检查与 Git 范围（历史记录）

- 基准：`6c6a1d81ea0471d9efbbd424280285e529fbcb04`；分支 `codex/llc-waveform-operating-point-plan`；沿用已配置上游 `pe-claw-1.1/codex/llc-waveform-operating-point-plan`。
- 初始工作区已有 95 项 tracked 删除及 2 项无关 untracked，均不纳入本次文档提交；保留用户 outputs、证据和库数据。
- 文档检查：连接/状态/导通/死区/换流/耐压表交叉审查；独立 Python 标量复核第 12.1 节；本地 Markdown 链接存在性；ChangeLog append-only；定向及暂存 `git diff --check` 和差异审查。
- 不运行 pytest、收集、电气链、GUI 或拓扑验收；本轮不生成工程黄金参考。提交/推送结果以实际 Git 回执为准。

## 14. 步骤 0 冻结且首轮已实现的接口

本节与 [实施计划](../Plan/completed/three_phase_three_level_t_type_implementation_plan.md) 共同规定第一轮子集；第 2–5 节电路与方向继续有效。第 6–10、12 节中有限死区、器件能量、动态电容、真实选型、系统效率及完整导出属于后续工程扩展，不作为第一轮门槛。本节输入、合成、波形、应力和刷新映射已实现；实际验收范围以 14.4 和计划回执为准，步骤 0 的 NPC 回执仍不能单独证明 T-type 正确性。

### 14.1 输入、规格与运行点

已实现 `LEGACY_KEY=ThreePhase_ThreeLevel_T_Type_Inverter`，显示名称 `Three-Phase Three-Level T-type Inverter`。raw input 保持字符串映射，经本拓扑解析器生成有限 SI 数值；不调用 NPC 的完整 design-basis 解析器带入死区、过冲或器件默认值。

| raw 键 | 默认值 / 单位 | 规范化及边界 |
|---|---|---|
| `vdc_nom` | 700 / 总母线 DC V | >0；首轮固定设计母线，无 min/max 工程包络 |
| `vac_ll_rms` | 400 / 基波线电压 RMS V | >0；电网电压固定于该次设计 |
| `f_line_hz` | 50 / Hz | >0；电网基频，不增加独立 `f_output_hz` |
| `fsw_hz` | 20000 / Hz | >0；首轮要求 fsw/fline 为正整数，完整线路周期包含整数载波周期；非整数比显式拒绝，后续再扩展 |
| `pout_w` | 10000 / 三相总有功 W | >0；不接受反向平均功率 |
| `power_factor` | 1 / 幅值 | 0<PF≤1；负 PF 不表示超前，与 NPC 负 PF 反向功率兼容语义分开 |
| `power_factor_phase` | `lagging` | 仅 `lagging` / `leading`；有符号滞后角 φ=+acos(PF) / −acos(PF)，PF=1 时 φ=0 |
| `inductor_current_ripple_ratio` | 0.2 / ΔIpp/I1pk | 0<r<2；设计估算目标，不是实际纹波承诺 |
| `dc_link_voltage_ripple_ratio` | 0.05 / ΔVdc,pp/Vdc | 0<r<1；仅用于标量电容估算，不模拟母线纹波 |

原始输入缺项使用本表默认；格式错误、非有限或越界值用 `ValueError` 指明字段和原因。未知键不进入电气计算；不接受非零死区或其他非理想模型参数后仍声称支持。若调用者显式要求未支持模型，返回带原因的拒绝。首轮无器件筛选/温度输入控件，不复制 NPC 的隐藏工程参数。

`TopologySpec`：`vin_min=vin_max=vdc_nom`，`vout=vac_ll_rms`，`pout=pout_w`，`fs_khz=fsw_hz/1000`，`ripple_current_ratio=r_i`，`ripple_voltage_ratio_percent=100*r_v`。`spec.metadata` 保留 `vdc_nom_v/vac_ll_rms_v/f_line_hz/fsw_hz/power_factor/power_factor_phase` 和两个 ratio；模型/范围与连接采用 `t_type_contract` 和 `t_type_model_scope` 局部键，不写 `npc_*`。

沿用现有 `OperatingPoint`，不新增共享字段：

- `vin_v` 是本次实际总母线 V；未提供 operating point 时采用 candidate 设计母线。>0 且有限，不用旧 nominal 覆盖它。
- `load_ratio` 在 [0,1]；P_actual=P_design×load_ratio；超出拒绝，不静默裁剪。零负载只表示基波有功参考为零，PWM 电感电流仍可能有纹波。
- `power_factor=None` 使用设计 PF，否则验证幅值；`power_factor_phase` 固定于 candidate，本轮换相位类型需要重新设计。
- `vout_v=None` 或等于设计 VLL；`switching_frequency_hz=None` 或等于设计 fsw。改变网压/频率不属于首轮刷新，显式拒绝，不忽略覆盖请求。
- 表单运行点母线使用独立控件 `operating_vdc_v`，默认 700；该控件及运行点 load/PF 不进入 `get_raw_input()`，只进入 `get_operating_point()`。改变设计字段触发重新合成，改变运行点控件保留 candidate 和 L。

### 14.2 合成公式与候选映射

独立参考：V1,rms=VLL/√3；I1,rms=P/(√3·VLL·PF)；I1,pk=√2·I1,rms；ΔI_target,pp=r_i·I1,pk。相邻 pole-to-O 电平阶跃 ΔV=Vdc/2，单个中心对齐脉冲在常量平均电压近似下有 ΔIpp=ΔV·d(1−d)/(fsw·L)，d=1/2 取最大，得到：

```text
L_initial = Vdc / (8 * fsw * ΔI_target,pp)
I_phasor = I1,rms * (cos(φ) - j*sin(φ))
V_inv,phasor = V_grid,phase,rms + j*2π*fline*L_initial*I_phasor
m_command = 2*sqrt(2)*abs(V_inv,phasor)/Vdc
```

该 L 是单极点纹波初值。三线系统还有共模消除、其他相的切换和电网变化，因此不称它为三相实际纹波上界。NPC 当前保留历史 `Vdc/(16*fsw*ΔIpp)`，T-type 采用独立初值公式；本轮不修 NPC、不改变其快照。比较输出侧求解时必须显式令 L 相同，不能用相同设计输入推断 L 相同。基波 m_command≤1 只是必要可行性，分段求解实际平均命令仍须单独检查；饱和/未收敛点不得伪装达到目标。

首轮选择交付电容标量代理，以满足既有 candidate 必填数值，采用并明确标注假设充电量尺度 Q_proxy=2·I_dc,avg/fsw：Ceq_proxy=Q_proxy/ΔVdc,pp，Cbank_proxy=2·Ceq_proxy；I_dc,avg=P/Vdc。该式是沿用 NPC 的初始估算政策，不是根据真实源电流积分得到的最低电容要求，不证明纹波达标。两个相等银行的串联关系可独立验证；不创建已选电容结果。GUI 仅显示“每银行初始估算”。

| candidate 字段 | 首轮含义 / 所有者 |
|---|---|
| `vin_min/vin_max/vin_nom`、`vout_target/pout_target/fs_hz` | 设计母线、设计 VLL RMS、三相额定有功、设计 fsw；不随刷新改写 |
| `inductance_h` | 每相 L_initial，3 个相同理想 L；不是三相总 L或实物磁件 |
| `capacitance_f` | 一个银行 Cbank_proxy；2 银行；不是 Ceq 或银行之和 |
| `iout` | 每相基波 I1,rms；不是系统 DC 输出电流 |
| `delta_il`、`delta_vo/output_ripple_vpp_v` | 设计 ΔI_target,pp A、总母线纹波目标 Vpp；后者不是实际输出 AC 纹波 |
| `il_peak/il_valley` | ±(I1,pk+ΔI_target,pp/2) 估算包络，不是刷新后的实际极值 |
| `duty_nom` | 0.5 兼容载波中值；不能作为真实三相占空比展示，实际 d+/d0/d− 放局部载荷 |
| `ccm_valid` | 与既有 AC 候选一致的 ΔI_target,pp<2·I1,pk 设计启发式；不证明交流过零时的 DC CCM，也不用于裁剪电流 |
| `mode_capable`、`feasible` | 本拓扑理想 PD-SPWM 模型说明、当前可行性；feasible 不能替代完整波形检查 |

`candidate.metadata["t_type_design_estimates"]` 保存上述估算、公式 ID、单位/数量、相位、主/中点静态电压及逐位置保守电流估计；刷新不修改该字典。`t_type_model_scope` 显式声明 ideal/zero-deadtime/balanced-bus/unselected-components/unmodeled-losses。

B1 独立标量参考：L=1.071651762 mH/相，ΔI_target,pp=4.082482905 A，Ceq_proxy=40.816326531 μF，Cbank_proxy=81.632653061 μF，m_command≈0.933345504。B3 两次 PF=0.8 设计各自 L=0.857321410 mH，滞后/超前 m_command≈0.945050474/0.921491868。解析参考及实际合成回执见实施计划 9.8/9.11。

### 14.3 波形、应力与报告字段

`WaveformSet.metadata["three_phase_t_type_pd_spwm_waveforms"]` 是三相完整载荷的唯一绘图来源；当前采用 `waveform.py` 生成的拓扑局部字典，`stress.py` 校验和读回，不改共享模型：

- `schema_version=1`；`basis` 含实际 `vdc_v/vac_ll_rms_v/pout_w/load_ratio/power_factor/power_factor_phase/fsw_hz/f_line_hz/inductance_h/model_scope`，全部单位固定；线路周期和窗口随载荷记录。
- `time_s`；`phases.a/b/c` 各有 `state`（+1/0/−1）、`pole_to_o_voltage_v`、`phase_neutral_voltage_v`、`grid_voltage_v`、`current_a`、`reference_current_a`、`inductor_voltage_v`、`gates.QP/QN/QA/QO`；线电压在 `line_line_voltage_v.ab/bc/ca`。
- `segments` 包含统一 t_start_s/t_end_s、三相 states、start/end currents、平均命令、占空序列；积分用精确事件片段，不把只采样 8 点当作事件积分。
- `positions.a_QP` 等 12 项含局部有符号端子电流、非负 `channel_current_a/antiparallel_diode_current_a`、`static_blocking_voltage_v` 及完整周期 peak/RMS/average 指标。正局部电流走参考晶体管，负值走该位置反并联二极管；精确零值无承载路径。
- `events` 含 time_s/phase/from_state/to_state、切换位置及 on/off、相电流/局部电流、方向/参考承载路径、半母线 level_step_v 和 ideal 类别；不填能量、恢复能量或 ZVS。逐位置翻转与相邻状态事件区分，禁止 P↔N。
- `diagnostics` 含周期收敛/残差、实际命令可行性、目标/实际纹波与积分方法；`stress` 含 `basis=waveform_actual`、12 位置指标及 main/midpoint 两组逐指标最大值包络（非总电流）。任何缺项/非有限/未收敛使当前结果无效，不回填设计数组。

电流 RMS/平均取完整线路周期时间权重，signed 平均与 channel/diode 非负平均分开。实际纹波按每周期电流减去基波参考后的 peak-to-peak 记录及其定义，不混成全周期最大减最小。展示采样点取统一事件边界加每载波 8 个均匀点；必要时加密并证明积分收敛。首轮不模拟电容电流/动态电压。

| WaveformSet 兼容字段 | 精确映射 |
|---|---|
| `time_s` / `time_span_s` / `switching_period_s` | 同局部时间轴 / 1/fline / 1/fsw |
| `switch_node_voltage_v` | A 相 pole-to-O 瞬时电压 |
| `inductor_current_a`、`inductor_voltage_v` | A 相电感电流、去共模相电压减电网 A 相电压 |
| `output_voltage_v` | A 相电网瞬时相电压；页面明确相电压，不能与线电压混用 |
| `operating_vin_v/operating_vout_v` | 实际总母线 DC V / 固定电网 VLL RMS V；后者与瞬时数组统计类型不同 |
| `inductor_current_min_a/max_a` | 当前 A 相完整周期实际极值 |
| `switch_current_a/diode_current_a` | A_QP 非负 channel 电流 / 该位置 DP 非负承载电流；不代表 12 位置总量 |
| `gate_s1/s2/s3/s4` | A 相 QP/QN/QA/QO；完整 12 路从本拓扑载荷读取 |
| `load_ratio/duty/mode` | 实际负载 / 0.5 兼容载波中值 / 本拓扑三相理想周期模式，注释说明不作 DC 占空或 CCM 判据 |
| `capacitor_current_a/input_source_current_a/output_ripple_v/vox_voltage_v` | 空列表并在 notes 明示未建模；不填全零假波形；T-type 专用视图跳过它们 |

`StressResult.switch` 是 12 个参考晶体管位置各指标独立最大值包络；`rectifier` 是实际反并联二极管路径包络，**不改名中点开关、不创建 NPC clamp**。voltage_max_v 为相应位置静态阻断上限，main=Vdc、midpoint=Vdc/2；器件额定值/过冲未评估。首轮 `role_voltage_checks={}`，避免借 NPC 电压裕量类型伪造选型通过。无波形时电流 peak 仅给 I1pk+ΔI_target/2 保守估算，RMS/average=None，notes 标估计；有波形时从同一局部指标获得真实时间积分值。逐位置/主中点视图读取本地 `readback`：优先当前 waveform 的 stress，只有确实尚未生成波形时读取 candidate 的 design estimates；失效/失败波形不能回退冒充有效运行点。

`DesignReport` 保持 spec/candidate/waveform/stress/topology_result/current operating_point；无波形也可给估算说明。`device/capacitor/magnetic/loss/thermal/geometry/semiconductor_geometry/bridge_rectifier/efficiency_sweep` 全为 None、阶段未运行有理由，不生成零损耗或 100% 效率。报告组装/evaluator 所有权在 T-type 包；GUI 从当前 state report 读回。运行点失败保留可恢复的固定 candidate，清除有效当前波形及页面；步骤 6/7 补所需局部能力保护，不修改旧拓扑失败语义。

生命周期：设计输入改变使 candidate 与所有依赖数据失效；母线/load/PF 改变使当前 waveform/stress/topology_result 失效但保留 candidate；换拓扑清除本拓扑载荷。每次刷新生成新不可混用载荷，不原地修改旧 report/candidate。缺项、非法状态或不收敛保留具体原因，不声明有效/完整结果。

步骤 7 实现：first-pass 刷新先检查 spec/candidate/plugin 标识，生成后调用拓扑的 build_report 核验请求与当前载荷，再仅替换原报告的运行点/波形/应力/评估。原 run_context、设计计时和设计估算保留；控制器检查所选拓扑与报告来源。T-type 报告校验 candidate 与 spec 的规范化设计数据，并核对 L/C 与原设计估算；不能混入另一设计或手改参数的来源。电网 VLL 与开关频率仍固定，等值请求的绝对容差分别为 1e-9 V 和 1e-12 Hz，与波形入口一致。

身份检查覆盖双向混用，只要 spec/candidate/plugin 任一是 first-pass T-type，就不能在三者身份不一致时进入求解或下游。运行点刷新要求非空当前 waveform；缺失时明确拒绝，不能使用 Run Design 的无波形估算报告作为刷新成功结果。

T-type 表单的三个运行控件写入时，Workspace 立即清空 state report 的 operating_point/waveform/stress/topology_result，并清空页面，保留 spec/candidate/run_context/设计记录；随后 Generate Waveforms 只刷新运行点。失败保留具体错误，仍可使用原 candidate 恢复。该失效回调仅接入 first-pass T-type，旧拓扑沿用原交互。

### 14.4 验证来源与当前状态

数值容差、NPC 共享抽取名单及基准见实施计划步骤 0；步骤 1–5 的公式、导通/理想事件、实际波形、时间积分应力和基础报告回执见 9.7–9.11。步骤 6 GUI/注册证据记录于 9.12；步骤 7 刷新测试与实际回执记录于 9.13：累计 377 项、收尾 38 项及 candidate-only 来源保护补充 4 项均实际通过，且为不同修订的明确执行范围。步骤 8 聚焦 7 项、首组累计 283 项及补充旧消费者 143 项均实际通过，0 failures/errors/skips；两组共 426 个不同项覆盖最终默认清单，生产源码相同，非一次 full suite。NPC 六份完整 payload SHA 在各次运行中精确不变。GUI/报告证据只覆盖当前首轮的设计、波形、应力、运行点刷新和 bounded L/C 摘要；未覆盖真实器件、死区/换流能量、损耗/效率/热、完整工程导出或 full suite。初版收尾状态过早，已按补齐门禁后的实际结果修正，详见计划 9.14。

## 15. 第二轮步骤 0 冻结的工程接口（2026-10-13）

依据 [第二轮工程链接入计划](../Plan/Active/three_phase_three_level_t_type_engineering_integration_plan.md)。本节是实施合同，不代表以下新类型、字段、能力或选型已实现。步骤 0 仅核查现有接口、生成基线和执行合同探针；第 14 节首轮生产行为不变。

### 15.1 模型范围和最小真实器件路径

- 第二轮损耗范围 ID 冻结为 `t_type_conduction_magnetics_capacitors_v1`，与首轮电路 `model_scope` 分开。包含通道/反并联二极管导通、三相电感铜/磁芯、上/下银行既有 ESR 损耗。
- `excluded_components` 精确记录 `switching_on`、`switching_off`、`reverse_recovery`、`output_capacitance`、`gate_drive`、`control_auxiliary`、`fan`、`snubber`、`equalizer`、`precharge`；状态 `not_modeled`，不报告物理零功耗。热和排名必须标相同范围；效率为范围内估算。
- 两角色名 `t_type_main_switch`（QP/QN，各相 2 个，共 6）、`t_type_midpoint_switch`（QA/QO，共 6）。设计静态最大 main=Vdc,max、midpoint=Vdc,max/2；overshoot 未建模，沿用既有 20% 电压 margin 和 10% 电流 margin，不冒充实测过冲。额定电压不能用作事件能量电压。
- 首个实物路径采用库内 ROHM RG 带 FRD 的离散 IGBT：同时要求 `RohmRGIGBTDevice.has_frd`、IGBT/FRD conduction table 存在、额定及热/结构过滤成立。不带 FRD 记录的 `frd_vf_V` 当前返回 0，该返回不能作为有效二极管模型；应排除并记录原因，不能补零通过。
- 已核查 Mitsubishi `vce_sat_V` / `vec_V`、ROHM `vce_sat_V` / `frd_vf_V` 可独立访问导通表，不调用 `eon/eoff/err`。Mitsubishi 与模块 section 复用以终端映射已验证为条件；普通共集电极半桥不能直接组成共发射极中点支路。最小离散路径不等待模块组合；未验证模块须 `unsupported_package_connection`，不宣称所有模块可用。
- 厂商过滤默认 Any，技术限定 IGBT；并联方案沿用每位置 n=1/2/3，同方案两组同 n，型号可分别选择。筛选/评分/方案优先级沿用公共政策；器件基础模型与库不改。

### 15.2 类型化结果和物理字段字典

拟新增 `models/t_type_engineering.py` 中冻结 dataclass，通过 `DesignReport.t_type_engineering: TTypeEngineeringResult | None` 承载（均待后续实现）。拓扑适配拥有 `topologies/dc_ac/three_phase_three_level_t_type_inverter/engineering_adapter.py`；公共模型仅放类型，不放公式。`engineering_result` 在第二轮 JSON 为顶层新节；旧 schema 必填/字段语义保持。字段均有明确 status/source，不靠自由 notes 承载完整性。

| 拟定精确类型/路径 | 物理含义、单位/统计 | 来源、消费者、生命周期与缺项 |
|---|---|---|
| `TTypeEngineeringResult.schema_version` / `loss_scope_id` / `excluded_components` | 1 / 上述范围 ID / 排除项 tuple | adapter→全部组件/页面/导出；范围不匹配拒绝，不替代电路 waveform model_scope |
| `.design_basis: TTypeDesignBasis` | topology/run/candidate fingerprint、额定 P/VLL、fline/fsw、phase、vdc_min/max、pf_min/max、load_min/max、temperature/margins、case tuple | spec/candidate＋工程输入→选择 envelope；设计输入改动整套失效；不得由运行点反写 |
| `.hardware: TTypeHardwareSnapshot | None` | hardware_id、两角色 devices、三相 inductors、banks.upper/lower、packages | 已选组件→waveform/refresh/thermal/geometry；ID 由稳定工程内容哈希生成，排除 run 时间；缺实例不能生成完整快照 |
| `TTypeSelectedDevice.role/part_number/parallel_count/position_ids` | 型号/n/6 个唯一位置；每角色物理 switch section=6n | selection→封装/逐位置损耗；数量与采购封装区分，FRD 已属位置、不增 clamp BOM |
| `TTypeSelectedPackage.package_instance_id/part_number/member_position_ids/section_bindings` | 单采购封装、实际映射的 section/位置 | package adapter→geometry/BOM；离散每位置/n 各独立；模块终端映射缺失拒绝，不用 ceil(位置数/模块开关数) 推定 |
| `TTypeSelectedInductor.phase/design_id/inductance_h/turns/parallel_bundles/stack_count` | a/b/c 三实例、实际每相 H/绕组；model 可相同，instance 不同 | MagneticResult.selected_design_id→硬件→刷新；库 virtual/catalog/source 逐项保留，选择后不能改变绕组 |
| `TTypeSelectedBank.side/part_number/series_count/parallel_count/capacitance_f` | upper/lower 银行，S/P、实际每银行 F | CapacitorSelectionEntry→hardware→纹波/损耗/几何；C_U/C_L 独立，Ceq 仅派生，不重定义 candidate Cbank_proxy |
| `.operating_basis: TTypeOperatingBasis | None` | topology/run/candidate fingerprint/hardware_id/scope、vdc_v/VLL/有功 W/load/PF magnitude/phase/fline/fsw/L_H/C_U_F/C_L_F | 当前求解与硬件快照→全下游；每次刷新新对象，任意来源不符清当前有效结果 |
| `.position_losses: tuple[TTypePositionLoss,...]` | position_id、role、n、per_device_channel_w、per_device_diode_w、position_total_w、reference_tj_c/source/status | 完整线路周期逐位置积分→role/scope/thermal；position_total=n*(channel+diode)，12 唯一位置全覆盖 |
| `.role_selection_reference: dict[str,TTypeRoleSelectionReference]` | 本设计 envelope 内最坏单器件导通 W/结温/位置/case，选型用包络 | selector callback→排名/设计页；不将最坏值×6当当前真实损耗；chosen envelope 来源必须保存 |
| `.split_link: TTypeSplitLinkResult | None` | `time_s/j_p_a/j_o_a/j_n_a/source_current_a/i_cu_a/i_cl_a/upper_voltage_ripple_v/lower_voltage_ripple_v`，各 mean/RMS/q_drift_C | 当前状态/事件电流→两银行 selector/刷新；原始均值和漂移保留，缺时间/不周期不可用 |
| `.system: TTypeScopeSystemResult | None` | `components_w/status/missing_components/total_loss_w/efficiency_ratio/output_power_w/basis/source` | 当前全部组件→Summary/Loss/Sweep/Export；完整才 total/eta；不借 report.loss 的磁件小计发布系统量 |
| `.stage_status` / `.diagnostics` | device/magnetics/capacitors/hardware_refresh/system/thermal/geometry/sweep/export 的既有状态语义及原因 | pipeline→GUI/report；nonnull/complete 标志不代替检查；未开放阶段 not_started/blocked 有原因 |

`hardware.inductors` 初版只接受三相相同 L 的设计（明确实例）。不相同 L 不属于现有 solver 模型，拒绝而非取平均。原 `report.candidate.inductance_h/capacitance_f` 和 design_estimates 保持首轮设计目标/初估；实际 L/C 只来自 hardware。step4 拟建内部 effective-candidate 视图供旧波形计算接口，禁止改原对象。报告/波形校验新增 hardware-aware 分支核查 effective 参数与 snapshot；不能沿用首轮“L 必须等于初始估算”的断言接受实际选后参数，也不能跳过来源检查。

波形局部 `schema_version=1` 的电气字段保持兼容；工程模式新增 `basis.hardware_id/loss_scope_id`，basis.inductance_h 是实际求解 L，固定 candidate 本身仍是设计目标。纯首轮结果没有这些字段，不可冒充已选硬件报告。硬件读回先校验后原子发布，失败只保留选定硬件和诊断，清 operating/system/sweep/export。

### 15.3 共享请求、回调与精确适配接口

以下函数均为拟新增入口，步骤 0 不实现生产 adapter：

```text
engineering_adapter.build_device_selection_requests(report, design_basis)
    -> tuple[SwitchStressCase,...] + 逐 case/位置非线性导通积分请求
engineering_adapter.build_inductor_design_request(report, design_basis)
    -> 现有 InductorDesignRequest
engineering_adapter.build_inductor_operating_request(report, hardware, operating_basis)
    -> 现有 InductorOperatingPointRequest
engineering_adapter.build_split_link_result(report, hardware_or_design_capacitance)
    -> TTypeSplitLinkResult
engineering_adapter.build_capacitor_requests(report, split_link, design_basis)
    -> (upper_CapacitorSizingRequest, lower_CapacitorSizingRequest)
engineering_adapter.build_effective_waveform_candidate(report, hardware)
    -> 私有只读参数视图（实际 L/C），不重选、不覆盖 design candidate
engineering_adapter.validate_operating_sources(report, hardware, operating_basis)
    -> 成功或字段/来源明确的 ValueError
```

- 公共 `SwitchStress` 角色选择字段冻结：`v_block_V` 为该组静态设计 envelope；`i_rms_A` 为每位置 channel/diode 所需连续电流保守包络，`i_avg_A` 为通道非负完整周期平均参考；`i_turn_on_A/i_turn_off_A` 在当前公共 filter 无独立 peak 字段的兼容桥中承载 peak 上限，mode/notes 明示 `selection_peak_bound_no_energy`，不作为事件能量依据。`body_diode_conduction_time_s` 是完整周期 diode 承载比例×Ts，不加有限死区；逐位置曲线积分不用这些代表量近似替代。
- `selector.select_switch_device_with_audit(..., loss_evaluator=callback)` 的 callback 在 device engine 拟用 `evaluate_t_type_conduction_reference(device,stress,position_requests,scope)`，只通过上述厂商压降表积分，不能先调用 whole-loss evaluator 再减去能量项。能量接口测试设 forbidden；热复用 thermal_backsolve/interface，要求 finite/thermal_feasible。
- callback 的 `DeviceLossResult` 是公共 selector 内部兼容视图，`mode/method/thermal_design_notes` 明示范围；`p_total_W=p_cond_W`，被排除项的数值 0 仅为结构兼容，并由 typed exclusions 和所有 GUI/export reader 屏蔽“物理零”结论。范围结果仅发布 TTypePositionLoss/System，不让通用无 scope 的全部损耗表误读。
- 按设计 envelope 的每位置/每 case 求最坏单器件功耗及结温筛选/排名；最终当前工况逐位置求值后加和。保留电气/热过滤与现有排序，不能用组平均替代非线性积分。n 并联先缩放电流再按 n 汇总。
- `InductorDesignRequest`：L=每相 target，i_avg=0（正负完整周期平均，不等于无励磁），i_rms/peak/valley/delta_i_pp 从实际事件波形；throughput=P_ac/3；metadata.phase_count=magnetic_quantity=3、system_pout_w、line_frequency_hz、current_basis、source/cases。`InductorOperatingPointRequest` 对应 current basis 及已选实际 L；保留初筛/allow/frontier/Pareto 原政策。
- `CapacitorSizingRequest.side="upper"/"lower"`、role=dc_link、topology_id=T-type；dc_voltage=各银行当前/设计最坏电压，current_time/current/voltage 指向同源数据；capacitance_min_f 是工程最低要求，不自动拿首轮 proxy 冒充。最小 S 默认 1，最大 S/P 使用现有 DC-link 请求政策并在输入保存，不硬继承 NPC 2S；技术/温度/margin 与库 selection 同口径。
- 现有 `CapacitorResult.input_selection/current_operating_input` 可作 upper 的兼容入口，`output_selection/current_operating_output` 可作 lower，必须显示实际银行标签并在 typed hardware 中映射；不能对外重定义为普通输入/输出电容。库推荐物理容量回写只进入 selected hardware。

### 15.4 电容近似、工况包络与数值门槛

三线 KCL 和方向严格使用第 10 节；`I_src=<V_U*J_P-V_L*J_N>/Vdc` 是完整周期常量，本轮 V_U=V_L=Vdc/2。记录 `<J_P>/-<J_N>` 的差异，不独立去均值改变中点电荷。上下 raw i_C 各积分得到 q_drift；若周期端点偏移显著，报告 `nonperiodic_split_link_charge`，不重置电压伪造稳态。周期均值消除仅作已有供电近似声明，不替代 KCL。附加 ripple 不反向改变极点电压，报告 `fixed_bus_ripple_estimate`；不宣称动态能量耦合已实现。

拟新增设计工程输入键与 spec.metadata 同名：`engineering_vdc_min_v=700`、`engineering_vdc_max_v=800`、`engineering_pf_min=0.8`、`engineering_pf_max=1`、`engineering_load_min=0.1`、`engineering_load_max=1`、`engineering_ambient_temp_c=25`、`engineering_target_junction_temp_c=100`、`engineering_device_type=IGBT`、`engineering_device_implementation=Discrete`、`engineering_manufacturer=Any`。这些是后续最小工程默认值，不是当前 schema 接受的键；实施时接既有同义输入须显式映射，不引入两个不一致温度来源。温度在验证的库曲线范围内，case temperature 若未提供沿用公共 thermal reference/散热反求。完整性不能靠 input ignored 的现状判断。

设计 envelope 固定本次 phase 类型，在同一 candidate L、VLL/fline/fsw/Pout 下枚举 bus={700,800}×load={0.1,0.5,1}×PF={0.8,1}；每 phase 家族 12 个实际波形点。默认 design PF1 对应 L=1.0716517624676405 mH，每次刷新不能改此目标。选后实际 L 改变时重新校核同 envelope（不是重新设计）；任一 envelope 点不可达不能宣称全部范围通过。超前/滞后不同设计族；PF1 等价作交叉检查；运行 load=0 为诊断点，eta 不可用；500 V 为受控失败，不算范围有效点。未来用户自定义设计范围需要独立边界检查，不用这 24 点证明全包络。

| 指标 | 冻结容差/证据要求 |
|---|---|
| 稳态角色/位置/数量/ID/scope | 精确一致，无缺实例或错误位置 |
| KCL、电流方向、signed=channel−diode | 绝对 1e-8 A；局部方向表独立参考 |
| 电荷周期漂移 | abs(q_drift)≤max(1e-10 C, 1e-8*∫abs(i_C)dt)，分别上下；超限保留 raw 值和诊断 |
| 标量 R*I²、C/ESR 串并联、相电压/基波功率 | 相对 1e-6；近零绝对：A/V 1e-8，W 1e-8，H/F 1e-12，C 1e-10 |
| 非线性导通/电荷/励磁时间积分 | 对独立分段参考相对 1e-4；绝对 A/V/W 1e-6，电荷 1e-10 C；至少二倍加密并记录误差，非周期失败不能靠容差抹平 |
| 系统 published 总量/效率恒等式 | W 相对 1e-9/绝对 1e-8；ratio 相对 1e-9/绝对 1e-12；检查原发布值非只重算显示 |
| 热阻解析与近似 | Tj/温升解析比较绝对 1e-6 °C；模型精度另标 engineering proxy，数值一致不是实测精度 |
| structured/GUI | 工程字段上述容差；GUI按实际 precision；IDs/provenance/basis 精确；missing/NaN/Inf 不补零 |

### 15.5 阶段开放和消费者保护

拟在现有 `topology_capabilities.py` 增加 `supports_engineering_stage(topology_id, stage)`，T-type 的 stage 取本拓扑已实施能力表；旧拓扑映射保持已实现路径。完整/刷新/独立控制器共用此入口。T-type 的 `is_first_pass_topology_only` 仅在至少 device 正式接通后为 False，随后仍逐 stage 检查；不能移出集合便调用整个旧默认链。

| 完成步骤 | 新开放能力 | 仍必须保护 |
|---|---|---|
| 当前/step0 | 原基础设计/波形/应力/固定 candidate 刷新 | 所有工程组件/系统/sweep/export |
| step1 | device、已支持封装参考几何 | magnetics/capacitors/system/thermal/system geometry/sweep/export |
| step2 | magnetics、单磁件参考结果 | 未选银行与选后完整 closure；系统结果仍不可用 |
| step3 | capacitors、bank selection/ripple diagnostics | 未完成硬件快照/全链刷新前不得系统合计 |
| step4 | hardware_refresh/current component readback | scope 系统/热/整体几何及扫描仍待 step5/6 |
| step5 | scope system/thermal/geometry/current component GUI | 固定硬件 sweep/完整工程 export 尚待 step6 |
| step6 | sweep/engineering export | finite deadtime/energy/control 模型继续未开放 |

拓扑声明、full/refresh、RunDesignController/WaveformController/EfficiencySweepController、组件 controller 入口和结果页均核查阶段，direct call 也不可绕过。首轮 forbidden-downstream 测试在以后已开放阶段更新为能力契约，未开放负例继续保留。公共模型/typed报告扩展时全家族 schema/contract 消费者回归，当前 step0 不修改这些生产文件。

### 15.6 当前基线与实施边界

本步工具 `scripts/validate_t_type_engineering_step0.py` 保存当前解释器/源码/测试 SHA、未过滤库记录与源文件 checksum、normalized-v2 固定库 provenance、六 NPC 电气快照、NPC 真实完整组件链及两点固定硬件扫描、旧两电平/全桥器件链 report/structured/overview。原始报告保持完整；归一化仅按工具显式 timing/run ID 清单和该 case 精确输出根替换，硬件/数值/状态/警告/source 不删除；非有限标记保留且不能算接受。

NPC 当前工程链 baseline 是旧行为保护，不自动证明其全包络、原全部 proxy 精度或硬件验收。当前 T-type 只做真实基础 envelope 与 selector callback/导通表/失败接口探针；callback 受控热 fixture 不证明真实选型。实际命令、结果、证据、限制及 Git 回执记录在第二轮计划第 10 节。

## 16. 第二轮步骤 1 的实际接入边界（2026-10-13）

第15节保留步骤0冻结时的规划记录。本节和[当前字段字典](t_type_engineering_field_dictionary.md)记录步骤1已接入的生产接口；验证/Git状态以第二轮计划第11节实际回执为准。

- 新建 `models/t_type_engineering.py` 的 design basis、selected devices/packages 和 role selection reference，添加 optional `DesignReport.t_type_engineering`；结构报告仅有本结果时添加 `engineering_result`。完整 hardware/operating/position losses/split-link/system 类型仍属后续步骤，当前不存在这些已完成结果。
- `engineering_adapter.build_design_basis(report)`保存额定P/VLL/fline/fsw、设计L、phase、temperature、20%/10%裕量和实际case清单；`build_device_selection_requests(report, design_basis, plugin)`返回两组case stresses及每case/12位置导通请求。不可达或来源不符拒绝；显式包络必须包含设计点，未给包络时扩展默认值纳入该点。
- ROHM RG IGBT/FRD表在目标结温作双线性查表，按完整线路周期分段积分。FRD连续/脉冲额定与表的电流/温度覆盖另校验，不调用能量接口或静默clamp。主/中点分别全母线/半母线电压；peak桥mode为selection_peak_bound_no_energy。channel/diode占比用实际过零区间，不把diode time留假零，也不加死区。
- 导通engine拥有非线性积分与保守封装热反求；pipeline拥有两角色选择/审计和n=1/2/3比较，公共selector/排序/库不改。公共IGBT默认单方案政策不改，T-type按冻结合同显式创建三个方案。排名/拒绝/电压电流热过滤记录均保留。模块或无FRD不可用原因保留，不用零压降补齐。
- 最坏单封装channel/diode W与bare reference Tj用于选型，不能当当前功耗；组合功耗配max(IGBT/FRD Rth_jc)和既有TIM/backsolve进行保守散热参考。角色/方案总量为None，当前/系统损耗与效率不可用。complete且feasible才发布两个角色和12n离散采购封装，FRD不增加clamp计数。
- T-type只开放device和package reference geometry；磁件/电容/系统损耗/热/系统几何/扫描仍保护direct/controller入口。封装页面无共享sink体积且明确范围。固定candidate刷新保留设计选型、不重选、不改为当前损耗；实际L/C硬件回读仍待步骤4。
- 结构validator核查scope/exclusions、两角色/位置、封装绑定与数量、参考身份及finite损耗；缺项不能发布成功。旧拓扑optional字段为None，旧structured没有新节；原始dataclass增加None是明确的兼容结构差异，工程基线比较只可按记录政策忽略此一空字段。
- 效率页以sweep阶段能力判断，不能因device开放而提示可运行效率扫描。T-type设计输入行间距为4 px，保证1240×760最小窗口的顶部Run Design和滚动后的波形控件可达。按用户最新指示，本次收尾验证限定T-type；其他拓扑全面回归及跨拓扑隔离不作为已完成结论。

## 17. NPC 一致用户输入与半导体选择冻结合同（2026-10-13）

用户要求先冻结输入合同，再调整后台，随后继续工程链；半导体选择也与 NPC 一致。本节是后续实施的权威合同，覆盖第 14–16 节中冲突的输入、PF、选型工况、技术/厂家及并联策略。历史实现和验证回执保留，不能证明本节已实现。本次只改文档，生产界面和后台仍待适配。

### 17.1 实际参考与一致性边界

以 [NPC 表单](../src/pe_claw_gui/app/topology_forms/three_phase_three_level_npc_inverter_form.py)、[公共表单](../src/pe_claw_gui/app/topology_forms/base_form.py)、[筛选 metadata](../src/pe_claw_gui/libraries/semiconductors/metadata.py)、[NPC 输入解析](../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/input_schema.py)、[应力适配](../src/pe_claw_gui/engines/devices/stress_adapter.py) 和 [公共器件流水线](../src/pe_claw_gui/pipeline/run_device_pipeline.py) 在 `d1ac433610d0d4af37b092d5ece2ba90dab9bf36` 的实际行为为参考。只读核对 NPC，不执行 NPC 测试或电气链。

一致范围包括用户字段、顺序、标签、单位、默认值、选项、输入作用、公共库、筛选、方案生成、排名和审计机制。T-type 仍拥有自己的电路、门极、方向、逐位置应力与导通损耗适配；同输入不意味着相同 L、应力、型号或损耗。拓扑名称/示意图/模型说明与能力状态按实际 T-type 显示，不把 NPC 的 clamp 或能量模型复制进来。

### 17.2 设计输入：精确 12 字段

以下为 GUI 顺序；文本框的 raw 值保持字符串，经过归一化后形成有限 SI 数值。两个公共半导体控件使用只读选项框。

| 顺序 | raw key | 标签 | 默认 raw 值 | 对象、单位及含义 |
|---|---|---|---|---|
| 1 | `vdc_nom` | `Vdc nominal [V]` | `700` | 总母线 DC V；设计标称母线 |
| 2 | `vac_ll_rms` | `Vac line-line rms [V]` | `400` | 基波线间电压 RMS V，不是相电压 |
| 3 | `f_line_hz` | `Line frequency [Hz]` | `50` | 电网基频 Hz |
| 4 | `fsw_hz` | `Switching frequency [Hz]` | `20000` | 开关频率 Hz |
| 5 | `pout_w` | `Pout [W]` | `10000` | 三相额定有功功率幅值 W，不是每相功率 |
| 6 | `power_factor` | `Power factor` | `1.0` | 设计 PF；符号按 17.3 |
| 7 | `inductor_current_ripple_ratio` | `Inductor ripple ratio [pp/Ipk]` | `0.2` | 每相目标电流峰峰纹波/基波电流峰值，无量纲 |
| 8 | `dc_link_voltage_ripple_ratio` | `DC-link ripple ratio [pp/Vdc]` | `0.05` | 总母线目标电压峰峰纹波/Vdc，无量纲 |
| 9 | `ambient_temp_c` | `Ambient temperature [C]` | `25` | 环境温度 °C，供选择及热计算 |
| 10 | `target_junction_temp_c` | `Target junction temperature [C]` | `100` | 目标结温 °C，供选择及热约束 |
| 11 | `semiconductor_device_type` | `Semiconductor device type` | `Any` | 按公共类型过滤 |
| 12 | `semiconductor_manufacturer` | `Semiconductor manufacturer` | `Any` | 按公共厂家过滤 |

- 类型选项及顺序精确为 `Any, MOSFET, IGBT, Diode`；厂家为 `Any, Infineon, Navitas, Mitsubishi, ROHM, Wolfspeed`。不要改成 Switch category，也不减少为 IGBT。
- 基础正值、设计 PF 幅值 `(0,1]`、有限值与温度/额定前置约束从实际解析及公共消费者对齐；输入合法与电路可调制性、库曲线/额定覆盖分别判定，不以统一报错掩盖模型限制。设计 PF=0 拒绝。
- 不再显示 `power_factor_phase`、`operating_vdc_v` 或任何独立 `engineering_*` 输入；不另设高级输入页保留第二套字段。公共温度和厂家是唯一用户来源。
- 布局沿用 `Design Inputs`、`Waveform Operating Point`、`Notes` 及公共行/按钮构造。Run Capacitor、Run Magnetics、效率扫描按钮按当前 T-type 能力禁用，完成相应工程步骤后再开放。

### 17.3 运行输入、PF 语义与来源

| 顺序 | key | 标签 | 初始值 | 读取及处理 |
|---|---|---|---|---|
| 1 | `load_ratio` | `Load ratio [0-1]` | `1.0` | GUI 有限数值裁剪到 [0,1] 并回写，与 NPC 表单一致 |
| 2 | `power_factor` | `PF [-1..1]` | 取设计 PF，默认 `1.0` | GUI 有限数值裁剪到 [-1,1] 并回写，与 NPC 表单一致 |

运行母线来自设计 `vdc_nom`，不增加独立控件。运行字段只进入 `OperatingPoint`，不混入 `get_raw_input()`；运行 PF 与设计 PF 分别保存。API 固定硬件刷新仍可显式传实际 `vin_v`，但这不属于 GUI 用户字段，且不代表扩大硬件覆盖。

[NPC 波形](../src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/waveform.py) 的 `active_power_sign=-1 if PF<0 else +1`、`phi=acos(abs(PF))` 为符号参考：负 PF 表示反向有功，不表示超前。当前 T-type 的正幅值加 leading/lagging 输入必须在后台纠偏；不能把负 PF 映射成 leading，也不能丢弃符号。P_actual 的有符号基波目标为 `active_power_sign*P_rated*load_ratio`，电流幅值使用绝对功率及 PF 幅值；零负载仍可有 PWM 纹波。

NPC 运行表单允许 PF=0，波形在幅值分母使用 `max(abs(PF),1e-6)`。此为现有数值兼容行为，不能称作有限有功的物理零 PF 解。T-type 保留相同输入可提交行为；后台须保留该兼容依据并检查命令可达性/有限值，失败时给具体诊断，不宣称 PF=0 正常运行。负功率系统效率口径在工程链恢复前必须单独明确，不能直接套正功率效率公式。

### 17.4 半导体选择：公共流程与 T-type 适配

1. 使用同一 `build_default_semiconductor_registry`，由公共 `merge_semiconductor_filter_metadata` / `SemiconductorLibraryFilter.from_raw` 归一化并实施用户筛选，保留候选计数、数据来源和淘汰审计。`Any` 不强制回退 ROHM/IGBT；指定厂家/类型必须实际作用于选择。
2. NPC 公共 `build_design_point_switch_stress_cases` 生成额定母线、100% 负载的 `design_point`，PF 由 candidate 设计值取得。T-type 采用相同选型工况政策，电流取自己的完整线路周期逐位置数据。GUI 未提供 min/max 时母线为固定标称值；隐藏 NPC PF/负载默认并不代表 selector 实际枚举了它们。旧 700/800×负载×超前/滞后 24 点不得作为新默认选型包络。
3. 保留 T-type 主开关、中点开关两角色，各 6 位置，主阻断全母线、中点半母线；每角色可选不同型号。电气/热过滤、公共 selector 评分与排序沿用现有方法。NPC 的独立 clamp diode 不属于 T-type；公共 `Diode` 选项不能把二极管当成可控开关，没有兼容主动角色时明确报告无候选。
4. 技术范围对齐 NPC 主动开关的 MOSFET/IGBT 候选，离散/模块使用同库和角色兼容过滤。T-type adapter 校核真实终端连接、反向导通及模型覆盖：模块共发射极映射缺失、无有效曲线等须记录明确原因。当前 ROHM RG IGBT+FRD 特例不是完成合同；MOSFET、其他厂家和可适配模块的导通接口仍待接入。技术模型缺口需作为实施缺口解决，不以缩减下拉框或忽略筛选来完成一致性。
5. 并联方案调用公共 `_resolve_scheme_variants` 的同一政策：用户类型过滤为 `IGBT` 时只有 `single`，其余过滤比较 `single/parallel2/parallel3`。同方案每位置 n 个并联，耐压不缩放、电流按 i/n 后计算；数量 6n/角色。采购封装由真实 section 绑定计数，离散为 12n，模块不能沿用离散采购数量。
6. 方案使用公共 `_select_active_semiconductor_scheme`：完整且 feasible 优先，并联数优先，其后为当前模型范围损耗；无可行方案的完整/单管 fallback 仅供诊断，不发布成功硬件。用户可比较/选择的方案及其切换读回均沿用公共机制，缺角色不得发布总量。
7. 保留公共筛选/热方法，损耗回调使用 T-type 导通范围；不调用 NPC 整套能量模型。死区、Eon/Eoff/恢复/Coss 等仍排除。器件和方案损耗不同于 NPC 是电路及模型范围差异，不是选择机制不一致；每次评分/热结果标明 scope。

### 17.5 输入适配、兼容与失效

生产路径为公共 raw 字段→T-type schema→spec/candidate→T-type 电路波形/逐位置应力→两角色选择请求→公共筛选/方案→typed 结果/GUI/导出。不直接调用 NPC 完整 design-basis 解析带入死区、50 V 过冲或中点偏差假设；公共同义字段明确映射，T-type 物理公式和排除范围另行保留。

旧 `engineering_ambient_temp_c/engineering_target_junction_temp_c/engineering_manufacturer` 仅可作为旧 API 兼容别名：公共字段缺失时映射，二者同传且归一化冲突则拒绝并说明字段，不能形成双来源。旧独立技术/封装、bus/PF/load 包络及 phase 输入不得静默改变新 GUI 合同；非默认旧扩展请求显式报告需迁移，尤其 leading 不能换成负 PF。历史报告保持其原始 basis，不能重标为新合同结果。确需保留扩展 API 时先另写明确合同与证据。

设计字段、温度、厂家或类型改变使 candidate、选择和所有下游结果失效；运行 load/PF 改变保留所选硬件并使当前波形/应力/损耗/热/扫描失效。刷新失败清除有效当前数据，不借旧设计参考冒充当前值。每份结果保存规范化用户输入、选择工况、候选/筛选/方案、硬件身份、库来源及模型范围；缺角色/曲线/来源时保留原因并阻止成功与系统总量。

### 17.6 纠偏验收与当前文档范围

后台纠偏按[工程链计划第 12 节](../Plan/Active/three_phase_three_level_t_type_engineering_integration_plan.md)先行实施。验收包括 12+2 字段精确比较、公共筛选真实生效、IGBT 单方案与其他三方案、额定设计点而非旧包络、正/负/零 PF、旧字段冲突、无候选与不支持连接、当前硬件/页面/报告来源和仅 T-type 重复运行隔离。至少保留真实库 IGBT 及 MOSFET 路径，厂家无匹配有诊断；尚缺真实技术模型时不得宣布选择一致性完成。

本次为文档变更，只检查源码参照、语义冲突、本地链接、ChangeLog 追加及 diff，不运行 pytest/电气链，不修改 Python、GUI、库或生成证据。第 16 节的 286 项属于旧合同历史，不能计入本节验收。其他拓扑测试按用户要求不执行；共享改动若不能限定影响须如实记录未验证消费者。

### 17.7 A1 界面与公共输入实际接入边界（2026-10-13）

17.6最后一段记录文档冻结时的范围；此后按用户“界面还是没有改成一致”实施A1。T-type现使用与NPC精确相同的12设计字段及2运行字段，复用公共筛选控件/行构造，分区/标签/默认值/选项/行距对齐；保留原滚动宿主保证最小窗口可达。未接电容/磁件/扫描按钮仍禁用，拓扑名称及模型说明按T-type实际能力。

`build_default_inputs()`只返回12个公共用户字段；旧phase和engineering包络暂为内部/API输入，尚未执行A2迁移。公共温度/厂家归一化映射到现有工程consumer，同传别名冲突拒绝，有限值诊断保留实际字段。`spec.raw_input`记录公共字段和显式旧API字段，内部默认由metadata/basis保留。公共device filter/manufacturer及公共scheme variants已进入T-type专用pipeline，真实过滤并保留库计数/model拒绝；当前仅ROHM RG IGBT+FRD导通分支可发布，其他技术有明确unsupported诊断，绝不回退用户类型或厂家。

运行母线取设计值，load/PF按NPC表单裁剪回写；GUI接受signed PF输入，但后台仍只支持正PF幅值，负/零PF尚有明确拒绝。A2有符号求解/额定选择basis、A3更多技术/封装导通支持及方案交互仍待实施。因此本次只完成界面与公共字段生效边界，不称后台完整一致；17.3/17.4目标合同仍为后续门槛。

当前验证/失败历史/解释器/真实Tk截图/源码修订及Git回执见[计划12.5](../Plan/Active/three_phase_three_level_t_type_engineering_integration_plan.md)。其他拓扑代码与库记录未修改，也未执行其电气测试。


## 18. Summary 展示合同（NPC 结构对齐，2026-10-13）

本节只约束用户概要展示，不改变设计/运行电气模型、报告字段或选型政策。

- Summary 沿用 NPC 的 Design summary / Electrical parameters / Stage runtime / Semiconductor stress summary / Notes 分区。T-type 不重复渲染 topology_result.summary_lines；该原始记录与导出保持完整。
- 设计字段按母线、线/相 RMS 电压、额定有功、PF、线路/开关频率、调制、每相初始电感、每银行电容 proxy、母线/PWM 纹波目标、基波相电流 RMS/peak、两角色位置数量和可行性展示。L/C 明确是初始值/proxy，不冒充真实选型硬件；没有 NPC clamp diode。
- 运行点母线/负载/PF/有功和 A 相含 PWM 全周期 RMS 来自当前 waveform payload.basis/diagnostics。实际 PWM 纹波是原求解器各相每 PWM 周期“电流减正弦参考”峰峰值的最大值，不重算或当成 sizing target。无 waveform 不显示运行数字；无 stress 显示不可用，不回填旧实际值。
- 主开关与中点开关各六位置，仅显示逐指标包络的 static blocking V 与 signed/channel/diode peak/RMS/avg A。各项可能由不同位置取得，不能相加为系统电流；完整线路周期、design_estimate 与 waveform_actual 区分沿用原应力契约。无波形时未知 RMS/avg 显示 N/A。
- 12 位置明细和常规应力说明留在 Stress；semiconductor selection 必须同时存在两个已发布角色及 active scheme 才显示 available，并标 conduction only。未接工程阶段合并为一条说明；系统损耗/效率仍不可用。已知流程提示去重，未知 report/stress warning 原样保留，部分硬件不能报 available。
- 此显示精简不删改 DesignReport、typed 工程记录、应力或器件 audit/diagnostics，不改变 ExportController/结构导出的既有合同。GUI 用六位小数展示电压/运行电流等，设计 metadata 的简洁数值格式与 NPC 一致。
- Run Design 当前仍使用旧 12 工况工程包络；改为 NPC 额定 design point 归第17节 A2，不能以 Summary 修复声称后台已一致或性能已优化。

生产入口：[summary_view.py](../src/pe_claw_gui/app/result_views/summary_view.py)；明细入口：[stress_view.py](../src/pe_claw_gui/app/result_views/stress_view.py)。验证为 `tests/test_t_type_summary_view.py` 及步骤6/7/8真实GUI节点；实际回执见工程计划第13节。


## 19. A2 额定设计点策略与应力积分复用（2026-10-13）

本节覆盖第16/17.7/18节中的旧包络待迁移状态，范围仅为用户授权的设计点与积分复用；17.3有符号PF仍待实施，正PF及旧leading API物理模型不变。

### 19.1 额定选择来源

`build_design_basis`使用spec/candidate一致的额定母线、100%负载、设计PF，cases精确为一个 `(Vdc_nom,1.0,PF_design)`，其余额定总有功W、VLL RMS V、fline/fsw Hz、每相L H、phase和公共温度C沿原source。20%耐压/10%电流裕量不变。静态阻断main=额定Vdc、midpoint=额定Vdc/2；逐位置完整线路周期peak/RMS/avg和导通占比沿原模型。额定工况之外的实际刷新不改变选型basis/硬件，不能认定额定选择证明了旧700/800×负载×PF全包络。

`TTypeDesignBasis.selection_policy="nominal_design_point"`明确新basis；该新增字段默认`legacy_envelope`以保持旧构造合同，历史JSON缺字段按旧政策处理，不能重标。原cases字段仍是真实选择工况列表，语义/单位不变。schema validator对新政策检查单case与原输入母线/PF/满载一致，role reference.case必须属于它；旧缺字段政策仍不改变历史数据。

六个旧`engineering_vdc_min_v/max_v、engineering_pf_min/max、engineering_load_min/max`不再是内部默认或接受的扩展API；显式传入给出字段名及retired迁移说明，非有限值先给有限值诊断。公共温度/厂家别名仍保留。旧leading/独立技术连接边界本轮未扩展。真实候选可能因旧最坏包络转为额定点而不同，属于本次授权的选择政策变化，不能用旧硬件作为不变断言。

### 19.2 波形级应力复用与安全边界

T-type producer使用拓扑私有`_PositionStressWaveform`（继承公共WaveformSet，未改公共模型）。每份实例保存仅运行期的`_position_stress_key`，以完整segments/basis及已计算stress的规范JSON SHA256关联原计算。它不进入dataclass fields/asdict/metadata/JSON，不是可从结构报告恢复的可信token；无全局状态、跨设计缓存或持久文件。

生成波形仍以原adaptive quadrature求完整线路周期逐位置应力一次并记录摘要。每次stress_readback仍执行原validate_waveform的来源/完整周期/有限值/KCL/连续性/精确电流公式/事件/采样/gates/相统计校验；摘要一致才复用积分。任意source或stress改变则沿原计算重新积分并比较；缺stress/NaN/Inf/未知数据类型有明确错误。位置metrics副本每次与原stress比较。无运行receipt的普通/导入WaveformSet走重新积分验证；dataclasses.replace产生无receipt的新实例，验证通过后才能记下该实例结果。deepcopy保持独立数据，摘要变化仍拒绝。readback返回独立深拷贝，不让caller修改payload或其他报告。

这不是新增物理公式，也不降低原quad精度、Gauss节点、完整周期采样或任何工程容差。导通engine/库筛选/方案数/热筛选仍原方法，死区/换流能量继续不计算。结构报告的工程basis增加政策字段，历史和新报告分别识别；内部运行receipt绝不导出。

验证包括旧应力独立dense Simpson/加密、真实库标量adaptive导通、篡改source/stress/metrics/统计/gates负例、无receipt fallback、调用次数、真实GUI/导出/固定来源及同T-type重复隔离。当前运行回执与性能证据以[计划第14节](../Plan/Active/three_phase_three_level_t_type_engineering_integration_plan.md)为准，未验证门禁不提前宣称完成。

## 20. 第二轮步骤 2：三相磁件接口（2026-10-13）

本节覆盖第16节磁件未开放的历史状态，保留步骤4完整硬件closure、电容、热/几何、系统损耗/效率和扫描暂缓。Run Design仍按原按钮路径只做电气/器件；Run Magnetics独立执行真实磁件搜索。full pipeline显式`enable_magnetic_design=True`才接磁件。其他拓扑生产路径、库和筛选政策不变。

### 20.1 请求来源与公式

`magnetic_adapter.py`拥有设计/运行请求：额定bus、满载、设计PF生成完整线路周期事件波形；a/b/c分别取exact statistics mean/RMS/min/max，peak为max(abs(min),abs(max))，ripple为每载波电流减基波参考后的最大App。共同型号请求使用三相逐指标最坏值，不取一相直接代表另外两相，不以`candidate.delta_il`目标填实际纹波。每相吞吐=Ptotal/3 W，系统对象为3个独立电感，双向AC电流；`mode=CCM`仅为既有固定磁件引擎兼容标识，说明AC过零，不声称DC恒正CCM。

当前电感电压`vL=vphase_neutral−vgrid`。在每个事件片段用8点Gauss积分，按PWM周期分别累计正/负volt-second，再取最大局部正向激励`A+=max_k integral_k(max(vL,0))`。规范请求保留原字段含义：`duty=0.5`、`v_l_on=2*fsw*A+`，因此既有引擎`Bpp=v_l_on*duty/(fsw*N*Ae)=A+/(N*Ae)`；负向字段同样保留对应负激励。这是当前PWM局部excursion的筛查/Steinmetz近似，不是全线路Bpp，也不是半母线固定电压。`Babsolute=Lactual*Ipeak/(N*Ae)`独立用于饱和，不能因signed平均为0判无励磁。铜损仍用现有`Irms²*Rdc*Fac`；磁芯损耗沿既有normalized-v2模型/单位转换和局部Bpp入口，完整线路/次回线物理损耗精度没有新增承诺。

设计请求→原fixed-inductor搜索、allow、压缩、allow-aware bounded frontier、same-core stacks、Pareto及middle representative。公共helper只抽取现有实现；旧消费者默认保持空初筛立即返回政策，T-type显式`expand_empty_shortlist=True`让有效请求的空shortlist也经过原完整配置frontier后再判耗尽。默认normalized-v2 production目前仅virtual；catalog请求按后端原诊断拒绝，不能把虚拟推荐写为可采购catalog型号。cache/source identity、MAS/MKF commit、版本、可用引擎记录数量、过滤/排序政策及checksums保留。

### 20.2 三实例、选定L与运行点

`engineering_result.magnetics`是可选schema-1扩展。`target_inductance_h`来自原candidate；`selected_inductance_h`来自推荐库设计。a/b/c以`library_candidate_id::phase_a/b/c`记录物理身份，分别调用原fixed evaluation，保存per-phase request、reference/current evaluation、实际L和volume。三相subtotal只在全部必需铜损、磁芯损耗、total、B、J、volume有限/非负且原total与组件相符时发布；不是系统效率分母。

选定L通过内部effective candidate重新生成完整三相waveform、调制/周期/局部纹波校核，原candidate与initial estimates不改。不支持三个不同L；物理实例共用同一型号和L。步骤2磁件结果拥有选定L的局部waveform基准，现有主Waveform/Stress页仍读原candidate的初始L；这一区别显式记录在两个L和magnetic operating_basis中，步骤4才接完整当前硬件的统一电气回读。

固定硬件刷新不搜索、不改额定器件/磁件选择，按当前bus/load/PF重新做选定L局部校核与三相评价。输入改变/失败清除current request/evaluation和小计、audit，保留设计身份及额定reference；恢复重新积分。候选指纹/run/库推荐ID/L/物理设计不符拒绝，缺任一相不得发布subtotal。

在已有运行点报告上点击Run Magnetics，先按额定点搜索并保存独立`reference_request/reference_evaluation`，再沿同一已选硬件回到报告当前工况评价，不把额定点参考写成低负载的当前结果。原`design_request`保留初始L目标请求，reference request拥有选定L的额定点基准；二者的L和电流差异显式保留。

三相各自使用共享core-loss excitation builder，以实际电流与L/N/Ae重建包含PWM的完整线路B(t)，frequency=fline，明确shadow-only，不替换生产Steinmetz loss或假称已接全物理效率。每个record拥有自己的instance ID与电压/电流来源路径；初始半母线proxy不填为实际励磁。

该公共builder将非均匀事件采样电流线性插值到完整线路周期均匀网格，闭合周期端点；shadow flux peak是该重采样网格的峰值，可能低于原始事件采样峰值，不能冒充精确连续极值。生产饱和评价仍独立使用event统计的精确Ipeak与`L*Ipeak/(N*Ae)`，不使用shadow峰值代填。独立验证在审计实际网格以NumPy插值核对完整B(t)及峰值，另核对生产精确峰值，容差1e-12相对。

### 20.3 交付/验证边界

GUI开放磁件按钮并沿现有磁件/Pareto页面读回；结构报告序列化三实例、小计、硬件身份与provenance。新增schema校验缺相/非有限/总量/来源/L/运行依据及unavailable总量负例。独立exact-ODE dense积分、`Babsolute`与铜损标量参考、真实库接受、控制allow/frontier耗尽、L改变可调制边界、固定硬件不重选、真实Tk刷新/失败恢复及同T-type隔离分别留证。当前结果以[计划步骤2回执](../Plan/Active/three_phase_three_level_t_type_engineering_integration_plan.md)为准；不运行NPC/其他拓扑及full suite，不能将本轮结果当旧家族回归或完整系统验收。

## 21. 第二轮步骤 3：上下电容银行（2026-10-14）

本节覆盖历史电容未接入状态。GUI Run Design 保持快速器件路径；Run Capacitors 单独执行真实库选型与银行形状导出。full pipeline 不传 options 时保持 T-type 快速默认；显式 enable_capacitor_design=True 才接两银行。系统损耗/热/几何/效率与全链实际硬件 closure 留步骤4/5，银行小计不是系统总量。

### 21.1 端口与数值模型

三线相电流正向母线→相，状态P/O/N分别累加带符号电流为 J_P/J_O/J_N，KCL=0（A）。VU=VL=Vdc/2，源模型为完整线路周期桥功率均值/Vdc，即 Isrc=(mean(J_P)-mean(J_N))/2。正向给电容正端充电：iCU=Isrc-J_P，iCL=Isrc+J_N，iCU-iCL=J_O。exact ideal-L事件电流用8点Gauss积分取得raw mean/RMS/drift/absolute charge，先按第15节 max(1e-10 C,1e-8*absolute_charge) 检查原始漂移，再交公共selector去均值。不能独立去均值隐藏中点漂移。

默认案例独立quad/Gauss都发现原始漂移2.7286e-8 C（非积分误差）。根因为逐PWM平均电流反馈的弱阻尼交替初始分量，整线路首尾残差未限定平衡正弦稳态。T-type局部producer在偶数fsw/fline时按 i(Tline/2)+i(0)=0 shooting更新初值并重跑原共享求解，最多4次；不改事件/样本/端点电流，不修改共享three_level_common。默认raw drift降到约3.3e-14 C，实际half-period残差保留。奇数载波周期沿原求解，银行仍必须通过raw drift门禁；未证明任意频率比都支持银行。

银行步骤3使用原candidate L的完整事件波形；步骤4才统一selected-L全链。设计是额定母线/满载/设计PF，当前刷新是当前Vdc/load/PF；source/run/candidate/selected hardware/waveform basis不一致拒绝。两电流数组在独立request中，公共单银行WaveformSet槽保持空。

Q_U/Q_L由解析电流primitive分段累加，DeltaVU=Q_U/Cu、DeltaVL=Q_L/Cl分别计算，支持不等C；Ceq=Cu*Cl/(Cu+Cl)。fixed_bus_ripple_estimate不反馈开关电压，不是动态中点能量闭环。共享selector用严格递增时间和梯形积分，事件左右值由相邻浮点时刻保留，每事件32细分；raw证据和微小离散DC correction独立记录。KCL绝对1e-8 A；独立ODE/trapezoid双分辨率参考RMS/Qswing相对1e-4、Q绝对1e-10 C、电压绝对1e-6 V，不能去均值代替原始门禁。

### 21.2 选型、刷新与物理计数

独立upper/lower CapacitorSizingRequest：每银行Vdc/2，输入纹波百分比乘该银行电压（两银行同百分比），min C=原candidate每银行proxy，ambient=公共温度，margin=1.2；铝电解、既有inverter_electrolytic_dc_link类型。显式S=1..4/P=1..5，不复制NPC固定minS2。复用list_registered_capacitors（32910 records）、现有过滤/压缩/S-P/Pareto/volume-loss-compromise推荐，保留全记录SHA256/每型号source/实际搜索及耗尽诊断，无库修改。

Count=Ns*Np，Cbank=Cpart*Np/Ns，ESRbank=ESRpart*Ns/Np，Irms_percap=Irms_bank/Np，PJoule=Irms_bank²*ESRbank；铝电解沿原ESR loss model，不额外重复计dielectric。原p_total必须等于两损耗项，per-cap loss*count必须等于bank total。Ripple_C=Qswing/Cbank，Ripple_ESR=Ipp*ESRbank，total是既有保守和。热点=ambient+per-cap loss*Rth，仅银行筛查；几何为原银行形状/排列，不是系统装配。

700 V默认真实推荐每银行B43703A5568M600，450 V、5600 uF、1S1P，满足420 V设计margin；800 V当前点要求480 V，固定银行必须拒绝。额定700 V选型不是800 V包络证明；独立800 V额定/PF0.8另有真实库接受测试，不改margin/库/选型政策凑成功。

刷新仅evaluate_capacitor_bank，不搜索/改型号/S/P；保留nominal selection。缺任何银行、耗尽、无效波形/source、当前margin/纹波/热点不满足，清空current banks/Ceq/两银行损耗与体积，保留硬件历史和具体原因。运行输入编辑/解析或波形失败同样失效；恢复重新计算。设计容器兼容input_selection=upper/output_selection=lower，request.side保持物理身份，npc_design为空。

### 21.3 报告与验证边界

engineering_result.capacitors为schema1可选扩展，owner为T-type capacitor stage。GUI上下银行当前数字来自当前快照；unavailable不回填设计损耗。结构capacitor.upper/lower及兼容input/output均当前读回，bank_subtotal保留单位/来源；hardware部分只是设计型号身份。系统阶段仍被能力门禁阻止，新增split capability仅供物理命名/页面路由；依赖NPC专有公式的系统consumer留步骤5适配。

Schema分别检查来源/数量/单位/公式、原发布小计、raw charge门禁、当前basis与public读回。真实Tk/库/搜索耗尽、独立公式、T-type隔离回执见工程计划16节。其他拓扑/full suite不执行。ExportController轻量摘要仍是原candidate初始L/C；银行JSON/Pareto CSV与形状工件是本步产物，完整系统导出留后续。


## 22. 第二轮步骤4：完整选定硬件与原子当前刷新

本节接续步骤2/3的分阶段结果。尚未完整选型的报告允许原综合参数预览；第一次拥有两器件角色、三物理电感和上下银行后，必须统一闭合，缺失组件不能再回退为预览成功。系统loss/eta、系统热/装配几何仍属步骤5，死区/换流能量继续排除。

### 22.1 身份、参数与物理数量

`hardware_adapter.build_hardware_snapshot`验证run、原candidate fingerprint、scope、当前active scheme、两角色各六位置及每位置n=1/2/3、12n离散IGBT/FRD封装、三相同型号磁件的model/winding/actual L、上下型号/S/P/actual C/ESR和温度/器件热配置。完整选定记录规范JSON的SHA256形成hardware_id；运行bus/load/PF不进入ID。型号文字相同但绕组/库记录不同不能混用。

原`report.candidate.inductance_h`/`capacitance_f`仍为H/F设计综合目标。内部effective candidate以selected L覆盖电感，metadata保留parent fingerprint、磁件ID和参数来源，仅用于生成/应力/评价，不替换原report candidate；当前波形metadata另有hardware_id和parent fingerprint。硬件snapshot保存选定参数，current_hardware_id仅在本次完整刷新成功时有效。Cu/Cl各自为物理银行F，ESR为ohm；Ceq=Cu*Cl/(Cu+Cl)。三相每相一物理电感，H不乘三；两角色各六电气位置，每位置n包。

### 22.2 顺序与当前量

完整闭合顺序为snapshot→selected-L完整事件波形→12位置实际stress/调制可行→固定型号导通曲线评价→同一波形三电感评价→同一波形上下银行评价→原子发布。库/selector/ODE/铜损/磁芯/ESR模型保持原方法。C仅用于既有fixed-bus Q/C估计，不反馈调制电压，不声称动态中点闭环。

12位置current_positions保存每器件channel/diode W，position_loss_w=n*(channel+diode)，仅乘n一次。Device兼容current_operating_losses是每角色当前最坏位置的每器件W，不是角色或系统总量。导通沿既有目标温度表格/热阻参考筛查，未调用任何开关/恢复能量。磁件current小计是三相铜/磁芯W及m3，银行current小计是上下W/cm3；均拥有相同current_basis：Vdc V、VLL RMS V、load pu、PF magnitude/phase、Pout W、fline/fsw Hz、actual L H。当前量不回填设计reference。

### 22.3 更新、失效与恢复

`refresh_t_type_hardware`只评价已选硬件，不综合、不搜索；已有快照与当前记录不同必须拒绝。组件选择动作通过限定closure或显式`update_t_type_selected_hardware`建立新快照，并清旧current/sweep/export。普通运行bus/load/PF刷新hardware_id不变；设计VLL/fsw/相位/温度继续遵守现有重新设计合同。

缺任何角色/相/银行，run/scope/identity错配、非有限值、不可调制、实际器件/银行额定裕量或曲线范围失败，都清current waveform/stress/topology result、12位置导通、器件current、磁件/银行current及小计、系统/热/装配/扫描；保留选型硬件和额定reference供修复后重算。已完整报告失效不能改成初估成功。GUI编辑、解析失败和WaveformController失败调用统一失效。

Summary短文本保留初估并补selected L/C与refresh status；Device区分当前12位置导通与额定reference；轻量export区分selected参数与current available/unavailable。structured `engineering_result.hardware/current_*`保留typed身份、basis和来源；validator检查selected L、同basis、12位置数量/功耗和失效无current。完整CSV/BOM/system export仍归步骤6。

### 22.4 验证边界

独立事件ODE/RMS与解析Q/C、独立标量双线性导通积分验证公式；真实库完整闭合/反向组件选择顺序、无重选、硬件编辑/身份注入、失效恢复验证契约；真实Tk当前数字/编辑失效/结构导出验证用户链；同T-type A→B→A与反序验证隔离。controlled selected-L变更仅验证实际参数读回，不宣称改后的磁件是可采购实物。仅执行T-type测试；其他拓扑共享消费者回归未执行，保留后续集成gate。当前实际回执见工程计划17节，收集/历史回执不作为本版通过依据。

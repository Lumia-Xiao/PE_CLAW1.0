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

| 证据类别 | 必需检查 | 本轮状态 |
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

## 14. 步骤 0 冻结的第一轮实现接口

本节与 [已完成的实施计划](../Plan/completed/three_phase_three_level_t_type_implementation_plan.md) 共同规定第一轮子集；第 2–5 节电路与方向继续有效。第 6–10、12 节中有限死区、器件能量、动态电容、真实选型、系统效率及完整导出属于后续工程扩展，不作为第一轮门槛。新增基础代码的公式、契约、GUI 数字和隔离测试仍须执行。本节只冻结未来行为；步骤 0 的 NPC 回执不能证明 T-type 已实现。

### 14.1 输入、规格与运行点

拟定 `LEGACY_KEY=ThreePhase_ThreeLevel_T_Type_Inverter`，显示名称 `Three-Phase Three-Level T-type Inverter`。raw input 保持字符串映射，经本拓扑解析器生成有限 SI 数值；不调用 NPC 的完整 design-basis 解析器带入死区、过冲或器件默认值。

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

B1 独立标量参考：L=1.071651762 mH/相，ΔI_target,pp=4.082482905 A，Ceq_proxy=40.816326531 μF，Cbank_proxy=81.632653061 μF，m_command≈0.933345504。B3 两次 PF=0.8 设计各自 L=0.857321410 mH，滞后/超前 m_command≈0.945050474/0.921491868。解析参考及实际合成回执见 Active 计划 9.8/9.11。

### 14.3 波形、应力与报告字段

`WaveformSet.metadata["three_phase_t_type_pd_spwm_waveforms"]` 是三相完整载荷的唯一绘图来源（拟本地类型结构，显式 `to_dict`；不改共享模型）：

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

数值容差、NPC 共享抽取名单及基准见实施计划步骤 0；步骤 1–5 的公式、导通/理想事件、实际波形、时间积分应力和基础报告回执见 9.7–9.11。步骤 6 GUI/注册证据记录于 9.12；步骤 7 刷新测试与实际回执记录于 9.13：累计 377 项、收尾 38 项及 candidate-only 来源保护补充 4 项均实际通过，且为不同修订的明确执行范围。步骤 8 聚焦 7 项、累计 283 项均为当前工作区实际通过，0 failures/errors/skips；NPC 六份完整 payload SHA 在各次运行中精确不变。GUI/报告证据只覆盖当前首轮的设计、波形、应力、运行点刷新和 bounded L/C 摘要；未覆盖真实器件、死区/换流能量、损耗/效率/热、完整工程导出或 full suite。

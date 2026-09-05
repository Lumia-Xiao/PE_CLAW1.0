# 三相三电平 NPC Efficiency Sweep 实时性优化计划

## 1. 任务背景

目标拓扑：`three_phase_three_level_npc_inverter`

目标是缩短 NPC `Efficiency Sweep` 的运行时间，使 GUI 能够更接近实时刷新，同时保持已经确认的精确开关损耗计算语义：

- 开关损耗使用一个工频周期内每个实际开关事件的实际电流和阻断电压。
- 负电流开通视为软开关，`Eon = 0`。
- 正电流开通使用硬开通损耗模型。
- 关断损耗使用关断时刻实际电流。
- SiC 二极管反向恢复损耗为零。
- 开关频率继续来自原有用户输入 `fsw_hz`。
- 不增加任何 GUI 用户输入。

当前默认效率扫描保持原有点数和结果契约：

- 负载扫描：20 个点，`0.05` 至 `1.0 p.u.`。
- 三相逆变器 PF 扫描：20 个非零 PF 点。
- 本计划不通过减少扫描点数量改变现有曲线语义；先优化每个点的计算。

## 2. 当前性能基线

当前 NPC 波形参数：

```text
SAMPLES_PER_SWITCHING_PERIOD = 24
默认工频周期采样点 = 9601
默认开关事件数 = 4800
```

已知耗时热点：

- 每个负载点和 PF 点都会重新调用一次 `plugin.generate_waveforms()`。
- 单个 NPC 波形生成约 17 秒。
- `_sample_npc_event_segments()` 中的 `_current_at_event_time()` 反复从头扫描全部分段，是最大的单点瓶颈。
- `_states_at_event_time()` 和事件提取中的前后分段查找也存在重复线性搜索。
- 周期稳态求解会在每个扫描点重复执行工频周期仿真。
- 每个点还会重复执行运行点器件损耗刷新，以及可能的磁性、热和电容刷新。

性能优化必须分别记录：

- 波形生成时间。
- 周期稳态求解时间。
- 事件提取时间。
- 事件级开关损耗计算时间。
- 单个负载点耗时。
- 单个 PF 点耗时。
- 整个 NPC efficiency sweep 耗时。

## 3. 共同约束

- 只修改 NPC efficiency sweep 相关路径，其他拓扑行为保持不变。
- 不引入电感等效电阻，不修改电流物理模型。
- 不改变精确事件分段积分、周期稳态条件和开关损耗公式。
- 不用峰值电流替代开关时刻实际电流。
- 不新增用户输入，不改变原有 GUI 输入窗口。
- 不删除或恢复已经移除的 `other` 损耗。
- 测试临时文件全部写入工程根目录的 `pytest_temp`。
- 设计输出继续写入当前单次运行的独立 `outputs` 子目录；不提交生成文件、缓存和测试临时目录。
- 每完成一个步骤都必须运行该步骤测试，更新本计划和 `ChangeLog.md`，独立 `commit` 并 `push`。

## 4. 实施步骤

### 第一步：建立 NPC Efficiency Sweep 性能基线

状态：已完成

#### 修改内容

- 增加或整理只供测试使用的性能测量入口，不改变计算结果。
- 分别测量：

  - 单次 `plugin.generate_waveforms()`。
  - 单个 `_evaluate_load_point()`。
  - 一个负载点 sweep。
  - 一个 PF 点 sweep。
  - 完整 NPC efficiency sweep。

- 记录采样点数、统一事件分段数、事件数和周期稳态迭代次数。
- 固定测试输入和 Python 运行环境，确保后续前后对比可重复。
- 增加结果不变量测试，锁定事件数、事件来源、事件电流来源、周期稳态残差和开关损耗规则。

#### 验收标准

- 性能基线可以重复运行。
- 测量不会写入 `outputs`，或生成文件只写入隔离的 `pytest_temp` 子目录。
- 当前计算结果和已有 NPC 合同保持一致。

#### 版本控制

测试完成后更新计划和日志，独立 commit 并 push。

#### 执行回执

- 新增 `scripts/measure_npc_efficiency_performance.py` 和
  `tests/test_npc_efficiency_performance_baseline.py`，仅用于 NPC 性能测量和结果不变量验证，不改变生产计算逻辑。
- 测量范围仅覆盖 NPC 代表性单点：单次波形、一个满载点和一个 `PF=0.8` 点；完整 sweep 按当前 20 个负载点加 20 个 PF 点的固定网格估算，不重复执行长时间全扫描。
- 基线参数：`SAMPLES_PER_SWITCHING_PERIOD=24`，单工频周期 `9601` 个采样点，`4800` 个开关事件。
- 实测：单次波形约 `18.07 s`，单负载点约 `17.92 s`，单 PF 点约 `18.26 s`，代表性单点平均约 `18.09 s`，完整 40 点 sweep 估算约 `723.58 s`。
- 结果不变量：周期稳态已收敛，最大首尾残差约 `2.95e-9 A`；事件来源为精确统一事件分段边界，电流来源为精确分段积分，阻断电压来源为事件时刻分裂直流链路电压；负电流软开通事件存在。
- 测试：`tests/test_npc_efficiency_performance_baseline.py` 为 `3 passed`；`py_compile` 和 `git diff --check` 通过。
- 基线 JSON：`pytest_temp/npc-efficiency-step1-baseline-run/baseline.json`，未写入 `outputs`，未提交生成物。
- 第一步代码提交：`628e420`（`test: add NPC efficiency performance baseline`），已推送至 `origin/codex/npc-output-run-isolation-step1`。
- 本步骤计划和日志回执将在代码提交后单独提交并推送。

### 第二步：适当减少工频周期采样点

状态：已完成

#### 修改内容

- 将 NPC 波形的 `SAMPLES_PER_SWITCHING_PERIOD` 从 `24` 调整为 `8`，作为第一版性能参数。
- 默认工频周期采样点由约 `9601` 降至约 `3201`。
- 保持统一开关事件时间轴和逐段积分逻辑不变。
- 保持精确开关事件的事件时间、事件电流和阻断电压来源不变。
- 保持 GUI 必需的既有波形字段和数组长度一致性。
- 对降低采样点后的电流 RMS、纹波、周期平均误差、周期首尾残差和事件损耗进行前后比较。

#### 验收标准

- NPC 事件数量和事件级实际电流计算仍然正确。
- 负电流开通仍为 `Eon = 0`，SiC 反向恢复仍为零。
- 周期平均电流误差、周期首尾残差和三相电流和满足原有容差。
- GUI 波形仍能正常绘制，不显示旧的参考电流替代实际电流。
- 相对于基线，单次波形生成和单个 sweep 点耗时明显下降。

#### 版本控制

测试完成后更新计划和日志，独立 commit 并 push。

#### 执行回执

- 将 NPC `SAMPLES_PER_SWITCHING_PERIOD` 从 `24` 调整为 `8`，默认工频周期采样点从 `9601` 降至 `3201`。
- 保持精确统一事件分段、逐段积分实际事件电流、事件时刻分裂直流母线阻断电压、负电流软开通和 SiC 反向恢复为零的逻辑不变；代表性运行点仍为 `4800` 个事件。
- 修正性能测量脚本，使采样参数从实际 waveform metadata 读取，避免从不含该字段的候选元数据读取旧默认值。
- 第二步测量结果：单次波形 `8.1643 s`，单负载点 `8.2597 s`，单 PF 点 `8.3620 s`，代表性点 `8.3109 s`，完整 40 点估算 `332.4342 s`；相较第一步约 `18.07 s`、`17.92 s`、`18.26 s`、`18.09 s`、`723.58 s`，耗时约降低 `54%`。
- 不变量：`event_count=4800`，`turn_on_count=2400`，`turn_off_count=2400`，`soft_turn_on_count=1199`，周期稳态最大残差 `2.94e-9 A`，周期末端人工修正为 `False`。
- 验证：NPC 步骤、性能基线和合同测试最终为 `43 passed`；`py_compile`、`git diff --check` 通过。测试输出写入 `pytest_temp/npc-efficiency-step2`，未写入设计结果 `outputs`。
- 性能 JSON：`pytest_temp/npc-efficiency-step2/baseline.json`，未提交生成物。

### 第三步：为统一事件分段建立有序索引

状态：已完成

#### 修改内容

- 优化 `_current_at_event_time()`，使用有序边界、单向游标或 `bisect` 定位当前分段，避免每次从头扫描。
- 优化 `_states_at_event_time()`，复用同一分段定位逻辑。
- 优化 `_extract_npc_switching_events_from_segments()` 的前后分段查找，直接使用相邻分段关系或边界索引。
- 事件边界处仍使用同一段积分得到的精确电流，不改为粗采样插值。
- 保持边界容差、事件排序、相别、开关编号、器件角色和阻断电压来源字段兼容。

#### 验收标准

- 优化前后事件时间和事件电流在数值容差内一致。
- 事件数量、开通/关断数量及软开通数量一致。
- 周期平均电流、三相电流和、开关损耗和报告结果一致。
- profiling 显示 `_current_at_event_time()` 和 `_states_at_event_time()` 不再占据主要耗时。

#### 版本控制

测试完成后更新计划和日志，独立 commit 并 push。

#### 执行回执

- 为统一 NPC 事件分段建立有序起止时间索引，使用 `bisect` 定位采样状态和事件电流所在分段。
- 事件提取改为直接遍历相邻分段生成切换边界，移除每个事件对全部分段的反向线性查找。
- 保持事件边界语义：事件电流取切换前段的精确分段积分值，状态取切换后段；事件时间、事件类型、阻断电压和审计来源字段不变。
- 第三步测量结果：单次波形 `0.3383 s`，单负载点 `0.4452 s`，单 PF 点 `0.3821 s`，代表性点 `0.4137 s`，完整 40 点估算 `16.5475 s`；相较第二步代表性点 `8.3109 s`，约提升 `20.1` 倍。
- 不变量：采样仍为 `3201` 点，`event_count=4800`，`turn_on_count=2400`，`turn_off_count=2400`，`soft_turn_on_count=1199`，周期稳态最大残差 `2.94e-9 A`；事件来源为精确统一事件边界，电流来源为精确分段积分，周期末端人工修正为 `False`。
- 验证：NPC 分段测试 `8 passed`；NPC 合同、性能基线和基线测试 `21 passed`；`py_compile`、`git diff --check` 通过。测试和性能输出写入 `pytest_temp/npc-efficiency-step3*`，未提交生成物。
- 性能 JSON：`pytest_temp/npc-efficiency-step3/baseline.json`，未提交生成物。

### 第四步：复用周期稳态初值

#### 修改内容

- 为 NPC efficiency sweep 增加内部 warm-start 机制。
- 负载扫描按连续顺序传递上一个运行点的周期稳态初始电流或收敛状态给下一个点。
- PF 扫描同样传递相邻 PF 点的周期稳态初始电流。
- 第一个点仍使用现有默认初值。
- 每个点仍必须检查周期首尾残差；warm start 失败时自动回退到现有周期稳态求解路径。
- 不改变周期稳态求解容差、投影约束和调制饱和诊断语义。

#### 验收标准

- warm start 不改变最终周期稳态初值、实际电流和事件损耗结果的容差范围。
- 收敛迭代次数和单点波形生成时间下降，或在不适合复用时可靠回退。
- 负载和 PF 扫描跨越正负功率因数时不会错误复用不适用的状态。
- 输出的周期稳态状态仍可审计。

#### 版本控制

测试完成后更新计划和日志，独立 commit 并 push。

### 第五步：减少扫描点中的固定硬件重复刷新

#### 修改内容

- 针对 NPC efficiency sweep 复用已经完成的固定硬件选择结果。
- 保留每个运行点必须重新计算的内容：

  - NPC 实际电流波形。
  - 实际开关事件。
  - 事件级开通和关断损耗。
  - 当前电流下的导通损耗。
  - 当前电流下的电容损耗。

- 避免每个点重新执行不改变选择结果的磁性搜索、完整热设计或固定器件筛选。
- 如果需要生成当前运行点的损耗对象，使用轻量的运行点刷新函数，并复用设计点的硬件、热边界和选型结果。
- 保持最终 `EfficiencySweepPoint`、CSV、结构化报告和 GUI 损耗视图字段兼容。

#### 验收标准

- 固定硬件 part number、并联数、磁性件和电容选型与优化前一致。
- 每个点的 NPC 事件损耗仍基于当前点实际事件电流和阻断电压。
- 不再重复执行无必要的固定硬件搜索。
- 损耗分解中不出现 `other` 损耗。
- 单个扫描点耗时进一步下降，结果与优化前在工程容差内一致。

#### 版本控制

测试完成后更新计划和日志，独立 commit 并 push。

### 第六步：NPC GUI 实时刷新与最终性能回归

#### 修改内容

- 检查 Efficiency Sweep 控制器继续使用当前设计报告和当前 NPC 运行上下文。
- 确认效率图、损耗分解、结构化报告和硬件概览不会因为性能优化重复触发设计或磁性流程。
- 保持现有负载点和 PF 点数量及输出格式，不增加用户输入。
- 在 NPC 专项测试中记录优化前后耗时和加速比例。
- 验证重复运行、输出目录隔离和 `pytest_temp` 临时文件边界。

#### 验收标准

- GUI Efficiency Sweep 可以完成并刷新效率图、损耗图和报告。
- NPC 实际波形、事件损耗和结构化报告保持一致。
- 运行期间不阻塞于不必要的重复设计流程；若仍需后台化，记录为后续任务，不在本计划强行引入 GUI 线程改造。
- NPC 范围内相关测试全部通过。
- 性能相对于基线有明确改善，且精确开关损耗语义不回退。

#### 版本控制

测试完成后更新计划和日志，记录最终 commit ID、远端分支、测试命令和结果，独立 commit 并 push。

## 5. 测试范围

每一步优先使用以下 NPC 测试，并将临时目录显式设置在 `pytest_temp`：

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/test_npc_step*.py -q --basetemp=pytest_temp/npc-efficiency-stepN
python -m pytest tests/test_dc_ac_three_phase_three_level_npc_contract.py -q --basetemp=pytest_temp/npc-efficiency-contract-stepN
python -m pytest tests/test_dc_ac_packaged_gui_runtime.py -q --basetemp=pytest_temp/npc-efficiency-gui-stepN
```

PowerShell 不直接展开 pytest 文件通配符时，先用 `Get-ChildItem` 枚举文件再传给 pytest。

必要的额外检查：

- `python -m py_compile` 或针对改动模块的 `compileall`。
- `git diff --check`。
- NPC 事件数量、事件实际电流、周期稳态残差和损耗结果前后对比。
- 输出目录和 `pytest_temp` 生成物不进入 commit。

## 6. 任务完成判定

只有当第 1 至第 6 步均已完成，且每一步都有测试、计划/日志回执、独立 commit 和 push，同时满足以下条件，本计划才算完成：

- NPC efficiency sweep 耗时相对于基线明显下降。
- 精确开关事件电流和阻断电压计算未被近似采样替代。
- 周期稳态、实际电流波形、事件损耗和 GUI 显示结果保持正确。
- 不新增 GUI 用户输入。
- 不恢复 `other` 损耗。
- 远端分支包含全部步骤提交，且工作区没有未提交的源码或测试修改。

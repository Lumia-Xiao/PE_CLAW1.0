# LLC 波形工况轻量级修正计划

- 创建日期：2026-09-22
- 状态：全部完成并归档。步骤 1（`ead8279`）、步骤 2（`85d1da8`）、步骤 3（`e955e2e`）均已推送至 `origin/codex/llc-waveform-operating-point-plan`。
- 唯一目标工程：`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`
- 范围：LLC 二极管整流及同步整流的 Waveform Operating Point / Generate Waveforms。
- 当前阶段执行方案 A 的最小修正与定向回归。

## 1. 已确认的问题

界面读取 Vin、Vout 和 load ratio，控制器及工况刷新管线将其传入波形生成函数。但 LLC 后端仅使用 Vin、load ratio 和可选 switching_frequency_hz；Vout 输入未参与计算。实际输出电压来自固定频率 FHA 增益计算，同步整流复用此实现。

当前目录下的默认设计复现：Vin=400 V、开关频率=120 kHz，输入 Vout=36/48/60 V 时，计算输出均为 50 V；此前检查得到波形一致。改变负载率会改变电流波形。正式回归需比较完整数组，不能只比较截图或部分采样摘要。

绘图入口会清空并重画当前报告，暂未发现图片缓存导致的问题。只有改变 Vout 无效的原因已确定；若用户改变 Vin 或负载率后仍看到相同结果，还需复现其具体工况及 GUI 调用链。

启动脚本使用自身目录及当前 `src`，默认输出路径根据模块位置解析到本工程。历史文档中的其他工作区说明和迁移证据属于来源记录，不作为运行配置批量替换。

## 2. 首先确定输入语义

步骤 1 依据当前契约选择方案 A：保持固定频率，后续取消可编辑 Waveform Vout，显示实际 Vout 和实际频率；本轮不新增 GUI 频率输入。这是基于现有契约的实施选择，并非用户已单独确认 A/B。公共 OperatingPoint.vout_v 保留，旧 LLC 调用方传入该字段不作为调频命令。详细公式、兼容行为和边界见 [步骤 1 核查记录](llc_waveform_operating_point_evidence/step1_findings.md)。

| 方案 | 界面与计算行为 | 需要处理的边界 |
| --- | --- | --- |
| A：保持固定频率 | Vin、负载率参与刷新；取消可编辑的目标 Vout，显示计算得到的实际 Vout 和实际频率。是否开放频率输入另行明确。 | 固定频率下 Vout 由电路决定；在谐振点改变负载后 Vout 可以不变，但电流必须正确变化。 |
| B：按目标 Vout 调频 | 保留目标 Vout，固定已设计的 Lr、Cr、Lm、变比和已选硬件，按 Vin、负载及目标 Vout 求工作频率，再生成波形。 | 明确允许频率范围、多解选择规则及无解提示；不得静默沿用旧频率、旧图片或伪称达到目标。 |

选型依据：先核实项目现有 LLC 固定频率契约和历史设计意图，再与期望的产品行为对齐。若采用 B，需明确负载率代表名义负载电阻的缩放还是目标输出功率比例；不得顺带改变其现有定义。

两种方案共同要求：输入、实际计算值、图标题及报告一致；相同输入确定性复现；刷新不重新选择器件、磁件或电容。

## 3. 修改范围与步骤

以下路径均相对于上述唯一目标工程。

### 步骤 1：固化行为与基线（已完成并推送）

- 核实 A/B、负载率语义、频率边界及旧调用方的兼容行为。
- 检查默认工况和用户报告的工况，比较完整波形数组、实际 Vout、频率、电流峰值与 RMS。
- 核实注册、输入规范化、设计候选及 GUI 表单的路由，明确设计输入与波形工况输入的区别。

已覆盖 6 个桥型组合、114 个直接场景、24 次表单到绘图链路检查。完整数组比较确认：只改变目标 Vout 不改变波形；Vin、负载率或频率改变会改变波形。默认全桥额定场景实际 Vout=50 V，iLr 峰值约 17.744196 A、采样 RMS 约 12.833116 A；50% 负载实际 Vout 仍为 50 V，峰值约 9.954512 A、RMS 约 7.470183 A。

用户未提供原始设计参数，具体保存项目尚未复现；本步骤采用默认重建案例，不将其计为用户原始项目验收。新增发现：空 device 报告会触发器件选型；SR 补充审计元数据会替换候选对象但不改变电气参数。该边界及旧增益误差提示纳入后续核查，不在步骤 1 修正运行代码。

验证命令与结果：

```powershell
python -B scripts/build_llc_waveform_operating_point_baseline.py --output Plan/Active/llc_waveform_operating_point_evidence/step1_baseline.json
# 6 个组合全部通过，含 114 个计算场景和 24 个链路检查
python -B -m pytest -q tests/test_llc_fha_boundary_cache.py tests/test_phase7_dc_dc_topologies.py::test_llc_first_pass_boundaries_are_preserved --basetemp pytest_temp/llc-waveform-step1 --junitxml=pytest_temp/llc-waveform-step1-tests.xml
# 6 passed in 24.50s，无失败或跳过
python -B -m pytest --collect-only -q tests -k llc
# 141/714 tests collected (573 deselected)；仅收集，没有执行 141 项回归
git diff --check
```

首次基线运行在 SR 候选对象身份断言处失败。已查明是空器件报告触发选型、补充 metadata/notes，而非电路被重新设计；脚本改为检查所有电气字段、完整 llc_fha 和后续器件选择是否保留，同时将对象变化记录进证据。最终重跑通过，未隐藏该诊断过程。

### 步骤 2：最小修正与定向回归（已完成并推送）

- GUI：`src/pe_claw_gui/app/topology_forms/llc_resonant_converter_diode_rectifier_form.py` 及同步整流继承表单。
- 核心：`src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/waveform.py`，必要时复用 `fha_design.py` 中的增益算法；核对同步整流 `waveform.py` 的委托路径。
- 端到端核对：`app/shell/main_window.py`、`app/controllers/waveform_controller.py`、`pipeline/run_operating_point_refresh.py`、`app/result_views/waveform_view.py`（均位于 `src/pe_claw_gui/` 下）；只修改存在实际缺陷的层。
- 检查应力、已选器件损耗及报告是否使用本次波形；若改变共享模型或报告契约，同步更新相应校验和测试。
- 不扩展 Web 功能，不重写 FHA 为时域仿真，不重做硬件搜索。

执行结果：

- 两类 LLC 表单移除可编辑波形 Vout，显示实际 Vout/频率；变更输入或清空报告时清除旧读数。图标题显示实际值与负载率。
- 波形公式及 114 个原场景的完整数组保持不变，修正越界提示和报告中“求得频率”的误导表述。
- SR 应力改用当前波形支路电流；LLC 当前电压和频率传递到器件损耗适配器，设计选型仍保留既有覆盖电压/SR 角点电流依据。缺少已选器件的 LLC 报告跳过损耗刷新，不再隐式选型。
- 新增 32 项工况回归；仅对齐三个旧效率测试替身的关键字参数签名，原断言保留。初始失败及修复经过见 [步骤 2 核查记录](llc_waveform_operating_point_evidence/step2_findings.md)。
- 新证据为 `llc_waveform_operating_point_evidence/step2_readback.json`，保留步骤 1 JSON 原样；使用说明为 `docs/llc_waveform_operating_point.md`。

验证命令与最终结果：

```powershell
python -B -m pytest -q tests/test_llc_waveform_operating_point.py --basetemp pytest_temp/llc-waveform-step2-final --junitxml=pytest_temp/llc-waveform-step2-final.xml
# 32 passed in 50.73s
python -B -m pytest -q tests -k llc --basetemp pytest_temp/llc-waveform-step2-regression-final --junitxml=pytest_temp/llc-waveform-step2-regression-final.xml
# 173 passed, 573 deselected in 160.99s；包括新增 32 项，无失败或跳过
python -B -m pytest -q tests/test_phase10_structured_output.py tests/test_dc_ac_operating_refresh_gui_chain.py tests/test_npc_loss_model_step5.py tests/test_phase9_operating_point_migration.py --basetemp pytest_temp/llc-waveform-step2-shared --junitxml=pytest_temp/llc-waveform-step2-shared.xml
# 15 passed in 104.94s
python -B scripts/build_llc_waveform_operating_point_baseline.py --output Plan/Active/llc_waveform_operating_point_evidence/step2_readback.json
# 6 个组合、114 个直接场景、24 次表单到绘图数据回读通过
git diff --check
# 通过
```

以上为步骤 2 自动化验证，未替代步骤 3 的最终交互验收。未运行全仓库测试。

### 步骤 3：验收与归档（已完成并推送）

- 覆盖二极管整流的现有桥型组合及同步整流，运行受影响 LLC 拓扑的全部现有工况。
- GUI 连续切换工况并点击 Generate Waveforms，核对当前输入、标题、坐标刻度、报告及波形数据。自动缩放可能使曲线外形相似，不要求每次截图外形明显不同。
- 记录命令、通过/失败/跳过数及边界证据，更新 ChangeLog。依仓库流程，每个实施步骤验证、提交并推送到指定分支后才标记完成；全部验收后归档到 `Plan/completed/`。

执行结果：

- 真实 MainWindow/Entry/按钮 invoke/TkAgg 全链路覆盖 6 种桥型、84 次波形按钮回调（72 次成功生成、12 次预期非法输入拒绝）。完整数组与原基线一致；重复/切换/恢复、实际值、图标题、坐标、应力、损耗和结构化报告一致，无重新设计或器件选型。
- 发现默认 860 像素高窗口中波形按钮位于 y=984，不可见；仅为 LLC 表单添加纵向滚动条。6 种桥型在 1400×860 和最小 1240×760 下均可滚动到工况控件，新增布局回归通过。
- 全部 LLC 测试：174 passed、573 deselected in 172.50s；共享 GUI/报告/刷新测试：21 passed in 130.32s；独立布局测试：1 passed in 5.96s。均无失败、错误或跳过。命令和范围见 [步骤 3 验收记录](llc_waveform_operating_point_evidence/step3_findings.md)，生成 JSON 为 `llc_waveform_operating_point_evidence/step3_gui_acceptance.json`。
- 计划及证据归档到 `Plan/completed/`，步骤 1/2 JSON 原样保留，测试基线路径同步更新。上文 Active 命令为历史执行记录；当前复现请使用验收记录中的命令，输出到临时目录。
- 归档后再次运行工况定向测试：32 passed in 43.50s，无失败或跳过；`git diff --check` 通过。
- 本次为程序化真实控件验收，未宣称人工鼠标验收；未提供用户原始工程参数，仍用默认重建案例。未运行全仓库测试；GUI 验收未执行磁件/电容选型，其现有 LLC 用例纳入拓扑回归。

## 4. 验证矩阵与命令

| 验证项 | 验收条件 |
| --- | --- |
| 相同输入重复生成 | 完整波形数组和主要计算结果一致。 |
| 分别改变 Vin、负载率 | 对应电压、电流及报告按模型变化；不读取上次工况。 |
| Vout 行为 | A：不再呈现无效的可编辑目标 Vout；B：可达目标在明确容差内达到，并输出求得的频率。 |
| 边界与异常 | 零/负负载、非法电压、频率范围边界有明确行为；B 额外覆盖无解、多解和频率越界。 |
| 硬件与结果一致性 | candidate 及已选硬件不变，波形、应力、损耗使用同一当前工况。 |
| 绘图更新 | 当前报告的数据进入绘图；数值变化可从标题、刻度或曲线读回。 |

已新增定向测试 `tests/test_llc_waveform_operating_point.py`。后续验收可复用以下命令：

```powershell
python -B -m pytest -q tests/test_llc_waveform_operating_point.py
python -B -m pytest --collect-only -q tests -k llc
python -B -m pytest -q tests -k llc --basetemp pytest_temp/llc-waveform-operating-point
git diff --check
```

若修改共享模型、管线或报告，再运行对应合同回归；纯文档计划阶段只检查路径、内容、差异和 Git 状态，不声称已执行上述测试。

## 5. 执行记录

| 日期 | 内容 | 状态 |
| --- | --- | --- |
| 2026-09-22 | 整理已确认根因、模型决策点、最小修改范围及验证矩阵 | 计划编写完成；实现未开始 |
| 2026-09-22 | 步骤 1：公式、注册/表单/刷新路由核查；基线脚本、JSON 证据及定向测试 | `ead8279` 已推送到 `origin/codex/llc-waveform-operating-point-plan`；步骤 2/3 未开始 |
| 2026-09-22 | 步骤 2：实际值显示、应力/损耗刷新一致性及定向回归 | `85d1da8` 已推送到 `origin/codex/llc-waveform-operating-point-plan`；步骤 3 未开始 |
| 2026-09-22 | 步骤 3：真实按钮验收、LLC 表单滚动修正、全部 LLC/共享回归及计划证据归档 | `e955e2e` 已推送到 `origin/codex/llc-waveform-operating-point-plan`；全部步骤完成 |

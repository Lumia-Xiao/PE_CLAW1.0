# LLC 工况步骤 1：行为契约与基线

日期：2026-09-22。目标工程：`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`。

## 修正方向

依据现有实现采用计划方案 A：保留固定频率波形模型，后续取消 GUI 无效的可编辑 Waveform Vout，显示实际输出电压及实际开关频率。本步骤未改变模型。此为依据当前契约作出的实施选择，不声称用户已经单独确认 A/B。

本轮不新增 GUI 频率输入；实际频率以现有解析优先级为准。设计区的 Vout min/nom/max 继续表示设计覆盖目标，不替换成波形实际电压。若后续明确要求闭环调频，需要单独确定调频控制和多解规则，不能把当前固定频率代码直接当成调频控制器。

## 计算及兼容契约

令 n 为变比，kpri 为桥型增益因子，λ 为负载率：

```text
Rnom = Vout_nom² / Pout_max                  （新设计）
Rload = Rnom / max(max(λ, 0), 1e-12)         （当前波形实现）
Rac = (8 / π²) · n² · Rload
Q = Zr / Rac; fn = fs / fr
Vout_actual = FHA_gain(fn, Ln, Q) · kpri · Vin / n
Pout_actual = Vout_actual² / Rload
```

- 固定硬件导入时 Rnom 可以来自硬件快照，不必等于新设计公式。λ 是负载电导相对名义值的比例；实际功率由实际电压和电阻决定。在谐振点 FHA 增益为 1，变负载时 Vout 可以不变，而电流变化。
- 频率优先级：`OperatingPoint.switching_frequency_hz` → `candidate.metadata.llc_fha.commanded_switching_frequency_hz` → `candidate.fs_hz`。二极管 schema 对缺省命令频率使用频率上下限几何平均；默认为 120 kHz。同步整流候选通常没有命令频率字段，落到 `candidate.fs_hz`。
- `operating_point=None` 时使用候选名义 Vin 和负载率 1.0，不读取候选中保存的 load_ratio；这是现有兼容行为，应显式保留或另列修正。
- `vout_v=None` 或提供不同 Vout 都不影响当前波形。公共 OperatingPoint 字段供其他拓扑使用，不能为修正 LLC 而删除；后续 LLC GUI 应不再发送无效目标，旧调用方仍可传入但不当作控制指令。
- 设计 schema 要求命令频率在闭区间内、0 < λ ≤ 1。波形接口目前不同：非正 Vin/fs 抛错；零/负 λ 被夹为近似空载；λ > 1 可计算；正频率越界仍生成诊断波形，`operating_point_feasible=False`。该标志只判断频率范围，不能理解为已经满足目标 Vout 或所有器件约束。
- 越界提示错误地说“未达到 2% 增益误差容差”，但固定频率代码未执行这种目标求解。步骤 2 应修正文案，不暗改公式；对零/负 λ 的严格化或过载限制需显式标记为兼容变化，不能随 UI 修正悄悄加入。

## 注册和数据流核查

全部路径相对于目标工程：

| 层 | 入口与核查结论 |
| --- | --- |
| 注册 | `src/pe_claw_gui/topologies/base/registry.py` 的 `get_plugin/get_form_class` 解析两个 LLC 拓扑；同步整流表单继承二极管工况表单。 |
| 设计输入 | `app/topology_forms/llc_placeholder_form.py` 的 Vout 范围、功率和频率范围进入设计 raw_input；`topologies/dc_dc/llc_resonant_converter_*/input_schema.py` 规范化到 spec。上述相对路径均位于 `src/pe_claw_gui/` 下。 |
| 设计计算 | `fha_design.py` 的 `solve_operating_frequency` 用于覆盖范围检查，按目标增益搜索且容差为 2%；候选合成保留 Lr、Cr、Lm、变比、fr 和名义负载。设计覆盖求频率与刷新固定频率是两个不同用途。 |
| 表单事件 | `app/shell/main_window.py::_on_generate_waveforms` 先检查设计 raw_input 是否变化，再读取独立 operating_vars；`run_design_controller.py::ensure_active_topology_current` 只有设计输入变化或没有候选才重新设计。 |
| 刷新 | `app/controllers/waveform_controller.py` → `pipeline/run_operating_point_refresh.py` → 插件 `generate_waveforms`；同步整流委托二极管实现。 |
| 显示 | `app/shell/workspace.py::render_report` 把同一报告交给 `waveform_view.py`；后者清空 figure 并绘制当前四个完整数组，不加载磁盘旧图片。 |
| 报告 | `reports/structured_output.py` 分别保存 operating_point 输入 Vout 和 waveform 实际 Vout；现状二者可能不同，后续显示不能把前者误标成实际值。 |

本地 Git 历史中 waveform 文件由 `b81dcab` 引入时已经是固定频率实现，未找到本仓库内直接删除 `operating_point.vout_v` 使用的提交。不能据此声称已确认发生变更的历史提交。

## 基线证据和验证范围

生成脚本：`scripts/build_llc_waveform_operating_point_baseline.py`。
机器证据：同目录 `step1_baseline.json`。记录原始设计输入、源码基准提交、候选散列、全部数值数组的 SHA-256、逐数组完整相等比较及最大绝对差，以及实际 Vout、频率、功率、电流峰值与采样 RMS。

- 6 个桥型组合：二极管整流 2 种原边 × 2 种副边，同步整流 2 种原边。
- 每组合 19 个直接波形场景：默认/重复/None、三个 Vout 变体、Vin 上下限、10%/50%/零/负/过载、非法 Vin、频率上下边界/越界/零。
- 每组合另有 4 次表单→设计一致性检查→控制器→实际工况管线→绘图数据回读。使用隐藏 Tk 表单、Agg 绘图画布，不宣称人工点击过用户当前窗口；断言四条曲线逐样本等于当前报告，连续刷新后没有累积旧曲线。
- 默认测试工况为重建案例；用户未提供其原始设计参数和具体切换值，因此这不是对用户保存项目的逐项复现。
- 直接波形输入候选保持未变。GUI 链起始使用无器件的最小报告，发现 `run_device_operating_point_refresh` 在缺少 device 时调用选型流程。同步整流会以新 candidate 对象写入器件审计 metadata/notes，电气字段及 llc_fha 保持不变。最初对象身份断言因此失败；核实根因后改为严格检查电气字段与 llc_fha，并记录变化字段，未删除实际波形断言或掩盖选型行为。
- 此缺省报告路径与上层“不得重新选型”的注释不一致，列为后续边界项。正常完整 GUI Run Design 已包含选型；本步骤只验证首次补充后后续刷新保留所选器件，不声称完成已选磁件、电容或损耗精度验收。

验证命令及最终结果另记于主计划步骤 1 回执。步骤 2/3 未执行。

# 步骤 2 修正及验证记录

日期：2026-09-22。目标工程：`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`。

## 最终修改

- 两个 LLC GUI 共用工况表单，仅输入 Vin/负载率；不再发送无效 Vout。实际 Vout 和频率为只读标签。新输入、空报告、未生成波形时清空旧读数。
- 图标题分两行显示 Vin、实际 Vout、频率、负载率。保持原有完整波形数据和自动缩放。
- 保持固定频率公式、负载定义及公共 OperatingPoint 字段兼容，频率越界提示改为“超出配置范围”。设计覆盖使用调频，与波形固定频率明确区分。SR 摘要增加当前波形参数，旧 timing/loss metadata 标为设计点。
- 核查发现 SR stress 原先忽略 waveform_set，导致电流应力不能随负载变化。现在复用现有 FHA 支路 peak/RMS/average 提取；二极管和 SR 当前电压应力取 Vin/Vout，中心抽头副边为 2×Vout，器件适配器采用当前波形频率与周期。未引入新波形物理模型。
- 器件设计选型继续保留原有依据：二极管使用波形电流和覆盖角点电压；SR 使用覆盖角点应力；设计点适配频率保持原候选频率。当前工况则使用本次波形应力和频率。增加回归防止刷新修正影响选型边界。
- LLC 空器件报告不再隐式调用选型，记录跳过原因；有既定器件时复用所选器件和散热设计，更新 current_operating_losses。
- 结构化报告字段/单位/schema 未改变；测试核对空的输入 Vout 与 waveform.operating 下实际 Vout 的区别。补充 `docs/llc_waveform_operating_point.md`。

## 证据

`step1_baseline.json` 保持不变。新测试在 6 个桥型组合的全部 114 个原场景上比较完整数组散列及边界结果，保证固定频率波形算法未漂移；包含正常、近似空载、过载、非法输入和频率越界。

`step2_readback.json` 由更新后的基线脚本生成，记录 114 个直接场景和 24 次连续 GUI 表单→控制器→实际管线→Agg 绘图的数据回读。其 source_revision 是修改前基准 `7fcbde8`，采集时使用本次提交中的工作区代码；它不是该基准提交的原始结果。原始用户工况未提供，使用默认设计重建。

新增测试还检查已选器件不重选、损耗随负载变化、应力和频率到达损耗适配器、保留设计点选型依据。隐藏 Tk 表单和 Agg 图回读验证不等同于对用户当前打开窗口的人工验收，最终交互验收保留给步骤 3。

图表预览已生成并目视检查：`pytest_temp/llc-waveform-step2-preview.png`，900×700，标题和曲线无遮挡；临时图片不提交。

## 排错与范围限制

- 新测试首次误用 `waveform.operating_point`，实际既有 schema 为 `waveform.operating`；只修正测试字段路径，没有调整生产 schema。
- 一次逐用例建立 Tk 的测试遇到 tk.tcl 初始化失败。改为模块内共享一个 Tk 实例，逐表单销毁，重跑全部 GUI 用例通过，没有 skip。
- 全量 LLC 初次回归 164 passed / 3 failed；三个失败均为 `test_llc_efficiency_manifest_step7.py` 中已有 lambda 替身不接收生产函数已有的 `npc_periodic_initial_current_a` 关键字。生产效率扫描文件在此修改前后无差异。只补充测试替身的明确关键字签名，保留全部结果断言；该文件随后 10 passed。
- 磁件/电容重选、调频控制、真实时域仿真均未扩展。本次未执行全仓库测试，也未执行步骤 3 的最终交互验收和归档。

最终测试命令、结果及提交推送回执见主计划。

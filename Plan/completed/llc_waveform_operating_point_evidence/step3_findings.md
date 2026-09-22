# 步骤 3：真实 GUI 链路验收与归档

日期：2026-09-22。验收起点为 `d5771d2`，包含本步骤工作区中的 LLC 表单滚动修正。生成证据的 `source_revision` 记录脚本运行时的 HEAD；本步骤最终提交另见主计划推送回执。

## 实际发现与修正

默认主窗口为 1400×860。在当前 Windows/Tk 缩放环境，LLC 表单请求高度为 980，Generate Waveforms 按钮位于窗口内部 y=984，高 31 像素，已被窗口底部截断。此前表单/Agg 测试不会发现此问题。

`app/shell/workspace.py` 为两类 LLC 左侧表单增加纵向 Canvas/Scrollbar，内容按实际请求宽度布局，切换拓扑时随 workspace 销毁。没有更改计算公式或选型策略。新增 GUI 回归检查 1400×860 和最小 1240×760 下滚动后工况输入、实际读数及按钮均在可视区域内，并检查返回分类页后的清理。

## 可复现验收

新增脚本 `scripts/verify_llc_waveform_gui.py`：创建真实 `PEClawMainWindow`，通过 Entry 的 delete/insert 修改工况，调用真实 ttk 按钮的 invoke，执行 MainWindow/controller/pipeline/workspace 全链路与 FigureCanvasTkAgg 绘制。设计与器件选型是真实计算；仅拦截弹窗记录和输出目录，不替换计算结果。

- 6 种桥型，每种运行一次 Run Design、14 次 Generate Waveforms，共 84 次波形按钮回调。
- 每种包含额定、重复、Vin 最小/最大、50%/10%/零/负负载、150% 负载、恢复额定 10 次成功生成，以及两次非法输入拒绝和两次恢复生成。总计 72 次成功生成、12 次预期拒绝，无意外错误。
- 60 次连续场景逐次核对所有数值数组的完整散列与步骤 1 基线一致，核对图表四条曲线完整 X/Y 数据、标题、坐标范围与刻度、只读实际值、应力/损耗文本、结构化报告当前值；另 12 次错误恢复核对额定完整数组散列一致。
- 额定→半载电流纵轴范围变化；重复和恢复额定得到相同完整数组。Vin=360/400/420 V 的实际 Vout=45/50/52.5 V。
- 全桥二极管额定/半载的单个主开关支路 RMS 为 9.075188/5.283600 A（不是谐振电感 RMS）；对应主开关导通损耗记录为 0.103772/0.035175 W，整流器导通损耗记录为 73.747606/36.873803 W。
- 全过程候选对象与全部候选字段不变、已选器件及设计点损耗不变、Run Design 调用次数保持每种一次；当前导通损耗随负载改变。
- 非数值 Vin 弹出 `Operating Vin [V] must be a valid number.`；零 Vin 弹出 `Fixed-frequency LLC waveform inputs must be positive.`。失败时实际读数为空，原成功报告/图表保留；输入修正后生成恢复，不将错误输入计为成功。
- 两种窗口尺寸下，6 种桥型均能滚动到波形按钮。额定及半载实际 Tk 画布导出 PNG 已目视检查标题、刻度及曲线排版，图片保留在本地 `pytest_temp/llc-waveform-step3-gui/`。

执行时证据尚位于 Active，因此初次命令显式传入 `--baseline Plan/Active/llc_waveform_operating_point_evidence/step1_baseline.json` 并输出到同目录。归档后的复现命令（输出到临时目录，避免覆盖冻结证据）：

```powershell
python -B scripts/verify_llc_waveform_gui.py --output pytest_temp/llc-waveform-step3-replay.json
python -B -m pytest -q tests/test_phase10_gui_integration.py::test_llc_waveform_controls_reachable_at_default_and_minimum_window_size --basetemp pytest_temp/llc-waveform-step3-layout --junitxml=pytest_temp/llc-waveform-step3-layout.xml
python -B -m pytest -q tests -k llc --basetemp pytest_temp/llc-waveform-step3-regression --junitxml=pytest_temp/llc-waveform-step3-regression.xml
python -B -m pytest -q tests/test_phase10_structured_output.py tests/test_dc_ac_operating_refresh_gui_chain.py tests/test_npc_loss_model_step5.py tests/test_phase9_operating_point_migration.py tests/test_phase10_gui_integration.py tests/test_phase2_gui_bootstrap.py --basetemp pytest_temp/llc-waveform-step3-shared --junitxml=pytest_temp/llc-waveform-step3-shared.xml
python -B -m pytest -q tests/test_llc_waveform_operating_point.py --basetemp pytest_temp/llc-waveform-step3-archive --junitxml=pytest_temp/llc-waveform-step3-archive.xml
```

## 验收范围与证据保留

最终测试结果：新增布局定向测试 1 passed in 5.96s；全部 LLC 测试 174 passed、573 deselected in 172.50s（包括新增布局回归，原 114 个直接场景完整数组/边界均通过）；共享 GUI/报告/工况测试 21 passed in 130.32s。三个测试命令均无失败、错误或跳过。布局问题在验收探测中发现并修正，随后正式按钮脚本与测试首次执行均通过，没有将意外失败改成跳过。

归档后定向回归再次通过：32 passed in 43.50s，无失败或跳过；确认测试从 completed 路径读取原始基线。`git diff --check` 通过。

这是程序化真实控件/回调验收，不声称人工鼠标操作验收；用户未提供最初项目参数，使用默认重建设计。GUI 未新增频率/Vout 输入，其后端边界由 6×19 个原始场景回归覆盖。零/负负载沿用近似空载处理，FHA 不模拟真实空载控制或寄生瞬态。

该按钮验收未执行 Run Magnetics/Run Capacitor，不能据此声称所有已选磁件/电容的实物精度；这些模块的现有 LLC 测试包含在 LLC 回归中。未运行全仓库测试。

计划与证据一起归档到 `Plan/completed/`，定向测试的基线路径同步更新。步骤 1/2 JSON 原样保留，其历史命令和嵌入路径仍为来源记录；文件 SHA-256 分别为 `fdef156c9068267f778b5d51368bf1d50708fddb2f1b1f9d6a033bf614677dab`、`5e784f35e6258939c8bd785174142f5e3ec26fb28da3e29b72a72017557d1b6f`。

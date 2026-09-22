# LLC 目标输出电压自动调频修正

- 日期：2026-09-22
- 工程：`C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`
- 分支：`codex/llc-waveform-operating-point-plan`
- 状态：已完成并归档；实现与验收提交 `54c6b99` 已推送至 `origin/codex/llc-waveform-operating-point-plan`。
- 依据：用户明确要求按输入电压、输出电压和负载自动求频率。这替代已归档三步计划的固定频率 GUI 选择；旧计划及证据保留为历史，不作为当前产品行为。

## 本次单项修正

恢复 LLC/SR 工况目标 Vout 输入，固定已设计谐振参数及器件；在已有 fs_min/fs_max 范围内求 FHA 增益根并生成波形。负载率沿用 Rnom/load 定义，多解取最高频率，无解或非法输入明确报错、清除旧图及结果显示、保留硬件供重试。显式频率后端诊断调用和无目标旧调用保持兼容。

原设计覆盖搜索为 1501 点扫描、2% 覆盖误差容限，不足以当作目标调压器；本次复用同一 `llc_fha_gain`，增加精确的有界逆求解，不改变覆盖扫描、候选搜索或选型依据。令 x=fn²，1/M²=(A−B/x)²+Q²(x−2+1/x)，A=1+1/Ln，B=1/Ln；其导数符号由 Q²x³+(2AB−Q²)x−2B² 决定。正根唯一，故以增益峰值划分最多两个单调区间，分别二分求解，避免网格漏掉邻近峰值的两根及切点。误差为数值求解误差，不是实物精度或 ZVS 保证。

涉及 FHA/waveform、LLC 共用表单、标题/evaluator、主窗口错误显示、电容工况频率及效率扫描工况传递；不重做磁件模型。报告 schema 和单位不变，既有目标/实际字段解释补充到说明和字段字典。

## 验收

```powershell
python -B -m pytest -q tests/test_llc_automatic_frequency.py tests/test_llc_waveform_operating_point.py --basetemp pytest_temp/llc-auto-frequency-focused --junitxml=pytest_temp/llc-auto-frequency-focused.xml
python -B -m pytest -q tests -k llc --basetemp pytest_temp/llc-auto-frequency-regression --junitxml=pytest_temp/llc-auto-frequency-regression.xml
python -B scripts/verify_llc_waveform_gui.py --output Plan/Active/llc_automatic_frequency_evidence/gui_acceptance.json
python -B scripts/build_llc_waveform_operating_point_baseline.py --output Plan/Active/llc_automatic_frequency_evidence/compatibility_and_gui.json
python -B -m pytest -q tests/test_phase10_structured_output.py tests/test_dc_ac_operating_refresh_gui_chain.py tests/test_npc_loss_model_step5.py tests/test_phase9_operating_point_migration.py tests/test_phase10_gui_integration.py tests/test_phase2_gui_bootstrap.py --basetemp pytest_temp/llc-auto-frequency-shared --junitxml=pytest_temp/llc-auto-frequency-shared.xml
```

验收六种桥型的 Vin/Vout/load 变化、多根/无根/端点/切点、非有限值/零负载拒绝、显式频率兼容、完整波形差异与重现、硬件不变、应力/损耗/电容/效率扫描频率一致性，以及真实 GUI 按钮和错误恢复。定向 57 passed in 65.53s；全部 LLC 199 passed、573 deselected in 204.11s；共享 GUI/结构化报告/工况 21 passed in 139.27s，均无失败、错误或跳过。真实 GUI 验收 144 次按钮回调通过（102 次成功、42 次预期拒绝及恢复），兼容脚本 114 个直接场景和 24 次表单链路通过。图表排版与 git diff --check 已检查。

详细数值和限制见 [验收记录](llc_automatic_frequency_evidence/findings.md)。计划与证据验收后一起归档至 completed；上面的 Active 是实际执行命令，后续复现请将 JSON 输出到 pytest_temp，避免覆盖冻结证据。未运行全仓库测试。

归档证据中的 114 个固定频率场景通过显式指定原频率重放；不改旧 JSON，不将过去“忽略 Vout”行为误记为当前需求。当前 GUI 证据记录输入目标、实际值和求得频率；用户未提供具体项目参数，使用默认重建案例。

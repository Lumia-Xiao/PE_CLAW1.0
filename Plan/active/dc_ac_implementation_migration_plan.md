# PE-Claw DC-AC 实现迁移专项计划

## 1. 计划信息

| 项目 | 内容 |
| --- | --- |
| 计划状态 | `active`，第 11 步主体已完成验证，等待主体 commit/push 回执 |
| 建立日期 | 2026-08-27 |
| 计划类型 | DC-AC 实现及 GUI 运行链路专项迁移 |
| 源工程 | `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw` |
| 源仓库 | `PE-Claw_2.0` |
| 源基线 | `main`，计划建立时记录为 `6726f50` |
| 目标工程 | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| 目标仓库 | `PE_CLAW1.0` |
| 目标基线 | `master`，计划建立时记录为 `e8b5eac` |
| 目标目录 | `Plan\active` |
| 关联总计划 | `Plan\active\complete_migration_2_to_1_plan.md` |
| 关联专项计划 | `Plan\active\psfb_duty_policy_fix_plan.md` |
| 计划目标 | 将源工程已实现的三种 DC-AC 拓扑迁移到目标工程并打通 GUI 波形流程 |

本计划只处理 DC-AC 运行能力及其直接依赖。不会把整个源工程无差别复制到
目标工程，也不会迁移 AI Design、agentic、skills 或 md-first 设计请求执行链路。

## 1.1 每一步的强制提交和推送规则

本条是本计划的硬性执行规则，适用于第 0 步至第 11 步，包括只有基线、矩阵、
证据或文档产物的步骤：

```text
开始本步
  -> 只实施本步范围内的修改或产物
  -> 执行本步 focused validation
  -> 检查 git diff / git status / git diff --check
  -> 排除 outputs、__pycache__、.pytest_cache 和无关变更
  -> 创建本步唯一的独立 commit
  -> push 本步 commit 到 origin/codex/sync-gui-backend-from-2
  -> 记录 commit hash、push 结果、验证命令和证据路径
  -> 只有以上全部成功，才能开始下一步
```

具体要求：

1. 每一步必须独立 commit；不得把多个步骤合并成一个 commit 后再一次性 push。
2. 每一步必须独立 push；不得在最后一步集中补推前面步骤。
3. 默认 push 目标为 `origin/codex/sync-gui-backend-from-2`，除非用户明确指定其他分支。
4. commit message 必须包含本计划规定的步骤标识，便于从远端提交历史审计执行顺序。
5. push 失败时，本步状态保持 `in_progress` 或 `blocked`，不得进入下一步，也不得在计划中标记为 `completed`。
6. 只有远端确认 push 成功后，才允许更新本计划中的本步状态和 commit/push 记录。
7. 每步 push 前必须确认没有提交目标工程已有的无关用户修改、生成文件或源工程绝对路径。
8. 不执行 force-push，不改写远端历史，不直接向目标 `master` push。
9. 本计划获得用户批准后，阶段性 commit 和 push 是每一步的必要交付动作，不再适用“完成后再统一请求 push”的流程。

## 2. 当前问题和迁移目标

### 2.1 已确认问题

目标工程的旧版本存在以下边界：

1. `app/category_views/dc_ac_page.py` 是 DC-AC 占位页。
2. `topologies/dc_ac/__init__.py` 是占位包。
3. 目标工程的默认 registry 没有返回 DC-AC 拓扑。
4. 因此目标工程没有可执行的 DC-AC form、plugin 和 waveform backend。
5. 用户点击 `Generate Waveforms` 时无法进入真正的 DC-AC 生成链路。

源工程已经具备以下三种实现，并且源工程的后端最小复现已成功：

| 拓扑 ID | 源工程状态 | 目标结果 |
| --- | --- | --- |
| `single_phase_full_bridge_inverter` | 已实现 | GUI 可选、可设计、可生成波形 |
| `three_phase_two_level_voltage_source_inverter` | 已实现 | GUI 可选、可设计、可生成波形 |
| `three_phase_three_level_npc_inverter` | 已实现 | GUI 可选、可设计、可生成波形 |

### 2.2 迁移后的目标行为

三种拓扑都必须支持：

```text
DC-AC category
  -> topology selection
  -> topology form
  -> Run Design
  -> Generate Waveforms
  -> Waveform result view
```

在对应源工程能力已经存在时，还必须保持以下后续链路：

```text
Run Capacitor
  -> Run Magnetics
  -> Run Efficiency Sweep
  -> Devices / Loss / Thermal / Hardware Overview
```

迁移要求保持源工程的单位、字段名、拓扑 ID、设计点与 operating-point refresh
的边界，以及明确的 first-pass 限制说明。不得为了让按钮表面可用而在 GUI 中直接
实现计算逻辑。

## 3. 迁移范围

### 3.1 必须迁移的 DC-AC 拓扑代码

每个拓扑目录必须整体审查并按依赖迁移：

```text
src/pe_claw_gui/topologies/dc_ac/__init__.py
src/pe_claw_gui/topologies/dc_ac/single_phase_full_bridge_inverter/
src/pe_claw_gui/topologies/dc_ac/three_phase_two_level_voltage_source_inverter/
src/pe_claw_gui/topologies/dc_ac/three_phase_three_level_npc_inverter/
```

每个已实现拓扑通常包括：

- `__init__.py`：插件对象和公共导出；
- `input_schema.py`：默认输入、字段转换和校验；
- `synthesizer.py`：电气参数和 candidate 合成；
- `waveform.py`：operating-point 波形生成；
- `stress.py`：电压电流应力提取；
- `evaluator.py`：拓扑评估和 report 构建。

### 3.2 必须同步迁移的 GUI 代码

- `app/category_views/dc_ac_page.py`；
- 三个 DC-AC topology form；
- `app/shell/main_window.py` 中的 DC-AC 按钮回调和当前表单刷新逻辑；
- `app/shell/workspace.py` 中的 DC-AC form、result tab 和 report render 路由；
- `app/controllers/waveform_controller.py`；
- `app/controllers/run_design_controller.py`；
- `app/result_views/waveform_view.py`；
- `app/result_views/summary_view.py`、`stress_view.py`、`loss_view.py`、
  `hardware_overview_view.py` 中的 DC-AC 分支；
- DC-AC 拓扑图片和 package-data 配置。

### 3.3 必须迁移或合并的共享依赖

最终清单以 import closure 和测试结果为准，初始审查范围如下：

- `models/waveform.py`、`models/operating_point.py`、`models/design_report.py`；
- `models/candidate.py`、`models/stress_result.py`、`models/device_result.py`、
  `models/loss_result.py`、`models/magnetic_result.py`、`models/thermal_result.py`、
  `models/capacitor.py`、`models/geometry_result.py`；
- `topologies/base/` 的 plugin、registry、spec、candidate、result 契约；
- `pipeline/run_topology_pipeline.py`；
- `pipeline/run_full_pipeline.py`；
- `pipeline/run_operating_point_refresh.py`；
- DC-AC 使用到的 device、capacitor、magnetic、loss、thermal、geometry pipeline；
- `topology_capabilities.py`；
- `engines/devices/inverter_segmented_loss.py` 及其直接依赖；
- DC-AC 使用到的器件库、封装数据、电容库和磁性数据；
- `pyproject.toml`、`requirements.txt` 中的必要依赖和 package-data 声明。

### 3.4 明确排除范围

以下内容不在本计划迁移范围内：

- `src/pe_claw_gui/agentic/`；
- `src/pe_claw_gui/agents/`；
- `skills/`；
- md-first design request parser、runner、execution gate、session artifact 和 agentic report；
- 与 DC-AC 无直接依赖的其它 2.0 新功能；
- `outputs/`、`__pycache__/`、`.pytest_cache/`、临时日志和本地虚拟环境；
- 源工程 `.git/`；
- 源工程已经生成的设计结果、截图和历史 replay 输出。

## 4. 迁移原则

1. 以源工程指定 commit 的行为作为参考基线，以目标工程 Git 历史作为发布基础。
2. 相同路径文件必须先做语义 diff，再决定合并、替换或保留，禁止盲目覆盖。
3. 先迁移公共数据契约和 pipeline，再迁移 topology 和 GUI，减少临时兼容代码。
4. 任何同名模型字段、单位、状态或错误语义变化，都必须有测试和记录。
5. GUI 只负责采集输入、调用 controller 和显示 report；计算必须留在 backend。
6. 设计点硬件选择与 operating-point refresh 必须保持分离。
7. 源工程的 first-pass 限制必须原样保留并在结果页面可见，不得夸大为完整仿真。
8. 每一阶段都有独立验证和提交点；阶段未通过时停在上一通过提交点。
9. 不删除目标工程已有用户文件、migration evidence、golden baseline 或设计结果。
10. 不通过弱化断言、跳过测试或删除拓扑来制造“迁移成功”。

## 5. 实施前基线工作

### 第 0 步：确认授权和工作副本

安排：

1. 用户确认本计划后，才开始复制或修改 runtime 文件。
2. 重新读取源工程和目标工程的 `AGENTS.md`、`README.md`、`DEVELOPMENT.md`。
3. 记录源工程和目标工程的 commit、branch、remote 和 worktree 状态。
4. 对目标工程现有未跟踪的 `outputs/`、`__pycache__/` 等内容只读检查，确认不覆盖。
5. 按目标工程规则创建周备份；备份失败则停止迁移。
6. 创建或确认专用迁移分支，禁止直接在目标 `master` 上做实现提交。

本步提交/推送：

- commit message：`chore: record dc-ac migration baseline`；
- commit 内容：基线记录、备份记录、迁移分支记录和本计划执行状态；
- focused validation：基线命令、备份校验、目标启动/import smoke test、`git diff --check`；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：commit 创建成功且 push 成功，并在执行记录中写入 commit hash 和远端结果。

产物：

- 源/目标基线记录；
- 备份记录；
- 迁移分支记录；
- 迁移前测试和启动 smoke test 结果。

验收门：目标 worktree 的原有用户变更已识别，备份可恢复，且迁移范围获得批准。

### 第 1 步：建立文件、import 和数据依赖矩阵

安排：

1. 列出源工程 DC-AC 目录、表单、controller、pipeline、model、engine、library 和 tests。
2. 对源工程和目标工程同路径文件计算 SHA-256 并做语义比较。
3. 从 `pe_claw_gui.app.main`、`PEClawMainWindow`、registry 和三个 plugin 开始递归分析 import。
4. 将依赖分为 `add`、`replace`、`merge`、`keep`、`adapt`、`exclude`。
5. 记录每个 DC-AC import 需要的静态资源、器件记录、图片和输出目录。
6. 搜索依赖闭包中的 `agentic`、`agents`、`ai_design` 和 skills 引用。
7. 对混合用途模块标为 `adapt`，不得因一个 agentic 测试引用它就复制整个 agentic 目录。
8. 固化一份迁移矩阵，后续每次新增文件都必须先更新矩阵。

建议矩阵字段：

```text
source_path, target_path, classification, direct_owner, imports,
package_data, tests, conflict, action, status, evidence
```

验收门：三种拓扑的代码、GUI、模型、pipeline、工程数据和测试依赖均有明确归属，
没有 `review_required` 的未决 runtime 文件。

本步提交/推送：

- commit message：`docs: add dc-ac migration dependency matrix`；
- commit 内容：文件矩阵、import closure、package-data 清单、排除清单和测试映射；
- focused validation：矩阵完整性检查、禁止依赖搜索、源/目标路径检查、`git diff --check`；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：矩阵无未决 runtime 项，commit 和 push 均成功。

## 6. 分阶段迁移安排

### 第 2 步：迁移目标工程的基础包和公共契约

安排：

1. 合并必要的 `pyproject.toml`、`requirements.txt` 和 package-data 配置。
2. 确保 `pe_claw_gui`、`app`、`models`、`pipeline`、`topologies` 的包入口一致。
3. 迁移 `WaveformSet`、`OperatingPoint`、`DesignReport` 及 DC-AC 直接使用的模型字段。
4. 迁移 `TopologyPlugin`、`TopologyRegistry`、`TopologyDefinition` 和 `TopologySpec` 契约。
5. 保持目标工程已有 DC-DC 模型兼容；出现字段冲突时合并调用方和测试。
6. 将 `dc_ac` category 纳入 converter category metadata。
7. 加入 registry 唯一性、模型构造和 package import 测试。

验收门：目标工程可以导入公共模型和 registry；没有 DC-AC runtime 对 agentic 模块的依赖。

本步提交/推送：

- commit message：`refactor: merge shared dc-ac runtime contracts`；
- commit 内容：基础包配置、公共模型、topology base contract 和 category metadata；
- focused validation：公共 import、模型构造、registry contract、目标已有 DC-DC smoke test；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：公共契约测试通过，commit 和 push 均成功。

### 第 3 步：迁移 DC-AC registry 和 category page

安排：

1. 将三个 topology definition 加入 `topologies/base/registry.py`。
2. 每个 definition 指向正确的 module path、form path、form class 和 `implemented=True`。
3. 替换目标 DC-AC 占位页为源工程的 topology card/list 页面。
4. 迁移必要的 topology PNG，并使用 package resources 加载，不写绝对本地路径。
5. 测试 `list_topologies("dc_ac")` 的拓扑数量、ID、显示名称和实现状态。
6. 测试 registry 能加载三个 plugin 和三个 form class。

验收门：GUI 可看到三个 DC-AC 拓扑；三个 plugin/form 均可通过 registry 加载。

本步提交/推送：

- commit message：`feat: register dc-ac topology family`；
- commit 内容：三个 registry definition、真实 DC-AC category page 和拓扑图片资源；
- focused validation：registry 数量/ID/实现状态测试、plugin/form import 测试、资源加载测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：三个拓扑可被 GUI 发现并加载，commit 和 push 均成功。

### 第 4 步：迁移并验收单相全桥逆变器

安排：

1. 迁移 `single_phase_full_bridge_inverter` 的六个核心 Python 文件。
2. 迁移 CCM/TCM 输入字段、默认值、参数校验和 operating-point 表单。
3. 保留 unipolar-SPWM、DC-link twice-line ripple、output-inductor 和 TCM first-pass 语义。
4. 接入单相全桥的 switch stress、segmented loss 和 capacitor/magnetic adapter。
5. 迁移单相全桥表单的 `Run Design` 和 `Generate Waveforms` 控件。
6. 运行默认输入、非法输入、CCM、TCM、负载变化、PF 变化和 operating refresh 测试。
7. 确认 waveform view 显示 gate、switch-node、inductor current、capacitor current 和 output voltage。

验收门：单相全桥可以完成 `Run Design -> Generate Waveforms`，且目标输出与源基线在约定
容差内一致；selected switch 在 refresh 后保持不变。

本步提交/推送：

- commit message：`feat: migrate single-phase full-bridge inverter`；
- commit 内容：单相全桥 topology、form、直接依赖和专项测试；
- focused validation：单相全桥 schema/synthesis/waveform/stress/refresh/form/view 测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：单相全桥最小闭环及约定 parity 测试通过，commit 和 push 均成功。

### 第 5 步：迁移并验收三相两电平 VSI

安排：

1. 迁移 `three_phase_two_level_voltage_source_inverter` 的六个核心 Python 文件。
2. 保留 line-line RMS、phase RMS、phase peak、SPWM modulation 和六开关 bridge 语义。
3. 迁移三相电压、电流、PWM bus current 和 DC-link capacitor current 元数据。
4. 迁移六开关 stress、SxP DC-link capacitor selector 和 per-phase inductor adapter。
5. 迁移三相表单及其 PF、load ratio operating-point 输入。
6. 运行三相波形 metadata、PF 相位参考、load/PF refresh、device、capacitor 和 magnetic 测试。
7. 确认 waveform view 使用三相专用 renderer，不误用 DC-DC 标签。

验收门：三相两电平可以执行设计和波形生成；三相 phase waveform、switch stress、DC-link
和 per-phase magnetic 数据完整，且源/目标结构化字段一致。

本步提交/推送：

- commit message：`feat: migrate three-phase two-level vsi`；
- commit 内容：三相两电平 topology、form、三相波形/stress 依赖和专项测试；
- focused validation：三相 metadata、PF/load refresh、device、capacitor、magnetic 和 GUI 测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：三相两电平最小闭环及约定 parity 测试通过，commit 和 push 均成功。

### 第 6 步：迁移并验收三相三电平 NPC

安排：

1. 迁移 `three_phase_three_level_npc_inverter` 的六个核心 Python 文件。
2. 保留 PD level-shifted SPWM、三电平输出、split DC-link upper/lower bank 语义。
3. 迁移 NPC outer/inner switch 和 clamp-diode stress 角色映射。
4. 迁移 split capacitor selector、3x per-phase inductor adapter 和相关 loss/thermal 路径。
5. 迁移 NPC 表单、波形专用 renderer、summary 和 stress view 分支。
6. 运行 NPC 默认输入、PF/load refresh、switch/clamp roles、split capacitor 和 per-phase magnetic 测试。
7. 确认中点平衡、dead-time、parasitic transient 等未实现能力仍以 first-pass 限制显示。

验收门：NPC 可以执行设计和波形生成；四开关/二极管角色、split DC-link、三相波形和限制说明
均可在目标 GUI/report 中读回。

本步提交/推送：

- commit message：`feat: migrate three-phase three-level npc`；
- commit 内容：NPC topology、form、角色映射、split-link 依赖和专项测试；
- focused validation：NPC schema/synthesis/waveform/stress/refresh/capacitor/magnetic/view 测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：NPC 最小闭环、角色映射和限制说明通过，commit 和 push 均成功。

### 第 7 步：合并 DC-AC operating-point refresh 链路

安排：

1. 合并 `main_window.py` 的回调，使点击 waveform 前检查当前表单输入并保持当前 topology。
2. 合并 `run_design_controller.py` 的 design report 创建和 active plugin 保存逻辑。
3. 合并 `waveform_controller.py` 的 operating-point refresh 和 runtime override 处理。
4. 合并 `run_operating_point_refresh.py` 的 waveform、stress、topology evaluation 更新顺序。
5. 确认 DC-AC refresh 不会错误清空已选器件、磁性设计或电容结果。
6. 确认表单输入改变时会重新设计，只有 load/PF 等 operating-point 输入变化时执行 refresh。
7. 对三个拓扑分别验证：未 Run Design、设计后生成、重复生成、切换拓扑、非法输入和异常提示。

目标调用链必须保持：

```text
form callback
  -> main window
  -> design controller / waveform controller
  -> registry plugin
  -> run_operating_point_refresh
  -> waveform + stress + evaluator
  -> DesignReport
  -> Workspace.render_report
  -> WaveformView
```

验收门：三个 DC-AC 的 `Generate Waveforms` 按钮都能真正触发 backend，并能切换到 waveform tab；
异常通过 GUI 提示，不出现静默无响应。

本步提交/推送：

- commit message：`feat: connect dc-ac waveform refresh and result views`；
- commit 内容：main window、controllers、workspace、operating refresh 和结果页面合并；
- focused validation：三个拓扑的 GUI callback、design-before-waveform、重复生成、切换拓扑和异常提示测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：三个按钮均能进入 backend 和 waveform tab，commit 和 push 均成功。

### 第 8 步：合并下游工程能力

安排：

1. 合并 DC-AC 使用的 semiconductor role classification、device selection 和 operating refresh。
2. 合并 DC-link capacitor bank selector 和三相 NPC split-bank selector。
3. 合并单相/三相输出电感 magnetic adapter 和 per-phase hardware overview。
4. 合并 inverter segmented loss、efficiency sweep、thermal 和 geometry 结果路径。
5. 合并 Summary、Devices、Capacitors、Magnetics、Loss、Efficiency 和 Hardware Overview 页面。
6. 对每个拓扑确认未执行的下游阶段显示 `pending` 或 first-pass 说明，而非虚构数值。
7. 验证 operating refresh 复用已选硬件，不重新选择与工作点无关的器件。

验收门：三种拓扑在源工程已支持的 downstream 页面中显示正确结果、单位、硬件数量、警告和限制。

本步提交/推送：

- commit message：`feat: integrate dc-ac downstream engineering stages`；
- commit 内容：器件、电容、磁性、损耗、热、效率、geometry 和对应 result-view 分支；
- focused validation：三种拓扑 downstream pipeline、selected hardware reuse、loss/efficiency/view 测试；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：源工程已支持的 downstream 能力在目标中可读回，commit 和 push 均成功。

### 第 9 步：移植 DC-AC 专项测试和新增目标测试

安排：

1. 迁移三种 DC-AC topology tests 的确定性 backend 部分。
2. 迁移 DC-AC GUI form、registry、workspace、waveform view 集成测试。
3. 新增目标工程专项测试，验证当前目录启动后的 registry 不再返回空 DC-AC 列表。
4. 新增三种拓扑的最小 GUI/controller 端到端测试。
5. 新增 prohibited import 检查，确保 DC-AC runtime 不依赖 agentic/AI 模块。
6. 对每个拓扑固定至少一个 source/target 结构化输出 fixture。

验收门：专项测试能够覆盖 registry、form、schema、synthesis、waveform、stress、refresh、
result view 和下游直接依赖，不依赖人工点击才能证明核心链路。

本步提交/推送：

- commit message：`test: add dc-ac target integration coverage`；
- commit 内容：迁移的确定性测试、目标工程专项测试、source/target fixture 和禁止依赖检查；
- focused validation：DC-AC 三拓扑专项测试、GUI integration、prohibited import 和 fixture comparison；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：目标测试覆盖闭环且无未解释失败，commit 和 push 均成功。

### 第 10 步：打包、启动和 GUI 视觉检查

安排：

1. 在目标工程 clean environment 执行 editable install。
2. 验证 `python -m pe_claw_gui` 和目标 `run_pe_claw_gui.bat` 的 import 路径来自目标工程。
3. 验证拓扑 PNG、器件数据、电容数据和磁性数据从 package resources 读取。
4. 启动 GUI，依次打开三个 DC-AC topology form。
5. 对每个拓扑执行默认 `Run Design` 和 `Generate Waveforms`。
6. 检查 waveform tab、图例、单位、轴标签、文本换行和窗口布局。
7. 检查重复运行、切换拓扑、返回 category、重新进入 topology 后无旧 report 泄漏。

验收门：启动程序使用目标工程代码；三个 DC-AC 拓扑可完成 GUI 最小闭环；资源和布局无阻塞问题。

本步提交/推送：

- commit message：`test: verify dc-ac packaged gui runtime`；
- commit 内容：必要的打包适配、启动检查、资源检查和 GUI smoke evidence；
- focused validation：clean environment install、`python -m pe_claw_gui`、bat 启动路径、三拓扑 GUI smoke；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：目标 package/import 路径和 GUI 最小闭环确认，commit 和 push 均成功。

### 第 11 步：回归、证据和交付审查

安排：

1. 运行 DC-AC 专项测试。
2. 运行 operating refresh、GUI integration、device/capacitor/magnetic/loss/efficiency 相关回归。
3. 运行完整目标 pytest suite。
4. 对失败、error、skip、warning 分别分类，不把环境失败伪装成通过。
5. 生成 DC-AC acceptance matrix、source/target comparison 和 changed-file inventory。
6. 检查 `git diff --check`、绝对路径、缓存、生成文件和 agentic 依赖。
7. 更新目标工程 `ChangeLog.md` 和适用的 categorized report ledger。
8. 将本计划中的步骤状态、commit、测试命令和证据路径补全。

验收门：三种拓扑均通过专项验收；完整回归无未解释失败；目标工程可以独立运行，不引用源工程路径。

本步提交/推送：

- commit message：`docs: finalize dc-ac migration evidence and acceptance`；
- commit 内容：acceptance matrix、source/target comparison、ChangeLog/ledger、最终验证记录和本计划更新；
- focused validation：DC-AC 专项回归、相关回归、完整 pytest、路径/依赖扫描、`git diff --check`；
- push：`origin/codex/sync-gui-backend-from-2`；
- 完成条件：所有失败均有解释，证据完整，commit 和 push 均成功；之后才可请求用户验收。

## 7. 文件迁移矩阵初稿

| 文件/目录 | 处理方式 | 说明 |
| --- | --- | --- |
| `topologies/dc_ac/` | `add_or_replace` | 迁移三种拓扑及公共包入口 |
| `topologies/base/registry.py` | `merge` | 增加三个 DC-AC definitions，保留目标已有 topology |
| `topologies/base/*.py` | `merge_or_replace` | 以实际契约 diff 决定，保留兼容字段 |
| `models/waveform.py` | `merge_or_replace` | 必须支持三相、NPC、gate 和 metadata 字段 |
| `models/operating_point.py` | `merge_or_replace` | 必须支持 PF、Vout 和 switching frequency 字段 |
| `models/design_report.py` | `merge_or_replace` | 保证 report stage handoff 一致 |
| `pipeline/run_operating_point_refresh.py` | `merge_or_replace` | DC-AC refresh 统一入口 |
| `pipeline/run_full_pipeline.py` | `merge_or_replace` | 接通 DC-AC design pipeline |
| `pipeline/run_device_pipeline.py` | `merge_or_replace` | inverter switch roles 和 segmented loss |
| `pipeline/run_capacitor_pipeline.py` | `merge_or_replace` | DC-link 和 split-link bank |
| `pipeline/run_magnetic_pipeline.py` | `merge_or_replace` | output inductor/per-phase adapter |
| `app/category_views/dc_ac_page.py` | `replace` | 占位页替换为真实 topology list |
| 三个 DC-AC form | `add_or_replace` | 输入和 operating-point 控件 |
| `app/controllers/*.py` | `merge` | 保留 controller 边界 |
| `app/result_views/*.py` | `merge` | 增加 DC-AC renderer 和摘要分支 |
| `app/assets/topologies/dc_ac/*.png` | `add` | 使用 package resources |
| `engines/devices/inverter_segmented_loss.py` | `add_or_merge` | 仅迁移 DC-AC 直接依赖 |
| DC-AC 直接使用的 library data | `add` | 记录来源、数量和 checksum |
| `tests/test_dc_ac_*.py` | `add_or_adapt` | 迁移确定性测试并补目标集成测试 |
| `agentic/`, `agents/`, `skills/` | `exclude` | 本专项明确排除 |
| `outputs/`, `__pycache__/`, `.pytest_cache/` | `exclude_generated` | 不进入 Git 迁移 |

## 8. 三种拓扑验收矩阵

| 拓扑 | Registry | Form | Schema | Synthesis | Waveform | Stress | Refresh | GUI view | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `single_phase_full_bridge_inverter` | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed |
| `three_phase_two_level_voltage_source_inverter` | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed |
| `three_phase_three_level_npc_inverter` | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed | Passed |

每一列必须填入测试命令、结果和证据路径。`Status` 只有在本行所有必要列通过后才能标记
为 `passed`。源工程本身存在的 first-pass 限制应记录为 `accepted limitation`，不应被视为
迁移失败，也不能被隐藏。

第 11 步逐项命令、结果和证据路径记录在
`migration/evidence/20260827/step11_dc_ac/dc_ac_acceptance_matrix.csv`；源/目标
45 个确定性字段对照为 0 difference，详见同目录
`source_target_comparison.csv`。三种拓扑保留源工程声明的 first-pass preview/model
边界，属于已接受能力边界，不影响迁移一致性结论。

## 9. 验证命令安排

以下命令在目标工程执行，具体测试文件以实际迁移矩阵为准：

```powershell
cd C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')

python -m py_compile <migrated_files>
python -m compileall -q src/pe_claw_gui
python -c "from pe_claw_gui.topologies.base import build_default_registry; print([(d.topology_id, d.implemented) for d in build_default_registry().list_topologies('dc_ac')])"
python -m pytest -q tests/test_dc_ac_single_phase_full_bridge_inverter.py
python -m pytest -q tests/test_dc_ac_three_phase_two_level_inverter.py
python -m pytest -q tests/test_dc_ac_three_phase_three_level_npc_inverter.py
python -m pytest -q tests/test_dc_ac_placeholder_topologies.py
python -m pytest -q tests/test_ac_dc_gui_integration.py
python -m pytest -q tests/test_operating_refresh_semiconductor_roles_complete.py
python -m pytest -q --basetemp .pytest-tmp-full
git diff --check
```

第 11 步实际执行命令：

```powershell
$dcAc = Get-ChildItem tests -File -Filter 'test_dc_ac_*.py'
python -m pytest -q -ra --junitxml=.pytest-step11-focused.xml `
  --basetemp .pytest-tmp-step11 $dcAc `
  tests/test_phase7_dc_ac_migration.py `
  tests/test_phase9_dc_ac_topologies.py `
  tests/test_phase9_operating_point_migration.py `
  tests/test_phase10_gui_integration.py `
  tests/test_phase11_ai_isolation.py `
  tests/test_device_selector_rejects_overstress.py `
  tests/test_device_selector_single_candidate.py `
  tests/test_capacitor_registry.py tests/test_capacitor_selection.py `
  tests/test_magnetic_library_schema.py tests/test_magnetic_loss_contract.py `
  tests/test_magnetic_static_registry.py tests/test_core_loss_kernel.py `
  tests/test_core_loss_router.py `
  tests/test_default_packaged_normalized_magnetic_backend.py
python -m pytest -q --basetemp .pytest-tmp-full -rA
python -B scripts/build_dc_ac_step11_evidence.py
python -B -m compileall -q src tests scripts/build_dc_ac_step11_evidence.py
git diff --check
```

实际结果为 focused `183 passed, 1 skipped`，完整 suite `323 passed, 1 skipped`；
`failure=0`、`error=0`、`warning=0`。唯一 skip 是可选 legacy external
OpenMagnetics debug/reference 数据库不可用，目标工程默认 packaged normalized production
路径已通过。

最小功能验收必须得到：

```text
dc_ac registry count = 3
single-phase waveform = available
three-phase two-level waveform = available
three-phase NPC waveform = available
```

## 10. 提交、推送和阶段管理

每一步必须单独提交并立即推送。下面的 commit message 是每一步的最低要求，
不允许将多个步骤压缩成一个 commit：

```text
chore: record dc-ac migration baseline
docs: add dc-ac migration dependency matrix
refactor: merge shared dc-ac runtime contracts
feat: register dc-ac topology family
feat: migrate single-phase full-bridge inverter
feat: migrate three-phase two-level vsi
feat: migrate three-phase three-level npc
feat: connect dc-ac waveform refresh and result views
feat: integrate dc-ac downstream engineering stages
test: add dc-ac target integration coverage
test: verify dc-ac packaged gui runtime
docs: finalize dc-ac migration evidence and acceptance
```

第 0 步至第 11 步每一步完成后必须依次执行：

1. 检查 `git diff` 和 `git status`；
2. 排除缓存、`outputs/` 和无关文件；
3. 运行该步骤的 focused tests；
4. 更新 `ChangeLog.md` 和适用 ledger；
5. 执行 `git diff --check`；
6. 创建独立 commit；
7. 创建本步骤唯一独立 commit，并记录 commit hash。
8. 将该 commit push 到 `origin/codex/sync-gui-backend-from-2`。
9. 检查远端 push 成功，并记录 push 时间、远端分支和 commit hash。
10. 只有在 commit 和 push 成功后才把计划步骤标为 `completed`。
11. 只有当前步骤标记为 `completed` 后，才允许开始下一步骤。

本计划执行期间不得 push、merge、tag 或直接修改目标 `master`；每一步的 push
必须进入指定迁移分支。最终 merge、tag、发布或向 `master` 推送仍需用户明确批准。

## 11. 风险和控制措施

| 风险 | 控制措施 |
| --- | --- |
| 只复制 topology 目录导致公共模型缺失 | 先完成 import/dependency matrix，再按闭包迁移 |
| 同名公共文件契约不兼容 | 做语义 diff，模型和调用方一起修改并测试 |
| 启动时 import 到错误工程 | 检查 `pe_claw_gui.__file__`、`PYTHONPATH` 和 bat 工作目录 |
| package-data 缺失 | 安装后验证 PNG、器件、电容和磁性资源读取 |
| DC-AC refresh 误清空硬件选择 | 增加 selected hardware checksum 和 refresh 测试 |
| NPC 角色映射被简化 | 对 outer/inner switch 和 clamp diode 做结构化 role 断言 |
| first-pass 能力被宣传为完整仿真 | 保留源工程 notes、warnings 和 limitation 字段 |
| 迁移带入 agentic 依赖 | 运行 prohibited import 搜索和无 agentic clean import 测试 |
| 用户现有 outputs 被清理 | 只读识别，不执行广泛删除，不覆盖未跟踪文件 |
| 大迁移难以回滚 | 周备份、专用分支、分阶段 commit 和 exit gate |

## 12. 回滚策略

1. 保留目标工程原始 `master` 和迁移前 commit 不变。
2. 任何阶段失败时，回到该阶段前最后一个通过的迁移 commit；不使用 destructive reset。
3. 保留失败测试和证据，不能通过删测试或隐藏拓扑来回滚问题。
4. 迁移期间保留周备份，直到用户验收完成。
5. 如发现源工程在迁移期间发生变化，冻结当前源 commit，重新评估差异后再继续。
6. 如发现目标已有用户文件影响迁移，暂停并请求用户决定，不覆盖这些文件。

## 13. 最终完成条件

- [x] 计划已获用户批准，备份和基线完成。
- [x] import、文件、静态数据和测试依赖矩阵无未决项。
- [x] 三个 DC-AC 拓扑已注册并可加载 plugin/form。
- [x] 三个拓扑都能完成 `Run Design -> Generate Waveforms`。
- [x] Waveform view 能显示各拓扑专用波形和正确单位。
- [x] operating-point refresh、PF/load 变化和重复运行行为正确。
- [x] 器件、DC-link capacitor、output magnetic、loss、thermal、efficiency 和 geometry
  的源工程支持能力已迁移或明确记录为 limitation。
- [x] 目标工程 runtime 不依赖源工程绝对路径；测试/冻结证据仅保留来源 provenance。
- [x] 目标工程不依赖 AI/agentic/skills 代码。
- [x] DC-AC 专项测试和相关回归通过。
- [x] 完整目标 pytest suite 已运行，所有 failure/error/skip/warning 均已分类。
- [x] `ChangeLog.md`、适用 evidence ledger、迁移 evidence 和本计划状态已更新。
- [ ] 用户审查通过后，才执行 merge/tag/向 `master` push。
- [ ] 第 0 步至第 11 步均已各自完成独立 commit 和 push；第 11 步等待本次主体 push 回执。
- [ ] 每一步的远端 commit hash、push 结果、验证命令和证据路径均已记录；第 11 步等待回执。
- [x] 不存在跨步骤合并提交、补推或未记录的远端提交。

## 14. 计划执行记录

| 日期 | 步骤 | 状态 | 说明 | Commit | 验证 |
| --- | --- | --- | --- | --- | --- |
| 2026-08-27 | 计划建立 | completed | 已完成源/目标工程结构检查和 DC-AC 范围定义；尚未修改 runtime 代码 | - | 只读检查通过 |
| 2026-08-27 | 第 0 步 | Completed | 已完成备份、仓库基线、focused validation、独立 commit 和 push | `faf5e3f06f2874a25d106a68144c5cc78eeb6032` | `migration/phase0/dc_ac_step0_baseline.md`; registry 3; 12 focused tests passed; remote verified |
| 2026-08-27 | 第 1 步 | Completed | 已完成文件/import/资源/测试/排除扫描、独立 commit 和 push | `f9c85d58c38d86b4d4d3bc410879ce7333ddf097` | `migration/phase1/dc_ac_dependency_matrix.csv`; 58 rows; 0 review_required; remote verified |
| 2026-08-27 | 第 2 步 | Completed | 已补齐 DC-AC 公共 topology capability 导出和共享契约测试，并完成独立 commit + push | `01a2d1fa76a36d448ccf7826b61d30dd58e41612` | `tests/test_dc_ac_shared_contracts.py`; 33 focused tests passed; DC-AC regression 7 passed; remote verified |
| 2026-08-27 | 第 3 步 | Completed | 已完成 registry/category/resource 合并、独立 commit 和 push | `00b408aad6afac72f12d95c8a4ca43f9c1e1b33c` | `tests/test_dc_ac_registry_category.py`; 33 focused tests passed; source-path scan passed; remote verified |
| 2026-08-27 | 第 4 步 | Completed | 已确认单相全桥核心 runtime/form 与源工程一致，补齐专项契约测试并完成独立 commit + push | `3fe828f5cdbd64dfbacf0bd0ecca6f0b0690ee16` | `tests/test_dc_ac_single_phase_full_bridge_contract.py`; 17 passed; compileall passed; diff check passed; remote verified |
| 2026-08-27 | 第 5 步 | Completed | 已确认三相两电平核心 runtime/form 与源工程一致，补齐专项契约测试并完成独立 commit + push | `209807872d3095cc464b45c194c01933b3704837` | `tests/test_dc_ac_three_phase_two_level_contract.py`; 16 passed; compileall passed; diff check passed; remote verified |
| 2026-08-27 | 第 6 步 | Completed | 已确认三相三电平 NPC 核心 runtime/form 与源工程一致，补齐专项契约测试并完成独立 commit + push | `2ebc79fc08e8df0d1bb81dc726d1eb3f710a5b98` | `tests/test_dc_ac_three_phase_three_level_npc_contract.py`; 16 passed; compileall passed; diff check passed; remote verified |
| 2026-08-27 | 第 7 步 | Completed | 已完成 operating-point refresh、DC-AC 专用 waveform/summary/stress 路由、专项测试、独立主体提交和 push | `342ebf8f973089b94e14e957d56fd29b54646701` | `5 + 37 + 7` tests passed; compileall/diff check passed; remote verified; receipt follows |
| 2026-08-27 | 第 8 步 | Completed | 已完成 DC-AC downstream 工程阶段与结果页面合并；补齐效率管线 AC-DC 兼容引用和桥式整流拓扑集合；主体 commit + push 已完成，回执随后提交 | `57e080b` | DC-AC focused `51 passed`; 三拓扑 downstream smoke 均通过（各 2 load points + 20 PF points）；compileall/diff check 通过；full pytest `305 passed, 1 skipped, 3 errors`，3 errors 均为 pytest tmp_path 对系统临时目录 WinError 5 权限环境问题；无源工程绝对路径/agentic 命中；remote verified |
| 2026-08-27 | 第 9 步 | Completed | 已新增目标工程 DC-AC 集成覆盖、三拓扑结构化 fixture、controller 闭环、结果摘要和禁止依赖测试；独立 commit + push 已完成，回执随后提交 | `7357c99` | `tests/test_dc_ac_target_integration.py`；`migration/evidence/20260827/step9_dc_ac/dc_ac_target_fixtures.json`；与既有 DC-AC/GUI/isolation 测试合计 `64 passed`；compileall/diff check 通过；source/target 默认 fixture 对照通过；remote verified |
| 2026-08-27 | 第 10 步 | Completed | 已完成 editable install、目标包路径与资源检查、bat startup check、三种 DC-AC 默认设计/波形 GUI smoke；并修复 BaseTopologyForm 缺失的 numeric parsing helpers；主体 commit + push 已完成，回执随后提交 | `91be103` | `tests/test_dc_ac_packaged_gui_runtime.py`; `migration/evidence/20260827/step10_dc_ac/packaged_gui_runtime_validation.json`; `26 passed`; editable install passed; 19 topologies/3 DC-AC/3 PNG resources verified; bat startup check passed; compileall/diff check passed; remote verified |
| 2026-08-27 | 第 11 步 | In Progress | 已完成 DC-AC 专项、下游相关回归、完整 pytest、源/目标对照、路径/依赖扫描及交付证据；等待主体 commit/push 后补远端回执 | pending | `migration/evidence/20260827/step11_dc_ac/`; focused `183 passed, 1 skipped`; full `323 passed, 1 skipped`; 0 failures/errors/warnings; 45 source/target fields, 0 differences; runtime path/agentic scan 0 hits |

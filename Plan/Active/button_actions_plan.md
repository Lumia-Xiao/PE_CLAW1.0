# PE-Claw Web 后续按钮接入计划

- **状态**：Ready
- **基线分支**：`codex/react-buck-workspace`
- **目标**：将桌面版的后续分析操作逐一接入网页版，并保持设计点硬件选择、运行点刷新和固定硬件效率扫描的语义不变。

## 1. 当前按钮基线

桌面版 Buck 表单包含：

1. `Run Design`：拓扑综合、半导体选择及基础报告。
2. `Run Capacitor`：设计点电容选择和电容几何/纹波结果。
3. `Run Magnetics`：设计点磁性器件选择、Pareto 候选和磁性报告。
4. `Generate Waveforms`：使用已选硬件，刷新指定 Vin/load ratio 的运行点波形和损耗。
5. `Run Efficiency Sweep`：使用已选硬件，在 0.1–1.0 p.u. 负载范围扫描效率。

网页版当前只有 `Run Design` 可执行，其余页面标签用于显示状态，不能伪造完成结果。

## 2. 统一任务模型

### 2.1 任务请求

新增统一的 `DesignActionRequest`：

- `job_id`：依赖的基础设计任务；
- `schema_version`：固定为 `1.0`；
- `action`：`capacitor`、`magnetics`、`waveforms`、`efficiency_sweep`；基础设计沿用现有 `DesignJobCreate` 接口，不属于后续 action；
- `operating_point`：波形操作需要 `vin_v` 和 `load_ratio`；
- `options`：目前仅磁性动作可传 `llc_search_mode: fast | full`（对应 LLC adapter；Buck 不适用时由未来 API 明确拒绝）；其他动作只能传空对象。未实现的 debug 参数不开放；禁止任意路径、模块名和 Python 表达式。
- `vin_v` 必须为有限正数，`load_ratio` 必须为有限非负数；运行点对象仅对 waveforms 开放。具体拓扑工作范围由 API/adapter 再校验。
- 未知字段拒绝；`job_id` 限制为 1–64 位字母、数字、下划线或连字符。

### 2.2 任务关系和状态

- 一个基础 `design` 成功后，才允许后续 action；
- 后续 action 读取同一任务的结构化结果和选定硬件；
- 每个 action 有独立 `action_id`、状态、阶段进度、错误和 artifact manifest；
- 同一个 `job_id + action + 参数` 的重复提交应幂等，避免重复运行；
- 基础设计失败、过期或缺少选定硬件时，后续 action 返回明确的 `409/422`，不启动 Worker。

E0 固定依赖声明：四个动作都依赖成功的基础 `design`；不强制串行执行 capacitor → magnetics → waveforms。选定硬件是否足够由 adapter 按拓扑检查，该声明本身不会查询数据库或替代运行时校验。

状态转换约定：

| 当前状态 | 允许的下一状态 |
| --- | --- |
| queued | running、failed（发布队列失败）、cancelled、expired |
| running | succeeded、failed、cancelled |
| succeeded / failed / cancelled | expired |
| expired | 无 |

同一 action 不从终态回到 queued。重试/重新运行创建新的 `action_id`，保留原失败记录；普通重复提交复用现有动作，未来显式重试请求使用新的幂等键。Celery 重复投递须由数据库原子状态检查忽略，不能再次执行成功动作。运行中不能直接清理为 expired，须先结束或确认失败后清理。这里仅定义契约，执行、取消、幂等和清理能力在后续阶段实现。

响应统一采用 `DesignActionResponse`：包含 action/job ID、动作、状态、0–100 进度、阶段、时间戳、结构化 `DesignError`（code/message/correlation_id）及结果/artifact URL。

## 3. 后端 API 设计

新增版本化接口：

```text
POST /api/v1/design-jobs/{job_id}/actions/capacitor
POST /api/v1/design-jobs/{job_id}/actions/magnetics
POST /api/v1/design-jobs/{job_id}/actions/waveforms
POST /api/v1/design-jobs/{job_id}/actions/efficiency-sweep
GET  /api/v1/design-jobs/{job_id}/actions
GET  /api/v1/design-jobs/{job_id}/actions/{action_id}
GET  /api/v1/design-jobs/{job_id}/actions/{action_id}/result
GET  /api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts
GET  /api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts/{artifact_id}
```

`waveforms` 请求示例：

```json
{"schema_version": "1.0", "job_id": "job-1", "action": "waveforms", "operating_point": {"vin_v": 48, "load_ratio": 0.75}, "options": {}}
```

API 层负责校验依赖、操作点范围、任务归属和幂等键；Pipeline adapter 负责将已保存结果恢复为内部 `DesignReport`/context。

以上统一 envelope 用作后续 POST 请求体，路径中的 job_id/action 必须与请求体一致，否则拒绝；GET 返回统一响应模型。接口尚未在 E0 注册。

E1 前置工作：现有报告 JSON 是展示投影，不能默认可恢复完整 `DesignReport`。须设计带版本的可恢复快照，保存后续动作实际需要的类型和已选硬件，并以 fixture 验证恢复后硬件身份/参数一致；禁止通过重新选型冒充恢复。

## 4. Pipeline adapter 实现顺序

### B1：Run Capacitor

- 复用 `run_capacitor_pipeline` 和现有电容几何/纹波报告；
- 阶段：`validate → capacitor → geometry → report → finalize`；
- 结果合并回任务快照，保留基础设计结果；
- 输出电容候选、推荐 bank、纹波、几何和 CSV/JSON artifact；
- 测试没有基础设计或重复提交时的拒绝行为。

### B2：Run Magnetics

- 复用 `run_magnetic_pipeline` 和现有磁性 backend 配置；
- 阶段：`validate → magnetic_search → ranking → geometry → report → finalize`；
- 保持设计点选择策略、候选压缩和 provenance；
- 输出推荐磁芯/绕组、Pareto 候选、损耗、几何和 JSON/CSV artifact；
- 明确磁性 backend 不可用、无候选和超时错误。

### B3：Generate Waveforms

- 复用 `run_operating_point_refresh`，禁止重新选择器件、电容和磁性硬件；
- 阶段：`validate → operating_point → waveform → loss_refresh → report → finalize`；
- 校验 `vin_v > 0`、`load_ratio >= 0`；
- 结果只更新运行点、波形、应力和损耗，不覆盖设计点硬件；
- 输出 waveform JSON、PNG/SVG（如后端已有渲染器）和运行点报告。

### B4：Run Efficiency Sweep

- 复用 `run_efficiency_sweep_pipeline`；
- 阶段：`validate → fixed_hardware → sweep → summarize → report → finalize`；
- 固定已选半导体、电容和磁性器件；禁止在每个负载点重新选型；
- 输出 0.1–1.0 p.u. 点、峰值/满载/轻载效率、损耗分解和曲线 artifact；
- 缺少硬件时按现有 Pipeline 语义返回 warning 或 blocked 状态。

## 5. Worker 和持久化

- 将 Celery task 泛化为 `run_action_task(action_id)`，或为四个 action 建立薄 task 包装器；
- 使用 action 表记录 `action_id`、输入、状态、进度、依赖 job、结果和 artifact；
- 每个 action 使用独立输出目录：`outputs/web_jobs/{job_id}/actions/{action_id}/`；
- action 失败不得覆盖基础设计结果；
- 保留 action 输入快照、Pipeline 版本、schema 版本和输出 checksum；
- 为 action 增加 Alembic migration 和过期清理策略。

## 6. 前端按钮和页面

### 6.1 操作区

在 Buck 工作区左侧新增操作卡片：

- `Run Capacitor`；
- `Run Magnetics`；
- `Generate Waveforms`，附 Vin 和 Load ratio 输入；
- `Run Efficiency Sweep`。

按钮状态由依赖和任务状态决定：

- 未完成基础设计：禁用并说明“请先运行设计”；
- action 运行中：禁用相同 action，显示进度；
- action 失败：显示“重试”；
- action 成功：显示“重新运行”并允许查看结果；
- 其他 action 仍可在依赖满足时运行。

### 6.2 结果页

- 每个 tab 从 action 结果读取，不以旧结果填充新 action；
- action 运行中显示阶段进度和任务编号；
- action 失败显示错误码、用户消息和重试按钮；
- 波形页根据实际采样数据绘图；没有采样数据时显示明确空状态；
- Efficiency tab 使用后端扫描点绘图，并显示固定硬件说明；
- Files tab 合并基础设计和 action artifact，显示类型、大小、校验和、下载链接。

## 7. 测试矩阵

### 后端

- schema：四种 action 请求、范围和未知字段；
- dependency：无基础设计、基础设计失败、缺少硬件、过期任务；
- state machine：queued/running/succeeded/failed/cancelled/expired；
- idempotency：相同输入不重复创建；不同 operating point 生成独立 action；
- pipeline parity：每个 action 与 GUI/现有 Pipeline fixture 关键字段一致；
- artifact isolation：action 之间、用户任务之间不可互读；
- failure safety：action 失败不破坏基础设计结果。

### 前端

- 四个按钮依赖禁用/启用；
- 进度轮询和刷新恢复；
- 失败、重试、队列不可用；
- 波形输入校验；
- Efficiency 曲线只使用真实扫描点；
- action 文件下载和移动端布局。

### 真实联调

- Docker Compose 的 PostgreSQL、Redis、API、Worker、Nginx 全链路；
- Buck：design → capacitor → magnetics → waveforms → efficiency sweep；
- Worker 重启恢复、Redis 重启、数据库重连和 artifact 清理；
- 测试完成后更新 `ChangeLog.md` 和迁移证据。

## 8. 交付里程碑

- **E0**：冻结 action schema、依赖关系和状态机。
- **E1**：`Run Capacitor` API/Worker/页面/测试。
- **E2**：`Run Magnetics` API/Worker/页面/测试。
- **E3**：`Generate Waveforms` API/Worker/操作点表单/绘图/测试。
- **E4**：`Run Efficiency Sweep` API/Worker/曲线/测试。
- **E5**：统一 action artifact、历史任务和完整 Docker 联调。
- **E6**：扩展到其他拓扑；每个拓扑必须提供 capability、schema、adapter、按钮和 parity fixture。

## 9. 实施原则

- 先完成后端 action 和真实 Pipeline 调用，再显示可点击按钮；
- 不在浏览器复制工程公式或器件筛选；
- 不把基础设计结果和运行点结果混为一个快照；
- 不用 mock 成功状态冒充真实设计；测试可以 mock HTTP，但必须另有 Pipeline fixture parity；
- 每个里程碑单独测试、更新 ChangeLog、检查 `git diff --check` 并提交到 feature branch。

## 10. 本地实施记录

### 2026-09-15：E0 契约实现

- 新增 `src/pe_claw_web/schemas/actions.py` 并导出请求、响应、动作枚举、依赖/阶段声明和状态转换校验器。
- 新增契约测试覆盖四类请求/响应 JSON 往返、未知字段、非法参数、有限数值、结构化错误及全部 36 组状态转换。
- 验证命令：`python -m pytest -q tests/test_web_action_contracts.py tests/test_web_schemas.py`；结果见同次 ChangeLog。
- 范围：E0 为后续实现提供模型和规则；尚未接入 API/Worker/数据库/React 按钮。
- Git：本地实现与文档一起提交至 `codex/react-buck-workspace`；未推送，按仓库规则暂不将 E0 标记为已完成里程碑。下一步为 E1。

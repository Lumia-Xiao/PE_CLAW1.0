# PE-Claw 1.0 Web 化与异步设计服务实施计划

- **状态**：Draft
- **目标**：在保留现有确定性设计 Pipeline 的前提下，提供与 Tkinter GUI 功能和布局一致的 Web 界面。浏览器提交结构化设计请求，后端异步执行设计并返回可追溯的 JSON、图表和报告文件。
- **范围**：FastAPI API、Pydantic 契约、Redis/Celery 任务执行、结果文件服务、React 前端、认证授权、限额、Docker 部署。
- **不在首期范围**：重写拓扑公式、修改器件筛选策略、迁移 AI/Agent 逻辑、把核心计算移到浏览器端。

## 1. 现状基线与约束

1. 以 `src/pe_claw_gui` 为唯一后端计算来源，复用现有 registry、controllers、pipeline、models、reports 和 visualization。
2. Tkinter 仅作为现有行为和页面布局的参考，不向 Pipeline 引入 Web 或 GUI 依赖。
3. 保持设计点硬件选择与运行点刷新规则、字段名称、单位、状态语义、排序和报告 provenance 不变。
4. API 不直接暴露 Python 对象、任意模块路径、文件系统路径或内部异常堆栈。
5. 先实现单体部署和 Buck 端到端闭环，再扩展到全部拓扑和生产安全能力。

## 2. 目标架构

```text
React/Vue Web
    | HTTPS JSON + artifact download
FastAPI API
    | Pydantic request/response schemas
Job repository (SQLite/PostgreSQL)
    | enqueue
Redis broker/result metadata
    |
Celery worker(s)
    | adapter
Existing PE-Claw pipelines and reports
    |
Per-job artifact directory / object storage
```

首期建议 React + TypeScript、FastAPI、Pydantic v2、Celery、Redis、PostgreSQL（开发环境可 SQLite）、Docker Compose。API、Worker、Redis、数据库和前端均可独立扩展。

## 3. 阶段 A：契约和后端适配层

### A1. 盘点 Pipeline 输入输出

- 梳理 `run_full_pipeline`、`run_topology_pipeline`、器件、电容、磁性、损耗、热、波形、效率和报告入口。
- 为 Buck 建立一份固定 fixture，记录输入、关键输出、单位、状态、警告和生成文件。
- 明确可序列化边界：只允许 JSON 基础类型、枚举、数组、结构化报告和受控 artifact 引用。
- 验证设计点和 operating-point refresh 的调用顺序不能被 API 改变。

### A2. 定义 Pydantic 模型

建议新增 `src/pe_claw_web/`，避免污染 `pe_claw_gui.app`：

- `schemas/design.py`：`DesignJobCreate`、`DesignJobResponse`、`DesignJobStatus`、`DesignError`。
- `schemas/topology.py`：拓扑 ID、能力、字段定义和单位元数据。
- `schemas/result.py`：summary、stress、device、capacitor、magnetic、loss、thermal、waveform、efficiency、hardware overview。
- 所有数值字段定义范围、单位和空值语义；拒绝未知拓扑和未知字段。
- 版本化接口，例如 `/api/v1`，响应携带 `schema_version` 和后端版本。

### A3. 实现同步 FastAPI MVP

- 新增 `api/main.py`、`api/routes/design_jobs.py`、`api/routes/topologies.py`、`services/design_runner.py`。
- `POST /api/v1/design-jobs` 先同步调用 Buck adapter，返回结构化 JSON。
- `GET /api/v1/topologies` 返回注册表中的可用拓扑和表单字段元数据。
- `GET /api/v1/health` 检查 API、设计运行时和数据目录。
- 将内部异常转换为稳定的错误码、用户消息和 correlation ID；日志保留完整 traceback。
- 使用现有测试 fixture 对比 GUI 运行结果，确保 API 适配没有改变计算结果。

**阶段验收**：Buck 请求可通过 OpenAPI 文档提交；响应可被 Pydantic 重新验证；关键数值与现有 GUI fixture 一致；无绝对路径和内部 traceback 泄露。

## 4. 阶段 B：Redis/Celery 异步任务

### B1. 任务数据模型

- `design_jobs`：`id`、`user_id`、`topology`、`request_json`、`status`、`progress`、`stage`、`error_code`、`created_at`、`started_at`、`finished_at`、`result_ref`。
- 状态限定为 `queued`、`running`、`succeeded`、`failed`、`cancelled`、`expired`。
- 每个任务使用独立工作目录，禁止任务之间共享可变状态。

### B2. Celery Worker

- `workers/celery_app.py` 配置 Redis broker/backend。
- `workers/design_tasks.py` 只接收 job ID，从数据库读取请求，再调用 `design_runner`。
- 按阶段更新进度：validate、topology、devices、capacitor、magnetics、loss、thermal、report、finalize。
- 设置超时、重试次数、幂等键和任务取消策略；重试不得重复污染最终 artifact。
- worker 进程不接受用户提交的 Python 表达式、路径或命令。

### B3. API 状态接口

- `POST /api/v1/design-jobs` 创建任务并返回 `202 Accepted` 和 `job_id`。
- `GET /api/v1/design-jobs/{job_id}` 返回状态、阶段、进度、警告和错误信息。
- 首期使用轮询；后续可增加 SSE/WebSocket 推送。
- 设计结果只在任务成功后开放，失败任务返回可读错误和 correlation ID。

**阶段验收**：多个 Buck 任务可并行排队；刷新网页不会丢失任务；Worker 重启后状态可恢复；相同请求具备可重复结果；失败任务不会显示为成功。

## 5. 阶段 C：结果文件与报告

- 统一 artifact manifest：文件 ID、类型、MIME、大小、校验和、创建时间和过期时间。
- `GET /api/v1/design-jobs/{job_id}/result` 返回结构化结果。
- `GET /api/v1/design-jobs/{job_id}/artifacts` 列出报告、CSV、PNG、SVG、JSON、PDF。
- 下载接口按用户和 job 所有权鉴权，使用安全文件名和流式传输。
- 图表优先返回结构化数据，由前端渲染；必须保留下载 PNG/SVG/PDF 的能力。
- 结果目录与源代码、库文件、日志目录隔离；设置清理和保留策略。

**阶段验收**：summary、波形、效率曲线、器件表和报告在浏览器正确显示；下载文件可打开；任务之间不能访问彼此 artifact。

## 6. 阶段 D：React 前端复刻 Tkinter

### D1. 页面和状态

- Shell：左侧导航、分类页、拓扑选择页、工作区和结果页。
- 表单：从 `/topologies` 元数据生成字段、单位、范围、默认值和校验提示。
- 任务页：提交、排队、阶段进度、警告、失败重试和取消。
- 结果页：summary、stress、device、capacitor、magnetic、loss、thermal、waveform、efficiency、hardware overview。
- 全局状态只保存 request、job ID、结果引用和 UI 选项，不能保存后端内部对象。

### D2. 视觉一致性

- 先截取 Tkinter 页面尺寸、导航顺序、标签文本、按钮行为和结果分组，建立 UI parity checklist。
- 用 TypeScript 类型直接对应 Pydantic API schema。
- 使用 Plotly/ECharts 等前端图表库；结果数值和单位由 API 明确提供。
- 加入桌面宽度、窄屏和错误状态的可视化测试。

### D3. 前端验证

- API contract tests：请求/响应 schema、状态机、错误码。
- Playwright：Buck 表单提交、进度轮询、结果渲染、artifact 下载。
- 与 Tkinter golden fixture 做字段和关键数值比对。

**阶段验收**：用户无需运行 `.bat` 即可完成一次 Buck 设计；页面导航和核心操作与现有 GUI 一致；API 不可用时有清晰错误提示。

## 7. 阶段 E：扩展全部拓扑和功能

按风险和复用程度分批接入：

1. 现有完整 DC-DC 拓扑。
2. 电容、磁性、损耗、热和效率独立阶段。
3. DC-AC、AC-DC、AC-AC 页面及其能力声明。
4. 设计请求导入、报告导出和历史任务。
5. AI/Agent 功能另立接口和权限边界，不与确定性 API 混合发布。

每接入一个拓扑，必须更新 registry/能力元数据、schema、adapter、API contract、前端表单、结果视图和对应测试。

## 8. 阶段 F：认证、授权和任务限制

- 使用 OIDC/OAuth2 或成熟身份服务；API 只保存用户 ID 和权限，不保存明文密码。
- JWT/会话 token 放在安全 Cookie 或受控 Authorization header；启用 HTTPS、CORS 白名单和 CSRF 防护。
- 资源归属检查：用户只能读取自己的 job、result 和 artifact；管理员权限单独定义。
- 限制并发任务数、单任务运行时间、请求大小、文件大小、每日配额和历史保留时间。
- 对 job 创建、下载、失败、取消和管理员操作记录审计日志。
- 生产环境隐藏 Celery/Redis 管理端口，密钥使用环境变量或密钥管理服务。

**阶段验收**：未登录不能提交；用户 A 不能读取用户 B 的 job；超限请求被稳定拒绝；审计记录包含用户、任务、时间和结果。

## 9. 阶段 G：Docker 和部署

服务拆分：`frontend`、`api`、`worker`、`redis`、`db`、反向代理（Nginx/Caddy）。

- 编写开发用 `docker-compose.yml` 和生产用 compose/部署配置。
- API/Worker 使用相同版本的 PE-Claw 包和数据；固定 Python、依赖和库数据版本。
- 健康检查、结构化日志、优雅关闭、Worker 并发和资源上限必须可配置。
- 反向代理只公开 443；Redis、数据库和 Flower 仅内网访问。
- 使用独立 artifact volume 或对象存储；备份数据库和结果 manifest。
- 建立 CI：lint、类型检查、后端测试、前端测试、API contract、Docker build 和安全依赖扫描。

**阶段验收**：全新机器可按文档启动；API、Worker、Redis、数据库故障有可诊断日志；升级后旧 job 结果仍可读取。

## 10. 代码保护策略

- 生产浏览器只拿到前端 bundle；核心 Python、器件库、公式和 Pipeline 只部署在受控后端。
- API 响应只返回结果，不返回内部模块、源码、调试堆栈或完整原始库。
- 使用最小容器镜像、非 root 用户、私有镜像仓库和密钥管理。
- 若必须离线本地运行，应明确这是可逆向的软件交付；可使用 Nuitka/Cython、签名许可证和加密数据文件提高成本，但不能承诺绝对保密。

## 11. 测试和质量门槛

- 单元：Pydantic 校验、状态机、adapter、artifact manifest、权限函数。
- 集成：API + Redis + Worker + 数据库 + artifact 生命周期。
- 回归：Buck 全流程及所有已接入拓扑的关键 fixture。
- 前端：表单、轮询、失败/重试、图表、下载和权限状态。
- 安全：越权访问、路径穿越、超大请求、无效 token、CORS/CSRF、错误信息泄露。
- 性能：并发任务、队列延迟、Worker 内存、单任务超时和结果存储增长。
- 推荐命令：`python -m pytest -q --basetemp .pytest-tmp-full`，另行执行前端 lint/test 和 Docker compose smoke test。

## 12. 交付里程碑

- **M0**：契约和 Buck fixture 冻结。
- **M1**：同步 FastAPI Buck API 可用。
- **M2**：Redis/Celery 异步任务和状态查询可用。
- **M3**：结果、图表、报告和下载可用。
- **M4**：React Buck 页面完成 parity smoke test。
- **M5**：首批拓扑迁移完成。
- **M6**：认证、授权、配额和审计完成。
- **M7**：Docker、CI、备份、监控和发布文档完成。

每个里程碑都要运行对应验证、更新 `ChangeLog.md`、检查 `git diff --check`，并在独立 feature branch 提交。不得把 `outputs/`、缓存、密钥或本地数据库提交到仓库。

## 13. 风险与回滚

- Pipeline 依赖 Tkinter：先提取纯 Python runner，禁止在 Worker 中创建 GUI。
- 长任务占用 Worker：设置阶段超时、任务隔离和有限并发。
- 结果格式变化：schema version、manifest 和向后兼容转换器并行保留。
- 前端与 GUI 不一致：以固定输入 fixture 和 parity checklist 驱动验收。
- 数据或代码泄露：默认后端不返回路径/traceback，持续执行越权和容器扫描。
- 任一阶段失败时保留旧 `.bat` GUI 和同步 runner；异步 API 通过 feature flag 禁用，不影响原有本地工作流。

## 14. 阶段 D 本地实施记录（2026-09-14）

- 分支：`codex/react-buck-workspace`；状态：Buck 工作区本地实现并验证，尚未推送，不标记远端交付完成。
- 新增 `web/frontend`（React、TypeScript、Vite）：顶部分类导航、注册拓扑目录、左侧 Buck 参数、右侧结果标签页、任务提交/状态轮询、刷新恢复、错误重试、下载和手机宽度布局。
- 参数元数据来自新增 `/api/v1/topologies`，默认输入复用现有 Buck 定义。未接入拓扑禁用；没有波形/效率数据时明确显示未提供。
- Summary、Stress、Devices、Capacitor、Magnetics、Loss、Thermal、Geometry、Efficiency、Files 对接现有结构化报告分区。效率图只在确有扫描点时绘制；波形报告只有统计量时不构造时域曲线。
- 联调修复：API 合并桌面默认参数；补齐 Pydantic/Uvicorn 依赖；Worker 自动发现任务；队列不可用返回 503；按任务隔离 Pipeline 输出；下载 JSON 使用真实 job ID，且仅成功任务可下载。
- 验证：`npm run build` 通过；Playwright `9 passed`（包括真实 HTTP 文件流内容校验）；Python Web 相关测试 `10 passed`（含真实 Buck 同步 HTTP 计算、GUI 参数/数值对照、跨存储实例任务读取、Worker 函数、下载及失败隔离）。桌面和 390px 窄屏截图已检查。
- 启动文档和具体验证边界：`web/frontend/README.md`。前端测试响应由真实拓扑 fixture 驱动，但任务排队状态由测试拦截；外部 PostgreSQL/Redis/独立 Celery 进程尚未完成联合验收。
- 当前本机 Redis 6379 连接超时，前端和 API 可启动浏览，实际异步设计须先启动 Redis/Worker。
- 剩余范围：其他拓扑属于阶段 E；独立运行点/波形/效率扫描、任务取消和 PDF/CSV 等仍需后端接口；现有迁移和清理策略的生产完整性需另外验收。当前页面不模拟这些操作。

## 15. 统一完整设计执行方案（替代独立动作按钮）

经评估，前端不再展示 Run Capacitor、Run Magnetics、Generate Waveforms、Run Efficiency Sweep 四个独立按钮。用户确认设计输入后，由一个完整设计任务按固定顺序执行并统一输出结果。这能减少操作顺序错误、动作之间的状态不一致和“基础任务不存在”问题，同时保留每个阶段的可追踪状态。

### F1：统一请求与执行配置

- 在现有 `DesignJobCreate` 中增加 `execution_profile`，首期固定支持 `complete`。
- 增加可选 `operating_point`；未填写时由后端根据设计输入生成额定 Vin、100% 负载的默认运行点，并在响应中明确记录。
- 请求只包含 Pydantic 基础类型；禁止路径、模块名、表达式和内部对象。
- 保留 `schema_version`、幂等键和客户端请求 ID。相同输入与执行配置复用同一任务。

### F2：完整顺序 Worker

完整任务固定执行：

`validate → topology → devices → capacitor → magnetics → operating_point/waveform → loss → thermal → efficiency_sweep → report → finalize`

- 电容和磁性选择各执行一次。
- 波形、损耗和效率扫描必须复用已选硬件；效率扫描禁止逐点重新选型。
- 每个阶段写入进度、阶段状态、warning 和结构化错误。
- 阶段失败时保留已完成阶段结果，后续阶段标记 blocked/unavailable，不伪造成功结果。
- Worker 重试通过数据库原子状态检查保证幂等。

### F3：前端完整设计确认流程

- 移除四个独立 action 按钮及其独立轮询入口。
- 保留一个“确认并运行完整设计”按钮；提交前展示运行点和执行配置确认。
- 页面显示总进度、当前阶段、任务 ID、失败阶段和重试入口。
- 刷新页面后根据 job ID 恢复任务；提交期间防止重复点击。

### F4：统一结果与 artifact

- Summary、Capacitor、Magnetics、Waveforms、Efficiency、Loss、Thermal、Files 标签全部读取同一个完整任务结果。
- 没有数据的阶段显示明确 unavailable/blocked 状态，不使用旧结果或示例数据填充。
- artifact 使用任务独立目录和 manifest，记录类型、大小、SHA-256、schema 版本和生成阶段。
- 输出 JSON、CSV、波形图和效率曲线（仅在 Pipeline 实际生成时提供）。

### F5：恢复、迁移和集成验收

- 为完整任务保存带版本的可恢复快照，至少包含规范化输入、Pipeline 版本、已选电容/磁件/半导体身份与参数；禁止通过重新选型冒充恢复。
- 失败重试从最近安全阶段开始；运行中的任务不能被清理策略删除。
- 为 SQLite 旧表、PostgreSQL migration、Redis 重启和 Worker 重启增加测试。
- 端到端验证：设计提交 → 固定顺序执行 → 全部结果 → artifact 下载；覆盖队列不可用、阶段失败、重复提交和刷新恢复。

### 15.1 已完成工作处理

- E0 action schema、状态机和依赖契约保留为内部兼容模型，可供迁移和历史记录使用。
- E1/E2 action API 暂时保留兼容入口，但新前端不再依赖它们；后续统一任务稳定后再评估下线。
- 本计划取代 `button_actions_plan.md`，以后所有 Web 设计功能按 F1–F5 执行。

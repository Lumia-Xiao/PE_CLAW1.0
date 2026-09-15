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

### F4 本地实施记录（2026-09-15）

- 同一任务导出 result.json、可用阶段 CSV、真实采样波形 PNG 和真实扫描效率 PNG；不扫描或发布内部 Pipeline 文件夹。
- API 清单包含大小、SHA-256、schema 版本及阶段；result.json 列出其他文件，自身清单由 API 返回，避免自引用校验和。
- 下载须命中本任务 manifest 和固定 ID，校验路径归属、大小、hash 及任务成功状态；旧结果仍可下载已有文件。
- 结果页识别 blocked/unavailable、显示原因与警告；Files 展示元数据和下载；任务切换不复用上一任务结果。
- 验证包含真实 Buck 波形采样/导出、HTTP 文件字节/校验、跨任务文件拒绝、文件篡改和过期状态；浏览器验证含阻塞阶段、文件元数据、图像与移动端。详细计数以同次 ChangeLog 为准。
- 本地提交，未推送，暂不标记远端里程碑完成。Redis/PostgreSQL/独立 Worker 故障恢复及用户认证不属于此次验证；按 F5/生产安全阶段继续。

### 15.1 已完成工作处理

- E0 action schema、状态机和依赖契约保留为内部兼容模型，可供迁移和历史记录使用。
- E1/E2 action API 暂时保留兼容入口，但新前端不再依赖它们；后续统一任务稳定后再评估下线。
- 本计划取代 `button_actions_plan.md`，以后所有 Web 设计功能按 F1–F5 执行。

### F5 本地实施与验收记录（2026-09-15）

- **本地实现及 SQLite/Redis 链路通过，PostgreSQL/Docker 部署验收待环境具备后完成；不标记 F5 全部验收完成。**
- 完整 Buck 使用真实阶段回调：topology → devices → capacitor → magnetics → operating_point → efficiency_sweep → report → finalize。loss/thermal 已包含在固定硬件 operating-point refresh 中，完成时记录子阶段状态，避免重复计算和虚假进度。每个安全阶段边界保存带版本/输入摘要/校验和的内部报告 JSON 和公开部分结果。
- 新增任务领取租约、心跳、过期租约回收、三次自动恢复上限、attempt 输出隔离及最终发布保护。停止后的旧 Worker 不得覆盖新的检查点或结果。独立 recovery 进程在 Redis 恢复后重新投递数据库中的 queued 任务。
- 新增同一任务恢复接口、前端“从已保存阶段恢复”、失败阶段及部分结果；不兼容快照显式失败，用户可选择从头运行。相同完整请求通过数据库唯一键复用；client request ID 不允许换参数复用。
- Alembic 增加 0002/0003 修订，兼容未纳管的旧 SQLite 表，保留旧任务；迁移与运行模型分离。SQLite 自动迁移，PostgreSQL 显式 migrate。清理只操作到期终态任务，保护运行中任务、活动兼容 action 和未知目录。
- 后端专项：85 passed、2 skipped（无 PostgreSQL 测试连接；Windows 符号链接权限）；前端构建通过，Playwright 13 passed。SQL 数据库故障传播/恢复是故障注入测试，PostgreSQL 真实连接终止/重连测试已提供但未运行。
- 真实隔离联调：`pytest_temp/recovery-smoke-6cf2ed84/evidence.json`；job `c683c8e0-5295-4b6d-ac7b-7a5ff0bb66ed`。真实 HTTP 提交，在 capacitor 检查点后终止独立 Celery Worker、重启隔离 Redis；第二次执行从快照继续并成功，已选硬件摘要一致，重复投递没有第三次运行。HTTP 下载校验 11 个 artifact；1200 个真实波形采样、20 个有效效率点。
- 新增根 Dockerfile、迁移 service 和独立 recovery service；本机无 Docker/PostgreSQL，官方 PostgreSQL 二进制下载探测超时，未声明镜像构建、PostgreSQL 重启或 Compose 全链路已通过。
- 启动、升级、恢复、清理及测试命令：`docs/web-recovery.md`。检查点为完整报告，当前真实电容阶段快照约 35 MB，生产并发和存储容量需后续压测；保留完整类型与硬件信息优先于压缩优化。
- Git：在 `codex/react-buck-workspace` 本地提交，未推送；保留用户 outputs 和测试证据，不执行生产清理或修改用户运行中的服务。

### F5 PostgreSQL 部署验收补充（2026-09-15）

- **PostgreSQL 本地真实验收通过；Docker 配置校验通过，但镜像构建与容器链路仍受环境阻塞。F5 不标记全部完成，亦未推送远端。** 本记录更新上一次“无 PostgreSQL 环境”的现状，保留历史记录。
- 使用官方 EDB PostgreSQL 16.14 二进制创建独立临时集群，仅绑定 loopback 随机端口，随机 SCRAM 密码；不安装系统服务、不修改已有数据库。补装项目已声明的 psycopg 驱动。
- 新增 `scripts/verify_web_postgres_deployment.py`：自动建库、执行真实 PostgreSQL 专项测试、停止/重启测试数据库、运行完整 HTTP 恢复验收并保存证据；结束后停止自有集群和子进程，保留测试数据。
- PostgreSQL 专项 **4 passed**：数据库迁移/连接池重连；并发重复提交/领取/过期租约隔离/client ID 绑定；0001 旧版本升级；未纳管旧表迁移。重复迁移保留已有成功任务和结果。
- 实测修复：PostgreSQL 连接原本缺少超时，数据库停止后会长时间等待。`JobStore` 增加 5 秒连接超时并保留 `pool_pre_ping`；故障复验约 **5.09 秒**返回错误，数据库重启后原连接池恢复。此前失败运行日志保留，不作为通过证据。
- 完整链路：首先在 Redis 不可用时提交，确认 queued 状态已持久化；Redis 启动后由独立 recovery 服务投递。在电容检查点停止 Worker、Redis 和 PostgreSQL，重启后由同一 recovery 服务恢复任务，未由测试直接调用 recover 或手动投递恢复任务。
- 成功任务 `1768513f-9196-4d73-b37e-8054585e1d43`：attempt=2，全部阶段 succeeded，已选半导体/电容及基础候选摘要保持一致；11 个 artifact 的 HTTP 字节/hash 校验通过，1200 波形采样、20 效率扫描点，迟到重复投递未增加 attempt。
- 证据：`pytest_temp/postgres-deployment-65b9fe78/evidence.json`；细节 `pytest_temp/recovery-smoke-8864a620/evidence.json`。数据库测试日志及 JUnit XML 保留在前者目录。
- 数据库超时修改后回归：Web 后端 **85 passed、1 skipped**（Windows 符号链接权限）。本次未改 React 页面，未重复前端浏览器测试；上一轮浏览器验收保持历史结论。
- Docker：下载官方独立 Compose v5.5.1 并校验官方 SHA-256；`config --quiet` 通过，连接 `docker_engine` 命名管道失败。证据 `pytest_temp/pe-claw-f5-d3548325/evidence.json` 明确记录 `blocked`、`container_acceptance=false`。
- 新增 `scripts/verify_web_docker_deployment.py`，供具备 Docker 引擎的主机执行独立 Compose 项目的镜像构建、真实 HTTP 设计、数据库/Redis/Worker 重启、硬件摘要、artifact 和整栈重启持久化验收。当前仅执行其前置检查，容器部分尚未验证。
- Compose 前端端口支持 `PE_CLAW_WEB_PORT`，默认仍为 5173，验收自动使用空闲端口；补充前端 `.dockerignore`，避免 Windows node_modules 覆盖镜像内 Linux 依赖。未停止用户现有 5173 服务。
- **下一步唯一环境门槛**：在受支持的 Windows 版本启用 WSL2 并启动 Docker Desktop，或使用已有 Linux Docker 主机，然后执行 `python scripts/verify_web_docker_deployment.py`。本机 Windows 11 Home 22H2/22621 低于当前 Docker 文档的 Windows 11 22631 要求；系统组件启用需要管理员权限。此次未升级/重启操作系统，未安装不受支持的旧 Docker。
- 通过真正的容器验收后，再推进认证、用户资源归属、配额及 HTTPS 发布；不要把配置验证视为生产可发布证明。

### F5-W：Windows 原生部署验收（替代 Docker 部署验收，2026-09-15）

用户决定只使用 Windows，因此 F5 的部署门槛改为 F5-W。Docker/WSL 不再是 Windows 交付前置条件；已有 Docker 文件仅保留作可选开发资产。

- **W1 依赖安装**：固定 Python、Node.js、PostgreSQL、Redis/Memurai、NSSM/WinSW、IIS URL Rewrite/ARR 版本；安装原生 PostgreSQL 和 Redis 服务，创建最小权限账号、数据库、artifact 目录和服务账号 ACL。数据库与 Redis 只允许受控内网访问。
- **W2 服务化**：使用 NSSM 或 WinSW 注册 Uvicorn API、Celery Worker（Windows 使用 `--pool=solo`）和独立 Recovery 服务。统一环境变量、代码/库版本、自动启动、失败重启、日志轮转、健康检查；先执行 `python -m alembic upgrade head`，再启动应用服务。
- **W3 IIS 发布**：IIS 静态发布 `web/frontend/dist`，通过 URL Rewrite/ARR 将 `/api/*` 转发到 `127.0.0.1:8000`；只开放 443，启用证书、HTTP→HTTPS、CORS 白名单、请求限制和安全响应头，隐藏数据库、Redis、Worker 端口。
- **W4 重启恢复**：真实 Windows 服务执行完整 Buck 任务，在 capacitor 检查点停止 Worker，重启 Redis，由独立 Recovery 自动重新投递；停止/启动 PostgreSQL 验证 5 秒连接超时与 `pool_pre_ping` 重连；重启 API/IIS 和整台机器后继续轮询原 job，迟到投递不能产生第三次 attempt。
- **W5 集成验收**：验证 IIS 页面/API、迁移、备份恢复、服务权限、路径隔离、artifact hash 下载、刷新恢复和完整结果。证据记录 Windows/依赖版本、服务状态、迁移版本、job/attempt/阶段、artifact hash、重启时间线和日志目录。测试使用独立数据库与 artifact 目录，不触碰用户服务或 `outputs/`。
- F5-W 通过后才进入认证、用户归属、配额、审计和 HTTPS 加固。Docker 配置验证不能替代 F5-W。

### F5-W 执行记录（2026-09-15）

- 已新增 `deployment/windows/`：Windows 部署说明、环境变量模板、NSSM/WinSW 服务注册脚本、IIS `web.config`、IIS 配置脚本和原生验收脚本。
- 本机 Redis 原生服务已存在且为 Running/Automatic；React `dist` 已成功构建；PowerShell 部署脚本语法检查和 API/IIS 配置文件检查已完成。
- PostgreSQL 原生临时集群、完整 Buck 恢复、数据库断线重连和 artifact 校验已在本机通过，证据沿用 `pytest_temp/postgres-deployment-65b9fe78/evidence.json`。
- 尚未执行服务注册和 IIS HTTPS 验收：本机当前没有可确认的 IIS/URL Rewrite/ARR 状态，且当前会话不是管理员；不擅自安装系统组件、创建 Windows 服务或修改现有 Redis 服务。
- 因此 F5-W 当前状态为 **W1 部署资产已准备、W2/W3/W4/W5 待管理员环境执行**，不能标记 F5-W 完成。下一步是在管理员 PowerShell 中配置 `pe-claw.env.ps1`、安装 NSSM 与 IIS 组件后运行对应脚本。

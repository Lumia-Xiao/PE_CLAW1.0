# PE-Claw 本地 Tkinter 到 Web 版本迁移实施计划

## 1. 任务目标

将当前通过 `run_pe_claw_gui.bat` 启动的本地 Tkinter 设计工具，逐步改造成浏览器访问的 Web 系统。

用户最终通过浏览器填写设计参数、提交设计、查看进度、查看结果并下载报告；核心 Python 代码、器件库、公式和 Pipeline 保留在受控后端服务器，不随网页交付给用户。

本计划面向负责实施的学生。学生应从 GitHub 仓库下载项目，通过 Codex 辅助阅读、修改、测试和记录，按阶段完成任务，不得一次性重写整个项目。

## 2. 项目来源和基础约束

远端仓库：

```text
https://github.com/Lumia-Xiao/PE_CLAW1.0.git
```

本地原始入口：

```text
run_pe_claw_gui.bat
```

核心目录：

```text
src/pe_claw_gui/     原有 Tkinter、模型、Pipeline、器件库和报告
tests/               原有测试和回归测试
scripts/             运行检查和维护脚本
outputs/             本地设计生成结果，不得删除
web/                 Web 前端和后端实现目录
Plan/                项目计划和验收记录
```

必须遵守以下约束：

- 不修改设计公式、单位、器件选择策略和原有报告语义来迁就 Web 测试。
- 不把 Tkinter 控件、窗口对象或 GUI 状态传入 Worker。
- Web API 只能接收 JSON 基础类型和经过校验的枚举值。
- 不允许请求携带路径、Python 模块名、表达式、可执行代码或内部对象。
- 不返回源码、内部路径、完整器件库、调试 traceback 或服务器环境信息。
- 不删除 `outputs/`、迁移证据、历史基线或用户生成结果。
- 每个阶段必须先验证再提交；没有测试证据不能标记阶段完成。
- 未经明确授权不得 push、部署生产服务、删除数据库或停止用户已有服务。

## 3. 学生开始工作前的基线步骤

### 输入

- GitHub 仓库地址。
- 可用的 Python 3.10 或更高版本。
- Tkinter 运行环境。
- 项目依赖安装权限。

### 操作

```powershell
git clone https://github.com/Lumia-Xiao/PE_CLAW1.0.git
cd PE_CLAW1.0
git branch --show-current
git status --short
python --version
python scripts/check_runtime_dependencies.py
```

启动原始 GUI：

```powershell
.\run_pe_claw_gui.bat
```

### 输出

- 基线分支名称和 commit ID。
- Python、Tkinter、numpy、pandas、scipy、matplotlib 版本。
- 原始 GUI 启动截图或日志。
- 一份完整 Buck 设计输入和输出结果。
- 基线结果目录和报告字段清单。

### 验收指标

- `run_pe_claw_gui.bat` 能正常启动。
- 至少完成一次原始 Buck 设计。
- 设计结果包含输入、拓扑、器件选择、波形、损耗、热和效率等已有字段。
- `git status` 中没有学生无法解释的修改。
- 基线结果被保存，不覆盖已有 `outputs/`。

### 不通过时的处理

先修复运行环境或记录阻塞原因，不得进入 Web API 实现。基线失败时，后续结果无法证明与原系统一致。

## 4. 阶段一：梳理 Tkinter 与 Pipeline 调用链

### 目标

找出 GUI 输入、校验、Pipeline 调用和报告输出的真实路径，识别可以复用的纯 Python 代码。

### 输入

- `run_pe_claw_gui.bat`。
- `src/pe_claw_gui/`。
- 原始 GUI 页面和设计结果。
- 相关测试。

### 输出

创建文档 `docs/web-pipeline-inventory.md`，至少包括：

- GUI 页面和导航结构。
- 每个输入字段的名称、类型、单位、默认值、最小值和最大值。
- 拓扑注册和能力声明位置。
- Pipeline 阶段顺序。
- 器件选择、波形、损耗、热和效率之间的依赖。
- 报告对象和结构化输出入口。
- GUI 专属代码与可复用纯 Python 代码的边界。
- 不能直接复用的代码和原因。

### 验收指标

- 能从 GUI 事件追踪到最终 Pipeline 调用。
- 每个输入字段都有明确单位。
- 能指出至少一条从输入到报告的完整调用链。
- 没有通过猜测补写算法。
- 计算核心没有因为梳理工作被修改。

## 5. 阶段二：冻结 Pydantic 请求和响应模型

### 目标

先定义稳定的 Web 契约，再写 FastAPI 路由。

### 输入

- `docs/web-pipeline-inventory.md`。
- 现有输入模型。
- 现有报告模型。
- 基线 JSON 或结构化报告。

### 输出

新增或完善 Web schema，至少包含：

```text
DesignRequest
BuckDesignRequest
DesignJobCreate
DesignJobResponse
DesignResultResponse
DesignError
ArtifactManifestEntry
```

建议首期 API：

```text
GET  /api/v1/health
GET  /api/v1/topologies
POST /api/v1/design/buck
```

### 输入约束

- 只允许 JSON 基础类型、列表、字典和受控枚举。
- 禁止路径、模块名、表达式、任意类名和内部对象。
- 所有电压、电流、功率、频率、纹波和温度字段明确单位。
- 对范围、组合关系和不支持拓扑给出稳定错误。

### 验收指标

- 正常请求可以被 Pydantic 解析。
- 缺少字段返回字段级错误。
- 越界值被拒绝。
- 非法拓扑被拒绝。
- schema 有明确版本字段。
- API 示例 JSON 可直接用于测试。

## 6. 阶段三：实现同步 FastAPI Buck 接口

### 目标

先实现一次请求、一次计算、一次 JSON 响应，证明 Web 层不会改变计算结果。

### 输入

- 已冻结的 Pydantic schema。
- 可复用的纯 Python Buck Pipeline。
- 阶段一生成的基线请求。

### 输出

- FastAPI 应用入口。
- `POST /api/v1/design/buck`。
- API 启动说明。
- 正常、校验失败和 Pipeline 失败测试。
- GUI 与 API 结果对比脚本。

### 验收指标

- API 在本机可以启动。
- 正常 Buck 请求返回 200 和结构化 JSON。
- 关键器件、数值、单位、状态和报告字段与 GUI 基线一致。
- 允许的数值误差必须有说明。
- 失败响应不暴露 traceback、源码路径或环境变量。
- API 测试至少覆盖正常请求、缺字段、越界和计算失败。

### 阶段门槛

同步接口没有通过之前，不得引入 Celery、Redis 或 React 任务页。

## 7. 阶段四：持久化设计任务

### 目标

为异步执行准备持久化任务状态和结果引用。

### 输入

- 同步 API。
- 任务状态机。
- 报告结构。

### 输出

- `design_jobs` 数据模型。
- SQLite 开发数据库。
- Alembic 迁移。
- 创建任务、查询任务和读取结果接口。

### 状态

```text
queued → running → succeeded
                 ↘ failed
```

### 验收指标

- 每个任务有唯一 ID。
- 相同任务状态可跨进程读取。
- 任务结果不会写入请求进程内存作为唯一副本。
- 迁移可重复执行。
- 旧表和已有数据不会被无提示删除。
- 查询任务不会再次执行设计。

## 8. 阶段五：Redis/Celery 异步任务

### 目标

将同步设计提交改为异步任务，API 快速返回任务 ID。

### 输入

- 已持久化的任务模型。
- 同步 Runner。
- Redis 服务。

### 输出

- Celery 应用和 Worker。
- Redis 队列配置。
- 异步任务提交接口。
- 任务状态查询接口。
- Worker 启动和故障排查文档。

### 验收指标

- 提交接口返回 202 和 job ID。
- Worker 能执行完整 Buck 任务。
- 任务状态可轮询。
- Redis 不可用时返回清晰的队列错误。
- 任务失败保存结构化错误。
- 同一个幂等键不会产生重复设计。
- Worker 使用受控并发；Windows 下优先使用 `--pool=solo`。

## 9. 阶段六：完整顺序 Worker

### 目标

用一个完整任务替代多个互相依赖的独立按钮。

### 固定顺序

```text
validate
→ topology
→ devices
→ capacitor
→ magnetics
→ operating_point
→ loss
→ thermal
→ efficiency_sweep
→ report
→ finalize
```

### 输入

- 设计请求。
- 已有 Pipeline adapter。
- 已选硬件和运行点模型。

### 输出

- 一个完整设计任务。
- 每阶段状态、进度、警告和错误。
- 统一结果报告。
- 失败阶段后的 blocked/unavailable 信息。

### 验收指标

- 电容和磁件各只选择一次。
- 波形、损耗、热和效率复用已选硬件。
- 阶段失败后后续阶段不伪造成功。
- 每个阶段可追踪开始、完成和失败状态。
- 重复投递不会并发执行同一任务。
- 完成任务只生成一份统一结果。

## 10. 阶段七：React 前端复刻 Tkinter 核心流程

### 目标

让用户无需运行 `.bat` 即可在浏览器完成一次完整设计。

### 输入

- API schema。
- GUI 页面截图、标签、导航和字段清单。
- 任务状态模型。

### 输出

- React/TypeScript 应用。
- 顶部或侧边导航。
- 拓扑和参数表单。
- 设计确认页。
- 单一“确认并运行完整设计”按钮。
- 任务进度和失败重试页。
- 结果页。

### 验收指标

- 字段、单位、默认值和校验与 API 一致。
- 提交期间防止重复点击。
- 刷新页面可以根据 job ID 恢复任务。
- API 不可用时显示可理解的错误。
- 桌面宽度和窄屏可用。
- 不保存后端内部对象到浏览器状态。

## 11. 阶段八：结果、报告和 artifact

### 输入

- 完整任务报告。
- 公开结果字段字典。
- 前端结果视图。

### 输出

- 统一 `result.json`。
- CSV 导出。
- 波形图和效率图。
- artifact manifest。
- 下载接口和前端 Files 页面。

### Manifest 最小字段

```text
id
name
media_type
size
sha256
schema_version
stage
download_url
```

### 验收指标

- 下载文件属于当前 job。
- 路径越界、跨任务 ID、篡改文件和过期任务都会被拒绝。
- manifest hash 与实际下载字节一致。
- 无数据阶段显示 unavailable 或 blocked。
- 不扫描和暴露内部 Pipeline 目录。
- JSON、CSV、PNG 只在确有真实数据时生成。

## 12. 阶段九：快照、恢复、迁移和清理

### 输入

- 完整 Worker。
- 数据库和 Redis。
- 阶段安全边界。

### 输出

- 版本化 checkpoint。
- Worker 租约和心跳。
- stale job 恢复。
- 重试接口。
- artifact 清理策略。
- SQLite 旧表和 PostgreSQL migration。

### 验收指标

- Worker 在 capacitor 后中断，重启后从安全阶段继续。
- 已选器件摘要保持一致，不通过重新选型冒充恢复。
- Redis 重启后 durable queued 任务可以重新投递。
- 数据库连接短暂中断后可恢复。
- 运行中任务不会被清理。
- 旧 Worker 不能覆盖新 Worker 的 checkpoint 或最终结果。
- 不兼容快照明确失败，并允许显式从头开始。

## 13. 阶段十：Windows 原生部署

如果最终只使用 Windows，应在功能完成后单独部署，不要在早期同时处理系统服务问题。

### 输入

- 已通过测试的 API、Worker 和 Recovery。
- Windows PostgreSQL。
- Windows Redis 或 Memurai。
- IIS、URL Rewrite 和 ARR。
- NSSM 或 WinSW。

### 输出

- PostgreSQL 初始化和备份说明。
- Redis 服务说明。
- API、Worker、Recovery 服务注册脚本。
- IIS 静态站点和 `/api` 反向代理。
- HTTPS 配置。
- Windows 服务重启验收脚本。

### 验收指标

- PostgreSQL、Redis、API、Worker、Recovery 和 IIS 可以自动启动。
- API、Worker、Recovery 使用相同的数据库、Redis、artifact 和代码版本。
- Redis、Worker、PostgreSQL 重启后完整任务可以恢复。
- IIS 能访问前端并代理 API。
- 用户无法访问 Python 源码、器件库和内部目录。
- 日志不包含数据库密码、token 或完整 traceback。

## 14. 阶段十一：认证、授权、配额和审计

此阶段必须在核心设计流程稳定后开始。

### 输出

- 登录和会话。
- 用户 ID 与 job 归属。
- artifact 所有权检查。
- 并发任务限制。
- 单任务超时。
- 每日配额。
- 审计日志。

### 验收指标

- 未登录用户不能提交任务。
- 用户 A 不能读取用户 B 的 job、result 或 artifact。
- 超出并发数、请求大小或每日配额时稳定返回错误。
- 管理员操作记录用户、任务、时间和结果。
- CORS、CSRF、Cookie 或 Authorization header 配置经过测试。

## 15. 阶段十二：最终发布和代码保护

### 输入

- 已完成的 Web 系统。
- Windows 部署配置。
- 安全测试结果。

### 输出

- 发布包或服务器部署包。
- 备份和恢复文档。
- 运维启动、停止、升级和回滚文档。
- 安全扫描报告。
- 最终验收报告。

### 验收指标

- 新机器可以按文档部署。
- 旧 job 结果在升级后仍可读取。
- 数据库和 artifact 有备份。
- API 不返回源码和内部路径。
- 核心 Python 代码只存在后端受控环境。
- 明确说明：服务器端代码可以降低客户端泄露风险，但不能承诺绝对不可逆向或绝对安全。

## 16. 每个阶段的标准交付格式

学生完成任一阶段时，必须提交以下内容：

```text
阶段名称：
目标：
修改文件：
新增接口或行为：
输入示例：
输出示例：
验收指标：
执行的测试命令：
测试结果：
已知限制：
回滚方式：
Git commit：
```

测试结果必须区分：

- 通过。
- 失败。
- 跳过及原因。
- 环境阻塞。
- 尚未执行。

不能把“代码看起来正确”写成测试通过，也不能把 schema 测试通过写成真实 Redis、PostgreSQL 或 Windows 服务验收通过。

## 17. Codex 辅助编程工作流

学生每次向 Codex 提交任务时，应包含：

1. 当前分支和 `git status`。
2. 当前阶段名称和阶段目标。
3. 相关文件路径。
4. 已有输入和预期输出。
5. 需要执行的验证命令。
6. 不得修改的内容，例如公式、单位、`outputs/` 或原有 GUI。

推荐提示模板：

```text
当前项目：PE-Claw
当前分支：codex/<stage-name>
当前阶段：阶段 X：<名称>
目标：<一句话目标>
输入：<文件、请求、基线 fixture>
预期输出：<接口、文件、结果或行为>
验收指标：<可测量条件>
禁止修改：<公式、库、outputs、旧 GUI 等>
请先阅读相关代码和测试，提出最小修改方案，然后执行实现和验证。
```

Codex 处理每个阶段时应遵循：

1. 读取 `AGENTS.md`、当前计划和相关测试。
2. 检查当前分支和未提交修改。
3. 先说明影响范围和测试命令。
4. 做最小改动。
5. 先跑局部测试，再跑阶段要求的集成测试。
6. 更新 `ChangeLog.md` 或阶段记录。
7. 执行 `git diff --check`。
8. 提交一个单一、可回滚的 commit。
9. 报告真实验证结果和未完成事项。

## 18. 分支和远端策略

每个阶段使用独立分支：

```text
codex/web-baseline
codex/web-api-contract
codex/web-sync-api
codex/web-persistence
codex/web-celery
codex/web-complete-worker
codex/web-frontend
codex/web-artifacts
codex/web-recovery
codex/web-windows-deploy
codex/web-security
```

每个分支都应从上一个已验收阶段创建。学生不得直接修改 `master`，不得覆盖其他人的分支，不得在没有测试证据时合并。

从 GitHub 下载时要特别注意：本地未 push 的 commit 不会出现在远端。任务交接时必须提供：

- 远端 commit ID。
- 分支名称。
- 本地未 push commit 列表。
- 工作区未跟踪文件列表。
- 需要保留的 `outputs/` 和测试证据。

## 19. 最终验收链条

最终必须按照以下顺序验收：

```text
原有 Tkinter 基线
→ 同步 FastAPI Buck
→ 持久化任务
→ Redis/Celery 异步任务
→ 完整顺序 Worker
→ React 参数和确认页面
→ 统一结果和 artifact
→ 刷新恢复和失败重试
→ Redis/Worker/PostgreSQL 故障恢复
→ Windows 服务化
→ IIS/HTTPS
→ 登录、授权、配额和审计
```

最终通过条件：

- 用户无需运行 `.bat` 即可完成一次完整 Buck 设计。
- Web 结果与 Tkinter 基线关键字段一致。
- 任务状态、阶段、错误和恢复行为可验证。
- artifact 下载安全且 hash 一致。
- Windows 服务可以启动、停止、重启和恢复。
- 用户不能通过网页获取后端源码和内部文件。
- 所有测试、环境限制和未完成项都写入最终验收报告。


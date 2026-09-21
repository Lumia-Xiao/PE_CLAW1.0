# PE-Claw Web 化与异步设计服务统一实施计划

- **状态**：Active
- **适用范围**：Web 功能迁移、异步设计任务、React 前端、结果文件和恢复机制。
- **部署范围**：Windows 原生部署另见 `Plan/Deployment/windows_native_deployment_plan.md`。
- **当前原则**：保留 Tkinter GUI 和现有确定性 Pipeline；Web 端只调用受控后端接口，不把核心计算迁移到浏览器。

## 1. 目标与范围

用户最终可以通过浏览器填写设计参数、提交设计、查看任务进度、查看统一结果并下载报告。后端继续复用 `src/pe_claw_gui` 中的 registry、controllers、pipeline、models、reports 和 visualization。

首期以 Buck 作为端到端验证拓扑，完成后再扩展其他拓扑。Web 计划不修改拓扑公式、器件筛选规则或既有 GUI 的计算口径。

不在首期范围内：重写拓扑公式、迁移 AI/Agent 逻辑、把核心计算放到浏览器、用前端状态替代后端任务状态。

## 2. 强制执行规则

1. 每个阶段先阅读现有实现，再进行最小范围修改。
2. 每个阶段必须有可复现的验收指标和测试证据；代码看起来正确不等于阶段完成。
3. 每次独立修改完成后更新 `ChangeLog.md` 或阶段记录，创建单一可回滚 commit，并 push 到对应远端分支。
4. 完成记录必须包含修改范围、测试命令和结果、分支、commit、push 状态及未完成事项。
5. 学生或协作者不得直接修改 `master`，不得覆盖其他分支，不得在没有测试证据时合并。
6. 不提交 `outputs/`、`pytest_temp/`、缓存、字节码、运行日志和本地密钥。
7. 不把 Tkinter 控件、窗口对象、GUI 状态或 Python 内部对象传入 Worker 或浏览器。
8. 任务、artifact、快照和临时文件必须按 job/run 独立隔离，不能复用其他任务的可变状态。
9. 阶段失败时保留已完成结果，后续阶段标记 `blocked` 或 `unavailable`，不得伪造成功。
10. 未明确授权时不 push 生产部署、不删除数据库、不停止用户已有服务。

## 3. 基线与交付格式

### 3.1 开始前基线

- 记录仓库地址、当前分支、commit、`git status`、Python/Node.js 版本。
- 运行原有 Tkinter Buck 设计，保存输入快照、关键数值、单位、状态、警告和生成文件清单。
- 确认原始 Pipeline 的阶段顺序、运行点刷新规则、输出目录规则和报告 provenance。
- 确认基线失败时先修复或记录阻塞原因，不进入下一阶段。

### 3.2 每阶段标准交付

```text
阶段名称：
目标：
修改文件：
验收命令：
验收结果：
生成证据：
Git 分支：
Git commit：
Push 状态：
未完成事项/环境限制：
```

## 4. 目标架构

```text
React Web
    | HTTPS JSON + artifact download
FastAPI API
    | Pydantic request/response schemas
Job repository (SQLite/PostgreSQL)
    | enqueue and durable status
Redis broker/result metadata
    | task delivery
Celery Worker / Recovery service
    | isolated run directory
Existing deterministic PE-Claw Pipeline
```

API 不直接暴露 Python 对象、绝对路径、任意模块路径、内部 traceback 或源码。浏览器只保存 request、job ID、结果引用和 UI 选项。

## 5. 实施阶段

### 阶段 0：基线和调用链盘点

**目标**：建立 Tkinter 到 Pipeline 的可追溯基线。

**工作内容**：

- 盘点表单、controllers、pipeline、models、reports 和 visualization 的输入输出。
- 记录 topology、devices、capacitor、magnetics、operating point、loss、thermal、efficiency、report、finalize 的依赖关系。
- 固定 Buck 输入 fixture，记录数值、单位、选定器件/磁件/电容、状态、warning 和 artifact。
- 明确 Web 不得依赖 Tkinter 控件或窗口对象。

**验收**：至少完成一次原始 Buck 设计；关键报告字段可从固定 fixture 复核；工作区没有无法解释的学生修改。

### 阶段 1：冻结请求、响应和输入契约

**目标**：建立稳定的 Pydantic API 边界。

**工作内容**：

- 定义 `DesignJobCreate`、`DesignJobResponse`、`DesignJobStatus`、`DesignError` 和 artifact 元数据模型。
- 只接受字符串、数字、布尔值、枚举、数组和对象；拒绝路径、表达式、模块名和任意 Python 对象。
- 固定 `schema_version`、幂等键、client request ID、execution profile 和可选 operating point。
- 标准化缺失字段、单位、范围和错误码；禁止把内部异常堆栈返回客户端。

**验收**：合法/非法请求均有稳定 schema 和错误响应；Pydantic 重验证通过；绝对路径和 traceback 不出现在响应中。

### 阶段 2：同步 FastAPI Buck MVP

**目标**：先完成无队列的同步后端闭环，确认 Web 与 GUI 计算一致。

**工作内容**：

- 实现拓扑目录和默认输入接口。
- 实现 Buck 设计提交和结构化结果接口。
- 复用现有 Pipeline，不在 API 层复制公式或另建器件筛选逻辑。
- 统一错误、warning、运行 ID、结果目录和 manifest 引用。

**验收**：OpenAPI 可提交一次 Buck 设计；关键器件、数值、单位、状态、warning 和报告字段与 GUI fixture 一致；接口不泄露内部路径。

### 阶段 3：持久化设计任务

**目标**：为异步执行保存任务状态、输入摘要、结果引用和生命周期。

**工作内容**：

- 建立 job、attempt、stage、artifact、snapshot 和 error 数据模型。
- 状态限定为 `queued`、`running`、`succeeded`、`failed`、`cancelled`、`expired`。
- 任务使用独立运行目录；相同输入和执行配置按幂等键复用任务。
- 实现 `GET /api/v1/design-jobs/{job_id}`，跨进程可读。
- SQLite 先作为本地实现，保留 PostgreSQL migration 边界。

**验收**：多个任务状态互不覆盖；服务重启后状态可读取；重复提交不产生错误的第二个任务；失败任务不会显示为成功。

### 阶段 4：Redis/Celery 异步任务

**目标**：将持久化任务投递给 Worker，并支持状态轮询。

**工作内容**：

- API 创建 queued job 后投递任务；Redis 不可用时返回可诊断错误，同时保留数据库任务状态。
- Worker 领取任务时使用 lease/attempt，更新阶段和心跳。
- 增加状态查询、失败信息、warning 和重试入口。
- Worker 重启、重复投递和过期 lease 必须有原子保护。

**验收**：任务可排队、执行、轮询和失败；刷新网页不丢失任务；Worker 重启不会覆盖新 attempt；重复投递不能制造第三次执行。

### 阶段 5：完整顺序 Worker

**目标**：将多个独立按钮统一为一条可审计的完整设计任务。

**固定顺序**：

```text
validate
-> topology
-> devices
-> capacitor
-> magnetics
-> operating_point/waveform
-> loss
-> thermal
-> efficiency_sweep
-> report
-> finalize
```

**工作内容**：

- 电容和磁性器件各执行一次。
- 波形、损耗、热和效率扫描复用已选硬件，禁止逐点重新选型。
- 每个阶段记录开始、结束、进度、warning、error 和 artifact。
- 阶段失败后后续阶段标记 blocked/unavailable，不生成伪造结果。
- 每个安全阶段保存带版本、输入摘要和校验和的内部快照。

**验收**：完整任务只生成一份统一结果；阶段状态可追踪；失败阶段及部分结果可解释；最终 report 与各阶段 artifact 属于同一 job/run。

### 阶段 6：React 前端复刻核心流程

**目标**：用户无需运行 `.bat` 即可通过浏览器完成一次设计。

**工作内容**：

- 复刻分类导航、拓扑目录、参数表单、设计确认、任务提交和状态页。
- 只保留一个“确认并运行完整设计”主操作，不再暴露会造成顺序错误的独立动作按钮。
- 显示 job ID、阶段、进度、warning、失败阶段、重试入口和刷新恢复状态。
- 页面保存 request、job ID、结果引用和 UI 选项，不保存后端内部对象。
- 适配桌面、窄屏和错误状态；使用真实 API schema，不用示例数据掩盖缺失阶段。

**验收**：Buck 页面完成 parity smoke test；提交、排队、刷新、失败和重试可操作；API 不可用时有明确提示；移动端不发生关键控件遮挡。

### 阶段 7：统一结果、报告和 artifact

**目标**：浏览器所有结果页面读取同一份最终任务结果。

**工作内容**：

- 对接 Summary、Stress、Devices、Capacitor、Magnetics、Waveforms、Efficiency、Loss、Thermal、Geometry 和 Files。
- manifest 至少记录 artifact ID、类型、相对路径、大小、SHA-256、schema 版本、生成阶段和 job ID。
- 下载只允许命中当前 job 的 manifest 和固定 artifact ID。
- 未生成的结果显示 unavailable/blocked，不读取旧任务或示例文件。
- 支持 JSON、CSV、PNG 和报告文件的安全下载与字节/hash 校验。

**验收**：跨任务路径访问被拒绝；文件篡改可检测；下载文件可打开；结果页不混用历史任务数据。

### 阶段 8：快照、恢复、迁移和清理

**目标**：支持 Worker、Redis、数据库和 API 重启后的可靠恢复。

**工作内容**：

- 快照包含规范化输入、Pipeline 版本、已选硬件身份和阶段结果引用。
- 从最近安全阶段恢复，禁止通过重新选型冒充恢复。
- 增加 SQLite 旧表、Alembic/PostgreSQL migration、Redis 重启和 Worker 重启测试。
- 清理策略只处理到期终态任务，保护运行中的任务、活动兼容 action 和未知目录。
- 记录恢复时间线、attempt、阶段和 artifact hash。

**验收**：在 capacitor 检查点停止 Worker，重启 Redis 后任务可继续；数据库断线能快速失败并在恢复后重连；迟到投递不产生第三次 attempt；旧任务仍可读取。

### 阶段 9：拓扑扩展

**目标**：在 Buck 闭环稳定后逐个扩展其他拓扑。

**工作内容**：

- 为每个拓扑建立输入 fixture、结果契约和独立适配器。
- 逐步接入 DC-DC、DC-AC、AC-DC 等拓扑，不在一次修改中批量改变公式。
- 保持每个拓扑的用户输入、器件选择、损耗、热、磁件、电容和效率口径。
- 每个拓扑独立完成 API、Worker、前端、artifact 和恢复验收。

**验收**：每个新增拓扑均有 GUI parity、任务隔离、结果下载和失败恢复证据。

### 阶段 10：认证、授权、配额和审计

**目标**：在核心设计链路稳定后增加多用户安全边界。

**工作内容**：

- 未登录不能提交和读取任务。
- job、artifact、快照和日志绑定用户/项目资源归属。
- 限制并发、输入规模、运行时间和存储容量。
- 记录用户、任务、时间、状态转换、下载和管理操作。

**验收**：用户 A 不能读取用户 B 的 job 或 artifact；超限请求稳定拒绝；审计记录完整；权限测试覆盖成功和失败路径。

### 阶段 11：最终发布和代码保护

**目标**：形成可交付的 Web 系统和运行文档。

**工作内容**：

- 完成启动、升级、恢复、清理、备份和故障排查文档。
- 生产配置不包含密钥；限制 CORS、文件路径、请求大小、响应头和日志内容。
- 运行依赖、迁移版本、Pipeline 版本和前端版本可追溯。
- Windows 原生部署按独立部署计划执行，不把环境配置检查当成部署完成。

**最终验收**：用户无需 `.bat` 完成完整 Buck 设计；Web 与 GUI 关键字段一致；任务状态、恢复、artifact hash、权限和环境限制均有证据。

## 6. 当前实施记录与未完成事项

- 已有本地 Web Buck 工作区、API、React 页面、任务持久化、恢复链路和 artifact 校验记录，但部分记录仍标明未推送或未完成生产验收。
- SQLite/Redis、本地 PostgreSQL 专项和部分 HTTP/前端测试已有证据；Docker 容器链路尚未完成。
- Windows 原生部署资产已经准备，但服务注册、IIS/HTTPS、完整 Windows 重启恢复尚未完成，详见独立部署计划。
- 其他拓扑、独立运行点/波形/效率扫描、任务取消、认证授权、配额和审计不能因 Buck 验收通过而自动标记完成。
- 当前仓库中用户手动删除的 Web 文件和生成目录不属于本计划文档重组范围，不在本次恢复或提交。

## 7. 分支和远端策略

每个阶段使用 `codex/<stage-name>` 或用户指定分支。阶段完成后必须提供：远端 commit ID、分支名称、本地未 push commit、未跟踪文件列表、测试证据和环境限制。未经明确验收不得把阶段合并到 `master`。

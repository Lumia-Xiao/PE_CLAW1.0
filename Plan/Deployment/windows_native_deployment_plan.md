# PE-Claw Windows 原生部署计划

- **状态**：Prepared / Pending administrator environment
- **上级计划**：`Plan/Active/web_migration_plan.md`
- **目标**：在 Windows 主机上部署 Web API、Worker、Recovery、PostgreSQL/Redis 和 IIS，完成可恢复的 Buck 端到端验收。
- **原则**：Docker/WSL 不是 Windows 交付前置条件；部署验证使用独立数据库、artifact 目录和测试任务，不触碰用户已有 `outputs/`、生产服务或数据库。

## 1. 当前边界

已具备：

- `deployment/windows/` 部署说明、环境变量模板、服务注册脚本、IIS 配置和原生验收脚本。
- React `dist` 构建和 PowerShell/API 配置文件静态检查。
- Redis 原生服务存在并可运行。
- PostgreSQL 临时集群、数据库迁移、恢复链路和 artifact 校验已有本地专项证据。

尚未完成：

- 管理员权限下的服务注册和服务账号 ACL。
- IIS、URL Rewrite、ARR、证书和 HTTPS 验收。
- 真实 Windows 服务状态下的 Worker/Redis/PostgreSQL 重启恢复。
- W5 完整集成验收和最终发布结论。

## 2. 强制规则

1. 每一步先执行前置检查，失败时保留 `blocked`，不得用配置文件存在代替真实部署通过。
2. 使用独立测试数据库、Redis namespace、artifact 根目录和 job 数据。
3. 不停止、覆盖或修改用户已有 Redis、数据库、IIS 和 `outputs/`。
4. 服务注册、IIS 配置、证书和 ACL 修改必须在管理员 PowerShell 中执行。
5. 每一步完成后运行对应验证，更新 `ChangeLog.md`，创建 commit 并 push；未完成项必须明确记录。

## 3. 部署步骤

### D1：环境和依赖检查

**内容**：确认 Windows 版本、Python、Node.js、PostgreSQL、Redis/Memurai、NSSM/WinSW、IIS、URL Rewrite、ARR 和证书能力；确认管理员权限和端口规划。

**输出**：版本清单、服务清单、端口清单、环境变量模板和阻塞项。

**验收**：所有必需依赖可执行；缺失管理员权限、IIS 组件或证书时明确阻塞，不继续安装系统组件。

### D2：数据库、Redis 和目录隔离

**内容**：创建最小权限数据库用户、独立测试数据库、Redis 配置、代码目录、artifact 目录、日志目录和服务账号 ACL；执行 `alembic upgrade head`。

**输出**：迁移版本、目录 ACL、连接测试和备份恢复测试记录。

**验收**：数据库迁移幂等；Redis 可连接；服务账号只能访问必要目录；测试目录不指向用户 `outputs/`。

### D3：API、Worker 和 Recovery 服务化

**内容**：使用 NSSM 或 WinSW 注册 Uvicorn API、Celery Worker（Windows 使用 `--pool=solo`）和 Recovery 服务；统一环境变量、自动启动、失败重启、健康检查和日志轮转。

**输出**：服务名称、启动参数、服务账号、依赖顺序、日志位置和健康检查结果。

**验收**：服务可启动、停止、重启；API health endpoint 正常；Worker 可以领取测试 job；Recovery 不重复投递。

### D4：IIS 和 HTTPS 发布

**内容**：发布 `web/frontend/dist`；配置 `/api/*` 到 `127.0.0.1:8000` 的 URL Rewrite/ARR；只开放 443；配置证书、HTTP 到 HTTPS、CORS 白名单、请求限制和安全响应头；隐藏数据库、Redis 和 Worker 端口。

**输出**：IIS site/application pool 配置、证书信息、反向代理检查和浏览器访问证据。

**验收**：浏览器可加载页面；API 可通过 IIS 访问；HTTPS 证书有效；内部端口不能从外部访问；静态文件和 API 路由不泄露服务器路径。

### D5：真实 Buck 服务恢复验收

**内容**：提交真实 Buck 设计，记录 job/attempt/阶段/selected hardware/artifact hash；在 capacitor 检查点停止 Worker，重启 Redis，由 Recovery 自动恢复；停止/重启 PostgreSQL，确认连接超时和 `pool_pre_ping` 重连；重启 API/IIS 后继续轮询原 job。

**输出**：完整时间线、阶段状态、恢复前后硬件摘要、artifact hash 和错误日志。

**验收**：任务从最近安全阶段继续；不重新选型；迟到投递不产生第三次 attempt；所有结果属于同一 job/run；下载 hash 与 manifest 一致。

### D6：备份、升级和最终集成验收

**内容**：验证数据库备份/恢复、旧 migration 升级、服务重启、日志轮转、目录权限、任务隔离、artifact 下载、浏览器刷新恢复和失败重试。

**输出**：Windows/依赖版本、服务状态、迁移版本、job/attempt/阶段、artifact hash、重启时间线和日志目录。

**验收**：完成 IIS 页面/API、迁移、备份、恢复、服务权限、路径隔离、artifact 下载和完整结果验收；形成最终 `pass`、`conditional` 或 `blocked` 结论。

## 4. 需要执行的验证命令

以下命令必须在目标环境中按实际路径执行，并保存输出到独立 `pytest_temp` 证据目录：

```text
python -m alembic upgrade head
python scripts/verify_web_postgres_deployment.py
python scripts/verify_web_docker_deployment.py  # 仅 Docker 环境需要，不替代 Windows 验收
python scripts/verify_web_windows_deployment.py
```

不存在的脚本或不具备的环境不得用手工描述替代；应先补充脚本或记录 `blocked`。

## 5. 完成定义

- D1 至 D6 均有真实环境证据。
- API、Worker、Recovery 和 IIS 服务可以启动、停止、重启和恢复。
- 完整 Buck 任务在 Worker/Redis/PostgreSQL/API 重启后可恢复，且不发生重复 attempt 或重新选型。
- 任务与 artifact 路径隔离，下载 hash 与 manifest 一致。
- 生产密钥、数据库、Redis、Worker 端口和内部路径不暴露。
- 最终验收报告明确记录系统版本、限制、未验证风险、commit、push 和回滚方式。


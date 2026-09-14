# PE-Claw React 工作区

当前交付为阶段 D 的 Buck 工作区：复用桌面版的 Categories → Topologies → 左侧表单/右侧结果页流程。其他注册拓扑展示为尚未接入，属于阶段 E。

## 本地启动

要求 Node.js 22.12+、Python 3.11+（现有 Web schema 使用 StrEnum）、Redis，以及与 API 使用同一数据库/文件目录的 Celery Worker。本项目当前没有登录鉴权，开发服务只绑定 localhost。

在仓库根目录安装 Python 依赖：

```powershell
python -m pip install -e ".[web-test]"
```

API 和 Worker 的两个终端都先进入仓库根目录，并设置相同的配置。以下默认配置使用 SQLite 文件与 Redis 0 号库：

```powershell
$env:PE_CLAW_DATABASE_URL = 'sqlite:///pe_claw_jobs.db'
$env:PE_CLAW_REDIS_URL = 'redis://127.0.0.1:6379/0'
$env:PE_CLAW_ARTIFACT_ROOT = 'outputs/web_jobs'
```

终端 1（API）：

```powershell
python -m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000
```

终端 2（Worker，Windows 开发使用 solo；生产部署建议 Linux）：

```powershell
python -m celery -A pe_claw_web.workers.celery_app:celery_app worker --pool=solo --loglevel=info
```

终端 3（前端）：

```powershell
cd web/frontend
npm ci
npm run dev
```

打开 http://127.0.0.1:5173。选择 DC-DC，再选择 Buck Diode Rectified Unidirectional。
开发服务器将 `/api` 转发到 `http://127.0.0.1:8000`；如需修改目标，在启动 Vite 前设置 `PE_CLAW_API_URL`。
浏览器不直接访问数据库、Redis 或 Python 源码。

## 使用与结果边界

- 七个设计参数的默认值来自 `GET /api/v1/topologies`；该接口从注册表、Buck 默认输入和 Pydantic 字段范围生成元数据。
- 提交 `POST /api/v1/design-jobs`，轮询任务状态，成功后读取结果与 artifact 清单。
- 当前任务编号和表单草稿保存在浏览器 localStorage，刷新可恢复；分类页支持手动输入任务编号。
- 遇到网络错误可重试查询；队列不可用、设计失败、任务不存在有不同提示。
- 结果表保留报告字段名称、单位与来源。Summary 显示核心参数；其他标签页显示报告对应分区。
- Waveforms 在报告缺少时域采样时只显示统计或未提供状态；不会从统计量构造波形。Efficiency 在报告确实含负载扫描点时绘制曲线。
- 当前后端完整运行默认关闭磁性设计，且未执行波形或效率扫描；这些空状态是后端能力边界。
- 当前下载为后端生成的 JSON 文件。PDF/CSV、独立磁性设计、运行点刷新、效率扫描、任务取消尚未提供 API，不在页面上模拟成功。
- 表单编辑后仍显示带任务编号的原结果，直到新的请求成功提交。结果中的 request 表格为计算时实际输入。

## 验证

```powershell
# 仓库根目录：真实 Buck 计算 + HTTP/数据库/下载契约
python -m pytest -q tests/test_web_schemas.py tests/test_web_api.py tests/test_web_persistence.py tests/test_web_frontend_contract.py

# 前端目录：类型、构建、浏览器流程
npm run build
npx playwright install chromium
npm test
```

浏览器测试使用拦截的任务 HTTP 响应，覆盖提交/轮询/恢复/错误/下载/窄屏。fixture 由真实 Buck 拓扑流水线生成，可在仓库根目录执行 `python -B scripts/export_web_test_fixtures.py` 更新。
后端集成测试使用临时 SQLite、临时输出目录；运行真实 Buck 同步计算，对照 fixture，并测试任务 Worker 函数与文件下载。它不等同于外部 PostgreSQL、Redis 和独立 Celery 进程的部署验收。

## 发布

`npm run build` 生成 `dist/`，仅包含前端资源。正式部署需反向代理将同源 `/api` 转发给 FastAPI；鉴权、配额、迁移修复和生产部署验收另行实施。不要将仓库根目录或 Python 文件目录作为静态文件根目录发布。

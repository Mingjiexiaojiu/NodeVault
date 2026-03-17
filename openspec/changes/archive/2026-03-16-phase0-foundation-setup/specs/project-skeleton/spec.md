## ADDED Requirements

### Requirement: FastAPI 项目目录结构
项目 SHALL 采用以下分层目录结构：`api/v1/`（路由）、`core/`（业务逻辑与配置）、`models/`（ORM 模型）、`schemas/`（Pydantic 模型）、`database/`（数据库连接与迁移）、`auth/`（认证）、`tests/`（测试）、`deploy/`（部署配置）。每个 Python 包目录 SHALL 包含 `__init__.py` 文件。

#### Scenario: 目录结构完整性
- **WHEN** 项目初始化完成后检查目录结构
- **THEN** 上述所有目录及其 `__init__.py` 文件 SHALL 存在

### Requirement: pyproject.toml 依赖管理
项目 SHALL 使用 `pyproject.toml` 管理元数据和依赖，`requires-python >= "3.11"`。核心依赖 SHALL 包含：fastapi、uvicorn、sqlalchemy（asyncio）、asyncpg、alembic、pydantic、pydantic-settings、python-jose、passlib、httpx、python-dotenv、structlog。开发依赖 SHALL 定义在 `[project.optional-dependencies] dev` 中，包含：pytest、pytest-asyncio、pytest-cov、ruff、mypy。

#### Scenario: 核心依赖可安装
- **WHEN** 执行 `pip install -e .`
- **THEN** 所有核心依赖 SHALL 被成功安装

#### Scenario: 开发依赖可安装
- **WHEN** 执行 `pip install -e ".[dev]"`
- **THEN** pytest、ruff、mypy 等开发工具 SHALL 可用

### Requirement: 应用入口文件
`main.py` SHALL 创建 FastAPI 应用实例，配置 CORS 中间件，挂载 API 路由前缀 `/api/v1`。

#### Scenario: 应用可启动
- **WHEN** 执行 `uvicorn main:app --port 8000`
- **THEN** 服务 SHALL 在 8000 端口启动且无报错

### Requirement: 健康检查端点
系统 SHALL 提供 `GET /healthz` 端点，返回 HTTP 200 及 JSON 格式的健康状态。

#### Scenario: 健康检查正常响应
- **WHEN** 发送 `GET /healthz` 请求
- **THEN** SHALL 返回 HTTP 200，响应体包含 `{"status": "ok"}`

### Requirement: 统一响应格式
所有 API 响应 SHALL 使用统一的 JSON 格式包装，成功时包含 `success: true, data, message, request_id`；失败时包含 `success: false, error: {code, message, details}, request_id`。

#### Scenario: 成功响应格式
- **WHEN** API 请求成功
- **THEN** 响应 SHALL 包含 `success` 为 `true`、`data` 字段承载业务数据、`request_id` 为 UUID

#### Scenario: 错误响应格式
- **WHEN** API 请求失败（如 404、422）
- **THEN** 响应 SHALL 包含 `success` 为 `false`、`error.code` 为业务错误码、`error.message` 为人类可读描述

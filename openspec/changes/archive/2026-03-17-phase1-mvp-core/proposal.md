## Why

Phase 0 建立了项目骨架和 Node Schema 标准，但系统目前无法真正运行——没有持久化存储、没有认证、没有 Node 的增删查改、也无法实际执行调用。Phase 1 的目标是打通「注册 → 查询 → 调用」这条核心链路，让 NodeVault 具备最小可用价值。

## What Changes

- **新增** User 认证系统：注册、登录、JWT 鉴权、当前用户信息
- **新增** ORM 模型：`Node`、`NodeVersion`、`NodeTag`、`NodeInvocationLog`、`User`、`Namespace`
- **新增** Alembic 初始迁移：建立全部数据库表
- **新增** Node Registry API：注册、查询、更新、软删除 Node，版本管理（CRUD）
- **新增** HTTP 执行器：`HTTPExecutor` + `RuntimeDispatcher`，支持 Bearer / API Key 认证
- **新增** Node 调用 API：`POST /api/v1/nodes/{id}/invoke`，记录调用日志
- **新增** 调用日志查询 API：`GET /api/v1/nodes/{id}/logs`
- **增强** Health Check：新增数据库连通性检测

## Capabilities

### New Capabilities

- `user-auth`: 用户注册/登录/JWT 签发与校验，`/api/v1/auth/*` 端点，密码 bcrypt 哈希，Bearer Token 鉴权中间件
- `node-registry`: Node 及 NodeVersion 的完整 CRUD，命名空间隔离，软删除，版本发布与默认版本管理
- `node-invocation`: HTTP 类型 Node 的实际执行，RuntimeDispatcher 分发，超时/错误处理，调用日志持久化与查询
- `database-models`: SQLAlchemy ORM 模型定义（User/Namespace/Node/NodeVersion/NodeTag/NodeInvocationLog）与 Alembic 初始迁移

### Modified Capabilities

- `database-foundation`: 新增 ORM 模型后需要对应 Alembic 迁移，`Base` 使用方式不变，但需要在迁移中 import 所有模型以确保 autogenerate 正常工作
- `node-schema-standard`: Phase 1 的 `NodeCreate` Pydantic schema 直接复用 Phase 0 中 `NodeSchemaBase` 的字段约束（name/version/runtime 校验规则），无需新增规则，仅需补充 API 层的请求/响应 schema

## Impact

- **新增文件**：`nodevault/models/` 目录（user.py、node.py）、`nodevault/auth/` 目录（jwt.py、deps.py）、`nodevault/core/registry.py`、`nodevault/core/runtime.py`、`nodevault/api/v1/auth.py`、`nodevault/api/v1/nodes.py`、`nodevault/api/v1/invoke.py`
- **修改文件**：`nodevault/api/v1/router.py`（注册新路由）、`nodevault/database/migrations/env.py`（import 模型）、`nodevault/api/v1/health.py`（增加 DB 检查）
- **新增依赖**：已在 pyproject.toml 中声明（`python-jose`、`passlib[bcrypt]`、`httpx`）
- **数据库**：需执行 Alembic 迁移建表，依赖远程 PostgreSQL（已在 .env 配置）

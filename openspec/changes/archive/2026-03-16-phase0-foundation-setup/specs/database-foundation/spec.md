## ADDED Requirements

### Requirement: PostgreSQL 异步数据库连接
系统 SHALL 使用 SQLAlchemy 2.0 async engine 连接 PostgreSQL，驱动为 asyncpg。数据库 URL SHALL 从环境变量 `DATABASE_URL` 读取，格式为 `postgresql+asyncpg://user:pass@host:port/dbname`。

#### Scenario: 数据库连接成功
- **WHEN** 提供有效的 DATABASE_URL 且 PostgreSQL 服务可用
- **THEN** 系统 SHALL 成功创建 async engine 和 async session factory

#### Scenario: 数据库连接失败
- **WHEN** PostgreSQL 服务不可用
- **THEN** 系统 SHALL 记录错误日志并在启动时抛出明确的连接错误

### Requirement: SQLAlchemy Async Session 管理
系统 SHALL 提供异步 session 工厂（`async_sessionmaker`），并通过 FastAPI 依赖注入（`Depends`）在每个请求中提供独立的数据库 session。Session SHALL 在请求结束后自动关闭。

#### Scenario: 请求级 session 隔离
- **WHEN** 两个并发 API 请求到达
- **THEN** 每个请求 SHALL 获得独立的数据库 session 实例

#### Scenario: session 自动清理
- **WHEN** 一个 API 请求处理完成（无论成功或异常）
- **THEN** 对应的数据库 session SHALL 被自动关闭

### Requirement: Alembic 迁移框架初始化
系统 SHALL 配置 Alembic 用于数据库 schema 迁移，`alembic.ini` 从环境变量读取数据库 URL，迁移脚本目录为 `database/migrations/`。

#### Scenario: Alembic 初始化配置
- **WHEN** 项目初始化完成
- **THEN** `alembic.ini` 和 `database/migrations/` 目录 SHALL 存在，`alembic revision --autogenerate` 可正常运行

#### Scenario: 迁移命令可执行
- **WHEN** 执行 `alembic upgrade head`
- **THEN** 数据库 schema SHALL 被更新到最新版本

### Requirement: 核心 ER 模型设计文档
Phase 0 SHALL 冻结以下核心表的设计：`users`、`namespaces`、`nodes`、`node_versions`、`node_tags`、`node_invocation_logs`、`workflows`、`workflow_versions`、`workflow_run_logs`。每张表的字段名、类型、约束 SHALL 在设计文档中明确定义。

#### Scenario: ER 模型覆盖所有核心实体
- **WHEN** 审查 ER 模型设计
- **THEN** SHALL 包含上述 9 张核心表的完整字段定义

### Requirement: 索引策略定义
设计 SHALL 为高频查询场景预定义索引，包括：`nodes(namespace_id)`、`nodes(status)`、`nodes(type)`、`node_tags(tag)`、`node_invocation_logs(node_id, created_at DESC)`，以及 JSONB 字段的 GIN 索引。

#### Scenario: 索引覆盖主要查询路径
- **WHEN** 审查索引策略
- **THEN** 针对 Node 按命名空间/状态/类型查询、标签查询、调用日志时间范围查询的索引 SHALL 被预定义

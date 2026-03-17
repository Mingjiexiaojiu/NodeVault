## Context

Phase 0 完成了项目骨架、Node Schema 标准和开发环境搭建，所有基础设施就位（FastAPI、SQLAlchemy async、Alembic、pydantic-settings）。当前系统只有一个 `/healthz` 端点，没有真实的业务逻辑。

Phase 1 需要在此基础上构建四个核心能力：**用户认证**、**ORM 数据模型**、**Node Registry CRUD**、**HTTP 执行器**。这四个能力存在明确的依赖顺序：数据模型是基础，认证系统依赖 User 模型，Registry API 依赖模型和认证，执行器依赖 Registry。

## Goals / Non-Goals

**Goals:**
- 用户可以注册/登录，获得 JWT Token
- 已认证用户可以注册、查询、更新、删除 Node 及版本
- HTTP 类型 Node 可以被实际调用，结果和日志持久化到 PostgreSQL
- 所有 API 都受 JWT 保护
- Alembic 迁移可以一条命令建好全部表

**Non-Goals:**
- gRPC / Docker / Python runtime 执行器（Phase 2+）
- MeiliSearch 全文搜索集成（Phase 2）
- 命名空间多租户完整权限控制（Phase 4）
- 前端 Web UI（Phase 1 仅提供 Swagger）
- 跨 Node 的 Workflow/DAG 编排（Phase 5）

## Decisions

### D1：User 模型存在于 Phase 1，Namespace 简化处理
**决策**：Phase 1 创建 `User` 模型和 `Namespace` 模型，但 Namespace 在注册时自动为每个用户创建一个「默认命名空间」，不暴露多命名空间管理 API。

**理由**：Node 表有 `namespace_id` 外键，完全跳过会导致数据模型残缺。但完整的多租户命名空间管理是 Phase 4 的工作，现在只做最小实现——用户注册时自动创建与用户名同名的 namespace，用于隔离其 Node。

**备选**：完全跳过 Namespace，直接用 `owner_id` 做隔离 → 会导致后续迁移成本高，不采用。

---

### D2：JWT 仅实现 Access Token，暂不实现 Refresh Token
**决策**：Phase 1 只实现 access token（30 分钟过期），`POST /api/v1/auth/refresh` 推迟到后续阶段。

**理由**：Refresh token 涉及 token 黑名单（需要 Redis）或 token rotation 机制，增加复杂度。Phase 1 的目标是核心链路跑通，30 分钟 token 对集成测试和开发调试已经足够。

**备选**：直接实现 refresh token 存入 Redis → 增加 Redis 依赖耦合，暂不做。

---

### D3：NodeRegistry 作为 Service 层，不直接在路由里写 ORM 查询
**决策**：创建 `nodevault/core/registry.py`，包含 `NodeRegistry` 类，所有数据库操作封装在此，路由层只调用 Service 方法。

**理由**：路由层直接写 SQLAlchemy 查询会导致测试困难、逻辑分散。Service 层可单独测试，也为后续添加缓存层（Redis）留出空间。

**备选**：Repository 模式（再抽一层 NodeRepository）→ 对当前规模过度设计，不采用。

---

### D4：HTTPExecutor 使用 httpx.AsyncClient，每次调用新建 client
**决策**：每次 `execute()` 调用都使用 `async with httpx.AsyncClient()` 上下文管理器，不做连接池复用。

**理由**：Phase 1 调用量小，不同 Node 的 endpoint 各异，连接池意义不大。连接池管理需要 lifespan 集成，增加复杂度。`httpx` 自身对单次请求已有合理的 TCP 复用。

**备选**：全局 AsyncClient 单例 → 需要处理连接泄漏和线程安全，推迟到 Phase 2 优化。

---

### D5：软删除而非物理删除
**决策**：`DELETE /api/v1/nodes/{id}` 将 Node 状态改为 `archived`，不删除数据库记录。

**理由**：调用日志引用了 Node，物理删除会破坏外键约束。归档的 Node 在查询时默认过滤掉，但保留历史数据。

---

### D6：调用日志在 finally 块中写入，保证记录成功和失败两种情况
**决策**：`invoke` 端点在 `try/finally` 中处理日志写入，无论调用成功还是失败都记录。

**理由**：失败的调用记录对排错和监控同等重要。如果只在成功时记录，日志数据会不完整。

## Risks / Trade-offs

- **[风险] 远程 PostgreSQL 连接稳定性** → 本地开发用 docker-compose.dev.yml，集成测试用 pytest fixtures mock DB 或 SQLite in-memory（仅单元测试）
- **[风险] bcrypt 哈希在测试中较慢** → 测试用 `passlib` 的 `rounds=4` 加速，通过 conftest 覆盖
- **[风险] Alembic autogenerate 遗漏模型** → 在 `migrations/env.py` 中显式 import 所有模型，确保 `target_metadata` 完整
- **[取舍] 无 Refresh Token** → 开发阶段每次测试重新登录，可接受；生产前需补齐

## Migration Plan

1. 在 `migrations/env.py` 中 import 所有新 ORM 模型
2. `alembic revision --autogenerate -m "phase1: users, namespaces, nodes, versions, tags, logs"`
3. `alembic upgrade head`（首次部署到远程 DB）
4. 回滚：`alembic downgrade -1`

## Open Questions

- 命名空间 slug 用 username 还是 UUID？→ **暂定用 username**，便于调试，后续可改
- 调用日志是否需要分页？→ **Phase 1 默认返回最近 50 条**，分页在 Phase 2 完善

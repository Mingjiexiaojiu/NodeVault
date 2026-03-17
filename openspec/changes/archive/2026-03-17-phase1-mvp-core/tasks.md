## 1. ORM 数据模型

- [x] 1.1 创建 `nodevault/models/__init__.py`，统一导出所有模型
- [x] 1.2 创建 `nodevault/models/user.py`：定义 `User` 模型（id/email/username/hashed_password/is_active/created_at/updated_at），email 和 username 加唯一索引
- [x] 1.3 创建 `nodevault/models/namespace.py`：定义 `Namespace` 模型（id/slug/owner_id/display_name/created_at），slug 加唯一索引，owner_id 外键指向 users.id
- [x] 1.4 创建 `nodevault/models/node.py`：定义 `Node`/`NodeVersion`/`NodeTag`/`NodeInvocationLog` 四个模型，含所有字段、索引和约束（参考 Phase 1 设计文档）
- [x] 1.5 更新 `nodevault/database/migrations/env.py`：在 `target_metadata` 前 import 所有模型模块（user/namespace/node），确保 autogenerate 完整

## 2. Alembic 数据库迁移

- [x] 2.1 执行 `alembic revision --autogenerate -m "phase1: users namespaces nodes versions tags logs"` 生成迁移脚本
- [x] 2.2 检查生成的迁移脚本，确认包含全部 6 张表的 create_table 以及索引和约束
- [x] 2.3 执行 `alembic upgrade head` 将迁移应用到远程 PostgreSQL

## 3. JWT 认证系统

- [x] 3.1 创建 `nodevault/auth/__init__.py`
- [x] 3.2 创建 `nodevault/auth/jwt.py`：实现 `verify_password`/`get_password_hash`/`create_access_token`/`decode_token` 函数（使用 passlib bcrypt + python-jose）
- [x] 3.3 创建 `nodevault/auth/deps.py`：实现 `get_current_user` FastAPI 依赖函数，从 Bearer Token 中解析并查询用户，未认证时抛出 401

## 4. 认证 API

- [x] 4.1 创建 `nodevault/schemas/auth.py`：定义 `UserRegister`/`UserLogin`/`TokenResponse`/`UserResponse` Pydantic 模型
- [x] 4.2 创建 `nodevault/api/v1/auth.py`：实现 `POST /api/v1/auth/register`（注册 + 自动创建默认 Namespace）、`POST /api/v1/auth/login`（登录返回 JWT）、`GET /api/v1/auth/me`（当前用户信息）
- [x] 4.3 在 `nodevault/api/v1/router.py` 中注册 auth 路由

## 5. Node Registry Service 层

- [x] 5.1 创建 `nodevault/schemas/node.py`：定义 `NodeCreate`/`NodeResponse`/`NodeDetailResponse`/`NodeVersionCreate`/`NodeVersionResponse`/`NodeUpdate` Pydantic 模型，`NodeCreate` 复用 `NodeSchemaBase` 的校验规则
- [x] 5.2 创建 `nodevault/core/registry.py`：实现 `NodeRegistry` 类，包含 `create_node`/`list_nodes`/`get_node`/`update_node`/`archive_node`/`list_versions`/`create_version`/`get_version`/`log_invocation` 方法

## 6. Node Registry API

- [x] 6.1 创建 `nodevault/api/v1/nodes.py`：实现 Node CRUD 端点（POST/GET /nodes，GET/PATCH/DELETE /nodes/{id}），所有端点需 JWT 认证
- [x] 6.2 创建 `nodevault/api/v1/versions.py` 或在 nodes.py 中追加：实现 `GET /nodes/{id}/versions` 和 `POST /nodes/{id}/versions` 端点
- [x] 6.3 在 `router.py` 中注册 nodes 路由

## 7. HTTP 执行器与调用 API

- [x] 7.1 创建 `nodevault/core/runtime.py`：实现 `HTTPExecutor.execute()` 方法（httpx async、超时处理、Bearer/API Key 认证、HTTPStatusError 捕获）和 `RuntimeDispatcher.get_executor()` 分发器
- [x] 7.2 创建 `nodevault/api/v1/invoke.py`：实现 `POST /api/v1/nodes/{node_id}/invoke` 端点，使用 try/finally 确保无论成功失败都写入调用日志
- [x] 7.3 创建 `nodevault/api/v1/logs.py`：实现 `GET /api/v1/nodes/{node_id}/logs` 端点，返回最近 50 条调用日志
- [x] 7.4 在 `router.py` 中注册 invoke 和 logs 路由

## 8. Health Check 增强

- [x] 8.1 更新 `nodevault/api/v1/health.py`：在 `/healthz` 中增加数据库连通性检测（`SELECT 1`），返回 `components.database` 状态字段

## 9. 测试

- [x] 9.1 创建 `nodevault/tests/test_auth.py`：测试注册（成功/邮箱重复/密码强度不足）、登录（成功/密码错误）、JWT 鉴权（有效/无 Token/过期 Token）
- [x] 9.2 创建 `nodevault/tests/test_nodes.py`：测试 Node CRUD（注册/查询/详情/更新/软删除/版本管理）
- [x] 9.3 创建 `nodevault/tests/test_invoke.py`：使用 `respx` mock 外部 HTTP 调用，测试成功调用、超时、目标服务错误、调用日志写入
- [x] 9.4 运行 `pytest --cov=nodevault --cov-report=term-missing`，确认测试覆盖率 ≥ 70%（实际 87%，56/56 通过）

## 10. 验证与收尾

- [x] 10.1 启动服务（`uvicorn nodevault.main:app --reload`），手动跑通「注册→登录→注册Node→查询Node→调用Node→查看日志」完整链路
- [x] 10.2 访问 `http://localhost:8000/docs` 确认 Swagger 文档完整，所有端点可见（14 个端点全部可见）
- [x] 10.3 在 `pyproject.toml` 中添加 `respx` 到 dev 依赖（用于 mock HTTP 调用测试）

## ADDED Requirements

### Requirement: 同步客户端初始化与认证
SDK 的 `NodeVaultClient` 类 SHALL 支持两种认证方式：`api_key`（直接使用 Bearer token）和 `email + password`（调用登录接口获取 token）。所有后续请求 SHALL 自动携带 `Authorization: Bearer <token>` 请求头。未认证时调用任何方法 SHALL 抛出 `AuthError`。

#### Scenario: 使用 email/password 初始化
- **WHEN** 传入有效的 `email` 和 `password` 创建 NodeVaultClient
- **THEN** 客户端 SHALL 自动调用登录接口获取 token，后续请求自动携带认证头

#### Scenario: 凭据无效时抛出 AuthError
- **WHEN** 传入错误的 email/password
- **THEN** 初始化 SHALL 抛出 `AuthError("Invalid credentials")`

#### Scenario: 使用 api_key 初始化
- **WHEN** 传入 `api_key` 字符串创建 NodeVaultClient
- **THEN** 客户端 SHALL 直接使用该 key 作为 Bearer token，不请求登录接口

---

### Requirement: Node 注册方法
`NodeVaultClient.register()` SHALL 封装 `POST /api/v1/nodes`，接受 `name`、`type`、`input_schema`、`output_schema`、`endpoint`、`description`、`tags`、`version` 参数，返回 `NodeResponse` 对象。

#### Scenario: 注册新 Node 成功
- **WHEN** 调用 `vault.register(name="my_node", type="analysis", ...)` 且 Node 不存在
- **THEN** 方法 SHALL 返回包含 id/name/status 的 `NodeResponse` 对象

#### Scenario: Node 已存在时抛出异常
- **WHEN** 注册同名 Node（服务端返回 409）
- **THEN** 方法 SHALL 抛出 `NodeVaultError` 包含错误描述

---

### Requirement: Node 查询与搜索方法
`NodeVaultClient` SHALL 提供：
- `get(node_name: str) -> NodeResponse`：按名称获取 Node，不存在时抛出 `NodeNotFoundError`
- `search(query: str, **filters) -> list[NodeResponse]`：调用搜索接口，支持 type/tags 等过滤参数
- `list_nodes(**filters) -> list[NodeResponse]`：列出 Node，支持过滤参数

#### Scenario: 按名称获取存在的 Node
- **WHEN** 调用 `vault.get("detect_fund_pool")`
- **THEN** 方法 SHALL 返回对应 `NodeResponse`

#### Scenario: 按名称获取不存在的 Node
- **WHEN** 调用 `vault.get("nonexistent_node")`
- **THEN** 方法 SHALL 抛出 `NodeNotFoundError`

#### Scenario: 关键词搜索返回列表
- **WHEN** 调用 `vault.search("资金分析", type="analysis")`
- **THEN** 方法 SHALL 返回匹配的 `NodeResponse` 列表（可为空列表）

---

### Requirement: Node 调用方法
`NodeVaultClient.invoke(node_name: str, input_data: dict, version: str | None)` SHALL 先调用 `get()` 获取 node_id，再调用 `POST /api/v1/nodes/{node_id}/invoke`，返回 `InvokeResponse`（含 output/latency_ms/invocation_id）。

#### Scenario: 成功调用 Node
- **WHEN** 调用 `vault.invoke("detect_fund_pool", {"transactions": [...]})`
- **THEN** 方法 SHALL 返回 `InvokeResponse`，`output` 字段包含目标服务响应

#### Scenario: 指定版本调用
- **WHEN** 调用时传入 `version="1.0.0"`
- **THEN** 请求体 SHALL 包含 `version` 字段

---

### Requirement: `@vault.node` 装饰器
`NodeVaultClient.node()` SHALL 提供装饰器，接受 `name`、`type`、`description`、`tags`、`endpoint`、`auto_register`（默认 True）参数。当 `auto_register=True` 时，装饰器 SHALL 从被装饰函数的 Python 类型注解自动推断 input/output schema 并注册 Node（Node 已存在时静默跳过）。

#### Scenario: 装饰器自动注册新 Node
- **WHEN** 使用 `@vault.node(name=..., type=..., endpoint=...)` 装饰一个带类型注解的函数
- **THEN** 导入该模块时 SHALL 自动调用 `register()` 完成 Node 注册

#### Scenario: Node 已存在时静默跳过
- **WHEN** 装饰器尝试注册一个已存在的 Node（服务端返回 409）
- **THEN** 装饰器 SHALL NOT 抛出异常，仅静默忽略

#### Scenario: 从类型注解生成 input schema
- **WHEN** 函数签名为 `def f(account_id: str, count: int) -> dict`
- **THEN** 推断的 input_schema SHALL 包含 `account_id`（type: string）和 `count`（type: integer），两者均在 required 列表中

#### Scenario: `auto_register=False` 时不触发注册
- **WHEN** 装饰器携带 `auto_register=False`
- **THEN** 模块导入时 SHALL NOT 调用任何注册接口

---

### Requirement: 异步客户端
SDK 的 `AsyncNodeVaultClient` 类 SHALL 提供异步版本的 `invoke()` 方法（`async def invoke(...)`），基于 `httpx.AsyncClient`，适用于 FastAPI / asyncio 场景。初始化通过 `api_key` 进行认证。

#### Scenario: 异步调用 Node
- **WHEN** 在 async 上下文中调用 `await async_client.invoke("my_node", {...})`
- **THEN** 方法 SHALL 返回 `InvokeResponse`，全程无阻塞操作

---

### Requirement: SDK 异常体系
SDK SHALL 定义以下异常类（均继承自 `NodeVaultError`）：
- `AuthError`：认证失败（401）
- `NodeNotFoundError`：Node 不存在（404）
- `NodeVaultError`：其他 API 错误（基类）

#### Scenario: 服务端 401 时抛出 AuthError
- **WHEN** API 请求返回 401 状态码
- **THEN** SDK SHALL 抛出 `AuthError`

#### Scenario: 服务端 404 时抛出 NodeNotFoundError
- **WHEN** API 请求返回 404 状态码
- **THEN** SDK SHALL 抛出 `NodeNotFoundError`

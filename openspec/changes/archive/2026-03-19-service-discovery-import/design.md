## Context

NodeVault 当前 Node 注册是单个手动填写模式。每个 Node 包含 name、input/output schema、runtime_config（含 endpoint、method、auth）。当一个目标服务有多个 API 时，需要逐一创建，且每个 Node 独立维护 auth 配置。

项目使用 FastAPI + SQLAlchemy async + PostgreSQL，前端 Vue 3 + TypeScript + Tailwind CSS。已有 Node CRUD、版本管理、invoke 引擎、API Key 认证（`nvk_` 前缀）等能力。

## Goals / Non-Goals

**Goals:**
- 用户输入一个服务 base URL，自动探测 OpenAPI Spec 并解析出全部接口
- 支持目标服务需要认证的场景（账号密码登录获取 token、静态 token、API Key、Basic Auth）
- 凭据加密存储，invoke 时自动获取/刷新目标服务的 token
- 从 OpenAPI operation 批量生成 Node，用户可勾选、自定义名称后一键导入
- 兜底支持手动指定 spec 路径和上传 spec 文件
- 安全防护：SSRF 防止探测内网敏感地址，凭据明文不回显

**Non-Goals:**
- gRPC reflection / GraphQL introspection 自动发现（后期扩展）
- SDK 主动注册模式（服务启动时推送 spec 到 NodeVault）
- 凭据的外部密钥管理服务集成（HashiCorp Vault / AWS KMS，后期升级路径）
- Spec 变更 diff 对比（再次探测同一地址时高亮新增/变更/删除接口——v2）

## Decisions

### 1. 加密方案：应用层 AES-256-GCM

**选择**：使用 Python `cryptography` 库的 AES-256-GCM，密钥通过环境变量 `CREDENTIAL_ENCRYPT_KEY` 注入。

**替代方案**：
- HashiCorp Vault / AWS KMS：更安全但引入外部依赖，内部部署场景不需要
- 不加密直接存明文：安全性不可接受

**理由**：AES-256-GCM 提供认证加密（防篡改），`cryptography` 是 Python 加密标准库，无额外运维成本。密钥由部署环境管理，代码中不硬编码。

### 2. 凭据与 Node 的关系：独立实体 + credential_id 引用

**选择**：`service_credentials` 是独立表，Node 的 `runtime_config` 中通过 `credential_id` 引用。

**替代方案**：
- 每个 Node 内嵌 auth 配置：现状，冗余且更新麻烦
- 抽象 Service 模型包含 Nodes：改动太大，不符合 Node 独立性设计

**理由**：同一服务的多个 Node 共享一套凭据，更新凭据只需改一处。credential 独立于 Node 生命周期——删 Node 不影响 credential，删 credential 时清除关联 Node 的 credential_id。

### 3. 探测策略：有序尝试内置路径列表

**选择**：维护一个有序的探测路径列表（内置 + 用户可扩展），按优先级逐一 GET 请求，首个返回 200 且内容合法的即为 spec。

**替代方案**：
- 只支持 `/openapi.json`：覆盖率太低
- 爬虫式全站扫描：复杂且侵入性强

**路径列表（内置默认）**：
```
/openapi.json, /swagger.json, /openapi.yaml,
/v3/api-docs, /v2/api-docs, /api/schema/,
/swagger/v1/swagger.json, /swagger/doc.json,
/api-docs, /docs/openapi.json
```

### 4. Token 缓存：数据库表 + 内存 TTL

**选择**：`credential_token_cache` 表存储 token 和过期时间，invoke 引擎先查缓存，过期则用凭据重新登录。

**替代方案**：
- 纯 Redis 缓存：引入额外依赖
- 纯内存缓存：多进程/重启后丢失

**理由**：数据库已有，无额外依赖。Token 不是高频变更数据，数据库读写性能足够。提前 60 秒刷新避免边界竞态。

### 5. OpenAPI → Node 映射规则

| OpenAPI 字段 | Node 字段 |
|---|---|
| `operationId` 或 `method_path` | 用户自定义名称（前端提供建议值） |
| `summary` | `display_name` |
| `description` | `description` |
| `requestBody.content.application/json.schema` | `input_schema` |
| `responses.200.content.application/json.schema` | `output_schema` |
| `servers[0].url` + path | `runtime_config.endpoint`（存相对路径） |
| HTTP method | `runtime_config.method` |
| `tags[0]` | `category` |
| `tags` | `tags` |

**噪音过滤**：默认取消勾选匹配以下模式的路径：
```
/health*, /ready*, /metrics, /prometheus,
/favicon.ico, /openapi.json, /swagger*, /docs, /redoc
```

### 6. SSRF 防护

**选择**：后端探测请求前校验目标 URL，拒绝以下地址段：
- `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- `169.254.0.0/16`（云元数据）
- `fd00::/8`（IPv6 私有）

**可配置**：管理员可通过环境变量 `ALLOWED_PRIVATE_CIDRS` 白名单放行特定内网地址段（适用于 NodeVault 部署在内网的场景）。

### 7. 认证流程：先无认证探测，401 时引导配置

**流程**：
1. 无 header 探测 spec 路径
2. 如果有 spec 返回 200 → 直接解析
3. 如果所有路径返回 401/403 → 引导用户配置认证
4. 如果全部 404 → 兜底选项（手动 spec 路径 / 上传文件 / 退回手动注册）

**Token 提取智能猜测**：登录响应后递归搜索 JSON 中以 `eyJ` 开头的字符串值，或 key 名含 `token`/`jwt`/`access` 的字段，多候选时让用户确认。

## Risks / Trade-offs

- **[SSRF]** NodeVault 后端代理用户请求探测外部 URL → 严格 IP 校验 + 白名单机制 + User-Agent 标识 `NodeVault/1.0 ServiceProbe`
- **[凭据泄露]** 数据库被攻破可能泄露密文 → AES-256-GCM 加密，密钥在环境变量中而非 DB；定期轮转密钥（后期支持）
- **[Token 竞态]** 多个并发 invoke 同时发现 token 过期 → 第一个获取锁并刷新，其余等待；或允许少量重复登录（MVP 可接受）
- **[OpenAPI 兼容性]** 不同框架生成的 OpenAPI spec 格式不完全一致 → 使用 `openapi-spec-validator` 或手写宽松解析，对 Swagger 2.x 做 upconvert
- **[密码存储风险]** MVP 阶段只缓存 Token 不存密码；后期引入加密凭据存储时需加密密钥管理
- **[探测超时]** 目标服务不可达时阻塞 → 每个探测路径设 5 秒超时，总体 30 秒上限

## Migration Plan

1. 新增 `service_credentials` 和 `credential_token_cache` 表（Alembic 迁移）
2. 新增后端 API 模块 `backend/api/v1/discovery.py` 和 `backend/api/v1/credentials.py`
3. 新增 `backend/core/probe.py`（探测引擎）和 `backend/core/credential_vault.py`（加密/解密）
4. 修改 `backend/core/runtime.py` 适配 `credential_id` 路径
5. 新增前端页面和路由
6. **向后兼容**：现有无 `credential_id` 的 Node 完全不受影响，invoke 逻辑走原有 auth 路径
7. **回滚**：删除新增的表和 API 端点即可，不影响已有数据

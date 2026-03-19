## Why

当前注册 Node 需要用户逐个手动填写名称、input/output schema、runtime 配置等完整信息。当一个服务有多个接口时（如翻译服务包含翻译、语种检测、批量翻译等），重复劳动严重。同时，目标服务的认证信息需要在每个 Node 的 runtime_config 里单独维护，缺乏统一管理。

本变更引入"服务发现 + 批量导入"能力：用户只需输入一个服务地址，NodeVault 自动探测 OpenAPI Spec、解析接口列表，经用户确认后批量创建 Node。同时引入凭据保险箱，统一管理目标服务的认证信息，invoke 时自动获取/刷新 token。

## What Changes

- **新增 OpenAPI 探测引擎**：给定 base URL，自动尝试常见 spec 路径（`/openapi.json`、`/v3/api-docs`、`/swagger.json` 等），找到并解析 OpenAPI 2.x/3.x 文档
- **新增凭据保险箱**：AES-256-GCM 加密存储目标服务的认证凭据（账号密码、静态 token、API Key），支持 bearer_login / bearer_static / basic / api_key 四种认证方式
- **新增 Token 缓存与自动刷新**：invoke 时检查 token 有效期，过期自动用保险箱中的凭据重新登录获取
- **新增批量导入 API**：将 OpenAPI paths 中的 operation 映射为 Node 草稿，用户预览勾选、自定义名称后批量创建
- **新增 Spec 文件上传**：支持直接上传 `.json`/`.yaml` 格式的 OpenAPI 文件作为兜底
- **修改 Node runtime_config**：新增 `credential_id` 字段，endpoint 改为相对路径，base_url 由凭据记录提供
- **新增探测路径管理**：内置默认路径列表，支持全局扩展（用户手动填的成功路径可加入探测库）
- **新增前端服务发现页面**：输入地址 → 探测进度 → 认证配置 → 接口预览 → 勾选命名 → 批量导入

## Capabilities

### New Capabilities
- `service-probe`: OpenAPI Spec 自动探测引擎——给定 URL 尝试常见 spec 路径，解析 OpenAPI 2.x/3.x 文档，提取接口列表，过滤噪音端点
- `credential-vault`: 凭据保险箱——加密存储目标服务认证信息，支持四种认证方式（bearer_login/bearer_static/basic/api_key），token 缓存与自动刷新
- `batch-import`: 批量导入——OpenAPI operation → Node 草稿映射、用户预览勾选、自定义名称、批量创建 Node，支持上传 spec 文件
- `frontend-service-discovery`: 前端服务发现与导入界面——探测流程可视化、认证配置弹窗、接口预览表、批量导入操作

### Modified Capabilities
- `node-invocation`: invoke 时新增 credential_id 关联，支持自动从凭据保险箱获取/刷新 token 后请求目标服务
- `node-registry`: Node 的 runtime_config 新增 credential_id 字段，endpoint 支持相对路径（配合凭据的 base_url 拼接）

## Impact

- **数据库**：新增 `service_credentials` 和 `credential_token_cache` 两张表，Node 模型变更（runtime_config 新增字段）
- **后端 API**：新增 `/api/v1/discovery/probe`、`/api/v1/discovery/import`、`/api/v1/credentials` CRUD 端点
- **依赖**：需要引入 `cryptography` 库（AES-256-GCM 加密）、`pyyaml`（解析 YAML 格式 spec）、`httpx`（异步 HTTP 探测）
- **安全**：新增 `CREDENTIAL_ENCRYPT_KEY` 环境变量；SSRF 防护（禁止探测私有 IP 段）；凭据明文不回显
- **前端**：新增服务发现页面路由和组件
- **现有功能**：invoke 逻辑需适配 credential_id 路径，现有无 credential_id 的 Node 不受影响（向后兼容）

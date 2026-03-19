## 1. 数据库与模型

- [x] 1.1 创建 `ServiceCredential` 模型（`backend/models/credential.py`）：id, owner_id, name, base_url, auth_type, login_endpoint, login_method, login_body_template, credential_encrypted, credential_nonce, token_json_path, token_ttl, static_token_encrypted, static_token_nonce, api_key_header, api_key_encrypted, api_key_nonce, created_at, updated_at
- [x] 1.2 创建 `CredentialTokenCache` 模型（`backend/models/credential.py`）：id, credential_id(FK), access_token, expires_at, created_at
- [x] 1.3 更新 `backend/models/__init__.py` 导出新模型
- [x] 1.4 创建 Alembic 迁移：`service_credentials` 表和 `credential_token_cache` 表
- [x] 1.5 运行迁移并验证表结构

## 2. 加密引擎

- [x] 2.1 创建 `backend/core/credential_vault.py`：`encrypt_value(plaintext) -> (ciphertext, nonce)` 和 `decrypt_value(ciphertext, nonce) -> plaintext`，使用 AES-256-GCM
- [x] 2.2 在 `backend/core/config.py` 中添加 `CREDENTIAL_ENCRYPT_KEY` 配置项，启动时校验格式（64字符 hex 或 44字符 base64，解码后 32 字节）
- [x] 2.3 编写加密/解密单元测试

## 3. 凭据管理 API

- [x] 3.1 创建 `backend/schemas/credential.py`：`CredentialCreate`、`CredentialResponse`、`CredentialDetail` Pydantic schemas
- [x] 3.2 创建 `backend/api/v1/credentials.py`：`POST /api/v1/credentials`（创建凭据，加密存储）
- [x] 3.3 `GET /api/v1/credentials`（列表，脱敏返回）
- [x] 3.4 `GET /api/v1/credentials/{id}`（详情，脱敏返回）
- [x] 3.5 `DELETE /api/v1/credentials/{id}`（删除凭据，关联 Node 的 credential_id 置 null）
- [x] 3.6 在 `backend/main.py` 注册 credentials 路由
- [x] 3.7 编写凭据 CRUD 测试

## 4. SSRF 防护

- [x] 4.1 创建 `backend/core/url_validator.py`：校验 URL 目标地址是否在私有 IP 段，支持 `ALLOWED_PRIVATE_CIDRS` 环境变量白名单
- [x] 4.2 编写 SSRF 防护单元测试（私有 IP 拒绝、白名单放行、公网地址放行）

## 5. OpenAPI 探测引擎

- [x] 5.1 创建 `backend/core/probe.py`：`probe_spec(base_url, auth_token=None) -> ProbeResult`，有序尝试内置路径列表
- [x] 5.2 实现探测超时控制：单路径 5 秒，总计 30 秒
- [x] 5.3 实现 User-Agent 标记 `NodeVault/1.0 ServiceProbe`
- [x] 5.4 集成 SSRF 校验（调用 url_validator）
- [x] 5.5 实现认证探测：接受 login_endpoint + username + password，POST 登录，智能提取 token，带 token 重试
- [x] 5.6 实现 OpenAPI 2.x / 3.x 解析（JSON + YAML），提取 paths 中的 operations
- [x] 5.7 编写探测引擎测试（mock HTTP 响应）

## 6. OpenAPI → Node 草稿映射

- [x] 6.1 创建 `backend/core/openapi_mapper.py`：`parse_operations(spec_dict) -> list[NodeDraft]`
- [x] 6.2 实现 operation → NodeDraft 映射：operationId → suggested name, requestBody → input_schema, response → output_schema, path → endpoint, method, tags → category
- [x] 6.3 实现噪音端点过滤逻辑（health/metrics/docs 默认 `selected=False`）
- [x] 6.4 编写映射测试（Swagger 2.x + OpenAPI 3.x 样本）

## 7. 服务发现与批量导入 API

- [x] 7.1 创建 `backend/schemas/discovery.py`：`ProbeRequest`、`ProbeResult`、`ProbeAuthConfig`、`NodeDraft`、`BatchImportRequest`、`BatchImportResponse` schemas
- [x] 7.2 创建 `backend/api/v1/discovery.py`：`POST /api/v1/discovery/probe`（探测 spec）
- [x] 7.3 `POST /api/v1/discovery/probe-with-auth`（带认证探测）
- [x] 7.4 `POST /api/v1/discovery/upload-spec`（上传 spec 文件解析）
- [x] 7.5 `POST /api/v1/discovery/import`（批量创建 Nodes，事务内完成）
- [x] 7.6 在 `backend/main.py` 注册 discovery 路由
- [x] 7.7 编写发现与导入 API 测试

## 8. Node 批量创建端点

- [x] 8.1 在 `backend/api/v1/nodes.py` 添加 `POST /api/v1/nodes/batch`（接受 Node 数组，原子事务）
- [x] 8.2 在 `backend/core/registry.py` 添加 `batch_register()` 方法
- [x] 8.3 处理 name 冲突检测（批量查询 namespace 内已有名称）
- [x] 8.4 编写批量创建测试（成功、冲突回滚）

## 9. Invoke 适配 credential_id

- [x] 9.1 修改 `backend/core/runtime.py`：在 HTTP 分发前检查 `credential_id`，若存在则获取/刷新 token
- [x] 9.2 实现 URL 拼接逻辑：credential.base_url + node.endpoint
- [x] 9.3 实现 token 缓存读取 → 过期刷新 → 401 强制重试流程
- [x] 9.4 确保无 credential_id 的 Node 走原有 auth 路径（向后兼容测试）
- [x] 9.5 编写 invoke + credential 集成测试

## 10. 前端：API 层

- [x] 10.1 创建 `frontend/src/api/discovery.ts`：`probeSpec()`、`probeWithAuth()`、`uploadSpec()`、`batchImport()` 函数和类型定义
- [x] 10.2 创建 `frontend/src/api/credentials.ts`：`createCredential()`、`listCredentials()`、`deleteCredential()` 函数和类型定义

## 11. 前端：服务发现页面

- [x] 11.1 创建 `frontend/src/views/ServiceDiscoveryView.vue`：地址输入 + 探测按钮
- [x] 11.2 实现探测进度可视化（逐行显示路径尝试结果）
- [x] 11.3 实现认证配置弹窗（auth type 选择 + 对应表单字段）
- [x] 11.4 实现 spec 文件上传区域（拖拽 + 点选，支持 .json/.yaml/.yml）
- [x] 11.5 实现接口预览表（checkbox + method + path + 名称编辑输入 + description）
- [x] 11.6 实现噪音接口默认取消勾选
- [x] 11.7 实现公共字段配置（category 下拉、tags 输入、visibility 选择）
- [x] 11.8 实现"导入选中"按钮 + 导入结果展示
- [x] 11.9 实现探测失败兜底 UI（手动路径 / 上传文件 / 退回手动注册）

## 12. 前端：路由与导航

- [x] 12.1 在 `frontend/src/router/index.ts` 添加 `/discover` 路由
- [x] 12.2 在 `AppLayout.vue` 导航栏添加"服务发现"菜单项
- [x] 12.3 在 NodeCreateView 或 Dashboard 适当位置添加"从服务导入"入口链接

## 13. 前端：凭据管理

- [x] 13.1 在服务发现页面中集成凭据选择（已有凭据复用 / 新建凭据）
- [x] 13.2 可选：在 ProfileView 或独立页面添加凭据列表管理（查看 / 删除）

## 14. 依赖与配置

- [x] 14.1 在 `pyproject.toml` 添加 `cryptography`、`pyyaml`（如未有）、`httpx`（如未有）依赖
- [x] 14.2 在 `.env.example` 添加 `CREDENTIAL_ENCRYPT_KEY` 示例
- [x] 14.3 在 `backend/core/config.py` 添加 `CREDENTIAL_ENCRYPT_KEY` 和 `ALLOWED_PRIVATE_CIDRS` 配置项

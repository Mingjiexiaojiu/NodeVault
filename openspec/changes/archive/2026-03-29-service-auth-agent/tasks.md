## 1. 后端 API 补全

- [x] 1.1 修复 `DELETE /credentials/{id}` bug：用 `db.delete()` 替换无效的 `select()` 来删除 token_cache 记录
- [x] 1.2 新增 `PATCH /credentials/{id}` 端点：支持更新 name、token_ttl 及重新加密密码/token/api_key；更新加密字段时清空 token_cache
- [x] 1.3 新增 `POST /credentials/{id}/test` 端点：验证凭据可用性，返回 `{success, message, latency_ms}`，不写入 token_cache
- [x] 1.4 在 `CredentialCreate` Pydantic Schema 中补充缺失字段（如需要）；新增 `CredentialUpdate` Schema 用于 PATCH
- [x] 1.5 在 `credentials.py` API 响应 Schema 中添加 `test` 相关的响应类型

## 2. Node 凭据绑定（后端）

- [x] 2.1 在 `NodeCreate` Schema 中添加可选 `credential_id: UUID | None` 字段
- [x] 2.2 在 `NodeUpdate` Schema 中添加可选 `credential_id: UUID | None` 字段（null 表示解绑）
- [x] 2.3 修改 `NodeRegistry.create_node()`：将 `credential_id` 写入 NodeVersion.runtime_config
- [x] 2.4 修改 `NodeRegistry.update_node()`：当 payload 包含 `credential_id` 时，更新默认版本的 runtime_config
- [x] 2.5 修改 `NodeResponse`：从默认版本 runtime_config 中读取并暴露 `credential_id` 字段

## 3. 凭据自动匹配（后端）

- [x] 3.1 在 `HTTPExecutor.execute()` 签名中添加可选 `owner_id: UUID | None = None` 参数
- [x] 3.2 实现 `HTTPExecutor._auto_match_credential(db, owner_id, endpoint)` — 按最长前缀匹配 ServiceCredential
- [x] 3.3 在 `execute()` 中添加调用逻辑：无显式 credential_id 且有 owner_id 时触发自动匹配
- [x] 3.4 修改 `invocation.py` 中 `invoke_node_by_name()` 调用 `executor.execute()` 时传入 `owner_id=user.id`
- [x] 3.5 确认自动匹配 credential_id 不写入 NodeInvocationLog

## 4. 前端 API Client 更新

- [x] 4.1 在 `frontend/src/api/credentials.ts` 中添加 `updateCredential(id, payload)` 函数（PATCH）
- [x] 4.2 在 `frontend/src/api/credentials.ts` 中添加 `testCredential(id)` 函数（POST test）
- [x] 4.3 更新 `CredentialCreate` / `CredentialResponse` TypeScript 类型（如有字段变化）
- [x] 4.4 在 `frontend/src/api/nodes.ts` 中更新 `NodeCreate` / `NodeUpdate` 类型，添加 `credential_id` 字段

## 5. 前端凭据管理页面

- [x] 5.1 新建 `frontend/src/views/CredentialListView.vue`：展示凭据列表（表格或卡片），空状态引导，测试/编辑/删除操作
- [x] 5.2 新建凭据创建/编辑抽屉组件（或内嵌到 CredentialListView）：支持 4 种 auth_type 动态字段切换，密码字段隐藏
- [x] 5.3 实现"测试连接"按钮逻辑：调用 `testCredential(id)`，显示 loading → 成功/失败状态
- [x] 5.4 实现删除凭据确认对话框：提示影响范围，确认后调用 `deleteCredential(id)` 并刷新列表
- [x] 5.5 在 `frontend/src/router/index.ts` 中注册 `/credentials` 路由，指向 `CredentialListView`
- [x] 5.6 在侧边栏导航（`AppLayout.vue` 或对应导航组件）中添加"凭据管理"菜单项及图标

## 6. 前端 Node 凭据绑定

- [x] 6.1 在 `NodeCreateView.vue` 的表单中添加"绑定凭据"选择器：下拉菜单列出 `GET /credentials` 的凭据，可选（留空则不绑定）
- [x] 6.2 在 `NodeEditView.vue` 中添加相同的凭据绑定选择器，初始值从 `node.credential_id` 读取，支持设为 null（解绑）
- [x] 6.3 在 `NodeDetailView.vue` 中展示当前绑定的凭据名称（从 `credential_id` + `listCredentials` 查找），无绑定时显示"无（将使用自动匹配）"

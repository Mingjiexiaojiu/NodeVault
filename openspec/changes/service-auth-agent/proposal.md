## Why

NodeVault 已具备完整的 Auth Agent 后端基础设施（ServiceCredential 模型、AES-256-GCM 加密、HTTPExecutor 自动 Token 刷新与 401 重试），但这套能力目前缺乏前端管理界面，且手动创建的 Node 无法绑定凭据——用户无法通过 UI 配置服务鉴权，实际上无法感知和使用这套机制。

## What Changes

- **新增** 凭据管理前端页面（列表、创建表单、测试连接、删除）
- **新增** 手动创建/编辑 Node 时可绑定或解绑凭据
- **新增** `PATCH /credentials/{id}` — 更新凭据（密码变更等）
- **新增** `POST /credentials/{id}/test` — 验证凭据是否可以成功登录
- **新增** 凭据 base_url 前缀自动匹配：runtime_config 无显式 credential_id 时，系统自动查找 owner 名下 base_url 匹配的凭据
- **修复** `DELETE /credentials/{id}` 中 token_cache 未真正删除的 bug

## Capabilities

### New Capabilities

- `frontend-credential-management`: 凭据管理前端 UI — 凭据列表页、创建表单（支持全部 auth_type）、测试连接按钮、删除，以及侧边栏导航入口
- `credential-auto-match`: 调用 Node 时，若 runtime_config 未设置 credential_id，系统自动按 endpoint base_url 前缀匹配 owner 名下的 ServiceCredential，实现零配置鉴权

### Modified Capabilities

- `credential-vault`: 补充 PATCH 更新接口、POST test 接口，修复 DELETE 的 token_cache 清理 bug
- `node-registry`: Node 创建（POST /nodes）和编辑（PATCH /nodes/{id}）支持传入 `credential_id`，绑定到 NodeVersion.runtime_config

## Impact

- **后端**: `backend/api/v1/credentials.py`（新增 PATCH/test 端点，修复 DELETE），`backend/core/runtime.py`（auto-match 逻辑），`backend/api/v1/nodes.py` + `backend/core/registry.py`（NodeCreate/NodeUpdate 支持 credential_id）
- **前端**: 新增 `CredentialListView.vue`、`CredentialCreateView.vue`（或抽屉组件），更新 `NodeCreateView.vue`、`NodeEditView.vue` 增加凭据绑定选择器，更新路由与侧边栏
- **数据库**: 无新表，NodeVersion.runtime_config（JSON 字段）已支持 credential_id，无 schema 迁移
- **依赖**: 无新依赖

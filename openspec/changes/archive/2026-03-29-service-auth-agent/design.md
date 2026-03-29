## Context

NodeVault 的后端已经完整实现了 Auth Agent 核心能力：
- `ServiceCredential` 模型（4 种 auth_type，AES-256-GCM 加密存储）
- `CredentialTokenCache` 模型（Token 缓存 + 过期跟踪）
- `HTTPExecutor`（401 感知 → 强制刷新 → 重试，最多一次）
- `POST/GET/DELETE /credentials` API 及前端 `credentials.ts` API client

缺失的是：前端 UI、手动 Node 绑定、更新/测试接口、自动匹配以及一个 bug 修复。本 Change 不引入新的技术依赖，属于"把已有基础设施暴露给用户"的完善性工作。

## Goals / Non-Goals

**Goals:**
- 用户可以通过前端 UI 完整管理凭据（增删查改+测试）
- 手动创建或编辑 Node 时可以绑定一个凭据
- 无显式绑定时，系统按 base_url 前缀自动匹配，减少重复配置
- 修复 DELETE 接口的 token_cache 清理 bug

**Non-Goals:**
- 凭据共享/权限（不同用户互相访问他人凭据）
- OAuth 2.0 Authorization Code / PKCE 流程（仅支持 client_credentials 等无交互流）
- SDK 层的 Auth Agent（本次只做后端代理层 Layer B）

## Decisions

### D1：前端凭据管理入口位置

选择在**侧边栏独立页面**（`/credentials`），而非嵌入到服务发现或 Profile 页面。

理由：凭据是全局配置，与多个 Node 关联；放在发现流程中会让非发现场景的用户找不到。Profile 页面已有 API Keys，增加凭据会显得混乱。独立页面职责清晰。

### D2：Node 绑定凭据的粒度

选择**在 NodeVersion.runtime_config 中存储 credential_id**（现有实现方式），而非在 Node 表上增加独立字段。

理由：Node 可以有多个版本，不同版本可能需要不同的目标服务鉴权配置；版本级绑定更灵活。现有代码已按此方式实现，无需迁移。

前端创建/编辑 Node 时，`credential_id` 通过 `NodeCreate.runtime.credential_id` 传递，`registry.py` 写入 `NodeVersion.runtime_config`。

### D3：base_url 自动匹配逻辑位置

在 `HTTPExecutor.execute()` 的最开始加入自动匹配：

```
if not credential_id and db:
    credential = await self._auto_match_credential(db, owner_id, endpoint)
```

`_auto_match_credential` 按 endpoint 前缀搜索 `service_credentials`：
```sql
SELECT * FROM service_credentials
WHERE owner_id = :owner_id
  AND :endpoint LIKE base_url || '%'
ORDER BY LENGTH(base_url) DESC  -- 最长前缀优先
LIMIT 1
```

需要将 `owner_id` 传入 `execute()`，来自 invocation 调用者的 User。

### D4：凭据测试接口实现

`POST /credentials/{id}/test` 直接触发一次 `_get_bearer_login_token(force_refresh=True)` 或相应的静态验证，返回 `{success: bool, message: str}`。不缓存测试结果（不写 token_cache）。

对于 `bearer_static` / `api_key` / `basic`：测试时发一个 `HEAD` 或 `GET` 请求到 `credential.base_url` 并附上 auth header，检查是否非 401。

### D5：PATCH 更新凭据

仅允许更新可变字段：`name`、`token_ttl`、以及覆盖加密字段（更新密码/token/api_key 时重新加密）。不允许修改 `auth_type` 和 `base_url`（需删除重建，避免缓存污染）。更新加密字段后自动清空对应 token_cache。

## Risks / Trade-offs

- **[风险] auto_match 误匹配** → base_url 取最长前缀匹配，前缀越长精确度越高。用户可以通过显式绑定 credential_id 覆盖自动匹配。
- **[风险] owner_id 传入 execute()** → HTTPExecutor 目前不感知用户，需要改动 invocation 调用链传入 user.id。影响面：`invocation.py`、`runtime.py`；若调用方不传则 fallback 到无自动匹配（向后兼容）。
- **[权衡] PATCH 不允许改 auth_type** → 简化了加密字段的迁移复杂度，代价是用户改变鉴权类型时需删除重建，可接受。
- **[风险] test 接口对 basic/api_key 的误判** → HEAD 请求可能被服务拦截或返回 405，不一定准确。返回信息应注明"测试结果仅供参考"。

## Migration Plan

1. 无数据库 schema 变更（runtime_config 是 JSON，credential_id 已在其中）
2. auto_match 需要在 `HTTPExecutor.execute()` 签名中新增可选的 `owner_id` 参数，默认 None（不破坏现有调用）
3. 前端新增路由和页面，不影响已有页面
4. Bug 修复（DELETE token_cache）直接上线，无副作用

## Open Questions

- 自动匹配是否需要在 NodeVersion 创建时就解析并写入 credential_id（预解析），还是每次 invoke 时动态查询？当前设计是动态查询（更灵活，凭据更新立即生效，轻微性能开销可接受）。

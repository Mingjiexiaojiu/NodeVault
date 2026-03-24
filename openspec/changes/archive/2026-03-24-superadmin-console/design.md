## Context

NodeVault 已有三级角色（0=超级管理员/1=主管/2=普通用户），但目前后端无任何 `role=0` 专属守卫，所有接口均对任意已认证用户开放或受 namespace 隔离。前端无管理入口。超管账号实际上与普通用户权限相同，无法完成平台运营所需的用户管控、全局资源审查、系统配置等操作。

**约束**：
- PostgreSQL + SQLAlchemy AsyncSession，ORM 模式
- FastAPI 依赖注入体系（deps.py 模式）
- Vue 3 + Pinia + Vue Router，前端已有 `useAuthStore` 管理登录态
- 不引入新的外部依赖

## Goals / Non-Goals

**Goals:**
- 建立后端超管权限守卫，所有 `/admin/` 路由只有 role=0 可访问
- 提供用户管理 CRUD API（含封禁/角色变更）
- 提供全局节点/技能/命名空间列表 API（跨 namespace）
- 提供平台统计聚合 API
- 提供系统配置 KV 存储 API（读写）
- 前端独立 AdminLayout 与 `/admin/*` 路由，路由级守卫阻止非超管访问
- 5 个管理页面：用户管理、全局资源、分类管理、平台统计、系统设置

**Non-Goals:**
- 细粒度 RBAC/权限矩阵（当前只区分超管 vs 非超管）
- 审计日志持久化到独立表（本期不做）
- role=1 主管的专属功能（本期 role=1 与 role=2 权限相同）
- 多超管之间的操作隔离

## Decisions

### 决策 1：独立 `/admin/` 路由前缀 vs 现有 API 扩展

**选择**：新建 `backend/api/v1/admin.py`，注册在 `/admin/` 前缀下。

**理由**：
- 边界清晰，权限守卫统一在路由层而非业务逻辑层
- 不污染现有接口，普通用户不会意外触碰管理端点
- 便于日后添加审计中间件只覆盖 `/admin/` 路径

**放弃的方案**：在现有 nodes/users API 加 `?admin=true` 参数——守卫分散，维护成本高。

---

### 决策 2：权限守卫实现方式

**选择**：在 `backend/auth/deps.py` 新增 `get_superadmin_user` 依赖函数：

```python
async def get_superadmin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != 0:
        raise HTTPException(status_code=403, detail="Superadmin required")
    return current_user
```

**理由**：复用现有认证链，只在上层加角色校验，零重复代码。

---

### 决策 3：系统设置存储方案

**选择**：使用数据库新表 `system_settings (key VARCHAR PK, value TEXT, updated_at)`，通过 Alembic migration 创建。

**理由**：
- 设置需持久化且跨进程共享（多 worker 场景）
- 比环境变量更灵活，可运行时修改无需重启
- 比 Redis 少一个外部依赖

**放弃的方案**：JSON 文件存储——Docker 容器重启后丢失。

---

### 决策 4：前端管理区布局隔离

**选择**：新建 `AdminLayout.vue`，`/admin` 路由使用该 layout，与主应用的 `MainLayout` 完全独立。

```
router:
  /admin          → AdminLayout
    /admin/users  → UserManageView
    /admin/nodes  → GlobalNodesView
    ...
  /               → MainLayout（不变）
```

**路由守卫**：在 `router/index.ts` 的 `beforeEach` 中，检测到 `/admin` 前缀时验证 `authStore.user.role === 0`，否则重定向 `/`。

**理由**：与主应用完全隔离，管理员界面外观/导航可独立定制，非超管用户即使知道 URL 也无法访问。

---

### 决策 5：全局资源查询——新增查询参数 vs 独立端点

**选择**：在 `/admin/` 下创建独立的全局资源端点（`GET /admin/nodes`, `GET /admin/namespaces`），而非修改现有 `/nodes/` 端点。

**理由**：现有 `/nodes/` 的 namespace 隔离是核心安全特性，不应被参数绕过。独立端点明确语义，也方便独立添加分页/过滤逻辑。

## Risks / Trade-offs

- **[风险] 超管误删自身账号** → 后端在删除用户时检查目标用户 role=0 且是唯一超管时拒绝操作
- **[风险] 角色降级后 token 仍有效** → JWT 无状态，降级后旧 token 在过期前仍可访问；缓解：token TTL 设置为 1 小时，接受此窗口期
- **[风险] system_settings 表迁移** → 需要新 Alembic migration，部署时须先运行 `alembic upgrade head`
- **[Trade-off] 无审计日志** → 超管操作无记录，本期接受，后续可通过中间件补充
- **[Trade-off] 平台统计为实时查询** → 数据量大时可能有性能问题；缓解：加查询索引，后期可引入缓存层

## Migration Plan

1. 运行 `alembic upgrade head`（新建 `system_settings` 表）
2. 部署后端（新路由自动注册）
3. 部署前端（新路由自动注册，无 UI 变更影响现有用户）
4. 验证：用超管账号访问 `/admin`，用普通账号访问应被重定向

**回滚**：前端回滚 → 管理页面消失但无任何影响；后端回滚 → 删除 admin 路由文件并从 router.py 注销；DB 回滚 → `alembic downgrade -1`（仅删除 `system_settings` 表）

## Open Questions

- 系统设置的初始默认值如何处理？（建议 seed migration 写入默认值）
- 是否需要超管看到其他用户的 AI 配置密钥？（建议：不需要，本期隐藏加密字段）
- 平台统计是否需要按时间范围过滤？（建议：初版支持 7d/30d/90d 三档）

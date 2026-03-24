## Why

NodeVault 已存在三级角色体系（超级管理员/主管/普通用户），但 `role=0` 的超级管理员目前没有任何专属后台——无法全局管理用户、跨 namespace 查看资源、配置系统参数。平台随着用户增长，运营管控能力成为迫切需求。

## What Changes

- 新增后端 `/api/v1/admin/` 路由前缀，包含超管专属 API，受 `require_superadmin` 依赖守卫保护
- 新增 `get_superadmin_user` 权限依赖，未授权用户返回 403
- 新增用户管理 API：列表/详情/封禁/解封/角色变更/删除
- 扩展节点/技能 API 支持超管全局视图（跨 namespace）
- 扩展统计 API 支持平台级聚合数据
- 前端新增 `/admin` 独立路由区域（AdminLayout），含导航侧栏
- 前端新增 5 个管理页面：用户管理、全局节点视图、分类管理增强、平台统计、系统设置

## Capabilities

### New Capabilities

- `admin-auth-guard`: 后端超管权限守卫——`get_superadmin_user` 依赖，`/admin/` 路由前缀，role=0 校验
- `admin-user-management`: 用户管理能力——查看全部用户、封禁/解封、角色变更、删除用户
- `admin-global-resources`: 全局资源视图——跨 namespace 查看所有节点、技能、命名空间
- `admin-platform-analytics`: 平台统计大盘——全平台用户/节点/调用量趋势，热门资源排行
- `admin-system-settings`: 系统配置——开放注册开关、平台公告等全局参数
- `frontend-admin-console`: 前端管理控制台——AdminLayout、路由守卫、5 个管理页面

### Modified Capabilities

- `node-registry`: 节点查询接口新增超管全局查询模式（跨 namespace 不受可见性限制）
- `category-management`: 分类管理接口限制只有超管可创建/删除/排序系统分类

## Impact

- **后端**：`backend/auth/deps.py`（新增守卫）、`backend/api/v1/`（新增 admin 路由文件）、`backend/api/v1/router.py`（注册路由）、`backend/models/user.py`（无需变更）
- **前端**：`frontend/src/layouts/`（新增 AdminLayout）、`frontend/src/views/`（新增 admin/* 页面）、`frontend/src/router/`（新增路由守卫）、`frontend/src/stores/`（auth store 增加 role 判断）
- **数据库**：无 schema 变更，仅新增查询逻辑
- **依赖**：无新增外部依赖

## ADDED Requirements

### Requirement: Superadmin permission guard
系统 SHALL 提供 `get_superadmin_user` FastAPI 依赖函数，对 role != 0 的用户返回 HTTP 403，所有 `/api/v1/admin/` 路由 SHALL 使用此守卫。

#### Scenario: Superadmin accesses admin route
- **WHEN** role=0 的用户携带有效 JWT 访问 `/api/v1/admin/` 下任意端点
- **THEN** 系统正常处理请求，返回 200

#### Scenario: Regular user attempts admin route
- **WHEN** role=2 的用户携带有效 JWT 访问 `/api/v1/admin/` 下任意端点
- **THEN** 系统返回 HTTP 403，body 包含 `"detail": "Superadmin required"`

#### Scenario: Unauthenticated access to admin route
- **WHEN** 未携带 token 的请求访问 `/api/v1/admin/` 下任意端点
- **THEN** 系统返回 HTTP 401

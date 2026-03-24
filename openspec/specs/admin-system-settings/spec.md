## ADDED Requirements

### Requirement: Read system settings
系统 SHALL 提供 `GET /api/v1/admin/settings` 端点，返回所有系统配置项（key-value 列表）。

#### Scenario: Get all settings
- **WHEN** 超管请求 `GET /admin/settings`
- **THEN** 系统返回所有配置项数组，每项含 key/value/updated_at

---

### Requirement: Update system setting
系统 SHALL 提供 `PUT /api/v1/admin/settings/{key}` 端点，允许超管更新指定配置项的值。支持的 key 包括：`enable_registration`（bool）、`platform_announcement`（text）、`default_user_role`（int）。

#### Scenario: Disable open registration
- **WHEN** 超管 PUT `{"value": "false"}` 到 `settings/enable_registration`
- **THEN** 系统更新该配置，后续 `/auth/register` 接口对未邀请用户返回 403

#### Scenario: Set platform announcement
- **WHEN** 超管 PUT `{"value": "系统将于今晚维护"}` 到 `settings/platform_announcement`
- **THEN** 系统更新公告内容，普通用户登录后可通过 `GET /api/v1/settings/announcement` 获取

#### Scenario: Update unknown setting key
- **WHEN** 超管尝试更新一个不在允许列表中的 key
- **THEN** 系统返回 HTTP 400，提示 "Unknown setting key"

---

### Requirement: Public announcement endpoint
系统 SHALL 提供 `GET /api/v1/settings/announcement` 端点（无需认证），返回当前平台公告文本，供前端展示。

#### Scenario: Get current announcement
- **WHEN** 任意客户端请求 `GET /settings/announcement`
- **THEN** 系统返回 `{"announcement": "<text>"}` 或空字符串（无公告时）

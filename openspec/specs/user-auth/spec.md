## ADDED Requirements

### Requirement: 用户注册
系统 SHALL 提供 `POST /api/v1/auth/register` 端点，接受 `email` 和 `password` 字段。密码 SHALL 使用 bcrypt 哈希存储，明文密码 SHALL NOT 写入数据库。注册成功后 SHALL 同步创建与用户 email 前缀同名的默认 Namespace。

#### Scenario: 注册成功
- **WHEN** 提供有效的 email 和符合强度要求的 password（≥8位，含大小写和数字）
- **THEN** 系统 SHALL 创建 User 记录和对应的默认 Namespace，返回 201 和用户信息（不含密码）

#### Scenario: 邮箱已存在
- **WHEN** 使用已注册的 email 发起注册请求
- **THEN** 系统 SHALL 返回 409，提示邮箱已被使用

#### Scenario: 密码强度不足
- **WHEN** 提供长度不足 8 位或不含数字的密码
- **THEN** 系统 SHALL 返回 422 并说明密码规则

---

### Requirement: 用户登录与 JWT 签发
系统 SHALL 提供 `POST /api/v1/auth/login` 端点，验证 email/password 后签发 JWT access token。Token SHALL 使用 `jwt_secret_key` 签名，算法为 `HS256`，有效期 30 分钟（可通过 `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` 配置）。

#### Scenario: 登录成功
- **WHEN** 提供正确的 email 和 password
- **THEN** 系统 SHALL 返回 200，body 包含 `access_token`（JWT 字符串）和 `token_type: bearer`

#### Scenario: 密码错误
- **WHEN** 提供正确 email 但错误 password
- **THEN** 系统 SHALL 返回 401，提示凭据无效（不区分 email 不存在还是密码错误，防止用户枚举）

#### Scenario: Token 包含正确 Claims
- **WHEN** 登录成功后解码返回的 JWT
- **THEN** payload SHALL 包含 `sub`（user_id 字符串）、`exp`（过期时间戳）、`iat`（签发时间戳）

---

### Requirement: JWT Bearer Token 鉴权中间件
系统 SHALL 提供 `get_current_user` FastAPI 依赖函数，从 `Authorization: Bearer <token>` 中提取并验证 JWT，返回当前用户对象。该依赖 SHALL 用于所有需要认证的端点。

#### Scenario: 有效 Token 通过鉴权
- **WHEN** 请求头携带有效且未过期的 Bearer Token
- **THEN** `get_current_user` SHALL 返回对应的 User 对象

#### Scenario: 无 Token 时拒绝请求
- **WHEN** 请求头不包含 Authorization 字段
- **THEN** 系统 SHALL 返回 401，提示需要认证

#### Scenario: 过期 Token 被拒绝
- **WHEN** 请求头携带已过期的 Bearer Token
- **THEN** 系统 SHALL 返回 401，提示 Token 已过期

---

### Requirement: 获取当前用户信息
系统 SHALL 提供 `GET /api/v1/auth/me` 端点，需要 Bearer Token 认证，返回当前用户的基本信息。

#### Scenario: 获取用户信息成功
- **WHEN** 使用有效 Token 调用 GET /api/v1/auth/me
- **THEN** 系统 SHALL 返回 200，包含 `id`、`email`、`username`、`created_at`（不含密码哈希）

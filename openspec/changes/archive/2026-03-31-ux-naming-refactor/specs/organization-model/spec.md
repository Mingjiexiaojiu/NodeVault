## ADDED Requirements

### Requirement: Organization 数据表
系统 SHALL 提供 `organizations` 表，字段包含 id（UUID PK）、name（VARCHAR(128) UNIQUE NOT NULL）、created_at（DateTime）。

#### Scenario: 创建 Organization 成功
- **WHEN** 系统通过创建团队流程或管理接口提交合法的 organization name
- **THEN** 系统 SHALL 创建 Organization 记录，name 唯一

#### Scenario: Organization name 重复
- **WHEN** 尝试创建与已有 Organization 同名的记录
- **THEN** 系统 SHALL 返回 409 Conflict

### Requirement: 创建 Organization
系统 SHALL 提供 `POST /api/v1/organizations` 端点（需认证，role ≤ 1），创建新的 Organization。

#### Scenario: 主管创建组织成功
- **WHEN** role=1 的用户提交合法的 name
- **THEN** 系统 SHALL 创建 Organization 记录，返回 201

#### Scenario: 普通用户创建被拒绝
- **WHEN** role=2 的普通用户尝试创建组织
- **THEN** 系统 SHALL 返回 403

### Requirement: 查询 Organization 列表
系统 SHALL 提供 `GET /api/v1/organizations` 端点（需认证），返回所有 Organization 及其下属团队数量。

#### Scenario: 列出所有组织
- **WHEN** 任意已认证用户调用 GET /api/v1/organizations
- **THEN** 系统 SHALL 返回组织列表，每项含 id、name、team_count、created_at

### Requirement: 创建团队时自动创建 Organization
系统 SHALL 在创建团队（Department）时，如果前端提交的 organization name 不存在，自动创建对应的 Organization 记录后关联。

#### Scenario: 选择已有组织创建团队
- **WHEN** 用户创建团队时选择已有的 Organization
- **THEN** 系统 SHALL 将新团队的 org_id 指向该 Organization

#### Scenario: 输入新组织名创建团队
- **WHEN** 用户创建团队时输入一个不存在的组织名
- **THEN** 系统 SHALL 先创建 Organization 记录，再将新团队的 org_id 指向它

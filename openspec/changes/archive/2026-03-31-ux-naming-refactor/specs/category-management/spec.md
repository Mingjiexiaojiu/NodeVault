## MODIFIED Requirements

### Requirement: Category 数据表
系统 SHALL 提供 `categories` 表，字段包含 id（UUID PK）、display_name（VARCHAR(128) UNIQUE NOT NULL）、icon（VARCHAR(64) 可选）、sort_order（INT 默认 0）、is_default（BOOL 默认 false）、created_by（UUID FK → users.id）、created_at、updated_at。原 `name`（snake_case 标识）字段 SHALL 删除。

#### Scenario: 系统启动时种子数据
- **WHEN** 执行 Alembic 迁移
- **THEN** 系统 SHALL 创建 8 条默认分类记录，每条 `is_default=true`，display_name 分别为 数据清洗/数据分析/风控/自然语言处理/计算机视觉/机器学习/工具/通用

### Requirement: 创建自定义分类
系统 SHALL 提供 `POST /api/v1/categories` 端点（需认证，role=0），创建新的自定义分类。请求体只需 `display_name`（必填）、`icon`（可选）、`sort_order`（可选），不再需要 `name` 字段。

#### Scenario: 超管创建分类成功
- **WHEN** role=0 的用户提交合法的 display_name
- **THEN** 系统 SHALL 创建分类记录（is_default=false），返回 201

#### Scenario: display_name 重复
- **WHEN** 提交的 display_name 与已有分类重复
- **THEN** 系统 SHALL 返回 409

#### Scenario: 普通用户创建被拒绝
- **WHEN** role=2 的普通用户尝试创建分类
- **THEN** 系统 SHALL 返回 403

### Requirement: 查询分类列表
系统 SHALL 提供 `GET /api/v1/categories` 端点（需认证），返回所有分类，按 sort_order 升序排列。

#### Scenario: 列出所有分类
- **WHEN** 任意已认证用户调用 GET /api/v1/categories
- **THEN** 系统 SHALL 返回分类列表，每项含 id/display_name/icon/sort_order/is_default

### Requirement: 更新分类
系统 SHALL 提供 `PATCH /api/v1/categories/{category_id}` 端点（需认证，role=0），允许更新 display_name、icon、sort_order。

#### Scenario: 更新 display_name 成功
- **WHEN** 超管用户更新某分类的 display_name
- **THEN** 系统 SHALL 返回 200 和更新后的分类信息

#### Scenario: 更新后 display_name 与其他分类重复
- **WHEN** 更新后的 display_name 已被其他分类使用
- **THEN** 系统 SHALL 返回 409

### Requirement: 默认分类自动创建系统 Skill
系统 SHALL 在创建默认分类种子数据的同时，为每个默认分类创建一个系统级 Skill（name 基于 display_name 生成的 kebab-case，如"数据清洗" → "shu-ju-qing-xi-collection"，is_system=true）。

#### Scenario: 迁移后系统 Skill 存在
- **WHEN** 迁移执行完成后
- **THEN** 系统 SHALL 存在 8 个 is_system=true 的 Skill，与默认分类一一对应

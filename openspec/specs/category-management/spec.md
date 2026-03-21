## ADDED Requirements

### Requirement: Category 数据表
系统 SHALL 提供 `categories` 表，字段包含 id（UUID PK）、name（VARCHAR(64) UNIQUE）、display_name（VARCHAR(128)）、icon（VARCHAR(64) 可选）、sort_order（INT 默认 0）、is_default（BOOL 默认 false）、created_by（UUID FK → users.id）、created_at、updated_at。

#### Scenario: 系统启动时种子数据
- **WHEN** 执行 Alembic 迁移
- **THEN** 系统 SHALL 创建 8 条默认分类记录（data_cleaning/analysis/risk/nlp/vision/ml/tool/utility），每条 `is_default=true`，display_name 分别为 数据清洗/分析/风控/NLP/视觉/机器学习/工具/通用

### Requirement: 查询分类列表
系统 SHALL 提供 `GET /api/v1/categories` 端点（需认证），返回所有分类，按 sort_order 升序排列。

#### Scenario: 列出所有分类
- **WHEN** 任意已认证用户调用 GET /api/v1/categories
- **THEN** 系统 SHALL 返回分类列表，每项含 id/name/display_name/icon/sort_order/is_default

### Requirement: 创建自定义分类
系统 SHALL 提供 `POST /api/v1/categories` 端点（需认证，role ≤ 1），创建新的自定义分类。

#### Scenario: 主管创建分类成功
- **WHEN** role=1 的用户提交合法的 name（snake_case）和 display_name
- **THEN** 系统 SHALL 创建分类记录（is_default=false），返回 201

#### Scenario: 普通用户创建被拒绝
- **WHEN** role=2 的普通用户尝试创建分类
- **THEN** 系统 SHALL 返回 403

#### Scenario: name 重复
- **WHEN** 提交的 name 与已有分类重复
- **THEN** 系统 SHALL 返回 409

### Requirement: 更新分类
系统 SHALL 提供 `PATCH /api/v1/categories/{category_id}` 端点（需认证，role ≤ 1），允许更新 display_name、icon、sort_order。系统默认分类的 name 字段 SHALL NOT 允许修改。

#### Scenario: 更新 display_name 成功
- **WHEN** 主管用户更新某分类的 display_name
- **THEN** 系统 SHALL 返回 200 和更新后的分类信息

#### Scenario: 不允许修改默认分类的 name
- **WHEN** 用户尝试修改 is_default=true 的分类的 name
- **THEN** 系统 SHALL 返回 422，提示"系统默认分类名称不可修改"

### Requirement: 删除自定义分类
系统 SHALL 提供 `DELETE /api/v1/categories/{category_id}` 端点（需认证，role ≤ 1），仅允许删除 is_default=false 的分类。删除前 SHALL 检查是否有节点引用该分类。

#### Scenario: 删除无引用的自定义分类
- **WHEN** 主管用户删除一个没有节点引用的自定义分类
- **THEN** 系统 SHALL 返回 204

#### Scenario: 删除被引用的分类被拒绝
- **WHEN** 该分类下仍有节点
- **THEN** 系统 SHALL 返回 409，提示"该分类下仍有 N 个节点，请先移动节点"

#### Scenario: 删除默认分类被拒绝
- **WHEN** 用户尝试删除 is_default=true 的分类
- **THEN** 系统 SHALL 返回 422，提示"系统默认分类不可删除"

### Requirement: 默认分类自动创建系统 Skill
系统 SHALL 在创建默认分类种子数据的同时，为每个默认分类创建一个系统级 Skill（name 为 `{category_name}-collection`，is_system=true）。

#### Scenario: 迁移后系统 Skill 存在
- **WHEN** 迁移执行完成后
- **THEN** 系统 SHALL 存在 8 个 is_system=true 的 Skill，name 分别为 data_cleaning-collection、analysis-collection 等

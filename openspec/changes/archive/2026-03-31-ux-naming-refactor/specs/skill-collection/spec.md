## MODIFIED Requirements

### Requirement: 创建 Skill
系统 SHALL 提供 `POST /api/v1/skills` 端点（需认证），创建一个新的 Skill 实体。`display_name` 为必填主字段；`name`（kebab-case 标识）为可选字段，未提供时系统 SHALL 基于 display_name 自动生成。Skill `name` SHALL 全局唯一。

#### Scenario: 仅提供 display_name 创建成功
- **WHEN** 已认证用户只提供 display_name 和可选 description，不提供 name
- **THEN** 系统 SHALL 基于 display_name 自动生成 kebab-case 的 name（中文用 pinyin 转换），创建 Skill 记录，返回 201

#### Scenario: 提供 name 和 display_name 创建成功
- **WHEN** 已认证用户同时提供合法的 name 和 display_name
- **THEN** 系统 SHALL 使用用户提供的 name 创建 Skill 记录

#### Scenario: 自动生成 name 冲突时追加后缀
- **WHEN** 自动生成的 name 与已有 Skill 重复
- **THEN** 系统 SHALL 追加数字后缀（-2、-3 等）直到唯一

#### Scenario: name 格式非法
- **WHEN** 用户手动提供的 name 包含大写字母或下划线（非 kebab-case）
- **THEN** 系统 SHALL 返回 422

#### Scenario: name 重复
- **WHEN** 用户手动提供的 name 已存在
- **THEN** 系统 SHALL 返回 409

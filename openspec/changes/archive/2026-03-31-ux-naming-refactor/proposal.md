## Why

当前系统的命名体系过于"程序员向"——部门要求填写英文 slug、分类同时需要 `name`（snake_case 标识）和 `display_name`、技能集同时需要 `name`（kebab-case）和 `display_name`、部门内角色标签"管理员"与全局角色"主管"含义交叉。普通用户面对 slug、标识、name 等概念容易迷惑，表单字段存在明显的信息冗余。需要重构命名体系，让用户界面更直观、概念更清晰。

## What Changes

### 部门 → 组织 + 团队（两层模型）
- **BREAKING** 新增 `Organization`（组织）表，承载"大组织/部门"概念（如"人工智能部"），可跨团队复用
- **BREAKING** `Department` 表改造为"团队"：删除 `slug` 字段，`display_name` 改为 `team_name`，新增 `org_id` 外键关联 Organization
- `Department.owner_id` 前端标签改为"拥有者"
- `DepartmentMember.role = "admin"` 前端标签从"管理员"改为"主管"
- 创建团队时，部门名称字段改为下拉选择已有组织（可新建）

### 分类简化
- **BREAKING** `Category` 表删除 `name`（snake_case 标识）字段
- `display_name` 加 UNIQUE 约束，成为分类唯一名称字段
- 前端创建/编辑分类表单简化为只有"名称"、"图标"、"排序"
- 种子数据（默认分类）只保留 `display_name`

### 技能集交互优化
- `Skill.display_name` 改为 required，成为创建技能集的主字段，标签改为"技能集名称"
- `Skill.name`（kebab-case 标识）保留（用于导出文件名、SKILL.md），但前端藏到"高级选项"折叠区域
- 未提供 `name` 时系统自动生成（基于 display_name 拼音转换或 UUID 前缀）

## Capabilities

### New Capabilities
- `organization-model`: 新增 Organization 实体，支持大组织概念的独立管理（CRUD）、可复用关联

### Modified Capabilities
- `department-supervisor`: 部门（团队）表结构重构——删除 slug、关联 Organization、字段重命名；角色标签调整
- `category-management`: 分类字段简化——删除 name 标识字段，display_name 成为唯一名称
- `skill-collection`: 技能集创建交互优化——display_name 变为 required 主字段，name 退为可选高级字段，支持自动生成
- `frontend-node-list`: 节点列表中部门相关展示字段从 slug 改为组织名+团队名
- `frontend-node-detail`: 节点详情中部门信息展示调整
- `frontend-dashboard`: 仪表盘中部门 badge 从 slug 改为团队名称
- `frontend-category-management`: 分类管理表单简化
- `frontend-skill-collection`: 技能集创建/列表交互重构
- `admin-global-resources`: 管理后台中部门相关字段展示调整
- `admin-platform-analytics`: 统计分析视图中部门字段调整
- `node-search`: 搜索索引中部门字段调整

## Impact

- **数据库**: 需新增 `organizations` 表；`departments` 表删除 `slug` 列、新增 `org_id` 列、重命名 `display_name` → `team_name`；`categories` 表删除 `name` 列、`display_name` 加唯一约束；`skills` 表 `display_name` 改为 NOT NULL
- **后端 API**: departments、categories、skills、nodes、admin、auth、search 等模块的 schema 和 response 都需要调整
- **前端**: ~12 个视图文件需要更新表单、列表、详情展示
- **数据迁移**: 需要 Alembic migration 处理所有 schema 变更，已有数据需要迁移（slug 数据归档/转换、category name 数据清理）
- **SDK**: 不受影响（SDK 使用 UUID，不依赖 slug）
- **BREAKING**: API response 中 `department_slug` 字段将被移除，替换为 `organization_name` + `team_name`

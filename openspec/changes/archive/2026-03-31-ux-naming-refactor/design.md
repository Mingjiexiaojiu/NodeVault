## Context

当前 NodeVault 数据模型中，Department（部门）用 `slug`（英文 kebab-case）作为标识、`display_name` 作为中文展示名。Category 同时维护 `name`（snake_case 标识）和 `display_name`。Skill 同时维护 `name`（kebab-case）和 `display_name`。部门内 admin 角色在前端显示为"管理员"，与全局角色"主管"含义交叉。

用户反馈这套命名体系过于技术化，字段冗余，概念混淆。需要引入"组织→团队"两层结构、简化分类命名、优化技能集创建体验、统一角色术语。

## Goals / Non-Goals

**Goals:**
- 引入 Organization 实体承载"大组织/部门"概念，支持跨团队复用
- Department 改造为"团队"，关联 Organization，删除 slug
- Category 删除 `name` 标识字段，`display_name` 成为唯一名称
- Skill 的 `display_name` 变为 required 主字段，`name` 退为自动生成的可选高级字段
- 前端角色术语统一：部门内 admin → "主管"，owner_id → "拥有者"

**Non-Goals:**
- 不改变全局用户角色体系（role=0/1/2）
- 不改变 DepartmentMember 表的 role 字段值（仍为 "admin"/"member"），只改前端展示标签
- 不为 Organization 引入独立权限体系或成员管理
- 不改变 SDK 接口（SDK 使用 UUID，不受影响）
- 不改变 Skill 导出文件名逻辑（仍用 name），只改创建交互

## Decisions

### D1: Organization 作为轻量实体

**决定**：Organization 只有 `id`、`name`、`created_at` 三个字段，不引入独立的成员管理或权限。

**理由**：Organization 的核心需求是"可复用的大组织标签"。如果引入成员管理，会和 Department 的成员管理形成双层权限，大幅增加复杂度。保持轻量，未来需要时再扩展。

**替代方案**：
- 给 Organization 加 owner_id 和成员表 → 过度设计，当前没有组织级管理需求
- 不建表，用字符串字段 → 无法保证一致性，改名时要改所有行

### D2: Department.slug 改为 org_id 外键

**决定**：删除 `slug` 列，新增 `org_id` UUID 外键指向 `organizations.id`。原 `display_name` 重命名为 `team_name`。`UNIQUE(org_id, team_name)` 替代原 slug 唯一约束。

**理由**：slug 在 API 路由中完全不用（所有端点走 UUID），其展示功能由 org.name + team_name 替代。两层模型更符合用户心智模型。

**替代方案**：
- 保留 slug 改标签 → 无法实现"大组织可复用"的核心需求
- slug 改为允许中文 → 仍是单层模型，不符合层级需求

### D3: Category 删除 name 字段

**决定**：删除 `name`（snake_case 标识），`display_name` 加 UNIQUE 约束成为唯一名称字段。种子数据只保留 `display_name`。系统 Skill 命名改为基于 display_name（如"数据清洗-collection"）。

**理由**：Category.name 在 API 路由和前端展示中几乎不使用，所有面向用户的场景都用 display_name。维持两个名称字段只增加用户创建分类时的困惑。

**影响**：迁移脚本需要将现有 `name` 数据移除，将已有默认分类的 display_name 加唯一索引。系统 Skill 的 name（如 `data_cleaning-collection`）需要更新。

### D4: Skill.name 保留但自动生成

**决定**：`Skill.name` 保留（用于导出文件名、SKILL.md 标识），但 `display_name` 改为 NOT NULL required。创建时如果不提供 name，后端自动生成（策略：将 display_name 转为 kebab-case，优先 pinyin 转换，冲突时追加数字后缀）。前端将 name 藏到"高级选项"折叠区。

**理由**：name 有机器用途（导出文件名、SDK 引用），不能完全删除。但让它退居二线，用户默认只填一个名称即可。

**自动生成策略**：
1. 尝试将 display_name 转为 kebab-case（英文直接转换，中文用 pinyin）
2. 若结果已存在，追加 `-2`、`-3` 等数字后缀
3. 后端引入 `pypinyin` 依赖做中文转拼音

**替代方案**：
- 用 UUID 前8位作为 name → 毫无可读性，导出文件名不友好
- 完全删除 name → 破坏导出文件名和 SKILL.md 格式

### D5: 角色标签变更仅限前端

**决定**：DepartmentMember.role 字段值不变（仍为 `"admin"` / `"member"`），只改前端展示文案：
- `role=admin` → 显示"主管"（原"管理员"）
- `owner_id` 对应用户 → 显示"拥有者"（原"创建者"/"所有者"）

**理由**：字段值是 API 契约，改值会影响 SDK 和所有调用方。只改展示最安全。

### D6: 创建团队时组织选择交互

**决定**：创建团队表单中"部门名称"用 combobox（下拉选择已有组织 + 可输入新组织名）。选择已有组织直接关联 org_id；输入新名称时后端先创建 Organization 再关联。

**理由**：combobox 模式让复用和新建自然融合，不需要用户先去别的页面创建组织。

### D7: 数据迁移策略

**决定**：
1. 为每个现有 department，取其 `slug` 作为 organization name 创建 Organization 记录
2. department 的 `display_name` 直接作为 `team_name`
3. 关联 org_id 后删除 slug 列
4. Category 的 display_name 加唯一约束（先检查无重复）
5. 删除 Category.name 列

**回滚**：迁移脚本包含 downgrade，可恢复 slug 和 name 列。

## Risks / Trade-offs

- **[Risk] pypinyin 依赖** → 仅用于 Skill name 自动生成，是轻量库；若不愿引入，可退化为 UUID 前缀方案
- **[Risk] 现有 department slug 数据丢失** → 迁移时将 slug 作为 Organization.name 保留，不丢失语义
- **[Risk] Category display_name 唯一约束可能冲突** → 迁移前加校验，确保无重复 display_name
- **[Risk] API breaking change (department_slug 字段移除)** → 前端和后端同步发布，SDK 不受影响
- **[Risk] 系统 Skill name 变更（如 data_cleaning-collection → 数据清洗-collection）** → 迁移时同步更新

## Migration Plan

1. **创建 organizations 表** — 新增 Alembic migration
2. **填充 organizations** — 从现有 departments.slug 去重创建 Organization 记录
3. **departments 表改造** — 添加 org_id 列并回填，重命名 display_name → team_name，添加 UNIQUE(org_id, team_name)，删除 slug 列
4. **categories 表改造** — display_name 加 UNIQUE 约束，删除 name 列
5. **skills 表改造** — display_name 改 NOT NULL
6. **后端 API 调整** — 更新所有 schema、response、route
7. **前端同步更新** — 所有视图文件更新字段和标签
8. **回滚策略** — 每个 migration 包含 downgrade 函数

## Open Questions

- Organization 是否需要 description 字段？（当前设计不含，可后续按需添加）
- 是否需要 Organization 的管理页面（CRUD），还是仅通过创建团队时自动管理？

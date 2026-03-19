## 1. 数据库：新增表与字段迁移

- [x] 1.1 创建 `skills` 表（id/name/display_name/description/namespace_id/owner_id/status/is_stale/created_at/updated_at）
- [x] 1.2 创建 `skill_versions` 表（id/skill_id/version/skill_md/node_snapshot JSONB/release_notes/is_default/created_at）
- [x] 1.3 `nodes` 表新增 `skill_id` UUID 外键（nullable，ON DELETE SET NULL）和 `usage_hint` VARCHAR(500) 字段
- [x] 1.4 编写 Alembic migration 脚本，运行并验证迁移成功（HEAD: f6a7b8c9d0e1）
- [x] 1.5 编写数据迁移脚本：按现有 `category` 字符串分组 → 创建 Skill 记录 → 回填 `nodes.skill_id`

## 2. 后端 Model 与 Schema

- [x] 2.1 创建 `backend/models/skill.py`：`Skill` 和 `SkillVersion` SQLAlchemy 模型
- [x] 2.2 更新 `backend/models/node.py`：添加 `skill_id` 和 `usage_hint` 字段，添加 `skill` relationship（lazy="joined")
- [x] 2.3 创建 `backend/schemas/skill.py`：`SkillCreate`、`SkillUpdate`、`SkillResponse`、`SkillDetailResponse`、`SkillVersionCreate`、`SkillVersionResponse`
- [x] 2.4 更新 `backend/schemas/node.py`：`NodeCreate` 和 `NodeUpdate` 新增 `skill_id` 和 `usage_hint` 字段；`NodeResponse` 新增 `skill_id`、`usage_hint`、`skill_name`

## 3. 后端核心逻辑

- [x] 3.1 创建 `backend/core/skill_registry.py`：`SkillRegistry` 类，实现 create_skill / list_skills / get_skill / update_skill / archive_skill 方法
- [x] 3.2 在 `SkillRegistry` 中实现 `create_version`：锁定 node_snapshot（查询当前所有节点的默认 node_version_id）、保存 skill_md、重置 is_stale=false
- [x] 3.3 在 `backend/core/registry.py` 的 `update_node` 中加入 is_stale 触发逻辑：变更 skill_id、usage_hint、description 时更新对应 Skill 的 is_stale=true（含双端更新）
- [x] 3.4 创建 `backend/core/skill_md_generator.py`：收集节点 metadata → 构建 Prompt → 调用 LLM API（支持 `LLM_PROVIDER` env 切换 claude/openai）→ 返回 skill_md 文本；实现并发锁（数据库行级锁）

## 4. 后端 API

- [x] 4.1 创建 `backend/api/v1/skills.py` 路由文件，注册到 `router.py`
- [x] 4.2 实现 `GET /api/v1/skills`：列表，含 node_count 和 latest_version
- [x] 4.3 实现 `POST /api/v1/skills`：创建，name kebab-case 校验，namespace 内唯一性校验
- [x] 4.4 实现 `GET /api/v1/skills/{skill_id}`：详情，含 nodes 数组和 versions 数组
- [x] 4.5 实现 `PATCH /api/v1/skills/{skill_id}`：更新 display_name/description/status，所有者鉴权
- [x] 4.6 实现 `DELETE /api/v1/skills/{skill_id}`：软删除，返回 204
- [x] 4.7 实现 `GET /api/v1/skills/{skill_id}/versions`：版本历史列表
- [x] 4.8 实现 `POST /api/v1/skills/{skill_id}/versions`：发布版本，版本号唯一性校验，创建快照
- [x] 4.9 实现 `POST /api/v1/skills/{skill_id}/generate`：调用 LLM 生成 SKILL.md 草稿，返回 skill_md + suggested_version；空节点/LLM 失败/并发冲突处理
- [x] 4.10 实现 `GET /api/v1/skills/{skill_id}/export`：读取 SkillVersion.skill_md，组装 ZIP（SKILL.md + references/setup.md），支持 `?version=` 参数

## 5. 后端测试

- [x] 5.1 创建 `backend/tests/test_skills.py`：覆盖 Skill CRUD、版本发布、is_stale 触发逻辑、并发生成锁、ZIP 导出

## 6. 前端 API 层

- [x] 6.1 创建 `frontend/src/api/skills.ts`：`getSkills`、`createSkill`、`getSkillDetail`、`updateSkill`、`deleteSkill`、`getSkillVersions`、`createSkillVersion`、`generateSkillMd`、`downloadSkillZip` 函数及对应类型定义
- [x] 6.2 更新 `frontend/src/api/nodes.ts`：`NodeItem` 新增 `skill_id`、`usage_hint`、`skill_name` 字段；`createNode` / `updateNode` 请求体新增对应字段

## 7. 前端：节点创建/编辑页改造

- [x] 7.1 在 `NodeCreateView.vue` 中新增 Skill 选择器：调用 `getSkills()` 填充下拉列表，含"不归属任何技能集"选项
- [x] 7.2 新增 `usage_hint` textarea（选填，500字限制，实时字符计数）
- [x] 7.3 在节点详情页：当 `usage_hint` 为空且有 `skill_id` 时，显示引导提示

## 8. 前端：技能集列表与创建

- [x] 8.1 创建 `frontend/src/views/SkillListView.vue`：展示技能集卡片列表（含 is_stale 标识）、新建按钮及创建表单（模态框）
- [x] 8.2 在路由 `frontend/src/router/index.ts` 中注册 `/skills` 和 `/skills/:id` 路由
- [x] 8.3 在 `AppLayout.vue` 导航栏中添加"技能"入口

## 9. 前端：技能集详情页

- [x] 9.1 创建 `frontend/src/views/SkillDetailView.vue`：展示 Skill 基本信息、is_stale 警告 banner、节点列表（含 usage_hint 状态）、版本历史列表
- [x] 9.2 实现"生成 SKILL.md"流程：点击 → loading → 可编辑预览 → 发布版本表单
- [x] 9.3 实现"下载 ZIP"：点击触发 `downloadSkillZip(skillId)`；版本历史每行提供独立下载

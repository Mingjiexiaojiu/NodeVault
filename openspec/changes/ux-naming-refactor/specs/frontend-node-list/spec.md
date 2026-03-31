## MODIFIED Requirements

### Requirement: 节点卡片展示分类标和部门信息
- **WHEN** 节点列表渲染节点卡片 / 列表行
- **THEN** 每个节点 SHALL 展示对应类别的 display_name 作为"类别"标签（badge），部门信息 SHALL 展示为"组织名称 / 团队名称"格式（替代原 department_slug）

#### Scenario: 节点卡片展示组织和团队
- **WHEN** 节点关联了某个团队
- **THEN** 节点卡片 SHALL 显示该团队所属组织名和团队名（如"人工智能部 / 视觉算法团队"）

#### Scenario: 节点未关联团队
- **WHEN** 节点未关联任何团队
- **THEN** 节点卡片 SHALL 在部门位置显示"—"

### Requirement: User can filter nodes by department
前端 SHALL 将原按 department_slug 筛选改为按组织名称和团队名称筛选。

#### Scenario: 按组织筛选节点
- **WHEN** 用户在筛选栏选择某个组织
- **THEN** 列表 SHALL 只显示该组织下所有团队的节点

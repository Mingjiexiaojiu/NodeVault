## MODIFIED Requirements

### Requirement: User can view full node metadata
The system SHALL display a node detail page with all metadata fields from GET /api/v1/nodes/:id. 部门信息 SHALL 展示为"组织名称 / 团队名称"格式，替代原 department_slug。

#### Scenario: Detail page renders metadata
- **WHEN** user navigates to /nodes/:id
- **THEN** page shows: name, display_name, description, type, status, visibility, category, owner_id, organization_name, team_name, tags, created_at, updated_at

#### Scenario: 节点部门信息展示
- **WHEN** 节点关联了某个团队
- **THEN** 详情页 SHALL 显示"组织名称 / 团队名称"（如"人工智能部 / 视觉算法团队"），替代原 department_slug 字段

## MODIFIED Requirements

### Requirement: Dashboard shows recent nodes
The system SHALL display the 5 most recently created nodes. 节点卡片中的部门 badge SHALL 显示团队名称（team_name），替代原 department_slug。

#### Scenario: Recent nodes list renders
- **WHEN** dashboard loads
- **THEN** a "最近注册的节点" section shows the 5 most recent nodes with name, type badge, team_name badge（替代原 slug badge）, and status

#### Scenario: 节点无团队关联
- **WHEN** 节点未关联任何团队
- **THEN** 团队 badge SHALL 不显示

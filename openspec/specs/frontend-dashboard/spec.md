## ADDED Requirements

### Requirement: Dashboard shows node summary statistics
The system SHALL display a statistics overview on the dashboard home page.

#### Scenario: Stats cards render on load
- **WHEN** user navigates to /
- **THEN** dashboard displays cards for: total nodes, active nodes, total invocations (from logs), draft nodes

#### Scenario: Stats derived from node list
- **WHEN** the backend has no dedicated stats endpoint
- **THEN** frontend calls GET /api/v1/nodes (all pages) and computes counts client-side

### Requirement: Dashboard shows recent nodes
The system SHALL display the 5 most recently created nodes.

#### Scenario: Recent nodes list renders
- **WHEN** dashboard loads
- **THEN** a "最近注册的节点" section shows the 5 most recent nodes with name, type badge, and status

#### Scenario: Click recent node navigates to detail
- **WHEN** user clicks a node in the recent list
- **THEN** user is navigated to /nodes/:id

### Requirement: Dashboard has a quick-action bar
The system SHALL show prominent action buttons for common tasks.

#### Scenario: Primary actions visible
- **WHEN** dashboard renders
- **THEN** buttons "注册新节点" and "浏览全部节点" are shown with clear visual hierarchy

### Requirement: Dashboard shows welcome message with username
The system SHALL personalize the dashboard with the logged-in user's information.

#### Scenario: Username shown in header
- **WHEN** user is authenticated
- **THEN** the dashboard header shows "欢迎，{username}"


---

## Changes from ux-naming-refactor

## MODIFIED Requirements

### Requirement: Dashboard shows recent nodes（更新）
The system SHALL display the 5 most recently created nodes. 节点卡片中的部门 badge SHALL 显示团队名称（team_name），替代原 department_slug。

#### Scenario: Recent nodes list renders
- **WHEN** dashboard loads
- **THEN** a "最近注册的节点" section shows the 5 most recent nodes with name, type badge, team_name badge（替代原 slug badge）, and status

#### Scenario: 节点无团队关联
- **WHEN** 节点未关联任何团队
- **THEN** 团队 badge SHALL 不显示

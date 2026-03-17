## ADDED Requirements

### Requirement: User can view a list of all nodes
The system SHALL display all accessible nodes in a paginated table/card list.

#### Scenario: Default node list loads
- **WHEN** user navigates to /nodes
- **THEN** a list of nodes from GET /api/v1/nodes is displayed, showing name, type, status, and creation date

#### Scenario: List shows empty state
- **WHEN** no nodes exist for the user's namespace
- **THEN** an empty state illustration and "暂无节点，立即注册第一个" button is shown

### Requirement: User can filter nodes by type and status
The system SHALL provide filter controls above the node list.

#### Scenario: Filter by node type
- **WHEN** user selects a type from the type dropdown (e.g., "tool")
- **THEN** list refreshes with query param `?type=tool` and only matching nodes are shown

#### Scenario: Filter by status
- **WHEN** user selects status "active" from the status dropdown
- **THEN** list refreshes with `?status=active` and only active nodes are shown

#### Scenario: Clear filters
- **WHEN** user clicks "重置筛选"
- **THEN** all filter dropdowns reset and full list is reloaded

### Requirement: Node list supports pagination
The system SHALL paginate the node list with configurable page size.

#### Scenario: Navigate to next page
- **WHEN** there are more nodes than the current page size (default 20)
- **THEN** pagination controls are shown; clicking "下一页" loads the next page

### Requirement: Node list links to detail page
Each node row SHALL have a clickable area leading to the node detail page.

#### Scenario: Click node name to view detail
- **WHEN** user clicks a node's name or "查看详情" link
- **THEN** user is navigated to /nodes/:id

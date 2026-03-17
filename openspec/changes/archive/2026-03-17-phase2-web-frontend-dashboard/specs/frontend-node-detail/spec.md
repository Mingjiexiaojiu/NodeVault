## ADDED Requirements

### Requirement: User can view full node metadata
The system SHALL display a node detail page with all metadata fields from GET /api/v1/nodes/:id.

#### Scenario: Detail page renders metadata
- **WHEN** user navigates to /nodes/:id
- **THEN** page shows: name, display_name, description, type, status, visibility, category, owner_id, namespace_id, tags, created_at, updated_at

#### Scenario: Node not found
- **WHEN** the node ID does not exist or is inaccessible
- **THEN** a 404 error card is shown with a "返回列表" button

### Requirement: Detail page shows all versions
The system SHALL show a version list from GET /api/v1/nodes/:id/versions.

#### Scenario: Version list renders
- **WHEN** page loads
- **THEN** all versions are shown in a table with columns: version, is_default, is_deprecated, created_at

#### Scenario: Default version is highlighted
- **WHEN** a version has is_default=true
- **THEN** it is marked with a "默认" badge

### Requirement: Detail page shows recent invocation logs
The system SHALL show the last 50 invocation logs from GET /api/v1/nodes/:id/logs.

#### Scenario: Log list renders
- **WHEN** page loads
- **THEN** logs are shown with: invocation time, status (success/failure/timeout), latency_ms

#### Scenario: Empty logs state
- **WHEN** no invocations have been made
- **THEN** an empty state message "暂无调用记录" is displayed

### Requirement: Detail page provides navigation to invoke
The system SHALL have a prominent "调用此节点" button.

#### Scenario: Navigate to invoke page
- **WHEN** user clicks "调用此节点"
- **THEN** user is navigated to /nodes/:id/invoke

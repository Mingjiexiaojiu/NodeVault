## MODIFIED Requirements

### Requirement: Service discovery page
The system SHALL provide a dedicated frontend page at `/discover/new` for service discovery and batch import (previously at `/discover`).

#### Scenario: Navigate to discovery wizard
- **WHEN** user clicks "新建发现" on the history list or visits `/discover/new`
- **THEN** system SHALL display the three-step wizard with probe URL input

#### Scenario: Redirect bare /discover to history list
- **WHEN** user visits `/discover`
- **THEN** system SHALL display the discovery session history list page, NOT the wizard

### Requirement: Batch import action
The system SHALL provide an "导入选中" button that creates all selected Nodes and updates the discovery session.

#### Scenario: Successful batch import with session
- **WHEN** user has selected 4 operations and clicks "导入选中 (4)"
- **THEN** system SHALL call the batch import API with the current `session_id`, and on success navigate to `/discover` (history list)

#### Scenario: Partial failure
- **WHEN** one of the batch imports fails (e.g., name conflict)
- **THEN** system SHALL show which Nodes succeeded and which failed with error details

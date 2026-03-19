## ADDED Requirements

### Requirement: Service discovery page
The system SHALL provide a dedicated frontend page at `/discover` for service discovery and batch import.

#### Scenario: Navigate to discovery page
- **WHEN** user clicks "服务发现" in the navigation or visits `/discover`
- **THEN** system SHALL display an input field for the service base URL with a "探测" button

### Requirement: Probe progress visualization
The system SHALL show real-time progress while probing spec paths.

#### Scenario: Probing in progress
- **WHEN** the probe is running
- **THEN** system SHALL display each attempted path with its result (✓ success / ✗ 404 / ⏱ timeout) as they complete

### Requirement: Authentication configuration modal
The system SHALL present an authentication configuration UI when the service requires credentials.

#### Scenario: Show auth form on 401
- **WHEN** probe detects that authentication is needed (all paths return 401/403)
- **THEN** system SHALL display a modal with auth type selection (账号密码登录 / 直接填 Token / API Key / Basic Auth) and corresponding input fields

#### Scenario: Login and retry
- **WHEN** user fills in login endpoint, username, password and clicks "登录并继续探测"
- **THEN** system SHALL call the backend to authenticate, then re-probe with the obtained token, showing progress

### Requirement: Interface preview table
The system SHALL display discovered API operations in a table with checkboxes for selection.

#### Scenario: Preview discovered operations
- **WHEN** probe succeeds and OpenAPI is parsed
- **THEN** system SHALL show a table with columns: checkbox, HTTP method, path, suggested name (editable input), and description; noise endpoints SHALL be unchecked by default

#### Scenario: Edit Node name inline
- **WHEN** user clicks on a suggested name field in the preview table
- **THEN** user SHALL be able to type a custom name which will be used as the Node's display_name

### Requirement: Shared fields configuration
The system SHALL provide inputs for fields shared across all imported Nodes: category selector, tags input, and visibility selector.

#### Scenario: Set shared category
- **WHEN** user selects category "NLP" from the dropdown
- **THEN** all imported Nodes SHALL receive category "NLP"

### Requirement: Batch import action
The system SHALL provide an "导入选中" button that creates all selected Nodes.

#### Scenario: Successful batch import
- **WHEN** user has selected 4 operations and clicks "导入选中 (4)"
- **THEN** system SHALL call the batch import API and show a success message with links to the created Nodes

#### Scenario: Partial failure
- **WHEN** one of the batch imports fails (e.g., name conflict)
- **THEN** system SHALL show which Nodes succeeded and which failed with error details

### Requirement: Fallback options when probe fails
The system SHALL present three fallback options when auto-probe discovers no spec.

#### Scenario: Show fallback UI
- **WHEN** all probe paths return 404 and no spec is found
- **THEN** system SHALL display three options: (1) manually specify a spec path and re-probe, (2) upload an OpenAPI spec file, (3) go to manual Node registration page

### Requirement: Spec file upload interface
The system SHALL provide file upload for OpenAPI/Swagger spec files with drag-and-drop support.

#### Scenario: Upload and parse spec file
- **WHEN** user drags a `.json` or `.yaml` file into the upload area
- **THEN** system SHALL upload the file, parse it, and display the same preview table as URL-based discovery

### Requirement: Credential management in discovery flow
The system SHALL allow creating and selecting credentials during the discovery workflow, reusing existing credentials if available.

#### Scenario: Existing credential for base URL
- **WHEN** user enters a base URL that matches an existing credential's base_url
- **THEN** system SHALL offer to reuse the existing credential instead of creating a new one

#### Scenario: Create credential during auth flow
- **WHEN** user provides authentication details during discovery
- **THEN** system SHALL automatically create a `service_credential` record for future use

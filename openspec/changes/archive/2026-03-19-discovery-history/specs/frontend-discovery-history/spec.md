## ADDED Requirements

### Requirement: Discovery history list page
The system SHALL provide a history list page at `/discover` showing all past discovery sessions for the current user.

#### Scenario: Navigate to discover
- **WHEN** user clicks "发现" in the navigation bar or visits `/discover`
- **THEN** system SHALL display a list of past discovery sessions with columns: 创建时间, 来源 URL / 文件上传, 发现接口数, 已导入数, 状态; and a "新建发现" button

#### Scenario: Empty state
- **WHEN** user has no discovery sessions
- **THEN** system SHALL display an empty state with a prompt to start the first discovery and a visible "新建发现" button

### Requirement: New discovery wizard accessible via route
The system SHALL host the three-step discovery wizard at `/discover/new`.

#### Scenario: Click new discovery
- **WHEN** user clicks "新建发现" button on the history list page
- **THEN** system SHALL navigate to `/discover/new` showing the existing three-step wizard

#### Scenario: Wizard completion redirects to history
- **WHEN** import succeeds in the wizard
- **THEN** system SHALL navigate to `/discover` (history list), where the new session SHALL appear at the top

### Requirement: Discovery session detail page
The system SHALL provide a detail page at `/discover/:id` showing a specific session's results.

#### Scenario: View session detail
- **WHEN** user clicks a session row on the history list
- **THEN** system SHALL navigate to `/discover/:id` showing the session metadata (URL, status, date) and a table of all imported Nodes with links to their detail pages

#### Scenario: Status badge on list
- **WHEN** session has status "failed"
- **THEN** system SHALL display a red badge; "completed" SHALL display green; "probing" SHALL display a spinner

### Requirement: Navigation active state for discover routes
The system SHALL highlight the "发现" nav link as active for all `/discover/*` routes.

#### Scenario: Active nav on sub-routes
- **WHEN** user is on `/discover/new` or `/discover/:id`
- **THEN** the "发现" link in the top nav SHALL have the active (indigo) style

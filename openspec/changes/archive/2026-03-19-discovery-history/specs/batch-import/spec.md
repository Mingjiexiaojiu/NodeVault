## MODIFIED Requirements

### Requirement: Batch create Nodes
The system SHALL create all selected Node drafts in a single batch operation, with an optional `session_id` to link Nodes to a discovery session.

#### Scenario: Import with session_id
- **WHEN** user confirms import with 4 selected operations and a `session_id` is present
- **THEN** system SHALL create 4 Nodes with `discovery_session_id` set to the given session's ID, and update the session's `imported_count` and `status` to `"completed"`

#### Scenario: Import without session_id (backward compatible)
- **WHEN** batch import is called without a `session_id`
- **THEN** system SHALL create Nodes with `discovery_session_id = NULL`, maintaining full backward compatibility

#### Scenario: Name conflict during import
- **WHEN** a generated Node name conflicts with an existing Node in the same namespace
- **THEN** system SHALL report the conflict and require user to change the name before proceeding

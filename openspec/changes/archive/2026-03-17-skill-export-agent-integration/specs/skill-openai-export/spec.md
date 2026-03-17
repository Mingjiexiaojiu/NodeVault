## ADDED Requirements

### Requirement: Export single Node as OpenAI Function Calling format
The system SHALL export a single Node (with its active version) as an OpenAI Function Calling tool descriptor `{type: "function", function: {name, description, parameters}}`.
Node name SHALL be sanitized to `[a-z0-9_]` and truncated to 64 characters.
Description SHALL be truncated to 1024 characters and append tag information if present.

#### Scenario: Export active node with valid schema
- **WHEN** `GET /api/v1/nodes/{id}/export/openai` is called with a valid node ID
- **THEN** response contains valid OpenAI tool JSON with `type: "function"` and `function.parameters` equal to the node's active version `input_schema`

#### Scenario: Node name contains special characters
- **WHEN** node name contains uppercase letters, hyphens, or spaces
- **THEN** exported function name replaces all non-`[a-z0-9_]` characters with `_` and is truncated to 64 characters

#### Scenario: Export batch nodes as OpenAI tools array
- **WHEN** `GET /api/v1/export/batch?format=openai&ids=id1,id2,id3` is called
- **THEN** response contains `{"tools": [...]}` with one entry per requested node that has an active version

#### Scenario: Node has no active version
- **WHEN** `GET /api/v1/nodes/{id}/export/openai` is called for a node with no active version
- **THEN** response returns HTTP 404 with error message indicating no active version available

## ADDED Requirements

### Requirement: Parse OpenAPI operations into Node drafts
The system SHALL parse an OpenAPI document and generate a list of Node draft objects, each representing one API operation.

#### Scenario: Map operation to Node draft
- **WHEN** an OpenAPI document contains `POST /translate` with operationId `translateText`, summary, requestBody schema, and response schema
- **THEN** system SHALL generate a draft with suggested name derived from operationId, display_name from summary, input_schema from requestBody, output_schema from 200 response, endpoint as relative path, and method as POST

#### Scenario: Operation without operationId
- **WHEN** an operation has no operationId
- **THEN** system SHALL generate a suggested name from `{method}_{path}` in snake_case (e.g., `post_translate`)

### Requirement: Filter noise endpoints
The system SHALL identify and default-exclude health check, metrics, and documentation endpoints from the draft list.

#### Scenario: Health endpoint filtered
- **WHEN** the OpenAPI document includes `GET /health` and `GET /metrics`
- **THEN** these operations SHALL appear in the draft list but with `selected: false` by default

#### Scenario: User can override filter
- **WHEN** a filtered endpoint is shown as unchecked in the preview
- **THEN** user SHALL be able to manually check it for inclusion

### Requirement: User customizes Node names
The system SHALL present suggested Node names but allow users to override each name before import.

#### Scenario: Custom name provided
- **WHEN** user changes the suggested name `translate_text` to `智能翻译`
- **THEN** the created Node SHALL use `智能翻译` as its display_name, and the system SHALL generate a valid snake_case `name` field

### Requirement: Batch create Nodes
The system SHALL create all selected Node drafts in a single batch operation, with an optional `session_id` to link Nodes to a discovery session.

#### Scenario: Import 4 out of 5 discovered operations
- **WHEN** user selects 4 of 5 discovered operations and confirms import
- **THEN** system SHALL create 4 Nodes, each with runtime_config containing the relative endpoint path and the shared credential_id; each Node SHALL have version `1.0.0`

#### Scenario: Import with session_id
- **WHEN** user confirms import with 4 selected operations and a `session_id` is present
- **THEN** system SHALL create 4 Nodes with `discovery_session_id` set to the given session's ID, and update the session's `imported_count` and `status` to `"completed"`

#### Scenario: Import without session_id (backward compatible)
- **WHEN** batch import is called without a `session_id`
- **THEN** system SHALL create Nodes with `discovery_session_id = NULL`, maintaining full backward compatibility

#### Scenario: Name conflict during import
- **WHEN** a generated Node name conflicts with an existing Node in the same namespace
- **THEN** system SHALL report the conflict and require user to change the name before proceeding

### Requirement: Support spec file upload
The system SHALL accept uploaded OpenAPI spec files (JSON and YAML) as an alternative to URL probing.

#### Scenario: Upload JSON spec file
- **WHEN** user uploads a valid OpenAPI 3.x JSON file and provides a base_url
- **THEN** system SHALL parse it and present the same Node draft preview as URL-based discovery

#### Scenario: Upload YAML spec file
- **WHEN** user uploads a valid OpenAPI YAML file
- **THEN** system SHALL parse it identically to JSON format

#### Scenario: Invalid spec file
- **WHEN** user uploads a file that is not valid OpenAPI
- **THEN** system SHALL return an error indicating the file could not be parsed as OpenAPI 2.x or 3.x

### Requirement: Record import source metadata
The system SHALL record the discovery source on each imported Node for traceability.

#### Scenario: Node metadata after import
- **WHEN** a Node is created via batch import from `https://api.example.com` discovered at `/openapi.json`
- **THEN** the Node's metadata SHALL include `source_url`, `spec_path`, and `discovered_at` fields

### Requirement: Shared configuration for batch import
The system SHALL allow users to set common fields (category, tags, visibility) that apply to all Nodes in the import batch.

#### Scenario: Set shared category and tags
- **WHEN** user sets category to "NLP" and tags to ["翻译", "多语言"] before importing
- **THEN** all imported Nodes SHALL have category "NLP" and tags ["翻译", "多语言"]

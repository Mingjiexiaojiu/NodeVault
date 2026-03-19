## ADDED Requirements

### Requirement: Node runtime_config supports credential_id
The system SHALL support an optional `credential_id` field in Node's runtime_config. When present, the system SHALL use the referenced credential for authentication and combine the credential's `base_url` with the Node's relative `endpoint` to form the full request URL.

#### Scenario: Node created with credential_id
- **WHEN** a Node is created via batch import with `credential_id` referencing a valid credential
- **THEN** the Node's runtime_config SHALL contain `credential_id` and a relative `endpoint` (e.g., `/translate` instead of `https://api.xxx.com/translate`)

#### Scenario: Node without credential_id (backward compatible)
- **WHEN** an existing Node has no `credential_id` in its runtime_config
- **THEN** the system SHALL continue using the full `endpoint` URL and the existing `auth` config from runtime_config (no behavior change)

### Requirement: Batch create Nodes endpoint
The system SHALL provide `POST /api/v1/nodes/batch` endpoint that accepts an array of Node definitions and creates them all in a single transaction.

#### Scenario: Batch create succeeds
- **WHEN** authenticated user submits an array of 4 valid Node definitions with a shared credential_id
- **THEN** the system SHALL create all 4 Nodes and their initial versions in one transaction, returning 201 with an array of NodeResponse objects

#### Scenario: Batch create with name conflict
- **WHEN** one of the batch items has a name that conflicts with an existing Node in the namespace
- **THEN** the system SHALL reject the entire batch with 409, indicating which name(s) conflict

#### Scenario: Batch create atomic rollback
- **WHEN** any Node in the batch fails validation
- **THEN** the system SHALL rollback the entire transaction (no partial creates)

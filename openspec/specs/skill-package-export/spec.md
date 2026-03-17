## ADDED Requirements

### Requirement: Download Node as Skill Package ZIP
The system SHALL generate and return a ZIP file when `GET /api/v1/nodes/{id}/export/skill` is called.
The ZIP SHALL contain: `skill.yaml` (metadata + I/O schema), `skill.py` (executable via NodeVault SDK), `README.md` (usage instructions), `tests/test_skill.py` (example test cases).
ZIP generation SHALL use Python's standard `zipfile` module and stream the response in memory without writing temporary files to disk.

#### Scenario: Download skill package for active node
- **WHEN** `GET /api/v1/nodes/{id}/export/skill` is called for an active node
- **THEN** response has `Content-Type: application/zip`, `Content-Disposition: attachment; filename="<node_name>.zip"`, and a valid ZIP containing all four required files

#### Scenario: skill.yaml contains correct metadata
- **WHEN** ZIP is downloaded and `skill.yaml` is read
- **THEN** it contains `name`, `version`, `description`, `category`, `tags`, `entrypoint: skill.execute`, and `input`/`output` sections derived from the node's active version schema

#### Scenario: skill.py uses NodeVault SDK
- **WHEN** ZIP is downloaded and `skill.py` is read
- **THEN** it imports `NodeVaultClient` from `nodevault`, calls `vault.invoke("<node_name>", input_data={...})`, and all function parameters match the node's `input_schema.properties`

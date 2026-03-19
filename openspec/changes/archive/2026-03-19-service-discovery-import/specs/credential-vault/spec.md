## ADDED Requirements

### Requirement: Create encrypted credential
The system SHALL allow users to create a credential record for a target service, encrypting sensitive fields (password, static token, API key) with AES-256-GCM before storage.

#### Scenario: Create bearer_login credential
- **WHEN** user provides base_url, login_endpoint, username, password, and token_json_path
- **THEN** system SHALL encrypt the username and password, store them in `service_credentials`, and return the credential ID and metadata (without plaintext secrets)

#### Scenario: Create bearer_static credential
- **WHEN** user provides base_url and a static bearer token
- **THEN** system SHALL encrypt the token and store it in `service_credentials`

#### Scenario: Create api_key credential
- **WHEN** user provides base_url, API key header name, and API key value
- **THEN** system SHALL encrypt the API key value and store it

#### Scenario: Create basic auth credential
- **WHEN** user provides base_url, username, and password for HTTP Basic auth
- **THEN** system SHALL encrypt the credentials and store them

### Requirement: List credentials
The system SHALL allow users to list their own credential records, showing metadata without revealing plaintext secrets.

#### Scenario: List user credentials
- **WHEN** user requests their credential list
- **THEN** system SHALL return each credential's id, name, base_url, auth_type, created_at, and last_used_at, with sensitive fields masked (e.g., username shown, password hidden)

### Requirement: Delete credential
The system SHALL allow users to delete their own credential records.

#### Scenario: Delete credential clears Node references
- **WHEN** user deletes a credential that is referenced by Nodes via credential_id
- **THEN** system SHALL set those Nodes' credential_id to null (not delete the Nodes) and delete the credential record

### Requirement: Token caching
The system SHALL cache access tokens obtained from target services in `credential_token_cache` with an expiration timestamp.

#### Scenario: Token cached after login
- **WHEN** system obtains a token by logging into a target service
- **THEN** system SHALL store the token and its expiration time in the cache, associated with the credential ID

#### Scenario: Cached token returned when valid
- **WHEN** a cached token exists and has not expired (with 60-second safety margin)
- **THEN** system SHALL return the cached token without re-authenticating

### Requirement: Automatic token refresh
The system SHALL automatically refresh expired tokens during invoke by re-authenticating with stored credentials.

#### Scenario: Token expired, auto-refresh succeeds
- **WHEN** an invoke operation needs a token but the cached token is expired
- **THEN** system SHALL decrypt the credential, authenticate against the target service, cache the new token, and proceed with the invoke

#### Scenario: Auto-refresh fails
- **WHEN** the target service rejects the stored credentials during auto-refresh
- **THEN** system SHALL return an error indicating authentication failure and suggest the user update their credentials

#### Scenario: Token rejected mid-request, retry once
- **WHEN** the target service returns 401 during an invoke even though the token was not expired
- **THEN** system SHALL force-refresh the token once and retry the request; if still 401, return an authentication error

### Requirement: Encryption key management
The system SHALL read the AES-256 encryption key from environment variable `CREDENTIAL_ENCRYPT_KEY`. The key MUST be exactly 32 bytes (provided as 64-char hex or 44-char base64).

#### Scenario: Missing encryption key
- **WHEN** `CREDENTIAL_ENCRYPT_KEY` is not set and a credential operation is attempted
- **THEN** system SHALL return an error indicating the encryption key is not configured

#### Scenario: Invalid encryption key format
- **WHEN** `CREDENTIAL_ENCRYPT_KEY` is set but is not a valid 32-byte key
- **THEN** system SHALL fail fast at startup with a clear error message

### Requirement: Credential secrets never returned in API responses
The system SHALL never include plaintext passwords, tokens, or API keys in any API response.

#### Scenario: Create credential response
- **WHEN** a credential is successfully created
- **THEN** the response SHALL include the credential ID, name, base_url, auth_type, and created_at, but SHALL NOT include password, token, or API key values

#### Scenario: Get credential detail
- **WHEN** user requests a specific credential's details
- **THEN** the response SHALL show the username (if applicable) but SHALL mask or omit all secret fields

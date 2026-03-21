## ADDED Requirements

### Requirement: Service discovery page
The system SHALL provide a dedicated frontend page at `/discover/new` for service discovery and batch import (previously at `/discover`).

#### Scenario: Navigate to discovery wizard
- **WHEN** user clicks "æ–°å»ºå‘ç°" on the history list or visits `/discover/new`
- **THEN** system SHALL display the three-step wizard with probe URL input

#### Scenario: Redirect bare /discover to history list
- **WHEN** user visits `/discover`
- **THEN** system SHALL display the discovery session history list page, NOT the wizard

### Requirement: Probe progress visualization
The system SHALL show real-time progress while probing spec paths.

#### Scenario: Probing in progress
- **WHEN** the probe is running
- **THEN** system SHALL display each attempted path with its result (âœ“ success / âœ— 404 / â± timeout) as they complete

### Requirement: Authentication configuration modal
The system SHALL present an authentication configuration UI when the service requires credentials.

#### Scenario: Show auth form on 401
- **WHEN** probe detects that authentication is needed (all paths return 401/403)
- **THEN** system SHALL display a modal with auth type selection (è´¦å·å¯†ç ç™»å½• / ç›´æ¥å¡« Token / API Key / Basic Auth) and corresponding input fields

#### Scenario: Login and retry
- **WHEN** user fills in login endpoint, username, password and clicks "ç™»å½•å¹¶ç»§ç»­æ¢æµ‹"
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
The system SHALL provide an "å¯¼å…¥é€‰ä¸­" button that creates all selected Nodes and updates the discovery session.

#### Scenario: Successful batch import with session
- **WHEN** user has selected 4 operations and clicks "å¯¼å…¥é€‰ä¸­ (4)"
- **THEN** system SHALL call the batch import API with the current `session_id`, and on success navigate to `/discover` (history list)

#### Scenario: Partial failure
- **WHEN** one of the batch imports fails (e.g., name conflict)
- **THEN** system SHALL show which Nodes succeeded and which failed with error details

### Requirement: Session created at probe start
The system SHALL create a `DiscoverySession` record when the user initiates a probe or uploads a spec file.

#### Scenario: Create session before probe
- **WHEN** user clicks "å¼€å§‹æ¢æµ‹" with a base URL
- **THEN** system SHALL call `POST /discovery/sessions` to create a session with `status: "probing"` and return a `session_id`

#### Scenario: Create session for file upload
- **WHEN** user uploads a spec file instead of entering a URL
- **THEN** system SHALL create a session with `source: "upload"` and an empty `base_url`

### Requirement: Session status transitions
The system SHALL update session status to reflect the outcome of each stage.

#### Scenario: Probe succeeds
- **WHEN** probe finds at least one valid OpenAPI path
- **THEN** system SHALL update session to `status: "found"` and record `spec_url` and `total_operations`

#### Scenario: Probe fails
- **WHEN** all probe paths return non-2xx responses and no spec is found
- **THEN** system SHALL update session to `status: "failed"`

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

### Requirement: ·şÎñ·¢ÏÖÁ÷³ÌÒ³Ãæ
Ç°¶Ë SHALL ÔÚ /discovery Ò³ÃæÌá¹©ÍêÕûµÄ·şÎñ·¢ÏÖÁ÷³Ì£¬µ¼Èë½ÚµãÊ±Ê¹ÓÃ¶¯Ì¬·ÖÀàÑ¡ÔñÆ÷£¨´Ó GET /api/v1/categories ¼ÓÔØ£©£¬Ìæ´ú¾ÉµÄ NodeType Ã¶¾ÙÀàĞÍÑ¡ÔñÆ÷¡£

### Requirement: ÖØ¸´ URL ¼ì²âÓëÌáÊ¾
ÔÚÓÃ»§ÊäÈë base_url µã»÷¡¸Ì½²â¡¹Ö®Ç°£¬Ç°¶Ë SHALL ¼ì²â¸Ã URL ÊÇ·ñÒÑ±»×¢²á¹ı£¬²¢¸ø³ö½»»¥ÌáÊ¾¡£

#### Scenario: URL ÒÑ×¢²á¹ı
- **WHEN** ÏµÍ³¼ì²âµ½¸Ã base_url ÒÑÓĞ×¢²á½Úµã
- **THEN** Ç°¶Ë SHALL µ¯³ö¶Ô»°¿òÌáÊ¾£¬Ìá¹©¡¸µü´ú¸üĞÂ¡¹¡¢¡¸ÖØĞÂµ¼Èë¡¹¡¢¡¸È¡Ïû¡¹Èı¸öÑ¡Ïî

### Requirement: µü´ú±È¶Ô²îÒìÊÓÍ¼
µ±ÓÃ»§Ñ¡Ôñ¡¸µü´ú¸üĞÂ¡¹ºó£¬Ç°¶Ë SHALL Õ¹Ê¾ĞÂ¾ÉÌ½²â½á¹ûµÄ²îÒìÊÓÍ¼£¬´ø×´Ì¬ badge£¨new ÂÌ/updated »Æ/imported »Ò/removed ºì£©¡£

### Requirement: Ì½²âÊ§°ÜÊ±Õ¹Ê¾½á¹¹»¯´íÎóĞÅÏ¢
Ç°¶Ë SHALL ¸ù¾İ ProbeResult.error_type Õ¹Ê¾¶ÔÓ¦µÄÓÃ»§ÓÑºÃÌáÊ¾ºÍÖØÊÔ°´Å¥¡£

## Requirements

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

#### Scenario: Import completes
- **WHEN** user confirms import and batch creation succeeds
- **THEN** system SHALL update session to `status: "completed"` and set `imported_count` to the number of created Nodes

### Requirement: Node linked to its discovery session
The system SHALL associate each imported Node with the session that produced it.

#### Scenario: Node has session FK after import
- **WHEN** a Node is created through the discovery import flow with a `session_id`
- **THEN** the Node record SHALL have `discovery_session_id` set to that session's ID

#### Scenario: Manually registered Node has no session link
- **WHEN** a Node is created manually via `/nodes/new`
- **THEN** `discovery_session_id` SHALL be NULL

### Requirement: Session list endpoint
The system SHALL provide a paginated list of discovery sessions for the current user.

#### Scenario: List sessions
- **WHEN** user calls `GET /discovery/sessions`
- **THEN** system SHALL return sessions belonging to the current user, ordered by `created_at` descending, with fields: `id`, `base_url`, `source`, `status`, `spec_url`, `total_operations`, `imported_count`, `created_at`, `completed_at`

### Requirement: Session detail endpoint
The system SHALL provide details of a single session including its linked Nodes.

#### Scenario: Get session with imported nodes
- **WHEN** user calls `GET /discovery/sessions/:id`
- **THEN** system SHALL return the session metadata plus a list of linked Node summaries (`id`, `name`, `display_name`, `source_path`, `status`)

### Requirement: µü´ú·¢ÏÖÖ§³Ö£¨Í¬Ò» base_url ¶à´ÎÌ½²â£©
ÏµÍ³ SHALL Ö§³ÖÍ¬Ò» base_url µÄ¶à´ÎÌ½²â£¨µü´ú£©£¬Ã¿´ÎÌ½²â´´½¨ĞÂµÄ DiscoverySession£¬²¢¿ÉÓëÀúÊ· Session ½øĞĞ¶Ëµã±È¶Ô¡£

#### Scenario: ´´½¨µü´ú Session
- **WHEN** ÓÃ»§¶ÔÒ»¸öÒÑÓĞ Session µÄ base_url ÔÙ´Î·¢ÆğÌ½²â
- **THEN** ÏµÍ³ SHALL ´´½¨ĞÂµÄ DiscoverySession£¬base_url ÏàÍ¬£¬session_id ²»Í¬£»¾É Session ±£Áô²»±ä

#### Scenario: ²éÑ¯Í¬Ò» base_url µÄÀúÊ· Sessions
- **WHEN** µ÷ÓÃ `GET /api/v1/discovery/sessions?base_url={url}`
- **THEN** ÏµÍ³ SHALL ·µ»Ø¸Ã base_url ¶ÔÓ¦µÄËùÓĞ DiscoverySession£¬°´ created_at µ¹ĞòÅÅÁĞ

### Requirement: ¶Ëµã±È¶Ô API
ÏµÍ³ SHALL Ìá¹© `POST /api/v1/discovery/sessions/{session_id}/compare` ¶Ëµã£¬½ÓÊÜ `{"previous_session_id": "<UUID>"}` body£¬±È½ÏÁ½´ÎÌ½²âµÄ endpoint ²îÒì¡£

#### Scenario: ±È¶Ô·µ»Ø²îÒìÁĞ±í
- **WHEN** µ÷ÓÃ compare ½Ó¿Ú£¬Ìá¹©ĞÂ¾ÉÁ½¸ö session_id
- **THEN** ÏµÍ³ SHALL ÒÔ path+method ×÷ÎªÎ¨Ò»±êÊ¶½øĞĞÆ¥Åä£¬·µ»Øº¬ new/imported/updated/removed ×´Ì¬µÄÊı×é

#### Scenario: previous_session_id ²»´æÔÚ
- **WHEN** Ìá¹©µÄ previous_session_id ²»´æÔÚ
- **THEN** ÏµÍ³ SHALL ·µ»Ø 404£¬message Îª"ÀúÊ··¢ÏÖ»á»°²»´æÔÚ"

### Requirement: µü´úµ¼ÈëÖ´ĞĞ API
ÏµÍ³ SHALL Ìá¹© `POST /api/v1/discovery/sessions/{session_id}/iterate` ¶Ëµã£¬¸ù¾İÓÃ»§Ñ¡ÔñµÄ actions Ö´ĞĞ´´½¨/¸üĞÂ/Ìø¹ı²Ù×÷¡£

#### Scenario: Ö´ĞĞµü´úµ¼Èë
- **WHEN** µ÷ÓÃ iterate ½Ó¿Ú£¬body º¬ actions Êı×é
- **THEN** ÏµÍ³ SHALL ¶Ô import Ö´ĞĞ´´½¨ĞÂ Node£¬¶Ô update ÔÚÒÑÓĞ Node ÉÏ´´½¨ĞÂ NodeVersion£¬·µ»ØÖ´ĞĞ±¨¸æ `{"imported": N, "updated": N, "skipped": N}`

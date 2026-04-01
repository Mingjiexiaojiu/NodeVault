## ADDED Requirements

### Requirement: User can view a list of all nodes
The system SHALL display all accessible nodes in a paginated table/card list.

#### Scenario: Default node list loads
- **WHEN** user navigates to /nodes
- **THEN** a list of nodes from GET /api/v1/nodes is displayed, showing name, type, status, and creation date

#### Scenario: List shows empty state
- **WHEN** no nodes exist for the user's namespace
- **THEN** an empty state illustration and "æš‚æ— èŠ‚ç‚¹ï¼Œç«‹å³æ³¨å†Œç¬¬ä¸€ä¸ª" button is shown

### Requirement: User can filter nodes by type and status
The system SHALL provide filter controls above the node list.

#### Scenario: Filter by node type
- **WHEN** user selects a type from the type dropdown (e.g., "tool")
- **THEN** list refreshes with query param `?type=tool` and only matching nodes are shown

#### Scenario: Filter by status
- **WHEN** user selects status "active" from the status dropdown
- **THEN** list refreshes with `?status=active` and only active nodes are shown

#### Scenario: Clear filters
- **WHEN** user clicks "é‡ç½®ç­›é€‰"
- **THEN** all filter dropdowns reset and full list is reloaded

### Requirement: Node list supports pagination
The system SHALL paginate the node list with configurable page size.

#### Scenario: Navigate to next page
- **WHEN** there are more nodes than the current page size (default 20)
- **THEN** pagination controls are shown; clicking "ä¸‹ä¸€é¡µ" loads the next page

### Requirement: Node list links to detail page
Each node row SHALL have a clickable area leading to the node detail page.

#### Scenario: Click node name to view detail
- **WHEN** user clicks a node's name or "æŸ¥çœ‹è¯¦æƒ…" link
- **THEN** user is navigated to /nodes/:id

### Requirement: ½ÚµãÁĞ±íÕ¹Ê¾ÓëÉ¸Ñ¡
Ç°¶Ë SHALL ÔÚ /nodes Ò³ÃæÕ¹Ê¾½ÚµãÁĞ±í£¬Ö§³Ö°´·ÖÀà¡¢×´Ì¬¡¢¿É¼ûĞÔµÈÌõ¼şÉ¸Ñ¡¡£

#### Scenario: ·ÖÀàÉ¸Ñ¡Ìæ´úÀàĞÍÉ¸Ñ¡
- **WHEN** ÓÃ»§´ò¿ª½ÚµãÁĞ±íÒ³Ãæ
- **THEN** É¸Ñ¡ÇøÓò SHALL Õ¹Ê¾¡¸·ÖÀà¡¹ÏÂÀ­£¬Ñ¡Ïî´Ó `GET /api/v1/categories` ¶¯Ì¬¼ÓÔØ£¬Ñ¡Ôñºó´« category_id ²ÎÊıµ½ºó¶Ë²éÑ¯½Ó¿Ú
- **AND** ²»ÔÙÏÔÊ¾¾ÉµÄ¡¸ÀàĞÍ¡¹É¸Ñ¡ÏÂÀ­£¨NodeType Ã¶¾Ù£©

#### Scenario: ½Úµã¿¨Æ¬Õ¹Ê¾·ÖÀà±êÇ©
- **WHEN** ½ÚµãÁĞ±íäÖÈ¾½Úµã¿¨Æ¬ / ±í¸ñĞĞ
- **THEN** Ã¿¸ö½Úµã SHALL Õ¹Ê¾ÆäËùÊô·ÖÀàµÄ display_name ×÷Îª±êÇ©£¨badge£©£¬Ìæ´úÔ­ÓĞµÄ type ±êÇ©


---

## Changes from ux-naming-refactor

## MODIFIED Requirements

### Requirement: èŠ‚ç‚¹å¡ç‰‡å±•ç¤ºåˆ†ç±»æ ‡å’Œéƒ¨é—¨ä¿¡æ¯ï¼ˆæ›´æ–°ï¼‰
- **WHEN** èŠ‚ç‚¹åˆ—è¡¨æ¸²æŸ“èŠ‚ç‚¹å¡ç‰‡ / åˆ—è¡¨è¡Œ
- **THEN** æ¯ä¸ªèŠ‚ç‚¹ SHALL å±•ç¤ºå¯¹åº”ç±»åˆ«çš„ display_name ä½œä¸º"ç±»åˆ«"æ ‡ç­¾ï¼ˆbadgeï¼‰ï¼Œéƒ¨é—¨ä¿¡æ¯ SHALL å±•ç¤ºä¸º"ç»„ç»‡åç§° / å›¢é˜Ÿåç§°"æ ¼å¼ï¼ˆæ›¿ä»£åŸ department_slugï¼‰

#### Scenario: èŠ‚ç‚¹å¡ç‰‡å±•ç¤ºç»„ç»‡å’Œå›¢é˜Ÿ
- **WHEN** èŠ‚ç‚¹å…³è”äº†æŸä¸ªå›¢é˜Ÿ
- **THEN** èŠ‚ç‚¹å¡ç‰‡ SHALL æ˜¾ç¤ºè¯¥å›¢é˜Ÿæ‰€å±ç»„ç»‡åå’Œå›¢é˜Ÿåï¼ˆå¦‚"äººå·¥æ™ºèƒ½éƒ¨ / è§†è§‰ç®—æ³•å›¢é˜Ÿ"ï¼‰

#### Scenario: èŠ‚ç‚¹æœªå…³è”å›¢é˜Ÿ
- **WHEN** èŠ‚ç‚¹æœªå…³è”ä»»ä½•å›¢é˜Ÿ
- **THEN** èŠ‚ç‚¹å¡ç‰‡ SHALL åœ¨éƒ¨é—¨ä½ç½®æ˜¾ç¤º"â€”"

### Requirement: User can filter nodes by departmentï¼ˆæ›´æ–°ï¼‰
å‰ç«¯ SHALL å°†åŸæŒ‰ department_slug ç­›é€‰æ”¹ä¸ºæŒ‰ç»„ç»‡åç§°å’Œå›¢é˜Ÿåç§°ç­›é€‰ã€‚

#### Scenario: æŒ‰ç»„ç»‡ç­›é€‰èŠ‚ç‚¹
- **WHEN** ç”¨æˆ·åœ¨ç­›é€‰æ é€‰æ‹©æŸä¸ªç»„ç»‡
- **THEN** åˆ—è¡¨ SHALL åªæ˜¾ç¤ºè¯¥ç»„ç»‡ä¸‹æ‰€æœ‰å›¢é˜Ÿçš„èŠ‚ç‚¹

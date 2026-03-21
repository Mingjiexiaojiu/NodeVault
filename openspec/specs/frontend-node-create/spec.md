## ADDED Requirements

### Requirement: User can register a new node via form
The system SHALL provide a form page at /nodes/new for registering a new node via POST /api/v1/nodes. The form SHALL include a Skill selectorï¼ˆä¸‹æ‹‰é€‰æ‹©å·²æœ‰ Skillï¼‰and a `usage_hint` textareaï¼ˆä½¿ç”¨åœºæ™¯æè¿°ï¼Œé€‰å¡«ï¼Œæœ€é•¿ 500 å­—ç¬¦ï¼‰ã€‚

#### Scenario: Successful node creation
- **WHEN** user fills in all required fields (name, version, type, runtime.endpoint, runtime.method, input_schema, output_schema) and clicks "æ³¨å†ŒèŠ‚ç‚¹"
- **THEN** API POST /api/v1/nodes is called, and on success user is redirected to the new node's detail page

#### Scenario: Validation prevents invalid node name
- **WHEN** user enters a name that doesn't match pattern `^[a-z][a-z0-9_]{2,63}$`
- **THEN** inline validation shows: "åç§°é¡»ä¸ºå°å†™å­—æ¯ã€æ•°å­—ã€ä¸‹åˆ’çº¿ï¼Œ3-64ä½ï¼Œä»¥å­—æ¯å¼€å¤´"

#### Scenario: Duplicate node name error
- **WHEN** API returns 409
- **THEN** page shows error: "è¯¥å‘½åç©ºé—´ä¸‹å·²å­˜åœ¨åŒåèŠ‚ç‚¹"

#### Scenario: Skill selector loads existing Skills
- **WHEN** user opens the Skill selector dropdown
- **THEN** ç³»ç»Ÿ SHALL è°ƒç”¨ GET /api/v1/skills å¹¶å±•ç¤º Skill åˆ—è¡¨ï¼Œå«"ä¸å½’å±ä»»ä½•æŠ€èƒ½é›†"é€‰é¡¹

#### Scenario: usage_hint å­—ç¬¦æ•°æç¤º
- **WHEN** ç”¨æˆ·åœ¨ usage_hint è¾“å…¥æ¡†ä¸­è¾“å…¥å†…å®¹
- **THEN** è¡¨å• SHALL å®æ—¶æ˜¾ç¤ºå‰©ä½™å¯è¾“å…¥å­—ç¬¦æ•°ï¼ˆ500 - å·²è¾“å…¥å­—ç¬¦æ•°ï¼‰

### Requirement: èŠ‚ç‚¹ç¼–è¾‘é¡µæ”¯æŒæ›´æ–° Skill å’Œ usage_hint
The system SHALL allow updating `skill_id` and `usage_hint` on the node edit pageï¼ˆ`/nodes/{id}/edit` æˆ–è¯¦æƒ…é¡µå†…ç¼–è¾‘ï¼‰ã€‚

#### Scenario: åˆ‡æ¢ Skill æˆåŠŸ
- **WHEN** ç”¨æˆ·åœ¨ç¼–è¾‘é¡µå°†èŠ‚ç‚¹ä» Skill A æ”¹ä¸º Skill B å¹¶ä¿å­˜
- **THEN** ç³»ç»Ÿ SHALL è°ƒç”¨ PATCH /api/v1/nodes/{id}ï¼Œè¿”å›æˆåŠŸåé¡µé¢æ˜¾ç¤ºæ–°çš„æŠ€èƒ½é›†åç§°

#### Scenario: usage_hint ä¸ºç©ºçš„èŠ‚ç‚¹æ˜¾ç¤ºæé†’
- **WHEN** èŠ‚ç‚¹çš„ usage_hint ä¸ºç©ºä¸”å·²å½’å±æŸä¸ª Skill
- **THEN** èŠ‚ç‚¹è¯¦æƒ…é¡µ SHALL æ˜¾ç¤ºæç¤ºï¼š\"å»ºè®®å¡«å†™ä½¿ç”¨åœºæ™¯æè¿°ï¼Œä»¥æå‡ SKILL.md ç”Ÿæˆè´¨é‡\"

### Requirement: Form provides runtime configuration fields
The system SHALL show conditional runtime fields based on selected type.

#### Scenario: HTTP runtime fields appear for type=http
- **WHEN** user selects runtime type "http"
- **THEN** fields for endpoint URL and method (GET/POST/PUT/DELETE) are shown

### Requirement: Form provides JSON schema editors for input/output
The system SHALL provide a textarea-based JSON editor for input_schema and output_schema.

#### Scenario: JSON syntax validation
- **WHEN** user types invalid JSON in the input_schema or output_schema field and attempts to submit
- **THEN** submission is blocked and the field is highlighted with "æ— æ•ˆçš„ JSON æ ¼å¼"

### Requirement: Form includes tag input
The system SHALL allow users to add multiple tags as comma-separated values.

#### Scenario: Tags are parsed and submitted
- **WHEN** user types "finance,risk,aml" in the tags field
- **THEN** these are sent as the `tags` array in the request body

### Requirement: ½Úµã´´½¨±íµ¥
Ç°¶Ë SHALL Ìá¹©½Úµã´´½¨ / ±à¼­±íµ¥£¬°üº¬ËùÓĞ NodeCreate schema ÒªÇóµÄ×Ö¶Î£¬Ìá½»ºóµ÷ÓÃ POST /api/v1/nodes£¨´´½¨£©»ò PATCH /api/v1/nodes/{id}£¨±à¼­£©¡£

#### Scenario: ·ÖÀàÑ¡ÔñÆ÷Ìæ´úÔ­ÓĞ type ÏÂÀ­
- **WHEN** ÓÃ»§´ò¿ª½Úµã´´½¨»ò±à¼­±íµ¥
- **THEN** ±íµ¥ SHALL ÏÔÊ¾¡¸·ÖÀà¡¹ÏÂÀ­Ñ¡ÔñÆ÷£¬Ñ¡Ïî´Ó `GET /api/v1/categories` ¶¯Ì¬¼ÓÔØ£¬Õ¹Ê¾ display_name£¬Ìá½»Ê±´« category_id£¨UUID£©
- **AND** ²»ÔÙÏÔÊ¾¾ÉµÄ¡¸ÀàĞÍ¡¹ÏÂÀ­£¨NodeType Ã¶¾Ù£©

#### Scenario: ´´½¨Ê±·ÖÀàÎª±ØÌî
- **WHEN** ÓÃ»§Î´Ñ¡Ôñ·ÖÀà¾ÍÌá½»±íµ¥
- **THEN** Ç°¶Ë SHALL ¸ßÁÁ·ÖÀà×Ö¶Î²¢ÏÔÊ¾"ÇëÑ¡Ôñ·ÖÀà"Ğ£ÑéÌáÊ¾

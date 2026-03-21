## ADDED Requirements

### Requirement: 服务发现流程页面
前端 SHALL 在 /discovery 页面提供完整的服务发现流程：输入 URL → 探测 → 查看结果 → 选择导入。

#### Scenario: 分类选择器替代类型选择器
- **WHEN** 用户在发现流程中需要为导入的节点选择分类
- **THEN** 前端 SHALL 展示动态分类下拉（从 GET /api/v1/categories 加载），替代旧的 NodeType 枚举类型选择器

## ADDED Requirements

### Requirement: 重复 URL 检测与提示
在用户输入 base_url 点击「探测」之前，前端 SHALL 检测该 URL 是否已被注册过，并给出交互提示。

#### Scenario: URL 未注册过
- **WHEN** 调用探测接口前先检查（或探测返回无重复标识）
- **THEN** 正常进入探测流程，无额外提示

#### Scenario: URL 已注册过
- **WHEN** 系统检测到该 base_url 已有注册节点
- **THEN** 前端 SHALL 弹出对话框提示"该服务已注册过 N 个节点"，提供两个选项：
  - 「迭代更新」—— 进入迭代模式，将新探测结果与旧结果比对
  - 「重新导入」—— 忽略旧数据，按全新探测处理
  - 「取消」—— 关闭对话框

### Requirement: 迭代比对差异视图
当用户选择「迭代更新」后，前端 SHALL 展示新旧探测结果的差异视图。

#### Scenario: 差异列表渲染
- **WHEN** 调用 compare API 获取比对结果
- **THEN** 前端 SHALL 以列表展示所有端点，每条带状态 badge：
  - 🟢 **new（新增）**：绿色 badge，默认勾选导入
  - ⚪ **imported（已导入）**：灰色 badge，默认不勾选
  - 🟡 **updated（已变更）**：黄色 badge，默认勾选更新，可展开查看 schema diff
  - 🔴 **removed（已移除）**：红色 badge，仅展示信息，不可操作

#### Scenario: 用户确认迭代操作
- **WHEN** 用户在差异视图中调整勾选后点击「确认导入」
- **THEN** 前端 SHALL 收集用户选择，组装 actions 数组调用 `POST /api/v1/discovery/sessions/{session_id}/iterate`
- **AND** 完成后展示执行报告（imported / updated / skipped 计数）

### Requirement: 探测失败时展示结构化错误信息
前端 SHALL 根据 ProbeResult.error_type 展示对应的用户友好提示。

#### Scenario: 各类错误渲染
- **WHEN** 探测返回 success=false
- **THEN** 前端 SHALL 展示对应错误图标和提示文案：
  - connection_refused → 🔌 图标 + "无法连接到目标服务，请确认地址和端口是否正确"
  - timeout → ⏱ 图标 + "连接超时，请确认服务是否可达"
  - dns_error → 🌐 图标 + "域名无法解析，请检查 URL 是否正确"
  - ssl_error → 🔒 图标 + "SSL 证书验证失败"
  - spec_not_found → 📄 图标 + "服务可达但未找到 OpenAPI 规范文件"
  - parse_error → ⚠️ 图标 + "规范文件格式错误，解析失败"
- **AND** 每种错误下方展示「重试」按钮

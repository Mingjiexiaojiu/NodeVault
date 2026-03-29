## Requirements

### Requirement: 凭据列表页
系统 SHALL 提供 `/credentials` 前端路由，展示当前用户名下所有凭据的列表，包括名称、base_url、auth_type、创建时间，以及测试连接和删除操作按钮。列表为空时 SHALL 显示引导用户创建凭据的空状态。

#### Scenario: 查看凭据列表
- **WHEN** 用户导航到 `/credentials` 页面
- **THEN** 页面 SHALL 调用 `GET /api/v1/credentials` 并以表格或卡片形式展示凭据列表，每行包含 name、base_url、auth_type、created_at

#### Scenario: 凭据列表为空
- **WHEN** 当前用户没有任何凭据
- **THEN** 页面 SHALL 显示空状态提示，并提供"创建凭据"按钮

---

### Requirement: 创建凭据表单
系统 SHALL 提供创建凭据的表单（抽屉或独立页面），支持 4 种 auth_type 的动态字段切换：bearer_login（login_endpoint、username、password、token_json_path、token_ttl）、bearer_static（static_token）、api_key（api_key_header、api_key_value）、basic（username、password）。所有需要输入密码/token 的字段 SHALL 使用密码输入框（隐藏明文）。

#### Scenario: 选择 bearer_login 类型
- **WHEN** 用户在表单中选择 auth_type = bearer_login
- **THEN** 表单 SHALL 显示 login_endpoint、username、password、token_json_path（可选）、token_ttl（可选）字段，隐藏其他 auth_type 专属字段

#### Scenario: 选择 api_key 类型
- **WHEN** 用户在表单中选择 auth_type = api_key
- **THEN** 表单 SHALL 显示 api_key_header（默认值 "X-API-Key"）和 api_key_value 字段

#### Scenario: 创建凭据成功
- **WHEN** 用户填写完整表单并提交
- **THEN** 系统 SHALL 调用 `POST /api/v1/credentials`，成功后刷新列表并显示成功提示，表单关闭

#### Scenario: 创建凭据失败
- **WHEN** 提交时后端返回 422 错误（字段缺失等）
- **THEN** 表单 SHALL 在对应字段下方显示错误提示，不关闭表单

---

### Requirement: 更新凭据
系统 SHALL 允许用户编辑已有凭据的 name、token_ttl，以及重新设置密码/token/api_key（可选，留空则保持原值）。不允许修改 auth_type 和 base_url。

#### Scenario: 更新凭据名称
- **WHEN** 用户修改凭据名称并保存
- **THEN** 系统 SHALL 调用 `PATCH /api/v1/credentials/{id}` 并在列表中反映更新后的名称

#### Scenario: 更新密码（留空保持原值）
- **WHEN** 用户打开编辑表单，密码字段为空（placeholder 提示"留空则不修改"），直接保存
- **THEN** 系统 SHALL 不覆盖原有加密密码

---

### Requirement: 测试凭据连接
系统 SHALL 在凭据列表和编辑表单中提供"测试连接"按钮，触发后调用后端测试接口并显示结果。

#### Scenario: 测试成功
- **WHEN** 用户点击"测试连接"，后端返回 success=true
- **THEN** 按钮区域 SHALL 显示绿色"连接成功"标识，包含延迟信息（如有）

#### Scenario: 测试失败
- **WHEN** 用户点击"测试连接"，后端返回 success=false
- **THEN** 按钮区域 SHALL 显示红色"连接失败"和错误信息（如"凭据无效"或"服务不可达"）

---

### Requirement: Node 凭据绑定选择器
系统 SHALL 在 NodeCreateView 和 NodeEditView 的表单中提供凭据绑定选择器（下拉菜单），列出当前用户的凭据列表，支持选择或置空（解绑）。NodeDetailView SHALL 展示当前绑定的凭据名称，未绑定时显示"无（将使用自动匹配）"。

#### Scenario: 创建 Node 时绑定凭据
- **WHEN** 用户在创建表单中选择一个凭据
- **THEN** NodeCreate 请求体中 SHALL 包含 `credential_id` 字段

#### Scenario: 编辑 Node 解绑凭据
- **WHEN** 用户在编辑表单中将凭据选择器设为空
- **THEN** NodeUpdate 请求体中 SHALL 包含 `credential_id: null`

#### Scenario: NodeDetailView 展示凭据绑定状态
- **WHEN** 用户查看一个已绑定凭据的 Node 详情
- **THEN** 页面 SHALL 显示绑定凭据的名称；未绑定时显示"无（将使用自动匹配）"

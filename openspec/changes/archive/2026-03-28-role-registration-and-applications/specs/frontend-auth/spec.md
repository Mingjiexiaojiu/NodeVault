## MODIFIED Requirements

### Requirement: User can register a new account
注册页面 SHALL 在基本信息填写区域之后展示"身份选择"单选区块，选项为"普通用户"（默认选中）和"申请成为主管"。

当选择"普通用户"时，页面 SHALL 显示可选的"选择部门"下拉框（从 `/api/v1/departments` 加载部门列表），该字段非必填，用户可跳过。

当选择"申请成为主管"时，部门选择区块 SHALL 隐藏，页面 SHALL 显示一行提示文字："提交后需等待管理员审批，审批期间账号可正常使用"。

注册提交后，若选择了"申请成为主管"，成功页 / 跳转前 SHALL 显示一次性提示："主管申请已提交，管理员审批通过后权限将自动升级"。

#### Scenario: 默认状态
- **WHEN** 用户打开注册页
- **THEN** 页面 SHALL 默认选中"普通用户"，部门选择框可见但为空

#### Scenario: 切换到主管申请
- **WHEN** 用户选择"申请成为主管"单选项
- **THEN** 部门选择框 SHALL 隐藏，页面 SHALL 显示主管申请提示文字

#### Scenario: 普通用户选择部门提交
- **WHEN** 用户选择"普通用户"并选择了一个部门后点击注册
- **THEN** 前端 SHALL 将 `department_id` 携带在注册请求体中

#### Scenario: 主管申请提交
- **WHEN** 用户选择"申请成为主管"后点击注册
- **THEN** 前端 SHALL 将 `requested_role: 1` 携带在注册请求体中，注册成功后显示申请提交提示

## ADDED Requirements

### Requirement: 注册页部门列表加载
注册页面 SHALL 在渲染时异步加载可用部门列表（`GET /api/v1/departments`），用于"选择部门"下拉框。加载中 SHALL 显示骨架/禁用状态，加载失败 SHALL 隐藏部门选择区块（不阻断注册流程）。

#### Scenario: 部门列表加载成功
- **WHEN** 注册页面初始化
- **THEN** 部门下拉框 SHALL 展示所有可用部门的 display_name 或 slug

#### Scenario: 部门列表加载失败
- **WHEN** 部门列表 API 请求失败
- **THEN** 部门选择区块 SHALL 隐藏，注册流程 SHALL 不受影响

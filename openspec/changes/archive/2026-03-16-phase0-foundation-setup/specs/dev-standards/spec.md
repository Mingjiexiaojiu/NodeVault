## ADDED Requirements

### Requirement: 代码格式化与检查工具
项目 SHALL 使用 Ruff 作为唯一的代码 lint 和 format 工具。行宽 SHALL 设置为 88 字符。配置 SHALL 写入 `pyproject.toml` 的 `[tool.ruff]` 节。

#### Scenario: Ruff 格式化可执行
- **WHEN** 执行 `ruff format .`
- **THEN** 所有 Python 文件 SHALL 被格式化为一致的代码风格

#### Scenario: Ruff 检查可执行
- **WHEN** 执行 `ruff check .`
- **THEN** SHALL 报告代码中的 lint 违规（如未使用的 import、变量命名问题）

### Requirement: 命名规范
项目 SHALL 遵循以下命名规范：类名使用 `PascalCase`、函数和变量使用 `snake_case`、常量使用 `UPPER_SNAKE_CASE`、API 路径使用 `kebab-case`。

#### Scenario: Python 代码命名
- **WHEN** 审查代码中的类定义
- **THEN** 类名 SHALL 为 PascalCase（如 `NodeVersion`、`Settings`）

#### Scenario: API 路径命名
- **WHEN** 审查 API 路由定义
- **THEN** URL 路径 SHALL 使用 kebab-case 或资源名复数形式（如 `/api/v1/nodes`、`/api/v1/node-versions`）

### Requirement: Git 提交规范
项目 SHALL 采用 Conventional Commits 规范。提交消息格式为 `<type>(<scope>): <description>`，type 包括：`feat`、`fix`、`refactor`、`docs`、`test`、`chore`。

#### Scenario: 合规的提交消息
- **WHEN** 开发者提交代码时使用 `feat(registry): add node version management API`
- **THEN** 该消息 SHALL 符合规范

#### Scenario: 不合规的提交消息
- **WHEN** 开发者提交代码时使用 `updated some stuff`
- **THEN** 该消息 SHALL 被视为不合规

### Requirement: 分支策略
项目 SHALL 采用以下分支模型：`main` 为生产分支（仅接受 merge request），`develop` 为开发主分支，功能分支命名为 `feature/<phase>-<description>`，修复分支命名为 `fix/<description>`。

#### Scenario: 功能分支命名
- **WHEN** 开发 Phase 1 的 Node 注册功能
- **THEN** 分支 SHALL 命名为 `feature/phase1-node-registry`

### Requirement: 测试策略
项目 SHALL 使用 pytest 作为测试框架，支持三种测试类型：单元测试（core/ 业务逻辑）、集成测试（API 端点，使用 TestClient）、E2E 测试（完整调用链路，使用 Docker）。目标代码覆盖率 SHALL 不低于 80%。

#### Scenario: 测试命令可执行
- **WHEN** 执行 `pytest tests/ --cov`
- **THEN** SHALL 运行所有测试并输出覆盖率报告

#### Scenario: conftest.py 提供基础 fixtures
- **WHEN** tests/conftest.py 被加载
- **THEN** SHALL 提供 `app`（FastAPI 测试实例）和 `client`（async TestClient）等基础 fixture

## Why

NodeVault 项目目前处于空白状态——没有代码、没有数据库、没有被定义的标准。在编写任何业务逻辑（Node 注册、调用、搜索等）之前，必须先建立整个系统的地基：**Node Schema 标准**、**项目骨架**、**开发规范**。没有这些基础，后续的 Phase 1-6 将无从发力，且容易因为缺乏约束而陷入混乱。现在是项目启动的第一步，所有后续工作都依赖于此。

## What Changes

- 制定 **Node Schema v1.0 标准**（YAML 格式），定义 Node 的完整描述、输入输出契约、运行时配置、执行策略等，作为整个系统的核心契约
- 搭建 **FastAPI 项目骨架**，包括目录结构、pyproject.toml 依赖配置、入口文件、健康检查端点
- 建立 **数据库基础设施**：PostgreSQL 连接、SQLAlchemy async session、Alembic 迁移框架初始化
- 定义 **核心 Pydantic 配置类**（Settings），统一管理环境变量
- 提供 **Docker Compose 开发环境**（PostgreSQL + Redis + MeiliSearch）
- 配置 **.env.example** 环境变量模板
- 确立 **开发规范**：Ruff lint/format、Conventional Commits、分支策略、测试策略
- 设计并冻结 **核心数据库 ER 模型**（users、namespaces、nodes、node_versions、node_tags、node_invocation_logs、workflows 等表），Phase 1 实现 ORM

## Capabilities

### New Capabilities
- `node-schema-standard`: Node Schema v1.0 YAML 标准定义，包含类型枚举、Runtime 类型、输入输出 JSON Schema 契约
- `project-skeleton`: FastAPI 项目骨架搭建，含目录结构、依赖管理、入口文件、健康检查端点
- `database-foundation`: PostgreSQL + SQLAlchemy async 连接、Alembic 迁移框架、核心 ER 模型设计
- `dev-environment`: Docker Compose 开发环境（PostgreSQL/Redis/MeiliSearch）、环境变量配置
- `dev-standards`: 代码规范（Ruff）、提交规范（Conventional Commits）、分支策略、测试策略、API 设计规范

### Modified Capabilities
<!-- 无已有能力需要修改，这是项目的第一个变更 -->

## Impact

- **代码**：从零创建 `nodevault/` 项目结构，包含 `api/`、`core/`、`models/`、`schemas/`、`database/`、`auth/`、`tests/`、`deploy/` 等目录
- **依赖**：引入 FastAPI、SQLAlchemy、Pydantic、Alembic、httpx、structlog 等核心依赖
- **基础设施**：需要 Docker 运行 PostgreSQL 16、Redis 7、MeiliSearch v1.7
- **API**：增加 `GET /healthz` 健康检查端点（Phase 0 唯一的可访问端点）
- **数据库**：确定 ER 模型设计（表结构在 Phase 1 实现，但 Phase 0 必须冻结设计）
- **团队**：所有后续开发者必须遵循此阶段确立的代码规范和提交规范

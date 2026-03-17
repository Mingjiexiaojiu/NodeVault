## Context

NodeVault 是一个从零开始的企业级 AI 能力注册中心项目。当前状态：仅有设计文档（Design/ 目录），无任何可运行代码。Phase 0 是项目的第一个实施阶段，需要在不写业务逻辑的前提下，建立整个系统可持续发展的技术基础。

核心约束：
- Python 3.11+，FastAPI 作为 Web 框架
- PostgreSQL 作为主数据库，SQLAlchemy 2.0 async ORM
- 必须支持异步（async/await）贯穿全栈
- 后续 Phase 1-6 的所有功能都将在此骨架上构建

## Goals / Non-Goals

**Goals:**
- 定义 Node Schema v1.0 标准，作为整个系统核心数据契约
- 搭建可运行的 FastAPI 项目骨架（`uvicorn main:app` 可启动，`/healthz` 可访问）
- 建立 PostgreSQL + Alembic 数据库迁移基础设施
- 提供一键启动的 Docker Compose 开发环境
- 确立团队开发规范（lint、format、commit、branch、test）
- 冻结核心 ER 模型设计，为 Phase 1 ORM 实现做准备

**Non-Goals:**
- 不实现任何 Node CRUD 业务逻辑（Phase 1 范畴）
- 不实现用户认证/JWT（Phase 1 范畴）
- 不创建实际 ORM 模型代码（Phase 0 只设计，Phase 1 实现）
- 不搭建搜索引擎集成（Phase 2 范畴）
- 不配置 CI/CD 流水线（可选，非阻塞交付项）

## Decisions

### 1. 异步优先架构

**选择**：全栈异步（async FastAPI + asyncpg + SQLAlchemy async session）

**替代方案**：同步 SQLAlchemy + psycopg2
**理由**：NodeVault 的核心操作是调用外部 Node 服务（HTTP/gRPC），这些都是 I/O 密集型操作。异步架构能显著提升并发吞吐量，且 FastAPI 原生支持 async，技术栈一致性好。

### 2. Pydantic Settings 统一配置管理

**选择**：`pydantic-settings` 的 `BaseSettings`，从 `.env` 文件和环境变量加载配置

**替代方案**：python-decouple、dynaconf
**理由**：与 FastAPI（Pydantic 原生）无缝集成，类型安全，自动验证，团队学习成本最低。

### 3. Ruff 替代 Black + isort + flake8

**选择**：Ruff 作为唯一的 lint + format 工具

**替代方案**：Black + isort + flake8 组合
**理由**：Ruff 用 Rust 编写，速度极快（10-100x），且兼容 Black 格式化 + isort 排序 + flake8 规则，一个工具替代三个，配置更简单。

### 4. structlog 结构化日志

**选择**：structlog 作为日志框架，输出 JSON 格式

**替代方案**：标准 logging 库、loguru
**理由**：生产环境需要结构化日志便于 ELK/Loki 采集，structlog 支持 JSON 输出、上下文绑定（request_id）、处理器链，比标准 logging 更适合微服务场景。

### 5. 目录结构采用分层架构

**选择**：按职责分目录（api/、core/、models/、schemas/、database/、auth/）

**替代方案**：按功能模块分目录（nodes/、workflows/、users/）
**理由**：Phase 0 阶段项目规模小，分层结构更清晰直观。随着项目成长，每个层内可以再按模块细分文件（如 `api/v1/nodes.py`、`api/v1/workflows.py`）。

### 6. Node Schema 使用 YAML 而非 JSON

**选择**：YAML 作为 Node Schema 人类可读格式

**替代方案**：纯 JSON Schema
**理由**：YAML 支持注释、可读性更好，适合开发者手写和维护。数据库中以 JSON/JSONB 存储（PostgreSQL 原生支持），YAML ↔ JSON 转换在注册时自动完成。

## Risks / Trade-offs

- **[Risk] 异步全栈增加调试复杂度** → 使用 structlog 绑定 request_id 实现全链路追踪，pytest-asyncio 处理异步测试
- **[Risk] ER 模型在 Phase 0 冻结后可能需要调整** → 仅冻结核心表结构（nodes、node_versions），Workflow 等表留有 JSONB 灵活字段，Alembic 迁移支持平滑演进
- **[Risk] MeiliSearch 在 Docker Compose 中引入但 Phase 0 不使用** → 不影响启动，Phase 2 时无需调整基础设施配置
- **[Trade-off] 不在 Phase 0 配置 CI/CD** → 降低初始复杂度，但需在 Phase 1 开始前补上，避免"坏窗户效应"

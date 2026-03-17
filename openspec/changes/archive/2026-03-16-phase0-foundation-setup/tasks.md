## 1. 项目骨架与配置

- [x] 1.1 创建项目目录结构（api/v1/、core/、models/、schemas/、database/、auth/、tests/、deploy/），每个包含 `__init__.py`
- [x] 1.2 创建 `pyproject.toml`，配置项目元数据、核心依赖和开发依赖（fastapi、sqlalchemy、pydantic、ruff、pytest 等）
- [x] 1.3 配置 `pyproject.toml` 中的 `[tool.ruff]` 节（行宽 88、规则集、target Python 3.11）
- [x] 1.4 创建 `.gitignore`（Python、venv、.env、__pycache__、IDE 文件等）

## 2. 环境变量与配置管理

- [x] 2.1 创建 `.env.example`，包含所有必需的环境变量（APP_ENV、APP_SECRET_KEY、DATABASE_URL、JWT_SECRET_KEY 等）及注释说明
- [x] 2.2 实现 `core/config.py` 的 `Settings` 类（继承 BaseSettings，类型注解，从 .env 加载配置）
- [x] 2.3 实现 `Environment` 枚举（development、staging、production）

## 3. 数据库基础设施

- [x] 3.1 实现 `database/session.py`（async engine、async_sessionmaker、`get_db` 依赖注入函数）
- [x] 3.2 创建 `database/base.py`（SQLAlchemy DeclarativeBase 基类）
- [x] 3.3 初始化 Alembic 配置（alembic.ini、database/migrations/ 目录、env.py 配置异步引擎）

## 4. 应用入口与健康检查

- [x] 4.1 实现 `main.py`（创建 FastAPI 实例、配置 CORS、挂载路由、lifespan 管理数据库连接）
- [x] 4.2 实现 `GET /healthz` 健康检查端点，返回 `{"status": "ok"}`
- [x] 4.3 实现统一响应格式 Pydantic 模型（`schemas/response.py`：ApiResponse、ErrorResponse、错误码枚举）

## 5. Node Schema 验证模型

- [x] 5.1 实现 Node 类型枚举（`schemas/enums.py`：NodeType、RuntimeType、NodeStatus、NodeVisibility）
- [x] 5.2 实现 Node Schema Pydantic 验证模型（`schemas/node_schema.py`：NodeSchemaBase，含 name、version、type、runtime、input_schema、output_schema 验证逻辑）
- [x] 5.3 实现 name 字段的 snake_case 验证器（正则 `^[a-z][a-z0-9_]{2,63}$`）
- [x] 5.4 实现 version 字段的 SemVer 验证器
- [x] 5.5 实现 Runtime 配置条件验证（http 类型时 endpoint 和 method 必填）

## 6. Docker Compose 开发环境

- [x] 6.1 创建 `deploy/docker-compose.dev.yml`（PostgreSQL 16、Redis 7、MeiliSearch v1.7，含命名 volume）
- [x] 6.2 创建 `deploy/Dockerfile`（多阶段构建，适用于开发和生产）

## 7. 测试基础设施

- [x] 7.1 创建 `tests/conftest.py`（app fixture、async TestClient fixture、测试数据库 session fixture）
- [x] 7.2 编写 `tests/test_health.py`（健康检查端点测试）
- [x] 7.3 编写 `tests/test_node_schema.py`（Node Schema 验证测试：合法/非法 name、version、type、runtime 配置）

## 8. 文档与规范

- [x] 8.1 在项目根目录创建 `CONTRIBUTING.md`（包含分支策略、提交规范、代码风格说明）
- [x] 8.2 验证完整启动流程（docker compose up → pip install → alembic upgrade → uvicorn 启动 → /healthz 返回 200）

## ADDED Requirements

### Requirement: Docker Compose 开发环境
项目 SHALL 提供 `deploy/docker-compose.dev.yml`，包含以下服务：PostgreSQL 16（端口 5432）、Redis 7（端口 6379）、MeiliSearch v1.7（端口 7700）。每个有状态服务 SHALL 使用命名 volume 持久化数据。

#### Scenario: 一键启动开发环境
- **WHEN** 执行 `docker compose -f deploy/docker-compose.dev.yml up -d`
- **THEN** PostgreSQL、Redis、MeiliSearch 三个服务 SHALL 全部正常启动

#### Scenario: 数据持久化
- **WHEN** 停止并重新启动 Docker Compose
- **THEN** PostgreSQL 和 MeiliSearch 的数据 SHALL 保持不变

### Requirement: 环境变量模板
项目 SHALL 提供 `.env.example` 文件，包含所有必需的环境变量及说明注释。变量 SHALL 包含：`APP_ENV`、`APP_SECRET_KEY`、`APP_DEBUG`、`APP_PORT`、`DATABASE_URL`、`REDIS_URL`、`JWT_SECRET_KEY`、`JWT_ALGORITHM`、`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`、`LOG_LEVEL`、`LOG_FORMAT`。

#### Scenario: 环境变量模板完整
- **WHEN** 开发者执行 `cp .env.example .env`
- **THEN** 所有必需配置项 SHALL 有默认的开发环境值，应用可直接启动

#### Scenario: 敏感信息不明文存储
- **WHEN** 审查 `.env.example`
- **THEN** 密钥类变量（APP_SECRET_KEY、JWT_SECRET_KEY）SHALL 使用占位值（如 `change-me-in-production`），不包含真实密钥

### Requirement: Pydantic Settings 配置类
系统 SHALL 提供 `core/config.py` 中的 `Settings` 类，继承 `pydantic_settings.BaseSettings`，自动从 `.env` 文件和环境变量加载配置。所有配置项 SHALL 有类型注解，敏感字段不设默认值（强制用户配置）。

#### Scenario: 配置加载成功
- **WHEN** `.env` 文件存在且包含所有必填项
- **THEN** `Settings()` 实例 SHALL 成功创建，所有字段类型正确

#### Scenario: 缺少必填配置
- **WHEN** `.env` 文件缺少 `APP_SECRET_KEY` 或 `DATABASE_URL`
- **THEN** 应用启动时 SHALL 抛出 Pydantic ValidationError，明确指出缺失字段

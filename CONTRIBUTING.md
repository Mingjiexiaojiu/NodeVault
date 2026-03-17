# Contributing to NodeVault

## 分支策略

```
main          ← 生产分支，只接受 merge request
  └── develop ← 开发主分支
        ├── feature/phase1-node-registry
        ├── feature/phase2-sdk
        └── fix/node-invocation-timeout
```

- 所有新功能从 `develop` 拉出 `feature/<phase>-<description>` 分支
- Bug 修复使用 `fix/<description>` 分支
- 完成后提交 Merge Request 到 `develop`
- `main` 分支仅通过 `develop` 合并

## 提交规范 (Conventional Commits)

```
<type>(<scope>): <description>
```

### Type

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 代码重构 |
| `docs` | 文档 |
| `test` | 测试 |
| `chore` | 构建/工具 |

### 示例

```
feat(registry): add node version management API
fix(runtime): handle HTTP timeout correctly
docs(schema): update Node Schema v1.1
test(schema): add validation tests for runtime config
```

## 代码风格

- **工具**: Ruff（lint + format）
- **行宽**: 88 字符
- **命名**:
  - 类名: `PascalCase`
  - 函数/变量: `snake_case`
  - 常量: `UPPER_SNAKE_CASE`
  - API 路径: `kebab-case` 或资源名复数

### 运行检查

```bash
# 格式化
ruff format .

# Lint 检查
ruff check .

# 类型检查
mypy nodevault/
```

## 测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=nodevault

# 运行特定测试
pytest nodevault/tests/test_node_schema.py -v
```

### 测试类型

| 类型 | 位置 | 说明 |
|------|------|------|
| 单元测试 | `nodevault/tests/test_*.py` | 业务逻辑 |
| 集成测试 | `nodevault/tests/test_*.py` | API 端点 |
| E2E 测试 | `nodevault/tests/e2e/` | 完整链路 |

目标覆盖率: **≥ 80%**

## 开发环境

```bash
# 启动基础设施
docker compose -f deploy/docker-compose.dev.yml up -d

# 安装依赖
pip install -e ".[dev]"

# 复制环境变量
cp .env.example .env

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn nodevault.main:app --reload --port 8000
```

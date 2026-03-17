## ADDED Requirements

### Requirement: 迁移脚本 import 所有 ORM 模型
`database/migrations/env.py` 中的 `target_metadata` SHALL 能感知所有 ORM 模型（User/Namespace/Node/NodeVersion/NodeTag/NodeInvocationLog），即在 `env.py` 中显式 import 对应模块后再引用 `Base.metadata`。

#### Scenario: autogenerate 不遗漏表
- **WHEN** 在已有 Base 但未 import 模型的情况下运行 `alembic revision --autogenerate`
- **THEN** 生成的脚本 SHALL 为空（无操作），验证 import 是必要的

#### Scenario: 正确 import 后 autogenerate 完整
- **WHEN** `env.py` 中 import 所有模型后运行 `alembic revision --autogenerate`
- **THEN** 生成的脚本 SHALL 包含全部 6 张表的 create_table 语句

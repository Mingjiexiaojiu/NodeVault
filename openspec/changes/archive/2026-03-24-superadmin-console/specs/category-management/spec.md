## MODIFIED Requirements

### Requirement: Category creation restricted to superadmin
系统分类（categories）的创建、更新和删除 SHALL 仅允许 role=0 的超管执行；普通用户 SHALL 不能创建或删除分类（只读）。

#### Scenario: Superadmin creates a category
- **WHEN** role=0 的用户调用 `POST /api/v1/categories`
- **THEN** 系统成功创建分类，返回 201

#### Scenario: Regular user attempts to create category
- **WHEN** role=2 的用户调用 `POST /api/v1/categories`
- **THEN** 系统返回 HTTP 403，提示 "Superadmin required"

#### Scenario: Superadmin deletes a category
- **WHEN** role=0 的用户调用 `DELETE /api/v1/categories/{id}`
- **THEN** 系统删除该分类（若分类下有节点，返回 409 提示需先迁移节点）

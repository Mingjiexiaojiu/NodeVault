## Why

NodeVault 目前已完成 Phase 1 后端 MVP（REST API、JWT 认证、Node 注册/查询/调用），但没有任何可视化界面，开发者只能通过 Swagger 或命令行与系统交互。缺少 Web UI 严重影响产品可用性与演示价值，是当前最高优先级的体验缺口。

## What Changes

- **新增** 基于 Vue 3 + Vite 的前端独立应用（`frontend/` 目录）
- **新增** 认证页面：登录 / 注册
- **新增** 仪表盘主页：Node 总览统计卡片
- **新增** Node 列表页：搜索/过滤/分页浏览所有 Node
- **新增** Node 详情页：查看 Node 元信息、版本列表、调用日志
- **新增** Node 注册页：表单提交新 Node（支持 runtime 配置）
- **新增** Node 调用页：在线测试 Node（输入参数、查看输出）
- **新增** 前端构建配置：Vite、Tailwind CSS、Vue Router、Pinia、Axios
- **新增** 开发代理配置：将 `/api` 请求代理到后端 `http://localhost:8000`

## Capabilities

### New Capabilities

- `frontend-auth`: 登录、注册页面及 JWT Token 本地存储、全局认证状态管理
- `frontend-node-list`: Node 列表页，支持按类型/状态/标签过滤，分页展示
- `frontend-node-detail`: Node 详情页，展示元信息、版本列表、最近调用日志
- `frontend-node-create`: Node 注册表单，验证字段并提交到 API
- `frontend-node-invoke`: Node 在线调用界面，JSON 输入编辑器，响应展示
- `frontend-dashboard`: 首页仪表盘，展示 Node 总数、调用统计等概览数据
- `frontend-infra`: Vite 项目脚手架、路由、状态管理、API 封装、构建配置

### Modified Capabilities

（无现有 spec 需变更）

## Impact

- **新增目录**：`frontend/`（独立 Node.js 项目，不影响后端）
- **后端 API**：无需修改，前端直接调用已有 REST 端点
- **部署**：`frontend/dist/` 可由 FastAPI 挂载为静态文件，或独立部署
- **依赖**：Node.js 18+、pnpm、Vue 3、Vite 5、Tailwind CSS 3、Vue Router 4、Pinia 2

## Context

NodeVault Phase 1 已完成所有后端 REST API（认证、Node CRUD、调用、日志），共 13 个端点，覆盖率 87%。目前没有任何 Web UI，用户只能通过 Swagger (`/docs`) 或 curl 操作。

项目后端技术栈：FastAPI + SQLAlchemy async + PostgreSQL（远程）+ Redis。API 基础路径 `/api/v1`，使用 Bearer JWT 认证。设计规范见 `Design/Phase0-基础与规范.md`。

## Goals / Non-Goals

**Goals:**

- 提供完整可运行的前端 SPA，覆盖核心功能：认证、Node 浏览/注册/调用
- 前端独立目录 `frontend/`，与后端解耦，可独立开发和部署
- 开发模式下通过 Vite 代理访问本地后端
- 生产构建产物可被 FastAPI 挂载为静态文件（`/`路由）
- 界面风格简洁专业，使用 Tailwind CSS + shadcn 风格组件

**Non-Goals:**

- 不实现 Phase 2 搜索功能（MeiliSearch）
- 不实现 Workflow 可视化（Phase 4）
- 不实现用户管理、命名空间管理（Phase 5）
- 不做响应式移动端适配（桌面优先）
- 不实现暗色模式

## Decisions

### D1：前端技术栈选 Vue 3 + Vite + Tailwind CSS

**选择**：Vue 3 (Composition API + `<script setup>`) + Vite 5 + Tailwind CSS 3 + Vue Router 4 + Pinia 2

**理由**：
- Vue 3 Composition API 与 React Hooks 体验相近，学习曲线平滑
- Vite 启动极快，开发体验好
- Tailwind CSS 无需设计系统依赖，直接 utility-first 快速出样式
- Pinia 是 Vue 官方推荐状态管理，API 简洁

**备选考量**：
- React + Next.js：更大生态，但对纯 SPA 来说配置较重
- Nuxt 3：SSR 优势对内部工具意义不大

### D2：不引入重型组件库，使用轻量 UI 原语

**选择**：自行用 Tailwind 封装小型组件（Button、Card、Badge、Input 等），不引入 Element Plus / Ant Design Vue。

**理由**：
- 避免样式冲突和 bundle 膨胀
- 项目 UI 相对简单，自定义组件够用
- 保持灵活度，后续可按需升级

**备选**：Element Plus（体积大）、Headless UI（需更多封装工作）

### D3：API 层用 axios + 统一拦截器

**选择**：`src/api/` 目录下按资源分文件（`auth.ts`、`nodes.ts`、`invocations.ts`），使用 axios 实例统一设置 baseURL 和 JWT 请求头。

**优势**：
- 请求/响应拦截器统一处理 401 跳转登录
- API 函数类型化，IDE 补全好
- 易于 mock 测试

### D4：路由结构与权限守卫

```
/login              → LoginPage（无需认证）
/register           → RegisterPage（无需认证）
/                   → DashboardPage（需认证）
/nodes              → NodeListPage（需认证）
/nodes/new          → NodeCreatePage（需认证）
/nodes/:id          → NodeDetailPage（需认证）
/nodes/:id/invoke   → NodeInvokePage（需认证）
```

Vue Router 全局前置守卫检查 Pinia auth store 中的 token；未登录自动跳转 `/login`。

### D5：JWT Token 持久化到 localStorage

**选择**：Token 存在 `localStorage`，页面刷新后从 localStorage 恢复到 Pinia store。

**权衡**：XSS 风险 vs 使用便利性。对内部工具项目可接受，后续可迁移至 HttpOnly Cookie（Phase 5 安全加固）。

### D6：生产集成方案——FastAPI 挂载静态文件

前端 `pnpm build` 产出 `frontend/dist/`，在 FastAPI `main.py` 末尾挂载：
```python
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```
开发时前端 `pnpm dev`（Vite 代理 `/api` → `http://localhost:8000`），后端 `uvicorn` 分别运行。

## Risks / Trade-offs

| 风险 | 缓解方案 |
|------|---------|
| 后端 CORS 未配置导致开发时跨域 | 后端已有 `CORSMiddleware`，开发通过 Vite proxy 绕过，生产同源无问题 |
| Node.js 版本依赖 | 明确要求 Node.js 18+，在 README 中说明 |
| JWT 存 localStorage 的 XSS 风险 | 当前为内部工具，可接受；Phase 5 迁移至 HttpOnly Cookie |
| 调用 Node 时需访问外部 URL，可能被浏览器 CORS 拦截 | 调用由后端代理执行（`/api/v1/nodes/:id/invoke`），浏览器不直接访问目标服务 |
| shadcn/tailwind 与 Vue 集成无官方支持 | 手写基础组件，不依赖 shadcn-vue，避免维护困境 |

## Migration Plan

1. 在项目根目录创建 `frontend/` 子项目（`pnpm create vite`）
2. 开发阶段：前后端分别独立运行，通过 Vite proxy 联调
3. 生产集成：构建后由 FastAPI 挂载（可选，也可独立 nginx 部署）
4. 无数据库迁移，无 API 变更，零回滚风险

## Open Questions

- 是否需要在前端实现 Node 调用结果的 JSON 语法高亮？（倾向：yes，用 `highlight.js` 轻量方案）
- Dashboard 首页的统计数据来自哪个 API？（当前后端无聚合接口，暂用 node 列表 count 代替）

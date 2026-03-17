## 1. 项目脚手架（frontend-infra�?

- [x] 1.1 在项目根目录执行 `pnpm create vite frontend -- --template vue-ts`，初始化 Vite + Vue 3 + TypeScript 项目
- [x] 1.2 安装依赖：`pnpm add vue-router@4 pinia axios`；`pnpm add -D tailwindcss postcss autoprefixer`；初始化 Tailwind（`npx tailwindcss init -p`�?
- [x] 1.3 配置 `tailwind.config.js`：content 包含 `./src/**/*.{vue,ts,js}`；在 `src/style.css` 引入 Tailwind 指令
- [x] 1.4 配置 `vite.config.ts`：添�?server.proxy，将 `/api` 代理�?`http://localhost:8000`
- [x] 1.5 创建目录结构：`src/api/`、`src/stores/`、`src/views/`、`src/components/`、`src/layouts/`、`src/router/`

## 2. API 封装与状态管理（frontend-infra + frontend-auth�?

- [x] 2.1 创建 `src/api/http.ts`：配�?axios 实例，设�?baseURL=`/api/v1`，响应拦截器处理 401（清�?token �?redirect /login�?
- [x] 2.2 创建 `src/api/auth.ts`：实�?`login(email, password)`、`register(email, username, password)`、`getMe()` 函数
- [x] 2.3 创建 `src/api/nodes.ts`：实�?`listNodes(params)`、`getNode(id)`、`createNode(payload)`、`updateNode(id, payload)`、`deleteNode(id)`、`listVersions(id)`、`invokeNode(id, payload)`、`getLogs(id)`
- [x] 2.4 创建 `src/stores/auth.ts`（Pinia store）：state = `{ token, user }`，actions = `login`, `logout`, `fetchMe`；token 读写 localStorage
- [x] 2.5 �?axios 实例的请求拦截器中读�?auth store �?token，注�?`Authorization: Bearer <token>` �?

## 3. 路由与布局（frontend-infra�?

- [x] 3.1 创建 `src/router/index.ts`：定义路由表�?login�?register�?�?nodes�?nodes/new�?nodes/:id�?nodes/:id/invoke�?
- [x] 3.2 实现全局路由前置守卫：无 token 时重定向�?/login；已登录访问 /login 时重定向�?/
- [x] 3.3 创建 `src/layouts/AppLayout.vue`：包含顶部导航栏（Logo、导航链接：Dashboard/Nodes、右上角用户�?登出按钮）、主内容 `<router-view>`
- [x] 3.4 修改 `src/App.vue`：根据路�?meta.layout 条件渲染 AppLayout 或直接渲�?`<router-view>`（登�?注册页不�?AppLayout�?

## 4. 通用组件

- [x] 4.1 创建 `src/components/BaseButton.vue`：支�?variant（primary/secondary/danger）、loading、disabled 属�?
- [x] 4.2 创建 `src/components/BaseInput.vue`：支�?label、error 属性，绑定 v-model
- [x] 4.3 创建 `src/components/StatusBadge.vue`：根�?status（draft/active/deprecated/archived）显示不同颜�?badge
- [x] 4.4 创建 `src/components/TypeBadge.vue`：根�?NodeType 显示类型标签
- [x] 4.5 创建 `src/components/JsonEditor.vue`：textarea + JSON 语法验证，提�?`modelValue` �?`error` slot
- [x] 4.6 创建 `src/components/EmptyState.vue`：空状态插�?+ 描述文字 + 可选操作按�?

## 5. 认证页面（frontend-auth�?

- [x] 5.1 创建 `src/views/LoginView.vue`：邮�?密码表单，提交调�?auth store �?login，成功跳�?/，失败显示错误信�?
- [x] 5.2 创建 `src/views/RegisterView.vue`：邮�?用户�?密码表单，前端密码强度校验，提交调用 `api/auth.register`，成功后自动登录跳转 /

## 6. 仪表盘（frontend-dashboard�?

- [x] 6.1 创建 `src/views/DashboardView.vue`：欢迎语（`欢迎，{username}`）、快捷操作按钮（注册新节点、浏览全部节点）
- [x] 6.2 实现统计卡片：调�?`listNodes({page_size: 100})` 后计�?total/active/draft 数量，渲染为 3 �?stat card
- [x] 6.3 实现"最近节�?列表：展示最�?5 个节点（name、type badge、status badge），点击跳转详情�?

## 7. Node 列表页（frontend-node-list�?

- [x] 7.1 创建 `src/views/NodeListView.vue`：页面标�?+ "注册新节�? 按钮 + 下方节点表格
- [x] 7.2 实现类型/状态筛选下拉框：选项来自枚举，变更时重新调用 API
- [x] 7.3 实现节点表格：列包括名称（链接到详情）、类�?badge、状�?badge、创建时间；支持空状�?
- [x] 7.4 实现分页控件：上一�?下一页按钮，基于 `page` query 参数

## 8. Node 详情页（frontend-node-detail�?

- [x] 8.1 创建 `src/views/NodeDetailView.vue`：顶部操作栏（返回列表、调用此节点按钮�? 元信息卡�?
- [x] 8.2 元信息卡片：展示所有字段，tags 渲染�?badge 列表，timestamps 格式化为可读日期
- [x] 8.3 版本列表卡片：GET /nodes/:id/versions，表格展�?version、is_default（默�?badge）、created_at
- [x] 8.4 调用日志卡片：GET /nodes/:id/logs，表格展示调用时间、状态（颜色区分）、latency_ms；空状态处�?

## 9. Node 注册页（frontend-node-create�?

- [x] 9.1 创建 `src/views/NodeCreateView.vue`：分组表单（基本信息、运行时配置、IO Schema�?
- [x] 9.2 实现基本信息区块：name（正则校验）、version（semver 校验）、display_name、description、type 下拉、category、tags 输入
- [x] 9.3 实现运行时配置区块：runtime.type 下拉（默�?http）、endpoint URL 输入、method 下拉（GET/POST/PUT/DELETE�?
- [x] 9.4 实现 IO Schema 区块：两�?JsonEditor 组件（input_schema、output_schema），默认�?`{"type":"object","properties":{}}`
- [x] 9.5 表单提交逻辑：POST /api/v1/nodes，成功跳转到新节点详情页�?09 显示重名错误�?22 展示字段校验错误

## 10. Node 调用页（frontend-node-invoke�?

- [x] 10.1 创建 `src/views/NodeInvokeView.vue`：顶部显�?node 名称（从路由参数加载�?
- [x] 10.2 实现版本选择器：GET /nodes/:id/versions 获取列表，默认选中"默认版本"（null�?
- [x] 10.3 实现输入面板：JsonEditor 组件，默认�?`{}`，JSON 校验通过后才允许提交
- [x] 10.4 实现调用按钮：提交时按钮 loading 态，调用 POST /nodes/:id/invoke
- [x] 10.5 实现结果面板：用 `<pre>` + Tailwind 样式展示 JSON 输出（JSON.stringify with indent）、latency_ms、invocation_id�?02 错误用红�?alert 展示

## 11. 生产集成

- [x] 11.1 验证 `pnpm build` �?`frontend/` 下能成功生成 `dist/`
- [x] 11.2 �?`nodevault/main.py` 中添�?`StaticFiles` 挂载（仅�?`frontend/dist/` 存在时），使生产模式�?`/` 路由提供 Vue SPA
- [x] 11.3 在项目根 `README.md` 中补充前端开发启动说明（`pnpm install && pnpm dev`�?

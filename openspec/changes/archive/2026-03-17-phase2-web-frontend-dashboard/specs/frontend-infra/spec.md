## ADDED Requirements

### Requirement: Frontend project is initialized with Vite + Vue 3
The system SHALL have a `frontend/` directory at project root containing a Vite 5 + Vue 3 project.

#### Scenario: Project structure is valid
- **WHEN** developer runs `pnpm install` in `frontend/`
- **THEN** all dependencies install without errors

#### Scenario: Dev server starts
- **WHEN** developer runs `pnpm dev` in `frontend/`
- **THEN** Vite dev server starts on port 5173 and proxies `/api` to `http://localhost:8000`

### Requirement: API module encapsulates all backend calls
The system SHALL have `frontend/src/api/` with typed functions for each resource.

#### Scenario: Auth API functions exist
- **WHEN** `src/api/auth.ts` is imported
- **THEN** it exports `login(email, password)`, `register(email, username, password)`, `getMe()`

#### Scenario: Nodes API functions exist
- **WHEN** `src/api/nodes.ts` is imported
- **THEN** it exports `listNodes(params)`, `getNode(id)`, `createNode(payload)`, `updateNode(id, payload)`, `deleteNode(id)`, `listVersions(id)`, `invokeNode(id, payload)`, `getLogs(id)`

### Requirement: Axios instance includes JWT Authorization header
The system SHALL configure a global axios instance that reads the token from Pinia store and attaches it to every request.

#### Scenario: Authenticated request includes header
- **WHEN** a logged-in user's action triggers an API call
- **THEN** the request includes `Authorization: Bearer <token>` header

#### Scenario: 401 response triggers logout and redirect
- **WHEN** any API response returns 401
- **THEN** axios response interceptor clears the auth store and redirects to /login

### Requirement: Application layout includes persistent navigation
The system SHALL have a shared layout with a sidebar or top navbar for authenticated pages.

#### Scenario: Navigation links are visible on all protected pages
- **WHEN** user is on any authenticated page
- **THEN** navigation shows links to: Dashboard, Nodes, and a logout action

### Requirement: Frontend can be built for production
The system SHALL produce an optimized static build.

#### Scenario: Production build succeeds
- **WHEN** developer runs `pnpm build` in `frontend/`
- **THEN** `frontend/dist/` is generated with `index.html` and hashed asset files

#### Scenario: FastAPI mounts frontend in production
- **WHEN** `frontend/dist/` exists and `main.py` has the StaticFiles mount
- **THEN** navigating to `http://localhost:8000/` in a browser loads the Vue app

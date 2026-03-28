import http from './http'

// ---------- Types ----------

export interface ProbeRequest {
  base_url: string
  probe_paths?: string[]
}

export interface ProbeAuthConfig {
  base_url: string
  login_endpoint: string
  login_method?: string
  login_body: Record<string, unknown>
  token_json_path?: string
  probe_paths?: string[]
}

export interface ProbeAttempt {
  path: string
  status: number | null
  success: boolean
  error: string | null
}

export interface ProbeResult {
  base_url: string
  found: boolean
  spec_url: string | null
  needs_auth: boolean
  error: string | null
  error_type: string | null
  attempts: ProbeAttempt[]
}

export interface NodeDraft {
  suggested_name: string
  display_name: string
  description: string
  endpoint: string
  method: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  category: string | null
  tags: string[]
  selected: boolean
}

export interface NodeDraftListResponse {
  base_url: string
  drafts: NodeDraft[]
}

export interface BatchImportItem {
  name: string
  display_name?: string
  description?: string
  endpoint: string
  method: string
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  category_id?: string
  tags?: string[]
  source_path?: string
}

export interface BatchImportRequest {
  department_id: string
  credential_id?: string
  base_url: string
  items: BatchImportItem[]
  visibility?: string
  session_id?: string
}

export interface BatchImportResultItem {
  name: string
  node_id: string
}

export interface BatchImportResponse {
  imported: number
  nodes: BatchImportResultItem[]
}

// ---------- API ----------

/** Probe a URL for OpenAPI spec */
export const probeSpec = (payload: ProbeRequest) =>
  http.post<ProbeResult | NodeDraftListResponse>('/discovery/probe', payload)

/** Probe with authentication */
export const probeWithAuth = (payload: ProbeAuthConfig) =>
  http.post<ProbeResult | NodeDraftListResponse>('/discovery/probe-with-auth', payload)

/** Upload an OpenAPI spec file */
export const uploadSpec = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<NodeDraftListResponse>('/discovery/upload-spec', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** Batch import nodes from discovered drafts */
export const batchImport = (payload: BatchImportRequest) =>
  http.post<BatchImportResponse>('/discovery/import', payload)

export interface ImportedPathsResponse {
  credential_id: string
  imported_paths: string[]
}

/** Get all source_paths already imported from a given service credential */
export const getImportedPaths = (credentialId: string) =>
  http.get<ImportedPathsResponse>(`/discovery/imported?credential_id=${credentialId}`)


// ---------- Discovery Session ----------

export interface DiscoverySessionCreate {
  base_url?: string
  source?: 'probe' | 'upload'
}

export interface DiscoverySessionUpdate {
  status?: string
  spec_url?: string
  total_operations?: number
  imported_count?: number
  completed_at?: string
}

export interface DiscoverySession {
  id: string
  base_url: string
  source: 'probe' | 'upload'
  status: 'probing' | 'found' | 'failed' | 'completed'
  spec_url: string | null
  total_operations: number | null
  imported_count: number
  created_at: string
  completed_at: string | null
}

export interface LinkedNode {
  id: string
  name: string
  display_name: string | null
  source_path: string | null
  status: string
}

export interface DiscoverySessionDetail extends DiscoverySession {
  nodes: LinkedNode[]
}

/** Create a new discovery session */
export const createSession = (payload: DiscoverySessionCreate = {}) =>
  http.post<DiscoverySession>('/discovery/sessions', payload)

/** Update session status / metadata */
export const updateSession = (sessionId: string, payload: DiscoverySessionUpdate) =>
  http.patch<DiscoverySession>(`/discovery/sessions/${sessionId}`, payload)

/** List discovery sessions for current user */
export const listSessions = (page = 1, pageSize = 20, baseUrl?: string) => {
  const params: Record<string, unknown> = { page, page_size: pageSize }
  if (baseUrl) params.base_url = baseUrl
  return http.get<DiscoverySession[]>('/discovery/sessions', { params })
}

/** Get session detail with linked nodes */
export const getSession = (sessionId: string) =>
  http.get<DiscoverySessionDetail>(`/discovery/sessions/${sessionId}`)

// ---------- Duplicate Detection & Iteration ----------

export interface DuplicateUrlResponse {
  is_duplicate: boolean
  existing_sessions: { id: string; base_url: string; status: string; created_at: string }[]
  existing_node_count: number
}

/** Check if a base_url has already been discovered/imported */
export const checkDuplicate = (baseUrl: string) =>
  http.get<DuplicateUrlResponse>('/discovery/check-duplicate', { params: { base_url: baseUrl } })

export interface CompareResultItem {
  source_path: string
  method: string
  status: 'new' | 'imported' | 'updated' | 'removed'
  node_id: string | null
  display_name: string | null
}

export interface CompareResponse {
  items: CompareResultItem[]
}

/** Compare current session endpoints with previous ones */
export const compareSession = (sessionId: string, previousSessionId: string) =>
  http.post<CompareResponse>(`/discovery/sessions/${sessionId}/compare`, { previous_session_id: previousSessionId })

export interface IterateAction {
  source_path: string
  method: string
  action: 'import' | 'update' | 'skip'
}

export interface IterateResponse {
  imported: number
  updated: number
  skipped: number
}

/** Execute iteration actions on compared endpoints */
export const iterateSession = (sessionId: string, actions: IterateAction[], departmentId: string) =>
  http.post<IterateResponse>(`/discovery/sessions/${sessionId}/iterate`, { actions, department_id: departmentId })

import http from './http'

export type NodeStatus = 'draft' | 'active' | 'deprecated' | 'archived'

export interface CategoryBrief {
  id: string
  display_name: string
}

export interface NodeVersion {
  id: string
  node_id: string
  version: string
  is_default: boolean
  is_deprecated: boolean
  runtime_config: Record<string, unknown>
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  changelog: string | null
  created_at: string
}

export interface NodeVersionCreate {
  version: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  runtime_config: Record<string, unknown>
  changelog?: string
  is_default?: boolean
}

export interface NodeItem {
  id: string
  name: string
  display_name: string
  description: string
  category_id: string
  category: CategoryBrief | null
  status: NodeStatus
  tags: string[]
  owner_id: string
  owner_username: string | null
  namespace_id: string
  namespace_slug: string | null
  source_credential_id: string | null
  source_path: string | null
  source_service_name: string | null
  created_at: string
  updated_at: string
}

export interface InvocationLog {
  id: string
  node_id: string
  version_id: string | null
  status: 'success' | 'error' | 'timeout'
  latency_ms: number | null
  created_at: string
}

export interface InvokeResult {
  invocation_id: string
  status: string
  output: unknown
  latency_ms: number | null
}

export interface NodeListParams {
  page?: number
  page_size?: number
  category_id?: string
  status?: NodeStatus
  mine?: boolean
}

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface CreateNodePayload {
  name: string
  display_name?: string
  description?: string
  category_id: string
  tags?: string[]
  version?: string
  runtime: {
    type: string
    endpoint: string
    method: string
    timeout?: number
    headers?: Record<string, string>
  }
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
}

export interface NodeStats {
  node_id: string
  period_days: number
  total_invocations: number
  success_rate: number | null
  avg_latency_ms: number | null
  p95_latency_ms: number | null
  p99_latency_ms: number | null
  daily_trend: { date: string; count: number; success: number }[]
  top_callers: { user_id: string; count: number }[]
}

export interface SearchResult {
  total: number
  page: number
  page_size: number
  results: NodeItem[]
}

export interface TagItem {
  tag: string
  node_count: number
}

export interface UpdateNodePayload {
  display_name?: string
  description?: string
  category_id?: string
  status?: NodeStatus
  tags?: string[]
}

export const listNodes = (params?: NodeListParams) =>
  http.get<NodeItem[]>('/nodes', { params })

export const getNode = (id: string) => http.get<NodeItem>(`/nodes/${id}`)

export const createNode = (payload: CreateNodePayload) =>
  http.post<NodeItem>('/nodes', payload)

export const updateNode = (id: string, payload: UpdateNodePayload) =>
  http.patch<NodeItem>(`/nodes/${id}`, payload)

export const deleteNode = (id: string) => http.delete(`/nodes/${id}`)

export const deleteVersion = (nodeId: string, version: string) =>
  http.delete(`/nodes/${nodeId}/versions/${version}`)

export const listVersions = (id: string) =>
  http.get<NodeVersion[]>(`/nodes/${id}/versions`)

export interface NodeVersionUpdate {
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  runtime_config?: Record<string, unknown>
  changelog?: string
}

export const createVersion = (nodeId: string, payload: NodeVersionCreate) =>
  http.post<NodeVersion>(`/nodes/${nodeId}/versions`, payload)

export const updateVersion = (nodeId: string, version: string, payload: NodeVersionUpdate) =>
  http.patch<NodeVersion>(`/nodes/${nodeId}/versions/${encodeURIComponent(version)}`, payload)

export const setDefaultVersion = (nodeId: string, version: string) =>
  http.post(`/nodes/${nodeId}/versions/${encodeURIComponent(version)}/set-default`)

export const invokeNode = (
  id: string,
  payload: { input: unknown; version?: string },
) => http.post<InvokeResult>(`/nodes/${id}/invoke`, payload)

export const getLogs = (id: string, params?: { page?: number; page_size?: number }) =>
  http.get<InvocationLog[]>(`/nodes/${id}/logs`, { params })

export const getNodeStats = (id: string, days = 30) =>
  http.get<NodeStats>(`/nodes/${id}/stats`, { params: { days } })

export const searchNodes = (params: {
  q?: string
  type?: string
  tags?: string[]
  sort?: 'relevance' | 'latest' | 'popular'
  page?: number
  page_size?: number
}) => http.get<SearchResult>('/search/nodes', { params })

export const getPopularTags = (limit = 20) =>
  http.get<TagItem[]>('/tags', { params: { limit } })

export const getNodesByTag = (tag: string, params?: { page?: number; page_size?: number }) =>
  http.get<NodeItem[]>(`/tags/${tag}/nodes`, { params })

// ---- Export APIs ----

export const exportNodeOpenAI = (id: string) =>
  http.get<Record<string, unknown>>(`/nodes/${id}/export/openai`)

export const exportNodeLangChain = (id: string) =>
  http.get<string>(`/nodes/${id}/export/langchain`, {
    responseType: 'text',
    transformResponse: [(data) => data],
  })

export const exportNodeMCP = (id: string) =>
  http.get<Record<string, unknown>>(`/nodes/${id}/export/mcp`)

export const downloadNodeSkillZip = (id: string, nodeName: string) => {
  const token = localStorage.getItem('token')
  const a = document.createElement('a')
  a.href = `/api/v1/nodes/${id}/export/skill`
  // Trigger download with auth via fetch + blob
  fetch(`/api/v1/nodes/${id}/export/skill`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => r.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      a.href = url
      a.download = `${nodeName}.zip`
      a.click()
      URL.revokeObjectURL(url)
    })
}

export const batchExport = (
  ids: string[],
  format: 'openai' | 'langchain' | 'mcp' = 'openai',
) =>
  http.get<Record<string, unknown>>('/export/batch', {
    params: { ids: ids.join(','), format },
  })

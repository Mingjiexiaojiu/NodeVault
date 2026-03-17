import http from './http'

export type NodeType =
  | 'data_cleaning'
  | 'analysis'
  | 'risk'
  | 'nlp'
  | 'vision'
  | 'ml'
  | 'tool'
  | 'utility'

export type NodeStatus = 'draft' | 'active' | 'deprecated' | 'archived'

export interface NodeVersion {
  id: string
  node_id: string
  version: string
  is_default: boolean
  runtime: Record<string, unknown>
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  created_at: string
}

export interface NodeItem {
  id: string
  name: string
  display_name: string
  description: string
  type: NodeType
  status: NodeStatus
  category: string
  tags: string[]
  owner_id: string
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
  type?: NodeType
  status?: NodeStatus
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
  type: NodeType
  category?: string
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

export const listNodes = (params?: NodeListParams) =>
  http.get<PagedResponse<NodeItem>>('/nodes', { params })

export const getNode = (id: string) => http.get<NodeItem>(`/nodes/${id}`)

export const createNode = (payload: CreateNodePayload) =>
  http.post<NodeItem>('/nodes', payload)

export const updateNode = (id: string, payload: Partial<CreateNodePayload>) =>
  http.put<NodeItem>(`/nodes/${id}`, payload)

export const deleteNode = (id: string) => http.delete(`/nodes/${id}`)

export const listVersions = (id: string) =>
  http.get<NodeVersion[]>(`/nodes/${id}/versions`)

export const invokeNode = (
  id: string,
  payload: { input: unknown; version?: string },
) => http.post<InvokeResult>(`/nodes/${id}/invoke`, payload)

export const getLogs = (id: string, params?: { page?: number; page_size?: number }) =>
  http.get<PagedResponse<InvocationLog>>(`/nodes/${id}/logs`, { params })

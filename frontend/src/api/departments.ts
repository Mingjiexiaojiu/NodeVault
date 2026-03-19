import http from './http'
import type { NodeStatus } from './nodes'

export interface DepartmentBrief {
  id: string
  slug: string
  display_name: string | null
  description: string | null
  owner_id: string
  member_count: number
  node_count: number
  created_at: string
}

export interface DepartmentListResponse {
  items: DepartmentBrief[]
  total: number
}

export interface DepartmentMember {
  user_id: string
  username: string
  email: string
  role: string
  joined_at: string
}

export interface DepartmentNode {
  id: string
  name: string
  display_name: string | null
  type: string
  status: NodeStatus
  tags: string[]
  created_at: string
}

export interface DepartmentStats {
  node_count: number
  member_count: number
  total_invocations: number
  status_distribution: Record<string, number>
  type_distribution: Record<string, number>
}

export interface DepartmentDetail {
  id: string
  slug: string
  display_name: string | null
  description: string | null
  owner_id: string
  owner_username: string | null
  created_at: string
  stats: DepartmentStats
  members: DepartmentMember[]
  nodes: DepartmentNode[]
}

export const listDepartments = (params?: { page?: number; page_size?: number }) =>
  http.get<DepartmentListResponse>('/departments', { params })

export const getDepartment = (id: string) =>
  http.get<DepartmentDetail>(`/departments/${id}`)

export const createDepartment = (payload: { slug: string; display_name: string; description?: string }) =>
  http.post('/departments', payload)

export const updateDepartment = (id: string, payload: { display_name?: string; description?: string }) =>
  http.patch(`/departments/${id}`, payload)

export const addMember = (deptId: string, payload: { username: string; role?: string }) =>
  http.post(`/departments/${deptId}/members`, payload)

export const removeMember = (deptId: string, userId: string) =>
  http.delete(`/departments/${deptId}/members/${userId}`)

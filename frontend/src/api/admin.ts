import http from './http'

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface AdminUserListItem {
  id: string
  email: string
  username: string
  display_name: string | null
  role: number
  role_label: string
  is_active: boolean
  created_at: string
}

export interface AdminUserDetail extends AdminUserListItem {
  avatar_url: string | null
  bio: string | null
  phone: string | null
  department: string | null
  title: string | null
  namespace_count: number
  node_count: number
  skill_count: number
}

export interface AdminNodeListItem {
  id: string
  name: string
  display_name: string | null
  department_id: string
  department_slug: string | null
  owner_id: string
  owner_username: string | null
  category_id: string
  category_name: string | null
  status: string
  visibility: string
  invocation_count: number
  created_at: string
}

export interface AdminDepartmentListItem {
  id: string
  slug: string
  display_name: string | null
  owner_id: string
  owner_username: string | null
  supervisor_username: string | null
  member_count: number
  node_count: number
  created_at: string
}

export interface AdminSkillListItem {
  id: string
  name: string
  display_name: string | null
  department_id: string
  department_slug: string | null
  owner_id: string
  owner_username: string | null
  status: string
  is_stale: boolean
  created_at: string
}

export interface PlatformOverview {
  total_users: number
  total_nodes: number
  total_skills: number
  total_invocations: number
  new_users_24h: number
  invocations_24h: number
}

export interface DailyInvocationStat {
  date: string
  success: number
  failure: number
}

export interface TopNodeItem {
  id: string
  name: string
  display_name: string | null
  department_slug: string | null
  owner_username: string | null
  invocation_count: number
}

export interface TopUserItem {
  id: string
  username: string
  display_name: string | null
  node_count: number
  skill_count: number
}

export interface SystemSettingItem {
  key: string
  value: string | null
  updated_at: string
}

export interface PagedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ─────────────────────────────────────────────
// User Management
// ─────────────────────────────────────────────

export function listUsers(params?: { q?: string; role?: number; is_active?: boolean; page?: number; page_size?: number }) {
  return http.get<PagedResult<AdminUserListItem>>('/admin/users', { params })
}

export function getUserDetail(userId: string) {
  return http.get<AdminUserDetail>(`/admin/users/${userId}`)
}

export function updateUserStatus(userId: string, isActive: boolean) {
  return http.patch(`/admin/users/${userId}/status`, { is_active: isActive })
}

export function updateUserRole(userId: string, role: number) {
  return http.patch(`/admin/users/${userId}/role`, { role })
}

export function deleteUser(userId: string) {
  return http.delete(`/admin/users/${userId}`)
}

// ─────────────────────────────────────────────
// Global Resources
// ─────────────────────────────────────────────

export function listAllNodes(params?: { department_id?: string; status?: string; category_id?: string; page?: number; page_size?: number }) {
  return http.get<PagedResult<AdminNodeListItem>>('/admin/nodes', { params })
}

export function updateNodeStatus(nodeId: string, status: string) {
  return http.patch(`/admin/nodes/${nodeId}/status`, { status })
}

export function listAllDepartments(params?: { page?: number; page_size?: number }) {
  return http.get<PagedResult<AdminDepartmentListItem>>('/admin/departments', { params })
}

export function adminCreateDepartment(payload: { slug: string; display_name: string; description?: string }) {
  return http.post('/admin/departments', payload)
}

export function adminDeleteDepartment(deptId: string) {
  return http.delete(`/admin/departments/${deptId}`)
}

export function listAllSkills(params?: { page?: number; page_size?: number }) {
  return http.get<PagedResult<AdminSkillListItem>>('/admin/skills', { params })
}

// ─────────────────────────────────────────────
// Analytics
// ─────────────────────────────────────────────

export function getAnalyticsOverview() {
  return http.get<PlatformOverview>('/admin/analytics/overview')
}

export function getInvocationTrend(range: '7d' | '30d' | '90d' = '30d') {
  return http.get<DailyInvocationStat[]>('/admin/analytics/invocations', { params: { range } })
}

export function getTopNodes(limit = 10) {
  return http.get<TopNodeItem[]>('/admin/analytics/top-nodes', { params: { limit } })
}

export function getTopUsers(limit = 10) {
  return http.get<TopUserItem[]>('/admin/analytics/top-users', { params: { limit } })
}

// ─────────────────────────────────────────────
// System Settings
// ─────────────────────────────────────────────

export function getSettings() {
  return http.get<SystemSettingItem[]>('/admin/settings')
}

export function updateSetting(key: string, value: string) {
  return http.put(`/admin/settings/${key}`, { value })
}

export function getAnnouncement() {
  return http.get<{ announcement: string }>('/settings/announcement')
}

// ─────────────────────────────────────────────
// API Keys (Authorization Audit)
// ─────────────────────────────────────────────

export interface AdminApiKeyListItem {
  id: string
  name: string
  key_prefix: string
  user_id: string
  username: string
  is_active: boolean
  last_used_at: string | null
  created_at: string
}

export function listAllApiKeys(params?: { page?: number; page_size?: number }) {
  return http.get<PagedResult<AdminApiKeyListItem>>('/admin/api-keys', { params })
}

import http from './http'

export interface RoleApplicationItem {
  id: string
  user_id: string
  username: string | null
  email: string | null
  display_name: string | null
  requested_role: number
  requested_role_label: string
  status: 'pending' | 'approved' | 'rejected'
  reason: string | null
  review_note: string | null
  reviewed_by: string | null
  created_at: string
  reviewed_at: string | null
}

export interface RoleApplicationListResponse {
  items: RoleApplicationItem[]
  total: number
  page: number
  page_size: number
}

export const listRoleApplications = (params?: { status?: string; page?: number; page_size?: number }) =>
  http.get<RoleApplicationListResponse>('/admin/role-applications', { params })

export const approveApplication = (id: string, payload: { department_id: string; review_note?: string }) =>
  http.post(`/admin/role-applications/${id}/approve`, payload)

export const rejectApplication = (id: string, review_note?: string) =>
  http.post(`/admin/role-applications/${id}/reject`, { review_note })

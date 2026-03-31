import http from './http'

export interface Organization {
  id: string
  name: string
  team_count: number
  created_at: string
}

export const listOrganizations = () =>
  http.get<{ items: Organization[] }>('/organizations')

export const createOrganization = (payload: { name: string }) =>
  http.post<Organization>('/organizations', payload)

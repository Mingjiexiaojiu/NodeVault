import http from './http'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
}

export interface UserNamespaceBrief {
  id: string
  slug: string
  display_name: string | null
  role: string
}

export interface UserInfo {
  id: string
  email: string
  username: string
  role: number
  role_label: string
  display_name: string | null
  avatar_url: string | null
  bio: string | null
  phone: string | null
  department: string | null
  title: string | null
  created_at: string
  namespaces: UserNamespaceBrief[]
}

export interface ProfilePayload {
  display_name?: string
  avatar_url?: string
  bio?: string
  phone?: string
  department?: string
  title?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export const login = (payload: LoginPayload) =>
  http.post<TokenResponse>('/auth/login', payload)

export const register = (payload: RegisterPayload) =>
  http.post<UserInfo>('/auth/register', payload)

export const getMe = () => http.get<UserInfo>('/auth/me')

export const updateProfile = (payload: ProfilePayload) =>
  http.patch<UserInfo>('/auth/profile', payload)

// ── API Key 管理 ──────────────────────────────────────────────

export interface ApiKeyInfo {
  id: string
  name: string
  key_prefix: string
  is_active: boolean
  created_at: string
  last_used_at: string | null
}

export interface ApiKeyCreated extends ApiKeyInfo {
  full_key: string
}

export const createApiKey = (name: string) =>
  http.post<ApiKeyCreated>('/auth/api-keys', { name })

export const listApiKeys = () =>
  http.get<ApiKeyInfo[]>('/auth/api-keys')

export const deleteApiKey = (id: string) =>
  http.delete(`/auth/api-keys/${id}`)

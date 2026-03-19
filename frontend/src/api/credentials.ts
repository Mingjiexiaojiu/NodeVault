import http from './http'

// ---------- Types ----------

export type AuthType = 'bearer_login' | 'bearer_static' | 'api_key' | 'basic'

export interface CredentialCreate {
  name: string
  base_url: string
  auth_type: AuthType
  // bearer_login
  login_endpoint?: string
  login_method?: string
  login_body_template?: string
  username?: string
  password?: string
  token_json_path?: string
  token_ttl?: number
  // bearer_static
  static_token?: string
  // api_key
  api_key_header?: string
  api_key_value?: string
}

export interface CredentialResponse {
  id: string
  name: string
  base_url: string
  auth_type: AuthType
  login_endpoint: string | null
  api_key_header: string | null
  token_json_path: string | null
  token_ttl: number | null
  created_at: string
  updated_at: string
}

// ---------- API ----------

export const createCredential = (payload: CredentialCreate) =>
  http.post<CredentialResponse>('/credentials', payload)

export const listCredentials = () =>
  http.get<CredentialResponse[]>('/credentials')

export const getCredential = (id: string) =>
  http.get<CredentialResponse>(`/credentials/${id}`)

export const deleteCredential = (id: string) =>
  http.delete(`/credentials/${id}`)

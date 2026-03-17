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

export interface UserInfo {
  id: string
  email: string
  username: string
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

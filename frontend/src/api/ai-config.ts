import http from './http'

// ---------- Types ----------

export type AIProvider = 'openai' | 'claude' | 'custom'

export interface AIConfigCreate {
  name: string
  provider: AIProvider
  model: string
  api_key: string
  base_url?: string
  is_default?: boolean
}

export interface AIConfigUpdate {
  name?: string
  provider?: AIProvider
  model?: string
  api_key?: string
  base_url?: string
  is_default?: boolean
}

export interface AIConfigItem {
  id: string
  name: string
  provider: AIProvider
  model: string
  api_key_masked: string
  base_url: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface AIConfigTestPayload {
  provider: AIProvider
  model: string
  api_key: string
  base_url?: string
}

export interface AIConfigTestResult {
  ok: boolean
  message?: string
  latency_ms?: number
}

// ---------- API ----------

export async function getAIConfigs(): Promise<AIConfigItem[]> {
  const res = await http.get('/ai-configs')
  return res.data
}

export async function createAIConfig(payload: AIConfigCreate): Promise<AIConfigItem> {
  const res = await http.post('/ai-configs', payload)
  return res.data
}

export async function updateAIConfig(id: string, payload: AIConfigUpdate): Promise<AIConfigItem> {
  const res = await http.patch(`/ai-configs/${id}`, payload)
  return res.data
}

export async function deleteAIConfig(id: string): Promise<void> {
  await http.delete(`/ai-configs/${id}`)
}

export async function testAIConfig(payload: AIConfigTestPayload): Promise<AIConfigTestResult> {
  const res = await http.post('/ai-configs/test', payload)
  return res.data
}

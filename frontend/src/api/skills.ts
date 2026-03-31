import http from './http'

// ---------- Types ----------

export interface SkillCreate {
  display_name: string
  name?: string
  description?: string
}

export interface SkillUpdate {
  display_name?: string
  description?: string
  status?: string
}

export interface SkillNodeItem {
  id: string
  name: string
  display_name: string | null
  usage_hint: string | null
  category_name: string | null
  sort_order: number
}

export interface SkillVersionCreate {
  version: string
  skill_md: string
  release_notes?: string
  is_default?: boolean
}

export interface SkillVersion {
  id: string
  skill_id: string
  version: string
  skill_md: string
  node_snapshot: Record<string, unknown>[]
  release_notes: string | null
  is_default: boolean
  created_at: string
}

export interface SkillItem {
  id: string
  name: string
  display_name: string
  description: string | null
  owner_id: string
  status: string
  is_stale: boolean
  is_system: boolean
  node_count: number
  latest_version: string | null
  created_at: string
  updated_at: string
}

export interface SkillDetail extends SkillItem {
  nodes: SkillNodeItem[]
  versions: SkillVersion[]
}

export interface GenerateResult {
  skill_md: string
  suggested_version: string
}

// ---------- API functions ----------

export async function getSkills(params?: { skip?: number; limit?: number }): Promise<SkillItem[]> {
  const res = await http.get('/skills', { params })
  return res.data
}

export async function createSkill(payload: SkillCreate): Promise<SkillDetail> {
  const res = await http.post('/skills', payload)
  return res.data
}

export async function getSkillDetail(skillId: string): Promise<SkillDetail> {
  const res = await http.get(`/skills/${skillId}`)
  return res.data
}

export async function updateSkill(skillId: string, payload: SkillUpdate): Promise<SkillDetail> {
  const res = await http.patch(`/skills/${skillId}`, payload)
  return res.data
}

export async function deleteSkill(skillId: string): Promise<void> {
  await http.delete(`/skills/${skillId}`)
}

export async function getSkillVersions(skillId: string): Promise<SkillVersion[]> {
  const res = await http.get(`/skills/${skillId}/versions`)
  return res.data
}

export async function createSkillVersion(skillId: string, payload: SkillVersionCreate): Promise<SkillVersion> {
  const res = await http.post(`/skills/${skillId}/versions`, payload)
  return res.data
}

export async function generateSkillMd(skillId: string, configId?: string): Promise<GenerateResult> {
  const res = await http.post(`/skills/${skillId}/generate`, configId ? { config_id: configId } : {})
  return res.data
}

export async function downloadSkillZip(skillId: string, version?: string): Promise<Blob> {
  const res = await http.get(`/skills/${skillId}/export`, {
    params: version ? { version } : undefined,
    responseType: 'blob',
  })
  return res.data
}

// ---------- M2M: Skill ↔ Node ----------

export interface AddNodePayload {
  node_id: string
  usage_hint?: string
}

export async function addNodeToSkill(skillId: string, payload: AddNodePayload): Promise<void> {
  await http.post(`/skills/${skillId}/nodes`, payload)
}

export async function removeNodeFromSkill(skillId: string, nodeId: string): Promise<void> {
  await http.delete(`/skills/${skillId}/nodes/${nodeId}`)
}

export async function updateSkillNode(skillId: string, nodeId: string, payload: { usage_hint?: string }): Promise<void> {
  await http.patch(`/skills/${skillId}/nodes/${nodeId}`, payload)
}

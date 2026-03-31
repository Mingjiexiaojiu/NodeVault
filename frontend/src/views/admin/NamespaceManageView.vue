<template>
  <div class="space-y-5">
    <!-- 顶部栏 -->
    <div class="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <input
        v-model="q"
        @input="onSearch"
        type="text"
        placeholder="搜索组织或团队…"
        class="text-sm border border-gray-200 rounded-xl px-3 py-2 w-60 focus:outline-none focus:ring-2 focus:ring-indigo-300"
      />
      <span class="text-sm text-gray-400 ml-auto">{{ orgTree.length }} 个组织 · {{ totalTeams }} 个团队</span>
      <button
        @click="showCreateOrg = true"
        class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium text-white transition-colors"
        style="background: #6366f1"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        新建组织
      </button>
    </div>

    <!-- 树状列表 -->
    <div class="space-y-3">
      <div v-if="loading" class="bg-white rounded-2xl flex items-center justify-center h-48" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="orgTree.length === 0" class="bg-white rounded-2xl py-16 text-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <svg class="w-10 h-10 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
        <p class="text-sm text-gray-400">暂无组织</p>
        <p class="text-xs text-gray-300 mt-1">点击「新建组织」开始创建</p>
      </div>

      <template v-else>
        <div
          v-for="org in filteredTree"
          :key="org.name"
          class="bg-white rounded-2xl overflow-hidden"
          style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)"
        >
          <!-- 组织头部 -->
          <div
            class="flex items-center gap-3 px-5 py-4 cursor-pointer select-none hover:bg-gray-50/60 transition-colors"
            @click="toggleOrg(org.name)"
          >
            <svg
              class="w-4 h-4 text-gray-400 transition-transform duration-200 shrink-0"
              :class="expandedOrgs.has(org.name) ? 'rotate-90' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            ><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
              <span class="text-white text-xs font-bold">{{ org.name.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-sm font-semibold text-gray-900">{{ org.name }}</div>
              <div class="text-xs text-gray-400">{{ org.teams.length }} 个团队 · {{ org.totalMembers }} 人 · {{ org.totalNodes }} 个节点</div>
            </div>
            <button
              @click.stop="startCreateTeam(org.name)"
              class="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-indigo-600 hover:bg-indigo-50 transition-colors"
              title="在此组织下新建团队"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
              添加团队
            </button>
          </div>

          <!-- 团队列表（展开时显示） -->
          <div v-if="expandedOrgs.has(org.name)" class="border-t border-gray-100">
            <div v-if="org.teams.length === 0" class="px-5 py-6 text-center text-xs text-gray-400">
              暂无团队，点击「添加团队」创建第一个
            </div>
            <div v-else class="divide-y divide-gray-50">
              <div
                v-for="team in org.teams"
                :key="team.id"
                class="flex items-center gap-3 px-5 py-3.5 pl-[3.25rem] hover:bg-gray-50/60 transition-colors group"
              >
                <!-- 树线 -->
                <div class="w-4 flex items-center justify-center shrink-0">
                  <div class="w-px h-full bg-gray-200 absolute" style="display:none"></div>
                  <svg class="w-4 h-4 text-gray-300" viewBox="0 0 16 16" fill="none">
                    <path d="M4 0v8h8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="w-7 h-7 rounded-md bg-gray-100 flex items-center justify-center shrink-0">
                  <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium text-gray-900">{{ team.team_name }}</div>
                  <div class="text-xs text-gray-400">
                    {{ team.member_count }} 人 · {{ team.node_count }} 个节点
                    <template v-if="team.owner_username"> · 负责人: {{ team.owner_username }}</template>
                  </div>
                </div>
                <div class="text-xs text-gray-300 shrink-0">{{ team.created_at?.slice(0, 10) }}</div>
                <button
                  @click="confirmDelete(team)"
                  class="shrink-0 p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
                  title="删除团队"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 新建组织弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateOrg" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="showCreateOrg = false">
        <div class="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
          <h3 class="text-base font-semibold text-gray-900 mb-4">新建组织</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">组织名称 <span class="text-red-500">*</span></label>
              <input
                v-model="orgForm.name"
                type="text"
                placeholder="如 AI 中心"
                class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                @keyup.enter="doCreateOrg"
              />
            </div>
            <p v-if="orgError" class="text-xs text-red-500">{{ orgError }}</p>
          </div>
          <div class="flex gap-2 justify-end mt-5">
            <button @click="showCreateOrg = false; orgError = ''" class="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50">取消</button>
            <button
              @click="doCreateOrg"
              :disabled="creatingOrg"
              class="px-4 py-2 text-sm rounded-xl text-white font-medium transition-colors disabled:opacity-60"
              style="background: #6366f1"
            >{{ creatingOrg ? '创建中…' : '创建' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 新建团队弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateTeam" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="showCreateTeam = false">
        <div class="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
          <h3 class="text-base font-semibold text-gray-900 mb-1">添加团队</h3>
          <p class="text-xs text-gray-400 mb-4">组织：<span class="text-gray-600 font-medium">{{ teamForm.org_name }}</span></p>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">团队名称 <span class="text-red-500">*</span></label>
              <input
                v-model="teamForm.team_name"
                type="text"
                placeholder="如 算法组"
                class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                @keyup.enter="doCreateTeam"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">简介（可选）</label>
              <textarea
                v-model="teamForm.description"
                rows="2"
                placeholder="团队描述"
                class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
              />
            </div>
            <p v-if="teamError" class="text-xs text-red-500">{{ teamError }}</p>
          </div>
          <div class="flex gap-2 justify-end mt-5">
            <button @click="showCreateTeam = false; teamError = ''" class="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50">取消</button>
            <button
              @click="doCreateTeam"
              :disabled="creatingTeam"
              class="px-4 py-2 text-sm rounded-xl text-white font-medium transition-colors disabled:opacity-60"
              style="background: #6366f1"
            >{{ creatingTeam ? '创建中…' : '创建' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deleteTarget = null">
        <div class="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
          <h3 class="text-base font-semibold text-gray-900 mb-2">删除团队</h3>
          <p class="text-sm text-gray-600 mb-2">
            确定要永久删除团队 <span class="font-semibold text-gray-900">{{ deleteTarget.organization_name }} / {{ deleteTarget.team_name }}</span> 吗？该操作不可撤销。
          </p>
          <p v-if="deleteTarget.member_count > 0" class="text-sm text-amber-600 bg-amber-50 rounded-xl px-3 py-2 mb-4">
            该团队当前有 <span class="font-semibold">{{ deleteTarget.member_count }}</span> 名成员，删除前请先移除所有成员。
          </p>
          <p v-if="deleteError" class="text-sm text-red-600 bg-red-50 rounded-xl px-3 py-2 mb-4">{{ deleteError }}</p>
          <div class="flex gap-2 justify-end">
            <button @click="deleteTarget = null; deleteError = ''" class="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50">取消</button>
            <button
              @click="doDelete"
              :disabled="deleting || deleteTarget.member_count > 0"
              class="px-4 py-2 text-sm rounded-xl text-white font-medium bg-red-500 hover:bg-red-600 transition-colors disabled:opacity-60"
            >{{ deleting ? '删除中…' : '确认删除' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listAllDepartments, adminCreateDepartment, adminDeleteDepartment, type AdminDepartmentListItem } from '@/api/admin'
import { listOrganizations, createOrganization } from '@/api/organizations'

const allDepts = ref<AdminDepartmentListItem[]>([])
const allOrgNames = ref<string[]>([])
const loading = ref(false)
const q = ref('')
let searchTimer: ReturnType<typeof setTimeout>

// ── 展开状态 ──────────────────────────────
const expandedOrgs = ref<Set<string>>(new Set())

function toggleOrg(name: string) {
  if (expandedOrgs.value.has(name)) {
    expandedOrgs.value.delete(name)
  } else {
    expandedOrgs.value.add(name)
  }
}

// ── 树状数据 ──────────────────────────────
interface OrgNode {
  name: string
  teams: AdminDepartmentListItem[]
  totalMembers: number
  totalNodes: number
}

const orgTree = computed<OrgNode[]>(() => {
  const map = new Map<string, AdminDepartmentListItem[]>()
  // 先把所有组织名注册进去（包括没有团队的）
  for (const name of allOrgNames.value) {
    if (!map.has(name)) map.set(name, [])
  }
  for (const d of allDepts.value) {
    const key = d.organization_name
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(d)
  }
  return Array.from(map.entries())
    .map(([name, teams]) => ({
      name,
      teams,
      totalMembers: teams.reduce((s, t) => s + t.member_count, 0),
      totalNodes: teams.reduce((s, t) => s + t.node_count, 0),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const filteredTree = computed(() => {
  if (!q.value.trim()) return orgTree.value
  const keyword = q.value.trim().toLowerCase()
  return orgTree.value
    .map(org => ({
      ...org,
      teams: org.teams.filter(t =>
        t.team_name.toLowerCase().includes(keyword) ||
        t.organization_name.toLowerCase().includes(keyword)
      ),
    }))
    .filter(org => org.name.toLowerCase().includes(keyword) || org.teams.length > 0)
})

const totalTeams = computed(() => allDepts.value.length)

// ── 创建组织 ──────────────────────────────
const showCreateOrg = ref(false)
const creatingOrg = ref(false)
const orgError = ref('')
const orgForm = ref({ name: '' })

async function doCreateOrg() {
  orgError.value = ''
  if (!orgForm.value.name.trim()) {
    orgError.value = '组织名称不能为空'
    return
  }
  creatingOrg.value = true
  try {
    await createOrganization({ name: orgForm.value.name.trim() })
    showCreateOrg.value = false
    orgForm.value = { name: '' }
    // 组织创建后不需要刷新部门列表，因为组织还没有团队
    // 但为了在树上显示空组织，需要手动加一条
    await load()
  } catch (e: any) {
    orgError.value = e?.response?.data?.detail || '创建失败'
  } finally {
    creatingOrg.value = false
  }
}

// ── 创建团队 ──────────────────────────────
const showCreateTeam = ref(false)
const creatingTeam = ref(false)
const teamError = ref('')
const teamForm = ref({ org_name: '', team_name: '', description: '' })

function startCreateTeam(orgName: string) {
  teamForm.value = { org_name: orgName, team_name: '', description: '' }
  teamError.value = ''
  showCreateTeam.value = true
}

async function doCreateTeam() {
  teamError.value = ''
  if (!teamForm.value.team_name.trim()) {
    teamError.value = '团队名称不能为空'
    return
  }
  creatingTeam.value = true
  try {
    await adminCreateDepartment({
      org_name: teamForm.value.org_name,
      team_name: teamForm.value.team_name.trim(),
      description: teamForm.value.description || undefined,
    })
    showCreateTeam.value = false
    teamForm.value = { org_name: '', team_name: '', description: '' }
    await load()
    // 确保新团队所属组织展开
    expandedOrgs.value.add(teamForm.value.org_name || teamForm.value.org_name)
  } catch (e: any) {
    teamError.value = e?.response?.data?.detail || '创建失败'
  } finally {
    creatingTeam.value = false
  }
}

// ── 删除 ──────────────────────────────────
const deleteTarget = ref<AdminDepartmentListItem | null>(null)
const deleting = ref(false)
const deleteError = ref('')

function confirmDelete(ns: AdminDepartmentListItem) {
  deleteTarget.value = ns
  deleteError.value = ''
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await adminDeleteDepartment(String(deleteTarget.value.id))
    deleteTarget.value = null
    await load()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || e?.response?.data?.error?.message
    deleteError.value = detail || '删除失败，请稍后重试'
  } finally {
    deleting.value = false
  }
}

// ── 加载 ──────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [deptRes, orgRes] = await Promise.all([
      listAllDepartments({ page: 1, page_size: 500 }),
      listOrganizations(),
    ])
    allDepts.value = deptRes.data.items
    allOrgNames.value = orgRes.data.items.map((o: { name: string }) => o.name)
    // 默认展开所有组织
    for (const org of orgTree.value) {
      expandedOrgs.value.add(org.name)
    }
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {}, 350)
}

onMounted(load)
</script>

<template>
  <div>
    <!-- 加载态 -->
    <div v-if="loading" class="text-center py-20 text-gray-400">加载中...</div>

    <template v-else-if="dept">
      <!-- 页头 -->
      <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-2xl">
              {{ dept.team_name.charAt(0).toUpperCase() }}
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ dept.team_name }}</h1>
              <div class="flex items-center gap-3 mt-1 text-sm text-gray-500">
                <span class="font-mono bg-gray-100 px-2 py-0.5 rounded text-xs">{{ dept.organization_name }}</span>
                <span>拥有者：<strong class="text-gray-700">{{ dept.owner_username }}</strong></span>
                <span>{{ formatDate(dept.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="myRole" class="px-3 py-1 text-xs rounded-full" :class="myRole === 'admin' ? 'bg-indigo-100 text-indigo-700' : 'bg-green-50 text-green-600'">
              {{ myRole === 'admin' ? '主管' : '成员' }}
            </span>
            <button v-if="isAdmin" @click="editMode ? (editMode = false) : startEdit()" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              {{ editMode ? '取消编辑' : '编辑部门' }}
            </button>
          </div>
        </div>

        <!-- 编辑模式 -->
        <div v-if="editMode" class="mt-4 pt-4 border-t border-gray-100">
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">团队名称</label>
              <input v-model="editForm.team_name" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">团队简介</label>
              <textarea v-model="editForm.description" rows="3" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"></textarea>
            </div>
            <button @click="handleUpdate" :disabled="saving" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>

        <!-- 简介 -->
        <div v-else-if="dept.description" class="mt-4 pt-4 border-t border-gray-100">
          <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ dept.description }}</p>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div v-if="dept.stats" class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <div class="text-xs text-gray-400">节点数</div>
          <div class="text-xl font-bold text-gray-900 mt-1">{{ dept.stats.node_count }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <div class="text-xs text-gray-400">成员数</div>
          <div class="text-xl font-bold text-gray-900 mt-1">{{ dept.stats.member_count }}</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <div class="text-xs text-gray-400">总调用次数</div>
          <div class="text-xl font-bold text-indigo-600 mt-1">{{ dept.stats.total_invocations.toLocaleString() }}</div>
        </div>
      </div>

      <!-- 分布标签 -->
      <div v-if="dept.stats && (Object.keys(dept.stats.type_distribution).length || Object.keys(dept.stats.status_distribution).length)" class="flex flex-wrap gap-2 mb-6">
        <span v-for="(count, type) in dept.stats.type_distribution" :key="'t-'+type" class="px-2.5 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">{{ type }} ({{ count }})</span>
        <span v-for="(count, st) in dept.stats.status_distribution" :key="'s-'+st" class="px-2.5 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">{{ st }} ({{ count }})</span>
      </div>

      <!-- Tab 切换 -->
      <div class="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="px-4 py-2 text-sm rounded-md transition-all"
          :class="activeTab === tab.key ? 'bg-white text-indigo-600 shadow-sm font-medium' : 'text-gray-500 hover:text-gray-700'"
        >
          {{ tab.label }}
          <span class="ml-1 text-xs text-gray-400">({{ tab.count }})</span>
        </button>
      </div>

      <!-- 成员列表 -->
      <div v-if="activeTab === 'members'">
        <!-- 添加成员 -->
        <div v-if="isAdmin" class="bg-white rounded-xl border border-gray-200 p-4 mb-4">
          <form @submit.prevent="handleAddMember" class="flex items-end gap-3">
            <div class="flex-1">
              <label class="block text-xs font-medium text-gray-500 mb-1">用户名</label>
              <input v-model="newMemberUsername" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500" placeholder="输入要添加的用户名" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">角色</label>
              <select v-model="newMemberRole" class="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500">
                <option value="member">成员</option>
                <option value="admin">主管</option>
              </select>
            </div>
            <button type="submit" :disabled="addingMember || !newMemberUsername.trim()" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              添加
            </button>
          </form>
          <p v-if="memberError" class="text-sm text-red-600 mt-2">{{ memberError }}</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">加入时间</th>
                <th v-if="isAdmin" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in dept.members" :key="m.user_id" class="border-b border-gray-50 hover:bg-gray-50">
                <td class="px-6 py-3.5">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-medium text-gray-600">
                      {{ m.username.charAt(0).toUpperCase() }}
                    </div>
                    <div>
                      <div class="text-sm font-medium text-gray-900">{{ m.username }}</div>
                      <div class="text-xs text-gray-400">{{ m.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-3.5">
                  <span class="px-2 py-0.5 text-xs rounded-full" :class="m.role === 'admin' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'">
                    {{ m.role === 'admin' ? '主管' : '成员' }}
                  </span>
                </td>
                <td class="px-6 py-3.5 text-sm text-gray-500">{{ formatDate(m.joined_at) }}</td>
                <td v-if="isAdmin" class="px-6 py-3.5 text-right">
                  <button
                    v-if="m.user_id !== dept.owner_id"
                    @click="handleRemoveMember(m.user_id, m.username)"
                    class="text-xs text-red-500 hover:text-red-700"
                  >移除</button>
                  <span v-else class="text-xs text-gray-300">拥有者</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 节点列表 -->
      <div v-else-if="activeTab === 'nodes'">
        <div v-if="dept.nodes.length === 0" class="text-center py-16 text-gray-400">该部门暂无节点</div>
        <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">节点</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标签</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in dept.nodes" :key="n.id" class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer" @click="$router.push(`/nodes/${n.id}`)">
                <td class="px-6 py-3.5">
                  <div class="text-sm font-medium text-gray-900">{{ n.display_name || n.name }}</div>
                  <div class="text-xs text-gray-400 font-mono">{{ n.name }}</div>
                </td>
                <td class="px-6 py-3.5">
                  <span class="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded-full">{{ n.type }}</span>
                </td>
                <td class="px-6 py-3.5">
                  <StatusBadge :status="n.status" />
                </td>
                <td class="px-6 py-3.5">
                  <div class="flex gap-1 flex-wrap">
                    <span v-for="tag in n.tags.slice(0, 3)" :key="tag" class="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs">{{ tag }}</span>
                  </div>
                </td>
                <td class="px-6 py-3.5 text-sm text-gray-500">{{ formatDate(n.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="flex flex-col items-center justify-center py-24 gap-4">
      <div class="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
        <svg class="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v3m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        </svg>
      </div>
      <p class="text-gray-700 font-medium">{{ loadError || '部门不存在' }}</p>
      <button @click="$router.push('/departments')" class="px-4 py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors">
        返回部门列表
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getDepartment, updateDepartment, addMember, removeMember, type DepartmentDetail } from '@/api/departments'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const authStore = useAuthStore()
const deptId = route.params.id as string

const dept = ref<DepartmentDetail | null>(null)
const loading = ref(true)
const loadError = ref<string | null>(null)
const activeTab = ref<'members' | 'nodes'>('nodes')

const tabs = computed(() => [
  { key: 'nodes' as const, label: '节点', count: dept.value?.nodes.length ?? 0 },
  { key: 'members' as const, label: '成员', count: dept.value?.members.length ?? 0 },
])

const myRole = computed(() => {
  return authStore.user?.departments?.find(ns => ns.id === deptId)?.role ?? null
})
const isAdmin = computed(() => myRole.value === 'admin')

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function loadDept() {
  loading.value = true
  loadError.value = null
  try {
    const res = await getDepartment(deptId)
    dept.value = res.data
  } catch (e: any) {
    dept.value = null
    const status = e?.response?.status
    if (status === 404) {
      loadError.value = '部门不存在或已被删除'
    } else if (status === 403) {
      loadError.value = '无权限访问该部门'
    } else if (status === 401) {
      loadError.value = '请先登录'
    } else {
      loadError.value = e?.uiMessage || '加载失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

// ── 编辑部门 ──
const editMode = ref(false)
const saving = ref(false)
const editForm = ref({ team_name: '', description: '' })

function startEdit() {
  editForm.value = {
    team_name: dept.value?.team_name ?? '',
    description: dept.value?.description ?? '',
  }
  editMode.value = true
}

async function handleUpdate() {
  saving.value = true
  try {
    await updateDepartment(deptId, editForm.value)
    editMode.value = false
    await loadDept()
  } catch {
    // ignore
  } finally {
    saving.value = false
  }
}

// ── 成员管理 ──
const newMemberUsername = ref('')
const newMemberRole = ref('member')
const addingMember = ref(false)
const memberError = ref('')

async function handleAddMember() {
  addingMember.value = true
  memberError.value = ''
  try {
    await addMember(deptId, { username: newMemberUsername.value.trim(), role: newMemberRole.value })
    newMemberUsername.value = ''
    await Promise.all([loadDept(), authStore.fetchMe()])
  } catch (e: any) {
    memberError.value = e?.response?.data?.error?.message || e?.message || '添加失败'
  } finally {
    addingMember.value = false
  }
}

async function handleRemoveMember(userId: string, username: string) {
  if (!confirm(`确定移除成员 ${username}？`)) return
  try {
    await removeMember(deptId, userId)
    await loadDept()
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadDept()
  // 初始编辑表单
  if (dept.value) {
    editForm.value = {
      team_name: dept.value.team_name ?? '',
      description: dept.value.description ?? '',
    }
  }
})
</script>

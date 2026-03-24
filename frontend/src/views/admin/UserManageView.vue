<template>
  <div class="space-y-5">
    <!-- 搜索与过滤 -->
    <div class="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div class="relative flex-1 min-w-48">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          v-model="searchQ"
          @input="debouncedSearch"
          type="text"
          placeholder="搜索用户名或邮箱..."
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-300 transition"
        />
      </div>
      <select v-model="filterRole" @change="loadUsers" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300">
        <option value="">全部角色</option>
        <option value="0">超级管理员</option>
        <option value="1">主管</option>
        <option value="2">普通用户</option>
      </select>
      <select v-model="filterActive" @change="loadUsers" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300">
        <option value="">全部状态</option>
        <option value="true">正常</option>
        <option value="false">已封禁</option>
      </select>
      <span class="text-sm text-gray-400 ml-auto">共 {{ total }} 名用户</span>
    </div>

    <!-- 用户表格 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">用户</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">角色</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">注册时间</th>
            <th class="text-right px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
                  {{ (user.display_name || user.username).charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="font-medium text-gray-900">{{ user.display_name || user.username }}</div>
                  <div class="text-xs text-gray-400">{{ user.email }}</div>
                </div>
              </div>
            </td>
            <td class="px-4 py-3.5">
              <select
                :value="user.role"
                @change="changeRole(user, Number(($event.target as HTMLSelectElement).value))"
                class="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                :class="user.role === 0 ? 'border-purple-200 text-purple-700' : user.role === 1 ? 'border-blue-200 text-blue-700' : 'border-gray-200 text-gray-600'"
              >
                <option value="0">超级管理员</option>
                <option value="1">主管</option>
                <option value="2">普通用户</option>
              </select>
            </td>
            <td class="px-4 py-3.5">
              <span
                class="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full"
                :class="user.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-green-500' : 'bg-red-400'"></span>
                {{ user.is_active ? '正常' : '已封禁' }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-gray-500 text-xs">{{ formatDate(user.created_at) }}</td>
            <td class="px-5 py-3.5 text-right">
              <button
                @click="toggleBan(user)"
                class="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                :class="user.is_active ? 'text-red-500 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'"
              >
                {{ user.is_active ? '封禁' : '解封' }}
              </button>
              <button
                @click="confirmDelete(user)"
                class="text-xs font-medium px-3 py-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors ml-1"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!loading && users.length === 0">
            <td colspan="5" class="text-center py-16 text-gray-400">暂无用户</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button
        v-for="p in totalPages" :key="p"
        @click="page = p; loadUsers()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
      >{{ p }}</button>
    </div>

    <!-- 确认对话框 -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white rounded-2xl p-6 w-80 shadow-2xl">
        <h3 class="font-semibold text-gray-900 mb-2">确认删除用户？</h3>
        <p class="text-sm text-gray-500 mb-5">将删除用户 <strong>{{ deleteTarget.username }}</strong> 及其所有数据，此操作不可逆。</p>
        <div class="flex gap-2 justify-end">
          <button @click="deleteTarget = null" class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-xl transition-colors">取消</button>
          <button @click="doDelete" class="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors">确认删除</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-full shadow-lg z-50 transition-all">
      {{ toast }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listUsers, updateUserStatus, updateUserRole, deleteUser } from '@/api/admin'
import type { AdminUserListItem } from '@/api/admin'

const users = ref<AdminUserListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const searchQ = ref('')
const filterRole = ref('')
const filterActive = ref('')
const toast = ref('')
const deleteTarget = ref<AdminUserListItem | null>(null)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

let searchTimer: ReturnType<typeof setTimeout>
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadUsers() }, 350)
}

async function loadUsers() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (searchQ.value) params.q = searchQ.value
    if (filterRole.value !== '') params.role = Number(filterRole.value)
    if (filterActive.value !== '') params.is_active = filterActive.value === 'true'

    const res = await listUsers(params as Parameters<typeof listUsers>[0])
    users.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function toggleBan(user: AdminUserListItem) {
  try {
    await updateUserStatus(user.id, !user.is_active)
    user.is_active = !user.is_active
    showToast(user.is_active ? '用户已解封' : '用户已封禁')
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    showToast(err?.uiMessage || '操作失败')
  }
}

async function changeRole(user: AdminUserListItem, newRole: number) {
  try {
    await updateUserRole(user.id, newRole)
    user.role = newRole
    showToast('角色已更新')
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    showToast(err?.uiMessage || '操作失败')
    await loadUsers() // reload to reset select
  }
}

function confirmDelete(user: AdminUserListItem) {
  deleteTarget.value = user
}

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await deleteUser(deleteTarget.value.id)
    showToast('用户已删除')
    deleteTarget.value = null
    await loadUsers()
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    showToast(err?.uiMessage || '删除失败')
    deleteTarget.value = null
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

let toastTimer: ReturnType<typeof setTimeout>
function showToast(msg: string) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2500)
}

onMounted(loadUsers)
</script>

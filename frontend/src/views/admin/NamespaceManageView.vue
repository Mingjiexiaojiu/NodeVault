<template>
  <div class="space-y-5">
    <!-- 过滤栏 -->
    <div class="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <input
        v-model="q"
        @input="onSearch"
        type="text"
        placeholder="搜索部门名称或 slug…"
        class="text-sm border border-gray-200 rounded-xl px-3 py-2 w-60 focus:outline-none focus:ring-2 focus:ring-indigo-300"
      />
      <span class="text-sm text-gray-400 ml-auto">共 {{ total }} 个部门</span>
      <button
        @click="showCreate = true"
        class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium text-white transition-colors"
        style="background: #6366f1"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        新建部门
      </button>
    </div>

    <!-- 表格 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">部门</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">所有者</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">成员数</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">节点数</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
            <th class="px-4 py-3.5"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="ns in namespaces" :key="ns.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5">
              <div class="font-medium text-gray-900">{{ ns.display_name || ns.slug }}</div>
              <div class="text-xs text-gray-400 font-mono">{{ ns.slug }}</div>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.owner_username || '—' }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.member_count }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.node_count }}</td>
            <td class="px-4 py-3.5 text-gray-400 text-xs">{{ ns.created_at?.slice(0, 10) }}</td>
            <td class="px-4 py-3.5 text-right">
              <button
                @click="confirmDelete(ns)"
                class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="删除部门"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </td>
          </tr>
          <tr v-if="!loading && namespaces.length === 0">
            <td colspan="6" class="text-center py-16 text-gray-400">暂无部门</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button
        v-for="p in totalPages" :key="p"
        @click="page = p; load()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
      >{{ p }}</button>
    </div>

    <!-- 新建部门弹窗 -->
    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="showCreate = false">
      <div class="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h3 class="text-base font-semibold text-gray-900 mb-4">新建部门</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">部门标识 (slug)</label>
            <input
              v-model="form.slug"
              type="text"
              placeholder="如 ai-team（小写字母、数字、-、_）"
              class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">显示名称</label>
            <input
              v-model="form.display_name"
              type="text"
              placeholder="如 AI 团队"
              class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">简介（可选）</label>
            <textarea
              v-model="form.description"
              rows="2"
              placeholder="部门描述"
              class="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
            />
          </div>
          <p v-if="createError" class="text-xs text-red-500">{{ createError }}</p>
        </div>
        <div class="flex gap-2 justify-end mt-5">
          <button @click="showCreate = false; createError = ''" class="px-4 py-2 text-sm rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50">取消</button>
          <button
            @click="doCreate"
            :disabled="creating"
            class="px-4 py-2 text-sm rounded-xl text-white font-medium transition-colors disabled:opacity-60"
            style="background: #6366f1"
          >{{ creating ? '创建中…' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="deleteTarget = null">
      <div class="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
        <h3 class="text-base font-semibold text-gray-900 mb-2">删除部门</h3>
        <p class="text-sm text-gray-600 mb-2">
          确定要永久删除部门 <span class="font-semibold text-gray-900">{{ deleteTarget.display_name || deleteTarget.slug }}</span> 吗？该操作不可撤销。
        </p>
        <p v-if="deleteTarget.member_count > 0" class="text-sm text-amber-600 bg-amber-50 rounded-xl px-3 py-2 mb-4">
          该部门当前有 <span class="font-semibold">{{ deleteTarget.member_count }}</span> 名成员，删除前请先移除所有成员。
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listAllDepartments, adminCreateDepartment, adminDeleteDepartment, type AdminDepartmentListItem } from '@/api/admin'

const namespaces = ref<AdminDepartmentListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const q = ref('')
let searchTimer: ReturnType<typeof setTimeout>

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ── 创建 ──────────────────────────────────
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = ref({ slug: '', display_name: '', description: '' })

async function doCreate() {
  createError.value = ''
  if (!form.value.slug || !form.value.display_name) {
    createError.value = '标识和名称不能为空'
    return
  }
  creating.value = true
  try {
    await adminCreateDepartment({
      slug: form.value.slug,
      display_name: form.value.display_name,
      description: form.value.description || undefined,
    })
    showCreate.value = false
    form.value = { slug: '', display_name: '', description: '' }
    page.value = 1
    await load()
  } catch (e: any) {
    createError.value = e?.response?.data?.detail || '创建失败'
  } finally {
    creating.value = false
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

// ── 列表 ──────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res = await listAllDepartments({ page: page.value, page_size: pageSize })
    namespaces.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 350)
}

onMounted(load)
</script>

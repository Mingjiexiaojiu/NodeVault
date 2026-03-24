<template>
  <div class="space-y-5">
    <!-- 过滤栏 -->
    <div class="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <select v-model="filterStatus" @change="loadNodes" class="text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300">
        <option value="">全部状态</option>
        <option value="active">运行中</option>
        <option value="draft">草稿</option>
        <option value="disabled">已禁用</option>
        <option value="deprecated">已弃用</option>
      </select>
      <span class="text-sm text-gray-400 ml-auto">共 {{ total }} 个节点</span>
    </div>

    <!-- 节点表格 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">节点名称</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">命名空间</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">所有者</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">调用次数</th>
            <th class="text-right px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="node in nodes" :key="node.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5">
              <div class="font-medium text-gray-900">{{ node.display_name || node.name }}</div>
              <div class="text-xs text-gray-400 font-mono">{{ node.name }}</div>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ node.namespace_slug || '—' }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ node.owner_username || '—' }}</td>
            <td class="px-4 py-3.5">
              <span
                class="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full"
                :class="statusStyle(node.status)"
              >
                {{ statusLabel(node.status) }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ node.invocation_count.toLocaleString() }}</td>
            <td class="px-5 py-3.5 text-right">
              <button
                v-if="node.status !== 'disabled'"
                @click="setNodeStatus(node, 'disabled')"
                class="text-xs font-medium px-3 py-1.5 rounded-lg text-red-500 hover:bg-red-50 transition-colors"
              >下线</button>
              <button
                v-else
                @click="setNodeStatus(node, 'active')"
                class="text-xs font-medium px-3 py-1.5 rounded-lg text-green-600 hover:bg-green-50 transition-colors"
              >恢复</button>
            </td>
          </tr>
          <tr v-if="!loading && nodes.length === 0">
            <td colspan="6" class="text-center py-16 text-gray-400">暂无节点</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button
        v-for="p in totalPages" :key="p"
        @click="page = p; loadNodes()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
      >{{ p }}</button>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-full shadow-lg z-50">
      {{ toast }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listAllNodes, updateNodeStatus } from '@/api/admin'
import type { AdminNodeListItem } from '@/api/admin'

const nodes = ref<AdminNodeListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const filterStatus = ref('')
const toast = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize))

async function loadNodes() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await listAllNodes(params as Parameters<typeof listAllNodes>[0])
    nodes.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function setNodeStatus(node: AdminNodeListItem, newStatus: string) {
  try {
    await updateNodeStatus(node.id, newStatus)
    node.status = newStatus
    showToast(newStatus === 'disabled' ? '节点已下线' : '节点已恢复')
  } catch (e: unknown) {
    const err = e as { uiMessage?: string }
    showToast(err?.uiMessage || '操作失败')
  }
}

function statusLabel(s: string) {
  const map: Record<string, string> = { active: '运行中', draft: '草稿', disabled: '已禁用', deprecated: '已弃用' }
  return map[s] ?? s
}

function statusStyle(s: string) {
  if (s === 'active') return 'bg-green-50 text-green-700'
  if (s === 'disabled') return 'bg-red-50 text-red-600'
  if (s === 'deprecated') return 'bg-yellow-50 text-yellow-700'
  return 'bg-gray-100 text-gray-500'
}

let toastTimer: ReturnType<typeof setTimeout>
function showToast(msg: string) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2500)
}

onMounted(loadNodes)
</script>

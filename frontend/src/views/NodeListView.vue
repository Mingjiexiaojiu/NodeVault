<template>
  <div>
    <!-- 标题栏 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">节点管理</h1>
        <p class="text-sm text-gray-400 mt-0.5">管理所有注册的 AI 能力节点</p>
      </div>
      <RouterLink to="/nodes/new">
        <button class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
          </svg>
          注册新节点
        </button>
      </RouterLink>
    </div>

    <!-- 筛选栏 -->
    <div class="flex flex-wrap items-center gap-3 mb-5 bg-white rounded-2xl border border-gray-100 px-5 py-3.5" style="box-shadow: 0 1px 3px rgba(0,0,0,0.03)">
      <span class="text-xs font-medium text-gray-400 uppercase tracking-wide mr-1">筛选</span>
      <div class="flex items-center gap-1.5">
        <label class="text-xs text-gray-500">类型</label>
        <select
          v-model="filter.type"
          class="text-sm border border-gray-200 bg-gray-50 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
          @change="fetchNodes"
        >
          <option value="">全部</option>
          <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div class="flex items-center gap-1.5">
        <label class="text-xs text-gray-500">状态</label>
        <select
          v-model="filter.status"
          class="text-sm border border-gray-200 bg-gray-50 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
          @change="fetchNodes"
        >
          <option value="">全部</option>
          <option v-for="s in nodeStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
    </div>

    <!-- 节点表格 -->
    <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <div v-if="loading" class="p-6 space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded animate-pulse" />
      </div>

      <EmptyState
        v-else-if="nodes.length === 0"
        description="没有找到符合条件的节点"
      >
        <RouterLink to="/nodes/new">
          <BaseButton variant="secondary" class="mt-2">注册第一个节点</BaseButton>
        </RouterLink>
      </EmptyState>

      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50/80 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">名称</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">类型</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">归属</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
            <th class="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="node in nodes"
            :key="node.id"
            class="hover:bg-indigo-50/40 cursor-pointer transition-colors group"
            @click="$router.push(`/nodes/${node.id}`)"
          >
            <td class="px-6 py-4">
              <p class="font-medium text-gray-900">{{ node.display_name || node.name }}</p>
              <p class="text-xs text-gray-400 font-mono">{{ node.name }}</p>
            </td>
            <td class="px-6 py-4"><TypeBadge :type="node.type" /></td>
            <td class="px-6 py-4"><StatusBadge :status="node.status" /></td>
            <td class="px-6 py-4">
              <div class="flex flex-col">
                <span class="text-xs text-indigo-600 font-medium">{{ node.namespace_slug || '—' }}</span>
                <span class="text-xs text-gray-400">{{ node.owner_username || '—' }}</span>
              </div>
            </td>
            <td class="px-6 py-4 text-gray-400">{{ formatDate(node.created_at) }}</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div
        v-if="total > pageSize"
        class="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50"
      >
        <span class="text-sm text-gray-500">共 {{ total }} 条</span>
        <div class="flex gap-2">
          <BaseButton
            variant="secondary"
            :disabled="page <= 1"
            @click="changePage(page - 1)"
          >
            上一页
          </BaseButton>
          <BaseButton
            variant="secondary"
            :disabled="page * pageSize >= total"
            @click="changePage(page + 1)"
          >
            下一页
          </BaseButton>
        </div>
      </div>
    </div>
  </div>

  <!-- 删除节点确认弹窗 -->
  <div
    v-if="deletingNode"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    @click.self="deletingNode = null"
  >
    <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center shrink-0">
          <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <div>
          <h3 class="text-base font-semibold text-gray-900">删除节点</h3>
          <p class="text-sm text-gray-500 mt-0.5">此操作不可撤销</p>
        </div>
      </div>
      <p class="text-sm text-gray-600 mb-6">
        确定要删除节点 <span class="font-semibold text-gray-900">{{ deletingNode.display_name || deletingNode.name }}</span> 吗？
        删除后该节点的所有版本和调用日志将一并移除。
      </p>
      <div class="flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="deletingLoading" @click="deletingNode = null">取消</BaseButton>
        <button
          class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors disabled:opacity-50"
          :disabled="deletingLoading"
          @click="handleDeleteNode"
        >
          {{ deletingLoading ? '删除中...' : '确认删除' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listNodes, deleteNode } from '@/api/nodes'
import type { NodeItem, NodeType, NodeStatus } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TypeBadge from '@/components/TypeBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const nodes = ref<NodeItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(true)
const deletingNode = ref<NodeItem | null>(null)
const deletingLoading = ref(false)

const filter = reactive<{ type: NodeType | ''; status: NodeStatus | '' }>({
  type: '',
  status: '',
})

const nodeTypes = [
  { value: 'data_cleaning', label: '数据清洗' },
  { value: 'analysis', label: '分析' },
  { value: 'risk', label: '风控' },
  { value: 'nlp', label: 'NLP' },
  { value: 'vision', label: '视觉' },
  { value: 'ml', label: '机器学习' },
  { value: 'tool', label: '工具' },
  { value: 'utility', label: '实用程序' },
]

const nodeStatuses = [
  { value: 'draft', label: '草稿' },
  { value: 'active', label: '活跃' },
  { value: 'deprecated', label: '已弃用' },
  { value: 'archived', label: '已归档' },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function fetchNodes() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      mine: true,
      ...(filter.type ? { type: filter.type } : {}),
      ...(filter.status ? { status: filter.status } : {}),
    }
    const res = await listNodes(params)
    nodes.value = res.data
    total.value = res.data.length
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  fetchNodes()
}

async function handleDeleteNode() {
  if (!deletingNode.value) return
  deletingLoading.value = true
  try {
    await deleteNode(deletingNode.value.id)
    nodes.value = nodes.value.filter(n => n.id !== deletingNode.value!.id)
    total.value = Math.max(0, total.value - 1)
    deletingNode.value = null
  } catch {
    deletingNode.value = null
  } finally {
    deletingLoading.value = false
  }
}

onMounted(fetchNodes)
</script>

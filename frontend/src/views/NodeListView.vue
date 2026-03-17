<template>
  <div>
    <!-- 标题栏 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">节点管理</h1>
      <RouterLink to="/nodes/new">
        <BaseButton>注册新节点</BaseButton>
      </RouterLink>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex flex-wrap gap-4">
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-600">类型</label>
        <select
          v-model="filter.type"
          class="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @change="fetchNodes"
        >
          <option value="">全部</option>
          <option v-for="t in nodeTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-600">状态</label>
        <select
          v-model="filter.status"
          class="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @change="fetchNodes"
        >
          <option value="">全部</option>
          <option v-for="s in nodeStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
    </div>

    <!-- 节点表格 -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
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
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-3 text-left font-medium text-gray-500">名称</th>
            <th class="px-6 py-3 text-left font-medium text-gray-500">类型</th>
            <th class="px-6 py-3 text-left font-medium text-gray-500">状态</th>
            <th class="px-6 py-3 text-left font-medium text-gray-500">分类</th>
            <th class="px-6 py-3 text-left font-medium text-gray-500">创建时间</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="node in nodes"
            :key="node.id"
            class="hover:bg-gray-50 cursor-pointer transition-colors"
            @click="$router.push(`/nodes/${node.id}`)"
          >
            <td class="px-6 py-4">
              <p class="font-medium text-gray-900">{{ node.display_name || node.name }}</p>
              <p class="text-xs text-gray-400 font-mono">{{ node.name }}</p>
            </td>
            <td class="px-6 py-4"><TypeBadge :type="node.type" /></td>
            <td class="px-6 py-4"><StatusBadge :status="node.status" /></td>
            <td class="px-6 py-4 text-gray-500">{{ node.category || '—' }}</td>
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
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listNodes } from '@/api/nodes'
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
      ...(filter.type ? { type: filter.type } : {}),
      ...(filter.status ? { status: filter.status } : {}),
    }
    const res = await listNodes(params)
    nodes.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  fetchNodes()
}

onMounted(fetchNodes)
</script>

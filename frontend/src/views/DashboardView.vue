<template>
  <div>
    <!-- 标题 -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">欢迎，{{ auth.user?.username }} 👋</h1>
        <p class="text-gray-500 text-sm mt-1">这是你的 NodeVault 控制台</p>
      </div>
      <div class="flex gap-3">
        <RouterLink to="/nodes/new">
          <BaseButton>注册新节点</BaseButton>
        </RouterLink>
        <RouterLink to="/nodes">
          <BaseButton variant="secondary">浏览全部节点</BaseButton>
        </RouterLink>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">节点总数</p>
        <p class="text-3xl font-bold text-gray-900">{{ stats.total }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">活跃节点</p>
        <p class="text-3xl font-bold text-green-600">{{ stats.active }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">草稿节点</p>
        <p class="text-3xl font-bold text-gray-400">{{ stats.draft }}</p>
      </div>
    </div>

    <!-- 最近节点 -->
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">最近节点</h2>

      <div v-if="loading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-10 bg-gray-100 rounded animate-pulse" />
      </div>

      <EmptyState v-else-if="recentNodes.length === 0" description="还没有节点">
        <RouterLink to="/nodes/new">
          <BaseButton variant="secondary" class="mt-2">注册第一个节点</BaseButton>
        </RouterLink>
      </EmptyState>

      <div v-else class="divide-y divide-gray-100">
        <RouterLink
          v-for="node in recentNodes"
          :key="node.id"
          :to="`/nodes/${node.id}`"
          class="flex items-center justify-between py-3 hover:bg-gray-50 px-2 rounded-md transition-colors"
        >
          <div class="flex items-center gap-3">
            <TypeBadge :type="node.type" />
            <span class="text-sm font-medium text-gray-900">{{ node.display_name || node.name }}</span>
          </div>
          <div class="flex items-center gap-3">
            <StatusBadge :status="node.status" />
            <span class="text-xs text-gray-400">{{ formatDate(node.created_at) }}</span>
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listNodes } from '@/api/nodes'
import type { NodeItem } from '@/api/nodes'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TypeBadge from '@/components/TypeBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const auth = useAuthStore()
const nodes = ref<NodeItem[]>([])
const loading = ref(true)

const stats = computed(() => ({
  total: nodes.value.length,
  active: nodes.value.filter((n) => n.status === 'active').length,
  draft: nodes.value.filter((n) => n.status === 'draft').length,
}))

const recentNodes = computed(() =>
  [...nodes.value].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  ).slice(0, 5),
)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(async () => {
  try {
    const res = await listNodes({ page_size: 100 })
    nodes.value = res.data.items
  } finally {
    loading.value = false
  }
})
</script>

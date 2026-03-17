<template>
  <div>
    <!-- 加载骨架 -->
    <div v-if="loading" class="space-y-4">
      <div class="h-8 bg-gray-100 rounded w-64 animate-pulse" />
      <div class="h-40 bg-gray-100 rounded animate-pulse" />
    </div>

    <!-- 404 -->
    <div v-else-if="notFound" class="text-center py-20">
      <p class="text-gray-500 mb-4">节点未找到</p>
      <RouterLink to="/nodes">
        <BaseButton variant="secondary">返回列表</BaseButton>
      </RouterLink>
    </div>

    <template v-else-if="node">
      <!-- 操作栏 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <RouterLink to="/nodes" class="text-gray-400 hover:text-gray-600 transition-colors">
            ← 返回列表
          </RouterLink>
          <span class="text-gray-300">/</span>
          <h1 class="text-xl font-bold text-gray-900">
            {{ node.display_name || node.name }}
          </h1>
        </div>
        <RouterLink :to="`/nodes/${node.id}/invoke`">
          <BaseButton>调用此节点</BaseButton>
        </RouterLink>
      </div>

      <!-- 元信息卡片 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p class="text-xs text-gray-400 mb-1">唯一标识</p>
            <p class="text-sm font-mono text-gray-700">{{ node.name }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">显示名称</p>
            <p class="text-sm text-gray-700">{{ node.display_name || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">类型</p>
            <TypeBadge :type="node.type" />
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">状态</p>
            <StatusBadge :status="node.status" />
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">分类</p>
            <p class="text-sm text-gray-700">{{ node.category || '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">创建时间</p>
            <p class="text-sm text-gray-700">{{ formatDate(node.created_at) }}</p>
          </div>
          <div class="sm:col-span-2">
            <p class="text-xs text-gray-400 mb-1">描述</p>
            <p class="text-sm text-gray-700">{{ node.description || '暂无描述' }}</p>
          </div>
          <div v-if="node.tags?.length" class="sm:col-span-2">
            <p class="text-xs text-gray-400 mb-2">标签</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in node.tags"
                :key="tag"
                class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 版本列表 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">版本列表</h2>
        <EmptyState v-if="versions.length === 0" description="暂无版本记录" />
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left font-medium text-gray-500">版本号</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">默认</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">创建时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="v in versions" :key="v.id">
              <td class="px-4 py-3 font-mono text-gray-700">{{ v.version }}</td>
              <td class="px-4 py-3">
                <span
                  v-if="v.is_default"
                  class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium"
                >
                  默认
                </span>
                <span v-else class="text-gray-400 text-xs">—</span>
              </td>
              <td class="px-4 py-3 text-gray-400">{{ formatDate(v.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 调用日志 -->
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">最近调用日志</h2>
        <EmptyState v-if="logs.length === 0" description="暂无调用记录" />
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2 text-left font-medium text-gray-500">调用时间</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">状态</th>
              <th class="px-4 py-2 text-left font-medium text-gray-500">耗时 (ms)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="log in logs" :key="log.id">
              <td class="px-4 py-3 text-gray-500">{{ formatDate(log.created_at) }}</td>
              <td class="px-4 py-3">
                <span
                  :class="[
                    'px-2 py-0.5 rounded-full text-xs font-medium',
                    log.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : log.status === 'timeout'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700',
                  ]"
                >
                  {{ log.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ log.latency_ms ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNode, listVersions, getLogs } from '@/api/nodes'
import type { NodeItem, NodeVersion, InvocationLog } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TypeBadge from '@/components/TypeBadge.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const id = route.params.id as string

const node = ref<NodeItem | null>(null)
const versions = ref<NodeVersion[]>([])
const logs = ref<InvocationLog[]>([])
const loading = ref(true)
const notFound = ref(false)

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

onMounted(async () => {
  try {
    const [nodeRes, versionsRes, logsRes] = await Promise.all([
      getNode(id),
      listVersions(id),
      getLogs(id, { page_size: 10 }),
    ])
    node.value = nodeRes.data
    versions.value = versionsRes.data
    logs.value = logsRes.data.items
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 404) {
      notFound.value = true
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <!-- 返回 + 标题栏 -->
    <div class="flex items-center gap-3 mb-6">
      <RouterLink
        to="/discover"
        class="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        返回列表
      </RouterLink>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="space-y-4">
      <div class="h-24 bg-gray-100 rounded-2xl animate-pulse" />
      <div class="h-48 bg-gray-100 rounded-2xl animate-pulse" />
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
      <p class="text-sm text-red-600">{{ error }}</p>
    </div>

    <template v-else-if="session">
      <!-- 元信息卡片 -->
      <div class="bg-white rounded-2xl border border-gray-100 p-6 mb-5" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <h1 class="text-xl font-semibold text-gray-900">发现详情</h1>
              <StatusBadge :status="session.status" />
            </div>
            <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-600">
              <div class="flex items-center gap-1.5">
                <span class="text-gray-400 text-xs">来源</span>
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="session.source === 'upload' ? 'bg-purple-50 text-purple-700' : 'bg-blue-50 text-blue-700'"
                >
                  {{ session.source === 'probe' ? '接口探测' : '文件上传' }}
                </span>
              </div>
              <div v-if="session.base_url" class="flex items-center gap-1.5">
                <span class="text-gray-400 text-xs">地址</span>
                <span class="font-mono text-xs text-gray-700 max-w-xs truncate">{{ session.base_url }}</span>
              </div>
              <div v-if="session.spec_url" class="flex items-center gap-1.5">
                <span class="text-gray-400 text-xs">Spec URL</span>
                <a :href="session.spec_url" target="_blank" class="font-mono text-xs text-indigo-600 hover:underline max-w-xs truncate">
                  {{ session.spec_url }}
                </a>
              </div>
            </div>
          </div>
          <div class="flex gap-6 text-center shrink-0">
            <div>
              <p class="text-2xl font-bold text-gray-900">{{ session.total_operations ?? '-' }}</p>
              <p class="text-xs text-gray-400 mt-0.5">发现接口</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-indigo-600">{{ session.imported_count }}</p>
              <p class="text-xs text-gray-400 mt-0.5">已导入</p>
            </div>
          </div>
        </div>

        <!-- 时间信息 -->
        <div class="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-400">
          <span>创建于 {{ formatDateTime(session.created_at) }}</span>
          <span v-if="session.completed_at">完成于 {{ formatDateTime(session.completed_at) }}</span>
        </div>
      </div>

      <!-- 已导入节点列表 -->
      <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 class="text-sm font-semibold text-gray-900">关联节点</h2>
            <p class="text-xs text-gray-400 mt-0.5">本次发现导入的 {{ session.nodes.length }} 个节点</p>
          </div>
        </div>

        <!-- 空状态（无节点） -->
        <div v-if="session.nodes.length === 0" class="py-12 text-center">
          <p class="text-sm text-gray-400">暂无已导入节点</p>
          <RouterLink
            to="/discover/new"
            class="inline-block mt-3 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
          >
            重新导入
          </RouterLink>
        </div>

        <!-- 节点表格 -->
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50/80 border-b border-gray-100">
            <tr>
              <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">名称</th>
              <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">路径</th>
              <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
              <th class="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="node in session.nodes"
              :key="node.id"
              class="hover:bg-indigo-50/40 transition-colors"
            >
              <td class="px-6 py-4">
                <p class="font-medium text-gray-900">{{ node.display_name || node.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5 font-mono">{{ node.name }}</p>
              </td>
              <td class="px-6 py-4 font-mono text-xs text-gray-500 max-w-xs truncate" :title="node.source_path ?? ''">
                {{ node.source_path || '-' }}
              </td>
              <td class="px-6 py-4">
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="nodeStatusClass(node.status)"
                >
                  {{ node.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <RouterLink
                  :to="`/nodes/${node.id}`"
                  class="text-xs text-indigo-600 hover:text-indigo-800 hover:underline transition-colors"
                >
                  查看详情 →
                </RouterLink>
              </td>
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
import { getSession } from '@/api/discovery'
import type { DiscoverySessionDetail } from '@/api/discovery'

// ---- 状态徽章（内联子组件） ----
const StatusBadge = {
  props: ['status'],
  template: `
    <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-semibold" :class="cls">
      <span v-if="status === 'probing'" class="w-1.5 h-1.5 rounded-full bg-current animate-pulse inline-block"></span>
      {{ label }}
    </span>
  `,
  computed: {
    cls(this: { status: string }): string {
      const map: Record<string, string> = {
        probing: 'bg-gray-100 text-gray-600',
        found: 'bg-blue-100 text-blue-700',
        failed: 'bg-red-100 text-red-700',
        completed: 'bg-green-100 text-green-700',
      }
      return map[this.status] ?? 'bg-gray-100 text-gray-600'
    },
    label(this: { status: string }): string {
      const map: Record<string, string> = {
        probing: '探测中',
        found: '已发现',
        failed: '失败',
        completed: '已完成',
      }
      return map[this.status] ?? this.status
    },
  },
}

const route = useRoute()
const session = ref<DiscoverySessionDetail | null>(null)
const loading = ref(false)
const error = ref('')

function nodeStatusClass(status: string) {
  const map: Record<string, string> = {
    active: 'bg-green-50 text-green-700',
    inactive: 'bg-gray-100 text-gray-500',
    deprecated: 'bg-amber-50 text-amber-700',
    draft: 'bg-blue-50 text-blue-700',
  }
  return map[status] ?? 'bg-gray-100 text-gray-500'
}

function formatDateTime(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getSession(route.params.id as string)
    session.value = res.data as DiscoverySessionDetail
  } catch (e: any) {
    error.value = e.uiMessage || e.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

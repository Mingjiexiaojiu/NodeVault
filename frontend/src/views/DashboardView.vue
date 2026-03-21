<template>
  <div>
    <!-- 欢迎横幅 -->
    <div class="relative overflow-hidden rounded-2xl mb-8 px-8 py-7" style="background: linear-gradient(135deg, #6366f1 0%, #7c3aed 60%, #a78bfa 100%)">
      <div class="relative z-10 flex items-start justify-between gap-4">
        <div>
          <p class="text-indigo-200 text-sm font-medium">欢迎回来</p>
          <h1 class="text-2xl font-bold text-white mt-1">{{ auth.user?.display_name || auth.user?.username }} 👋</h1>
          <p class="text-indigo-200/80 text-sm mt-1.5">你的 NodeVault AI 能力控制台</p>
        </div>
        <div class="flex gap-2 shrink-0">
          <RouterLink to="/nodes/new">
            <button class="flex items-center gap-1.5 px-4 py-2 bg-white text-indigo-700 text-sm font-semibold rounded-xl hover:bg-indigo-50 transition-colors shadow-sm">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
              </svg>
              注册新节点
            </button>
          </RouterLink>
          <RouterLink to="/discover">
            <button class="flex items-center gap-1.5 px-4 py-2 bg-white/20 text-white text-sm font-medium rounded-xl hover:bg-white/30 transition-colors border border-white/25">
              从服务导入
            </button>
          </RouterLink>
        </div>
      </div>
      <!-- 装饰圆 -->
      <div class="absolute -top-10 -right-10 w-44 h-44 rounded-full bg-white/10 pointer-events-none"></div>
      <div class="absolute -bottom-8 right-28 w-28 h-28 rounded-full bg-white/10 pointer-events-none"></div>
      <div class="absolute top-6 right-52 w-14 h-14 rounded-full bg-white/10 pointer-events-none"></div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-sm hover:border-indigo-100 transition-all">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">节点总数</p>
            <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.total }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-3">全部注册节点</p>
      </div>
      <div class="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-sm hover:border-emerald-100 transition-all">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">活跃节点</p>
            <p class="text-3xl font-bold text-emerald-600 mt-2">{{ stats.active }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-3">正在运行中</p>
      </div>
      <div class="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-sm transition-all">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">草稿节点</p>
            <p class="text-3xl font-bold text-gray-400 mt-2">{{ stats.draft }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-gray-50 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-3">待完善发布</p>
      </div>
    </div>

    <!-- 最近节点 -->
    <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-900">最近节点</h2>
        <RouterLink to="/nodes" class="text-xs text-indigo-500 hover:text-indigo-700 transition-colors">查看全部 →</RouterLink>
      </div>

      <div v-if="loading" class="space-y-3 px-6 py-4">
        <div v-for="i in 5" :key="i" class="h-10 bg-gray-100 rounded animate-pulse" />
      </div>

      <div v-else-if="loadError" class="flex flex-col items-center justify-center py-12 text-center px-6">
        <svg class="h-12 w-12 text-red-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
        <p class="text-sm text-gray-500 mb-3">加载失败，请刷新页面重试</p>
        <button @click="reload" class="text-sm text-indigo-600 hover:underline">重新加载</button>
      </div>

      <div v-else-if="recentNodes.length === 0" class="flex flex-col items-center justify-center py-12 text-center px-6">
        <svg class="h-14 w-14 text-indigo-100 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p class="text-gray-900 font-medium mb-1">还没有节点</p>
        <p class="text-sm text-gray-500 mb-4">注册你的第一个节点，开始管理 AI 能力</p>
        <RouterLink to="/nodes/new">
          <BaseButton>注册第一个节点</BaseButton>
        </RouterLink>
      </div>

      <div v-else class="divide-y divide-gray-50 px-3 pb-3">
        <RouterLink
          v-for="node in recentNodes"
          :key="node.id"
          :to="`/nodes/${node.id}`"
          class="flex items-center justify-between py-3 px-3 hover:bg-indigo-50/50 rounded-xl transition-colors"
        >
          <div class="flex items-center gap-3">
            <TypeBadge :category="node.category" />
            <span class="text-sm font-medium text-gray-900">{{ node.display_name || node.name }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span v-if="node.namespace_slug" class="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-medium">{{ node.namespace_slug }}</span>
            <span v-if="node.owner_username" class="text-xs text-gray-400">{{ node.owner_username }}</span>
            <StatusBadge :status="node.status" />
            <span class="text-xs text-gray-300">{{ formatDate(node.created_at) }}</span>
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

const auth = useAuthStore()
const nodes = ref<NodeItem[]>([])
const loading = ref(true)
const loadError = ref(false)

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

async function reload() {
  loading.value = true
  loadError.value = false
  try {
    const res = await listNodes({ page_size: 100 })
    nodes.value = res.data
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

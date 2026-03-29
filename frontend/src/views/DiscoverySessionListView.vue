<template>
  <div>
    <!-- 标题栏 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">服务发现历史</h1>
        <p class="text-sm text-gray-400 mt-0.5">查看每次 OpenAPI 探测和导入的记录</p>
      </div>
      <RouterLink to="/discover/new">
        <button class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-sm shadow-indigo-200">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          新建发现
        </button>
      </RouterLink>
    </div>

    <!-- 列表 -->
    <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
      <!-- 加载骨架屏 -->
      <div v-if="loading" class="p-6 space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded animate-pulse" />
      </div>

      <!-- 空状态 -->
      <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center py-20 gap-4 text-center">
        <div class="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center">
          <svg class="w-8 h-8 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
        <div>
          <p class="text-sm font-medium text-gray-600">还没有发现记录</p>
          <p class="text-xs text-gray-400 mt-1">通过探测 OpenAPI 地址或上传 Spec 文件来发现接口</p>
        </div>
        <RouterLink to="/discover/new">
          <button class="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors mt-1">
            开始第一次发现
          </button>
        </RouterLink>
      </div>

      <!-- 数据表格 -->
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50/80 border-b border-gray-100">
          <tr>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">来源</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">URL / 文件</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">发现数</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">导入数</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="session in sessions"
            :key="session.id"
            class="hover:bg-indigo-50/40 cursor-pointer transition-colors"
            @click="$router.push(`/discover/${session.id}`)"
          >
            <!-- 来源类型 -->
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="session.source === 'upload' ? 'bg-purple-50 text-purple-700' : 'bg-blue-50 text-blue-700'"
              >
                <svg v-if="session.source === 'probe'" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <svg v-else class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                {{ session.source === 'probe' ? '探测' : '上传' }}
              </span>
            </td>
            <!-- URL -->
            <td class="px-6 py-4 max-w-xs">
              <p class="font-mono text-xs text-gray-600 truncate" :title="session.base_url">
                {{ session.base_url || '-' }}
              </p>
            </td>
            <!-- 发现数 -->
            <td class="px-6 py-4 text-gray-700">
              {{ session.total_operations ?? '-' }}
            </td>
            <!-- 导入数 -->
            <td class="px-6 py-4 text-gray-700">
              {{ session.imported_count }}
            </td>
            <!-- 状态 -->
            <td class="px-6 py-4">
              <StatusBadge :status="session.status" />
            </td>
            <!-- 创建时间 -->
            <td class="px-6 py-4 text-gray-400 text-xs whitespace-nowrap">
              {{ formatTime(session.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="sessions.length > 0" class="flex items-center justify-between px-6 py-4 border-t border-gray-100">
        <p class="text-xs text-gray-400">共 {{ total }} 条记录</p>
        <div class="flex gap-2">
          <button
            :disabled="page <= 1"
            class="px-3 py-1.5 text-xs rounded-lg border border-gray-200 text-gray-500 disabled:opacity-40 hover:bg-gray-50 transition-colors"
            @click="changePage(page - 1)"
          >
            上一页
          </button>
          <span class="px-3 py-1.5 text-xs text-gray-500">第 {{ page }} 页</span>
          <button
            :disabled="sessions.length < pageSize"
            class="px-3 py-1.5 text-xs rounded-lg border border-gray-200 text-gray-500 disabled:opacity-40 hover:bg-gray-50 transition-colors"
            @click="changePage(page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listSessions } from '@/api/discovery'
import type { DiscoverySession } from '@/api/discovery'

// ---- 状态徽章子组件（内联，避免额外文件） ----
const StatusBadge = {
  props: ['status'],
  template: `
    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium" :class="cls">
      <span v-if="status === 'probing'" class="w-1.5 h-1.5 rounded-full bg-current animate-pulse inline-block"></span>
      {{ label }}
    </span>
  `,
  computed: {
    cls(this: { status: string }): string {
      const map: Record<string, string> = {
        probing: 'bg-gray-100 text-gray-500',
        found: 'bg-blue-50 text-blue-700',
        failed: 'bg-red-50 text-red-600',
        completed: 'bg-green-50 text-green-700',
      }
      return map[this.status] ?? 'bg-gray-100 text-gray-500'
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

const sessions = ref<DiscoverySession[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

async function fetchSessions() {
  loading.value = true
  try {
    const res = await listSessions(page.value, pageSize)
    const data = res.data as any
    // 支持两种返回格式：直接数组 或 { items, total }
    if (Array.isArray(data)) {
      sessions.value = data
      total.value = data.length
    } else {
      sessions.value = data.items ?? []
      total.value = data.total ?? sessions.value.length
    }
  } catch {
    sessions.value = []
  } finally {
    loading.value = false
  }
}

function changePage(newPage: number) {
  page.value = newPage
  fetchSessions()
}

function formatTime(iso: string) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchSessions()
})
</script>

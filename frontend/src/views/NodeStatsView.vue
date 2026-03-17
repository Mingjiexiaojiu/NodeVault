<template>
  <div>
    <div v-if="loading" class="space-y-4">
      <div class="h-8 bg-gray-100 rounded w-64 animate-pulse" />
      <div class="h-48 bg-gray-100 rounded animate-pulse" />
    </div>

    <div v-else-if="!stats" class="text-center py-20">
      <p class="text-gray-500">无法加载统计数据</p>
    </div>

    <template v-else>
      <!-- 标题 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-bold text-gray-900">调用统计</h1>
          <p class="text-sm text-gray-500 mt-0.5">节点 <span class="font-mono text-gray-700">{{ nodeId }}</span></p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">统计周期</span>
          <select
            v-model="days"
            class="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            @change="fetchStats"
          >
            <option :value="7">近 7 天</option>
            <option :value="30">近 30 天</option>
            <option :value="90">近 90 天</option>
            <option :value="365">近 365 天</option>
          </select>
        </div>
      </div>

      <!-- KPI 卡片 -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-2xl border border-gray-200 p-5">
          <p class="text-xs text-gray-500 mb-1">总调用次数</p>
          <p class="text-3xl font-bold text-gray-900">{{ stats.total_invocations }}</p>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 p-5">
          <p class="text-xs text-gray-500 mb-1">成功率</p>
          <p
            class="text-3xl font-bold"
            :class="successRateColor"
          >
            {{ stats.success_rate !== null ? (stats.success_rate * 100).toFixed(1) + '%' : '—' }}
          </p>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 p-5">
          <p class="text-xs text-gray-500 mb-1">平均延迟</p>
          <p class="text-3xl font-bold text-gray-900">
            {{ stats.avg_latency_ms !== null ? stats.avg_latency_ms + ' ms' : '—' }}
          </p>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 p-5">
          <p class="text-xs text-gray-500 mb-1">P95 延迟</p>
          <p class="text-3xl font-bold text-gray-900">
            {{ stats.p95_latency_ms !== null ? stats.p95_latency_ms + ' ms' : '—' }}
          </p>
        </div>
      </div>

      <!-- 每日趋势 -->
      <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
        <h2 class="text-sm font-semibold text-gray-700 mb-4">每日调用趋势</h2>
        <div v-if="stats.daily_trend.length === 0" class="py-10 text-center text-gray-400 text-sm">
          该周期内暂无调用数据
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="day in stats.daily_trend"
            :key="day.date"
            class="flex items-center gap-3"
          >
            <span class="text-xs text-gray-400 w-20 shrink-0">{{ formatDay(day.date) }}</span>
            <div class="flex-1 flex items-center gap-1 h-6">
              <!-- 成功 bar -->
              <div
                class="h-full rounded-sm bg-indigo-500 transition-all"
                :style="{ width: barWidth(day.success, maxDayCount) }"
              />
              <!-- 失败 bar -->
              <div
                v-if="day.count - day.success > 0"
                class="h-full rounded-sm bg-red-300 transition-all"
                :style="{ width: barWidth(day.count - day.success, maxDayCount) }"
              />
            </div>
            <span class="text-xs text-gray-500 w-12 text-right shrink-0">{{ day.count }}</span>
          </div>
          <div class="flex items-center gap-4 pt-2 text-xs text-gray-400">
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm bg-indigo-500 inline-block"></span>成功</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-sm bg-red-300 inline-block"></span>失败</span>
          </div>
        </div>
      </div>

      <!-- 延迟分布 -->
      <div class="bg-white rounded-2xl border border-gray-200 p-6">
        <h2 class="text-sm font-semibold text-gray-700 mb-4">延迟分布</h2>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div class="bg-gray-50 rounded-xl p-4">
            <p class="text-xs text-gray-400 mb-1">平均 (Avg)</p>
            <p class="text-xl font-semibold text-gray-700">{{ stats.avg_latency_ms ?? '—' }} <span class="text-xs font-normal text-gray-400">ms</span></p>
          </div>
          <div class="bg-indigo-50 rounded-xl p-4">
            <p class="text-xs text-indigo-400 mb-1">P95</p>
            <p class="text-xl font-semibold text-indigo-700">{{ stats.p95_latency_ms ?? '—' }} <span class="text-xs font-normal text-indigo-400">ms</span></p>
          </div>
          <div class="bg-violet-50 rounded-xl p-4">
            <p class="text-xs text-violet-400 mb-1">P99</p>
            <p class="text-xl font-semibold text-violet-700">{{ stats.p99_latency_ms ?? '—' }} <span class="text-xs font-normal text-violet-400">ms</span></p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNodeStats } from '@/api/nodes'
import type { NodeStats } from '@/api/nodes'

const route = useRoute()
const nodeId = route.params.id as string

const stats = ref<NodeStats | null>(null)
const loading = ref(true)
const days = ref(30)

const successRateColor = computed(() => {
  if (stats.value?.success_rate === null || stats.value?.success_rate === undefined) return 'text-gray-400'
  const r = stats.value.success_rate
  if (r >= 0.95) return 'text-green-600'
  if (r >= 0.8) return 'text-yellow-600'
  return 'text-red-600'
})

const maxDayCount = computed(() =>
  Math.max(1, ...((stats.value?.daily_trend ?? []).map(d => d.count)))
)

function barWidth(value: number, max: number) {
  return `${Math.max(2, Math.round((value / max) * 100))}%`
}

function formatDay(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function fetchStats() {
  loading.value = true
  try {
    const res = await getNodeStats(nodeId, days.value)
    stats.value = res.data
  } catch {
    stats.value = null
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

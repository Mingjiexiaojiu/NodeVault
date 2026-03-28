<template>
  <div class="space-y-6">
    <!-- 概览卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <div v-for="card in statCards" :key="card.label"
        class="bg-white rounded-2xl p-4 flex flex-col gap-1" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <span class="text-xs text-gray-400">{{ card.label }}</span>
        <span class="text-2xl font-bold text-gray-900">{{ card.value }}</span>
        <span v-if="card.sub" class="text-xs text-emerald-500">{{ card.sub }}</span>
      </div>
    </div>

    <!-- 调用趋势 -->
    <div class="bg-white rounded-2xl p-5" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-800">调用趋势</h2>
        <div class="flex gap-1">
          <button
            v-for="r in ranges" :key="r.value"
            @click="range = r.value; loadTrend()"
            class="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
            :class="range === r.value ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
          >{{ r.label }}</button>
        </div>
      </div>

      <div v-if="trendLoading" class="flex items-center justify-center h-40">
        <div class="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <div v-else-if="trendData.length" class="relative">
        <!-- SVG 折线图 -->
        <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" class="w-full" style="height:180px">
          <!-- Y轴网格线 -->
          <line v-for="y in yTicks" :key="y" :y1="toY(y)" :y2="toY(y)" x1="40" :x2="SVG_W - 10"
            stroke="#f0f0f0" stroke-width="1" />
          <text v-for="y in yTicks" :key="'l'+y" x="34" :y="toY(y)+4" text-anchor="end"
            font-size="10" fill="#aaa">{{ formatNum(y) }}</text>

          <!-- X轴标签（只显示首尾和中间几个） -->
          <text v-for="(d, i) in xLabels" :key="'x'+i" :x="toX(d.i)" :y="SVG_H - 4"
            text-anchor="middle" font-size="10" fill="#bbb">{{ d.label }}</text>

          <!-- 成功面积 -->
          <path :d="successArea" fill="#6366f1" fill-opacity="0.08" />
          <!-- 失败面积 -->
          <path :d="failureArea" fill="#f87171" fill-opacity="0.08" />
          <!-- 成功折线 -->
          <polyline :points="successLine" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          <!-- 失败折线 -->
          <polyline :points="failureLine" fill="none" stroke="#f87171" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 2" />
        </svg>

        <!-- 图例 -->
        <div class="flex gap-4 justify-end mt-1">
          <span class="flex items-center gap-1 text-xs text-gray-500">
            <span class="w-6 h-0.5 bg-indigo-500 inline-block"></span> 成功
          </span>
          <span class="flex items-center gap-1 text-xs text-gray-500">
            <span class="w-6 h-0.5 bg-red-400 inline-block" style="border-top: 1.5px dashed #f87171;background:none"></span> 失败
          </span>
        </div>
      </div>
      <div v-else class="text-center text-gray-400 py-10 text-sm">暂无调用数据</div>
    </div>

    <!-- Top 节点 & Top 用户 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <!-- Top 节点 -->
      <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="px-5 py-4 border-b border-gray-50">
          <h2 class="font-semibold text-gray-800">热门节点 Top 10</h2>
        </div>
        <div v-if="topNodesLoading" class="flex items-center justify-center h-32">
          <div class="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <table v-else class="w-full text-sm">
          <tbody class="divide-y divide-gray-50">
            <tr v-for="(node, i) in topNodes" :key="node.id" class="hover:bg-gray-50/60 transition-colors">
              <td class="pl-5 pr-2 py-3 w-8 text-xs font-semibold text-gray-400">{{ i + 1 }}</td>
              <td class="px-2 py-3">
                <div class="font-medium text-gray-800 text-xs">{{ node.display_name || node.name }}</div>
                <div class="text-xs text-gray-400">{{ node.department_slug }}</div>
              </td>
              <td class="px-3 py-3 text-xs text-gray-500">{{ node.owner_username }}</td>
              <td class="pr-5 py-3 text-right text-xs font-semibold text-indigo-600">{{ node.invocation_count.toLocaleString() }}</td>
            </tr>
            <tr v-if="topNodes.length === 0">
              <td colspan="4" class="text-center py-10 text-gray-400 text-sm">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Top 用户 -->
      <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="px-5 py-4 border-b border-gray-50">
          <h2 class="font-semibold text-gray-800">活跃用户 Top 10</h2>
        </div>
        <div v-if="topUsersLoading" class="flex items-center justify-center h-32">
          <div class="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <table v-else class="w-full text-sm">
          <tbody class="divide-y divide-gray-50">
            <tr v-for="(u, i) in topUsers" :key="u.id" class="hover:bg-gray-50/60 transition-colors">
              <td class="pl-5 pr-2 py-3 w-8 text-xs font-semibold text-gray-400">{{ i + 1 }}</td>
              <td class="px-2 py-3">
                <div class="font-medium text-gray-800 text-xs">{{ u.display_name || u.username }}</div>
                <div class="text-xs text-gray-400">@{{ u.username }}</div>
              </td>
              <td class="px-3 py-3 text-xs text-gray-500">{{ u.node_count }} 节点</td>
              <td class="pr-5 py-3 text-right text-xs font-semibold text-purple-600">{{ u.skill_count }} Skill</td>
            </tr>
            <tr v-if="topUsers.length === 0">
              <td colspan="4" class="text-center py-10 text-gray-400 text-sm">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getAnalyticsOverview, getInvocationTrend, getTopNodes, getTopUsers,
  type PlatformOverview, type DailyInvocationStat, type TopNodeItem, type TopUserItem
} from '@/api/admin'

// ── Constants ──────────────────────────────────
const SVG_W = 640
const SVG_H = 160
const PAD_L = 44
const PAD_R = 12
const PAD_T = 12
const PAD_B = 22

// ── State ──────────────────────────────────────
const overview = ref<PlatformOverview | null>(null)
const trendData = ref<DailyInvocationStat[]>([])
const topNodes = ref<TopNodeItem[]>([])
const topUsers = ref<TopUserItem[]>([])
const range = ref<'7d' | '30d' | '90d'>('30d')
const trendLoading = ref(false)
const topNodesLoading = ref(false)
const topUsersLoading = ref(false)

const ranges = [
  { label: '7天', value: '7d' as const },
  { label: '30天', value: '30d' as const },
  { label: '90天', value: '90d' as const },
]

// ── Stat cards ─────────────────────────────────
const statCards = computed(() => {
  const o = overview.value
  if (!o) return []
  return [
    { label: '总用户', value: o.total_users.toLocaleString() },
    { label: '总节点', value: o.total_nodes.toLocaleString() },
    { label: '总 Skill', value: o.total_skills.toLocaleString() },
    { label: '总调用', value: o.total_invocations.toLocaleString() },
    { label: '新增用户 24h', value: o.new_users_24h.toLocaleString(), sub: '过去一天' },
    { label: '调用次数 24h', value: o.invocations_24h.toLocaleString(), sub: '过去一天' },
  ]
})

// ── Chart helpers ──────────────────────────────
const maxY = computed(() => {
  const maxSuccess = Math.max(...trendData.value.map(d => d.success), 1)
  const maxFail = Math.max(...trendData.value.map(d => d.failure), 0)
  return Math.max(maxSuccess, maxFail)
})

const yTicks = computed(() => {
  const m = maxY.value
  const step = Math.ceil(m / 4 / 10) * 10 || 1
  return [step, step * 2, step * 3, step * 4].filter(v => v <= m * 1.1)
})

function toX(i: number) {
  const n = trendData.value.length - 1
  return PAD_L + (i / Math.max(n, 1)) * (SVG_W - PAD_L - PAD_R)
}
function toY(v: number) {
  return PAD_T + (1 - v / (maxY.value * 1.1)) * (SVG_H - PAD_T - PAD_B)
}

const successLine = computed(() =>
  trendData.value.map((d, i) => `${toX(i)},${toY(d.success)}`).join(' ')
)
const failureLine = computed(() =>
  trendData.value.map((d, i) => `${toX(i)},${toY(d.failure)}`).join(' ')
)
const successArea = computed(() => {
  const n = trendData.value.length - 1
  const base = toY(0)
  const pts = trendData.value.map((d, i) => `${toX(i)},${toY(d.success)}`).join(' L ')
  return `M ${toX(0)},${base} L ${pts} L ${toX(n)},${base} Z`
})
const failureArea = computed(() => {
  const n = trendData.value.length - 1
  const base = toY(0)
  const pts = trendData.value.map((d, i) => `${toX(i)},${toY(d.failure)}`).join(' L ')
  return `M ${toX(0)},${base} L ${pts} L ${toX(n)},${base} Z`
})

const xLabels = computed(() => {
  const data = trendData.value
  if (!data.length) return []
  const n = data.length
  const indices = new Set([0, Math.floor(n / 4), Math.floor(n / 2), Math.floor((3 * n) / 4), n - 1])
  return [...indices].map(i => ({
    i,
    label: data[i]?.date?.slice(5) ?? '',
  }))
})

function formatNum(n: number) {
  if (n >= 1000) return (n / 1000).toFixed(0) + 'k'
  return String(n)
}

// ── Data loading ───────────────────────────────
async function loadOverview() {
  const res = await getAnalyticsOverview()
  overview.value = res.data
}
async function loadTrend() {
  trendLoading.value = true
  try {
    const res = await getInvocationTrend(range.value)
    trendData.value = res.data
  } finally {
    trendLoading.value = false
  }
}
async function loadTopNodes() {
  topNodesLoading.value = true
  try {
    const res = await getTopNodes()
    topNodes.value = res.data
  } finally {
    topNodesLoading.value = false
  }
}
async function loadTopUsers() {
  topUsersLoading.value = true
  try {
    const res = await getTopUsers()
    topUsers.value = res.data
  } finally {
    topUsersLoading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadTrend()
  loadTopNodes()
  loadTopUsers()
})
</script>

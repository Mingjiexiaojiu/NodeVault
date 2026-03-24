<template>
  <div class="space-y-5">
    <!-- 头部统计卡片 -->
    <div class="grid grid-cols-3 gap-4">
      <div v-for="card in cards" :key="card.label"
        class="bg-white rounded-2xl p-5 flex items-center gap-4"
        style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
        <div class="w-10 h-10 rounded-xl flex items-center justify-center" :style="`background:${card.bg}`">
          <svg class="w-5 h-5" :style="`color:${card.color}`" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" v-html="card.icon"></svg>
        </div>
        <div>
          <div class="text-2xl font-bold text-gray-900">{{ card.value }}</div>
          <div class="text-xs text-gray-500">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- API Key 列表 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-gray-800">API 密钥管理</h3>
        <span class="text-xs text-gray-400">只读审计视图</span>
      </div>
      <div v-if="loading" class="flex items-center justify-center h-40">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">名称</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">所属用户</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">前缀</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">状态</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">最后使用</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="key in apiKeys" :key="key.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5 font-medium text-gray-900">{{ key.name }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ key.username }}</td>
            <td class="px-4 py-3.5 font-mono text-xs text-gray-500">{{ key.key_prefix }}…</td>
            <td class="px-4 py-3.5">
              <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="key.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'">
                <span class="w-1.5 h-1.5 rounded-full"
                  :class="key.is_active ? 'bg-green-500' : 'bg-gray-400'"></span>
                {{ key.is_active ? '启用' : '停用' }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-xs text-gray-400">{{ key.last_used_at?.slice(0, 10) || '从未' }}</td>
            <td class="px-4 py-3.5 text-xs text-gray-400">{{ key.created_at?.slice(0, 10) }}</td>
          </tr>
          <tr v-if="!loading && apiKeys.length === 0">
            <td colspan="6" class="text-center py-16 text-gray-400">暂无 API 密钥数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button
        v-for="p in totalPages" :key="p"
        @click="page = p; loadKeys()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
      >{{ p }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listAllApiKeys, type AdminApiKeyListItem } from '@/api/admin'

const apiKeys = ref<AdminApiKeyListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const cards = ref([
  {
    label: '有效密钥',
    value: '—',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"/>',
    bg: '#eef2ff', color: '#4f46e5'
  },
  {
    label: '已停用密钥',
    value: '—',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>',
    bg: '#fef3c7', color: '#d97706'
  },
  {
    label: '总密钥数',
    value: '—',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"/>',
    bg: '#f0fdf4', color: '#16a34a'
  }
])

async function loadKeys() {
  loading.value = true
  try {
    const res = await listAllApiKeys({ page: page.value, page_size: pageSize })
    apiKeys.value = res.data.items
    total.value = res.data.total
    // 更新统计卡片
    const all = res.data.items
    const active = all.filter((k: AdminApiKeyListItem) => k.is_active).length
    cards.value[0].value = String(active)
    cards.value[1].value = String(all.length - active)
    cards.value[2].value = String(res.data.total)
  } finally {
    loading.value = false
  }
}

onMounted(loadKeys)
</script>

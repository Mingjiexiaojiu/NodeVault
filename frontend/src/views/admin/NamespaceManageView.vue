<template>
  <div class="space-y-5">
    <!-- 过滤栏 -->
    <div class="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-center" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <input
        v-model="q"
        @input="onSearch"
        type="text"
        placeholder="搜索部门名称或 slug…"
        class="text-sm border border-gray-200 rounded-xl px-3 py-2 w-60 focus:outline-none focus:ring-2 focus:ring-indigo-300"
      />
      <span class="text-sm text-gray-400 ml-auto">共 {{ total }} 个部门</span>
    </div>

    <!-- 表格 -->
    <div class="bg-white rounded-2xl overflow-hidden" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06)">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">部门</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">所有者</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">成员数</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">节点数</th>
            <th class="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">创建时间</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="ns in namespaces" :key="ns.id" class="hover:bg-gray-50/60 transition-colors">
            <td class="px-5 py-3.5">
              <div class="font-medium text-gray-900">{{ ns.display_name || ns.slug }}</div>
              <div class="text-xs text-gray-400 font-mono">{{ ns.slug }}</div>
            </td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.owner_username || '—' }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.member_count }}</td>
            <td class="px-4 py-3.5 text-gray-600">{{ ns.node_count }}</td>
            <td class="px-4 py-3.5 text-gray-400 text-xs">{{ ns.created_at?.slice(0, 10) }}</td>
          </tr>
          <tr v-if="!loading && namespaces.length === 0">
            <td colspan="5" class="text-center py-16 text-gray-400">暂无部门</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2">
      <button
        v-for="p in totalPages" :key="p"
        @click="page = p; load()"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
        :class="p === page ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:bg-gray-100'"
      >{{ p }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listAllDepartments, type AdminDepartmentListItem } from '@/api/admin'

const namespaces = ref<AdminDepartmentListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const q = ref('')
let searchTimer: ReturnType<typeof setTimeout>

const totalPages = computed(() => Math.ceil(total.value / pageSize))

async function load() {
  loading.value = true
  try {
    const res = await listAllDepartments({ page: page.value, page_size: pageSize })
    namespaces.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 350)
}

onMounted(load)
</script>
